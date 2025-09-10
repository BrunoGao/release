#!/usr/bin/env python3
"""
告警规则缓存管理器 - 跨DB Redis订阅者
实现ljwx-boot和ljwx-bigscreen之间的告警规则缓存同步
"""

import redis
import json
import logging
import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from redis_config import get_redis_client

# 设置日志
logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """告警规则数据结构"""
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

class AlertRulesCacheManager:
    """告警规则缓存管理器 - 支持跨DB Redis通信"""
    
    def __init__(self):
        # ljwx-bigscreen Redis客户端 (DB=0)
        self.redis_client = get_redis_client()
        
        # ljwx-boot Redis客户端 (DB=1) 
        self.boot_redis_client = redis.Redis(
            host='127.0.0.1',
            port=6379,
            db=1,  # ljwx-boot使用DB=1
            password='123456',
            decode_responses=True,
            socket_timeout=30,
            socket_connect_timeout=30,
            retry_on_timeout=True
        )
        
        # 本地缓存
        self.local_cache = {}  # {customer_id: rules_list}
        self.version_cache = {}  # {customer_id: version}
        
        # 订阅者状态
        self.subscriber_thread = None
        self.running = False
        self.pubsub = None
        
    def start_subscriber(self):
        """启动Redis订阅者监听告警规则更新"""
        if self.running:
            logger.warning("告警规则订阅者已在运行中")
            return
            
        self.running = True
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe('alert_rules_channel')
        
        # 启动订阅者线程
        self.subscriber_thread = threading.Thread(
            target=self._subscriber_loop,
            daemon=True,
            name="AlertRulesSubscriber"
        )
        self.subscriber_thread.start()
        logger.info("告警规则订阅者已启动，监听 alert_rules_channel")
        
    def stop_subscriber(self):
        """停止Redis订阅者"""
        self.running = False
        if self.pubsub:
            self.pubsub.unsubscribe('alert_rules_channel')
            self.pubsub.close()
        logger.info("告警规则订阅者已停止")
        
    def _subscriber_loop(self):
        """订阅者主循环"""
        while self.running:
            try:
                for message in self.pubsub.listen():
                    if not self.running:
                        break
                        
                    if message['type'] == 'message':
                        self._handle_cache_update(message['data'])
                        
            except Exception as e:
                logger.error(f"Redis订阅者错误: {e}")
                if self.running:
                    time.sleep(5)  # 错误后重试间隔
                    
    def _handle_cache_update(self, message: str):
        """处理缓存更新消息"""
        try:
            # 解析消息格式: "update:customer_id:version"
            parts = message.split(':')
            if len(parts) >= 2 and parts[0] == 'update':
                customer_id = int(parts[1])
                version = int(parts[2]) if len(parts) > 2 else 0
                
                # 检查是否需要更新本地缓存
                if self._should_update_cache(customer_id, version):
                    self._refresh_local_cache(customer_id)
                    
        except Exception as e:
            logger.error(f"处理缓存更新消息失败: {message}, error: {e}")
            
    def _should_update_cache(self, customer_id: int, version: int) -> bool:
        """检查是否需要更新缓存"""
        local_version = self.version_cache.get(customer_id, 0)
        return version > local_version
        
    def _refresh_local_cache(self, customer_id: int):
        """刷新本地缓存 - 从ljwx-boot的Redis DB=1获取"""
        try:
            cache_key = f"alert_rules_{customer_id}"
            # 从ljwx-boot的Redis DB=1获取数据
            cached_data = self.boot_redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                rules_data = data.get('rules', [])
                version = data.get('version', 0)
                
                # 转换为AlertRule对象
                rules = []
                for rule_dict in rules_data:
                    try:
                        rule = AlertRule(
                            id=rule_dict.get('id'),
                            rule_type=rule_dict.get('ruleType', ''),
                            physical_sign=rule_dict.get('physicalSign', ''),
                            threshold_min=rule_dict.get('thresholdMin'),
                            threshold_max=rule_dict.get('thresholdMax'),
                            trend_duration=rule_dict.get('trendDuration'),
                            severity_level=rule_dict.get('severityLevel', ''),
                            alert_message=rule_dict.get('alertMessage', ''),
                            customer_id=rule_dict.get('customerId'),
                            is_enabled=rule_dict.get('isEnabled', True)
                        )
                        rules.append(rule)
                    except Exception as e:
                        logger.warning(f"解析告警规则失败: {rule_dict}, error: {e}")
                
                # 更新本地缓存
                self.local_cache[customer_id] = rules
                self.version_cache[customer_id] = version
                
                logger.info(f"告警规则缓存更新成功: customer_id={customer_id}, version={version}, rules={len(rules)}")
                
        except Exception as e:
            logger.error(f"刷新告警规则缓存失败: customer_id={customer_id}, error: {e}")
            
    def get_alert_rules(self, customer_id: int) -> List[AlertRule]:
        """获取告警规则 - 三级缓存策略 + 自动预热"""
        # L1: 本地缓存
        if customer_id in self.local_cache:
            logger.debug(f"告警规则本地缓存命中: customer_id={customer_id}")
            return self.local_cache[customer_id]
            
        # L2: 从ljwx-boot的Redis获取
        try:
            cache_key = f"alert_rules_{customer_id}"
            cached_data = self.boot_redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                rules_data = data.get('rules', [])
                version = data.get('version', 0)
                
                # 转换并缓存到本地
                rules = self._convert_rules_data(rules_data)
                self.local_cache[customer_id] = rules
                self.version_cache[customer_id] = version
                
                logger.info(f"告警规则从ljwx-boot Redis获取成功: customer_id={customer_id}, rules={len(rules)}")
                return rules
                
        except Exception as e:
            logger.error(f"从ljwx-boot Redis获取告警规则失败: customer_id={customer_id}, error: {e}")
            
        # L3: 自动预热机制 - 尝试从数据库获取并缓存
        logger.warning(f"告警规则缓存miss，尝试自动预热: customer_id={customer_id}")
        rules = self._auto_warmup_from_database(customer_id)
        return rules
        
    def _convert_rules_data(self, rules_data: List[Dict]) -> List[AlertRule]:
        """转换规则数据为AlertRule对象"""
        rules = []
        for rule_dict in rules_data:
            try:
                rule = AlertRule(
                    id=rule_dict.get('id'),
                    rule_type=rule_dict.get('ruleType', ''),
                    physical_sign=rule_dict.get('physicalSign', ''),
                    threshold_min=rule_dict.get('thresholdMin'),
                    threshold_max=rule_dict.get('thresholdMax'),
                    trend_duration=rule_dict.get('trendDuration'),
                    severity_level=rule_dict.get('severityLevel', ''),
                    alert_message=rule_dict.get('alertMessage', ''),
                    customer_id=rule_dict.get('customerId'),
                    is_enabled=rule_dict.get('isEnabled', True)
                )
                rules.append(rule)
            except Exception as e:
                logger.warning(f"转换告警规则数据失败: {rule_dict}, error: {e}")
        return rules
        
    def preload_customer_rules(self, customer_ids: List[int]):
        """预加载指定客户的告警规则"""
        for customer_id in customer_ids:
            try:
                self.get_alert_rules(customer_id)
                logger.info(f"预加载告警规则成功: customer_id={customer_id}")
            except Exception as e:
                logger.error(f"预加载告警规则失败: customer_id={customer_id}, error: {e}")
                
    def warmup_active_customers(self, days: int = 7):
        """预热活跃客户的告警规则缓存"""
        try:
            import pymysql
            from redis_config import get_mysql_config
            
            # 获取MySQL配置
            mysql_config = get_mysql_config()
            
            # 连接数据库
            connection = pymysql.connect(
                host=mysql_config['host'],
                port=mysql_config['port'],
                user=mysql_config['user'],
                password=mysql_config['password'],
                database=mysql_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with connection.cursor() as cursor:
                    # 查询最近活跃的客户ID
                    sql = """
                        SELECT DISTINCT customer_id
                        FROM t_user_health_data 
                        WHERE create_time >= DATE_SUB(NOW(), INTERVAL %s DAY)
                        AND customer_id IS NOT NULL
                        LIMIT 100
                    """
                    cursor.execute(sql, (days,))
                    active_customers = cursor.fetchall()
                    
                    customer_ids = [row['customer_id'] for row in active_customers]
                    logger.info(f"发现活跃客户: {len(customer_ids)}个，开始预热缓存")
                    
                    # 批量预加载
                    self.preload_customer_rules(customer_ids)
                    
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"预热活跃客户告警规则失败: error={e}")
                
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'local_cache_size': len(self.local_cache),
            'cached_customers': list(self.local_cache.keys()),
            'version_info': self.version_cache,
            'subscriber_running': self.running,
            'redis_connection_status': self._check_redis_connections()
        }
        
    def _check_redis_connections(self) -> Dict[str, bool]:
        """检查Redis连接状态"""
        connections = {}
        try:
            self.redis_client.ping()
            connections['bigscreen_redis'] = True
        except:
            connections['bigscreen_redis'] = False
            
        try:
            self.boot_redis_client.ping()
            connections['boot_redis'] = True
        except:
            connections['boot_redis'] = False
            
        return connections
        
    def _auto_warmup_from_database(self, customer_id: int) -> List[AlertRule]:
        """自动预热机制 - 从数据库获取告警规则并缓存"""
        try:
            import pymysql
            from redis_config import get_mysql_config
            
            # 获取MySQL配置
            mysql_config = get_mysql_config()
            
            # 连接数据库
            connection = pymysql.connect(
                host=mysql_config['host'],
                port=mysql_config['port'],
                user=mysql_config['user'],
                password=mysql_config['password'],
                database=mysql_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with connection.cursor() as cursor:
                    # 查询告警规则
                    sql = """
                        SELECT id, rule_type, physical_sign, threshold_min, threshold_max,
                               trend_duration, severity_level, alert_message, customer_id, is_enabled
                        FROM t_alert_rules 
                        WHERE customer_id = %s AND is_enabled = 1
                        ORDER BY id
                    """
                    cursor.execute(sql, (customer_id,))
                    db_rules = cursor.fetchall()
                    
                    if not db_rules:
                        logger.info(f"数据库中未找到客户告警规则: customer_id={customer_id}")
                        return []
                    
                    # 转换为AlertRule对象
                    rules = []
                    for rule_dict in db_rules:
                        try:
                            rule = AlertRule(
                                id=rule_dict.get('id'),
                                rule_type=rule_dict.get('rule_type', ''),
                                physical_sign=rule_dict.get('physical_sign', ''),
                                threshold_min=rule_dict.get('threshold_min'),
                                threshold_max=rule_dict.get('threshold_max'),
                                trend_duration=rule_dict.get('trend_duration'),
                                severity_level=rule_dict.get('severity_level', ''),
                                alert_message=rule_dict.get('alert_message', ''),
                                customer_id=rule_dict.get('customer_id'),
                                is_enabled=rule_dict.get('is_enabled', True)
                            )
                            rules.append(rule)
                        except Exception as e:
                            logger.warning(f"转换数据库告警规则失败: {rule_dict}, error: {e}")
                    
                    # 缓存到本地和Redis
                    if rules:
                        # 更新本地缓存
                        self.local_cache[customer_id] = rules
                        self.version_cache[customer_id] = int(time.time())
                        
                        # 缓存到ljwx-boot Redis (DB=1)
                        try:
                            cache_data = {
                                'rules': [
                                    {
                                        'id': rule.id,
                                        'ruleType': rule.rule_type,
                                        'physicalSign': rule.physical_sign,
                                        'thresholdMin': rule.threshold_min,
                                        'thresholdMax': rule.threshold_max,
                                        'trendDuration': rule.trend_duration,
                                        'severityLevel': rule.severity_level,
                                        'alertMessage': rule.alert_message,
                                        'customerId': rule.customer_id,
                                        'isEnabled': rule.is_enabled
                                    }
                                    for rule in rules
                                ],
                                'version': self.version_cache[customer_id],
                                'cached_at': int(time.time())
                            }
                            
                            cache_key = f"alert_rules_{customer_id}"
                            self.boot_redis_client.setex(
                                cache_key, 
                                3600,  # 1小时缓存
                                json.dumps(cache_data, ensure_ascii=False)
                            )
                            
                            logger.info(f"告警规则自动预热成功: customer_id={customer_id}, rules={len(rules)}, 已缓存到Redis")
                            
                        except Exception as e:
                            logger.warning(f"缓存告警规则到Redis失败: customer_id={customer_id}, error: {e}")
                    
                    return rules
                    
            finally:
                connection.close()
                
        except Exception as e:
            logger.error(f"从数据库自动预热告警规则失败: customer_id={customer_id}, error: {e}")
            return []
    
    def clear_local_cache(self, customer_id: Optional[int] = None):
        """清理本地缓存"""
        if customer_id:
            self.local_cache.pop(customer_id, None)
            self.version_cache.pop(customer_id, None)
            logger.info(f"清理告警规则本地缓存: customer_id={customer_id}")
        else:
            self.local_cache.clear()
            self.version_cache.clear()
            logger.info("清理所有告警规则本地缓存")

# 全局缓存管理器实例
alert_rules_cache_manager = AlertRulesCacheManager()

def get_alert_rules_cache_manager() -> AlertRulesCacheManager:
    """获取告警规则缓存管理器实例"""
    return alert_rules_cache_manager

if __name__ == "__main__":
    # 测试代码
    print("🔧 告警规则缓存管理器测试")
    
    manager = get_alert_rules_cache_manager()
    
    # 检查Redis连接
    stats = manager.get_cache_stats()
    print(f"Redis连接状态: {stats['redis_connection_status']}")
    
    # 启动订阅者
    manager.start_subscriber()
    
    # 测试获取告警规则
    try:
        rules = manager.get_alert_rules(1)  # 假设customer_id=1
        print(f"获取到告警规则: {len(rules)}条")
    except Exception as e:
        print(f"测试失败: {e}")
    
    # 等待一段时间测试订阅
    print("等待Redis消息...")
    time.sleep(5)
    
    manager.stop_subscriber()