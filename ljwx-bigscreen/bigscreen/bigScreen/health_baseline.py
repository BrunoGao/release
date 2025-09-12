#!/usr/bin/env python3
"""健康基线生成和查询模块"""
import pymysql
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from .models import db, HealthBaseline, OrgHealthBaseline, UserHealthData, UserInfo, UserOrg, OrgInfo
from flask import jsonify
import logging
import statistics as py_statistics
from .health_cache_manager import health_cache, cache_result

logger = logging.getLogger(__name__)

class HealthBaselineQuery:
    """健康基线查询服务 - 仅提供查询功能，生成逻辑已迁移至ljwx-boot"""
    
    def __init__(self):
        self.features = ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low', 'stress']
        self.cache = health_cache
        logger.info("健康基线查询服务初始化完成，已集成Redis缓存策略")

def get_baseline_chart_data(org_id, user_id=None, start_date=None, end_date=None):
    """获取基线图表数据 - 集成缓存优化"""
    try:
        if not start_date:
            start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
        # 构建缓存键
        cache_params = {
            'org_id': org_id,
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        # 尝试从缓存获取图表数据
        cached_data = health_cache.get_chart_data('baseline_chart', user_id or org_id, cache_params)
        if cached_data:
            logger.info(f"命中基线图表缓存: org_id={org_id}, user_id={user_id}")
            return cached_data
        
        # 生成日期范围
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        dates = [(start_dt + timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range((end_dt - start_dt).days + 1)]
        
        if user_id:
            # 查询用户基线数据
            baselines = db.session.query(HealthBaseline)\
                .filter(HealthBaseline.user_id == user_id)\
                .filter(HealthBaseline.baseline_date.between(start_dt, end_dt))\
                .all()
        else:
            # 查询组织基线数据
            baselines = db.session.query(OrgHealthBaseline)\
                .filter(OrgHealthBaseline.org_id == org_id)\
                .filter(OrgHealthBaseline.baseline_date.between(start_dt, end_dt))\
                .all()
        
        # 按体征分组数据
        feature_data = {}
        for baseline in baselines:
            feature = baseline.feature_name
            if feature not in feature_data:
                feature_data[feature] = {}
            
            date_str = baseline.baseline_date.strftime('%Y-%m-%d')
            feature_data[feature][date_str] = baseline.mean_value
        
        # 构建图表数据格式
        metrics = []
        feature_config = {
            'heart_rate': {'name': '心率', 'color': '#00D4AA', 'unit': 'bpm', 'normal_range': [60, 100]},
            'blood_oxygen': {'name': '血氧', 'color': '#1890FF', 'unit': '%', 'normal_range': [95, 100]},
            'temperature': {'name': '体温', 'color': '#FAAD14', 'unit': '℃', 'normal_range': [36.0, 37.5]},
            'pressure_high': {'name': '收缩压', 'color': '#F5222D', 'unit': 'mmHg', 'normal_range': [90, 140]},
            'pressure_low': {'name': '舒张压', 'color': '#FA8C16', 'unit': 'mmHg', 'normal_range': [60, 90]},
            'stress': {'name': '压力', 'color': '#722ED1', 'unit': '分', 'normal_range': [20, 60]}
        }
        
        for feature, data in feature_data.items():
            config = feature_config.get(feature, {'name': feature, 'color': '#52C41A', 'unit': '', 'normal_range': []})
            values = []
            
            for date_str in dates:
                value = data.get(date_str)
                if value is not None:
                    values.append(round(float(value), 1))
                else:
                    values.append(None)
            
            metrics.append({
                'name': config['name'],
                'feature': feature,
                'color': config['color'],
                'unit': config['unit'],
                'normal_range': config['normal_range'],
                'values': values,
                'data_count': len([v for v in values if v is not None])
            })
        
        # 按数据量排序，有数据的指标优先显示
        metrics.sort(key=lambda x: x['data_count'], reverse=True)
        
        result = {
            'success': True,
            'dates': dates,
            'metrics': metrics,
            'date_range': f"{start_date} 至 {end_date}",
            'total_days': len(dates),
            'data_source': 'user_baseline' if user_id else 'org_baseline',
            'cached': False
        }
        
        # 缓存结果
        health_cache.cache_chart_data('baseline_chart', user_id or org_id, cache_params, result)
        logger.info(f"基线图表数据已缓存: org_id={org_id}, user_id={user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"获取基线图表数据失败: {e}")
        return {'success': False, 'error': str(e)}

def generate_baseline_task():
    """定时任务：生成基线数据 - 已禁用，功能迁移至ljwx-boot"""
    logger.warning("基线生成任务已禁用，请使用ljwx-boot后端的定时任务")
    return {
        'user_baseline': {'success': True, 'message': '基线生成已迁移至ljwx-boot'},
        'org_baseline': {'success': True, 'message': '基线生成已迁移至ljwx-boot'}
    } 