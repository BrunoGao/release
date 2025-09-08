"""
健康建议实时生成引擎
基于实时健康评分结果，生成个性化健康建议和改进方案

依赖统一的get_all_health_data_optimized查询方法和health_score_engine
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .redis_helper import RedisHelper
from .health_score_engine import realtime_score_engine
from .models import db, HealthRecommendationTrack
from sqlalchemy import and_
import json
import time

logger = logging.getLogger(__name__)

class RealTimeHealthRecommendationEngine:
    """实时健康建议生成引擎"""
    
    def __init__(self):
        self.redis = RedisHelper()
        
        # 健康特征配置 - 与其他引擎保持一致
        self.HEALTH_FEATURES = [
            "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
            "pressure_low", "stress", "step", "calorie", "distance", "sleep"
        ]
        
        # 建议模板配置
        self.RECOMMENDATION_TEMPLATES = {
            "heart_rate": {
                "excellent": [
                    "您的心率水平非常健康，请继续保持规律的运动习惯",
                    "建议适当增加有氧运动强度，进一步提升心肺功能"
                ],
                "good": [
                    "心率状况良好，建议保持当前的运动频率",
                    "可以尝试间歇性训练来优化心率表现"
                ],
                "fair": [
                    "心率偏离正常范围，建议调整运动强度和作息时间",
                    "减少剧烈运动，增加轻度有氧运动如散步"
                ],
                "poor": [
                    "心率异常，建议立即调整生活方式",
                    "避免高强度运动，优先改善睡眠质量和饮食结构"
                ],
                "critical": [
                    "心率严重异常，强烈建议就医检查",
                    "立即停止剧烈运动，保持平静状态并密切监测"
                ]
            },
            "blood_oxygen": {
                "excellent": [
                    "血氧饱和度优秀，呼吸系统功能良好",
                    "建议继续保持室内通风良好的环境"
                ],
                "good": [
                    "血氧水平正常，建议增加深呼吸练习",
                    "保持适量户外活动，呼吸新鲜空气"
                ],
                "fair": [
                    "血氧偏低，建议改善室内空气质量",
                    "增加深呼吸训练，避免长时间久坐"
                ],
                "poor": [
                    "血氧不足，需要立即改善呼吸环境",
                    "建议进行呼吸康复训练，必要时使用制氧设备"
                ],
                "critical": [
                    "血氧严重不足，请立即就医",
                    "保持半卧位休息，避免过度活动"
                ]
            },
            "temperature": {
                "excellent": [
                    "体温正常，身体状况良好",
                    "继续保持良好的作息规律"
                ],
                "good": [
                    "体温略有波动但在正常范围，建议观察",
                    "保持适当的室内温度和湿度"
                ],
                "fair": [
                    "体温偏高或偏低，注意保暖或降温",
                    "调整衣物，保持体温稳定"
                ],
                "poor": [
                    "体温异常，建议多测量几次确认",
                    "注意休息，避免过度疲劳"
                ],
                "critical": [
                    "体温严重异常，建议立即就医",
                    "密切监测体温变化，采取必要的物理降温措施"
                ]
            },
            "pressure_high": {
                "excellent": [
                    "收缩压正常，心血管健康状况良好",
                    "继续保持低盐饮食和规律运动"
                ],
                "good": [
                    "收缩压略高但可控，建议监测血压趋势",
                    "减少钠盐摄入，增加钾离子丰富的食物"
                ],
                "fair": [
                    "收缩压偏高，需要调整饮食和生活方式",
                    "限制咖啡因摄入，保持心情舒畅"
                ],
                "poor": [
                    "收缩压明显升高，建议寻求医疗建议",
                    "严格控制盐分摄入，避免激动情绪"
                ],
                "critical": [
                    "收缩压危险性升高，请立即就医",
                    "卧床休息，避免一切可能引起血压波动的因素"
                ]
            },
            "pressure_low": {
                "excellent": [
                    "舒张压正常，心血管功能健康",
                    "保持当前的健康生活方式"
                ],
                "good": [
                    "舒张压轻微波动，建议继续监测",
                    "保持适度运动和充足睡眠"
                ],
                "fair": [
                    "舒张压异常，需要关注心血管健康",
                    "调整作息时间，减少精神压力"
                ],
                "poor": [
                    "舒张压明显异常，建议医疗咨询",
                    "控制体重，减少高脂食物摄入"
                ],
                "critical": [
                    "舒张压严重异常，必须立即就医",
                    "避免剧烈运动，保持情绪稳定"
                ]
            },
            "stress": {
                "excellent": [
                    "压力水平很低，心理状态良好",
                    "继续保持良好的压力管理习惯"
                ],
                "good": [
                    "压力在可控范围内，建议适当放松",
                    "尝试冥想或瑜伽来进一步减压"
                ],
                "fair": [
                    "压力较大，需要采取减压措施",
                    "合理安排工作时间，增加休息间隔"
                ],
                "poor": [
                    "压力过大，严重影响健康",
                    "建议寻求专业心理咨询，学习压力管理技巧"
                ],
                "critical": [
                    "压力极大，需要立即干预",
                    "暂停高压工作，寻求专业医疗和心理支持"
                ]
            },
            "step": {
                "excellent": [
                    "日常步数充足，运动量很好",
                    "保持当前的活跃度，可尝试新的运动形式"
                ],
                "good": [
                    "步数达标，运动量适中",
                    "可以设定更高的步数目标挑战自己"
                ],
                "fair": [
                    "步数偏少，建议增加日常活动",
                    "尝试步行上下班或使用楼梯代替电梯"
                ],
                "poor": [
                    "缺乏运动，需要立即增加身体活动",
                    "从每天短距离散步开始，逐步增加运动量"
                ],
                "critical": [
                    "严重缺乏运动，健康风险较高",
                    "建议咨询医生制定适合的运动康复计划"
                ]
            },
            "calorie": {
                "excellent": [
                    "卡路里消耗充足，代谢水平良好",
                    "保持当前的运动强度和频率"
                ],
                "good": [
                    "卡路里消耗适中，可以适当增加",
                    "尝试间歇性运动提高代谢率"
                ],
                "fair": [
                    "卡路里消耗不足，需要增加运动量",
                    "结合有氧运动和力量训练"
                ],
                "poor": [
                    "代谢水平较低，建议增加身体活动",
                    "从低强度运动开始，逐步提升"
                ],
                "critical": [
                    "代谢极低，需要专业指导",
                    "建议寻求营养师和健身教练的专业建议"
                ]
            },
            "distance": {
                "excellent": [
                    "运动距离充足，体能水平很好",
                    "可以尝试更有挑战性的运动项目"
                ],
                "good": [
                    "运动距离适中，建议保持",
                    "可以增加运动的多样性"
                ],
                "fair": [
                    "运动距离偏少，建议增加",
                    "设定每周的运动距离目标"
                ],
                "poor": [
                    "缺乏足够的运动距离",
                    "从每日短距离开始，逐步增加"
                ],
                "critical": [
                    "运动量严重不足",
                    "需要制定系统的运动计划"
                ]
            },
            "sleep": {
                "excellent": [
                    "睡眠质量很好，保持当前的睡眠习惯",
                    "继续维持规律的作息时间"
                ],
                "good": [
                    "睡眠质量良好，可以进一步优化",
                    "注意睡前环境和放松技巧"
                ],
                "fair": [
                    "睡眠质量一般，需要改善",
                    "建立固定的睡前仪式，避免睡前使用电子设备"
                ],
                "poor": [
                    "睡眠质量差，严重影响健康",
                    "检查睡眠环境，考虑使用睡眠辅助工具"
                ],
                "critical": [
                    "睡眠严重不足，需要立即改善",
                    "建议寻求专业的睡眠医学帮助"
                ]
            }
        }
        
        # 综合建议模板
        self.COMPREHENSIVE_TEMPLATES = {
            "excellent": [
                "您的整体健康状况非常优秀，请继续保持当前的健康生活方式",
                "建议定期体检，预防为主，维持当前的运动和饮食习惯"
            ],
            "good": [
                "您的健康状况良好，有进一步优化的空间",
                "建议重点关注{priority_issues}方面的改善"
            ],
            "fair": [
                "您的健康状况需要关注和改善",
                "建议优先解决{priority_issues}问题，制定改善计划"
            ],
            "poor": [
                "您的健康状况存在多个问题，需要积极干预",
                "强烈建议就医咨询，同时改善{priority_issues}指标"
            ],
            "critical": [
                "您的健康状况存在严重风险，请立即寻求医疗帮助",
                "紧急处理{priority_issues}问题，避免进一步恶化"
            ]
        }
    
    def generate_user_health_recommendations_realtime(self, user_id: int, target_date: str = None) -> Dict:
        """
        生成用户健康建议，优先从数据库查询，空值时实时生成
        
        Args:
            user_id: 用户ID
            target_date: 目标日期，默认为昨天
            
        Returns:
            Dict: 包含健康建议和优先级信息
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始获取用户 {user_id} 的健康建议，目标日期: {target_date}")
        
        try:
            # 步骤1: 优先从数据库查询已生成的建议
            db_result = self._query_database_recommendations(user_id, target_date)
            if db_result['success'] and db_result['data']:
                logger.info(f"✅ 用户 {user_id} 从数据库获取建议成功，建议数量: {len(db_result['data'].get('feature_recommendations', {}))}") 
                return db_result
            
            # 步骤2: 数据库无数据，执行实时生成
            logger.info(f"📊 用户 {user_id} 数据库无建议数据，开始实时生成...")
            return self._generate_recommendations_realtime(user_id, target_date, start_time)
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 建议获取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _query_database_recommendations(self, user_id: int, target_date: str) -> Dict:
        """从数据库查询已生成的健康建议"""
        try:
            # 查询健康建议记录
            recommendation_records = db.session.query(HealthRecommendationTrack).filter(
                and_(
                    HealthRecommendationTrack.user_id == user_id,
                    HealthRecommendationTrack.start_date == target_date,
                    HealthRecommendationTrack.is_deleted == False
                )
            ).all()
            
            if not recommendation_records:
                return {'success': True, 'data': None, 'source': 'database_empty'}
            
            # 转换为标准格式
            feature_recommendations = {}
            priority_issues = []
            
            for record in recommendation_records:
                rec_type = record.recommendation_type
                if rec_type in self.HEALTH_FEATURES:  # 只处理健康特征相关的建议
                    feature_recommendations[rec_type] = {
                        'feature_name': rec_type,
                        'score': 0,  # 数据库中没有存储评分，设为默认值
                        'level': self._extract_level_from_title(record.title),
                        'recommendation': record.description or record.title,
                        'priority': self._extract_priority_from_status(record.status),
                        'recommended_actions': record.recommended_actions or [],
                        'source': 'database'
                    }
                    
                    # 从状态判断是否为优先问题
                    if record.status in ['pending', 'in_progress'] and record.recommendation_type:
                        display_name = self._get_feature_display_name(record.recommendation_type)
                        if display_name not in priority_issues:
                            priority_issues.append(display_name)
            
            # 生成综合建议（从最新的记录中获取）
            latest_record = max(recommendation_records, key=lambda r: r.create_time)
            comprehensive_recommendation = latest_record.description or latest_record.title
            
            # 生成汇总信息
            summary = {
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'database',
                'overall_score': 0,  # 数据库建议表中没有总分，设为默认值
                'health_level': 'fair',  # 默认等级
                'priority_issues_count': len(priority_issues),
                'features_with_recommendations': len(feature_recommendations),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 从数据库获取用户 {user_id} 建议: {len(feature_recommendations)} 个特征建议，{len(priority_issues)} 个优先问题")
            
            return {
                'success': True,
                'data': {
                    'feature_recommendations': feature_recommendations,
                    'comprehensive_recommendation': comprehensive_recommendation,
                    'priority_issues': priority_issues,
                    'summary': summary
                },
                'source': 'database'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 数据库建议查询失败: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'database_error'}
    
    def _generate_recommendations_realtime(self, user_id: int, target_date: str, start_time: float) -> Dict:
        """实时生成健康建议（原有逻辑）"""
        logger.info(f"🔄 开始实时生成用户 {user_id} 健康建议，日期: {target_date}")
        
        try:
            # 1. 获取用户健康评分
            score_result = realtime_score_engine.calculate_user_health_score_realtime(user_id, target_date)
            
            if not score_result.get('success'):
                logger.warning(f"⚠️ 用户 {user_id} 评分获取失败: {score_result.get('error')}")
                return {
                    'success': False,
                    'error': f"健康评分获取失败: {score_result.get('error')}",
                    'user_id': user_id,
                    'target_date': target_date
                }
            
            feature_scores = score_result['data']['feature_scores']
            summary = score_result['data']['summary']
            overall_score = summary['overall_score']
            health_level = summary['health_level']
            
            # 2. 生成特征级建议
            feature_recommendations = {}
            priority_issues = []
            
            for feature, score_data in feature_scores.items():
                feature_score = score_data['score_value']
                feature_level = self._determine_health_level(feature_score)
                
                # 获取该特征的建议模板
                templates = self.RECOMMENDATION_TEMPLATES.get(feature, {}).get(feature_level, [
                    f"{feature}指标需要关注，建议咨询专业人员"
                ])
                
                # 选择合适的建议（基于评分详情）
                recommendation = self._select_recommendation(feature, feature_level, score_data, templates)
                
                feature_recommendations[feature] = {
                    'feature_name': feature,
                    'score': feature_score,
                    'level': feature_level,
                    'recommendation': recommendation,
                    'priority': self._calculate_priority(feature_score, score_data),
                    'baseline_reference': score_data.get('baseline_reference', {}),
                    'data_quality': score_data.get('data_quality', {}),
                    'source': 'realtime'
                }
                
                # 识别优先问题
                if feature_score < 70:  # 评分低于70的作为优先问题
                    priority_issues.append(self._get_feature_display_name(feature))
            
            # 3. 生成综合建议
            comprehensive_recommendation = self._generate_comprehensive_recommendation(
                health_level, priority_issues, feature_recommendations
            )
            
            # 4. 计算建议质量指标
            recommendation_quality = self._calculate_recommendation_quality(feature_recommendations)
            
            # 5. 生成建议汇总
            recommendation_summary = {
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'realtime',
                'overall_score': overall_score,
                'health_level': health_level,
                'priority_issues_count': len(priority_issues),
                'features_with_recommendations': len(feature_recommendations),
                'generated_at': datetime.now().isoformat()
            }
            
            # 6. 缓存结果
            cache_key = f"realtime_recommendations:user:{user_id}:{target_date}"
            cache_data = {
                'feature_recommendations': feature_recommendations,
                'comprehensive_recommendation': comprehensive_recommendation,
                'priority_issues': priority_issues,
                'summary': recommendation_summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 3600)
            
            logger.info(f"✅ 用户 {user_id} 健康建议生成完成: 整体等级 {health_level}，优先问题 {len(priority_issues)} 个")
            
            return {
                'success': True,
                'data': {
                    'feature_recommendations': feature_recommendations,
                    'comprehensive_recommendation': comprehensive_recommendation,
                    'priority_issues': priority_issues,
                    'summary': recommendation_summary
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 健康建议生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def generate_department_health_recommendations_realtime(self, org_id: int, target_date: str = None) -> Dict:
        """
        实时生成部门健康建议聚合
        
        Args:
            org_id: 组织ID
            target_date: 目标日期，默认为昨天
            
        Returns:
            Dict: 包含部门级别的健康建议聚合
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始生成部门 {org_id} 的实时健康建议聚合，日期: {target_date}")
        
        try:
            # 1. 获取部门下所有用户
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(org_id)
            
            if not users:
                return {
                    'success': False,
                    'error': '未找到部门用户',
                    'org_id': org_id,
                    'target_date': target_date
                }
            
            # 2. 获取每个用户的健康建议
            user_recommendations = {}
            department_issues = {}
            total_users = len(users)
            processed_users = 0
            
            for user in users:
                user_id = user['id']
                user_rec_result = self.generate_user_health_recommendations_realtime(user_id, target_date)
                
                if user_rec_result.get('success'):
                    user_recommendations[user_id] = user_rec_result['data']
                    processed_users += 1
                    
                    # 聚合部门级别的问题
                    priority_issues = user_rec_result['data'].get('priority_issues', [])
                    for issue in priority_issues:
                        department_issues[issue] = department_issues.get(issue, 0) + 1
                else:
                    logger.warning(f"⚠️ 用户 {user_id} 建议生成失败: {user_rec_result.get('error')}")
            
            # 3. 生成部门级别统计
            department_stats = self._calculate_department_stats(user_recommendations)
            
            # 4. 生成部门优先建议
            department_priority_recommendations = self._generate_department_priority_recommendations(
                department_issues, total_users, department_stats
            )
            
            # 5. 生成部门汇总
            department_summary = {
                'org_id': org_id,
                'target_date': target_date,
                'total_users': total_users,
                'processed_users': processed_users,
                'coverage_rate': round(processed_users / total_users, 3) if total_users > 0 else 0,
                'department_issues_count': len(department_issues),
                'priority_recommendations_count': len(department_priority_recommendations),
                'generation_time': round(time.time() - start_time, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            # 6. 缓存结果
            cache_key = f"realtime_recommendations:department:{org_id}:{target_date}"
            cache_data = {
                'user_recommendations': user_recommendations,
                'department_stats': department_stats,
                'department_issues': department_issues,
                'priority_recommendations': department_priority_recommendations,
                'summary': department_summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 3600)
            
            logger.info(f"✅ 部门 {org_id} 健康建议聚合完成: 处理用户 {processed_users}/{total_users}，部门问题 {len(department_issues)} 个")
            
            return {
                'success': True,
                'data': {
                    'user_recommendations': user_recommendations,
                    'department_stats': department_stats,
                    'department_issues': department_issues,
                    'priority_recommendations': department_priority_recommendations,
                    'summary': department_summary
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 部门 {org_id} 健康建议聚合失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'org_id': org_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _determine_health_level(self, score: float) -> str:
        """根据评分确定健康等级"""
        if score >= 90:
            return 'excellent'    # 优秀
        elif score >= 80:
            return 'good'        # 良好
        elif score >= 70:
            return 'fair'        # 一般
        elif score >= 60:
            return 'poor'        # 较差
        else:
            return 'critical'    # 危险
    
    def _select_recommendation(self, feature: str, level: str, score_data: Dict, templates: List[str]) -> str:
        """根据具体情况选择合适的建议"""
        if not templates:
            return f"{feature}指标需要关注，建议咨询专业人员"
        
        # 根据Z分数选择更具体的建议
        z_score = score_data.get('z_score', 0)
        
        if len(templates) > 1:
            if abs(z_score) > 2:  # 显著偏离
                return templates[1] if len(templates) > 1 else templates[0]
            else:
                return templates[0]
        
        return templates[0]
    
    def _calculate_priority(self, score: float, score_data: Dict) -> int:
        """计算建议优先级 (1-5，5最高)"""
        if score < 50:
            return 5  # 危险
        elif score < 60:
            return 4  # 高优先级
        elif score < 70:
            return 3  # 中等优先级
        elif score < 80:
            return 2  # 低优先级
        else:
            return 1  # 维持现状
    
    def _get_feature_display_name(self, feature: str) -> str:
        """获取特征显示名称"""
        display_names = {
            "heart_rate": "心率",
            "blood_oxygen": "血氧",
            "temperature": "体温",
            "pressure_high": "收缩压",
            "pressure_low": "舒张压",
            "stress": "压力",
            "step": "步数",
            "calorie": "卡路里",
            "distance": "运动距离",
            "sleep": "睡眠"
        }
        return display_names.get(feature, feature)
    
    def _extract_level_from_title(self, title: str) -> str:
        """从建议标题中提取健康等级"""
        if not title:
            return 'fair'
        
        title_lower = title.lower()
        if '优秀' in title or '很好' in title or 'excellent' in title_lower:
            return 'excellent'
        elif '良好' in title or 'good' in title_lower:
            return 'good'
        elif '一般' in title or 'fair' in title_lower:
            return 'fair'
        elif '较差' in title or 'poor' in title_lower:
            return 'poor'
        elif '危险' in title or '严重' in title or 'critical' in title_lower:
            return 'critical'
        else:
            return 'fair'
    
    def _extract_priority_from_status(self, status: str) -> int:
        """从建议状态中提取优先级"""
        if not status:
            return 3
        
        # 根据状态判断优先级
        priority_map = {
            'completed': 1,  # 已完成，优先级最低
            'in_progress': 3,  # 进行中，中等优先级
            'pending': 4,  # 待处理，较高优先级
            'cancelled': 1,  # 已取消，低优先级
        }
        return priority_map.get(status, 3)
    
    def _generate_comprehensive_recommendation(self, health_level: str, priority_issues: List[str], 
                                            feature_recommendations: Dict) -> str:
        """生成综合健康建议"""
        templates = self.COMPREHENSIVE_TEMPLATES.get(health_level, [
            "您的健康状况需要关注，建议定期监测各项指标"
        ])
        
        # 选择合适的模板
        if priority_issues and len(templates) > 1:
            # 有优先问题，使用包含占位符的模板
            template = templates[1] if '{priority_issues}' in templates[1] else templates[0]
            priority_text = "、".join(priority_issues[:3])  # 最多显示3个优先问题
            return template.format(priority_issues=priority_text)
        else:
            return templates[0]
    
    def _calculate_recommendation_quality(self, feature_recommendations: Dict) -> Dict:
        """计算建议质量指标"""
        if not feature_recommendations:
            return {'overall_quality': 0, 'completeness': 0, 'actionability': 0}
        
        total_features = len(self.HEALTH_FEATURES)
        recommended_features = len(feature_recommendations)
        completeness = recommended_features / total_features
        
        # 计算可操作性（基于优先级分布）
        priorities = [rec.get('priority', 1) for rec in feature_recommendations.values()]
        actionability = np.mean(priorities) / 5 if priorities else 0
        
        overall_quality = (completeness * 0.6 + actionability * 0.4)
        
        return {
            'overall_quality': round(overall_quality, 3),
            'completeness': round(completeness, 3),
            'actionability': round(actionability, 3),
            'recommended_features': recommended_features,
            'total_features': total_features
        }
    
    def _calculate_department_stats(self, user_recommendations: Dict) -> Dict:
        """计算部门级别统计"""
        if not user_recommendations:
            return {}
        
        # 聚合各特征的评分统计
        feature_stats = {}
        health_level_distribution = {}
        priority_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for user_id, user_data in user_recommendations.items():
            # 健康等级分布
            health_level = user_data.get('summary', {}).get('health_level', 'unknown')
            health_level_distribution[health_level] = health_level_distribution.get(health_level, 0) + 1
            
            # 特征评分聚合
            feature_recs = user_data.get('feature_recommendations', {})
            for feature, rec_data in feature_recs.items():
                if feature not in feature_stats:
                    feature_stats[feature] = {
                        'scores': [],
                        'levels': [],
                        'priorities': []
                    }
                
                feature_stats[feature]['scores'].append(rec_data.get('score', 0))
                feature_stats[feature]['levels'].append(rec_data.get('level', 'unknown'))
                priority = rec_data.get('priority', 1)
                feature_stats[feature]['priorities'].append(priority)
                priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        # 计算每个特征的统计值
        aggregated_features = {}
        for feature, stats in feature_stats.items():
            aggregated_features[feature] = {
                'avg_score': round(np.mean(stats['scores']), 2),
                'min_score': round(np.min(stats['scores']), 2),
                'max_score': round(np.max(stats['scores']), 2),
                'std_score': round(np.std(stats['scores']), 2),
                'avg_priority': round(np.mean(stats['priorities']), 2),
                'user_count': len(stats['scores'])
            }
        
        return {
            'feature_stats': aggregated_features,
            'health_level_distribution': health_level_distribution,
            'priority_distribution': priority_distribution,
            'total_users_analyzed': len(user_recommendations)
        }
    
    def _generate_department_priority_recommendations(self, department_issues: Dict, 
                                                   total_users: int, department_stats: Dict) -> List[str]:
        """生成部门级别的优先建议"""
        recommendations = []
        
        # 基于问题频率生成建议
        sorted_issues = sorted(department_issues.items(), key=lambda x: x[1], reverse=True)
        
        for issue, count in sorted_issues[:3]:  # 最多3个主要问题
            percentage = round(count / total_users * 100, 1) if total_users > 0 else 0
            if percentage >= 20:  # 影响超过20%的用户
                recommendations.append(f"部门内{percentage}%的员工存在{issue}问题，建议组织相关健康培训或干预措施")
        
        # 基于整体健康等级分布生成建议
        health_distribution = department_stats.get('health_level_distribution', {})
        critical_count = health_distribution.get('critical', 0)
        poor_count = health_distribution.get('poor', 0)
        
        if critical_count > 0:
            recommendations.append(f"部门内有{critical_count}名员工健康状况危险，需要立即关注并提供医疗支持")
        
        if poor_count > total_users * 0.3:  # 超过30%的员工状况较差
            recommendations.append("部门整体健康状况需要改善，建议制定系统性健康促进计划")
        
        # 如果没有特别严重的问题，给出一般性建议
        if not recommendations:
            recommendations.append("部门整体健康状况良好，建议继续保持并定期开展健康监测活动")
        
        return recommendations


# 全局实例
realtime_recommendation_engine = RealTimeHealthRecommendationEngine()


def get_user_health_recommendations_realtime(user_id: int, target_date: str = None) -> Dict:
    """获取用户实时健康建议 - 对外接口"""
    return realtime_recommendation_engine.generate_user_health_recommendations_realtime(user_id, target_date)


def get_department_health_recommendations_realtime(org_id: int, target_date: str = None) -> Dict:
    """获取部门实时健康建议聚合 - 对外接口"""
    return realtime_recommendation_engine.generate_department_health_recommendations_realtime(org_id, target_date)


def get_health_recommendations_status(identifier: int, identifier_type: str = 'user', target_date: str = None) -> Dict:
    """获取建议状态 - 对外接口"""
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    cache_key = f"realtime_recommendations:{identifier_type}:{identifier}:{target_date}"
    cached_result = realtime_recommendation_engine.redis.get_data(cache_key)
    
    if cached_result:
        data = json.loads(cached_result)
        return {
            'success': True,
            'cached': True,
            'data': data,
            'cache_key': cache_key
        }
    else:
        return {
            'success': False,
            'cached': False,
            'message': '未找到缓存的建议数据',
            'identifier': identifier,
            'identifier_type': identifier_type,
            'target_date': target_date
        }