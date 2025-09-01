#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康数据缓存优化服务
Health Data Cache Optimization Service

提供高性能的Redis缓存机制，优化健康数据访问性能
- 基线数据缓存：减少数据库查询
- 评分结果缓存：加快健康评分计算
- 预计算缓存：预先计算常用统计数据
- 分级缓存策略：根据数据访问频率分级缓存

Author: System
Date: 2025-09-01
Version: 1.0
"""

import json
import logging
import hashlib
import pickle
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Union, Tuple
from functools import wraps
import redis.asyncio as redis
import redis as redis_sync
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .models import db, UserHealthData, HealthBaseline, UserHealthProfile, AlertInfo
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

logger = logging.getLogger(__name__)

class HealthCacheService:
    """健康数据缓存优化服务"""
    
    def __init__(self, redis_url=None):
        """初始化缓存服务"""
        self.redis_url = redis_url or Config.REDIS_URL or "redis://default:123456@localhost:6379/1"
        self.redis_client = None
        self.redis_sync_client = None
        
        # 缓存配置
        self.cache_config = {
            # 基线数据缓存 - 相对稳定，较长过期时间
            'baseline': {
                'prefix': 'health:baseline:',
                'ttl': 3600 * 24,  # 24小时
                'enable_compression': True
            },
            # 健康评分缓存 - 需要定期更新
            'health_score': {
                'prefix': 'health:score:',
                'ttl': 3600 * 2,   # 2小时
                'enable_compression': True
            },
            # 用户健康数据缓存 - 频繁访问，短期缓存
            'user_data': {
                'prefix': 'health:data:',
                'ttl': 1800,       # 30分钟
                'enable_compression': False
            },
            # 画像数据缓存 - 中等频率访问
            'profile': {
                'prefix': 'health:profile:',
                'ttl': 3600 * 6,   # 6小时
                'enable_compression': True
            },
            # 预计算统计缓存 - 长期缓存
            'statistics': {
                'prefix': 'health:stats:',
                'ttl': 3600 * 12,  # 12小时
                'enable_compression': True
            },
            # 热点数据缓存 - 极短期高频访问
            'hotspot': {
                'prefix': 'health:hot:',
                'ttl': 300,        # 5分钟
                'enable_compression': False
            }
        }
        
        # 性能统计
        self.performance_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_writes': 0,
            'cache_errors': 0
        }
        
        # 预热配置
        self.warmup_config = {
            'enable_auto_warmup': True,
            'warmup_interval': 3600,  # 1小时预热一次
            'warmup_batch_size': 100,
            'warmup_concurrent_limit': 10
        }

    async def initialize(self):
        """初始化Redis连接"""
        try:
            # 异步连接
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 同步连接（用于某些同步操作）
            self.redis_sync_client = redis_sync.from_url(
                self.redis_url,
                encoding="utf-8", 
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("✅ Redis 缓存服务初始化成功")
            
            # 启动自动预热
            if self.warmup_config['enable_auto_warmup']:
                asyncio.create_task(self._auto_warmup_loop())
                
        except Exception as e:
            logger.error(f"❌ Redis 缓存服务初始化失败: {e}")
            raise

    def _generate_cache_key(self, cache_type: str, identifier: str, **kwargs) -> str:
        """生成缓存键"""
        config = self.cache_config.get(cache_type, {})
        prefix = config.get('prefix', f'health:{cache_type}:')
        
        # 添加额外参数到键名
        if kwargs:
            params_str = "&".join([f"{k}={v}" for k, v in sorted(kwargs.items())])
            identifier = f"{identifier}?{params_str}"
        
        return f"{prefix}{identifier}"

    def _serialize_data(self, data: Any, enable_compression: bool = False) -> str:
        """序列化数据"""
        try:
            if enable_compression:
                # 使用pickle进行压缩序列化
                serialized = pickle.dumps(data)
                import gzip
                compressed = gzip.compress(serialized)
                # 标记为压缩数据
                return f"compressed:{compressed.hex()}"
            else:
                # JSON序列化
                return json.dumps(data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"数据序列化失败: {e}")
            return json.dumps({"error": "serialization_failed"})

    def _deserialize_data(self, data_str: str) -> Any:
        """反序列化数据"""
        try:
            if data_str.startswith("compressed:"):
                # 解压缩数据
                compressed_hex = data_str[11:]
                compressed = bytes.fromhex(compressed_hex)
                import gzip
                serialized = gzip.decompress(compressed)
                return pickle.loads(serialized)
            else:
                # JSON反序列化
                return json.loads(data_str)
        except Exception as e:
            logger.error(f"数据反序列化失败: {e}")
            return None

    async def get_cached_data(self, cache_type: str, identifier: str, **kwargs) -> Optional[Any]:
        """获取缓存数据"""
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            cached_str = await self.redis_client.get(cache_key)
            
            if cached_str:
                self.performance_stats['cache_hits'] += 1
                return self._deserialize_data(cached_str)
            else:
                self.performance_stats['cache_misses'] += 1
                return None
                
        except Exception as e:
            logger.error(f"缓存读取失败 [{cache_type}:{identifier}]: {e}")
            self.performance_stats['cache_errors'] += 1
            return None

    async def set_cached_data(self, cache_type: str, identifier: str, data: Any, 
                            custom_ttl: Optional[int] = None, **kwargs) -> bool:
        """设置缓存数据"""
        try:
            config = self.cache_config.get(cache_type, {})
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            ttl = custom_ttl or config.get('ttl', 3600)
            enable_compression = config.get('enable_compression', False)
            
            serialized_data = self._serialize_data(data, enable_compression)
            
            await self.redis_client.setex(cache_key, ttl, serialized_data)
            self.performance_stats['cache_writes'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"缓存写入失败 [{cache_type}:{identifier}]: {e}")
            self.performance_stats['cache_errors'] += 1
            return False

    async def invalidate_cache(self, cache_type: str, pattern: str = "*") -> int:
        """失效缓存"""
        try:
            config = self.cache_config.get(cache_type, {})
            prefix = config.get('prefix', f'health:{cache_type}:')
            
            keys_pattern = f"{prefix}{pattern}"
            keys = await self.redis_client.keys(keys_pattern)
            
            if keys:
                deleted_count = await self.redis_client.delete(*keys)
                logger.info(f"失效缓存 [{cache_type}]: {deleted_count} 个键")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"缓存失效失败 [{cache_type}:{pattern}]: {e}")
            return 0

    # ==================== 健康基线缓存 ====================
    
    async def get_cached_baseline(self, user_id: int, customer_id: int, 
                                baseline_type: str = "personal") -> Optional[Dict]:
        """获取缓存的健康基线"""
        identifier = f"{user_id}:{customer_id}:{baseline_type}"
        return await self.get_cached_data('baseline', identifier)

    async def cache_health_baseline(self, user_id: int, customer_id: int, 
                                  baseline_data: Dict, baseline_type: str = "personal") -> bool:
        """缓存健康基线数据"""
        identifier = f"{user_id}:{customer_id}:{baseline_type}"
        return await self.set_cached_data('baseline', identifier, baseline_data)

    # ==================== 健康评分缓存 ====================
    
    async def get_cached_health_score(self, user_id: int, customer_id: int, 
                                    score_date: Optional[str] = None) -> Optional[Dict]:
        """获取缓存的健康评分"""
        date_str = score_date or datetime.now().strftime("%Y-%m-%d")
        identifier = f"{user_id}:{customer_id}:{date_str}"
        return await self.get_cached_data('health_score', identifier)

    async def cache_health_score(self, user_id: int, customer_id: int, 
                               score_data: Dict, score_date: Optional[str] = None) -> bool:
        """缓存健康评分数据"""
        date_str = score_date or datetime.now().strftime("%Y-%m-%d")
        identifier = f"{user_id}:{customer_id}:{date_str}"
        return await self.set_cached_data('health_score', identifier, score_data)

    # ==================== 用户健康数据缓存 ====================
    
    async def get_cached_user_health_data(self, user_id: int, customer_id: int, 
                                        days_back: int = 30) -> Optional[List[Dict]]:
        """获取缓存的用户健康数据"""
        identifier = f"{user_id}:{customer_id}:days{days_back}"
        return await self.get_cached_data('user_data', identifier)

    async def cache_user_health_data(self, user_id: int, customer_id: int, 
                                   health_data: List[Dict], days_back: int = 30) -> bool:
        """缓存用户健康数据"""
        identifier = f"{user_id}:{customer_id}:days{days_back}"
        return await self.set_cached_data('user_data', identifier, health_data)

    # ==================== 健康画像缓存 ====================
    
    async def get_cached_health_profile(self, user_id: int, customer_id: int) -> Optional[Dict]:
        """获取缓存的健康画像"""
        identifier = f"{user_id}:{customer_id}"
        return await self.get_cached_data('profile', identifier)

    async def cache_health_profile(self, user_id: int, customer_id: int, 
                                 profile_data: Dict) -> bool:
        """缓存健康画像数据"""
        identifier = f"{user_id}:{customer_id}"
        return await self.set_cached_data('profile', identifier, profile_data)

    # ==================== 预计算统计缓存 ====================
    
    async def get_cached_statistics(self, stat_type: str, customer_id: int, 
                                  **filters) -> Optional[Dict]:
        """获取缓存的统计数据"""
        identifier = f"{stat_type}:{customer_id}"
        return await self.get_cached_data('statistics', identifier, **filters)

    async def cache_statistics(self, stat_type: str, customer_id: int, 
                             stats_data: Dict, **filters) -> bool:
        """缓存统计数据"""
        identifier = f"{stat_type}:{customer_id}"
        return await self.set_cached_data('statistics', identifier, stats_data, **filters)

    # ==================== 缓存预热策略 ====================
    
    async def warmup_user_cache(self, user_id: int, customer_id: int) -> bool:
        """预热用户相关缓存"""
        try:
            # 预热任务列表
            warmup_tasks = []
            
            # 1. 预热健康基线数据
            warmup_tasks.append(self._warmup_baseline_data(user_id, customer_id))
            
            # 2. 预热近期健康数据
            warmup_tasks.append(self._warmup_health_data(user_id, customer_id))
            
            # 3. 预热健康评分
            warmup_tasks.append(self._warmup_health_score(user_id, customer_id))
            
            # 并发执行预热任务
            results = await asyncio.gather(*warmup_tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            logger.info(f"用户 {user_id} 缓存预热完成: {success_count}/{len(warmup_tasks)} 成功")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"用户缓存预热失败 [{user_id}]: {e}")
            return False

    async def _warmup_baseline_data(self, user_id: int, customer_id: int) -> bool:
        """预热基线数据"""
        try:
            # 检查缓存是否存在
            cached = await self.get_cached_baseline(user_id, customer_id)
            if cached:
                return True
                
            # 从数据库加载基线数据
            baseline_query = db.session.query(HealthBaseline).filter(
                HealthBaseline.user_id == user_id,
                HealthBaseline.customer_id == customer_id,
                HealthBaseline.is_current == 1,
                HealthBaseline.is_deleted == 0
            )
            
            baselines = baseline_query.all()
            
            if baselines:
                baseline_data = {}
                for baseline in baselines:
                    baseline_data[baseline.feature_name] = {
                        'mean_value': float(baseline.mean_value) if baseline.mean_value else 0,
                        'std_dev': float(baseline.std_dev) if baseline.std_dev else 0,
                        'min_value': float(baseline.min_value) if baseline.min_value else 0,
                        'max_value': float(baseline.max_value) if baseline.max_value else 0,
                        'baseline_date': baseline.baseline_date.strftime("%Y-%m-%d") if baseline.baseline_date else None,
                        'confidence_level': float(baseline.confidence_level) if baseline.confidence_level else 0.95
                    }
                
                await self.cache_health_baseline(user_id, customer_id, baseline_data)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"基线数据预热失败: {e}")
            return False

    async def _warmup_health_data(self, user_id: int, customer_id: int, days_back: int = 30) -> bool:
        """预热健康数据"""
        try:
            # 检查缓存是否存在
            cached = await self.get_cached_user_health_data(user_id, customer_id, days_back)
            if cached:
                return True
                
            # 从数据库加载健康数据
            start_date = datetime.now() - timedelta(days=days_back)
            
            health_query = db.session.query(UserHealthData).filter(
                UserHealthData.user_id == user_id,
                UserHealthData.customer_id == customer_id,
                UserHealthData.create_time >= start_date,
                UserHealthData.is_deleted == 0
            ).order_by(UserHealthData.create_time.desc()).limit(1000)
            
            health_records = health_query.all()
            
            if health_records:
                health_data = []
                for record in health_records:
                    health_data.append({
                        'id': record.id,
                        'heart_rate': record.heart_rate,
                        'blood_pressure_systolic': record.blood_pressure_systolic,
                        'blood_pressure_diastolic': record.blood_pressure_diastolic,
                        'spo2': record.spo2,
                        'temperature': record.temperature,
                        'step_count': record.step_count,
                        'create_time': record.create_time.isoformat() if record.create_time else None,
                        'device_sn': record.device_sn
                    })
                
                await self.cache_user_health_data(user_id, customer_id, health_data, days_back)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"健康数据预热失败: {e}")
            return False

    async def _warmup_health_score(self, user_id: int, customer_id: int) -> bool:
        """预热健康评分"""
        try:
            # 检查缓存是否存在
            today = datetime.now().strftime("%Y-%m-%d")
            cached = await self.get_cached_health_score(user_id, customer_id, today)
            if cached:
                return True
                
            # 从数据库加载最新健康画像
            profile_query = db.session.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id,
                UserHealthProfile.customer_id == customer_id,
                UserHealthProfile.is_deleted == 0
            ).order_by(UserHealthProfile.profile_date.desc()).first()
            
            if profile_query:
                score_data = {
                    'overall_health_score': float(profile_query.overall_health_score) if profile_query.overall_health_score else 0.0,
                    'health_level': profile_query.health_level,
                    'physiological_score': float(profile_query.physiological_score) if profile_query.physiological_score else 0.0,
                    'behavioral_score': float(profile_query.behavioral_score) if profile_query.behavioral_score else 0.0,
                    'risk_factor_score': float(profile_query.risk_factor_score) if profile_query.risk_factor_score else 0.0,
                    'profile_date': profile_query.profile_date.strftime("%Y-%m-%d") if profile_query.profile_date else today,
                    'last_updated': datetime.now().isoformat()
                }
                
                await self.cache_health_score(user_id, customer_id, score_data, today)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"健康评分预热失败: {e}")
            return False

    async def _auto_warmup_loop(self):
        """自动预热循环"""
        while True:
            try:
                await asyncio.sleep(self.warmup_config['warmup_interval'])
                
                logger.info("开始自动缓存预热...")
                
                # 获取活跃用户列表（最近7天有数据的用户）
                seven_days_ago = datetime.now() - timedelta(days=7)
                
                active_users_query = db.session.query(
                    UserHealthData.user_id,
                    UserHealthData.customer_id
                ).filter(
                    UserHealthData.create_time >= seven_days_ago,
                    UserHealthData.is_deleted == 0
                ).distinct().limit(self.warmup_config['warmup_batch_size'])
                
                active_users = active_users_query.all()
                
                if active_users:
                    # 限制并发数量
                    semaphore = asyncio.Semaphore(self.warmup_config['warmup_concurrent_limit'])
                    
                    async def warmup_with_semaphore(user_info):
                        async with semaphore:
                            return await self.warmup_user_cache(user_info.user_id, user_info.customer_id)
                    
                    tasks = [warmup_with_semaphore(user) for user in active_users]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    success_count = sum(1 for result in results if result is True)
                    logger.info(f"自动预热完成: {success_count}/{len(active_users)} 用户预热成功")
                
            except Exception as e:
                logger.error(f"自动预热循环异常: {e}")

    # ==================== 缓存性能监控 ====================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取缓存性能统计"""
        total_requests = self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']
        hit_rate = (self.performance_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.performance_stats['cache_hits'],
            'cache_misses': self.performance_stats['cache_misses'],
            'cache_writes': self.performance_stats['cache_writes'],
            'cache_errors': self.performance_stats['cache_errors'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'error_rate_percent': round(
                (self.performance_stats['cache_errors'] / total_requests * 100) if total_requests > 0 else 0, 2
            )
        }

    async def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存状态信息"""
        try:
            info = await self.redis_client.info()
            memory_info = {
                'used_memory_human': info.get('used_memory_human', 'N/A'),
                'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
                'total_system_memory_human': info.get('total_system_memory_human', 'N/A')
            }
            
            # 统计各类型缓存的键数量
            key_counts = {}
            for cache_type, config in self.cache_config.items():
                prefix = config['prefix']
                keys = await self.redis_client.keys(f"{prefix}*")
                key_counts[cache_type] = len(keys)
            
            return {
                'memory_info': memory_info,
                'key_counts': key_counts,
                'connected_clients': info.get('connected_clients', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'performance_stats': self.get_performance_stats()
            }
            
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {'error': str(e)}

    # ==================== 缓存装饰器 ====================
    
    def cache_result(self, cache_type: str, ttl: Optional[int] = None, 
                    key_func: Optional[callable] = None):
        """缓存结果装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # 默认键生成策略
                    key_parts = [func.__name__] + [str(arg) for arg in args]
                    cache_key = ":".join(key_parts)
                
                # 尝试从缓存获取
                cached_result = await self.get_cached_data(cache_type, cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 缓存结果
                if result is not None:
                    await self.set_cached_data(cache_type, cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

    async def close(self):
        """关闭缓存连接"""
        try:
            if self.redis_client:
                await self.redis_client.close()
            if self.redis_sync_client:
                self.redis_sync_client.close()
            logger.info("✅ Redis 缓存连接已关闭")
        except Exception as e:
            logger.error(f"❌ 关闭Redis连接失败: {e}")


# 全局缓存服务实例
health_cache_service = HealthCacheService()

# 便捷的装饰器实例
cache_baseline = health_cache_service.cache_result('baseline', ttl=3600*24)
cache_health_score = health_cache_service.cache_result('health_score', ttl=3600*2)
cache_user_data = health_cache_service.cache_result('user_data', ttl=1800)
cache_statistics = health_cache_service.cache_result('statistics', ttl=3600*12)


if __name__ == "__main__":
    # 测试缓存服务
    import asyncio
    
    async def test_cache_service():
        """测试缓存服务"""
        try:
            # 初始化
            await health_cache_service.initialize()
            
            # 测试基本缓存操作
            test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
            
            # 写入测试
            success = await health_cache_service.set_cached_data('user_data', 'test_key', test_data)
            print(f"缓存写入测试: {'成功' if success else '失败'}")
            
            # 读取测试
            cached_data = await health_cache_service.get_cached_data('user_data', 'test_key')
            print(f"缓存读取测试: {'成功' if cached_data == test_data else '失败'}")
            
            # 性能统计
            stats = health_cache_service.get_performance_stats()
            print(f"性能统计: {stats}")
            
            # 缓存信息
            info = await health_cache_service.get_cache_info()
            print(f"缓存信息: {info}")
            
            print("✅ 缓存服务测试完成")
            
        except Exception as e:
            print(f"❌ 缓存服务测试失败: {e}")
        finally:
            await health_cache_service.close()
    
    # 运行测试
    asyncio.run(test_cache_service())