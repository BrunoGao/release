#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分布式事务和缓存一致性管理器

主要功能:
1. 分布式事务协调（Saga模式）
2. 最终一致性保证
3. 缓存失效策略
4. 补偿机制
5. 事件驱动架构
6. 死信队列处理

技术特性:
- Redis Stream消息队列
- 事务日志记录
- 自动重试和补偿
- 监控和告警集成

@Author: brunoGao
@CreateTime: 2025-09-11
@Version: 2.0-Fixed
"""

import json
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid

import redis
from redis import Redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


# ==================== 枚举和常量 ====================

class TransactionState(Enum):
    """事务状态"""
    PENDING = "pending"           # 待处理
    PROCESSING = "processing"     # 处理中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"            # 失败
    COMPENSATING = "compensating" # 补偿中
    COMPENSATED = "compensated"   # 已补偿


class EventType(Enum):
    """事件类型"""
    TRANSACTION_START = "transaction_start"
    TRANSACTION_COMMIT = "transaction_commit"
    TRANSACTION_ROLLBACK = "transaction_rollback"
    CACHE_INVALIDATE = "cache_invalidate"
    DATA_SYNC = "data_sync"
    COMPENSATION = "compensation"


class CacheInvalidationType(Enum):
    """缓存失效类型"""
    IMMEDIATE = "immediate"       # 立即失效
    DELAYED = "delayed"          # 延迟失效
    PATTERN = "pattern"          # 模式失效
    SELECTIVE = "selective"      # 选择性失效


# ==================== 数据结构定义 ====================

@dataclass
class TransactionStep:
    """事务步骤"""
    step_id: str
    step_name: str
    action: Callable
    compensation: Optional[Callable] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 30
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributedTransaction:
    """分布式事务"""
    transaction_id: str
    customer_id: int
    transaction_type: str
    steps: List[TransactionStep]
    state: TransactionState = TransactionState.PENDING
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheInvalidationEvent:
    """缓存失效事件"""
    event_id: str
    customer_id: int
    invalidation_type: CacheInvalidationType
    cache_keys: List[str]
    cache_patterns: List[str] = field(default_factory=list)
    delay_seconds: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventMessage:
    """事件消息"""
    event_id: str
    event_type: EventType
    customer_id: int
    payload: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = 0
    max_retries: int = 5


# ==================== 事务日志管理器 ====================

class TransactionLogger:
    """事务日志管理器"""
    
    def __init__(self, redis_client: Redis, db_session: Session):
        self.redis = redis_client
        self.db_session = db_session
    
    def log_transaction_start(self, transaction: DistributedTransaction):
        """记录事务开始"""
        log_entry = {
            'transaction_id': transaction.transaction_id,
            'customer_id': transaction.customer_id,
            'transaction_type': transaction.transaction_type,
            'state': transaction.state.value,
            'start_time': transaction.start_time.isoformat(),
            'step_count': len(transaction.steps),
            'context': transaction.context
        }
        
        # Redis日志（快速访问）
        self.redis.hset(
            f"transaction_log:{transaction.transaction_id}", 
            mapping=log_entry
        )
        self.redis.expire(f"transaction_log:{transaction.transaction_id}", 86400)  # 24小时过期
        
        # 数据库日志（持久化）
        try:
            self.db_session.execute(
                text("""
                    INSERT INTO t_transaction_log 
                    (transaction_id, customer_id, transaction_type, state, start_time, context, created_at)
                    VALUES (:transaction_id, :customer_id, :transaction_type, :state, :start_time, :context, :created_at)
                """),
                {
                    'transaction_id': transaction.transaction_id,
                    'customer_id': transaction.customer_id,
                    'transaction_type': transaction.transaction_type,
                    'state': transaction.state.value,
                    'start_time': transaction.start_time,
                    'context': json.dumps(transaction.context),
                    'created_at': datetime.now(timezone.utc)
                }
            )
            self.db_session.commit()
        except SQLAlchemyError as e:
            logger.warning(f"⚠️ 数据库事务日志记录失败: {e}")
            self.db_session.rollback()
    
    def log_transaction_step(
        self, 
        transaction_id: str, 
        step_id: str, 
        step_state: str, 
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """记录事务步骤"""
        step_log = {
            'step_id': step_id,
            'state': step_state,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'result': json.dumps(result) if result else None,
            'error': error
        }
        
        # 添加到Redis列表
        self.redis.lpush(f"transaction_steps:{transaction_id}", json.dumps(step_log))
        self.redis.expire(f"transaction_steps:{transaction_id}", 86400)
    
    def log_transaction_complete(self, transaction: DistributedTransaction):
        """记录事务完成"""
        # 更新Redis
        self.redis.hset(
            f"transaction_log:{transaction.transaction_id}",
            mapping={
                'state': transaction.state.value,
                'end_time': transaction.end_time.isoformat() if transaction.end_time else None,
                'error_message': transaction.error_message or '',
                'duration_ms': int((transaction.end_time - transaction.start_time).total_seconds() * 1000) if transaction.end_time else 0
            }
        )
        
        # 更新数据库
        try:
            self.db_session.execute(
                text("""
                    UPDATE t_transaction_log 
                    SET state = :state, end_time = :end_time, error_message = :error_message, updated_at = :updated_at
                    WHERE transaction_id = :transaction_id
                """),
                {
                    'transaction_id': transaction.transaction_id,
                    'state': transaction.state.value,
                    'end_time': transaction.end_time,
                    'error_message': transaction.error_message,
                    'updated_at': datetime.now(timezone.utc)
                }
            )
            self.db_session.commit()
        except SQLAlchemyError as e:
            logger.warning(f"⚠️ 事务完成日志更新失败: {e}")
            self.db_session.rollback()


# ==================== 缓存一致性管理器 ====================

class CacheConsistencyManager:
    """缓存一致性管理器"""
    
    def __init__(self, redis_client: Redis, event_publisher: 'EventPublisher'):
        self.redis = redis_client
        self.event_publisher = event_publisher
        self.invalidation_patterns = {}  # 缓存失效模式
        
    def register_invalidation_pattern(
        self, 
        event_type: str, 
        cache_pattern: str,
        delay_seconds: int = 0
    ):
        """注册缓存失效模式"""
        if event_type not in self.invalidation_patterns:
            self.invalidation_patterns[event_type] = []
            
        self.invalidation_patterns[event_type].append({
            'pattern': cache_pattern,
            'delay_seconds': delay_seconds
        })
    
    def invalidate_cache_immediate(
        self, 
        cache_keys: List[str], 
        cache_patterns: List[str] = None
    ) -> bool:
        """立即失效缓存"""
        try:
            # 删除指定键
            if cache_keys:
                deleted_count = self.redis.delete(*cache_keys)
                logger.debug(f"✅ 立即删除缓存键: {deleted_count}个")
            
            # 删除模式匹配的键
            if cache_patterns:
                for pattern in cache_patterns:
                    keys = self.redis.keys(pattern)
                    if keys:
                        deleted_count = self.redis.delete(*keys)
                        logger.debug(f"✅ 模式删除缓存键 {pattern}: {deleted_count}个")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 立即缓存失效失败: {e}")
            return False
    
    def invalidate_cache_delayed(
        self, 
        cache_keys: List[str], 
        delay_seconds: int,
        cache_patterns: List[str] = None
    ):
        """延迟失效缓存"""
        try:
            # 创建延迟失效任务
            invalidation_event = CacheInvalidationEvent(
                event_id=str(uuid.uuid4()),
                customer_id=0,  # 全局失效
                invalidation_type=CacheInvalidationType.DELAYED,
                cache_keys=cache_keys,
                cache_patterns=cache_patterns or [],
                delay_seconds=delay_seconds
            )
            
            # 发布延迟事件
            self.event_publisher.publish_event(
                EventMessage(
                    event_id=invalidation_event.event_id,
                    event_type=EventType.CACHE_INVALIDATE,
                    customer_id=0,
                    payload=invalidation_event.__dict__
                ),
                delay_seconds=delay_seconds
            )
            
            logger.debug(f"✅ 创建延迟缓存失效任务: {delay_seconds}秒后执行")
            
        except Exception as e:
            logger.error(f"❌ 创建延迟缓存失效任务失败: {e}")
    
    def invalidate_by_event(self, event_type: str, customer_id: int, context: Dict[str, Any]):
        """根据事件失效缓存"""
        patterns = self.invalidation_patterns.get(event_type, [])
        
        for pattern_config in patterns:
            cache_pattern = pattern_config['pattern']
            delay_seconds = pattern_config['delay_seconds']
            
            # 替换模式中的占位符
            cache_pattern = cache_pattern.format(
                customer_id=customer_id,
                **context
            )
            
            if delay_seconds > 0:
                self.invalidate_cache_delayed([cache_pattern], delay_seconds)
            else:
                self.invalidate_cache_immediate([], [cache_pattern])
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        try:
            info = self.redis.info('stats')
            
            # 计算缓存命中率
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total_requests = hits + misses
            hit_rate = (hits / max(total_requests, 1)) * 100
            
            return {
                'keyspace_hits': hits,
                'keyspace_misses': misses,
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 2),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B')
            }
            
        except Exception as e:
            logger.error(f"❌ 获取缓存统计失败: {e}")
            return {}


# ==================== 事件发布器 ====================

class EventPublisher:
    """事件发布器 - 基于Redis Stream"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.stream_name = "message_events"
        self.consumer_group = "message_processors"
        
        # 确保消费者组存在
        try:
            self.redis.xgroup_create(self.stream_name, self.consumer_group, id='0', mkstream=True)
        except redis.exceptions.ResponseError:
            # 组已存在
            pass
    
    def publish_event(self, event: EventMessage, delay_seconds: int = 0):
        """发布事件"""
        try:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'customer_id': str(event.customer_id),
                'payload': json.dumps(event.payload, default=str),
                'created_at': event.created_at.isoformat(),
                'retry_count': str(event.retry_count),
                'max_retries': str(event.max_retries)
            }
            
            if delay_seconds > 0:
                # 延迟发布：添加到延迟队列
                execute_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
                self.redis.zadd(
                    'delayed_events',
                    {json.dumps(event_data): execute_at.timestamp()}
                )
                logger.debug(f"✅ 事件已添加到延迟队列: {event.event_id}, 延迟: {delay_seconds}秒")
            else:
                # 立即发布
                message_id = self.redis.xadd(self.stream_name, event_data)
                logger.debug(f"✅ 事件已发布: {event.event_id}, 消息ID: {message_id}")
            
        except Exception as e:
            logger.error(f"❌ 事件发布失败: {event.event_id}, 错误: {e}")
            raise
    
    def process_delayed_events(self):
        """处理延迟事件（定时任务调用）"""
        try:
            current_time = datetime.now(timezone.utc).timestamp()
            
            # 获取到期的延迟事件
            ready_events = self.redis.zrangebyscore(
                'delayed_events', 
                '-inf', 
                current_time, 
                withscores=True
            )
            
            for event_data, score in ready_events:
                try:
                    # 发布到消息流
                    event_dict = json.loads(event_data)
                    message_id = self.redis.xadd(self.stream_name, event_dict)
                    
                    # 从延迟队列中移除
                    self.redis.zrem('delayed_events', event_data)
                    
                    logger.debug(f"✅ 延迟事件已发布: {event_dict.get('event_id')}, 消息ID: {message_id}")
                    
                except Exception as e:
                    logger.error(f"❌ 处理延迟事件失败: {e}")
            
        except Exception as e:
            logger.error(f"❌ 处理延迟事件任务失败: {e}")


