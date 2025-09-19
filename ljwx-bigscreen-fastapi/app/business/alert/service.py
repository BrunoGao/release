"""
告警服务
提供告警管理的业务逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import logging

from app.base.mysql import MySQLClient
from app.base.redis import RedisClient
from .engine import AlertEngine
from .processor import AlertProcessor

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务"""
    
    def __init__(self, mysql_client: MySQLClient, redis_client: RedisClient):
        self.mysql = mysql_client
        self.redis = redis_client
        self.alert_engine = AlertEngine(mysql_client, redis_client)
        self.alert_processor = AlertProcessor(mysql_client, redis_client)
        self.cache_prefix = "alert:"
        self.cache_ttl = 300  # 5分钟
    
    # 告警规则管理
    async def get_alert_rules(
        self, 
        customer_id: Optional[str] = None,
        status: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取告警规则列表"""
        cache_key = f"{self.cache_prefix}rules:{customer_id or 'all'}:{status or 'all'}"
        
        # 尝试从缓存获取
        cached_rules = await self.redis.get_json(cache_key)
        if cached_rules:
            return cached_rules
        
        try:
            conditions = ["del_flag = 0"]
            params = {}
            
            if customer_id:
                conditions.append("customer_id = :customer_id")
                params['customer_id'] = customer_id
            
            if status is not None:
                conditions.append("status = :status")
                params['status'] = status
            
            where_clause = " AND ".join(conditions)
            
            query = f"""
                SELECT 
                    id, rule_name, rule_code, rule_type, metric_type,
                    condition_config, threshold_config, level,
                    status, customer_id, description,
                    created_time, updated_time
                FROM alert_rules
                WHERE {where_clause}
                ORDER BY level DESC, created_time DESC
            """
            
            rules = await self.mysql.execute_query(query, params)
            
            # 解析配置JSON
            for rule in rules:
                if rule['condition_config']:
                    rule['condition_config'] = json.loads(rule['condition_config'])
                if rule['threshold_config']:
                    rule['threshold_config'] = json.loads(rule['threshold_config'])
            
            # 缓存结果
            await self.redis.set_json(cache_key, rules, self.cache_ttl)
            
            return rules
            
        except Exception as e:
            logger.error(f"获取告警规则失败: {e}")
            raise
    
    async def get_alert_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取告警规则"""
        cache_key = f"{self.cache_prefix}rule:{rule_id}"
        
        # 尝试从缓存获取
        cached_rule = await self.redis.get_json(cache_key)
        if cached_rule:
            return cached_rule
        
        try:
            query = """
                SELECT 
                    id, rule_name, rule_code, rule_type, metric_type,
                    condition_config, threshold_config, level,
                    status, customer_id, description,
                    created_time, updated_time
                FROM alert_rules
                WHERE id = :rule_id AND del_flag = 0
            """
            
            rule = await self.mysql.execute_first(query, {'rule_id': rule_id})
            
            if rule:
                # 解析配置JSON
                if rule['condition_config']:
                    rule['condition_config'] = json.loads(rule['condition_config'])
                if rule['threshold_config']:
                    rule['threshold_config'] = json.loads(rule['threshold_config'])
                
                # 缓存结果
                await self.redis.set_json(cache_key, rule, self.cache_ttl)
            
            return rule
            
        except Exception as e:
            logger.error(f"获取告警规则失败 {rule_id}: {e}")
            raise
    
    async def create_alert_rule(self, rule_data: Dict[str, Any]) -> str:
        """创建告警规则"""
        try:
            # 检查规则代码是否重复
            existing_rule = await self.mysql.execute_first(
                "SELECT id FROM alert_rules WHERE rule_code = :rule_code AND del_flag = 0",
                {'rule_code': rule_data['rule_code']}
            )
            
            if existing_rule:
                raise ValueError(f"规则代码 {rule_data['rule_code']} 已存在")
            
            # 序列化配置
            if 'condition_config' in rule_data and isinstance(rule_data['condition_config'], dict):
                rule_data['condition_config'] = json.dumps(rule_data['condition_config'])
            
            if 'threshold_config' in rule_data and isinstance(rule_data['threshold_config'], dict):
                rule_data['threshold_config'] = json.dumps(rule_data['threshold_config'])
            
            # 设置默认值
            rule_data.setdefault('status', 1)
            rule_data.setdefault('level', 2)  # 中等级别
            rule_data['created_time'] = datetime.now()
            rule_data['updated_time'] = datetime.now()
            
            query = """
                INSERT INTO alert_rules (
                    rule_name, rule_code, rule_type, metric_type,
                    condition_config, threshold_config, level,
                    status, customer_id, description,
                    created_time, updated_time
                ) VALUES (
                    :rule_name, :rule_code, :rule_type, :metric_type,
                    :condition_config, :threshold_config, :level,
                    :status, :customer_id, :description,
                    :created_time, :updated_time
                )
            """
            
            rule_id = await self.mysql.execute_insert(query, rule_data)
            
            # 清除规则缓存
            await self.clear_alert_rules_cache(rule_data.get('customer_id'))
            
            logger.info(f"告警规则创建成功: {rule_data['rule_name']} (ID: {rule_id})")
            return str(rule_id)
            
        except Exception as e:
            logger.error(f"创建告警规则失败: {e}")
            raise
    
    async def update_alert_rule(self, rule_id: str, update_data: Dict[str, Any]) -> bool:
        """更新告警规则"""
        try:
            # 移除不允许更新的字段
            forbidden_fields = ['id', 'rule_code', 'created_time']
            for field in forbidden_fields:
                update_data.pop(field, None)
            
            if not update_data:
                return True
            
            # 序列化配置
            if 'condition_config' in update_data and isinstance(update_data['condition_config'], dict):
                update_data['condition_config'] = json.dumps(update_data['condition_config'])
            
            if 'threshold_config' in update_data and isinstance(update_data['threshold_config'], dict):
                update_data['threshold_config'] = json.dumps(update_data['threshold_config'])
            
            update_data['updated_time'] = datetime.now()
            
            # 构建更新语句
            set_clause = ', '.join([f"{key} = :{key}" for key in update_data.keys()])
            query = f"""
                UPDATE alert_rules 
                SET {set_clause}
                WHERE id = :rule_id AND del_flag = 0
            """
            
            update_data['rule_id'] = rule_id
            affected_rows = await self.mysql.execute_update(query, update_data)
            
            if affected_rows > 0:
                # 清除缓存
                await self.clear_alert_rule_cache(rule_id)
                logger.info(f"告警规则更新成功: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新告警规则失败 {rule_id}: {e}")
            raise
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """删除告警规则（软删除）"""
        try:
            query = """
                UPDATE alert_rules 
                SET del_flag = 1, updated_time = :updated_time
                WHERE id = :rule_id
            """
            
            affected_rows = await self.mysql.execute_update(query, {
                'updated_time': datetime.now(),
                'rule_id': rule_id
            })
            
            if affected_rows > 0:
                # 清除缓存
                await self.clear_alert_rule_cache(rule_id)
                logger.info(f"告警规则删除成功: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除告警规则失败 {rule_id}: {e}")
            raise
    
    # 告警记录管理
    async def get_alerts(
        self,
        customer_id: Optional[str] = None,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        level: Optional[int] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取告警记录"""
        try:
            conditions = ["a.del_flag = 0"]
            params = {}
            
            if customer_id:
                conditions.append("a.customer_id = :customer_id")
                params['customer_id'] = customer_id
            
            if user_id:
                conditions.append("a.user_id = :user_id")
                params['user_id'] = user_id
            
            if org_id:
                conditions.append("a.org_id = :org_id")
                params['org_id'] = org_id
            
            if level is not None:
                conditions.append("a.level = :level")
                params['level'] = level
            
            if status:
                conditions.append("a.status = :status")
                params['status'] = status
            
            if start_time:
                conditions.append("a.alert_time >= :start_time")
                params['start_time'] = start_time
            
            if end_time:
                conditions.append("a.alert_time <= :end_time")
                params['end_time'] = end_time
            
            where_clause = " AND ".join(conditions)
            
            # 统计总数
            count_query = f"""
                SELECT COUNT(*) as total
                FROM alerts a
                WHERE {where_clause}
            """
            
            total_result = await self.mysql.execute_first(count_query, params)
            total = total_result['total'] if total_result else 0
            
            # 查询数据
            offset = (page - 1) * page_size
            params.update({
                'limit': page_size,
                'offset': offset
            })
            
            query = f"""
                SELECT 
                    a.id, a.rule_id, a.rule_name, a.metric_type,
                    a.alert_value, a.threshold_value, a.level,
                    a.status, a.alert_time, a.resolve_time,
                    a.user_id, a.org_id, a.customer_id,
                    a.description, a.created_time,
                    -- 用户信息
                    u.realname as user_name,
                    -- 组织信息
                    o.org_name
                FROM alerts a
                LEFT JOIN sys_user u ON a.user_id = u.id
                LEFT JOIN sys_org o ON a.org_id = o.id
                WHERE {where_clause}
                ORDER BY a.alert_time DESC
                LIMIT :limit OFFSET :offset
            """
            
            alerts = await self.mysql.execute_query(query, params)
            
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'alerts': alerts
            }
            
        except Exception as e:
            logger.error(f"获取告警记录失败: {e}")
            raise
    
    async def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取告警记录"""
        try:
            query = """
                SELECT 
                    a.id, a.rule_id, a.rule_name, a.metric_type,
                    a.alert_value, a.threshold_value, a.level,
                    a.status, a.alert_time, a.resolve_time,
                    a.user_id, a.org_id, a.customer_id,
                    a.description, a.created_time,
                    -- 用户信息
                    u.realname as user_name,
                    -- 组织信息
                    o.org_name,
                    -- 规则信息
                    r.rule_code, r.condition_config, r.threshold_config
                FROM alerts a
                LEFT JOIN sys_user u ON a.user_id = u.id
                LEFT JOIN sys_org o ON a.org_id = o.id
                LEFT JOIN alert_rules r ON a.rule_id = r.id
                WHERE a.id = :alert_id AND a.del_flag = 0
            """
            
            alert = await self.mysql.execute_first(query, {'alert_id': alert_id})
            
            if alert:
                # 解析配置JSON
                if alert['condition_config']:
                    alert['condition_config'] = json.loads(alert['condition_config'])
                if alert['threshold_config']:
                    alert['threshold_config'] = json.loads(alert['threshold_config'])
            
            return alert
            
        except Exception as e:
            logger.error(f"获取告警记录失败 {alert_id}: {e}")
            raise
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> str:
        """创建告警记录"""
        try:
            alert_data.setdefault('status', 'active')
            alert_data.setdefault('alert_time', datetime.now())
            alert_data['created_time'] = datetime.now()
            
            query = """
                INSERT INTO alerts (
                    rule_id, rule_name, metric_type, alert_value,
                    threshold_value, level, status, alert_time,
                    user_id, org_id, customer_id, description,
                    created_time
                ) VALUES (
                    :rule_id, :rule_name, :metric_type, :alert_value,
                    :threshold_value, :level, :status, :alert_time,
                    :user_id, :org_id, :customer_id, :description,
                    :created_time
                )
            """
            
            alert_id = await self.mysql.execute_insert(query, alert_data)
            
            # 触发告警处理
            await self.alert_processor.process_alert(str(alert_id))
            
            logger.info(f"告警记录创建成功: {alert_data['rule_name']} (ID: {alert_id})")
            return str(alert_id)
            
        except Exception as e:
            logger.error(f"创建告警记录失败: {e}")
            raise
    
    async def resolve_alert(self, alert_id: str, resolver_id: str) -> bool:
        """解决告警"""
        try:
            query = """
                UPDATE alerts 
                SET status = 'resolved', resolve_time = :resolve_time,
                    resolver_id = :resolver_id, updated_time = :updated_time
                WHERE id = :alert_id AND status = 'active'
            """
            
            affected_rows = await self.mysql.execute_update(query, {
                'resolve_time': datetime.now(),
                'resolver_id': resolver_id,
                'updated_time': datetime.now(),
                'alert_id': alert_id
            })
            
            if affected_rows > 0:
                logger.info(f"告警已解决: {alert_id} by {resolver_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"解决告警失败 {alert_id}: {e}")
            raise
    
    # 告警统计
    async def get_alert_statistics(
        self, 
        customer_id: Optional[str] = None,
        time_range: str = '24h'
    ) -> Dict[str, Any]:
        """获取告警统计"""
        cache_key = f"{self.cache_prefix}stats:{customer_id or 'all'}:{time_range}"
        
        # 尝试从缓存获取
        cached_stats = await self.redis.get_json(cache_key)
        if cached_stats:
            return cached_stats
        
        try:
            # 计算时间范围
            if time_range == '1h':
                start_time = datetime.now() - timedelta(hours=1)
            elif time_range == '24h':
                start_time = datetime.now() - timedelta(days=1)
            elif time_range == '7d':
                start_time = datetime.now() - timedelta(days=7)
            elif time_range == '30d':
                start_time = datetime.now() - timedelta(days=30)
            else:
                start_time = datetime.now() - timedelta(days=1)
            
            params = {'start_time': start_time}
            where_clause = "WHERE alert_time >= :start_time AND del_flag = 0"
            
            if customer_id:
                where_clause += " AND customer_id = :customer_id"
                params['customer_id'] = customer_id
            
            # 基础统计
            basic_stats_query = f"""
                SELECT 
                    COUNT(*) as total_alerts,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_alerts,
                    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved_alerts,
                    COUNT(CASE WHEN level = 1 THEN 1 END) as critical_alerts,
                    COUNT(CASE WHEN level = 2 THEN 1 END) as warning_alerts,
                    COUNT(CASE WHEN level = 3 THEN 1 END) as info_alerts
                FROM alerts
                {where_clause}
            """
            
            basic_stats = await self.mysql.execute_first(basic_stats_query, params)
            
            # 按类型统计
            type_stats_query = f"""
                SELECT 
                    metric_type,
                    COUNT(*) as count
                FROM alerts
                {where_clause}
                GROUP BY metric_type
                ORDER BY count DESC
            """
            
            type_stats = await self.mysql.execute_query(type_stats_query, params)
            
            # 时间趋势
            if time_range in ['24h', '7d']:
                date_format = '%Y-%m-%d %H:00:00'
                interval_hours = 1
            else:
                date_format = '%Y-%m-%d'
                interval_hours = 24
            
            trend_query = f"""
                SELECT 
                    DATE_FORMAT(alert_time, '{date_format}') as time_bucket,
                    COUNT(*) as count
                FROM alerts
                {where_clause}
                GROUP BY time_bucket
                ORDER BY time_bucket
            """
            
            trend_data = await self.mysql.execute_query(trend_query, params)
            
            stats = {
                'basic': basic_stats,
                'type_distribution': type_stats,
                'time_trend': trend_data,
                'time_range': time_range,
                'generated_at': datetime.now().isoformat()
            }
            
            # 缓存结果
            await self.redis.set_json(cache_key, stats, 60)  # 1分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"获取告警统计失败: {e}")
            raise
    
    # 实时告警检测
    async def check_health_data_alerts(self, health_data: Dict[str, Any]):
        """检测健康数据告警"""
        try:
            # 获取用户相关的告警规则
            rules = await self.get_alert_rules(
                customer_id=health_data.get('customer_id'),
                status=1
            )
            
            # 使用告警引擎检测
            for rule in rules:
                if await self.alert_engine.evaluate_rule(rule, health_data):
                    # 创建告警
                    alert_data = {
                        'rule_id': rule['id'],
                        'rule_name': rule['rule_name'],
                        'metric_type': rule['metric_type'],
                        'alert_value': health_data.get(rule['metric_type']),
                        'threshold_value': rule['threshold_config'].get('value'),
                        'level': rule['level'],
                        'user_id': health_data.get('user_id'),
                        'org_id': health_data.get('org_id'),
                        'customer_id': health_data.get('customer_id'),
                        'description': f"{rule['rule_name']} - 检测到异常值"
                    }
                    
                    await self.create_alert(alert_data)
            
        except Exception as e:
            logger.error(f"健康数据告警检测失败: {e}")
    
    # 缓存管理
    async def clear_alert_rules_cache(self, customer_id: Optional[str] = None):
        """清除告警规则缓存"""
        try:
            pattern = f"{self.cache_prefix}rules:*"
            if customer_id:
                pattern = f"{self.cache_prefix}rules:{customer_id}:*"
            
            keys = await self.redis.scan_keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            
        except Exception as e:
            logger.error(f"清除告警规则缓存失败: {e}")
    
    async def clear_alert_rule_cache(self, rule_id: str):
        """清除单个告警规则缓存"""
        try:
            cache_key = f"{self.cache_prefix}rule:{rule_id}"
            await self.redis.delete(cache_key)
            
        except Exception as e:
            logger.error(f"清除告警规则缓存失败 {rule_id}: {e}")