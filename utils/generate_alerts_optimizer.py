#!/usr/bin/env python3
"""
generate_alerts 函数优化器
解决upload_health_data接口的性能瓶颈问题 - 支持Redis缓存同步
"""

import time
import threading
import queue
import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from cachetools import TTLCache, LRUCache
import asyncio
from datetime import datetime, timedelta

# 添加ljwx-bigscreen路径以导入缓存管理器
sys.path.append(os.path.join(os.path.dirname(__file__), '../ljwx-bigscreen/bigscreen'))
try:
    from alert_rules_cache_manager import get_alert_rules_cache_manager, AlertRule
    CACHE_MANAGER_AVAILABLE = True
except ImportError:
    print("警告：无法导入告警规则缓存管理器，将使用数据库查询模式")
    AlertRule = None
    get_alert_rules_cache_manager = None
    CACHE_MANAGER_AVAILABLE = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """告警规则数据结构"""
    id: int
    rule_type: str
    physical_sign: str
    threshold_min: float
    threshold_max: float
    trend_duration: int
    severity_level: str
    alert_message: str
    is_enabled: bool = True

@dataclass
class DeviceInfo:
    """设备信息数据结构"""
    device_sn: str
    user_id: int
    org_id: int
    customer_id: int
    user_name: str
    org_name: str

@dataclass
class AlertCandidate:
    """候选告警数据"""
    rule_id: int
    rule_type: str
    device_sn: str
    alert_desc: str
    severity_level: str
    health_data_id: Optional[int]
    user_id: Optional[int]
    org_id: Optional[int]
    customer_id: Optional[int]
    alert_timestamp: datetime
    alert_value: Any = None
    threshold_violated: str = None

class AlertRuleCache:
    """告警规则缓存管理器"""
    
    def __init__(self, ttl=600):  # 10分钟缓存
        self.cache = TTLCache(maxsize=1000, ttl=ttl)
        self.lock = threading.RLock()
        self._last_refresh = 0
        self._refresh_interval = 300  # 5分钟强制刷新
        
    def get_rules(self) -> List[AlertRule]:
        """获取缓存的告警规则"""
        with self.lock:
            current_time = time.time()
            cache_key = "all_rules"
            
            # 检查是否需要强制刷新
            if (cache_key not in self.cache or 
                current_time - self._last_refresh > self._refresh_interval):
                self._refresh_rules()
                self._last_refresh = current_time
            
            return self.cache.get(cache_key, [])
    
    def _refresh_rules(self):
        """刷新告警规则缓存"""
        try:
            from ljwx_bigscreen.bigscreen.bigScreen.models import AlertRules
            from ljwx_bigscreen.bigscreen.bigScreen.models import db
            
            rules = AlertRules.query.filter_by(is_deleted=False).all()
            rule_objects = []
            
            for rule in rules:
                rule_obj = AlertRule(
                    id=rule.id,
                    rule_type=rule.rule_type,
                    physical_sign=rule.physical_sign or '',
                    threshold_min=float(rule.threshold_min or 0),
                    threshold_max=float(rule.threshold_max or float('inf')),
                    trend_duration=int(rule.trend_duration or 1),
                    severity_level=rule.severity_level,
                    alert_message=rule.alert_message,
                    is_enabled=getattr(rule, 'is_enabled', True)
                )
                rule_objects.append(rule_obj)
            
            self.cache["all_rules"] = rule_objects
            logger.info(f"告警规则缓存刷新完成，共{len(rule_objects)}条规则")
            
        except Exception as e:
            logger.error(f"刷新告警规则缓存失败: {e}")
            # 如果刷新失败，保持现有缓存
    
    def invalidate(self):
        """清除缓存"""
        with self.lock:
            self.cache.clear()

class DeviceInfoCache:
    """设备信息缓存管理器"""
    
    def __init__(self, ttl=300):  # 5分钟缓存
        self.cache = TTLCache(maxsize=10000, ttl=ttl)
        self.lock = threading.RLock()
    
    def get_device_info(self, device_sn: str) -> Optional[DeviceInfo]:
        """获取缓存的设备信息"""
        with self.lock:
            cached = self.cache.get(device_sn)
            if cached:
                return cached
        
        # 缓存未命中，查询数据库
        device_info = self._query_device_info(device_sn)
        if device_info:
            with self.lock:
                self.cache[device_sn] = device_info
        
        return device_info
    
    def _query_device_info(self, device_sn: str) -> Optional[DeviceInfo]:
        """查询设备信息"""
        try:
            from ljwx_bigscreen.bigscreen.bigScreen.device import get_device_user_org_info
            
            result = get_device_user_org_info(device_sn)
            if result.get('success'):
                return DeviceInfo(
                    device_sn=device_sn,
                    user_id=result.get('user_id'),
                    org_id=result.get('org_id'),
                    customer_id=result.get('customer_id', 0),
                    user_name=result.get('user_name', ''),
                    org_name=result.get('org_name', '')
                )
            return None
            
        except Exception as e:
            logger.error(f"查询设备信息失败 {device_sn}: {e}")
            return None

