"""
告警系统V2 Python服务层
与Java后端API集成的告警处理服务

Author: bruno.gao
CreateTime: 2025-08-31 - 12:15:00
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from .models import db, AlertInfo, UserInfo, DeviceInfo
from sqlalchemy import and_, or_, func, desc
from .redis_helper import RedisHelper

logger = logging.getLogger(__name__)
redis = RedisHelper()

# 后端API基础URL
BACKEND_API_BASE = "http://localhost:8080"

@dataclass
class AlertV2Model:
    """告警V2数据模型"""
    id: int
    customer_id: int
    user_id: Optional[int]
    device_sn: Optional[str]
    alert_type: str
    alert_desc: str
    level: str
    status: str
    source: str
    metric: Optional[str]
    value: Optional[float]
    unit: Optional[str]
    occur_at: datetime
    acknowledged_time: Optional[datetime]
    recover_at: Optional[datetime]

class AlertV2Service:
    """告警V2服务"""
    
    def __init__(self):
        self.cache_ttl = 300  # 5分钟缓存
    
    def get_alerts_by_conditions(self, conditions: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """根据条件查询告警"""
        try:
            cache_key = f"alerts:conditions:{hash(str(sorted(conditions.items())))}"
            cached = redis.get_cache(cache_key)
            if cached:
                logger.debug(f"命中告警查询缓存: {cache_key}")
                return cached
            
            # 构建查询
            query = db.session.query(AlertInfo)
            
            # 添加查询条件
            if 'customer_id' in conditions:
                query = query.filter(AlertInfo.customer_id == conditions['customer_id'])
            if 'status' in conditions:
                query = query.filter(AlertInfo.alert_status == conditions['status'])
            if 'level' in conditions:
                query = query.filter(AlertInfo.severity_level == conditions['level'])
            if 'user_id' in conditions:
                query = query.filter(AlertInfo.user_id == conditions['user_id'])
            if 'is_deleted' in conditions:
                query = query.filter(AlertInfo.is_deleted == conditions['is_deleted'])
            
            # 执行查询
            alerts = query.order_by(desc(AlertInfo.create_time)).limit(limit).all()
            
            # 转换为字典格式
            result = []
            for alert in alerts:
                alert_dict = {
                    'id': alert.id,
                    'customer_id': alert.customer_id,
                    'user_id': alert.user_id,
                    'device_sn': alert.device_sn,
                    'alert_type': alert.alert_type,
                    'alert_desc': alert.alert_desc,
                    'level': alert.severity_level,
                    'status': alert.alert_status,
                    'occur_at': alert.alert_timestamp.isoformat() if alert.alert_timestamp else None,
                    'create_time': alert.create_time.isoformat() if alert.create_time else None,
                    'update_time': alert.update_time.isoformat() if alert.update_time else None
                }
                result.append(alert_dict)
            
            # 缓存结果
            redis.set_cache(cache_key, result, expire=60)  # 1分钟缓存
            
            logger.info(f"查询告警完成: conditions={conditions}, count={len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"查询告警失败: conditions={conditions}, error={str(e)}")
            return []
    
    def acknowledge_alert_by_id(self, alert_id: int, user_id: Optional[int] = None) -> bool:
        """确认告警"""
        try:
            # 先尝试调用后端API
            api_success = self._call_backend_acknowledge(alert_id, user_id)
            if api_success:
                return True
            
            # 如果API调用失败，直接操作数据库
            alert = db.session.query(AlertInfo).filter(AlertInfo.id == alert_id).first()
            if not alert:
                logger.warning(f"告警不存在: alertId={alert_id}")
                return False
            
            # 更新告警状态
            alert.alert_status = 'acknowledged'
            alert.update_time = datetime.now()
            
            db.session.commit()
            
            # 清除相关缓存
            self._clear_alert_cache(alert.customer_id)
            
            logger.info(f"告警确认成功: alertId={alert_id}, userId={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"确认告警失败: alertId={alert_id}, error={str(e)}")
            db.session.rollback()
            return False
    
    def generate_alert_statistics(self, customer_id: int, start_date: Optional[str] = None, 
                                end_date: Optional[str] = None) -> Dict[str, Any]:
        """生成告警统计数据"""
        try:
            cache_key = f"alert:stats:{customer_id}:{start_date}:{end_date}"
            cached = redis.get_cache(cache_key)
            if cached:
                logger.debug(f"命中告警统计缓存: {cache_key}")
                return cached
            
            # 解析日期范围
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            else:
                start_dt = datetime.now() - timedelta(days=7)
                
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            else:
                end_dt = datetime.now()
            
            # 基础统计查询
            base_query = db.session.query(AlertInfo).filter(
                and_(
                    AlertInfo.customer_id == customer_id,
                    AlertInfo.is_deleted == 0,
                    AlertInfo.alert_timestamp >= start_dt,
                    AlertInfo.alert_timestamp <= end_dt
                )
            )
            
            total_alerts = base_query.count()
            
            # 按状态统计
            status_stats = {}
            for status in ['pending', 'notified', 'acknowledged', 'resolved', 'closed']:
                count = base_query.filter(AlertInfo.alert_status == status).count()
                status_stats[status] = count
            
            # 按级别统计
            level_stats = {}
            for level in ['info', 'minor', 'major', 'critical']:
                count = base_query.filter(AlertInfo.severity_level == level).count()
                level_stats[level] = count
            
            # 按类型统计
            type_stats = db.session.query(
                AlertInfo.alert_type,
                func.count(AlertInfo.id).label('count')
            ).filter(
                and_(
                    AlertInfo.customer_id == customer_id,
                    AlertInfo.is_deleted == 0,
                    AlertInfo.alert_timestamp >= start_dt,
                    AlertInfo.alert_timestamp <= end_dt
                )
            ).group_by(AlertInfo.alert_type).all()
            
            type_distribution = {row.alert_type: row.count for row in type_stats}
            
            # 趋势数据（每日统计）
            daily_stats = []
            current_date = start_dt.date()
            while current_date <= end_dt.date():
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                
                day_count = base_query.filter(
                    and_(
                        AlertInfo.alert_timestamp >= day_start,
                        AlertInfo.alert_timestamp <= day_end
                    )
                ).count()
                
                daily_stats.append({
                    'date': current_date.isoformat(),
                    'count': day_count
                })
                
                current_date += timedelta(days=1)
            
            # 响应时间统计
            acknowledged_alerts = base_query.filter(
                AlertInfo.alert_status.in_(['acknowledged', 'resolved', 'closed'])
            ).all()
            
            response_times = []
            for alert in acknowledged_alerts:
                if alert.alert_timestamp and alert.update_time:
                    response_time = (alert.update_time - alert.alert_timestamp).total_seconds()
                    response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            stats = {
                'total_alerts': total_alerts,
                'status_distribution': status_stats,
                'level_distribution': level_stats,
                'type_distribution': type_distribution,
                'daily_trend': daily_stats,
                'avg_response_time_seconds': round(avg_response_time, 2),
                'date_range': {
                    'start': start_dt.isoformat(),
                    'end': end_dt.isoformat()
                }
            }
            
            # 缓存结果
            redis.set_cache(cache_key, stats, expire=self.cache_ttl)
            
            logger.info(f"生成告警统计完成: customerId={customer_id}, total={total_alerts}")
            return stats
            
        except Exception as e:
            logger.error(f"生成告警统计失败: customerId={customer_id}, error={str(e)}")
            return {
                'total_alerts': 0,
                'status_distribution': {},
                'level_distribution': {},
                'type_distribution': {},
                'daily_trend': [],
                'avg_response_time_seconds': 0,
                'error': str(e)
            }
    
    def _call_backend_acknowledge(self, alert_id: int, user_id: Optional[int]) -> bool:
        """调用后端API确认告警"""
        try:
            url = f"{BACKEND_API_BASE}/alert/management/{alert_id}/acknowledge"
            params = {}
            if user_id:
                params['userId'] = user_id
                
            response = requests.post(url, params=params, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                logger.warning(f"后端API确认告警失败: status={response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"调用后端API确认告警异常: alertId={alert_id}, error={str(e)}")
            return False
    
    def _clear_alert_cache(self, customer_id: int):
        """清除告警相关缓存"""
        try:
            patterns = [
                f"alerts:conditions:*{customer_id}*",
                f"alert:stats:{customer_id}:*"
            ]
            
            for pattern in patterns:
                redis.delete_pattern(pattern)
                
            logger.debug(f"清除告警缓存: customerId={customer_id}")
            
        except Exception as e:
            logger.error(f"清除告警缓存失败: customerId={customer_id}, error={str(e)}")

# 全局服务实例
alert_v2_service = AlertV2Service()

# 导出函数供routes.py使用
def get_alerts_by_conditions(conditions: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
    return alert_v2_service.get_alerts_by_conditions(conditions, limit)

def acknowledge_alert_by_id(alert_id: int, user_id: Optional[int] = None) -> bool:
    return alert_v2_service.acknowledge_alert_by_id(alert_id, user_id)

def generate_alert_statistics(customer_id: int, start_date: Optional[str] = None, 
                            end_date: Optional[str] = None) -> Dict[str, Any]:
    return alert_v2_service.generate_alert_statistics(customer_id, start_date, end_date)