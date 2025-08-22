#!/usr/bin/env python3
"""
通用事件批量处理器 v2.0
CPU自适应高性能批处理系统，专门处理upload_common_event接口数据
"""

import threading
import queue
import time
import json
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from .redis_helper import RedisHelper
from .time_config import get_now
import logging
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import pymysql
from .models import db, AlertInfo, AlertRules
from sqlalchemy import and_

class CommonEventBatchProcessor:
    """CPU自适应通用事件批量处理器"""
    
    def __init__(self, app=None):
        # 系统信息检测
        self.cpu_cores = psutil.cpu_count(logical=True)
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # CPU自适应配置
        self.batch_size = self._calculate_optimal_batch_size()
        self.max_workers = self._calculate_optimal_workers()
        self.max_wait_time = 1.5  # 通用事件响应要求较高
        
        # 队列和线程管理
        self.event_queue = queue.Queue(maxsize=5000)
        self.redis = RedisHelper()
        self.running = False
        self.workers = []
        
        # 性能统计
        self.stats = {
            'processed': 0,
            'failed': 0, 
            'queued': 0,
            'batch_count': 0,
            'avg_processing_time': 0.0,
            'last_adjustment_time': time.time()
        }
        
        # 性能监控
        self.performance_window = []
        self.adjustment_interval = 30  # 30秒调整一次
        
        self.logger = logging.getLogger(__name__)
        self.app = app
        
        # 已处理事件去重
        self.processed_keys = set()
        
        self.logger.info(f"🚀 CommonEventBatchProcessor初始化:")
        self.logger.info(f"   CPU核心: {self.cpu_cores}")
        self.logger.info(f"   内存: {self.memory_gb:.1f}GB") 
        self.logger.info(f"   批次大小: {self.batch_size}")
        self.logger.info(f"   工作线程: {self.max_workers}")
    
    def _calculate_optimal_batch_size(self) -> int:
        """计算CPU自适应批次大小"""
        # 基础批次大小：CPU核心数 × 8（通用事件相对简单）
        base_size = self.cpu_cores * 8
        
        # 内存调整系数
        memory_factor = min(1.5, self.memory_gb / 8.0)  # 8GB为基准
        
        # 最终批次大小
        batch_size = int(base_size * memory_factor)
        
        return max(10, min(200, batch_size))  # 限制在10-200之间
    
    def _calculate_optimal_workers(self) -> int:
        """计算最优工作线程数"""
        # 通用事件处理：CPU核心数 × 1（主要是数据库I/O）
        workers = max(2, min(16, self.cpu_cores))
        
        return workers
    
    def start(self):
        """启动批量处理器"""
        if self.running:
            return
            
        self.running = True
        self.start_time = time.time()
        
        # 启动工作线程
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread, 
                name=f'CommonEventWorker-{i}',
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        # 启动性能监控线程
        monitor_thread = threading.Thread(
            target=self._performance_monitor,
            name='CommonEventMonitor',
            daemon=True
        )
        monitor_thread.start()
        
        self.logger.info(f"🎯 通用事件批处理器启动完成，工作线程数: {self.max_workers}")
    
    def stop(self):
        """停止批量处理器"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        self.logger.info("⛔ 通用事件批处理器已停止")
    
    def submit(self, event_data: Dict[str, Any]) -> bool:
        """提交通用事件数据到处理队列"""
        try:
            # 生成事件唯一键
            device_sn = event_data.get('deviceSn', '')
            event_type = event_data.get('eventType', '')
            timestamp = event_data.get('timestamp', get_now().strftime('%Y-%m-%d %H:%M:%S'))
            
            event_key = f"{device_sn}:{event_type}:{timestamp}"
            
            # 去重检查
            if event_key in self.processed_keys:
                self.logger.debug(f"⚠️ 重复事件跳过: {event_key}")
                return True
            
            # 添加处理标识
            enriched_data = {
                **event_data,
                'event_key': event_key,
                'submit_time': time.time()
            }
            
            # 提交到队列
            self.event_queue.put(enriched_data, timeout=0.1)
            self.stats['queued'] += 1
            
            return True
            
        except queue.Full:
            self.logger.warning("❌ 通用事件队列已满，数据丢弃")
            return False
        except Exception as e:
            self.logger.error(f"❌ 提交通用事件失败: {e}")
            return False
    
    def _worker_thread(self):
        """工作线程主循环"""
        batch_buffer = []
        last_process_time = time.time()
        
        while self.running:
            try:
                # 尝试获取数据
                try:
                    event_data = self.event_queue.get(timeout=0.5)
                    batch_buffer.append(event_data)
                except queue.Empty:
                    pass
                
                # 检查批处理条件
                current_time = time.time()
                should_process = (
                    len(batch_buffer) >= self.batch_size or  # 达到批次大小
                    (batch_buffer and current_time - last_process_time >= self.max_wait_time)  # 超时
                )
                
                if should_process and batch_buffer:
                    success = self._process_batch(batch_buffer)
                    if success:
                        # 标记已处理
                        for event in batch_buffer:
                            self.processed_keys.add(event.get('event_key', ''))
                    
                    batch_buffer.clear()
                    last_process_time = current_time
                    
            except Exception as e:
                self.logger.error(f"❌ 工作线程异常: {e}")
                batch_buffer.clear()
                time.sleep(1)
    
    def _process_batch(self, batch_events: List[Dict[str, Any]]) -> bool:
        """批量处理通用事件"""
        start_time = time.time()
        
        try:
            if not self.app:
                self.logger.error("❌ Flask应用实例未设置")
                return False
            
            with self.app.app_context():
                alerts_to_create = []
                
                for event_data in batch_events:
                    try:
                        alert = self._create_alert_from_event(event_data)
                        if alert:
                            alerts_to_create.append(alert)
                    except Exception as e:
                        self.logger.error(f"❌ 处理单个事件失败: {e}")
                        continue
                
                # 批量插入告警记录
                if alerts_to_create:
                    try:
                        db.session.bulk_save_objects(alerts_to_create)
                        db.session.commit()
                        
                        # 更新统计信息
                        processing_time = time.time() - start_time
                        self._update_performance_stats(len(batch_events), processing_time)
                        
                        self.logger.info(f"✅ 批量处理通用事件成功: {len(alerts_to_create)}条告警, "
                                       f"耗时: {processing_time:.2f}秒")
                        return True
                        
                    except Exception as e:
                        self.logger.error(f"❌ 批量插入告警失败: {e}")
                        db.session.rollback()
                        return False
                else:
                    self.logger.info("⚠️ 无有效告警需要创建")
                    return True
                    
        except Exception as e:
            self.logger.error(f"❌ 批量处理异常: {e}")
            return False
    
    def _create_alert_from_event(self, event_data: Dict[str, Any]) -> Optional[AlertInfo]:
        """从事件数据创建告警记录"""
        try:
            # 提取事件类型
            event_type = event_data.get('eventType', '').split('.')[-1]
            device_sn = event_data.get('deviceSn', '')
            
            if not event_type or not device_sn:
                return None
            
            # 查询告警规则
            rule = AlertRules.query.filter_by(
                rule_type=event_type, 
                is_deleted=False
            ).first()
            
            if not rule:
                self.logger.debug(f"⚠️ 未找到事件类型的告警规则: {event_type}")
                return None
            
            # 获取设备用户组织信息
            device_user_org = self._get_device_user_org_info(device_sn)
            
            # 创建告警记录
            alert = AlertInfo(
                rule_id=rule.id,
                alert_type=event_type,
                device_sn=device_sn,
                alert_desc=f"{rule.alert_message}(事件值:{event_data.get('eventValue', '')})",
                severity_level=rule.severity_level,
                latitude=event_data.get('latitude', 22.54036796),
                longitude=event_data.get('longitude', 114.01508952),
                altitude=event_data.get('altitude', 0),
                org_id=device_user_org.get('org_id') if device_user_org.get('success') else None,
                user_id=device_user_org.get('user_id') if device_user_org.get('success') else None,
                alert_timestamp=event_data.get('timestamp', get_now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            return alert
            
        except Exception as e:
            self.logger.error(f"❌ 创建告警记录失败: {e}")
            return None
    
    def _get_device_user_org_info(self, device_sn: str) -> Dict[str, Any]:
        """获取设备用户组织信息"""
        try:
            # 这里应该调用实际的设备信息查询逻辑
            # 暂时返回默认值
            return {
                'success': True,
                'org_id': 1,
                'user_id': 1
            }
        except Exception as e:
            self.logger.error(f"❌ 获取设备信息失败: {e}")
            return {'success': False}
    
    def _update_performance_stats(self, batch_size: int, processing_time: float):
        """更新性能统计信息"""
        self.stats['processed'] += batch_size
        self.stats['batch_count'] += 1
        
        # 计算平均处理时间
        total_time = self.stats['avg_processing_time'] * (self.stats['batch_count'] - 1)
        self.stats['avg_processing_time'] = (total_time + processing_time) / self.stats['batch_count']
        
        # 记录性能数据
        self.performance_window.append({
            'batch_size': batch_size,
            'processing_time': processing_time,
            'throughput': batch_size / processing_time if processing_time > 0 else 0,
            'timestamp': time.time()
        })
        
        # 保持性能窗口大小
        if len(self.performance_window) > 100:
            self.performance_window.pop(0)
    
    def _performance_monitor(self):
        """性能监控和自动调优"""
        while self.running:
            try:
                time.sleep(self.adjustment_interval)
                
                if len(self.performance_window) >= 5:
                    self._auto_adjust_configuration()
                
                # 清理过期的处理键
                self._cleanup_processed_keys()
                
            except Exception as e:
                self.logger.error(f"❌ 性能监控异常: {e}")
    
    def _auto_adjust_configuration(self):
        """自动调整配置参数"""
        if len(self.performance_window) < 5:
            return
            
        # 计算最近性能指标
        recent_performance = self.performance_window[-10:]
        avg_throughput = sum(p['throughput'] for p in recent_performance) / len(recent_performance)
        avg_processing_time = sum(p['processing_time'] for p in recent_performance) / len(recent_performance)
        
        # 获取系统资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        queue_size = self.event_queue.qsize()
        
        old_batch_size = self.batch_size
        
        # 调整策略
        if cpu_percent < 50 and avg_throughput < 30:
            # CPU利用率低，吞吐量低，增加批次大小
            self.batch_size = min(200, int(self.batch_size * 1.2))
        elif cpu_percent > 85 or memory_percent > 80:
            # 资源压力大，减少批次大小
            self.batch_size = max(10, int(self.batch_size * 0.8))
        elif queue_size > 1000:
            # 队列堆积，增加处理能力
            self.batch_size = min(200, int(self.batch_size * 1.1))
        
        # 记录调整
        if old_batch_size != self.batch_size:
            self.logger.info(f"📊 自动调整批次大小: {old_batch_size} → {self.batch_size} "
                           f"(CPU: {cpu_percent:.1f}%, 内存: {memory_percent:.1f}%, "
                           f"队列: {queue_size}, 吞吐量: {avg_throughput:.1f}/秒)")
    
    def _cleanup_processed_keys(self):
        """清理过期的已处理键"""
        # 保留最近1小时的键，避免内存泄漏
        if len(self.processed_keys) > 10000:
            # 简单的LRU策略，清理一半
            keys_list = list(self.processed_keys)
            self.processed_keys = set(keys_list[len(keys_list)//2:])
            self.logger.info(f"🧹 清理过期处理键，当前数量: {len(self.processed_keys)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        uptime = time.time() - getattr(self, 'start_time', time.time())
        
        return {
            'processor_name': 'CommonEventBatchProcessor',
            'cpu_cores': self.cpu_cores,
            'memory_gb': self.memory_gb,
            'batch_size': self.batch_size,
            'max_workers': self.max_workers,
            'queue_size': self.event_queue.qsize(),
            'processed_total': self.stats['processed'],
            'batch_count': self.stats['batch_count'],
            'failed_count': self.stats['failed'],
            'avg_processing_time': self.stats['avg_processing_time'],
            'uptime_seconds': uptime,
            'processed_keys_count': len(self.processed_keys),
            'running': self.running
        }
    
    def get_performance_report(self) -> str:
        """生成性能报告"""
        stats = self.get_stats()
        
        throughput = stats['processed_total'] / max(1, stats['uptime_seconds'])
        
        return f"""
