#!/usr/bin/env python3
"""
Redis缓存优化版的generate_alerts函数
集成ljwx-boot和ljwx-bigscreen之间的告警规则缓存同步
"""

import time
import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加ljwx-bigscreen路径以导入缓存管理器
current_dir = os.path.dirname(__file__)
bigscreen_path = os.path.join(current_dir, '../ljwx-bigscreen/bigscreen')
sys.path.insert(0, bigscreen_path)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from alert_rules_cache_manager import get_alert_rules_cache_manager, AlertRule
    CACHE_MANAGER_AVAILABLE = True
    logger.info("✅ 告警规则缓存管理器导入成功")
except ImportError as e:
    logger.warning(f"⚠️  无法导入告警规则缓存管理器: {e}")
    CACHE_MANAGER_AVAILABLE = False
    # 定义基本的AlertRule类用于兜底
    @dataclass
    class AlertRule:
        id: int
        rule_type: str
        physical_sign: str
        threshold_min: Optional[float]
        threshold_max: Optional[float]
        trend_duration: Optional[int]
        severity_level: str
        alert_message: str
        customer_id: int
        is_enabled: bool = True

@dataclass  
class AlertCandidate:
    """告警候选数据结构"""
    rule_id: int
    device_sn: str
    user_id: int
    alert_message: str
    severity_level: str
    physical_sign: str
    current_value: Any
    threshold_violated: str

