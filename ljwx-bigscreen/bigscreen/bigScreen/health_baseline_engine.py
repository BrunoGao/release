"""
健康基线生成算法引擎
实现多层次健康基线生成：个人基线、群体基线、职位风险基线
"""

import math
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import text, and_, or_
from .models import db, HealthBaseline, UserHealthData, UserInfo, Position, UserPosition
import logging

logger = logging.getLogger(__name__)

class HealthBaselineEngine:
    """健康基线生成算法引擎"""
    
    def __init__(self):
        self.feature_names = ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 
                             'temperature', 'stress', 'step', 'distance', 'calorie', 'sleep']
        self.seasonal_factors = {
            'heart_rate': {'winter': 1.02, 'spring': 1.00, 'summer': 0.98, 'autumn': 1.01},
            'blood_oxygen': {'winter': 0.98, 'spring': 1.00, 'summer': 1.02, 'autumn': 1.00},
            'pressure_high': {'winter': 1.05, 'spring': 1.00, 'summer': 0.96, 'autumn': 1.02},
            'pressure_low': {'winter': 1.03, 'spring': 1.00, 'summer': 0.97, 'autumn': 1.01},
            'temperature': {'winter': 0.99, 'spring': 1.00, 'summer': 1.01, 'autumn': 1.00}
        }
    
    def generate_personal_baseline(self, user_id, customer_id, days_back=30):
        """生成个人健康基线"""
        try:
            baseline_date = date.today()
            start_date = baseline_date - timedelta(days=days_back)
            
            # 获取用户健康数据
            user_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.is_deleted == False
                )
            ).all()
            
            if not user_data:
                logger.warning(f"用户 {user_id} 没有足够的健康数据生成基线")
                return False
            
            # 获取用户信息用于季节性调整
            user = db.session.query(UserInfo).filter_by(id=user_id).first()
            device_sn = user_data[0].device_sn if user_data else None
            
            # 按特征计算基线统计
            baseline_stats = {}
            for feature in self.feature_names:
                values = [getattr(record, feature) for record in user_data 
                         if getattr(record, feature) is not None]
                
                if len(values) >= 5:  # 至少需要5个样本
                    stats = self._calculate_feature_stats(values, feature, baseline_date)
                    baseline_stats[feature] = stats
            
            # 保存个人基线到数据库
            for feature, stats in baseline_stats.items():
                self._save_baseline_record(
                    device_sn=device_sn,
                    user_id=user_id,
                    customer_id=customer_id,
                    feature_name=feature,
                    baseline_date=baseline_date,
                    baseline_type='personal',
                    stats=stats
                )
            
            logger.info(f"成功生成用户 {user_id} 的个人健康基线，包含 {len(baseline_stats)} 个特征")
            return True
            
        except Exception as e:
            logger.error(f"生成个人基线失败: {e}")
            return False
    
    def generate_population_baseline(self, customer_id, age_group=None, gender=None):
        """生成群体健康基线"""
        try:
            baseline_date = date.today()
            start_date = baseline_date - timedelta(days=90)  # 使用90天数据
            
            # 构建查询条件
            query = db.session.query(UserHealthData, UserInfo).join(
                UserInfo, UserHealthData.user_id == UserInfo.id
            ).filter(
                and_(
                    UserHealthData.customer_id == customer_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.is_deleted == False,
                    UserInfo.is_deleted == False
                )
            )
            
            # 添加年龄组过滤
            if age_group:
                if age_group == 'young':
                    query = query.filter(text("YEAR(CURDATE()) - YEAR(birthday) < 30"))
                elif age_group == 'middle':
                    query = query.filter(text("YEAR(CURDATE()) - YEAR(birthday) BETWEEN 30 AND 50"))
                elif age_group == 'senior':
                    query = query.filter(text("YEAR(CURDATE()) - YEAR(birthday) > 50"))
            
            # 添加性别过滤
            if gender:
                query = query.filter(UserInfo.gender == gender)
            
            data_records = query.all()
            
            if len(data_records) < 10:  # 群体基线需要更多样本
                logger.warning(f"群体基线样本不足: {len(data_records)}")
                return False
            
            # 按特征计算群体统计
            baseline_stats = {}
            for feature in self.feature_names:
                values = [getattr(record.UserHealthData, feature) 
                         for record in data_records 
                         if getattr(record.UserHealthData, feature) is not None]
                
                if len(values) >= 10:
                    stats = self._calculate_feature_stats(values, feature, baseline_date)
                    baseline_stats[feature] = stats
            
            # 保存群体基线
            for feature, stats in baseline_stats.items():
                self._save_baseline_record(
                    device_sn=None,
                    user_id=None,
                    customer_id=customer_id,
                    feature_name=feature,
                    baseline_date=baseline_date,
                    baseline_type='population',
                    stats=stats,
                    age_group=age_group,
                    gender=gender
                )
            
            logger.info(f"成功生成客户 {customer_id} 群体基线，年龄组: {age_group}, 性别: {gender}")
            return True
            
        except Exception as e:
            logger.error(f"生成群体基线失败: {e}")
            return False
    
    def generate_position_risk_baseline(self, customer_id, position_id):
        """生成职位风险调整基线"""
        try:
            baseline_date = date.today()
            
            # 获取职位信息
            position = db.session.query(Position).filter_by(
                id=position_id, customer_id=customer_id, is_deleted=False
            ).first()
            
            if not position:
                logger.warning(f"职位 {position_id} 不存在")
                return False
            
            # 获取该职位下的所有用户
            user_positions = db.session.query(UserPosition).filter_by(
                position_id=position_id, is_deleted=False
            ).all()
            
            user_ids = [up.user_id for up in user_positions]
            
            if not user_ids:
                logger.warning(f"职位 {position_id} 下没有用户")
                return False
            
            # 获取职位用户的健康数据
            start_date = baseline_date - timedelta(days=60)
            health_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id.in_(user_ids),
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.customer_id == customer_id,
                    UserHealthData.is_deleted == False
                )
            ).all()
            
            if len(health_data) < 20:  # 职位基线需要足够样本
                logger.warning(f"职位 {position_id} 健康数据样本不足")
                return False
            
            # 计算职位基线并应用风险调整
            baseline_stats = {}
            for feature in self.feature_names:
                values = [getattr(record, feature) for record in health_data 
                         if getattr(record, feature) is not None]
                
                if len(values) >= 10:
                    stats = self._calculate_feature_stats(values, feature, baseline_date)
                    
                    # 应用职位风险调整
                    stats = self._apply_position_risk_adjustment(stats, position, feature)
                    baseline_stats[feature] = stats
            
            # 保存职位基线
            for feature, stats in baseline_stats.items():
                self._save_baseline_record(
                    device_sn=None,
                    user_id=None,
                    customer_id=customer_id,
                    feature_name=feature,
                    baseline_date=baseline_date,
                    baseline_type='position',
                    stats=stats,
                    position_risk_level=position.risk_level
                )
            
            logger.info(f"成功生成职位 {position_id} 的风险调整基线")
            return True
            
        except Exception as e:
            logger.error(f"生成职位基线失败: {e}")
            return False
    
    def _calculate_feature_stats(self, values, feature_name, baseline_date):
        """计算特征统计数据"""
        if not values:
            return None
        
        values_array = np.array(values)
        
        # 基础统计
        stats = {
            'mean_value': float(np.mean(values_array)),
            'std_value': float(np.std(values_array)),
            'min_value': float(np.min(values_array)),
            'max_value': float(np.max(values_array)),
            'sample_count': len(values)
        }
        
        # 应用季节性调整
        season = self._get_season(baseline_date.month)
        if feature_name in self.seasonal_factors:
            factor = self.seasonal_factors[feature_name].get(season, 1.0)
            stats['seasonal_factor'] = factor
            stats['mean_value'] *= factor
        else:
            stats['seasonal_factor'] = 1.0
        
        # 计算置信水平
        if len(values) >= 30:
            stats['confidence_level'] = 0.95
        elif len(values) >= 15:
            stats['confidence_level'] = 0.90
        else:
            stats['confidence_level'] = 0.85
        
        return stats
    
    def _apply_position_risk_adjustment(self, stats, position, feature_name):
        """应用职位风险调整"""
        if not stats or not position:
            return stats
        
        risk_adjustments = {
            'high': {'heart_rate': 0.85, 'blood_oxygen': 1.05, 'pressure_high': 0.90},
            'medium': {'heart_rate': 0.90, 'blood_oxygen': 1.02, 'pressure_high': 0.95},
            'low': {'heart_rate': 1.00, 'blood_oxygen': 1.00, 'pressure_high': 1.00}
        }
        
        risk_level = position.risk_level or 'medium'
        adjustment_factor = risk_adjustments.get(risk_level, {}).get(feature_name, 1.0)
        
        if adjustment_factor != 1.0:
            stats['mean_value'] *= adjustment_factor
            stats['position_risk_adjustment'] = adjustment_factor
        
        return stats
    
    def _save_baseline_record(self, device_sn, user_id, customer_id, feature_name, 
                             baseline_date, baseline_type, stats, age_group=None, 
                             gender=None, position_risk_level=None):
        """保存基线记录到数据库"""
        try:
            # 标记旧基线为非当前
            db.session.query(HealthBaseline).filter(
                and_(
                    HealthBaseline.user_id == user_id if user_id else True,
                    HealthBaseline.customer_id == customer_id,
                    HealthBaseline.feature_name == feature_name,
                    HealthBaseline.baseline_type == baseline_type,
                    HealthBaseline.is_current == True
                )
            ).update({'is_current': False})
            
            # 创建新基线记录
            baseline = HealthBaseline(
                device_sn=device_sn,
                user_id=user_id,
                customer_id=customer_id,
                feature_name=feature_name,
                baseline_date=baseline_date,
                mean_value=stats['mean_value'],
                std_value=stats['std_value'],
                min_value=stats['min_value'],
                max_value=stats['max_value'],
                sample_count=stats['sample_count'],
                is_current=True,
                baseline_type=baseline_type,
                age_group=age_group,
                gender=gender,
                position_risk_level=position_risk_level,
                seasonal_factor=stats.get('seasonal_factor', 1.0),
                confidence_level=stats.get('confidence_level', 0.95),
                baseline_time=datetime.now(),
                create_user='system',
                create_user_id=1
            )
            
            db.session.add(baseline)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存基线记录失败: {e}")
            raise
    
    def _get_season(self, month):
        """获取季节"""
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'
    
    def update_baseline_for_user(self, user_id, customer_id):
        """为指定用户更新基线"""
        try:
            # 生成个人基线
            personal_result = self.generate_personal_baseline(user_id, customer_id)
            
            # 获取用户信息
            user = db.session.query(UserInfo).filter_by(id=user_id).first()
            if user:
                # 确定年龄组
                age_group = self._determine_age_group(user)
                
                # 生成对应的群体基线
                population_result = self.generate_population_baseline(
                    customer_id, age_group, user.gender
                )
                
                # 获取用户职位并生成职位基线
                user_position = db.session.query(UserPosition).filter_by(
                    user_id=user_id, is_deleted=False
                ).first()
                
                if user_position:
                    position_result = self.generate_position_risk_baseline(
                        customer_id, user_position.position_id
                    )
                    return personal_result and population_result and position_result
            
            return personal_result
            
        except Exception as e:
            logger.error(f"更新用户基线失败: {e}")
            return False
    
    def _determine_age_group(self, user):
        """确定用户年龄组"""
        if not hasattr(user, 'birthday') or not user.birthday:
            return 'middle'  # 默认中年
        
        age = (date.today() - user.birthday).days // 365
        if age < 30:
            return 'young'
        elif age <= 50:
            return 'middle'
        else:
            return 'senior'
    
    def get_user_baseline(self, user_id, feature_name=None, baseline_type='personal'):
        """获取用户基线数据"""
        try:
            query = db.session.query(HealthBaseline).filter(
                and_(
                    HealthBaseline.user_id == user_id,
                    HealthBaseline.baseline_type == baseline_type,
                    HealthBaseline.is_current == True
                )
            )
            
            if feature_name:
                query = query.filter(HealthBaseline.feature_name == feature_name)
            
            baselines = query.all()
            
            if not baselines:
                return None
            
            # 转换为字典格式
            baseline_dict = {}
            for baseline in baselines:
                baseline_dict[baseline.feature_name] = {
                    'mean': baseline.mean_value,
                    'std': baseline.std_value,
                    'min': baseline.min_value,
                    'max': baseline.max_value,
                    'sample_count': baseline.sample_count,
                    'confidence_level': baseline.confidence_level,
                    'seasonal_factor': baseline.seasonal_factor
                }
            
            return baseline_dict
            
        except Exception as e:
            logger.error(f"获取用户基线失败: {e}")
            return None
    
    def batch_update_customer_baselines(self, customer_id):
        """批量更新客户下所有用户的基线"""
        try:
            # 获取客户下所有用户
            users = db.session.query(UserInfo).filter(
                and_(
                    UserInfo.customer_id == customer_id,
                    UserInfo.is_deleted == False
                )
            ).all()
            
            success_count = 0
            total_count = len(users)
            
            for user in users:
                if self.update_baseline_for_user(user.id, customer_id):
                    success_count += 1
            
            logger.info(f"批量基线更新完成: {success_count}/{total_count} 成功")
            return success_count, total_count
            
        except Exception as e:
            logger.error(f"批量更新基线失败: {e}")
            return 0, 0
    
    def calculate_baseline_deviation(self, user_id, current_data, feature_name):
        """计算当前数据相对于基线的偏离度"""
        try:
            baseline = self.get_user_baseline(user_id, feature_name)
            
            if not baseline or feature_name not in baseline:
                return None
            
            baseline_info = baseline[feature_name]
            current_value = current_data.get(feature_name)
            
            if current_value is None:
                return None
            
            # 计算Z-Score
            mean = baseline_info['mean']
            std = baseline_info['std']
            
            if std == 0:
                z_score = 0
            else:
                z_score = (current_value - mean) / std
            
            # 计算偏离等级
            if abs(z_score) <= 1:
                deviation_level = 'normal'
            elif abs(z_score) <= 2:
                deviation_level = 'mild'
            elif abs(z_score) <= 3:
                deviation_level = 'moderate'
            else:
                deviation_level = 'severe'
            
            return {
                'z_score': z_score,
                'deviation_level': deviation_level,
                'current_value': current_value,
                'baseline_mean': mean,
                'baseline_std': std,
                'confidence_level': baseline_info['confidence_level']
            }
            
        except Exception as e:
            logger.error(f"计算基线偏离度失败: {e}")
            return None