🎯 CommonEventBatchProcessor 性能报告
=====================================
📊 基本信息:
   - CPU核心数: {stats['cpu_cores']}
   - 内存: {stats['memory_gb']:.1f}GB
   - 当前批次大小: {stats['batch_size']}
   - 工作线程数: {stats['max_workers']}

📈 处理统计:
   - 总处理量: {stats['processed_total']}条
   - 批次数: {stats['batch_count']}
   - 失败数: {stats['failed_count']}  
   - 平均处理时间: {stats['avg_processing_time']:.2f}秒
   - 整体吞吐量: {throughput:.1f}条/秒

🔄 运行状态:
   - 运行时间: {stats['uptime_seconds']:.0f}秒
   - 队列长度: {stats['queue_size']}
   - 处理键数: {stats['processed_keys_count']}
   - 运行状态: {'✅ 正常' if stats['running'] else '❌ 已停止'}
"""


# 全局处理器实例
_common_event_processor = None

def get_common_event_processor(app=None) -> CommonEventBatchProcessor:
    """获取全局通用事件处理器实例"""
    global _common_event_processor
    
    if _common_event_processor is None:
        _common_event_processor = CommonEventBatchProcessor(app=app)
        _common_event_processor.start()
    
    return _common_event_processor

def init_common_event_processor(app):
    """初始化通用事件处理器"""
    processor = get_common_event_processor(app)
    app.logger.info("✅ CommonEventBatchProcessor 初始化完成")
    return processor