# ==================== 事件消费器 ====================

class EventConsumer:
    """事件消费器"""
    
    def __init__(
        self, 
        redis_client: Redis, 
        consumer_name: str,
        cache_manager: CacheConsistencyManager,
        transaction_logger: TransactionLogger
    ):
        self.redis = redis_client
        self.consumer_name = consumer_name
        self.cache_manager = cache_manager
        self.transaction_logger = transaction_logger
        self.stream_name = "message_events"
        self.consumer_group = "message_processors"
        self.running = False
        
        # 事件处理器映射
        self.event_handlers = {
            EventType.CACHE_INVALIDATE: self._handle_cache_invalidate,
            EventType.DATA_SYNC: self._handle_data_sync,
            EventType.TRANSACTION_COMMIT: self._handle_transaction_commit,
            EventType.COMPENSATION: self._handle_compensation
        }
    
    def start_consuming(self):
        """开始消费事件"""
        self.running = True
        logger.info(f"🚀 事件消费器启动: {self.consumer_name}")
        
        while self.running:
            try:
                # 读取新消息
                messages = self.redis.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: '>'},
                    count=10,
                    block=5000  # 5秒超时
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        self._process_message(msg_id, fields)
                        
            except KeyboardInterrupt:
                logger.info("⏹️ 收到停止信号，正在优雅停止...")
                break
            except Exception as e:
                logger.error(f"❌ 事件消费失败: {e}")
                time.sleep(1)  # 短暂延迟后重试
        
        logger.info(f"⏹️ 事件消费器已停止: {self.consumer_name}")
    
    def stop_consuming(self):
        """停止消费事件"""
        self.running = False
    
    def _process_message(self, msg_id: str, fields: Dict[str, Any]):
        """处理单个消息"""
        try:
            # 解析消息
            event_type = EventType(fields['event_type'])
            customer_id = int(fields['customer_id'])
            payload = json.loads(fields['payload'])
            retry_count = int(fields.get('retry_count', '0'))
            max_retries = int(fields.get('max_retries', '5'))
            
            logger.debug(f"📨 处理事件: {event_type.value}, ID: {fields['event_id']}")
            
            # 获取处理器
            handler = self.event_handlers.get(event_type)
            if not handler:
                logger.warning(f"⚠️ 未找到事件处理器: {event_type.value}")
                self._ack_message(msg_id)
                return
            
            # 执行处理器
            success = handler(customer_id, payload)
            
            if success:
                # 处理成功，确认消息
                self._ack_message(msg_id)
                logger.debug(f"✅ 事件处理成功: {fields['event_id']}")
            else:
                # 处理失败，检查重试
                if retry_count < max_retries:
                    self._retry_message(fields, retry_count + 1)
                    self._ack_message(msg_id)
                else:
                    # 超过重试次数，移到死信队列
                    self._move_to_dead_letter(fields)
                    self._ack_message(msg_id)
                    logger.error(f"❌ 事件处理最终失败，已移至死信队列: {fields['event_id']}")
                    
        except Exception as e:
            logger.error(f"❌ 消息处理异常: {e}")
            # 不确认消息，等待重新处理
    
    def _handle_cache_invalidate(self, customer_id: int, payload: Dict[str, Any]) -> bool:
        """处理缓存失效事件"""
        try:
            invalidation_type = CacheInvalidationType(payload['invalidation_type'])
            cache_keys = payload.get('cache_keys', [])
            cache_patterns = payload.get('cache_patterns', [])
            
            if invalidation_type == CacheInvalidationType.IMMEDIATE:
                return self.cache_manager.invalidate_cache_immediate(cache_keys, cache_patterns)
            elif invalidation_type == CacheInvalidationType.DELAYED:
                delay_seconds = payload.get('delay_seconds', 0)
                self.cache_manager.invalidate_cache_delayed(cache_keys, delay_seconds, cache_patterns)
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 缓存失效处理失败: {e}")
            return False
    
    def _handle_data_sync(self, customer_id: int, payload: Dict[str, Any]) -> bool:
        """处理数据同步事件"""
        # 这里可以实现具体的数据同步逻辑
        logger.debug(f"📊 数据同步事件: customer_id={customer_id}")
        return True
    
    def _handle_transaction_commit(self, customer_id: int, payload: Dict[str, Any]) -> bool:
        """处理事务提交事件"""
        # 这里可以实现事务提交后的处理逻辑
        logger.debug(f"💾 事务提交事件: customer_id={customer_id}")
        return True
    
    def _handle_compensation(self, customer_id: int, payload: Dict[str, Any]) -> bool:
        """处理补偿事件"""
        # 这里可以实现补偿逻辑
        logger.debug(f"🔄 补偿事件: customer_id={customer_id}")
        return True
    
    def _ack_message(self, msg_id: str):
        """确认消息"""
        try:
            self.redis.xack(self.stream_name, self.consumer_group, msg_id)
        except Exception as e:
            logger.error(f"❌ 消息确认失败: {msg_id}, 错误: {e}")
    
    def _retry_message(self, fields: Dict[str, Any], new_retry_count: int):
        """重试消息"""
        try:
            # 更新重试次数
            fields['retry_count'] = str(new_retry_count)
            
            # 重新发布到流
            self.redis.xadd(self.stream_name, fields)
            
            logger.debug(f"🔄 消息重试: {fields['event_id']}, 第{new_retry_count}次")
            
        except Exception as e:
            logger.error(f"❌ 消息重试失败: {e}")
    
    def _move_to_dead_letter(self, fields: Dict[str, Any]):
        """移动到死信队列"""
        try:
            # 添加失败时间戳
            fields['failed_at'] = datetime.now(timezone.utc).isoformat()
            
            # 移到死信队列
            self.redis.xadd('dead_letter_queue', fields)
            
            logger.warning(f"☠️ 消息已移至死信队列: {fields['event_id']}")
            
        except Exception as e:
            logger.error(f"❌ 死信队列操作失败: {e}")