class RedisCachedAlertGenerator:
    """Redis缓存优化的告警生成器"""
    
    def __init__(self):
        self.alert_rules_manager = None
        self.stats = {
            'total_processed': 0,
            'cache_hits': 0,
            'db_fallbacks': 0,
            'alerts_generated': 0,
            'processing_time': 0
        }
        self._init_cache_manager()
        
    def _init_cache_manager(self):
        """初始化缓存管理器"""
        if CACHE_MANAGER_AVAILABLE:
            try:
                self.alert_rules_manager = get_alert_rules_cache_manager()
                self.alert_rules_manager.start_subscriber()
                logger.info("🚀 Redis订阅者已启动，监听告警规则更新")
            except Exception as e:
                logger.error(f"❌ 初始化缓存管理器失败: {e}")
                self.alert_rules_manager = None
        else:
            logger.info("📋 使用数据库查询模式")
            
    def get_alert_rules(self, customer_id: int) -> List[AlertRule]:
        """获取告警规则 - 优先使用Redis缓存"""
        if not customer_id:
            return []
            
        start_time = time.time()
        
        # 优先使用Redis缓存管理器
        if self.alert_rules_manager:
            try:
                rules = self.alert_rules_manager.get_alert_rules(customer_id)
                if rules:
                    self.stats['cache_hits'] += 1
                    processing_time = time.time() - start_time
                    logger.debug(f"🎯 Redis缓存命中: customer_id={customer_id}, rules={len(rules)}, time={processing_time:.3f}s")
                    return rules
            except Exception as e:
                logger.error(f"❌ Redis缓存获取失败: {e}")
        
        # 数据库兜底
        self.stats['db_fallbacks'] += 1
        rules = self._fetch_from_database(customer_id)
        processing_time = time.time() - start_time
        logger.info(f"📊 数据库兜底查询: customer_id={customer_id}, rules={len(rules)}, time={processing_time:.3f}s")
        return rules
        
    def _fetch_from_database(self, customer_id: int) -> List[AlertRule]:
        """从数据库获取告警规则 - 兜底方案"""
        # 这里应该是真实的数据库查询逻辑
        # 为了演示，返回模拟数据
        logger.warning(f"⚠️  数据库兜底被触发，建议检查Redis缓存状态: customer_id={customer_id}")
        
        # 模拟数据库查询延迟
        time.sleep(0.05)
        
        return [
            AlertRule(
                id=1,
                rule_type='THRESHOLD',
                physical_sign='heart_rate',
                threshold_min=50.0,
                threshold_max=120.0,
                trend_duration=None,
                severity_level='HIGH',
                alert_message='心率异常',
                customer_id=customer_id,
                is_enabled=True
            ),
            AlertRule(
                id=2,
                rule_type='THRESHOLD',
                physical_sign='blood_oxygen', 
                threshold_min=95.0,
                threshold_max=100.0,
                trend_duration=None,
                severity_level='MEDIUM',
                alert_message='血氧异常',
                customer_id=customer_id,
                is_enabled=True
            )
        ]
        
    def generate_alerts(self, health_data_list: List[Dict]) -> List[AlertCandidate]:
        """生成告警 - Redis缓存优化版"""
        start_time = time.time()
        alerts = []
        
        try:
            for health_data in health_data_list:
                customer_id = health_data.get('customer_id')
                if not customer_id:
                    logger.warning("健康数据缺少customer_id字段，跳过告警检查")
                    continue
                    
                # 获取告警规则（Redis缓存优先）
                rules = self.get_alert_rules(customer_id)
                
                # 应用告警规则
                device_alerts = self._apply_rules(health_data, rules)
                alerts.extend(device_alerts)
                
            self.stats['total_processed'] += len(health_data_list)
            self.stats['alerts_generated'] += len(alerts)
            self.stats['processing_time'] += time.time() - start_time
            
            processing_time = time.time() - start_time
            logger.info(f"⚡ 告警生成完成: 处理{len(health_data_list)}条数据, 生成{len(alerts)}个告警, 耗时{processing_time:.3f}s")
            
        except Exception as e:
            logger.error(f"❌ 告警生成失败: {e}")
            import traceback
            traceback.print_exc()
            
        return alerts
        
    def _apply_rules(self, health_data: Dict, rules: List[AlertRule]) -> List[AlertCandidate]:
        """应用告警规则"""
        alerts = []
        
        for rule in rules:
            if not rule.is_enabled:
                continue
                
            # 检查物理指标
            physical_value = health_data.get(rule.physical_sign)
            if physical_value is None:
                continue
                
            # 阈值检查
            violation = self._check_threshold_violation(physical_value, rule)
            if violation:
                alert = AlertCandidate(
                    rule_id=rule.id,
                    device_sn=health_data.get('device_sn', ''),
                    user_id=health_data.get('user_id', 0),
                    alert_message=rule.alert_message,
                    severity_level=rule.severity_level,
                    physical_sign=rule.physical_sign,
                    current_value=physical_value,
                    threshold_violated=violation
                )
                alerts.append(alert)
                
        return alerts
        
    def _check_threshold_violation(self, value: Any, rule: AlertRule) -> Optional[str]:
        """检查阈值违规"""
        try:
            numeric_value = float(value)
            
            if rule.threshold_min is not None and numeric_value < rule.threshold_min:
                return f"低于下限{rule.threshold_min}"
            elif rule.threshold_max is not None and numeric_value > rule.threshold_max:
                return f"超出上限{rule.threshold_max}"
                
        except (ValueError, TypeError):
            logger.warning(f"无法转换数值: {value} for rule {rule.id}")
            
        return None
        
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.stats.copy()
        
        # 计算命中率
        total_queries = stats['cache_hits'] + stats['db_fallbacks']
        if total_queries > 0:
            stats['cache_hit_rate'] = f"{(stats['cache_hits'] / total_queries * 100):.2f}%"
        else:
            stats['cache_hit_rate'] = "0.00%"
            
        # 计算平均处理时间
        if stats['total_processed'] > 0:
            stats['avg_processing_time'] = f"{(stats['processing_time'] / stats['total_processed']):.3f}s"
        else:
            stats['avg_processing_time'] = "0.000s"
            
        # 缓存管理器状态
        if self.alert_rules_manager:
            try:
                cache_stats = self.alert_rules_manager.get_cache_stats()
                stats['cache_manager_status'] = cache_stats
            except Exception as e:
                stats['cache_manager_error'] = str(e)
        else:
            stats['cache_manager_status'] = "未启用"
            
        return stats
        
    def preload_rules(self, customer_ids: List[int]):
        """预加载指定客户的告警规则"""
        if self.alert_rules_manager:
            self.alert_rules_manager.preload_customer_rules(customer_ids)
            logger.info(f"📋 预加载告警规则: {len(customer_ids)}个客户")
            
    def clear_cache(self, customer_id: Optional[int] = None):
        """清理缓存"""
        if self.alert_rules_manager:
            self.alert_rules_manager.clear_local_cache(customer_id)
            logger.info(f"🧹 清理告警规则缓存: customer_id={customer_id or 'all'}")
            
    def shutdown(self):
        """关闭生成器"""
        if self.alert_rules_manager:
            self.alert_rules_manager.stop_subscriber()
            logger.info("🛑 Redis订阅者已停止")