class AbnormalCountTracker:
    """异常计数跟踪器"""
    
    def __init__(self, ttl=3600):  # 1小时过期
        self.counts = LRUCache(maxsize=50000)  # device_sn:physical_sign -> count
        self.lock = threading.RLock()
        self.timestamps = {}  # 记录最后更新时间
        self.ttl = ttl
    
    def update_count(self, device_sn: str, physical_sign: str, is_abnormal: bool) -> int:
        """更新异常计数"""
        key = f"{device_sn}:{physical_sign}"
        current_time = time.time()
        
        with self.lock:
            # 检查是否超时
            if key in self.timestamps:
                if current_time - self.timestamps[key] > self.ttl:
                    self.counts.pop(key, None)
                    self.timestamps.pop(key, None)
            
            if is_abnormal:
                current_count = self.counts.get(key, 0) + 1
                self.counts[key] = current_count
                self.timestamps[key] = current_time
                return current_count
            else:
                # 正常值，重置计数
                self.counts[key] = 0
                self.timestamps[key] = current_time
                return 0
    
    def get_count(self, device_sn: str, physical_sign: str) -> int:
        """获取当前异常计数"""
        key = f"{device_sn}:{physical_sign}"
        with self.lock:
            return self.counts.get(key, 0)

class OptimizedAlertGenerator:
    """优化的告警生成器"""
    
    def __init__(self, max_workers=4, batch_size=100):
        self.rule_cache = AlertRuleCache()
        self.device_cache = DeviceInfoCache()
        self.abnormal_tracker = AbnormalCountTracker()
        
        # 异步处理配置
        self.alert_queue = queue.Queue(maxsize=10000)
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        
        # 性能统计
        self.stats = {
            'total_processed': 0,
            'total_alerts_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_processing_time': 0.0,
            'rule_evaluation_time': 0.0,
            'db_save_time': 0.0
        }
        
        # 启动后台处理器
        self.start_background_processor()
    
    def start_background_processor(self):
        """启动后台处理器"""
        self.running = True
        for i in range(self.max_workers):
            self.executor.submit(self._background_worker)
        logger.info(f"告警生成器已启动，工作线程数: {self.max_workers}")
    
    def stop_background_processor(self):
        """停止后台处理器"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("告警生成器已停止")
    
    def generate_alerts_async(self, health_data: Dict, health_data_id: Optional[int] = None):
        """异步生成告警 - 主入口函数"""
        try:
            # 快速验证
            if not health_data or not isinstance(health_data, dict):
                logger.warning("无效的健康数据格式")
                return False
            
            device_sn = health_data.get('deviceSn')
            if not device_sn:
                logger.warning("健康数据缺少设备序列号")
                return False
            
            # 构造处理项
            process_item = {
                'health_data': health_data,
                'health_data_id': health_data_id,
                'timestamp': time.time(),
                'device_sn': device_sn
            }
            
            # 提交到异步队列
            try:
                self.alert_queue.put_nowait(process_item)
                return True
            except queue.Full:
                logger.warning("告警处理队列已满，丢弃请求")
                return False
                
        except Exception as e:
            logger.error(f"提交异步告警生成失败: {e}")
            return False
    
    def _background_worker(self):
        """后台工作线程"""
        batch = []
        last_process_time = time.time()
        max_wait_time = 2.0  # 最大等待时间
        
        while self.running:
            try:
                # 收集批次
                while (len(batch) < self.batch_size and 
                       (time.time() - last_process_time) < max_wait_time):
                    try:
                        item = self.alert_queue.get(timeout=0.5)
                        batch.append(item)
                    except queue.Empty:
                        break
                
                # 处理批次
                if batch:
                    self._process_batch(batch)
                    batch.clear()
                    last_process_time = time.time()
                    
            except Exception as e:
                logger.error(f"后台工作线程异常: {e}")
                batch.clear()
    
    def _process_batch(self, batch: List[Dict]):
        """批量处理告警生成"""
        start_time = time.time()
        alerts_to_insert = []
        
        try:
            # 预加载告警规则
            rules = self.rule_cache.get_rules()
            if not rules:
                logger.warning("没有可用的告警规则")
                return
            
            # 批量处理每个健康数据
            for item in batch:
                try:
                    health_data = item['health_data']
                    health_data_id = item['health_data_id']
                    device_sn = health_data.get('deviceSn', 'Unknown')
                    
                    # 获取设备信息（缓存）
                    device_info = self.device_cache.get_device_info(device_sn)
                    if not device_info:
                        logger.warning(f"设备信息未找到: {device_sn}")
                        continue
                    
                    # 评估告警规则
                    rule_start_time = time.time()
                    alert_candidates = self._evaluate_rules_optimized(
                        health_data, rules, device_info, health_data_id
                    )
                    
                    self.stats['rule_evaluation_time'] += time.time() - rule_start_time
                    alerts_to_insert.extend(alert_candidates)
                    
                except Exception as e:
                    logger.error(f"处理单个健康数据失败: {e}")
                    continue
            
            # 批量插入告警
            if alerts_to_insert:
                db_start_time = time.time()
                inserted_count = self._batch_insert_alerts(alerts_to_insert)
                self.stats['db_save_time'] += time.time() - db_start_time
                self.stats['total_alerts_generated'] += inserted_count
                logger.info(f"批量插入告警完成: {inserted_count}条")
            
            # 更新统计
            processing_time = time.time() - start_time
            self.stats['total_processed'] += len(batch)
            self.stats['avg_processing_time'] = (
                self.stats['avg_processing_time'] * 0.9 + processing_time * 0.1
            )
            
            logger.info(f"批量处理完成: 处理{len(batch)}条, 生成{len(alerts_to_insert)}个告警, 耗时{processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"批量处理异常: {e}")
    
    def _evaluate_rules_optimized(self, health_data: Dict, rules: List[AlertRule], 
                                device_info: DeviceInfo, health_data_id: Optional[int]) -> List[AlertCandidate]:
        """优化的规则评估"""
        alert_candidates = []
        device_sn = health_data.get('deviceSn', 'Unknown')
        
        for rule in rules:
            if not rule.is_enabled or not rule.physical_sign:
                continue
            
            try:
                # 获取对应的健康数据值
                is_abnormal, violation_info = self._check_rule_violation(health_data, rule)
                
                # 更新异常计数
                abnormal_count = self.abnormal_tracker.update_count(
                    device_sn, rule.physical_sign, is_abnormal
                )
                
                # 检查是否需要生成告警
                if abnormal_count >= rule.trend_duration:
                    alert_candidate = AlertCandidate(
                        rule_id=rule.id,
                        rule_type=rule.rule_type,
                        device_sn=device_sn,
                        alert_desc=f"{rule.alert_message} - {violation_info}",
                        severity_level=rule.severity_level,
                        health_data_id=health_data_id,
                        user_id=device_info.user_id,
                        org_id=device_info.org_id,
                        customer_id=device_info.customer_id,
                        alert_timestamp=datetime.now(),
                        alert_value=violation_info,
                        threshold_violated=f"连续{abnormal_count}次异常"
                    )
                    alert_candidates.append(alert_candidate)
                    
                    # 重置计数，避免重复告警
                    self.abnormal_tracker.update_count(device_sn, rule.physical_sign, False)
                    
            except Exception as e:
                logger.error(f"评估规则失败 rule_id={rule.id}: {e}")
                continue
        
        return alert_candidates
    
    def _check_rule_violation(self, health_data: Dict, rule: AlertRule) -> Tuple[bool, str]:
        """检查规则违反情况"""
        physical_sign = rule.physical_sign
        
        try:
            if physical_sign == 'bloodPressure':
                # 血压特殊处理
                systolic = self._safe_float(health_data.get('pressureHigh'))
                diastolic = self._safe_float(health_data.get('pressureLow'))
                
                systolic_abnormal = (systolic is not None and 
                                   (systolic < rule.threshold_min or systolic > rule.threshold_max))
                diastolic_abnormal = (diastolic is not None and 
                                    (diastolic < rule.threshold_min or diastolic > rule.threshold_max))
                
                if systolic_abnormal or diastolic_abnormal:
                    violation_info = f"收缩压:{systolic}, 舒张压:{diastolic} (范围:{rule.threshold_min}-{rule.threshold_max})"
                    return True, violation_info
                else:
                    return False, f"血压正常: {systolic}/{diastolic}"
            
            else:
                # 其他指标
                value = self._safe_float(health_data.get(physical_sign))
                if value is not None:
                    if value < rule.threshold_min or value > rule.threshold_max:
                        violation_info = f"{physical_sign}:{value} (范围:{rule.threshold_min}-{rule.threshold_max})"
                        return True, violation_info
                    else:
                        return False, f"{physical_sign}正常: {value}"
                else:
                    return False, f"{physical_sign}数据缺失"
            
        except Exception as e:
            logger.error(f"检查规则违反异常: {e}")
            return False, "检查失败"
    
    def _safe_float(self, value) -> Optional[float]:
        """安全的浮点数转换"""
        if value is None or value == '' or str(value).strip() == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _batch_insert_alerts(self, alert_candidates: List[AlertCandidate]) -> int:
        """批量插入告警"""
        try:
            from ljwx_bigscreen.bigscreen.bigScreen.models import AlertInfo, db
            
            # 构造插入数据
            alerts_to_insert = []
            for candidate in alert_candidates:
                alert_data = {
                    'rule_id': candidate.rule_id,
                    'alert_type': candidate.rule_type,
                    'device_sn': candidate.device_sn,
                    'alert_desc': candidate.alert_desc,
                    'severity_level': candidate.severity_level,
                    'alert_status': 'pending',
                    'alert_timestamp': candidate.alert_timestamp,
                    'health_id': candidate.health_data_id,
                    'user_id': candidate.user_id,
                    'org_id': candidate.org_id,
                    'customer_id': candidate.customer_id
                }
                alerts_to_insert.append(alert_data)
            
            # 批量插入
            if alerts_to_insert:
                db.session.bulk_insert_mappings(AlertInfo, alerts_to_insert)
                db.session.commit()
                return len(alerts_to_insert)
            
            return 0
            
        except Exception as e:
            logger.error(f"批量插入告警失败: {e}")
            from ljwx_bigscreen.bigscreen.bigScreen.models import db
            db.session.rollback()
            return 0
    
    def get_stats(self) -> Dict:
        """获取性能统计"""
        stats = self.stats.copy()
        stats['queue_size'] = self.alert_queue.qsize()
        stats['rule_cache_size'] = len(self.rule_cache.cache)
        stats['device_cache_size'] = len(self.device_cache.cache)
        stats['abnormal_tracker_size'] = len(self.abnormal_tracker.counts)
        return stats
    
    def clear_caches(self):
        """清除所有缓存"""
        self.rule_cache.invalidate()
        self.device_cache.cache.clear()
        self.abnormal_tracker.counts.clear()
        self.abnormal_tracker.timestamps.clear()
        logger.info("所有缓存已清除")

# 全局实例
_alert_generator_instance = None
_instance_lock = threading.Lock()

def get_optimized_alert_generator() -> OptimizedAlertGenerator:
    """获取优化告警生成器的全局实例"""
    global _alert_generator_instance
    
    if _alert_generator_instance is None:
        with _instance_lock:
            if _alert_generator_instance is None:
                _alert_generator_instance = OptimizedAlertGenerator()
    
    return _alert_generator_instance

# 兼容性函数 - 替换原有的generate_alerts
def generate_alerts_optimized(health_data: Dict, health_data_id: Optional[int] = None) -> bool:
    """优化版本的generate_alerts函数"""
    try:
        generator = get_optimized_alert_generator()
        return generator.generate_alerts_async(health_data, health_data_id)
    except Exception as e:
        logger.error(f"优化告警生成失败: {e}")
        return False

def get_alert_generator_stats() -> Dict:
    """获取告警生成器统计信息"""
    try:
        generator = get_optimized_alert_generator()
        return generator.get_stats()
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {}

def clear_alert_caches():
    """清除告警相关缓存"""
    try:
        generator = get_optimized_alert_generator()
        generator.clear_caches()
        return True
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return False

if __name__ == "__main__":
    # 测试代码
    generator = OptimizedAlertGenerator(max_workers=2, batch_size=10)
    
    # 模拟健康数据
    test_data = {
        'deviceSn': 'TEST001',
        'heartRate': 120,
        'bloodOxygen': 95,
        'pressureHigh': 140,
        'pressureLow': 90,
        'temperature': 37.2,
        'timestamp': '2025-01-15 10:00:00'
    }
    
    # 测试异步生成告警
    success = generator.generate_alerts_async(test_data, 12345)
    print(f"异步告警生成提交: {'成功' if success else '失败'}")
    
    # 等待处理完成
    time.sleep(3)
    
    # 查看统计信息
    stats = generator.get_stats()
    print(f"处理统计: {json.dumps(stats, indent=2, default=str)}")
    
    # 停止生成器
    generator.stop_background_processor()
    print("测试完成")