# ==================== 分布式事务管理器 ====================

class DistributedTransactionManager:
    """分布式事务管理器 - Saga模式实现"""
    
    def __init__(
        self, 
        redis_client: Redis, 
        db_engine: Engine,
        event_publisher: EventPublisher
    ):
        self.redis = redis_client
        self.db_engine = db_engine
        self.event_publisher = event_publisher
        self.Session = sessionmaker(bind=db_engine)
        
        # 组件初始化
        with self.Session() as session:
            self.transaction_logger = TransactionLogger(redis_client, session)
        
        self.cache_manager = CacheConsistencyManager(redis_client, event_publisher)
        
        # 预定义缓存失效模式
        self._setup_cache_invalidation_patterns()
    
    def _setup_cache_invalidation_patterns(self):
        """设置缓存失效模式"""
        # 消息相关缓存失效模式
        self.cache_manager.register_invalidation_pattern(
            'message_created', 
            'message_list:{customer_id}:*'
        )
        self.cache_manager.register_invalidation_pattern(
            'message_acknowledged', 
            'user_unread_count:{customer_id}:*'
        )
        self.cache_manager.register_invalidation_pattern(
            'message_stats_changed', 
            'message_stats:{customer_id}:*',
            delay_seconds=60  # 延迟1分钟失效
        )
    
    def create_transaction(
        self, 
        customer_id: int,
        transaction_type: str,
        steps: List[TransactionStep],
        context: Dict[str, Any] = None
    ) -> DistributedTransaction:
        """创建分布式事务"""
        transaction = DistributedTransaction(
            transaction_id=str(uuid.uuid4()),
            customer_id=customer_id,
            transaction_type=transaction_type,
            steps=steps,
            context=context or {}
        )
        
        # 记录事务开始
        with self.Session() as session:
            logger = TransactionLogger(self.redis, session)
            logger.log_transaction_start(transaction)
        
        return transaction
    
    async def execute_transaction(self, transaction: DistributedTransaction) -> bool:
        """执行分布式事务（异步）"""
        logger.info(f"🚀 开始执行分布式事务: {transaction.transaction_id}")
        
        transaction.state = TransactionState.PROCESSING
        executed_steps = []
        
        try:
            # 按依赖关系排序步骤
            sorted_steps = self._sort_steps_by_dependencies(transaction.steps)
            
            # 逐步执行
            for step in sorted_steps:
                logger.debug(f"🔧 执行步骤: {step.step_name}")
                
                # 记录步骤开始
                with self.Session() as session:
                    step_logger = TransactionLogger(self.redis, session)
                    step_logger.log_transaction_step(
                        transaction.transaction_id, 
                        step.step_id, 
                        'executing'
                    )
                
                # 执行步骤（带重试）
                success, result = await self._execute_step_with_retry(step, transaction.context)
                
                if success:
                    executed_steps.append(step)
                    
                    # 记录步骤成功
                    with self.Session() as session:
                        step_logger = TransactionLogger(self.redis, session)
                        step_logger.log_transaction_step(
                            transaction.transaction_id, 
                            step.step_id, 
                            'completed',
                            result=result
                        )
                    
                    logger.debug(f"✅ 步骤执行成功: {step.step_name}")
                else:
                    # 步骤失败，开始补偿
                    logger.error(f"❌ 步骤执行失败: {step.step_name}")
                    
                    # 记录步骤失败
                    with self.Session() as session:
                        step_logger = TransactionLogger(self.redis, session)
                        step_logger.log_transaction_step(
                            transaction.transaction_id, 
                            step.step_id, 
                            'failed',
                            error=str(result)
                        )
                    
                    # 执行补偿
                    await self._compensate_transaction(transaction, executed_steps)
                    return False
            
            # 所有步骤成功
            transaction.state = TransactionState.COMPLETED
            transaction.end_time = datetime.now(timezone.utc)
            
            # 记录事务完成
            with self.Session() as session:
                logger = TransactionLogger(self.redis, session)
                logger.log_transaction_complete(transaction)
            
            # 发布事务完成事件
            await self._publish_transaction_event(transaction, EventType.TRANSACTION_COMMIT)
            
            logger.info(f"✅ 分布式事务执行成功: {transaction.transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 分布式事务执行异常: {transaction.transaction_id}, 错误: {e}")
            
            transaction.state = TransactionState.FAILED
            transaction.end_time = datetime.now(timezone.utc)
            transaction.error_message = str(e)
            
            # 执行补偿
            await self._compensate_transaction(transaction, executed_steps)
            return False
    
    async def _execute_step_with_retry(
        self, 
        step: TransactionStep, 
        context: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """带重试的步骤执行"""
        for attempt in range(step.max_retries + 1):
            try:
                # 执行步骤
                if asyncio.iscoroutinefunction(step.action):
                    result = await step.action(context)
                else:
                    result = step.action(context)
                
                return True, result
                
            except Exception as e:
                step.retry_count = attempt + 1
                
                if attempt < step.max_retries:
                    logger.warning(f"⚠️ 步骤执行失败，准备重试: {step.step_name}, 第{attempt + 1}次重试")
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"❌ 步骤执行最终失败: {step.step_name}, 错误: {e}")
                    return False, str(e)
        
        return False, "重试次数超限"
    
    async def _compensate_transaction(
        self, 
        transaction: DistributedTransaction, 
        executed_steps: List[TransactionStep]
    ):
        """补偿事务"""
        logger.info(f"🔄 开始补偿事务: {transaction.transaction_id}")
        
        transaction.state = TransactionState.COMPENSATING
        
        # 按相反顺序执行补偿
        for step in reversed(executed_steps):
            if step.compensation:
                try:
                    logger.debug(f"🔄 执行补偿: {step.step_name}")
                    
                    if asyncio.iscoroutinefunction(step.compensation):
                        await step.compensation(transaction.context)
                    else:
                        step.compensation(transaction.context)
                    
                    logger.debug(f"✅ 补偿执行成功: {step.step_name}")
                    
                except Exception as e:
                    logger.error(f"❌ 补偿执行失败: {step.step_name}, 错误: {e}")
        
        transaction.state = TransactionState.COMPENSATED
        transaction.end_time = datetime.now(timezone.utc)
        
        # 记录事务补偿完成
        with self.Session() as session:
            logger = TransactionLogger(self.redis, session)
            logger.log_transaction_complete(transaction)
        
        # 发布补偿事件
        await self._publish_transaction_event(transaction, EventType.COMPENSATION)
        
        logger.info(f"✅ 事务补偿完成: {transaction.transaction_id}")
    
    def _sort_steps_by_dependencies(self, steps: List[TransactionStep]) -> List[TransactionStep]:
        """按依赖关系排序步骤（拓扑排序）"""
        # 简化实现：如果没有依赖关系，按原顺序返回
        # 实际实现应该包含完整的拓扑排序算法
        return steps
    
    async def _publish_transaction_event(
        self, 
        transaction: DistributedTransaction, 
        event_type: EventType
    ):
        """发布事务事件"""
        try:
            event = EventMessage(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                customer_id=transaction.customer_id,
                payload={
                    'transaction_id': transaction.transaction_id,
                    'transaction_type': transaction.transaction_type,
                    'state': transaction.state.value,
                    'context': transaction.context
                }
            )
            
            self.event_publisher.publish_event(event)
            
            # 触发缓存失效
            self.cache_manager.invalidate_by_event(
                f"{transaction.transaction_type}_{event_type.value}",
                transaction.customer_id,
                transaction.context
            )
            
        except Exception as e:
            logger.error(f"❌ 事务事件发布失败: {e}")
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """获取事务状态"""
        try:
            # 从Redis获取快速状态
            transaction_data = self.redis.hgetall(f"transaction_log:{transaction_id}")
            
            if transaction_data:
                # 获取步骤详情
                steps_data = self.redis.lrange(f"transaction_steps:{transaction_id}", 0, -1)
                steps = [json.loads(step) for step in steps_data]
                
                return {
                    'transaction_id': transaction_id,
                    'state': transaction_data.get('state'),
                    'start_time': transaction_data.get('start_time'),
                    'end_time': transaction_data.get('end_time'),
                    'duration_ms': transaction_data.get('duration_ms'),
                    'error_message': transaction_data.get('error_message'),
                    'steps': steps
                }
            
            return {'error': 'Transaction not found'}
            
        except Exception as e:
            logger.error(f"❌ 获取事务状态失败: {e}")
            return {'error': str(e)}


