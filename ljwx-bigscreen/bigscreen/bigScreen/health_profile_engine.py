"""
健康画像实时构建引擎
基于历史健康数据、基线、评分、建议和预测，构建全面的用户健康画像

依赖统一的get_all_health_data_optimized查询方法和其他健康分析引擎
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .redis_helper import RedisHelper
from .user_health_data import get_all_health_data_optimized
from .health_baseline_engine import realtime_baseline_engine
from .health_score_engine import realtime_score_engine
from .health_recommendation_engine import realtime_recommendation_engine
from .health_prediction_engine import realtime_prediction_engine
from .models import db, UserHealthProfile
from sqlalchemy import and_
import json
import time

logger = logging.getLogger(__name__)

class RealTimeHealthProfileEngine:
    """实时健康画像构建引擎"""
    
    def __init__(self):
        self.redis = RedisHelper()
        
        # 健康特征配置 - 与其他引擎保持一致
        self.HEALTH_FEATURES = [
            "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
            "pressure_low", "stress", "step", "calorie", "distance", "sleep"
        ]
        
        # 健康画像维度配置
        self.PROFILE_DIMENSIONS = {
            'cardiovascular': {
                'name': '心血管健康',
                'features': ['heart_rate', 'pressure_high', 'pressure_low'],
                'weight': 0.30,
                'icon': '❤️'
            },
            'respiratory': {
                'name': '呼吸系统',
                'features': ['blood_oxygen'],
                'weight': 0.20,
                'icon': '🫁'
            },
            'metabolic': {
                'name': '代谢健康',
                'features': ['temperature', 'calorie'],
                'weight': 0.15,
                'icon': '🔥'
            },
            'mental': {
                'name': '心理健康',
                'features': ['stress'],
                'weight': 0.15,
                'icon': '🧠'
            },
            'activity': {
                'name': '运动健康',
                'features': ['step', 'distance'],
                'weight': 0.10,
                'icon': '🏃'
            },
            'recovery': {
                'name': '恢复健康',
                'features': ['sleep'],
                'weight': 0.10,
                'icon': '😴'
            }
        }
        
        # 健康等级标签配置
        self.HEALTH_LABELS = {
            'excellent': {'label': '优秀', 'color': '#52c41a', 'badge': '🏆'},
            'good': {'label': '良好', 'color': '#1890ff', 'badge': '👍'},
            'fair': {'label': '一般', 'color': '#faad14', 'badge': '⚠️'},
            'poor': {'label': '较差', 'color': '#fa8c16', 'badge': '📉'},
            'critical': {'label': '危险', 'color': '#f5222d', 'badge': '🚨'}
        }
        
        # 健康画像类型配置
        self.PROFILE_TYPES = {
            'comprehensive': '综合画像',
            'cardiovascular_focused': '心血管重点',
            'activity_focused': '运动健康',
            'mental_focused': '心理健康',
            'preventive': '预防保健'
        }
        
        # 时间维度配置
        self.TIME_DIMENSIONS = {
            'current': {'days': 7, 'label': '当前状态'},
            'short_term': {'days': 30, 'label': '近期趋势'},
            'long_term': {'days': 90, 'label': '长期变化'}
        }
    
    def generate_user_health_profile_realtime(self, user_id: int, target_date: str = None, 
                                            profile_type: str = 'comprehensive') -> Dict:
        """
        生成用户健康画像，优先从数据库查询，空值时实时生成
        
        Args:
            user_id: 用户ID
            target_date: 目标日期，默认为今天
            profile_type: 画像类型，默认为综合画像
            
        Returns:
            Dict: 包含完整的用户健康画像
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始获取用户 {user_id} 的健康画像，目标日期: {target_date}，类型: {profile_type}")
        
        try:
            # 步骤1: 优先从数据库查询已生成的画像
            db_result = self._query_database_profile(user_id, target_date)
            if db_result['success'] and db_result['data']:
                logger.info(f"✅ 用户 {user_id} 从数据库获取画像成功，健康指数: {db_result['data'].get('health_index', {}).get('overall_score', 0)}")
                return db_result
            
            # 步骤2: 数据库无数据，执行实时生成
            logger.info(f"📊 用户 {user_id} 数据库无画像数据，开始实时生成...")
            return self._generate_profile_realtime(user_id, target_date, profile_type, start_time)
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 画像获取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _query_database_profile(self, user_id: int, target_date: str) -> Dict:
        """从数据库查询已生成的健康画像"""
        try:
            # 查询健康画像记录
            profile_record = db.session.query(UserHealthProfile).filter(
                and_(
                    UserHealthProfile.user_id == user_id,
                    UserHealthProfile.profile_date == target_date,
                    UserHealthProfile.is_deleted == False
                )
            ).first()
            
            if not profile_record:
                return {'success': True, 'data': None, 'source': 'database_empty'}
            
            # 转换为标准格式
            user_info = self._get_user_basic_info(user_id)
            
            # 构建健康指数
            health_index = {
                'overall_score': float(profile_record.overall_health_score or 0),
                'overall_level': profile_record.health_level or 'fair',
                'level_info': self.HEALTH_LABELS.get(profile_record.health_level or 'fair', {}),
                'dimension_scores': {
                    'cardiovascular': float(profile_record.cardiovascular_score or 0),
                    'respiratory': float(profile_record.respiratory_score or 0),
                    'metabolic': float(profile_record.metabolic_score or 0),
                    'mental': float(profile_record.psychological_score or 0),
                    'activity': float(profile_record.behavioral_score or 0),
                    'recovery': float(profile_record.sleep_quality_score or 0)
                },
                'stability_score': 0,  # 数据库中没有，设为默认值
                'risk_score': float(profile_record.predicted_risk_score or 0),
                'improvement_potential': 0,  # 计算改善潜力
                'data_quality_score': 0.8  # 默认质量评分
            }
            
            # 构建维度画像
            dimension_profiles = {}
            for dimension, config in self.PROFILE_DIMENSIONS.items():
                score = health_index['dimension_scores'].get(dimension, 0)
                dimension_profiles[dimension] = {
                    'name': config['name'],
                    'icon': config['icon'],
                    'score': score,
                    'level': self._determine_health_level(score),
                    'weight': config['weight'],
                    'feature_count': len(config['features']),
                    'scored_features': len(config['features']),
                    'feature_details': {},
                    'completeness': 1.0,
                    'source': 'database'
                }
            
            # 构建健康洞察
            health_insights = [f"用户健康画像来源于数据库记录，整体健康评分 {health_index['overall_score']} 分"]
            
            # 构建个性化标签
            level_config = self.HEALTH_LABELS.get(profile_record.health_level or 'fair', {})
            personality_tags = [{
                'type': 'health_level',
                'text': level_config.get('label', '一般'),
                'color': level_config.get('color', '#faad14'),
                'icon': level_config.get('badge', '⚠️')
            }]
            
            # 生成画像汇总
            profile_summary = {
                'user_id': user_id,
                'target_date': target_date,
                'profile_type': 'comprehensive',
                'data_source': 'database',
                'health_index': health_index,
                'dimension_count': len(dimension_profiles),
                'data_completeness': 1.0,
                'profile_confidence': 0.9,
                'last_update': profile_record.update_time.isoformat() if profile_record.update_time else datetime.now().isoformat(),
                'generation_time': 0
            }
            
            # 构建完整画像
            complete_profile = {
                'user_info': user_info,
                'health_index': health_index,
                'dimension_profiles': dimension_profiles,
                'health_insights': health_insights,
                'personality_tags': personality_tags,
                'raw_data': {
                    'detailed_analysis': profile_record.detailed_analysis,
                    'trend_analysis': profile_record.trend_analysis,
                    'recommendations': profile_record.recommendations
                },
                'summary': profile_summary
            }
            
            logger.info(f"📋 从数据库获取用户 {user_id} 画像: 健康等级 {profile_record.health_level}，综合评分 {health_index['overall_score']}")
            
            return {
                'success': True,
                'data': complete_profile,
                'source': 'database'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 数据库画像查询失败: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'database_error'}
    
    def _generate_profile_realtime(self, user_id: int, target_date: str, profile_type: str, start_time: float) -> Dict:
        """实时生成健康画像（原有逻辑）"""
        logger.info(f"🔄 开始实时生成用户 {user_id} 健康画像，日期: {target_date}，类型: {profile_type}")
        
        try:
            # 1. 获取用户基本信息
            user_info = self._get_user_basic_info(user_id)
            
            # 2. 并行获取各个维度的数据
            profile_data = {}
            
            # 2.1 获取基线数据
            baseline_result = realtime_baseline_engine.generate_user_baseline_realtime(
                user_id, (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            )
            profile_data['baseline'] = baseline_result.get('data', {}) if baseline_result.get('success') else {}
            
            # 2.2 获取评分数据
            score_result = realtime_score_engine.calculate_user_health_score_realtime(
                user_id, (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            )
            profile_data['score'] = score_result.get('data', {}) if score_result.get('success') else {}
            
            # 2.3 获取建议数据
            recommendation_result = realtime_recommendation_engine.generate_user_health_recommendations_realtime(
                user_id, (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            )
            profile_data['recommendations'] = recommendation_result.get('data', {}) if recommendation_result.get('success') else {}
            
            # 2.4 获取预测数据
            prediction_result = realtime_prediction_engine.generate_user_health_prediction_realtime(
                user_id, target_date, 30
            )
            profile_data['predictions'] = prediction_result.get('data', {}) if prediction_result.get('success') else {}
            
            # 2.5 获取历史趋势数据
            historical_trends = self._get_historical_trends(user_id, target_date)
            profile_data['trends'] = historical_trends
            
            # 3. 构建维度画像
            dimension_profiles = self._build_dimension_profiles(profile_data, profile_type)
            
            # 4. 计算综合健康指数
            health_index = self._calculate_health_index(dimension_profiles, profile_data)
            
            # 5. 生成健康洞察
            health_insights = self._generate_health_insights(
                dimension_profiles, health_index, profile_data, user_info
            )
            
            # 6. 构建个性化特征标签
            personality_tags = self._generate_personality_tags(profile_data, dimension_profiles, user_info)
            
            # 7. 生成健康画像汇总
            profile_summary = {
                'user_id': user_id,
                'target_date': target_date,
                'profile_type': profile_type,
                'data_source': 'realtime',
                'health_index': health_index,
                'dimension_count': len(dimension_profiles),
                'data_completeness': self._calculate_data_completeness(profile_data),
                'profile_confidence': self._calculate_profile_confidence(profile_data),
                'last_update': datetime.now().isoformat(),
                'generation_time': round(time.time() - start_time, 3)
            }
            
            # 8. 构建完整健康画像
            complete_profile = {
                'user_info': user_info,
                'health_index': health_index,
                'dimension_profiles': dimension_profiles,
                'health_insights': health_insights,
                'personality_tags': personality_tags,
                'raw_data': profile_data,
                'summary': profile_summary
            }
            
            # 9. 缓存结果
            cache_key = f"realtime_profile:user:{user_id}:{target_date}:{profile_type}"
            self.redis.set_data(cache_key, json.dumps(complete_profile, default=str), 7200)  # 缓存2小时
            
            logger.info(f"✅ 用户 {user_id} 健康画像生成完成: 健康指数 {health_index['overall_score']}")
            
            return {
                'success': True,
                'data': complete_profile
            }
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 健康画像生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def generate_department_health_profile_realtime(self, org_id: int, target_date: str = None) -> Dict:
        """
        实时生成部门健康画像聚合
        
        Args:
            org_id: 组织ID
            target_date: 目标日期，默认为今天
            
        Returns:
            Dict: 包含部门级别的健康画像聚合
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始生成部门 {org_id} 的实时健康画像聚合，日期: {target_date}")
        
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
            
            # 2. 获取每个用户的健康画像
            user_profiles = {}
            department_dimension_stats = {}
            department_health_distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0}
            total_users = len(users)
            processed_users = 0
            
            for user in users:
                user_id = user['id']
                user_profile_result = self.generate_user_health_profile_realtime(user_id, target_date)
                
                if user_profile_result.get('success'):
                    user_profiles[user_id] = user_profile_result['data']
                    processed_users += 1
                    
                    # 聚合维度统计
                    dimension_profiles = user_profile_result['data'].get('dimension_profiles', {})
                    for dimension, dim_data in dimension_profiles.items():
                        if dimension not in department_dimension_stats:
                            department_dimension_stats[dimension] = {
                                'scores': [],
                                'levels': [],
                                'user_count': 0
                            }
                        department_dimension_stats[dimension]['scores'].append(dim_data.get('score', 0))
                        department_dimension_stats[dimension]['levels'].append(dim_data.get('level', 'unknown'))
                        department_dimension_stats[dimension]['user_count'] += 1
                    
                    # 聚合健康等级分布
                    health_level = user_profile_result['data']['health_index'].get('overall_level', 'fair')
                    department_health_distribution[health_level] += 1
                else:
                    logger.warning(f"⚠️ 用户 {user_id} 画像生成失败: {user_profile_result.get('error')}")
            
            # 3. 计算部门级别统计
            department_stats = self._calculate_department_profile_stats(
                department_dimension_stats, department_health_distribution, total_users
            )
            
            # 4. 生成部门健康洞察
            department_insights = self._generate_department_health_insights(
                department_stats, department_health_distribution, total_users
            )
            
            # 5. 识别部门健康特征
            department_characteristics = self._identify_department_characteristics(
                user_profiles, department_stats
            )
            
            # 6. 生成部门汇总
            department_summary = {
                'org_id': org_id,
                'target_date': target_date,
                'total_users': total_users,
                'processed_users': processed_users,
                'coverage_rate': round(processed_users / total_users, 3) if total_users > 0 else 0,
                'health_distribution': department_health_distribution,
                'average_health_index': department_stats.get('avg_health_index', 0),
                'generation_time': round(time.time() - start_time, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            # 7. 缓存结果
            cache_key = f"realtime_profile:department:{org_id}:{target_date}"
            cache_data = {
                'user_profiles': user_profiles,
                'department_stats': department_stats,
                'health_distribution': department_health_distribution,
                'insights': department_insights,
                'characteristics': department_characteristics,
                'summary': department_summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 7200)
            
            logger.info(f"✅ 部门 {org_id} 健康画像聚合完成: 处理用户 {processed_users}/{total_users}")
            
            return {
                'success': True,
                'data': {
                    'user_profiles': user_profiles,
                    'department_stats': department_stats,
                    'health_distribution': department_health_distribution,
                    'insights': department_insights,
                    'characteristics': department_characteristics,
                    'summary': department_summary
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 部门 {org_id} 健康画像聚合失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'org_id': org_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _get_user_basic_info(self, user_id: int) -> Dict:
        """获取用户基本信息"""
        try:
            from .models import UserInfo, OrgInfo, UserOrg
            
            user = db.session.query(UserInfo, OrgInfo.name.label('dept_name')).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo, UserOrg.org_id == OrgInfo.id
            ).filter(
                UserInfo.id == user_id,
                UserInfo.is_deleted == False
            ).first()
            
            if user:
                return {
                    'user_id': user_id,
                    'user_name': user[0].user_name or '未知用户',
                    'phone': user[0].phone or '',
                    'dept_name': user[1] or '未知部门',
                    'device_sn': user[0].device_sn or '',
                    'avatar': user[0].avatar or '',
                    'create_time': user[0].create_time.isoformat() if user[0].create_time else None
                }
            else:
                return {
                    'user_id': user_id,
                    'user_name': '未知用户',
                    'phone': '',
                    'dept_name': '未知部门',
                    'device_sn': '',
                    'avatar': '',
                    'create_time': None
                }
        except Exception as e:
            logger.warning(f"获取用户 {user_id} 基本信息失败: {e}")
            return {
                'user_id': user_id,
                'user_name': '未知用户',
                'phone': '',
                'dept_name': '未知部门',
                'device_sn': '',
                'avatar': '',
                'create_time': None
            }
    
    def _get_historical_trends(self, user_id: int, target_date: str) -> Dict:
        """获取历史趋势数据"""
        trends = {}
        
        try:
            # 获取不同时间维度的数据
            for period, config in self.TIME_DIMENSIONS.items():
                start_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=config['days'])).strftime('%Y-%m-%d')
                
                history_result = get_all_health_data_optimized(
                    userId=user_id,
                    startDate=start_date,
                    endDate=target_date,
                    latest_only=False,
                    pageSize=None
                )
                
                if history_result.get('success'):
                    history_data = history_result.get('data', {}).get('healthData', [])
                    trends[period] = {
                        'label': config['label'],
                        'data_points': len(history_data),
                        'date_range': f"{start_date} to {target_date}",
                        'summary': self._analyze_period_trends(history_data)
                    }
                else:
                    trends[period] = {
                        'label': config['label'],
                        'data_points': 0,
                        'date_range': f"{start_date} to {target_date}",
                        'summary': {}
                    }
        
        except Exception as e:
            logger.warning(f"获取用户 {user_id} 历史趋势失败: {e}")
        
        return trends
    
    def _analyze_period_trends(self, health_data: List[Dict]) -> Dict:
        """分析时期趋势"""
        if not health_data:
            return {}
        
        df = realtime_baseline_engine._convert_to_dataframe(health_data)
        summary = {}
        
        for feature in self.HEALTH_FEATURES:
            if feature in df.columns:
                feature_data = df[feature].dropna()
                if len(feature_data) > 0:
                    summary[feature] = {
                        'mean': round(float(feature_data.mean()), 2),
                        'std': round(float(feature_data.std()), 2),
                        'min': round(float(feature_data.min()), 2),
                        'max': round(float(feature_data.max()), 2),
                        'count': len(feature_data)
                    }
        
        return summary
    
    def _build_dimension_profiles(self, profile_data: Dict, profile_type: str) -> Dict:
        """构建维度画像"""
        dimension_profiles = {}
        
        # 获取评分数据
        feature_scores = profile_data.get('score', {}).get('feature_scores', {})
        
        for dimension, config in self.PROFILE_DIMENSIONS.items():
            # 根据画像类型调整权重
            if profile_type != 'comprehensive':
                if dimension in profile_type:
                    weight_multiplier = 1.5  # 重点关注的维度
                else:
                    weight_multiplier = 0.7  # 其他维度
            else:
                weight_multiplier = 1.0
            
            # 计算维度评分
            dimension_scores = []
            feature_details = {}
            
            for feature in config['features']:
                if feature in feature_scores:
                    score_data = feature_scores[feature]
                    score = score_data.get('score_value', 0)
                    dimension_scores.append(score)
                    feature_details[feature] = {
                        'score': score,
                        'level': self._determine_health_level(score),
                        'display_name': self._get_feature_display_name(feature)
                    }
            
            # 计算维度综合评分
            if dimension_scores:
                dimension_score = round(np.mean(dimension_scores), 2)
                dimension_level = self._determine_health_level(dimension_score)
            else:
                dimension_score = 0
                dimension_level = 'unknown'
            
            dimension_profiles[dimension] = {
                'name': config['name'],
                'icon': config['icon'],
                'score': dimension_score,
                'level': dimension_level,
                'weight': config['weight'] * weight_multiplier,
                'feature_count': len(config['features']),
                'scored_features': len(dimension_scores),
                'feature_details': feature_details,
                'completeness': len(dimension_scores) / len(config['features']) if config['features'] else 0
            }
        
        return dimension_profiles
    
    def _calculate_health_index(self, dimension_profiles: Dict, profile_data: Dict) -> Dict:
        """计算综合健康指数"""
        # 计算加权综合评分
        total_weighted_score = 0
        total_weight = 0
        
        for dimension, dim_data in dimension_profiles.items():
            score = dim_data.get('score', 0)
            weight = dim_data.get('weight', 0)
            total_weighted_score += score * weight
            total_weight += weight
        
        overall_score = round(total_weighted_score / total_weight, 2) if total_weight > 0 else 0
        overall_level = self._determine_health_level(overall_score)
        
        # 计算健康指数的其他指标
        score_summary = profile_data.get('score', {}).get('summary', {})
        prediction_summary = profile_data.get('predictions', {}).get('summary', {})
        
        health_index = {
            'overall_score': overall_score,
            'overall_level': overall_level,
            'level_info': self.HEALTH_LABELS.get(overall_level, {}),
            'dimension_scores': {
                dim: data.get('score', 0) 
                for dim, data in dimension_profiles.items()
            },
            'stability_score': self._calculate_stability_score(profile_data),
            'risk_score': prediction_summary.get('overall_risk_score', 0),
            'improvement_potential': self._calculate_improvement_potential(dimension_profiles),
            'data_quality_score': score_summary.get('quality_indicators', {}).get('overall_quality', 0)
        }
        
        return health_index
    
    def _calculate_stability_score(self, profile_data: Dict) -> float:
        """计算健康稳定性评分"""
        trends = profile_data.get('trends', {})
        
        stability_scores = []
        
        for period, trend_data in trends.items():
            summary = trend_data.get('summary', {})
            for feature, stats in summary.items():
                if 'std' in stats and 'mean' in stats:
                    mean_val = stats['mean']
                    std_val = stats['std']
                    cv = std_val / mean_val if mean_val > 0 else 1
                    stability_score = max(0, 1 - cv)  # 变异系数越小，稳定性越高
                    stability_scores.append(stability_score)
        
        return round(np.mean(stability_scores), 3) if stability_scores else 0
    
    def _calculate_improvement_potential(self, dimension_profiles: Dict) -> float:
        """计算改善潜力评分"""
        improvement_scores = []
        
        for dimension, dim_data in dimension_profiles.items():
            current_score = dim_data.get('score', 0)
            # 改善潜力 = (100 - 当前分数) / 100，分数越低改善潜力越大
            improvement_potential = (100 - current_score) / 100
            improvement_scores.append(improvement_potential)
        
        return round(np.mean(improvement_scores), 3) if improvement_scores else 0
    
    def _generate_health_insights(self, dimension_profiles: Dict, health_index: Dict, 
                                 profile_data: Dict, user_info: Dict) -> List[str]:
        """生成健康洞察"""
        insights = []
        
        overall_level = health_index.get('overall_level', 'fair')
        overall_score = health_index.get('overall_score', 0)
        
        # 1. 总体健康状况洞察
        if overall_level == 'excellent':
            insights.append(f"🏆 {user_info['user_name']} 的整体健康状况优秀（{overall_score}分），各项指标表现良好")
        elif overall_level == 'good':
            insights.append(f"👍 {user_info['user_name']} 的健康状况良好（{overall_score}分），继续保持当前状态")
        elif overall_level == 'fair':
            insights.append(f"⚠️ {user_info['user_name']} 的健康状况一般（{overall_score}分），有进一步改善空间")
        elif overall_level == 'poor':
            insights.append(f"📉 {user_info['user_name']} 的健康状况较差（{overall_score}分），需要积极改善")
        else:
            insights.append(f"🚨 {user_info['user_name']} 的健康状况存在风险（{overall_score}分），建议立即关注")
        
        # 2. 维度强项洞察
        strong_dimensions = [
            (dim, data) for dim, data in dimension_profiles.items() 
            if data.get('score', 0) >= 80
        ]
        if strong_dimensions:
            strong_names = [self.PROFILE_DIMENSIONS[dim]['name'] for dim, _ in strong_dimensions]
            insights.append(f"💪 健康强项：{', '.join(strong_names[:3])} 表现优秀")
        
        # 3. 维度弱项洞察
        weak_dimensions = [
            (dim, data) for dim, data in dimension_profiles.items() 
            if data.get('score', 0) < 60
        ]
        if weak_dimensions:
            weak_names = [self.PROFILE_DIMENSIONS[dim]['name'] for dim, _ in weak_dimensions]
            insights.append(f"🔴 需要改善：{', '.join(weak_names[:3])} 需要重点关注")
        
        # 4. 稳定性洞察
        stability_score = health_index.get('stability_score', 0)
        if stability_score > 0.8:
            insights.append("📊 健康数据稳定性很好，各项指标波动较小")
        elif stability_score < 0.5:
            insights.append("📈 健康数据波动较大，建议关注指标稳定性")
        
        # 5. 风险预警洞察
        risk_score = health_index.get('risk_score', 0)
        if risk_score > 0.6:
            insights.append(f"⚠️ 健康风险较高（风险指数 {risk_score:.2f}），建议预防性干预")
        
        # 6. 建议洞察
        recommendations = profile_data.get('recommendations', {}).get('priority_issues', [])
        if recommendations:
            insights.append(f"💡 优先建议：关注{', '.join(recommendations[:2])}等方面的改善")
        
        return insights
    
    def _generate_personality_tags(self, profile_data: Dict, dimension_profiles: Dict, 
                                 user_info: Dict) -> List[Dict]:
        """生成个性化特征标签"""
        tags = []
        
        # 1. 基于整体健康等级的标签
        overall_level = profile_data.get('score', {}).get('summary', {}).get('health_level', 'fair')
        level_config = self.HEALTH_LABELS.get(overall_level, {})
        tags.append({
            'type': 'health_level',
            'text': level_config.get('label', '一般'),
            'color': level_config.get('color', '#faad14'),
            'icon': level_config.get('badge', '⚠️')
        })
        
        # 2. 基于维度表现的标签
        for dimension, dim_data in dimension_profiles.items():
            score = dim_data.get('score', 0)
            if score >= 90:
                config = self.PROFILE_DIMENSIONS[dimension]
                tags.append({
                    'type': 'strength',
                    'text': f"{config['name']}优秀",
                    'color': '#52c41a',
                    'icon': config['icon']
                })
            elif score < 60:
                config = self.PROFILE_DIMENSIONS[dimension]
                tags.append({
                    'type': 'concern',
                    'text': f"{config['name']}需改善",
                    'color': '#f5222d',
                    'icon': '⚠️'
                })
        
        # 3. 基于预测风险的标签
        risk_score = profile_data.get('predictions', {}).get('summary', {}).get('overall_risk_score', 0)
        if risk_score > 0.7:
            tags.append({
                'type': 'risk',
                'text': '高风险预警',
                'color': '#f5222d',
                'icon': '🚨'
            })
        elif risk_score < 0.3:
            tags.append({
                'type': 'safe',
                'text': '低风险状态',
                'color': '#52c41a',
                'icon': '✅'
            })
        
        # 4. 基于数据质量的标签
        data_quality = profile_data.get('score', {}).get('summary', {}).get('quality_indicators', {}).get('overall_quality', 0)
        if data_quality > 0.8:
            tags.append({
                'type': 'quality',
                'text': '数据充足',
                'color': '#1890ff',
                'icon': '📊'
            })
        elif data_quality < 0.5:
            tags.append({
                'type': 'quality',
                'text': '数据不足',
                'color': '#faad14',
                'icon': '📉'
            })
        
        return tags
    
    def _calculate_data_completeness(self, profile_data: Dict) -> float:
        """计算数据完整性"""
        completeness_scores = []
        
        # 基线数据完整性
        baseline_data = profile_data.get('baseline', {}).get('baselines', {})
        baseline_completeness = len(baseline_data) / len(self.HEALTH_FEATURES)
        completeness_scores.append(baseline_completeness)
        
        # 评分数据完整性
        score_data = profile_data.get('score', {}).get('feature_scores', {})
        score_completeness = len(score_data) / len(self.HEALTH_FEATURES)
        completeness_scores.append(score_completeness)
        
        # 建议数据完整性
        recommendation_data = profile_data.get('recommendations', {}).get('feature_recommendations', {})
        recommendation_completeness = len(recommendation_data) / len(self.HEALTH_FEATURES)
        completeness_scores.append(recommendation_completeness)
        
        # 预测数据完整性
        prediction_data = profile_data.get('predictions', {}).get('feature_predictions', {})
        prediction_completeness = len(prediction_data) / len(self.HEALTH_FEATURES)
        completeness_scores.append(prediction_completeness)
        
        return round(np.mean(completeness_scores), 3) if completeness_scores else 0
    
    def _calculate_profile_confidence(self, profile_data: Dict) -> float:
        """计算画像置信度"""
        confidence_scores = []
        
        # 评分置信度
        score_quality = profile_data.get('score', {}).get('summary', {}).get('quality_indicators', {}).get('overall_quality', 0)
        confidence_scores.append(score_quality)
        
        # 预测置信度
        prediction_confidence = profile_data.get('predictions', {}).get('summary', {}).get('prediction_confidence', 0)
        confidence_scores.append(prediction_confidence)
        
        # 建议质量
        recommendation_quality = profile_data.get('recommendations', {}).get('summary', {}).get('recommendation_quality', {}).get('overall_quality', 0)
        confidence_scores.append(recommendation_quality)
        
        # 数据完整性
        data_completeness = self._calculate_data_completeness(profile_data)
        confidence_scores.append(data_completeness)
        
        return round(np.mean(confidence_scores), 3) if confidence_scores else 0
    
    def _calculate_department_profile_stats(self, dimension_stats: Dict, 
                                          health_distribution: Dict, total_users: int) -> Dict:
        """计算部门画像统计"""
        stats = {}
        
        # 计算各维度的部门平均值
        for dimension, data in dimension_stats.items():
            scores = data.get('scores', [])
            if scores:
                stats[dimension] = {
                    'avg_score': round(np.mean(scores), 2),
                    'min_score': round(np.min(scores), 2),
                    'max_score': round(np.max(scores), 2),
                    'std_score': round(np.std(scores), 2),
                    'user_count': data.get('user_count', 0)
                }
        
        # 计算整体健康指数
        if stats:
            dimension_scores = [stat['avg_score'] for stat in stats.values()]
            avg_health_index = round(np.mean(dimension_scores), 2)
        else:
            avg_health_index = 0
        
        stats['avg_health_index'] = avg_health_index
        stats['health_distribution'] = health_distribution
        stats['total_users'] = total_users
        
        return stats
    
    def _generate_department_health_insights(self, department_stats: Dict, 
                                           health_distribution: Dict, total_users: int) -> List[str]:
        """生成部门健康洞察"""
        insights = []
        
        # 整体健康状况
        avg_health_index = department_stats.get('avg_health_index', 0)
        excellent_count = health_distribution.get('excellent', 0)
        good_count = health_distribution.get('good', 0)
        poor_count = health_distribution.get('poor', 0)
        critical_count = health_distribution.get('critical', 0)
        
        excellent_percentage = round(excellent_count / total_users * 100, 1) if total_users > 0 else 0
        good_percentage = round(good_count / total_users * 100, 1) if total_users > 0 else 0
        
        if excellent_percentage > 50:
            insights.append(f"🏆 部门整体健康状况优秀，{excellent_percentage}%的员工健康指数优秀")
        elif good_percentage + excellent_percentage > 70:
            insights.append(f"👍 部门健康状况良好，{good_percentage + excellent_percentage:.1f}%的员工健康状况良好以上")
        elif poor_count + critical_count > total_users * 0.3:
            insights.append(f"⚠️ 部门健康状况需要关注，{poor_count + critical_count}名员工健康状况较差")
        
        # 维度强弱项分析
        dimension_scores = [(dim, stat.get('avg_score', 0)) for dim, stat in department_stats.items() 
                           if dim != 'avg_health_index' and dim != 'health_distribution' and dim != 'total_users']
        dimension_scores.sort(key=lambda x: x[1], reverse=True)
        
        if dimension_scores:
            best_dimension = dimension_scores[0]
            worst_dimension = dimension_scores[-1]
            
            best_name = self.PROFILE_DIMENSIONS.get(best_dimension[0], {}).get('name', best_dimension[0])
            worst_name = self.PROFILE_DIMENSIONS.get(worst_dimension[0], {}).get('name', worst_dimension[0])
            
            insights.append(f"💪 部门健康强项：{best_name}（平均 {best_dimension[1]} 分）")
            if worst_dimension[1] < 70:
                insights.append(f"🔴 需要改善领域：{worst_name}（平均 {worst_dimension[1]} 分）")
        
        return insights
    
    def _identify_department_characteristics(self, user_profiles: Dict, department_stats: Dict) -> List[Dict]:
        """识别部门健康特征"""
        characteristics = []
        
        # 基于健康分布的特征
        total_users = len(user_profiles)
        if total_users == 0:
            return characteristics
        
        # 计算各等级比例
        level_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'critical': 0}
        for user_id, profile in user_profiles.items():
            level = profile.get('health_index', {}).get('overall_level', 'fair')
            level_counts[level] += 1
        
        # 识别主要特征
        if level_counts['excellent'] / total_users > 0.6:
            characteristics.append({
                'type': 'excellence',
                'title': '健康优秀型部门',
                'description': f"部门内{level_counts['excellent']}/{total_users}员工健康状况优秀",
                'icon': '🏆',
                'color': '#52c41a'
            })
        
        if level_counts['poor'] + level_counts['critical'] > total_users * 0.3:
            characteristics.append({
                'type': 'concern',
                'title': '健康关注型部门',
                'description': f"部门内{level_counts['poor'] + level_counts['critical']}名员工需要健康关注",
                'icon': '⚠️',
                'color': '#f5222d'
            })
        
        # 基于维度表现的特征
        avg_health_index = department_stats.get('avg_health_index', 0)
        if avg_health_index > 85:
            characteristics.append({
                'type': 'high_performance',
                'title': '高健康指数部门',
                'description': f"部门平均健康指数 {avg_health_index} 分，表现优异",
                'icon': '📊',
                'color': '#1890ff'
            })
        
        return characteristics
    
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


# 全局实例
realtime_profile_engine = RealTimeHealthProfileEngine()


def get_user_health_profile_realtime(user_id: int, target_date: str = None, 
                                   profile_type: str = 'comprehensive') -> Dict:
    """获取用户实时健康画像 - 对外接口"""
    return realtime_profile_engine.generate_user_health_profile_realtime(
        user_id, target_date, profile_type
    )


def get_department_health_profile_realtime(org_id: int, target_date: str = None) -> Dict:
    """获取部门实时健康画像聚合 - 对外接口"""
    return realtime_profile_engine.generate_department_health_profile_realtime(org_id, target_date)


def get_health_profile_status(identifier: int, identifier_type: str = 'user', 
                            target_date: str = None, profile_type: str = 'comprehensive') -> Dict:
    """获取画像状态 - 对外接口"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    if identifier_type == 'user':
        cache_key = f"realtime_profile:user:{identifier}:{target_date}:{profile_type}"
    else:
        cache_key = f"realtime_profile:department:{identifier}:{target_date}"
    
    cached_result = realtime_profile_engine.redis.get_data(cache_key)
    
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
            'message': '未找到缓存的画像数据',
            'identifier': identifier,
            'identifier_type': identifier_type,
            'target_date': target_date,
            'profile_type': profile_type
        }