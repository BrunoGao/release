"""
实时健康评分计算引擎
基于实时基线数据计算健康评分，支持用户和组织级别的评分

依赖统一的get_all_health_data_optimized查询方法和health_baseline_engine
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .redis_helper import RedisHelper
from .user_health_data import get_all_health_data_optimized
from .health_baseline_engine import realtime_baseline_engine
from .models import db, HealthScore
from sqlalchemy import and_
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
    
    def calculate_user_health_score_realtime(self, user_id: int, target_date: str = None) -> Dict:
        """
        计算用户健康评分，优先从数据库查询，空值时实时计算
        
        Args:
            user_id: 用户ID
            target_date: 目标日期，默认为昨天
            
        Returns:
            Dict: 包含健康评分和详细信息
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始获取用户 {user_id} 的健康评分，目标日期: {target_date}")
        
        try:
            # 步骤1: 优先从数据库查询已生成的评分
            db_result = self._query_database_scores(user_id, target_date)
            if db_result['success'] and db_result['data']:
                logger.info(f"✅ 用户 {user_id} 从数据库获取评分成功，特征数量: {len(db_result['data'].get('feature_scores', {}))}")
                return db_result
            
            # 步骤2: 数据库无数据，执行实时计算
            logger.info(f"📊 用户 {user_id} 数据库无评分数据，开始实时计算...")
            return self._calculate_scores_realtime(user_id, target_date, start_time)
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 评分获取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _query_database_scores(self, user_id: int, target_date: str) -> Dict:
        """从数据库查询已生成的健康评分"""
        try:
            # 查询健康评分记录
            score_records = db.session.query(HealthScore).filter(
                and_(
                    HealthScore.user_id == user_id,
                    HealthScore.score_date == target_date
                )
            ).all()
            
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
                    'baseline_date': record.baseline_time.strftime('%Y-%m-%d') if record.baseline_time else target_date,
                    'source': 'database'
                }
                
                total_weighted_score += score_value * weight
                total_weight += weight
            
            # 计算综合评分
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            health_level = self._determine_health_level(overall_score)
            
            # 生成汇总信息
            summary = {
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'database',
                'overall_score': round(overall_score, 2),
                'health_level': health_level,
                'features_evaluated': len(feature_scores),
                'total_weight': round(total_weight, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 从数据库获取用户 {user_id} 评分: {len(feature_scores)} 个特征，综合评分: {overall_score:.2f}")
            
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
    
    def _calculate_scores_realtime(self, user_id: int, target_date: str, start_time: float) -> Dict:
        """实时计算健康评分（原有逻辑）"""
        logger.info(f"🔄 开始实时计算用户 {user_id} 健康评分，日期: {target_date}")
        
        try:
            # 1. 首先获取或生成用户基线
            baseline_result = realtime_baseline_engine.generate_user_baseline_realtime(user_id, target_date)
            
            if not baseline_result.get('success'):
                logger.warning(f"⚠️ 用户 {user_id} 基线获取失败: {baseline_result.get('error')}")
                return {
                    'success': False,
                    'error': f"基线数据获取失败: {baseline_result.get('error')}",
                    'user_id': user_id,
                    'target_date': target_date
                }
            
            user_baselines = baseline_result['data']['baselines']
            
            # 2. 获取当日健康数据
            health_result = get_all_health_data_optimized(
                userId=user_id,
                startDate=target_date,
                endDate=target_date,
                latest_only=False,
                pageSize=None
            )
            
            if not health_result.get('success'):
                return {
                    'success': False,
                    'error': health_result.get('message'),
                    'user_id': user_id,
                    'target_date': target_date
                }
            
            health_data = health_result.get('data', {}).get('healthData', [])
            
            if not health_data:
                return {
                    'success': False,
                    'error': '当日无健康数据',
                    'user_id': user_id,
                    'target_date': target_date
                }
            
            # 3. 转换数据格式
            df = self._convert_to_dataframe(health_data)
            
            # 4. 计算每个特征的评分
            feature_scores = {}
            total_weighted_score = 0
            total_weights = 0
            
            for feature in self.HEALTH_FEATURES:
                if feature in user_baselines and feature in df.columns:
                    score_result = self._calculate_feature_score(
                        df, feature, user_baselines[feature], user_id, target_date)
                    
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
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'realtime',
                'overall_score': overall_score,
                'health_level': health_level,
                'features_evaluated': len(feature_scores),
                'total_weight': round(total_weights, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            # 7. 缓存结果
            cache_key = f"realtime_score:user:{user_id}:{target_date}"
            cache_data = {
                'feature_scores': feature_scores,
                'summary': summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 3600)
            
            logger.info(f"✅ 用户 {user_id} 健康评分计算完成: 总分 {overall_score}，等级 {health_level}")
            
            return {
                'success': True,
                'data': {
                    'feature_scores': feature_scores,
                    'summary': summary
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 健康评分计算失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
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


# 全局实例
realtime_score_engine = RealTimeHealthScoreEngine()


def get_user_health_score_realtime(user_id: int, target_date: str = None) -> Dict:
    """获取用户实时健康评分 - 对外接口"""
    return realtime_score_engine.calculate_user_health_score_realtime(user_id, target_date)


def get_health_score_status(identifier: int, identifier_type: str = 'user', target_date: str = None) -> Dict:
    """获取评分状态 - 对外接口"""
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    cache_key = f"realtime_score:{identifier_type}:{identifier}:{target_date}"
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