# ==================== 工厂函数 ====================

def create_distributed_transaction_manager(
    redis_client: Redis,
    db_engine: Engine
) -> DistributedTransactionManager:
    """创建分布式事务管理器"""
    
    # 创建事件发布器
    event_publisher = EventPublisher(redis_client)
    
    # 创建事务管理器
    manager = DistributedTransactionManager(redis_client, db_engine, event_publisher)
    
    return manager


def create_event_consumer(
    redis_client: Redis,
    db_engine: Engine,
    consumer_name: str = None
) -> EventConsumer:
    """创建事件消费器"""
    
    if not consumer_name:
        consumer_name = f"consumer_{uuid.uuid4().hex[:8]}"
    
    # 创建组件
    event_publisher = EventPublisher(redis_client)
    cache_manager = CacheConsistencyManager(redis_client, event_publisher)
    
    with sessionmaker(bind=db_engine)() as session:
        transaction_logger = TransactionLogger(redis_client, session)
    
    # 创建消费器
    consumer = EventConsumer(
        redis_client, 
        consumer_name,
        cache_manager,
        transaction_logger
    )
    
    return consumer


# ==================== 使用示例 ====================

if __name__ == "__main__":
    import redis
    from sqlalchemy import create_engine
    
    # 创建Redis客户端
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # 创建数据库引擎
    db_engine = create_engine('sqlite:///distributed_transaction.db', echo=True)
    
    # 创建分布式事务管理器
    manager = create_distributed_transaction_manager(redis_client, db_engine)
    
    print("✅ 分布式事务和缓存一致性管理器创建成功")
    print("主要功能:")
    print("1. 🔄 分布式事务协调（Saga模式）")
    print("2. 💾 最终一致性保证")
    print("3. 🗄️ 缓存失效策略")
    print("4. 🔧 补偿机制")
    print("5. 📡 事件驱动架构")
    print("6. ☠️ 死信队列处理")