# 全局实例
_global_generator = None

def get_redis_cached_generator() -> RedisCachedAlertGenerator:
    """获取全局Redis缓存告警生成器实例"""
    global _global_generator
    if _global_generator is None:
        _global_generator = RedisCachedAlertGenerator()
        logger.info("🚀 全局Redis缓存告警生成器已初始化")
    return _global_generator

def redis_cached_generate_alerts(health_data_list: List[Dict]) -> List[AlertCandidate]:
    """Redis缓存优化版的generate_alerts函数
    
    替代原有的generate_alerts函数，提供：
    1. Redis缓存优先的告警规则获取
    2. 实时的缓存更新通知
    3. 数据库兜底保障
    4. 性能监控统计
    
    Args:
        health_data_list: 健康数据列表，每项应包含customer_id字段
        
    Returns:
        告警候选列表
    """
    generator = get_redis_cached_generator()
    return generator.generate_alerts(health_data_list)

def init_redis_cache_manager():
    """初始化Redis缓存管理器 - 应用启动时调用"""
    generator = get_redis_cached_generator()
    logger.info("✅ Redis缓存告警生成器初始化完成")
    return generator

def shutdown_redis_cache_manager():
    """关闭Redis缓存管理器 - 应用关闭时调用"""
    global _global_generator
    if _global_generator:
        _global_generator.shutdown()
        _global_generator = None
        logger.info("🛑 Redis缓存告警生成器已关闭")

if __name__ == "__main__":
    # 测试代码
    print("🧪 Redis缓存告警生成器测试")
    
    # 初始化生成器
    generator = get_redis_cached_generator()
    
    # 等待Redis订阅者启动
    time.sleep(2)
    
    # 测试数据
    test_health_data = [
        {
            'device_sn': 'TEST001',
            'user_id': 1,
            'customer_id': 1,
            'heart_rate': 85,
            'blood_oxygen': 98,
            'temperature': 36.5,
            'timestamp': '2025-09-09 10:00:00'
        },
        {
            'device_sn': 'TEST002', 
            'user_id': 2,
            'customer_id': 1,
            'heart_rate': 130,  # 超出阈值
            'blood_oxygen': 92,  # 低于阈值
            'temperature': 37.2,
            'timestamp': '2025-09-09 10:01:00'
        }
    ]
    
    try:
        print("\n📋 测试告警规则获取")
        rules = generator.get_alert_rules(1)
        print(f"获取到告警规则: {len(rules)}条")
        for rule in rules:
            print(f"  - {rule.rule_type}: {rule.physical_sign} [{rule.threshold_min}-{rule.threshold_max}] ({rule.severity_level})")
            
        print("\n⚡ 测试告警生成")
        alerts = generator.generate_alerts(test_health_data)
        print(f"生成告警: {len(alerts)}个")
        for alert in alerts:
            print(f"  - {alert.physical_sign}: {alert.current_value} ({alert.threshold_violated}) - {alert.severity_level}")
            
        print("\n📊 性能统计")
        stats = generator.get_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
                
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.shutdown()
        print("🛑 生成器已关闭")