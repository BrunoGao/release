"""
实时统计模块 - 为大屏提供实时统计数据
包含健康数据、告警信息、消息、设备信息的统计接口
"""

import json
from datetime import datetime, timedelta
from flask import jsonify, request
from models import db, UserHealthData, AlertInfo, DeviceMessage, DeviceInfo, UserInfo
from sqlalchemy import and_, func, desc
import logging

# 配置日志
logger = logging.getLogger(__name__)

def get_realtime_health_stats(customer_id):
    """获取实时健康数据统计"""
    try:
        today = datetime.now().date()
        
        # 获取今日健康数据记录总数
        health_count = db.session.query(UserHealthData).filter(
            and_(
                func.date(UserHealthData.timestamp) == today,
                UserHealthData.customer_id == customer_id
            )
        ).count()
        
        # 计算增长率 (与昨日对比)
        yesterday = today - timedelta(days=1)
        yesterday_count = db.session.query(UserHealthData).filter(
            and_(
                func.date(UserHealthData.timestamp) == yesterday,
                UserHealthData.customer_id == customer_id
            )
        ).count()
        
        # 计算增长率
        if yesterday_count > 0:
            growth_rate = round(((health_count - yesterday_count) / yesterday_count) * 100)
        else:
            growth_rate = 100 if health_count > 0 else 0
            
        return {
            'count': health_count,
            'growth_rate': f"+{growth_rate}%" if growth_rate >= 0 else f"{growth_rate}%",
            'icon': 'health',
            'color': 'cyan'
        }
    except Exception as e:
        logger.error(f"获取健康数据统计失败: {str(e)}")
        return {
            'count': 0,
            'growth_rate': '+0%',
            'icon': 'health',
            'color': 'cyan'
        }

def get_realtime_alert_stats(customer_id):
    """获取实时告警统计"""
    try:
        # 获取待处理告警数量
        pending_alerts = db.session.query(AlertInfo).filter(
            and_(
                AlertInfo.alert_status == 'pending',
                AlertInfo.customer_id == customer_id
            )
        ).count()
        
        # 获取今日新增告警
        today = datetime.now().date()
        today_alerts = db.session.query(AlertInfo).filter(
            and_(
                func.date(AlertInfo.alert_timestamp) == today,
                AlertInfo.customer_id == customer_id
            )
        ).count()
        
        # 计算与昨日对比
        yesterday = today - timedelta(days=1)
        yesterday_alerts = db.session.query(AlertInfo).filter(
            and_(
                func.date(AlertInfo.alert_timestamp) == yesterday,
                AlertInfo.customer_id == customer_id
            )
        ).count()
        
        if yesterday_alerts > 0:
            growth_rate = round(((today_alerts - yesterday_alerts) / yesterday_alerts) * 100)
        else:
            growth_rate = 100 if today_alerts > 0 else 0
            
        return {
            'count': pending_alerts,
            'growth_rate': f"+{growth_rate}%" if growth_rate >= 0 else f"{growth_rate}%",
            'icon': 'alert',
            'color': 'red'
        }
    except Exception as e:
        logger.error(f"获取告警统计失败: {str(e)}")
        return {
            'count': 0,
            'growth_rate': '+0%',
            'icon': 'alert',
            'color': 'red'
        }

def get_realtime_device_stats(customer_id):
    """获取实时设备统计"""
    try:
        # 获取活跃设备数量 (状态为ACTIVE的设备)
        active_devices = db.session.query(DeviceInfo).filter(
            and_(
                DeviceInfo.status == 'ACTIVE',
                DeviceInfo.customer_id == customer_id
            )
        ).count()
        
        # 获取总设备数
        total_devices = db.session.query(DeviceInfo).filter(
            DeviceInfo.customer_id == customer_id
        ).count()
        
        # 计算设备在线率作为增长指标
        if total_devices > 0:
            online_rate = round((active_devices / total_devices) * 100)
        else:
            online_rate = 0
            
        return {
            'count': active_devices,
            'growth_rate': f"+{online_rate}%" if online_rate > 0 else "0%",
            'icon': 'device',
            'color': 'green'
        }
    except Exception as e:
        logger.error(f"获取设备统计失败: {str(e)}")
        return {
            'count': 0,
            'growth_rate': '+0%',
            'icon': 'device',
            'color': 'green'
        }

