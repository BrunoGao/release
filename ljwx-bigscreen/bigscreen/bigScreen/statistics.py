#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统计数据模块 - Statistics Module
提供系统统计数据相关功能
"""

from datetime import date, timedelta, datetime
from flask import request, jsonify, current_app
from sqlalchemy import func, and_
from .models import db, UserHealthData, DeviceInfo, AlertInfo, DeviceMessage
import logging

logger = logging.getLogger(__name__)


def get_realtime_stats_data():
    """获取实时统计数据API - 支持日期对比"""
    try:
        customer_id = request.args.get('customerId')
        selected_date = request.args.get('date')  # 新增日期参数
        
        if not customer_id:
            return {
                "success": False,
                "error": "customerId参数是必需的"
            }, 400
        
        # 解析选中的日期，默认为今天
        if selected_date:
            try:
                target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                target_date = date.today()
        else:
            target_date = date.today()
            
        # 对比日期（上一个工作日）
        def get_previous_workday(date_obj):
            """获取上一个工作日（周一到周五）"""
            prev_date = date_obj - timedelta(days=1)
            # 如果是周末，继续往前找到上一个周五
            while prev_date.weekday() > 4:  # weekday(): 周一=0, 周日=6
                prev_date = prev_date - timedelta(days=1)
            return prev_date
        
        compare_date = get_previous_workday(target_date)
        
        # 计算统计数据的函数
        def get_stats_for_date(query_date, is_current=True):
            # 健康数据统计
            health_query = db.session.query(func.count(UserHealthData.id)).join(
                DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id,
                func.date(UserHealthData.timestamp) == query_date
            )
            health_count = health_query.scalar() or 0
            
            # 告警统计
            alert_query = db.session.query(func.count(AlertInfo.id)).join(
                DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number  
            ).filter(
                DeviceInfo.org_id == customer_id,
                func.date(AlertInfo.alert_timestamp) == query_date
            )
            alert_count = alert_query.scalar() or 0
            
            # 消息统计
            message_query = db.session.query(func.count(DeviceMessage.id)).join(
                DeviceInfo, DeviceMessage.device_sn == DeviceInfo.serial_number
            ).filter(
                DeviceInfo.org_id == customer_id,
                func.date(DeviceMessage.create_time) == query_date
            )
            message_count = message_query.scalar() or 0
            
            # 设备统计
            device_count = db.session.query(func.count(DeviceInfo.id)).filter(
                DeviceInfo.org_id == customer_id
            ).scalar() or 0
            
            return {
                "health_data": health_count,
                "alerts": alert_count, 
                "messages": message_count,
                "devices": device_count,
                "date": query_date.strftime('%Y-%m-%d')
            }
        
        # 获取当前日期和对比日期的统计
        current_stats = get_stats_for_date(target_date, True)
        compare_stats = get_stats_for_date(compare_date, False)
        
        # 计算变化百分比
        def calculate_change(current, previous):
            if previous == 0:
                return "+100%" if current > 0 else "0%"
            change = ((current - previous) / previous) * 100
            return f"{change:+.1f}%"
        
        result = {
            "success": True,
            "data": {
                "current": current_stats,
                "compare": compare_stats,
                "changes": {
                    "health_data": calculate_change(current_stats["health_data"], compare_stats["health_data"]),
                    "alerts": calculate_change(current_stats["alerts"], compare_stats["alerts"]),
                    "messages": calculate_change(current_stats["messages"], compare_stats["messages"]),
                    "devices": calculate_change(current_stats["devices"], compare_stats["devices"])
                },
                "summary": {
                    "total_health_data": current_stats["health_data"],
                    "total_alerts": current_stats["alerts"],
                    "total_messages": current_stats["messages"], 
                    "total_devices": current_stats["devices"],
                    "query_date": target_date.strftime('%Y-%m-%d'),
                    "compare_date": compare_date.strftime('%Y-%m-%d')
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"实时统计查询成功: {customer_id}, 目标日期: {target_date}, 对比日期: {compare_date}")
        return result, 200
        
    except Exception as e:
        error_msg = f"实时统计查询失败: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }, 500


def get_statistics_overview_data():
    """统计概览接口数据"""
    try:
        customer_id = request.args.get('customerId', 1)
        days = int(request.args.get('days', 7))
        
        # 时间范围计算
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 基础统计查询
        stats = {}
        
        # 健康数据统计
        health_count = db.session.query(func.count(UserHealthData.id)).join(
            DeviceInfo, UserHealthData.device_sn == DeviceInfo.serial_number
        ).filter(
            DeviceInfo.org_id == customer_id,
            UserHealthData.timestamp >= start_date
        ).scalar() or 0
        
        # 告警统计
        alert_count = db.session.query(func.count(AlertInfo.id)).join(
            DeviceInfo, AlertInfo.device_sn == DeviceInfo.serial_number
        ).filter(
            DeviceInfo.org_id == customer_id,
            AlertInfo.alert_timestamp >= start_date
        ).scalar() or 0
        
        # 设备数量
        device_count = db.session.query(func.count(DeviceInfo.id)).filter(
            DeviceInfo.org_id == customer_id
        ).scalar() or 0
        
        # 消息数量
        message_count = db.session.query(func.count(DeviceMessage.id)).join(
            DeviceInfo, DeviceMessage.device_sn == DeviceInfo.serial_number
        ).filter(
            DeviceInfo.org_id == customer_id,
            DeviceMessage.create_time >= start_date
        ).scalar() or 0
        
        result = {
            "success": True,
            "data": {
                "overview": {
                    "health_data_count": health_count,
                    "alert_count": alert_count,
                    "device_count": device_count,
                    "message_count": message_count
                },
                "time_range": {
                    "start_date": start_date.strftime('%Y-%m-%d'),
                    "end_date": end_date.strftime('%Y-%m-%d'),
                    "days": days
                },
                "customer_id": customer_id
            },
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"统计概览查询成功: customer_id={customer_id}, days={days}")
        return result, 200
        
    except Exception as e:
        error_msg = f"统计概览查询失败: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }, 500