"""
实时健康评分计算引擎
基于实时基线数据计算健康评分，支持用户、组织和租户三级查询

依赖统一的get_all_health_data_optimized查询方法和health_baseline_engine
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from .redis_helper import RedisHelper
from .user_health_data import get_all_health_data_optimized
from .health_baseline_engine import realtime_baseline_engine
from .health_query_base import health_query_base
from .models import db, HealthScore
from sqlalchemy import and_, or_
import json
import time

logger = logging.getLogger(__name__)

class RealTimeHealthScoreEngine:
    """实时健康评分计算引擎"""
    
    def __init__(self):
        self.redis = RedisHelper()
        
        # 健康特征配置 - 与ljwx-boot保持一致
        self.HEALTH_FEATURES = [
            "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
            "pressure_low", "stress", "step", "calorie", "distance", "sleep"
        ]
        
        # 默认权重配置 - 基于医学重要性
        self.DEFAULT_WEIGHTS = {
            "heart_rate": 0.20,      # 最重要的生命体征
            "blood_oxygen": 0.18,    # 呼吸系统核心指标  
            "temperature": 0.15,     # 基础生命体征
            "pressure_high": 0.06,   # 心血管健康指标
            "pressure_low": 0.06,    # 心血管健康指标
            "stress": 0.12,          # 心理健康重要指标
            "sleep": 0.08,           # 恢复性健康指标
            "step": 0.04,            # 日常活动量
            "distance": 0.03,        # 运动强度
            "calorie": 0.03          # 代谢水平
        }
        
        # 特征值范围配置
        self.FEATURE_RANGES = {
            "heart_rate": (30.0, 200.0),
            "blood_oxygen": (70.0, 100.0),
            "temperature": (30.0, 45.0),
            "pressure_high": (60.0, 250.0),
            "pressure_low": (40.0, 150.0),
            "stress": (0.0, 100.0),
            "step": (0.0, 50000.0),
            "calorie": (0.0, 5000.0),
            "distance": (0.0, 100.0),
            "sleep": (0.0, 24.0)
        }
    
    def calculate_health_score_unified(self, **kwargs) -> Dict:
        """
        统一的健康评分计算方法
        支持用户、组织、租户三级查询
        
        Args:
            user_id: 用户ID (优先级最高)
            org_id: 组织ID (中等优先级)
            customer_id: 租户ID (最低优先级)
            startDate/start_date: 开始日期
            endDate/end_date: 结束日期
            
        Returns:
            Dict: 包含健康评分和详细信息
        """
        start_time = time.time()
        
        try:
            # 解析查询参数
            query_params = health_query_base.parse_query_params(**kwargs)
            
            # 验证参数
            is_valid, error_msg = health_query_base.validate_query_params(query_params)
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # 记录查询信息
            health_query_base.log_query_info('score', query_params)
            
            # 步骤1: 优先从数据库查询已生成的评分
            db_result = self._query_database_scores_unified(query_params)
            if db_result['success'] and db_result['data']:
                result_summary = {
                    'record_count': len(db_result['data'].get('feature_scores', {})),
                    'execution_time': round(time.time() - start_time, 3)
                }
                health_query_base.log_query_info('score', query_params, result_summary)
                return db_result
            
            # 步骤2: 数据库无数据，执行实时计算
            logger.info(f"📊 {query_params['query_level']} {query_params['identifier']} 数据库无评分数据，开始实时计算...")
            return self._calculate_scores_realtime_unified(query_params, start_time)
            
        except Exception as e:
            logger.error(f"❌ 健康评分获取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': round(time.time() - start_time, 3)
            }

    def calculate_user_health_score_realtime(self, user_id: int, target_date: str = None) -> Dict:
        """
        计算用户健康评分 - 兼容方法
        内部调用统一方法
        """
        return self.calculate_health_score_unified(
            user_id=user_id,
            startDate=target_date,
            endDate=target_date
        )
    
    def _query_database_scores_unified(self, query_params: Dict) -> Dict:
        """统一的数据库评分查询方法"""
        try:
            # 构建查询条件
            conditions, params = health_query_base.build_database_conditions(query_params)
            
            if not conditions:
                return {'success': True, 'data': None, 'source': 'database_empty'}
            
            # 构建查询
            query = db.session.query(HealthScore)
            
            # 添加基础条件
            if query_params['query_level'] == 'user':
                query = query.filter(HealthScore.user_id == query_params['identifier'])
            elif query_params['query_level'] == 'org':
                query = query.filter(HealthScore.org_id == query_params['identifier'])
            elif query_params['query_level'] == 'customer':
                query = query.filter(HealthScore.customer_id == query_params['identifier'])
            
            # 添加日期条件
            if query_params['start_date'] == query_params['end_date']:
                query = query.filter(HealthScore.score_date == query_params['start_date'])
            else:
                query = query.filter(
                    and_(
                        HealthScore.score_date >= query_params['start_date'],
                        HealthScore.score_date <= query_params['end_date']
                    )
                )
            
            score_records = query.all()
            
            if not score_records:
                return {'success': True, 'data': None, 'source': 'database_empty'}
            
            # 转换为标准格式
            feature_scores = {}
            total_weighted_score = 0
            total_weight = 0
            
            for record in score_records:
                feature_name = record.feature_name
                score_value = float(record.score_value) if record.score_value else 0.0
                weight = self.DEFAULT_WEIGHTS.get(feature_name, 0.1)
                
                feature_scores[feature_name] = {
                    'feature_name': feature_name,
                    'avg_value': float(record.avg_value) if record.avg_value else 0.0,
                    'z_score': float(record.z_score) if record.z_score else 0.0,
                    'score_value': score_value,
                    'penalty_value': float(record.penalty_value) if record.penalty_value else 0.0,
                    'weight': weight,
                    'baseline_date': record.baseline_time.strftime('%Y-%m-%d') if record.baseline_time else query_params['start_date'],
                    'source': 'database'
                }
                
                total_weighted_score += score_value * weight
                total_weight += weight
            
            # 计算综合评分
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            health_level = self._determine_health_level(overall_score)
            
            # 生成汇总信息
            summary = {
                'query_level': query_params['query_level'],
                'identifier': query_params['identifier'],
                'start_date': query_params['start_date'],
                'end_date': query_params['end_date'],
                'data_source': 'database',
                'overall_score': round(overall_score, 2),
                'health_level': health_level,
                'features_evaluated': len(feature_scores),
                'total_weight': round(total_weight, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 从数据库获取 {query_params['query_level']} {query_params['identifier']} 评分: {len(feature_scores)} 个特征，综合评分: {overall_score:.2f}")
            
            return {
                'success': True,
                'data': {
                    'feature_scores': feature_scores,
                    'summary': summary
                },
                'source': 'database'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 数据库评分查询失败: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'database_error'}

    def _query_database_scores(self, user_id: int, target_date: str) -> Dict:
        """从数据库查询已生成的健康评分 - 兼容方法"""
        query_params = health_query_base.parse_query_params(
            user_id=user_id,
            startDate=target_date,
            endDate=target_date
        )
        return self._query_database_scores_unified(query_params)
    
    def _calculate_scores_realtime_unified(self, query_params: Dict, start_time: float) -> Dict:
        """统一的实时计算健康评分方法"""
        logger.info(f"🔄 开始实时计算 {query_params['query_level']} {query_params['identifier']} 健康评分，日期: {query_params['start_date']}")
        
        try:
            # 1. 根据查询层级获取基线数据
            baseline_result = self._get_baseline_data_unified(query_params)
            
            if not baseline_result.get('success'):
                logger.warning(f"⚠️ {query_params['query_level']} {query_params['identifier']} 基线获取失败: {baseline_result.get('error')}")
                return {
                    'success': False,
                    'error': f"基线数据获取失败: {baseline_result.get('error')}",
                    'query_params': query_params
                }
            
            baselines = baseline_result['data']['baselines']
            
            # 2. 获取健康数据
            health_result = self._get_health_data_unified(query_params)
            
            if not health_result.get('success'):
                return {
                    'success': False,
                    'error': health_result.get('message'),
                    'query_params': query_params
                }
            
            health_data = health_result.get('data', {}).get('healthData', [])
            
            if not health_data:
                return {
                    'success': False,
                    'error': '指定日期无健康数据',
                    'query_params': query_params
                }
            
            # 3. 转换数据格式
            df = self._convert_to_dataframe(health_data)
            
            # 4. 计算每个特征的评分
            feature_scores = {}
            total_weighted_score = 0
            total_weights = 0
            
            for feature in self.HEALTH_FEATURES:
                if feature in baselines and feature in df.columns:
                    score_result = self._calculate_feature_score_unified(
                        df, feature, baselines[feature], query_params)
                    
                    if score_result:
                        feature_scores[feature] = score_result
                        weight = self.DEFAULT_WEIGHTS.get(feature, 0.01)
                        total_weighted_score += score_result['score_value'] * weight
                        total_weights += weight
            
            # 5. 计算综合评分
            if total_weights > 0:
                overall_score = round(total_weighted_score / total_weights, 2)
                health_level = self._determine_health_level(overall_score)
            else:
                overall_score = 0
                health_level = 'unknown'
            
            # 6. 生成评分汇总
            summary = {
                'query_level': query_params['query_level'],
                'identifier': query_params['identifier'],
                'start_date': query_params['start_date'],
                'end_date': query_params['end_date'],
                'data_source': 'realtime',
                'overall_score': overall_score,
                'health_level': health_level,
                'features_evaluated': len(feature_scores),
                'total_weight': round(total_weights, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            # 7. 缓存结果
            cache_key = health_query_base.build_cache_key('score', query_params)
            cache_data = {
                'feature_scores': feature_scores,
                'summary': summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 3600)
            
            logger.info(f"✅ {query_params['query_level']} {query_params['identifier']} 健康评分计算完成: 总分 {overall_score}，等级 {health_level}")
            
            return {
                'success': True,
                'data': {
                    'feature_scores': feature_scores,
                    'summary': summary
                }
            }
            
        except Exception as e:
            logger.error(f"❌ {query_params['query_level']} {query_params['identifier']} 健康评分计算失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query_params': query_params,
                'execution_time': round(time.time() - start_time, 3)
            }

    def _calculate_scores_realtime(self, user_id: int, target_date: str, start_time: float) -> Dict:
        """实时计算健康评分 - 兼容方法"""
        query_params = health_query_base.parse_query_params(
            user_id=user_id,
            startDate=target_date,
            endDate=target_date
        )
        return self._calculate_scores_realtime_unified(query_params, start_time)
    
    def _get_baseline_data_unified(self, query_params: Dict) -> Dict:
        """根据查询参数获取基线数据"""
        try:
            if query_params['query_level'] == 'user':
                # 用户级基线
                return realtime_baseline_engine.generate_user_baseline_realtime(
                    query_params['identifier'], 
                    query_params['start_date']
                )
            elif query_params['query_level'] == 'org':
                # 组织级基线 - 需要实现
                return realtime_baseline_engine.generate_org_baseline_realtime(
                    query_params['identifier'],
                    query_params['start_date']
                )
            elif query_params['query_level'] == 'customer':
                # 租户级基线 - 需要实现
                return realtime_baseline_engine.generate_customer_baseline_realtime(
                    query_params['identifier'],
                    query_params['start_date']
                )
            else:
                return {
                    'success': False,
                    'error': f"不支持的查询层级: {query_params['query_level']}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"基线数据获取异常: {str(e)}"
            }
    
    def _get_health_data_unified(self, query_params: Dict) -> Dict:
        """根据查询参数获取健康数据"""
        try:
            if query_params['query_level'] == 'user':
                # 用户级健康数据
                return get_all_health_data_optimized(
                    userId=query_params['identifier'],
                    startDate=query_params['start_date'],
                    endDate=query_params['end_date'],
                    latest_only=False,
                    pageSize=None
                )
            elif query_params['query_level'] == 'org':
                # 组织级健康数据 - 需要实现多用户查询
                return get_all_health_data_optimized(
                    orgId=query_params['identifier'],
                    startDate=query_params['start_date'],
                    endDate=query_params['end_date'],
                    latest_only=False,
                    pageSize=None
                )
            elif query_params['query_level'] == 'customer':
                # 租户级健康数据 - 需要实现多组织查询
                return get_all_health_data_optimized(
                    customerId=query_params['identifier'],
                    startDate=query_params['start_date'],
                    endDate=query_params['end_date'],
                    latest_only=False,
                    pageSize=None
                )
            else:
                return {
                    'success': False,
                    'error': f"不支持的查询层级: {query_params['query_level']}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"健康数据获取异常: {str(e)}"
            }

    def _calculate_feature_score_unified(self, df: pd.DataFrame, feature: str, 
                                       baseline: Dict, query_params: Dict) -> Dict:
        """统一的特征评分计算方法"""
        if feature not in df.columns:
            return None
        
        feature_data = df[feature].dropna()
        
        if len(feature_data) < 3:
            return None
        
        try:
            # 获取基线统计
            baseline_mean = baseline['mean_value']
            baseline_std = baseline['std_value']
            baseline_min = baseline['min_value']
            baseline_max = baseline['max_value']
            
            # 计算当日平均值
            daily_avg = float(feature_data.mean())
            daily_min = float(feature_data.min())
            daily_max = float(feature_data.max())
            
            # 计算Z分数
            if baseline_std > 0:
                z_score = (daily_avg - baseline_mean) / baseline_std
                z_score = max(-10, min(10, z_score))  # 限制Z分数范围
            else:
                z_score = 0
            
            # 计算基础评分 (0-100)
            base_score = max(0, min(100, 100 - abs(z_score) * 10))
            
            # 计算惩罚分数 - 基于极值偏离
            penalty = 0
            if daily_max > baseline_max * 1.2:
                penalty += min(20, (daily_max - baseline_max * 1.2) / baseline_max * 100)
            if daily_min < baseline_min * 0.8:
                penalty += min(20, (baseline_min * 0.8 - daily_min) / baseline_min * 100)
            
            # 最终评分
            final_score = max(0, base_score - penalty)
            
            score_result = {
                'feature_name': feature,
                'avg_value': round(daily_avg, 2),
                'z_score': round(z_score, 4),
                'score_value': round(final_score, 2),
                'penalty_value': round(penalty, 2),
                'weight': self.DEFAULT_WEIGHTS.get(feature, 0.01),
                'baseline_date': baseline['baseline_date'],
                'source': 'realtime'
            }
            
            return score_result
            
        except Exception as e:
            logger.warning(f"⚠️ 计算特征 {feature} 评分失败: {str(e)}")
            return None

    def _convert_to_dataframe(self, health_data: List[Dict]) -> pd.DataFrame:
        """将健康数据转换为pandas DataFrame"""
        if not health_data:
            return pd.DataFrame()
        
        # 复用基线引擎的转换逻辑
        return realtime_baseline_engine._convert_to_dataframe(health_data)
    
    def _calculate_feature_score(self, df: pd.DataFrame, feature: str, baseline: Dict, 
                               user_id: int, target_date: str) -> Dict:
        """计算单个特征的健康评分"""
        if feature not in df.columns:
            return None
        
        feature_data = df[feature].dropna()
        
        if len(feature_data) < 3:
            return None
        
        try:
            # 获取基线统计
            baseline_mean = baseline['mean_value']
            baseline_std = baseline['std_value']
            baseline_min = baseline['min_value']
            baseline_max = baseline['max_value']
            
            # 计算当日平均值
            daily_avg = float(feature_data.mean())
            daily_min = float(feature_data.min())
            daily_max = float(feature_data.max())
            
            # 计算Z分数
            if baseline_std > 0:
                z_score = (daily_avg - baseline_mean) / baseline_std
                z_score = max(-10, min(10, z_score))  # 限制Z分数范围
            else:
                z_score = 0
            
            # 计算基础评分 (0-100)
            base_score = max(0, min(100, 100 - abs(z_score) * 10))
            
            # 计算惩罚分数 - 基于极值偏离
            penalty = 0
            if daily_max > baseline_max * 1.2:
                penalty += min(20, (daily_max - baseline_max * 1.2) / baseline_max * 100)
            if daily_min < baseline_min * 0.8:
                penalty += min(20, (baseline_min * 0.8 - daily_min) / baseline_min * 100)
            
            # 最终评分
            final_score = max(0, base_score - penalty)
            
            score_result = {
                'feature_name': feature,
                'avg_value': round(daily_avg, 2),
                'z_score': round(z_score, 4),
                'score_value': round(final_score, 2),
                'penalty_value': round(penalty, 2),
                'weight': self.DEFAULT_WEIGHTS.get(feature, 0.01),
                'baseline_date': baseline['baseline_date'],
                'source': 'realtime'
            }
            
            return score_result
            
        except Exception as e:
            logger.warning(f"⚠️ 计算特征 {feature} 评分失败: {str(e)}")
            return None
    
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
    
    def _calculate_score_quality(self, feature_scores: Dict) -> Dict:
        """计算评分质量指标"""
        if not feature_scores:
            return {'overall_quality': 0, 'completeness': 0, 'reliability': 0}
        
        total_features = len(self.HEALTH_FEATURES)
        scored_features = len(feature_scores)
        completeness = scored_features / total_features
        
        # 计算可靠性（基于样本数量）
        sample_counts = [score.get('data_quality', {}).get('sample_count', 0) 
                        for score in feature_scores.values()]
        avg_sample_count = np.mean(sample_counts) if sample_counts else 0
        reliability = min(1.0, avg_sample_count / 20)  # 20个样本为满分
        
        overall_quality = (completeness * 0.6 + reliability * 0.4)
        
        return {
            'overall_quality': round(overall_quality, 3),
            'completeness': round(completeness, 3),
            'reliability': round(reliability, 3),
            'scored_features': scored_features,
            'total_features': total_features
        }
    
    def calculate_comprehensive_health_score(self, user_id: int, customer_id: int, days: int = 7) -> Dict:
        """
        计算综合健康评分 - API兼容方法
        
        Args:
            user_id: 用户ID
            customer_id: 租户ID (用于兼容，暂时忽略)
            days: 计算天数 (用于兼容，暂时忽略)
            
        Returns:
            Dict: 包含健康评分和详细信息
        """
        try:
            # 使用现有的实时计算方法
            result = self.calculate_user_health_score_realtime(user_id)
            
            if result.get('success'):
                # 重新格式化返回结果以符合API期望
                data = result.get('data', {})
                return {
                    'overall_score': data.get('overall_score', 0),
                    'health_level': data.get('health_level', 'unknown'),
                    'feature_scores': data.get('feature_scores', {}),
                    'quality': data.get('quality', {}),
                    'last_update': data.get('last_update', datetime.now().isoformat()),
                    'user_id': user_id,
                    'customer_id': customer_id,
                    'days': days
                }
            else:
                logger.warning(f"用户 {user_id} 健康评分计算失败: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"综合健康评分计算异常: {e}")
            return None
    
    def calculate_comprehensive_score(self, user_id: int, device_sn: str = None, 
                                     include_prediction: bool = True, 
                                     include_factors: bool = True) -> Dict:
        """
        计算综合健康评分 - POST API兼容方法
        
        Args:
            user_id: 用户ID
            device_sn: 设备序列号 (用于兼容，暂时忽略)
            include_prediction: 是否包含预测 (用于兼容，暂时忽略)
            include_factors: 是否包含因子分析 (用于兼容，暂时忽略)
            
        Returns:
            Dict: 包含健康评分和详细信息
        """
        try:
            # 使用现有的实时计算方法
            result = self.calculate_user_health_score_realtime(user_id)
            
            if result.get('success'):
                # 重新格式化返回结果以符合API期望
                data = result.get('data', {})
                return {
                    'overall_score': data.get('overall_score', 0),
                    'health_level': data.get('health_level', 'unknown'),
                    'feature_scores': data.get('feature_scores', {}),
                    'quality': data.get('quality', {}),
                    'last_update': data.get('last_update', datetime.now().isoformat()),
                    'user_id': user_id,
                    'device_sn': device_sn,
                    'prediction_included': include_prediction,
                    'factors_included': include_factors,
                    # 添加预测和因子分析的占位符
                    'predictions': [] if include_prediction else None,
                    'health_factors': {} if include_factors else None
                }
            else:
                logger.warning(f"用户 {user_id} 健康评分计算失败: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"综合健康评分计算异常: {e}")
            return None


# 全局实例
realtime_score_engine = RealTimeHealthScoreEngine()


def get_health_score_unified(**kwargs) -> Dict:
    """统一的健康评分获取接口 - 对外接口"""
    return realtime_score_engine.calculate_health_score_unified(**kwargs)


def get_user_health_score_realtime(user_id: int, target_date: str = None) -> Dict:
    """获取用户实时健康评分 - 兼容接口"""
    return get_health_score_unified(user_id=user_id, startDate=target_date, endDate=target_date)


def get_org_health_score_realtime(org_id: int, target_date: str = None) -> Dict:
    """获取组织实时健康评分 - 新接口"""
    return get_health_score_unified(org_id=org_id, startDate=target_date, endDate=target_date)


def get_customer_health_score_realtime(customer_id: int, target_date: str = None) -> Dict:
    """获取租户实时健康评分 - 新接口"""
    return get_health_score_unified(customer_id=customer_id, startDate=target_date, endDate=target_date)


def get_health_score_status(identifier: int, identifier_type: str = 'user', target_date: str = None) -> Dict:
    """获取评分状态 - 对外接口"""
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 构建查询参数
    kwargs = {f"{identifier_type}_id": identifier, "startDate": target_date, "endDate": target_date}
    query_params = health_query_base.parse_query_params(**kwargs)
    
    cache_key = health_query_base.build_cache_key('score', query_params)
    cached_result = realtime_score_engine.redis.get_data(cache_key)
    
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
            'message': '未找到缓存的评分数据',
            'identifier': identifier,
            'identifier_type': identifier_type,
            'target_date': target_date
        }