def get_realtime_message_stats(customer_id):
    """获取实时消息统计"""
    try:
        # 获取未读消息数量 (message_status=1为未读)
        unread_messages = db.session.query(DeviceMessage).filter(
            and_(
                DeviceMessage.message_status == 1,
                DeviceMessage.customer_id == customer_id
            )
        ).count()
        
        # 获取今日消息总数
        today = datetime.now().date()
        today_messages = db.session.query(DeviceMessage).filter(
            and_(
                func.date(DeviceMessage.sent_time) == today,
                DeviceMessage.customer_id == customer_id
            )
        ).count()
        
        # 计算与昨日对比
        yesterday = today - timedelta(days=1)
        yesterday_messages = db.session.query(DeviceMessage).filter(
            and_(
                func.date(DeviceMessage.sent_time) == yesterday,
                DeviceMessage.customer_id == customer_id
            )
        ).count()
        
        if yesterday_messages > 0:
            growth_rate = round(((today_messages - yesterday_messages) / yesterday_messages) * 100)
        else:
            growth_rate = 100 if today_messages > 0 else 0
            
        return {
            'count': unread_messages,
            'growth_rate': f"+{growth_rate}%" if growth_rate >= 0 else f"{growth_rate}%",
            'icon': 'message',
            'color': 'blue'
        }
    except Exception as e:
        logger.error(f"获取消息统计失败: {str(e)}")
        return {
            'count': 0,
            'growth_rate': '+0%',
            'icon': 'message',
            'color': 'blue'
        }

def get_system_alerts_count(customer_id):
    """获取系统告警总数"""
    try:
        # 获取系统级别告警数量
        system_alerts = db.session.query(AlertInfo).filter(
            and_(
                AlertInfo.alert_type.in_(['system_error', 'device_offline', 'data_anomaly']),
                AlertInfo.alert_status == 'pending',
                AlertInfo.customer_id == customer_id
            )
        ).count()
        
        return system_alerts
    except Exception as e:
        logger.error(f"获取系统告警数量失败: {str(e)}")
        return 0

def get_all_realtime_stats(customer_id):
    """获取所有实时统计数据"""
    try:
        stats = {
            'health_data': get_realtime_health_stats(customer_id),
            'alerts': get_realtime_alert_stats(customer_id),  
            'devices': get_realtime_device_stats(customer_id),
            'messages': get_realtime_message_stats(customer_id),
            'system_alerts': get_system_alerts_count(customer_id),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"实时统计数据获取成功 - customer_id: {customer_id}")
        return stats
    except Exception as e:
        logger.error(f"获取实时统计数据失败: {str(e)}")
        return {
            'health_data': {'count': 0, 'growth_rate': '+0%', 'icon': 'health', 'color': 'cyan'},
            'alerts': {'count': 0, 'growth_rate': '+0%', 'icon': 'alert', 'color': 'red'},
            'devices': {'count': 0, 'growth_rate': '+0%', 'icon': 'device', 'color': 'green'},
            'messages': {'count': 0, 'growth_rate': '+0%', 'icon': 'message', 'color': 'blue'},
            'system_alerts': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def get_user_list_by_customer_id(customer_id):
    """根据customer_id获取用户列表"""
    try:
        users = db.session.query(UserInfo).filter(
            UserInfo.customer_id == customer_id
        ).all()
        
        user_list = []
        for user in users:
            user_list.append({
                'user_id': user.id,
                'name': user.name,
                'phone': user.phone,
                'device_sn': user.device_sn,
                'department_name': getattr(user, 'department_name', '未知部门'),
                'status': 'active' if user.device_sn else 'inactive'
            })
        
        return user_list
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return []

def get_detailed_health_stats_by_users(customer_id, user_ids=None):
    """根据用户ID列表获取详细健康统计"""
    try:
        today = datetime.now().date()
        
        # 构建查询条件
        query_conditions = [
            func.date(UserHealthData.timestamp) == today,
            UserHealthData.customer_id == customer_id
        ]
        
        if user_ids:
            query_conditions.append(UserHealthData.user_id.in_(user_ids))
        
        # 获取今日健康数据
        health_records = db.session.query(UserHealthData).filter(
            and_(*query_conditions)
        ).all()
        
        # 统计各项指标
        total_records = len(health_records)
        heart_rate_avg = 0
        blood_pressure_avg = 0
        temperature_avg = 0
        
        if total_records > 0:
            heart_rates = [r.heart_rate for r in health_records if r.heart_rate and r.heart_rate > 0]
            if heart_rates:
                heart_rate_avg = sum(heart_rates) / len(heart_rates)
                
            blood_pressures = [r.pressure_high for r in health_records if r.pressure_high and r.pressure_high > 0]
            if blood_pressures:
                blood_pressure_avg = sum(blood_pressures) / len(blood_pressures)
                
            temperatures = [r.temperature for r in health_records if r.temperature and r.temperature > 0]
            if temperatures:
                temperature_avg = sum(temperatures) / len(temperatures)
        
        return {
            'total_records': total_records,
            'heart_rate_avg': round(heart_rate_avg, 1),
            'blood_pressure_avg': round(blood_pressure_avg, 1),
            'temperature_avg': round(temperature_avg, 1),
            'date': today.strftime('%Y-%m-%d')
        }
    except Exception as e:
        logger.error(f"获取详细健康统计失败: {str(e)}")
        return {
            'total_records': 0,
            'heart_rate_avg': 0,
            'blood_pressure_avg': 0,
            'temperature_avg': 0,
            'date': datetime.now().date().strftime('%Y-%m-%d')
        }