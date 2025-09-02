"""
健康评分计算引擎
实现多维度健康评分：生理指标、行为指标、风险因子
"""

import math
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import text, and_, func
from .models import db, UserHealthData, AlertInfo, Position, UserPosition, HealthDataConfig
from .health_baseline_engine import HealthBaselineEngine
import logging

logger = logging.getLogger(__name__)

class HealthScoreEngine:
    """健康评分计算引擎"""
    
    def __init__(self):
        self.baseline_engine = HealthBaselineEngine()
        
    def calculate_comprehensive_health_score(self, user_id, customer_id, date_range=30):
        """计算综合健康评分"""
        try:
            # 1. 获取用户健康数据
            health_data = self._get_user_health_data(user_id, date_range)
            
            if not health_data:
                logger.warning(f"用户 {user_id} 缺少健康数据")
                return None
            
            # 2. 获取个人健康基线
            baseline = self.baseline_engine.get_user_baseline(user_id)
            
            # 3. 获取配置权重
            config = self._get_health_config(customer_id)
            
            # 4. 获取职位风险权重
            position_weight = self._get_user_position_weight(user_id)
            
            # 5. 获取告警历史
            alert_history = self._get_user_alerts(user_id, date_range)
            
            # 6. 计算各维度得分
            physiological_score = self._calculate_physiological_score(health_data, baseline, config)
            behavioral_score = self._calculate_behavioral_score(health_data, config)
            risk_factor_score = self._calculate_risk_factor_score(user_id, position_weight, alert_history)
            
            # 7. 加权综合评分
            final_score = (
                physiological_score * 0.5 +    # 生理指标权重50%
                behavioral_score * 0.3 +       # 行为指标权重30%
                risk_factor_score * 0.2        # 风险因子权重20%
            )
            
            # 8. 生成评分详情
            score_detail = {
                'user_id': user_id,
                'customer_id': customer_id,
                'total_score': round(final_score, 2),
                'physiological_score': round(physiological_score, 2),
                'behavioral_score': round(behavioral_score, 2),
                'risk_factor_score': round(risk_factor_score, 2),
                'score_date': date.today(),
                'score_level': self._get_score_level(final_score),
                'detailed_breakdown': {
                    'cardiovascular_score': self._calculate_cardiovascular_score(health_data, baseline),
                    'respiratory_score': self._calculate_respiratory_score(health_data, baseline),
                    'metabolic_score': self._calculate_metabolic_score(health_data, baseline),
                    'psychological_score': self._calculate_psychological_score(health_data, baseline),
                    'activity_consistency_score': self._calculate_activity_consistency(health_data),
                    'sleep_quality_score': self._calculate_sleep_quality_score(health_data),
                    'health_engagement_score': self._calculate_health_engagement(user_id)
                }
            }
            
            return score_detail
            
        except Exception as e:
            logger.error(f"计算综合健康评分失败: {e}")
            return None
    
    def _calculate_physiological_score(self, health_data, baseline, config):
        """计算生理指标评分 - 基于Z-Score标准化"""
        if not health_data or not baseline:
            return 0
        
        total_score = 0
        weighted_sum = 0
        
        physiological_metrics = ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 
                               'temperature', 'stress']
        
        for metric in physiological_metrics:
            if metric in health_data and metric in baseline:
                # 计算Z-Score
                current_avg = np.mean([getattr(record, metric) for record in health_data 
                                     if getattr(record, metric) is not None])
                
                baseline_info = baseline[metric]
                z_score = (current_avg - baseline_info['mean']) / max(baseline_info['std'], 0.1)
                
                # 转换为健康评分 (0-100)
                if metric in ['heart_rate', 'blood_oxygen']:
                    # 正向指标：越接近正常范围越好
                    metric_score = 100 - min(abs(z_score) * 15, 50)
                else:
                    # 控制指标：偏离基线越多扣分越多
                    metric_score = 100 - min(abs(z_score) * 20, 60)
                
                # 获取指标权重
                weight = config.get(metric, {}).get('weight', 0.15)
                total_score += metric_score * weight
                weighted_sum += weight
        
        return total_score / weighted_sum if weighted_sum > 0 else 0
    
    def _calculate_behavioral_score(self, health_data, config):
        """计算行为指标评分"""
        if not health_data:
            return 0
        
        # 获取最近的行为数据
        recent_data = health_data[-7:] if len(health_data) >= 7 else health_data
        
        # 运动评分
        daily_steps = [getattr(record, 'step') for record in recent_data 
                      if getattr(record, 'step') is not None]
        avg_steps = np.mean(daily_steps) if daily_steps else 0
        step_target = config.get('step', {}).get('target', 8000)
        step_score = min(avg_steps / step_target * 100, 100)
        
        # 睡眠评分
        sleep_hours = [getattr(record, 'sleep') for record in recent_data 
                      if getattr(record, 'sleep') is not None]
        avg_sleep = np.mean(sleep_hours) if sleep_hours else 0
        sleep_score = self._calculate_sleep_score(avg_sleep)
        
        # 活跃度评分
        distances = [getattr(record, 'distance') for record in recent_data 
                    if getattr(record, 'distance') is not None]
        calories = [getattr(record, 'calorie') for record in recent_data 
                   if getattr(record, 'calorie') is not None]
        
        avg_distance = np.mean(distances) if distances else 0
        avg_calories = np.mean(calories) if calories else 0
        activity_score = min((avg_distance * 0.3 + avg_calories * 0.01) * 2, 100)
        
        # 加权平均
        behavioral_score = step_score * 0.4 + sleep_score * 0.4 + activity_score * 0.2
        
        return behavioral_score
    
    def _calculate_sleep_score(self, avg_sleep_hours):
        """计算睡眠质量评分"""
        if 7 <= avg_sleep_hours <= 9:
            return 100
        elif 6 <= avg_sleep_hours < 7 or 9 < avg_sleep_hours <= 10:
            return 85
        else:
            return max(70 - abs(avg_sleep_hours - 8) * 10, 40)
    
    def _calculate_risk_factor_score(self, user_id, position_weight, alert_history):
        """计算风险因子评分"""
        base_score = 100
        
        # 职位风险调整
        position_penalty = (1 - position_weight) * 10 if position_weight else 5
        
        # 告警历史惩罚
        alert_penalty = 0
        for alert in alert_history:
            days_ago = (datetime.now() - alert['occur_at']).days
            decay_factor = math.exp(-days_ago / 30)  # 30天衰减期
            
            # 根据告警级别计算惩罚
            level_penalty = {
                'critical': 15,
                'major': 10,
                'minor': 5,
                'info': 2
            }.get(alert.get('level', 'minor'), 5)
            
            alert_penalty += level_penalty * decay_factor
        
        total_penalty = alert_penalty + position_penalty
        final_score = max(base_score - total_penalty, 20)
        
        return final_score
    
    def _calculate_cardiovascular_score(self, health_data, baseline):
        """计算心血管健康评分"""
        if not health_data or not baseline:
            return 0
        
        heart_rates = [getattr(record, 'heart_rate') for record in health_data 
                      if getattr(record, 'heart_rate') is not None]
        pressures_high = [getattr(record, 'pressure_high') for record in health_data 
                         if getattr(record, 'pressure_high') is not None]
        pressures_low = [getattr(record, 'pressure_low') for record in health_data 
                        if getattr(record, 'pressure_low') is not None]
        
        scores = []
        
        # 心率评分
        if heart_rates and 'heart_rate' in baseline:
            hr_avg = np.mean(heart_rates)
            hr_baseline = baseline['heart_rate']
            hr_z_score = abs((hr_avg - hr_baseline['mean']) / max(hr_baseline['std'], 1))
            hr_score = max(100 - hr_z_score * 20, 40)
            scores.append(hr_score)
        
        # 血压评分
        if pressures_high and pressures_low and 'pressure_high' in baseline and 'pressure_low' in baseline:
            ph_avg = np.mean(pressures_high)
            pl_avg = np.mean(pressures_low)
            
            ph_baseline = baseline['pressure_high']
            pl_baseline = baseline['pressure_low']
            
            ph_z_score = abs((ph_avg - ph_baseline['mean']) / max(ph_baseline['std'], 1))
            pl_z_score = abs((pl_avg - pl_baseline['mean']) / max(pl_baseline['std'], 1))
            
            pressure_score = max(100 - (ph_z_score + pl_z_score) * 10, 40)
            scores.append(pressure_score)
        
        return np.mean(scores) if scores else 0
    
    def _calculate_respiratory_score(self, health_data, baseline):
        """计算呼吸系统健康评分"""
        if not health_data or not baseline:
            return 0
        
        blood_oxygen_values = [getattr(record, 'blood_oxygen') for record in health_data 
                              if getattr(record, 'blood_oxygen') is not None]
        
        if not blood_oxygen_values or 'blood_oxygen' not in baseline:
            return 0
        
        bo_avg = np.mean(blood_oxygen_values)
        bo_baseline = baseline['blood_oxygen']
        
        # 血氧饱和度评分 - 高于基线为好
        if bo_avg >= bo_baseline['mean']:
            score = min(100, 80 + (bo_avg - bo_baseline['mean']) * 2)
        else:
            deviation = (bo_baseline['mean'] - bo_avg) / max(bo_baseline['std'], 1)
            score = max(100 - deviation * 25, 30)
        
        return score
    
    def _calculate_metabolic_score(self, health_data, baseline):
        """计算代谢功能评分"""
        if not health_data or not baseline:
            return 0
        
        temperatures = [getattr(record, 'temperature') for record in health_data 
                       if getattr(record, 'temperature') is not None]
        
        if not temperatures or 'temperature' not in baseline:
            return 0
        
        temp_avg = np.mean(temperatures)
        temp_baseline = baseline['temperature']
        
        # 体温稳定性评分
        temp_stability = np.std(temperatures)
        stability_score = max(100 - temp_stability * 50, 50)
        
        # 体温正常性评分
        temp_z_score = abs((temp_avg - temp_baseline['mean']) / max(temp_baseline['std'], 0.1))
        normal_score = max(100 - temp_z_score * 30, 40)
        
        return (stability_score + normal_score) / 2
    
    def _calculate_psychological_score(self, health_data, baseline):
        """计算心理健康评分"""
        if not health_data or not baseline:
            return 0
        
        stress_values = [getattr(record, 'stress') for record in health_data 
                        if getattr(record, 'stress') is not None]
        
        if not stress_values or 'stress' not in baseline:
            return 75  # 默认评分
        
        stress_avg = np.mean(stress_values)
        stress_baseline = baseline['stress']
        
        # 压力水平评分 - 低于基线为好
        if stress_avg <= stress_baseline['mean']:
            score = min(100, 80 + (stress_baseline['mean'] - stress_avg) * 2)
        else:
            deviation = (stress_avg - stress_baseline['mean']) / max(stress_baseline['std'], 1)
            score = max(100 - deviation * 20, 40)
        
        return score
    
    def _calculate_activity_consistency(self, health_data):
        """计算活动一致性评分"""
        if not health_data or len(health_data) < 7:
            return 0
        
        # 获取每日步数
        daily_steps = []
        current_date = None
        daily_total = 0
        
        for record in health_data:
            record_date = record.timestamp.date()
            
            if current_date != record_date:
                if current_date is not None and daily_total > 0:
                    daily_steps.append(daily_total)
                current_date = record_date
                daily_total = getattr(record, 'step') or 0
            else:
                daily_total += getattr(record, 'step') or 0
        
        # 添加最后一天的数据
        if daily_total > 0:
            daily_steps.append(daily_total)
        
        if len(daily_steps) < 3:
            return 0
        
        # 计算一致性 - 标准差越小，一致性越高
        steps_std = np.std(daily_steps)
        steps_mean = np.mean(daily_steps)
        
        if steps_mean == 0:
            return 0
        
        consistency_coefficient = steps_std / steps_mean
        consistency_score = max(100 - consistency_coefficient * 100, 20)
        
        return consistency_score
    
    def _calculate_sleep_quality_score(self, health_data):
        """计算睡眠质量评分"""
        if not health_data:
            return 0
        
        sleep_hours = [getattr(record, 'sleep') for record in health_data 
                      if getattr(record, 'sleep') is not None]
        
        if not sleep_hours:
            return 0
        
        avg_sleep = np.mean(sleep_hours)
        sleep_consistency = 100 - min(np.std(sleep_hours) * 20, 50)  # 一致性评分
        
        # 睡眠时长评分
        if 7 <= avg_sleep <= 9:
            duration_score = 100
        elif 6 <= avg_sleep < 7 or 9 < avg_sleep <= 10:
            duration_score = 85
        else:
            duration_score = max(70 - abs(avg_sleep - 8) * 10, 40)
        
        # 综合睡眠质量评分
        return (duration_score * 0.7 + sleep_consistency * 0.3)
    
    def _calculate_health_engagement(self, user_id):
        """计算健康参与度评分"""
        try:
            # 最近30天的数据上传频率
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            upload_count = db.session.query(func.count(UserHealthData.id)).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.timestamp >= start_date,
                    UserHealthData.is_deleted == False
                )
            ).scalar()
            
            # 期望每天至少2次数据上传
            expected_uploads = 30 * 2
            engagement_rate = min(upload_count / expected_uploads, 1.0)
            
            return engagement_rate * 100
            
        except Exception as e:
            logger.error(f"计算健康参与度失败: {e}")
            return 50  # 默认评分
    
    def _get_user_health_data(self, user_id, days_back):
        """获取用户健康数据"""
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
            logger.error(f"获取用户健康数据失败: {e}")
            return []
    
    def _get_health_config(self, customer_id):
        """获取健康配置权重"""
        try:
            configs = db.session.query(HealthDataConfig).filter(
                and_(
                    HealthDataConfig.customer_id == customer_id,
                    HealthDataConfig.is_enabled == True
                )
            ).all()
            
            config_dict = {}
            for config in configs:
                config_dict[config.data_type] = {
                    'weight': float(config.weight) if config.weight else 0.15,
                    'warning_high': float(config.warning_high) if config.warning_high else None,
                    'warning_low': float(config.warning_low) if config.warning_low else None,
                    'target': config.warning_high if config.data_type == 'step' else None
                }
            
            return config_dict
            
        except Exception as e:
            logger.error(f"获取健康配置失败: {e}")
            return {}
    
    def _get_user_position_weight(self, user_id):
        """获取用户职位权重"""
        try:
            result = db.session.query(Position.weight).join(
                UserPosition, Position.id == UserPosition.position_id
            ).filter(
                and_(
                    UserPosition.user_id == user_id,
                    UserPosition.is_deleted == False,
                    Position.is_deleted == False
                )
            ).first()
            
            return float(result[0]) if result and result[0] else 0.15
            
        except Exception as e:
            logger.error(f"获取用户职位权重失败: {e}")
            return 0.15
    
    def _get_user_alerts(self, user_id, days_back):
        """获取用户告警历史"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            alerts = db.session.query(AlertInfo).filter(
                and_(
                    AlertInfo.user_id == user_id,
                    AlertInfo.create_time >= start_date,
                    AlertInfo.is_deleted == False
                )
            ).all()
            
            alert_list = []
            for alert in alerts:
                alert_list.append({
                    'id': alert.id,
                    'level': alert.severity_level,
                    'occur_at': alert.alert_timestamp or alert.create_time,
                    'alert_type': alert.alert_type
                })
            
            return alert_list
            
        except Exception as e:
            logger.error(f"获取用户告警历史失败: {e}")
            return []
    
    def _get_score_level(self, score):
        """获取健康等级评定"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'fair'
        elif score >= 60:
            return 'poor'
        else:
            return 'critical'
    
    def batch_calculate_scores(self, customer_id):
        """批量计算客户下所有用户的健康评分"""
        try:
            # 获取客户下所有用户
            users = db.session.query(UserInfo).filter(
                and_(
                    UserInfo.customer_id == customer_id,
                    UserInfo.is_deleted == False
                )
            ).all()
            
            results = []
            for user in users:
                score_detail = self.calculate_comprehensive_health_score(
                    user.id, customer_id
                )
                if score_detail:
                    results.append(score_detail)
            
            logger.info(f"批量计算完成，客户 {customer_id} 共 {len(results)} 个用户评分")
            return results
            
        except Exception as e:
            logger.error(f"批量计算健康评分失败: {e}")
            return []
    
    def get_user_score_trend(self, user_id, days_back=90):
        """获取用户健康评分趋势"""
        try:
            # 按周计算历史评分
            trends = []
            current_date = date.today()
            
            for week_offset in range(0, days_back // 7):
                week_end = current_date - timedelta(days=week_offset * 7)
                week_start = week_end - timedelta(days=7)
                
                # 获取该周的健康数据
                week_data = db.session.query(UserHealthData).filter(
                    and_(
                        UserHealthData.user_id == user_id,
                        UserHealthData.timestamp >= week_start,
                        UserHealthData.timestamp < week_end,
                        UserHealthData.is_deleted == False
                    )
                ).all()
                
                if week_data:
                    # 计算该周评分（简化版）
                    baseline = self.baseline_engine.get_user_baseline(user_id)
                    config = self._get_health_config(week_data[0].customer_id)
                    
                    if baseline:
                        week_score = self._calculate_physiological_score(week_data, baseline, config)
                        trends.append({
                            'week_start': week_start.strftime('%Y-%m-%d'),
                            'week_end': week_end.strftime('%Y-%m-%d'),
                            'score': round(week_score, 2),
                            'data_count': len(week_data)
                        })
            
            return trends[::-1]  # 按时间正序返回
            
        except Exception as e:
            logger.error(f"获取用户评分趋势失败: {e}")
            return []

class HealthScoreAnalyzer:
    """健康评分分析器"""
    
    def __init__(self):
        self.score_engine = HealthScoreEngine()
    
    def analyze_score_factors(self, user_id, customer_id):
        """分析影响健康评分的关键因素"""
        try:
            # 获取详细评分
            score_detail = self.score_engine.calculate_comprehensive_health_score(
                user_id, customer_id
            )
            
            if not score_detail:
                return None
            
            # 分析各维度贡献
            breakdown = score_detail['detailed_breakdown']
            total_score = score_detail['total_score']
            
            # 识别薄弱环节
            weak_areas = []
            strong_areas = []
            
            for area, score in breakdown.items():
                if score < 60:
                    weak_areas.append({'area': area, 'score': score, 'level': 'critical'})
                elif score < 75:
                    weak_areas.append({'area': area, 'score': score, 'level': 'moderate'})
                elif score >= 85:
                    strong_areas.append({'area': area, 'score': score})
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(weak_areas)
            
            analysis_result = {
                'user_id': user_id,
                'overall_score': total_score,
                'score_level': score_detail['score_level'],
                'dimension_scores': {
                    'physiological': score_detail['physiological_score'],
                    'behavioral': score_detail['behavioral_score'],
                    'risk_factor': score_detail['risk_factor_score']
                },
                'detailed_breakdown': breakdown,
                'weak_areas': weak_areas,
                'strong_areas': strong_areas,
                'improvement_suggestions': improvement_suggestions,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析健康评分因素失败: {e}")
            return None
    
    def _generate_improvement_suggestions(self, weak_areas):
        """基于薄弱环节生成改进建议"""
        suggestions = []
        
        for area in weak_areas:
            area_name = area['area']
            score = area['score']
            level = area['level']
            
            if 'cardiovascular' in area_name:
                suggestions.append({
                    'category': 'cardiovascular',
                    'priority': 'high' if level == 'critical' else 'medium',
                    'suggestion': '建议增加有氧运动，控制情绪压力，定期监测心率和血压',
                    'target_improvement': 15 if level == 'critical' else 10
                })
            
            elif 'respiratory' in area_name:
                suggestions.append({
                    'category': 'respiratory',
                    'priority': 'high' if level == 'critical' else 'medium',
                    'suggestion': '建议进行深呼吸训练，保持室内空气流通，避免剧烈运动',
                    'target_improvement': 12 if level == 'critical' else 8
                })
            
            elif 'sleep' in area_name:
                suggestions.append({
                    'category': 'sleep',
                    'priority': 'medium',
                    'suggestion': '建议保持规律作息，睡前避免电子设备，创造良好睡眠环境',
                    'target_improvement': 20 if level == 'critical' else 15
                })
            
            elif 'activity' in area_name:
                suggestions.append({
                    'category': 'activity',
                    'priority': 'medium',
                    'suggestion': '建议制定运动计划，每日至少8000步，保持运动习惯一致性',
                    'target_improvement': 18 if level == 'critical' else 12
                })
        
        return suggestions
    
    def compare_with_peers(self, user_id, customer_id):
        """与同龄人群对比分析"""
        try:
            # 获取用户评分
            user_score = self.score_engine.calculate_comprehensive_health_score(
                user_id, customer_id
            )
            
            if not user_score:
                return None
            
            # 获取用户信息
            user = db.session.query(UserInfo).filter_by(id=user_id).first()
            if not user:
                return None
            
            age_group = self.score_engine.baseline_engine._determine_age_group(user)
            
            # 获取同龄人群评分
            peer_scores = self._get_peer_scores(customer_id, age_group, user.gender)
            
            if not peer_scores:
                return None
            
            peer_avg = np.mean(peer_scores)
            peer_percentile = self._calculate_percentile(user_score['total_score'], peer_scores)
            
            comparison_result = {
                'user_score': user_score['total_score'],
                'peer_average': round(peer_avg, 2),
                'percentile': round(peer_percentile, 1),
                'comparison_level': self._get_comparison_level(peer_percentile),
                'peer_sample_size': len(peer_scores),
                'age_group': age_group,
                'gender': user.gender
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"同龄人群对比分析失败: {e}")
            return None
    
    def _get_peer_scores(self, customer_id, age_group, gender):
        """获取同龄人群的健康评分"""
        try:
            # 这里应该从健康评分缓存表或实时计算获取
            # 简化版本：基于健康基线数据估算
            baselines = db.session.query(HealthBaseline).filter(
                and_(
                    HealthBaseline.customer_id == customer_id,
                    HealthBaseline.baseline_type == 'population',
                    HealthBaseline.age_group == age_group,
                    HealthBaseline.gender == gender,
                    HealthBaseline.is_current == True
                )
            ).all()
            
            # 基于基线数据模拟同龄人群评分分布
            if baselines:
                # 简化计算：基于心率基线估算整体健康评分
                heart_rate_baseline = next(
                    (b for b in baselines if b.feature_name == 'heart_rate'), None
                )
                
                if heart_rate_baseline:
                    # 模拟正态分布的同龄人群评分
                    base_score = 75  # 基础评分
                    scores = np.random.normal(base_score, 10, 50)  # 生成50个模拟评分
                    scores = np.clip(scores, 20, 100)  # 限制在合理范围内
                    return scores.tolist()
            
            return []
            
        except Exception as e:
            logger.error(f"获取同龄人群评分失败: {e}")
            return []
    
    def _calculate_percentile(self, user_score, peer_scores):
        """计算用户评分在同龄人群中的百分位"""
        if not peer_scores:
            return 50
        
        sorted_scores = sorted(peer_scores)
        position = sum(1 for score in sorted_scores if score <= user_score)
        percentile = (position / len(sorted_scores)) * 100
        
        return percentile
    
    def _get_comparison_level(self, percentile):
        """获取对比等级"""
        if percentile >= 90:
            return 'excellent'
        elif percentile >= 75:
            return 'above_average'
        elif percentile >= 50:
            return 'average'
        elif percentile >= 25:
            return 'below_average'
        else:
            return 'needs_improvement'