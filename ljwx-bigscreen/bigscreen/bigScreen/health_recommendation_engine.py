"""
智能健康建议生成引擎
基于AI驱动的个性化健康建议生成和跟踪系统
"""

import json
import random
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
from .models import db, UserHealthData, AlertInfo, UserInfo, Position
from .health_score_engine import HealthScoreEngine, HealthScoreAnalyzer
import logging

logger = logging.getLogger(__name__)

class HealthRecommendationEngine:
    """智能健康建议生成引擎"""
    
    def __init__(self):
        self.score_engine = HealthScoreEngine()
        self.analyzer = HealthScoreAnalyzer()
        
        # 建议类型定义
        self.recommendation_types = {
            'physiological': '生理指标改善',
            'behavioral': '行为习惯调整',
            'risk_prevention': '风险预防',
            'lifestyle': '生活方式优化',
            'exercise': '运动建议',
            'nutrition': '营养指导',
            'sleep': '睡眠改善',
            'stress': '压力管理'
        }
        
        # 建议模板库
        self.recommendation_templates = self._load_recommendation_templates()
    
    def generate_personalized_recommendations(self, user_id, customer_id):
        """生成个性化健康建议"""
        try:
            # 1. 获取用户健康评分分析
            analysis = self.analyzer.analyze_score_factors(user_id, customer_id)
            
            if not analysis:
                logger.warning(f"用户 {user_id} 缺少健康分析数据")
                return []
            
            # 2. 获取用户基础信息
            user_profile = self._get_user_profile(user_id)
            
            # 3. 基于分析结果生成建议
            recommendations = []
            
            # 生理指标建议
            if analysis['dimension_scores']['physiological'] < 70:
                physio_recommendations = self._generate_physiological_recommendations(
                    analysis, user_profile
                )
                recommendations.extend(physio_recommendations)
            
            # 行为习惯建议
            if analysis['dimension_scores']['behavioral'] < 75:
                behavioral_recommendations = self._generate_behavioral_recommendations(
                    analysis, user_profile
                )
                recommendations.extend(behavioral_recommendations)
            
            # 风险预防建议
            if analysis['dimension_scores']['risk_factor'] < 80:
                risk_recommendations = self._generate_risk_prevention_recommendations(
                    analysis, user_profile
                )
                recommendations.extend(risk_recommendations)
            
            # 基于薄弱环节的针对性建议
            targeted_recommendations = self._generate_targeted_recommendations(
                analysis['weak_areas'], user_profile
            )
            recommendations.extend(targeted_recommendations)
            
            # 4. 个性化优先级排序
            prioritized_recommendations = self._prioritize_recommendations(
                recommendations, analysis, user_profile
            )
            
            # 5. 保存建议到数据库
            saved_recommendations = []
            for rec in prioritized_recommendations[:5]:  # 最多保存前5个建议
                saved_rec = self._save_recommendation(rec, user_id, customer_id)
                if saved_rec:
                    saved_recommendations.append(saved_rec)
            
            logger.info(f"为用户 {user_id} 生成 {len(saved_recommendations)} 条个性化建议")
            return saved_recommendations
            
        except Exception as e:
            logger.error(f"生成个性化建议失败: {e}")
            return []
    
    def _generate_physiological_recommendations(self, analysis, user_profile):
        """生成生理指标改善建议"""
        recommendations = []
        breakdown = analysis['detailed_breakdown']
        
        # 心血管建议
        if breakdown.get('cardiovascular_score', 0) < 70:
            recommendations.append({
                'type': 'physiological',
                'category': 'cardiovascular',
                'priority': 'high',
                'title': '心血管健康改善建议',
                'description': '您的心血管健康指标需要关注，建议采取以下措施改善',
                'actions': [
                    '每周进行3-4次有氧运动，每次30-45分钟',
                    '控制饮食中的饱和脂肪和胆固醇摄入',
                    '保持规律的作息时间，避免熬夜',
                    '学习放松技巧，如深呼吸和冥想',
                    '定期监测血压和心率变化'
                ],
                'timeline': '4-6周改善计划',
                'expected_improvement': 15,
                'difficulty': 'medium'
            })
        
        # 呼吸系统建议
        if breakdown.get('respiratory_score', 0) < 70:
            recommendations.append({
                'type': 'physiological',
                'category': 'respiratory',
                'priority': 'high',
                'title': '呼吸系统健康优化',
                'description': '血氧饱和度偏低，建议改善呼吸系统功能',
                'actions': [
                    '每日进行30分钟有氧运动提高肺活量',
                    '练习腹式呼吸，每天3次，每次10分钟',
                    '保持室内空气流通，避免空气污染',
                    '戒烟限酒，避免呼吸道刺激物',
                    '增加维生素C和抗氧化食物摄入'
                ],
                'timeline': '2-4周改善计划',
                'expected_improvement': 12,
                'difficulty': 'easy'
            })
        
        return recommendations
    
    def _generate_behavioral_recommendations(self, analysis, user_profile):
        """生成行为习惯调整建议"""
        recommendations = []
        breakdown = analysis['detailed_breakdown']
        
        # 睡眠改善建议
        if breakdown.get('sleep_quality_score', 0) < 75:
            sleep_rec = {
                'type': 'behavioral',
                'category': 'sleep',
                'priority': 'medium',
                'title': '睡眠质量改善计划',
                'description': '您的睡眠质量需要改善，良好的睡眠是健康的基础',
                'actions': [
                    '建立固定的睡眠时间，每晚同一时间上床',
                    '睡前1小时避免使用电子设备',
                    '保持卧室温度在18-22℃，环境安静黑暗',
                    '避免睡前3小时内大量饮食和饮酒',
                    '建立睡前放松仪式，如泡澡或阅读'
                ],
                'timeline': '2-3周习惯养成',
                'expected_improvement': 20,
                'difficulty': 'easy'
            }
            
            # 根据用户职业调整建议
            if user_profile.get('position_risk_level') == 'high':
                sleep_rec['actions'].append('工作日中午安排20-30分钟午休')
                sleep_rec['actions'].append('下班后进行轻度运动帮助放松')
            
            recommendations.append(sleep_rec)
        
        # 运动建议
        if breakdown.get('activity_consistency_score', 0) < 70:
            exercise_rec = {
                'type': 'behavioral',
                'category': 'exercise',
                'priority': 'medium',
                'title': '运动习惯建立计划',
                'description': '提高运动一致性，建立可持续的运动习惯',
                'actions': [
                    '制定每周运动计划，从每天20分钟开始',
                    '选择喜欢的运动项目，提高坚持性',
                    '设定每日步数目标，逐步增加到10000步',
                    '利用碎片时间进行简单运动，如爬楼梯',
                    '寻找运动伙伴或加入运动社群'
                ],
                'timeline': '4-8周习惯养成',
                'expected_improvement': 25,
                'difficulty': 'medium'
            }
            
            recommendations.append(exercise_rec)
        
        return recommendations
    
    def _generate_risk_prevention_recommendations(self, analysis, user_profile):
        """生成风险预防建议"""
        recommendations = []
        
        # 基于告警历史生成预防建议
        if analysis['dimension_scores']['risk_factor'] < 70:
            risk_rec = {
                'type': 'risk_prevention',
                'category': 'health_monitoring',
                'priority': 'high',
                'title': '健康风险预防方案',
                'description': '基于您的健康数据分析，建议加强预防措施',
                'actions': [
                    '增加健康监测频率，每日至少记录2次数据',
                    '建立健康异常早期识别机制',
                    '定期进行健康体检，建议3个月一次',
                    '学习健康急救知识和自我监测技能',
                    '与医疗专业人员建立定期联系'
                ],
                'timeline': '持续执行',
                'expected_improvement': 15,
                'difficulty': 'easy'
            }
            
            # 根据职业风险调整
            if user_profile.get('position_risk_level') == 'high':
                risk_rec['actions'].extend([
                    '工作期间每2小时进行健康状态检查',
                    '配备紧急联系设备，确保及时求助',
                    '参加职业健康培训和安全教育'
                ])
                risk_rec['priority'] = 'critical'
            
            recommendations.append(risk_rec)
        
        return recommendations
    
    def _generate_targeted_recommendations(self, weak_areas, user_profile):
        """基于薄弱环节生成针对性建议"""
        recommendations = []
        
        for area in weak_areas:
            area_name = area['area']
            score = area['score']
            level = area['level']
            
            if 'metabolic' in area_name and score < 65:
                recommendations.append({
                    'type': 'lifestyle',
                    'category': 'metabolism',
                    'priority': 'high' if level == 'critical' else 'medium',
                    'title': '代谢功能优化建议',
                    'description': '改善基础代谢和体温调节功能',
                    'actions': [
                        '增加蛋白质摄入，促进基础代谢',
                        '保持规律的饮食时间和饮食结构',
                        '进行力量训练增加肌肉量',
                        '保证充足的水分摄入，每日8-10杯水',
                        '避免极端饮食和节食行为'
                    ],
                    'timeline': '6-8周改善计划',
                    'expected_improvement': 18,
                    'difficulty': 'medium'
                })
            
            elif 'psychological' in area_name and score < 70:
                recommendations.append({
                    'type': 'lifestyle',
                    'category': 'stress_management',
                    'priority': 'medium',
                    'title': '压力管理和心理健康',
                    'description': '改善心理状态，增强抗压能力',
                    'actions': [
                        '学习正念冥想，每日10-15分钟',
                        '建立健康的工作生活平衡',
                        '培养兴趣爱好，增加生活乐趣',
                        '维护良好的社交关系和支持网络',
                        '必要时寻求专业心理咨询帮助'
                    ],
                    'timeline': '4-6周改善计划',
                    'expected_improvement': 22,
                    'difficulty': 'medium'
                })
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations, analysis, user_profile):
        """个性化优先级排序"""
        try:
            # 计算每个建议的优先级分数
            for rec in recommendations:
                priority_score = 0
                
                # 基础优先级权重
                priority_weights = {
                    'critical': 100,
                    'high': 80,
                    'medium': 60,
                    'low': 40
                }
                priority_score += priority_weights.get(rec.get('priority', 'medium'), 60)
                
                # 预期改善效果权重
                expected_improvement = rec.get('expected_improvement', 10)
                priority_score += expected_improvement * 2
                
                # 难度调整（越容易执行优先级越高）
                difficulty_weights = {
                    'easy': 20,
                    'medium': 10,
                    'hard': 0
                }
                priority_score += difficulty_weights.get(rec.get('difficulty', 'medium'), 10)
                
                # 用户特征调整
                if user_profile.get('position_risk_level') == 'high':
                    if rec.get('category') in ['cardiovascular', 'health_monitoring']:
                        priority_score += 15
                
                # 健康评分影响
                if analysis['overall_score'] < 60:
                    if rec.get('type') == 'physiological':
                        priority_score += 20
                
                rec['priority_score'] = priority_score
            
            # 按优先级分数排序
            return sorted(recommendations, key=lambda x: x['priority_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"建议优先级排序失败: {e}")
            return recommendations
    
    def _save_recommendation(self, recommendation, user_id, customer_id):
        """保存建议到数据库"""
        try:
            # 生成建议ID
            rec_id = f"REC_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
            
            # 创建建议记录
            rec_record = HealthRecommendationTrack(
                user_id=user_id,
                customer_id=customer_id,
                recommendation_id=rec_id,
                recommendation_type=recommendation['type'],
                title=recommendation['title'],
                description=recommendation['description'],
                recommended_actions=recommendation.get('actions', []),
                status='pending',
                start_date=date.today(),
                target_completion_date=self._calculate_target_date(recommendation.get('timeline', '4周')),
                create_time=datetime.now(),
                update_time=datetime.now(),
                is_deleted=False
            )
            
            db.session.add(rec_record)
            db.session.commit()
            
            # 返回保存后的建议信息
            return {
                'id': rec_record.id,
                'recommendation_id': rec_id,
                'type': recommendation['type'],
                'category': recommendation.get('category'),
                'priority': recommendation.get('priority'),
                'title': recommendation['title'],
                'description': recommendation['description'],
                'actions': recommendation.get('actions', []),
                'timeline': recommendation.get('timeline'),
                'expected_improvement': recommendation.get('expected_improvement'),
                'difficulty': recommendation.get('difficulty'),
                'status': 'pending',
                'create_time': rec_record.create_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存建议失败: {e}")
            return None
    
    def _calculate_target_date(self, timeline_str):
        """根据时间线字符串计算目标完成日期"""
        try:
            today = date.today()
            
            if '周' in timeline_str:
                weeks = int(''.join(filter(str.isdigit, timeline_str.split('周')[0])))
                return today + timedelta(weeks=weeks)
            elif '天' in timeline_str:
                days = int(''.join(filter(str.isdigit, timeline_str.split('天')[0])))
                return today + timedelta(days=days)
            elif '月' in timeline_str:
                months = int(''.join(filter(str.isdigit, timeline_str.split('月')[0])))
                return today + timedelta(days=months * 30)
            else:
                return today + timedelta(weeks=4)  # 默认4周
                
        except:
            return date.today() + timedelta(weeks=4)
    
    def _get_user_profile(self, user_id):
        """获取用户画像信息"""
        try:
            # 获取用户基础信息
            user = db.session.query(UserInfo).filter_by(id=user_id).first()
            
            if not user:
                return {}
            
            profile = {
                'user_id': user_id,
                'age_group': self._determine_age_group(user),
                'gender': user.gender,
                'working_years': user.working_years
            }
            
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
            
            if position_info:
                profile.update({
                    'position_name': position_info.name,
                    'position_risk_level': position_info.risk_level,
                    'position_weight': float(position_info.weight) if position_info.weight else 0.15
                })
            
            # 获取历史建议执行情况
            past_recommendations = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.user_id == user_id,
                    HealthRecommendationTrack.is_deleted == False
                )
            ).count()
            
            completed_recommendations = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.user_id == user_id,
                    HealthRecommendationTrack.status == 'completed',
                    HealthRecommendationTrack.is_deleted == False
                )
            ).count()
            
            profile['recommendation_completion_rate'] = (
                completed_recommendations / past_recommendations 
                if past_recommendations > 0 else 0
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"获取用户画像失败: {e}")
            return {}
    
    def _determine_age_group(self, user):
        """确定用户年龄组"""
        if not hasattr(user, 'birthday') or not user.birthday:
            return 'middle'
        
        age = (date.today() - user.birthday).days // 365
        if age < 30:
            return 'young'
        elif age <= 50:
            return 'middle'
        else:
            return 'senior'
    
    def update_recommendation_progress(self, recommendation_id, user_feedback, progress_data):
        """更新建议执行进度"""
        try:
            recommendation = db.session.query(HealthRecommendationTrack).filter_by(
                recommendation_id=recommendation_id, is_deleted=False
            ).first()
            
            if not recommendation:
                logger.warning(f"建议 {recommendation_id} 不存在")
                return False
            
            # 更新进度
            recommendation.user_feedback = user_feedback
            recommendation.update_time = datetime.now()
            
            # 根据进度数据更新状态
            if progress_data.get('completed', False):
                recommendation.status = 'completed'
                recommendation.actual_completion_date = date.today()
                recommendation.effectiveness_score = progress_data.get('effectiveness_score')
            elif progress_data.get('in_progress', False):
                recommendation.status = 'in_progress'
            
            # 保存健康改善指标
            if progress_data.get('health_metrics'):
                recommendation.health_improvement_metrics = progress_data['health_metrics']
            
            db.session.commit()
            
            logger.info(f"建议 {recommendation_id} 进度更新成功")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新建议进度失败: {e}")
            return False
    
    def get_user_recommendations(self, user_id, status=None, limit=10):
        """获取用户建议列表"""
        try:
            query = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.user_id == user_id,
                    HealthRecommendationTrack.is_deleted == False
                )
            )
            
            if status:
                query = query.filter(HealthRecommendationTrack.status == status)
            
            recommendations = query.order_by(
                HealthRecommendationTrack.create_time.desc()
            ).limit(limit).all()
            
            return [rec.to_dict() for rec in recommendations]
            
        except Exception as e:
            logger.error(f"获取用户建议列表失败: {e}")
            return []
    
    def evaluate_recommendation_effectiveness(self, recommendation_id):
        """评估建议执行效果"""
        try:
            recommendation = db.session.query(HealthRecommendationTrack).filter_by(
                recommendation_id=recommendation_id, is_deleted=False
            ).first()
            
            if not recommendation or recommendation.status != 'completed':
                return None
            
            user_id = recommendation.user_id
            
            # 获取建议执行前后的健康数据对比
            start_date = recommendation.start_date
            end_date = recommendation.actual_completion_date or date.today()
            
            # 执行前数据
            before_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.timestamp >= start_date - timedelta(days=7),
                    UserHealthData.timestamp < start_date,
                    UserHealthData.is_deleted == False
                )
            ).all()
            
            # 执行后数据
            after_data = db.session.query(UserHealthData).filter(
                and_(
                    UserHealthData.user_id == user_id,
                    UserHealthData.timestamp >= end_date,
                    UserHealthData.timestamp <= end_date + timedelta(days=7),
                    UserHealthData.is_deleted == False
                )
            ).all()
            
            if not before_data or not after_data:
                return None
            
            # 计算改善效果
            effectiveness = self._calculate_health_improvement(
                before_data, after_data, recommendation.recommendation_type
            )
            
            # 更新效果评分
            recommendation.effectiveness_score = effectiveness['overall_improvement']
            recommendation.health_improvement_metrics = effectiveness['detailed_metrics']
            db.session.commit()
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"评估建议效果失败: {e}")
            return None
    
    def _calculate_health_improvement(self, before_data, after_data, recommendation_type):
        """计算健康改善情况"""
        try:
            improvement_metrics = {}
            
            # 根据建议类型评估相应指标
            if recommendation_type == 'physiological':
                metrics_to_check = ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low']
            elif recommendation_type == 'behavioral':
                metrics_to_check = ['step', 'sleep', 'distance', 'calorie']
            else:
                metrics_to_check = ['heart_rate', 'blood_oxygen', 'step', 'sleep']
            
            total_improvement = 0
            valid_metrics = 0
            
            for metric in metrics_to_check:
                before_values = [getattr(record, metric) for record in before_data 
                               if getattr(record, metric) is not None]
                after_values = [getattr(record, metric) for record in after_data 
                              if getattr(record, metric) is not None]
                
                if before_values and after_values:
                    before_avg = np.mean(before_values)
                    after_avg = np.mean(after_values)
                    
                    # 计算改善百分比
                    if metric in ['heart_rate', 'pressure_high', 'pressure_low', 'stress']:
                        # 这些指标越低越好
                        improvement = (before_avg - after_avg) / before_avg * 100
                    else:
                        # 这些指标越高越好
                        improvement = (after_avg - before_avg) / before_avg * 100
                    
                    improvement_metrics[metric] = {
                        'before': round(before_avg, 2),
                        'after': round(after_avg, 2),
                        'improvement_percent': round(improvement, 2)
                    }
                    
                    total_improvement += improvement
                    valid_metrics += 1
            
            overall_improvement = total_improvement / valid_metrics if valid_metrics > 0 else 0
            
            return {
                'overall_improvement': round(overall_improvement, 2),
                'detailed_metrics': improvement_metrics,
                'evaluation_date': datetime.now().strftime('%Y-%m-%d'),
                'data_quality': {
                    'before_samples': len(before_data),
                    'after_samples': len(after_data),
                    'valid_metrics': valid_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"计算健康改善情况失败: {e}")
            return {'overall_improvement': 0, 'detailed_metrics': {}}
    
    def _load_recommendation_templates(self):
        """加载建议模板库"""
        # 这里可以从配置文件或数据库加载更丰富的建议模板
        return {
            'cardiovascular_improvement': [
                '增加有氧运动频率和强度',
                '控制饮食中的盐分和脂肪摄入',
                '保持心理健康，减少压力'
            ],
            'sleep_optimization': [
                '建立规律的睡眠时间表',
                '创造良好的睡眠环境',
                '避免睡前刺激性活动'
            ],
            'exercise_consistency': [
                '制定可行的运动计划',
                '寻找适合的运动方式',
                '建立运动习惯跟踪机制'
            ]
        }

class RecommendationTracker:
    """建议跟踪器"""
    
    def __init__(self):
        self.engine = HealthRecommendationEngine()
    
    def daily_recommendation_check(self, customer_id):
        """每日建议检查和提醒"""
        try:
            # 获取所有待执行的建议
            pending_recommendations = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.customer_id == customer_id,
                    HealthRecommendationTrack.status == 'pending',
                    HealthRecommendationTrack.start_date <= date.today(),
                    HealthRecommendationTrack.is_deleted == False
                )
            ).all()
            
            # 检查过期建议
            overdue_recommendations = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.customer_id == customer_id,
                    HealthRecommendationTrack.status.in_(['pending', 'in_progress']),
                    HealthRecommendationTrack.target_completion_date < date.today(),
                    HealthRecommendationTrack.is_deleted == False
                )
            ).all()
            
            logger.info(f"客户 {customer_id}: {len(pending_recommendations)} 待执行, {len(overdue_recommendations)} 已过期")
            
            return {
                'pending_count': len(pending_recommendations),
                'overdue_count': len(overdue_recommendations),
                'pending_recommendations': [rec.to_dict() for rec in pending_recommendations],
                'overdue_recommendations': [rec.to_dict() for rec in overdue_recommendations]
            }
            
        except Exception as e:
            logger.error(f"每日建议检查失败: {e}")
            return None
    
    def auto_generate_follow_up_recommendations(self, user_id, customer_id):
        """自动生成后续建议"""
        try:
            # 获取已完成的建议
            completed_recommendations = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.user_id == user_id,
                    HealthRecommendationTrack.status == 'completed',
                    HealthRecommendationTrack.actual_completion_date >= date.today() - timedelta(days=30),
                    HealthRecommendationTrack.is_deleted == False
                )
            ).all()
            
            if not completed_recommendations:
                return []
            
            # 分析完成效果，生成后续建议
            follow_up_recommendations = []
            
            for completed_rec in completed_recommendations:
                if completed_rec.effectiveness_score and completed_rec.effectiveness_score >= 70:
                    # 效果良好，生成进阶建议
                    follow_up = self._generate_advanced_recommendation(completed_rec)
                    if follow_up:
                        follow_up_recommendations.append(follow_up)
                elif completed_rec.effectiveness_score and completed_rec.effectiveness_score < 50:
                    # 效果不佳，调整建议策略
                    adjusted = self._generate_adjusted_recommendation(completed_rec)
                    if adjusted:
                        follow_up_recommendations.append(adjusted)
            
            logger.info(f"为用户 {user_id} 生成 {len(follow_up_recommendations)} 条后续建议")
            return follow_up_recommendations
            
        except Exception as e:
            logger.error(f"生成后续建议失败: {e}")
            return []
    
    def _generate_advanced_recommendation(self, completed_rec):
        """生成进阶建议"""
        # 基于成功完成的建议生成更高级的建议
        advanced_actions = {
            'exercise': [
                '增加运动强度，尝试高强度间歇训练',
                '加入力量训练，提升肌肉质量',
                '参加团体运动，增加运动乐趣'
            ],
            'sleep': [
                '优化睡眠环境，使用智能睡眠设备',
                '学习更高级的放松技巧',
                '建立个性化的睡眠优化方案'
            ]
        }
        
        category = completed_rec.recommendation_type
        actions = advanced_actions.get(category, [])
        
        if actions:
            return {
                'type': 'follow_up',
                'category': category,
                'priority': 'medium',
                'title': f'{completed_rec.title} - 进阶版',
                'description': f'基于您在"{completed_rec.title}"中的优异表现，建议进一步提升',
                'actions': actions,
                'timeline': '4-6周进阶计划',
                'expected_improvement': 10,
                'difficulty': 'medium'
            }
        
        return None
    
    def _generate_adjusted_recommendation(self, completed_rec):
        """生成调整建议"""
        # 基于效果不佳的建议生成调整版本
        return {
            'type': 'adjustment',
            'category': completed_rec.recommendation_type,
            'priority': 'medium',
            'title': f'{completed_rec.title} - 调整版',
            'description': f'根据之前的执行情况，调整策略以获得更好效果',
            'actions': [
                '重新评估目标，设定更现实的期望',
                '寻找执行困难的原因并解决',
                '考虑寻求专业指导',
                '调整执行方式，找到更适合的方法'
            ],
            'timeline': '2-4周调整期',
            'expected_improvement': 15,
            'difficulty': 'easy'
        }