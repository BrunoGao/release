"""
综合健康画像生成引擎
实现多维度用户健康画像构建、趋势分析和可视化数据生成
"""

import json
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, text
from .models import db, UserHealthData, UserInfo, Position, UserPosition, AlertInfo, UserHealthProfile
from .health_baseline_engine import HealthBaselineEngine
from .health_score_engine import HealthScoreEngine
from .health_recommendation_engine import HealthRecommendationEngine
import logging

logger = logging.getLogger(__name__)

class HealthProfileEngine:
    """综合健康画像生成引擎"""
    
    def __init__(self):
        self.baseline_engine = HealthBaselineEngine()
        self.score_engine = HealthScoreEngine()
        self.recommendation_engine = HealthRecommendationEngine()
    
    def generate_comprehensive_health_profile(self, user_id, customer_id):
        """生成综合健康画像"""
        try:
            logger.info(f"开始生成用户 {user_id} 的综合健康画像")
            
            # 1. 获取用户基础信息
            user_basic_info = self._get_user_basic_info(user_id)
            
            # 2. 计算当前健康状态
            current_health_status = self._get_current_health_status(user_id, customer_id)
            
            # 3. 获取健康指标分析
            health_metrics_analysis = self._get_health_metrics_analysis(user_id, customer_id)
            
            # 4. 分析行为模式
            behavioral_analysis = self._get_behavioral_analysis(user_id)
            
            # 5. 进行风险评估
            risk_assessment = self._get_risk_assessment(user_id, customer_id)
            
            # 6. 分析健康趋势
            health_trends = self._get_health_trends(user_id)
            
            # 7. 生成个性化建议
            personalized_recommendations = self.recommendation_engine.generate_personalized_recommendations(
                user_id, customer_id
            )
            
            # 8. 设定健康目标
            health_goals = self._generate_personalized_goals(user_id, current_health_status)
            
            # 9. 创建监测计划
            monitoring_plan = self._create_monitoring_plan(user_id, risk_assessment)
            
            # 10. 构建完整健康画像
            health_profile = {
                'profile_id': f"HP_{user_id}_{datetime.now().strftime('%Y%m%d')}",
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'user_basic_info': user_basic_info,
                'current_health_status': current_health_status,
                'health_metrics_analysis': health_metrics_analysis,
                'behavioral_analysis': behavioral_analysis,
                'risk_assessment': risk_assessment,
                'health_trends': health_trends,
                'personalized_recommendations': personalized_recommendations,
                'health_goals': health_goals,
                'monitoring_plan': monitoring_plan,
                'profile_summary': self._generate_profile_summary(current_health_status, risk_assessment)
            }
            
            # 11. 保存健康画像到数据库
            self._save_health_profile(user_id, customer_id, health_profile)
            
            logger.info(f"用户 {user_id} 健康画像生成完成")
            return health_profile
            
        except Exception as e:
            logger.error(f"生成综合健康画像失败: {e}")
            return None
    
    def _get_user_basic_info(self, user_id):
        """获取用户基础信息"""
        try:
            user = db.session.query(UserInfo).filter_by(id=user_id).first()
            
            if not user:
                return {}
            
            # 获取职位信息
            position_info = db.session.query(Position).join(
                UserPosition, Position.id == UserPosition.position_id
            ).filter(
                and_(
                    UserPosition.user_id == user_id,
                    UserPosition.is_deleted == False,
                    Position.is_deleted == False
                )
            ).first()
            
            # 获取设备信息
            latest_health_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.is_deleted == False
                )
            ).order_by(UserHealthData.timestamp.desc()).first()
            
            basic_info = {
                'user_id': user_id,
                'user_name': user.user_name,
                'real_name': user.real_name,
                'gender': user.gender,
                'phone': user.phone,
                'working_years': user.working_years,
                'customer_id': user.customer_id,
                'device_sn': latest_health_data.device_sn if latest_health_data else None,
                'registration_date': user.create_time.strftime('%Y-%m-%d') if user.create_time else None
            }
            
            if position_info:
                basic_info.update({
                    'position_name': position_info.name,
                    'position_risk_level': position_info.risk_level,
                    'position_weight': float(position_info.weight) if position_info.weight else 0.15,
                    'org_id': position_info.org_id
                })
            
            return basic_info
            
        except Exception as e:
            logger.error(f"获取用户基础信息失败: {e}")
            return {}
    
    def _get_current_health_status(self, user_id, customer_id):
        """获取当前健康状态"""
        try:
            # 计算综合健康评分
            health_score = self.score_engine.calculate_comprehensive_health_score(
                user_id, customer_id
            )
            
            if not health_score:
                return {}
            
            # 获取最新健康数据
            latest_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.is_deleted == False
                )
            ).order_by(UserHealthData.timestamp.desc()).first()
            
            # 获取关键健康指标
            key_indicators = {}
            if latest_data:
                key_indicators = {
                    'heart_rate': latest_data.heart_rate,
                    'blood_oxygen': latest_data.blood_oxygen,
                    'pressure_high': latest_data.pressure_high,
                    'pressure_low': latest_data.pressure_low,
                    'temperature': float(latest_data.temperature) if latest_data.temperature else None,
                    'stress': latest_data.stress,
                    'last_update': latest_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # 识别紧急关注点
            immediate_concerns = self._identify_immediate_concerns(latest_data, health_score)
            
            return {
                'overall_health_score': health_score['total_score'],
                'health_level': health_score['score_level'],
                'dimension_scores': {
                    'physiological': health_score['physiological_score'],
                    'behavioral': health_score['behavioral_score'],
                    'risk_factor': health_score['risk_factor_score']
                },
                'detailed_scores': health_score['detailed_breakdown'],
                'key_health_indicators': key_indicators,
                'immediate_concerns': immediate_concerns,
                'last_assessment': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"获取当前健康状态失败: {e}")
            return {}
    
    def _get_health_metrics_analysis(self, user_id, customer_id):
        """获取健康指标分析"""
        try:
            # 获取最近30天的健康数据
            recent_data = self._get_recent_health_data(user_id, 30)
            
            if not recent_data:
                return {}
            
            # 分析各系统健康状况
            cardiovascular_analysis = self._analyze_cardiovascular_system(recent_data)
            respiratory_analysis = self._analyze_respiratory_system(recent_data)
            metabolic_analysis = self._analyze_metabolic_system(recent_data)
            psychological_analysis = self._analyze_psychological_state(recent_data)
            
            return {
                'cardiovascular': cardiovascular_analysis,
                'respiratory': respiratory_analysis,
                'metabolic': metabolic_analysis,
                'psychological': psychological_analysis,
                'analysis_period': '30天',
                'data_quality': {
                    'total_records': len(recent_data),
                    'data_completeness': self._calculate_data_completeness(recent_data)
                }
            }
            
        except Exception as e:
            logger.error(f"获取健康指标分析失败: {e}")
            return {}
    
    def _get_behavioral_analysis(self, user_id):
        """分析用户行为模式"""
        try:
            # 获取最近90天的数据用于行为分析
            activity_data = self._get_recent_health_data(user_id, 90)
            
            if not activity_data:
                return {}
            
            # 活动模式分析
            activity_patterns = self._analyze_activity_patterns(activity_data)
            
            # 睡眠模式分析
            sleep_patterns = self._analyze_sleep_patterns(activity_data)
            
            # 健康参与度分析
            health_engagement = self._analyze_health_engagement(user_id, activity_data)
            
            return {
                'activity_patterns': activity_patterns,
                'sleep_patterns': sleep_patterns,
                'health_engagement': health_engagement,
                'analysis_period': '90天',
                'behavior_summary': self._generate_behavior_summary(
                    activity_patterns, sleep_patterns, health_engagement
                )
            }
            
        except Exception as e:
            logger.error(f"分析用户行为模式失败: {e}")
            return {}
    
    def _get_risk_assessment(self, user_id, customer_id):
        """进行风险评估"""
        try:
            # 获取告警历史
            alert_history = self._get_alert_history(user_id, 60)
            
            # 分析当前风险等级
            current_risk = self._assess_current_risk_level(user_id, alert_history)
            
            # 预测未来风险
            future_risk = self._predict_future_risk(user_id, customer_id)
            
            # 识别风险因子
            risk_factors = self._identify_risk_factors(user_id, alert_history)
            
            # 识别保护因子
            protective_factors = self._identify_protective_factors(user_id)
            
            return {
                'current_risk_level': current_risk['level'],
                'risk_score': current_risk['score'],
                'future_risk_prediction': future_risk,
                'risk_factors': risk_factors,
                'protective_factors': protective_factors,
                'risk_assessment_date': datetime.now().strftime('%Y-%m-%d'),
                'risk_trend': self._calculate_risk_trend(alert_history)
            }
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return {}
    
    def _get_health_trends(self, user_id):
        """分析健康趋势变化"""
        try:
            # 获取6个月的历史数据
            historical_data = self._get_recent_health_data(user_id, 180)
            
            if not historical_data:
                return {}
            
            trends = {}
            metrics = ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 'stress']
            
            for metric in metrics:
                metric_data = [getattr(record, metric) for record in historical_data 
                              if getattr(record, metric) is not None]
                
                if len(metric_data) >= 10:
                    # 趋势分析
                    trend_analysis = self._analyze_metric_trend(metric_data, metric)
                    trends[metric] = trend_analysis
            
            return trends
            
        except Exception as e:
            logger.error(f"分析健康趋势失败: {e}")
            return {}
    
    def _analyze_metric_trend(self, metric_data, metric_name):
        """分析单个指标的趋势"""
        try:
            # 计算线性趋势
            x = np.arange(len(metric_data))
            y = np.array(metric_data)
            
            # 线性回归计算趋势斜率
            trend_slope = np.polyfit(x, y, 1)[0]
            
            # 计算稳定性
            stability_score = 100 - min(np.std(y) / np.mean(y) * 100, 50)
            
            # 异常点检测
            q75, q25 = np.percentile(y, [75, 25])
            iqr = q75 - q25
            lower_bound = q25 - (iqr * 1.5)
            upper_bound = q75 + (iqr * 1.5)
            
            anomalies = [i for i, val in enumerate(y) if val < lower_bound or val > upper_bound]
            anomaly_frequency = len(anomalies) / len(y)
            
            # 季节性分析（简化版本）
            seasonal_pattern = self._detect_seasonal_pattern(metric_data, metric_name)
            
            return {
                'trend_direction': 'improving' if trend_slope < -0.1 else 'deteriorating' if trend_slope > 0.1 else 'stable',
                'trend_strength': abs(trend_slope),
                'stability_score': round(stability_score, 2),
                'anomaly_frequency': round(anomaly_frequency, 3),
                'seasonal_variation': seasonal_pattern,
                'data_quality': {
                    'sample_count': len(metric_data),
                    'data_span_days': 180,
                    'completeness': len(metric_data) / 180
                }
            }
            
        except Exception as e:
            logger.error(f"分析指标趋势失败: {e}")
            return {}
    
    def _save_health_profile(self, user_id, customer_id, health_profile):
        """保存健康画像到数据库"""
        try:
            profile_date = date.today()
            
            # 检查是否已存在今日画像
            existing_profile = db.session.query(UserHealthProfile).filter(
                and_(
                    UserHealthProfile.user_id == user_id,
                    UserHealthProfile.profile_date == profile_date,
                    UserHealthProfile.is_deleted == False
                )
            ).first()
            
            current_status = health_profile['current_health_status']
            detailed_scores = current_status.get('detailed_scores', {})
            
            if existing_profile:
                # 更新现有记录
                existing_profile.overall_health_score = current_status.get('overall_health_score', 0)
                existing_profile.health_level = current_status.get('health_level', 'fair')
                existing_profile.physiological_score = current_status.get('dimension_scores', {}).get('physiological', 0)
                existing_profile.behavioral_score = current_status.get('dimension_scores', {}).get('behavioral', 0)
                existing_profile.risk_factor_score = current_status.get('dimension_scores', {}).get('risk_factor', 0)
                existing_profile.cardiovascular_score = detailed_scores.get('cardiovascular_score', 0)
                existing_profile.respiratory_score = detailed_scores.get('respiratory_score', 0)
                existing_profile.metabolic_score = detailed_scores.get('metabolic_score', 0)
                existing_profile.psychological_score = detailed_scores.get('psychological_score', 0)
                existing_profile.activity_consistency_score = detailed_scores.get('activity_consistency_score', 0)
                existing_profile.sleep_quality_score = detailed_scores.get('sleep_quality_score', 0)
                existing_profile.health_engagement_score = detailed_scores.get('health_engagement_score', 0)
                existing_profile.current_risk_level = health_profile['risk_assessment'].get('current_risk_level', 'medium')
                existing_profile.predicted_risk_score = health_profile['risk_assessment'].get('future_risk_prediction', {}).get('risk_score', 0)
                existing_profile.detailed_analysis = health_profile['health_metrics_analysis']
                existing_profile.trend_analysis = health_profile['health_trends']
                existing_profile.recommendations = health_profile['personalized_recommendations']
                existing_profile.update_time = datetime.now()
                existing_profile.version += 1
                
            else:
                # 创建新记录
                new_profile = UserHealthProfile(
                    user_id=user_id,
                    customer_id=customer_id,
                    profile_date=profile_date,
                    overall_health_score=current_status.get('overall_health_score', 0),
                    health_level=current_status.get('health_level', 'fair'),
                    physiological_score=current_status.get('dimension_scores', {}).get('physiological', 0),
                    behavioral_score=current_status.get('dimension_scores', {}).get('behavioral', 0),
                    risk_factor_score=current_status.get('dimension_scores', {}).get('risk_factor', 0),
                    cardiovascular_score=detailed_scores.get('cardiovascular_score', 0),
                    respiratory_score=detailed_scores.get('respiratory_score', 0),
                    metabolic_score=detailed_scores.get('metabolic_score', 0),
                    psychological_score=detailed_scores.get('psychological_score', 0),
                    activity_consistency_score=detailed_scores.get('activity_consistency_score', 0),
                    sleep_quality_score=detailed_scores.get('sleep_quality_score', 0),
                    health_engagement_score=detailed_scores.get('health_engagement_score', 0),
                    current_risk_level=health_profile['risk_assessment'].get('current_risk_level', 'medium'),
                    predicted_risk_score=health_profile['risk_assessment'].get('future_risk_prediction', {}).get('risk_score', 0),
                    detailed_analysis=health_profile['health_metrics_analysis'],
                    trend_analysis=health_profile['health_trends'],
                    recommendations=health_profile['personalized_recommendations'],
                    create_time=datetime.now(),
                    update_time=datetime.now(),
                    is_deleted=False,
                    version=1
                )
                
                db.session.add(new_profile)
            
            db.session.commit()
            logger.info(f"用户 {user_id} 健康画像已保存到数据库")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存健康画像失败: {e}")
            return False
    
    def _get_recent_health_data(self, user_id, days_back):
        """获取最近的健康数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            health_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.is_deleted == False
                )
            ).order_by(UserHealthData.timestamp.desc()).all()
            
            return health_data
            
        except Exception as e:
            logger.error(f"获取最近健康数据失败: {e}")
            return []
    
    def _analyze_cardiovascular_system(self, health_data):
        """分析心血管系统"""
        try:
            heart_rates = [record.heart_rate for record in health_data if record.heart_rate]
            pressures_high = [record.pressure_high for record in health_data if record.pressure_high]
            pressures_low = [record.pressure_low for record in health_data if record.pressure_low]
            
            analysis = {}
            
            if heart_rates:
                analysis['heart_rate'] = {
                    'average': round(np.mean(heart_rates), 2),
                    'variability': round(np.std(heart_rates), 2),
                    'min': int(np.min(heart_rates)),
                    'max': int(np.max(heart_rates)),
                    'trend': self._calculate_simple_trend(heart_rates)
                }
            
            if pressures_high and pressures_low:
                analysis['blood_pressure'] = {
                    'systolic_avg': round(np.mean(pressures_high), 2),
                    'diastolic_avg': round(np.mean(pressures_low), 2),
                    'pressure_variability': round(np.std(pressures_high), 2),
                    'hypertension_risk': self._assess_hypertension_risk(pressures_high, pressures_low)
                }
            
            # 心血管风险评估
            analysis['cardiovascular_risk_score'] = self._calculate_cardiovascular_risk_score(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"心血管系统分析失败: {e}")
            return {}
    
    def _analyze_respiratory_system(self, health_data):
        """分析呼吸系统"""
        try:
            blood_oxygen_values = [record.blood_oxygen for record in health_data if record.blood_oxygen]
            
            if not blood_oxygen_values:
                return {}
            
            analysis = {
                'blood_oxygen': {
                    'average': round(np.mean(blood_oxygen_values), 2),
                    'stability': round(100 - np.std(blood_oxygen_values), 2),
                    'min': int(np.min(blood_oxygen_values)),
                    'max': int(np.max(blood_oxygen_values)),
                    'trend': self._calculate_simple_trend(blood_oxygen_values)
                },
                'respiratory_health_score': self._calculate_respiratory_health_score(blood_oxygen_values),
                'hypoxia_episodes': len([val for val in blood_oxygen_values if val < 90])
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"呼吸系统分析失败: {e}")
            return {}
    
    def _analyze_activity_patterns(self, health_data):
        """分析活动模式"""
        try:
            daily_steps = []
            distances = []
            calories = []
            
            # 按日期聚合数据
            daily_data = {}
            for record in health_data:
                date_key = record.timestamp.date()
                if date_key not in daily_data:
                    daily_data[date_key] = {'steps': 0, 'distance': 0, 'calories': 0}
                
                if record.step:
                    daily_data[date_key]['steps'] += record.step
                if record.distance:
                    daily_data[date_key]['distance'] += record.distance
                if record.calorie:
                    daily_data[date_key]['calories'] += record.calorie
            
            # 提取每日汇总
            for date_data in daily_data.values():
                daily_steps.append(date_data['steps'])
                distances.append(date_data['distance'])
                calories.append(date_data['calories'])
            
            if not daily_steps:
                return {}
            
            # 计算活动一致性
            activity_consistency = 100 - min(np.std(daily_steps) / max(np.mean(daily_steps), 1) * 100, 80)
            
            # 识别活跃时段
            peak_activity_hours = self._identify_peak_activity_hours(health_data)
            
            # 比较工作日和周末
            weekend_weekday_comparison = self._compare_weekend_weekday_activity(daily_data)
            
            return {
                'daily_step_average': round(np.mean(daily_steps), 0),
                'step_consistency': round(activity_consistency, 2),
                'daily_distance_average': round(np.mean(distances), 2),
                'daily_calories_average': round(np.mean(calories), 0),
                'activity_consistency': round(activity_consistency, 2),
                'peak_activity_hours': peak_activity_hours,
                'weekend_vs_weekday': weekend_weekday_comparison,
                'activity_trend': self._calculate_simple_trend(daily_steps)
            }
            
        except Exception as e:
            logger.error(f"分析活动模式失败: {e}")
            return {}
    
    def create_health_portrait_visualization(self, health_profile):
        """创建健康画像可视化数据"""
        try:
            if not health_profile:
                return {}
            
            # 雷达图数据：多维度健康指标
            detailed_scores = health_profile.get('current_health_status', {}).get('detailed_scores', {})
            
            radar_data = {
                'dimensions': ['心血管', '呼吸系统', '代谢功能', '心理健康', '运动能力', '睡眠质量'],
                'values': [
                    detailed_scores.get('cardiovascular_score', 0),
                    detailed_scores.get('respiratory_score', 0),
                    detailed_scores.get('metabolic_score', 0),
                    detailed_scores.get('psychological_score', 0),
                    detailed_scores.get('activity_consistency_score', 0),
                    detailed_scores.get('sleep_quality_score', 0)
                ],
                'max_value': 100
            }
            
            # 趋势图数据
            trend_data = {}
            health_trends = health_profile.get('health_trends', {})
            for metric, trend_info in health_trends.items():
                trend_data[metric] = {
                    'direction': trend_info.get('trend_direction', 'stable'),
                    'strength': trend_info.get('trend_strength', 0),
                    'stability': trend_info.get('stability_score', 0)
                }
            
            # 风险热力图数据
            risk_assessment = health_profile.get('risk_assessment', {})
            risk_heatmap = {
                'risk_factors': risk_assessment.get('risk_factors', []),
                'risk_levels': [factor.get('severity', 'medium') for factor in risk_assessment.get('risk_factors', [])],
                'current_risk_level': risk_assessment.get('current_risk_level', 'medium')
            }
            
            # 汇总指标
            summary_metrics = self._extract_summary_metrics(health_profile)
            
            return {
                'radar_chart': radar_data,
                'trend_charts': trend_data,
                'risk_heatmap': risk_heatmap,
                'summary_metrics': summary_metrics,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"创建可视化数据失败: {e}")
            return {}
    
    def _extract_summary_metrics(self, health_profile):
        """提取汇总指标"""
        try:
            current_status = health_profile.get('current_health_status', {})
            risk_assessment = health_profile.get('risk_assessment', {})
            behavioral_analysis = health_profile.get('behavioral_analysis', {})
            
            return {
                'overall_score': current_status.get('overall_health_score', 0),
                'health_level': current_status.get('health_level', 'fair'),
                'risk_level': risk_assessment.get('current_risk_level', 'medium'),
                'improvement_potential': self._calculate_improvement_potential(health_profile),
                'engagement_level': behavioral_analysis.get('health_engagement', {}).get('overall_engagement', 50),
                'data_quality_score': self._calculate_data_quality_score(health_profile)
            }
            
        except Exception as e:
            logger.error(f"提取汇总指标失败: {e}")
            return {}
    
    def _calculate_improvement_potential(self, health_profile):
        """计算改善潜力"""
        current_score = health_profile.get('current_health_status', {}).get('overall_health_score', 0)
        
        # 基于当前评分计算改善潜力
        if current_score >= 90:
            return 'low'  # 已经很好，改善空间有限
        elif current_score >= 70:
            return 'medium'  # 有一定改善空间
        else:
            return 'high'  # 有很大改善空间
    
    def get_user_health_profile(self, user_id, profile_date=None):
        """获取用户健康画像"""
        try:
            if not profile_date:
                profile_date = date.today()
            
            profile_record = db.session.query(UserHealthProfile).filter(
                and_(
                    UserHealthProfile.user_id == user_id,
                    UserHealthProfile.profile_date == profile_date,
                    UserHealthProfile.is_deleted == False
                )
            ).first()
            
            if profile_record:
                return profile_record.to_dict()
            else:
                logger.info(f"用户 {user_id} 在 {profile_date} 的健康画像不存在")
                return None
                
        except Exception as e:
            logger.error(f"获取用户健康画像失败: {e}")
            return None
    
    def _identify_immediate_concerns(self, latest_data, health_score):
        """识别紧急关注点"""
        concerns = []
        
        if not latest_data:
            return concerns
        
        # 检查关键指标异常
        if latest_data.heart_rate and (latest_data.heart_rate > 120 or latest_data.heart_rate < 50):
            concerns.append({
                'type': 'critical',
                'indicator': 'heart_rate',
                'value': latest_data.heart_rate,
                'message': '心率异常，建议立即关注'
            })
        
        if latest_data.blood_oxygen and latest_data.blood_oxygen < 90:
            concerns.append({
                'type': 'critical',
                'indicator': 'blood_oxygen',
                'value': latest_data.blood_oxygen,
                'message': '血氧饱和度偏低，需要医疗关注'
            })
        
        # 检查综合评分
        if health_score and health_score['total_score'] < 60:
            concerns.append({
                'type': 'warning',
                'indicator': 'overall_health',
                'value': health_score['total_score'],
                'message': '综合健康评分偏低，建议制定改善计划'
            })
        
        return concerns
    
    def _calculate_simple_trend(self, values):
        """计算简单趋势"""
        if len(values) < 3:
            return 'insufficient_data'
        
        recent_avg = np.mean(values[-7:]) if len(values) >= 7 else np.mean(values[-len(values)//2:])
        early_avg = np.mean(values[:7]) if len(values) >= 14 else np.mean(values[:len(values)//2])
        
        change_rate = (recent_avg - early_avg) / early_avg * 100
        
        if change_rate > 5:
            return 'increasing'
        elif change_rate < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _detect_seasonal_pattern(self, metric_data, metric_name):
        """检测季节性模式（简化版本）"""
        # 简化的季节性检测
        current_month = datetime.now().month
        season = self._get_season(current_month)
        
        # 基于当前季节返回预期模式
        seasonal_expectations = {
            'heart_rate': {
                'winter': 'slightly_higher',
                'spring': 'normal',
                'summer': 'slightly_lower',
                'autumn': 'normal'
            },
            'blood_oxygen': {
                'winter': 'lower',
                'spring': 'normal',
                'summer': 'higher',
                'autumn': 'normal'
            }
        }
        
        return seasonal_expectations.get(metric_name, {}).get(season, 'normal')
    
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
    
    def generate_personal_profile(self, user_id, device_sn, include_health_data=True, include_user_info=True):
        """生成个人健康画像 - API兼容方法"""
        try:
            # 通过device_sn获取customer_id - 使用正确的函数
            from .user import get_user_info_by_deviceSn
            user_info = get_user_info_by_deviceSn(device_sn)
            
            if not user_info:
                logger.error(f"设备 {device_sn} 对应的用户信息不存在")
                return None
            
            customer_id = user_info.get('customer_id', 0)
            actual_user_id = user_info.get('id', user_id)
            
            # 调用综合健康画像生成方法，使用实际的用户ID
            profile = self.generate_comprehensive_health_profile(actual_user_id, customer_id)
            
            if not profile:
                return None
            
            # 根据参数过滤返回数据
            result = {
                'user_id': user_id,
                'device_sn': device_sn,
                'generated_at': datetime.now().isoformat()
            }
            
            if include_user_info:
                result['user_info'] = profile.get('user_basic_info', {})
            
            if include_health_data:
                result['health_profile'] = profile
            else:
                # 只返回基本的画像摘要
                current_status = profile.get('current_health_status', {})
                risk_assessment = profile.get('risk_assessment', {})
                result['health_summary'] = {
                    'overall_health_score': current_status.get('overall_health_score'),
                    'health_level': current_status.get('health_level'),
                    'risk_level': risk_assessment.get('current_risk_level')
                }
            
            return result
            
        except Exception as e:
            logger.error(f"生成个人健康画像失败: {e}")
            return None

class HealthProfileBatchProcessor:
    """健康画像批处理器"""
    
    def __init__(self):
        self.profile_engine = HealthProfileEngine()
    
    def batch_generate_profiles(self, customer_id):
        """批量生成客户下所有用户的健康画像"""
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
            results = []
            
            for user in users:
                try:
                    profile = self.profile_engine.generate_comprehensive_health_profile(
                        user.id, customer_id
                    )
                    if profile:
                        success_count += 1
                        results.append({
                            'user_id': user.id,
                            'user_name': user.user_name,
                            'profile_generated': True,
                            'overall_score': profile['current_health_status'].get('overall_health_score', 0)
                        })
                    else:
                        results.append({
                            'user_id': user.id,
                            'user_name': user.user_name,
                            'profile_generated': False,
                            'error': '画像生成失败'
                        })
                except Exception as e:
                    logger.error(f"用户 {user.id} 画像生成失败: {e}")
                    results.append({
                        'user_id': user.id,
                        'user_name': user.user_name,
                        'profile_generated': False,
                        'error': str(e)
                    })
            
            logger.info(f"批量生成健康画像完成: {success_count}/{total_count} 成功")
            
            return {
                'success_count': success_count,
                'total_count': total_count,
                'success_rate': success_count / total_count if total_count > 0 else 0,
                'results': results,
                'batch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"批量生成健康画像失败: {e}")
            return None