class BaselineScheduler:
    """基线生成调度器"""
    
    def __init__(self):
        self.engine = HealthBaselineEngine()
    
    def daily_baseline_update(self):
        """每日基线更新任务"""
        try:
            logger.info("开始每日基线更新任务")
            
            # 获取所有活跃客户
            customers = db.session.execute(
                text("SELECT DISTINCT customer_id FROM sys_user WHERE is_deleted = 0")
            ).fetchall()
            
            total_success = 0
            total_processed = 0
            
            for customer in customers:
                customer_id = customer[0]
                success, total = self.engine.batch_update_customer_baselines(customer_id)
                total_success += success
                total_processed += total
            
            logger.info(f"每日基线更新完成: {total_success}/{total_processed} 成功")
            return True
            
        except Exception as e:
            logger.error(f"每日基线更新失败: {e}")
            return False
    
    def weekly_population_baseline_update(self):
        """每周群体基线更新任务"""
        try:
            logger.info("开始每周群体基线更新任务")
            
            # 获取所有客户
            customers = db.session.execute(
                text("SELECT DISTINCT customer_id FROM sys_user WHERE is_deleted = 0")
            ).fetchall()
            
            for customer in customers:
                customer_id = customer[0]
                
                # 为每个年龄组和性别组合生成群体基线
                age_groups = ['young', 'middle', 'senior']
                genders = ['1', '2']  # 1=男, 2=女
                
                for age_group in age_groups:
                    for gender in genders:
                        self.engine.generate_population_baseline(
                            customer_id, age_group, gender
                        )
            
            logger.info("每周群体基线更新完成")
            return True
            
        except Exception as e:
            logger.error(f"每周群体基线更新失败: {e}")
            return False
    
    def get_personal_baseline(self, user_id, device_sn, metrics=None, date_range=30):
        """获取个人基线数据 - API兼容方法"""
        try:
            # 获取用户信息
            from .user import get_user_info_by_deviceSn
            user_info = get_user_info_by_deviceSn(device_sn)
            
            if not user_info:
                logger.error(f"设备 {device_sn} 对应的用户信息不存在")
                return None
                
            customer_id = user_info.get('customer_id', 0)
            
            # 生成基线数据
            baseline_data = self.generate_personal_baseline(user_id, customer_id, date_range)
            
            if not baseline_data:
                return None
            
            # 如果指定了特定指标，过滤返回数据
            if metrics:
                filtered_data = {}
                for metric in metrics:
                    if metric in baseline_data:
                        filtered_data[metric] = baseline_data[metric]
                return filtered_data
            
            return baseline_data
            
        except Exception as e:
            logger.error(f"获取个人基线数据失败: {e}")
            return None