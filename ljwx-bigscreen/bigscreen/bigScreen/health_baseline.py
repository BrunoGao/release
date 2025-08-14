#!/usr/bin/env python3
"""健康基线生成和查询模块"""
import pymysql
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from .models import db, HealthBaseline, OrgHealthBaseline, UserHealthData, UserInfo, UserOrg, OrgInfo
from flask import jsonify
import logging
import statistics

logger = logging.getLogger(__name__)

class HealthBaselineGenerator:
    """健康基线生成器"""
    
    def __init__(self):
        self.features = ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low', 'stress']  # 支持的体征
    
    def generate_daily_user_baseline(self, target_date=None):
        """生成每日用户基线"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)  # 默认生成昨天的基线
        
        try:
            # 获取所有有数据的用户
            users_with_data = db.session.query(UserHealthData.user_id, UserHealthData.device_sn)\
                .filter(func.date(UserHealthData.create_time) == target_date)\
                .filter(UserHealthData.is_deleted == False)\
                .filter(UserHealthData.user_id.isnot(None))\
                .distinct().all()
            
            generated_count = 0
            for user_id, device_sn in users_with_data:
                for feature in self.features:
                    baseline = self._calculate_user_feature_baseline(user_id, device_sn, feature, target_date)
                    if baseline:
                        self._save_user_baseline(user_id, device_sn, feature, target_date, baseline)
                        generated_count += 1
            
            logger.info(f"生成用户基线完成: {target_date}, 共{generated_count}条")
            return {'success': True, 'count': generated_count, 'date': target_date.strftime('%Y-%m-%d')}
            
        except Exception as e:
            logger.error(f"生成用户基线失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_daily_org_baseline(self, target_date=None):
        """生成每日组织基线 - 暂时简化实现"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        try:
            logger.info(f"组织基线生成暂时跳过，等待表结构完善: {target_date}")
            return {'success': True, 'count': 0, 'date': target_date.strftime('%Y-%m-%d'), 'message': '组织基线功能暂时禁用'}
            
        except Exception as e:
            logger.error(f"生成组织基线失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_user_feature_baseline(self, user_id, device_sn, feature, target_date):
        """计算用户特定体征的基线"""
        try:
            # 查询用户当天的健康数据
            query = db.session.query(getattr(UserHealthData, feature))\
                .filter(UserHealthData.device_sn == device_sn)\
                .filter(func.date(UserHealthData.create_time) == target_date)\
                .filter(UserHealthData.is_deleted == False)\
                .filter(getattr(UserHealthData, feature).isnot(None))
            
            values = [float(v[0]) for v in query.all() if v[0] is not None]
            
            if len(values) < 3:  # 至少需要3个数据点
                return None
            
            baseline_data = {
                'mean_value': statistics.mean(values),
                'std_value': statistics.stdev(values) if len(values) > 1 else 0,
                'min_value': min(values),
                'max_value': max(values),
                'sample_count': len(values) if hasattr(HealthBaseline, 'sample_count') else None
            }
            
            # 移除sample_count如果表中不存在此字段
            if baseline_data['sample_count'] is None:
                del baseline_data['sample_count']
            
            return baseline_data
            
        except Exception as e:
            logger.error(f"计算用户基线失败 device_sn={device_sn}, feature={feature}: {e}")
            return None
    
    def _calculate_org_feature_baseline(self, org_id, feature, target_date):
        """计算组织特定体征的基线 - 修复字段映射"""
        try:
            # 查询组织下所有用户的基线数据 - 使用实际存在的字段
            user_baselines = db.session.query(HealthBaseline)\
                .join(UserOrg, text("find_in_set(:device_sn, (SELECT GROUP_CONCAT(u.device_sn) FROM sys_user u JOIN sys_user_org uo ON u.id = uo.user_id WHERE uo.org_id = :org_id))"))\
                .filter(HealthBaseline.feature_name == feature)\
                .filter(func.date(HealthBaseline.baseline_time) == target_date)\
                .params(org_id=org_id, device_sn=HealthBaseline.device_sn)\
                .all()
            
            if len(user_baselines) < 1:  # 至少需要1个用户的数据
                return None
            
            mean_values = [b.mean_value for b in user_baselines if b.mean_value is not None]
            all_samples = sum(b.sample_count or 0 for b in user_baselines)
            
            if not mean_values:
                return None
            
            return {
                'mean_value': statistics.mean(mean_values),
                'std_value': statistics.stdev(mean_values) if len(mean_values) > 1 else 0,
                'min_value': min(b.min_value for b in user_baselines if b.min_value is not None),
                'max_value': max(b.max_value for b in user_baselines if b.max_value is not None),
                'user_count': len(user_baselines),
                'sample_count': all_samples
            }
            
        except Exception as e:
            logger.error(f"计算组织基线失败 org_id={org_id}, feature={feature}: {e}")
            return None
    
    def _save_user_baseline(self, user_id, device_sn, feature, baseline_date, baseline_data):
        """保存用户基线"""
        try:
            # 检查是否已存在 - 基于实际表结构，使用baseline_time的日期部分
            existing = HealthBaseline.query.filter_by(
                device_sn=device_sn, 
                feature_name=feature
            ).filter(
                func.date(HealthBaseline.baseline_time) == baseline_date
            ).first()
            
            if existing:
                # 更新现有记录
                for key, value in baseline_data.items():
                    setattr(existing, key, value)
                existing.update_time = datetime.now()
            else:
                # 创建新记录 - 使用实际存在的字段
                baseline = HealthBaseline(
                    device_sn=device_sn,
                    feature_name=feature,
                    baseline_time=datetime.combine(baseline_date, datetime.min.time()),  # 使用baseline_time而不是baseline_date
                    is_current=True,
                    **baseline_data
                )
                db.session.add(baseline)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存用户基线失败: {e}")
    
    def _save_org_baseline(self, org_id, feature, baseline_date, baseline_data):
        """保存组织基线"""
        try:
            # 检查是否已存在
            existing = OrgHealthBaseline.query.filter_by(
                org_id=org_id, feature_name=feature, baseline_date=baseline_date
            ).first()
            
            if existing:
                # 更新现有记录
                for key, value in baseline_data.items():
                    setattr(existing, key, value)
                existing.update_time = datetime.now()
            else:
                # 创建新记录
                baseline = OrgHealthBaseline(
                    org_id=org_id,
                    feature_name=feature,
                    baseline_date=baseline_date,
                    **baseline_data
                )
                db.session.add(baseline)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存组织基线失败: {e}")

def get_baseline_chart_data(org_id, user_id=None, start_date=None, end_date=None):
    """获取基线图表数据"""
    try:
        if not start_date:
            start_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        
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
        
        return {
            'success': True,
            'dates': dates,
            'metrics': metrics,
            'date_range': f"{start_date} 至 {end_date}",
            'total_days': len(dates),
            'data_source': 'user_baseline' if user_id else 'org_baseline'
        }
        
    except Exception as e:
        logger.error(f"获取基线图表数据失败: {e}")
        return {'success': False, 'error': str(e)}

def generate_baseline_task():
    """定时任务：生成基线数据"""
    generator = HealthBaselineGenerator()
    
    # 生成用户基线
    user_result = generator.generate_daily_user_baseline()
    
    # 生成组织基线
    org_result = generator.generate_daily_org_baseline()
    
    return {
        'user_baseline': user_result,
        'org_baseline': org_result
    } 