"""
实时健康基线生成引擎
作为ljwx-boot定时任务的备份方案，在bigscreen中实现实时生成逻辑

依赖统一的get_all_health_data_optimized查询方法
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .redis_helper import RedisHelper
from .user_health_data import get_all_health_data_optimized
from .models import db, HealthBaseline
from sqlalchemy import text, and_
import json
import time

logger = logging.getLogger(__name__)

class RealTimeHealthBaselineEngine:
    """实时健康基线生成引擎"""
    
    def __init__(self):
        self.redis = RedisHelper()
        
        # 健康特征配置 - 与ljwx-boot保持一致
        self.HEALTH_FEATURES = [
            "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
            "pressure_low", "stress", "step", "calorie", "distance", "sleep"
        ]
        
        # 特征值范围配置 - 与ljwx-boot保持一致
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
        
        # 最小标准差配置 - 避免除零错误
        self.MIN_STD_VALUES = {
            "heart_rate": 1.0,
            "blood_oxygen": 0.5,
            "temperature": 0.1,
            "pressure_high": 2.0,
            "pressure_low": 1.5,
            "stress": 1.0,
            "step": 100.0,
            "calorie": 50.0,
            "distance": 0.5,
            "sleep": 0.2
        }
    
    def generate_user_baseline_realtime(self, user_id: int, target_date: str = None, days_back: int = 30) -> Dict:
        """
        生成单个用户的健康基线，优先从数据库查询，空值时实时生成
        
        Args:
            user_id: 用户ID
            target_date: 目标日期，默认为昨天
            days_back: 向前计算天数，默认30天
            
        Returns:
            Dict: 包含基线数据和统计信息
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始获取用户 {user_id} 的健康基线，目标日期: {target_date}")
        
        try:
            # 步骤1: 优先从数据库查询已生成的基线
            db_result = self._query_database_baseline(user_id, target_date)
            if db_result['success'] and db_result['data']:
                logger.info(f"✅ 用户 {user_id} 从数据库获取基线成功，特征数量: {len(db_result['data'].get('baselines', {}))}")
                return db_result
            
            # 步骤2: 数据库无数据，执行实时生成
            logger.info(f"📊 用户 {user_id} 数据库无基线数据，开始实时生成...")
            return self._generate_baseline_realtime(user_id, target_date, days_back, start_time)
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 基线获取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }
    
    def _query_database_baseline(self, user_id: int, target_date: str) -> Dict:
        """从数据库查询已生成的健康基线"""
        try:
            # 查询当前有效的基线记录 - 使用新表结构
            baseline_records = db.session.query(HealthBaseline).filter(
                and_(
                    HealthBaseline.user_id == user_id,
                    HealthBaseline.baseline_date == target_date,
                    HealthBaseline.is_current == 1,
                    HealthBaseline.baseline_type == 'personal',
                    HealthBaseline.is_deleted == 0
                )
            ).all()
            
            if not baseline_records:
                return {'success': True, 'data': None, 'source': 'database_empty'}
            
            # 转换为标准格式
            baseline_results = {}
            for record in baseline_records:
                feature_name = record.feature_name
                baseline_results[feature_name] = {
                    'identifier': user_id,
                    'feature_name': feature_name,
                    'baseline_date': target_date,
                    'mean_value': float(record.mean_value) if record.mean_value else 0.0,
                    'std_value': float(record.std_value) if record.std_value else 0.1,
                    'min_value': float(record.min_value) if record.min_value else 0.0,
                    'max_value': float(record.max_value) if record.max_value else 0.0,
                    'sample_count': record.sample_count or 0,
                    'quality_score': round((record.confidence_level or 0.95), 3),
                    'is_current': bool(record.is_current),
                    'generated_at': record.baseline_time.isoformat() if record.baseline_time else datetime.now().isoformat(),
                    'source': 'database'
                }
            
            # 生成汇总信息
            summary = {
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'database',
                'features_processed': len(baseline_results),
                'baseline_quality_score': self._calculate_baseline_quality(baseline_results),
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 从数据库获取用户 {user_id} 基线: {len(baseline_results)} 个特征")
            
            return {
                'success': True,
                'data': {
                    'baselines': baseline_results,
                    'summary': summary
                },
                'source': 'database'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ 数据库基线查询失败: {str(e)}")
            return {'success': False, 'error': str(e), 'source': 'database_error'}
    
    def _generate_baseline_realtime(self, user_id: int, target_date: str, days_back: int, start_time: float) -> Dict:
        """实时生成健康基线（原有逻辑）"""
        # 计算查询时间范围
        end_date = datetime.strptime(target_date, '%Y-%m-%d')
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始实时生成用户 {user_id} 健康基线，数据范围: {start_date_str} - {target_date}")
        
        try:
            # 使用统一的health data查询接口
            health_result = get_all_health_data_optimized(
                userId=user_id,
                startDate=start_date_str,
                endDate=target_date,
                latest_only=False,
                pageSize=None  # 获取所有数据，不分页
            )
            
            if not health_result.get('success'):
                logger.warning(f"⚠️ 用户 {user_id} 获取健康数据失败: {health_result.get('message')}")
                return {
                    'success': False,
                    'error': health_result.get('message'),
                    'user_id': user_id,
                    'target_date': target_date
                }
            
            health_data = health_result.get('data', {}).get('healthData', [])
            total_records = len(health_data)
            
            if total_records < 5:
                logger.warning(f"⚠️ 用户 {user_id} 数据不足，需要至少5条记录，实际: {total_records}")
                return {
                    'success': False,
                    'error': f'数据不足，需要至少5条记录，实际: {total_records}',
                    'user_id': user_id,
                    'target_date': target_date,
                    'data_count': total_records
                }
            
            # 转换为DataFrame进行分析
            df = self._convert_to_dataframe(health_data)
            
            # 为每个健康特征生成基线
            baseline_results = {}
            for feature in self.HEALTH_FEATURES:
                baseline = self._calculate_feature_baseline(df, feature, user_id, target_date)
                if baseline:
                    baseline_results[feature] = baseline
                    # 标记为实时生成
                    baseline_results[feature]['source'] = 'realtime'
            
            # 生成汇总统计
            summary = {
                'user_id': user_id,
                'target_date': target_date,
                'data_source': 'realtime',
                'data_period': f"{start_date_str} to {target_date}",
                'total_records': total_records,
                'features_processed': len(baseline_results),
                'baseline_quality_score': self._calculate_baseline_quality(baseline_results),
                'generation_time': round(time.time() - start_time, 3),
                'generated_at': datetime.now().isoformat()
            }
            
            # 缓存结果
            cache_key = f"realtime_baseline:user:{user_id}:{target_date}"
            cache_data = {
                'baselines': baseline_results,
                'summary': summary
            }
            self.redis.set_data(cache_key, json.dumps(cache_data, default=str), 3600)  # 缓存1小时
            
            logger.info(f"✅ 用户 {user_id} 实时基线生成完成: {len(baseline_results)} 个特征，质量评分: {summary['baseline_quality_score']:.2f}")
            
            return {
                'success': True,
                'data': {
                    'baselines': baseline_results,
                    'summary': summary
                },
                'source': 'realtime'
            }
            
        except Exception as e:
            logger.error(f"❌ 用户 {user_id} 实时基线生成失败: {str(e)}")
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
        
        # 标准化字段映射
        records = []
        for record in health_data:
            clean_record = {}
            
            # 基础字段
            clean_record['user_id'] = record.get('user_id') or record.get('userId')
            clean_record['device_sn'] = record.get('device_sn') or record.get('deviceSn')
            clean_record['timestamp'] = record.get('timestamp') or record.get('create_time')
            clean_record['dept_name'] = record.get('dept_name') or record.get('deptName')
            clean_record['dept_id'] = record.get('dept_id') or record.get('deptId')
            
            # 健康特征字段
            for feature in self.HEALTH_FEATURES:
                value = record.get(feature)
                
                # 处理特殊映射
                if feature == 'heart_rate' and value is None:
                    value = record.get('heartRate') or record.get('heart_rate')
                elif feature == 'blood_oxygen' and value is None:
                    value = record.get('bloodOxygen') or record.get('blood_oxygen')
                elif feature == 'pressure_high' and value is None:
                    value = record.get('pressureHigh') or record.get('pressure_high')
                elif feature == 'pressure_low' and value is None:
                    value = record.get('pressureLow') or record.get('pressure_low')
                
                # 数据验证和清理
                if value is not None:
                    try:
                        value = float(value)
                        min_val, max_val = self.FEATURE_RANGES.get(feature, (0, 10000))
                        if min_val <= value <= max_val:
                            clean_record[feature] = value
                        else:
                            clean_record[feature] = None
                    except (ValueError, TypeError):
                        clean_record[feature] = None
                else:
                    clean_record[feature] = None
            
            records.append(clean_record)
        
        df = pd.DataFrame(records)
        
        # 转换时间戳
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        return df
    
    def _calculate_feature_baseline(self, df: pd.DataFrame, feature: str, identifier: int, target_date: str) -> Dict:
        """计算单个特征的基线统计"""
        if feature not in df.columns:
            return None
        
        feature_data = df[feature].dropna()
        
        if len(feature_data) < 3:
            return None
        
        try:
            # 基础统计
            mean_val = float(feature_data.mean())
            std_val = max(float(feature_data.std()), self.MIN_STD_VALUES.get(feature, 0.1))
            min_val = float(feature_data.min())
            max_val = float(feature_data.max())
            count = int(len(feature_data))
            
            # 数据质量指标
            outlier_threshold = 3 * std_val
            outliers = len(feature_data[(feature_data < mean_val - outlier_threshold) | 
                                      (feature_data > mean_val + outlier_threshold)])
            quality_score = max(0, 1 - (outliers / count)) if count > 0 else 0
            
            baseline = {
                'identifier': identifier,
                'feature_name': feature,
                'baseline_date': target_date,
                'mean_value': round(mean_val, 2),
                'std_value': round(std_val, 2),
                'min_value': round(min_val, 2),
                'max_value': round(max_val, 2),
                'sample_count': count,
                'quality_score': round(quality_score, 3),
                'outlier_count': outliers,
                'is_current': True,
                'generated_at': datetime.now().isoformat()
            }
            
            return baseline
            
        except Exception as e:
            logger.warning(f"⚠️ 计算特征 {feature} 基线失败: {str(e)}")
            return None
    
    def _calculate_baseline_quality(self, baselines: Dict) -> float:
        """计算基线质量评分"""
        if not baselines:
            return 0.0
        
        total_score = 0
        for baseline in baselines.values():
            # 基于样本数量和数据分布的质量评分
            sample_count = baseline.get('sample_count', 0)
            std_value = baseline.get('std_value', 0)
            mean_value = baseline.get('mean_value', 0)
            
            # 样本数量评分 (0-0.4)
            sample_score = min(0.4, sample_count / 100)
            
            # 数据分布评分 (0-0.4)
            cv = std_value / mean_value if mean_value > 0 else 1
            distribution_score = max(0, 0.4 - cv * 0.1)
            
            # 完整性评分 (0-0.2)
            completeness_score = 0.2 if all(k in baseline for k in ['mean_value', 'std_value', 'sample_count']) else 0
            
            total_score += sample_score + distribution_score + completeness_score
        
        return round(total_score / len(baselines), 3) if baselines else 0.0

    def generate_org_baseline_realtime(self, org_id: int, target_date: str = None, days_back: int = 30) -> Dict:
        """
        生成组织级基线数据 - 直接从t_health_baseline表查询组织级基线
        
        Args:
            org_id: 组织ID
            target_date: 目标日期，默认为昨天
            days_back: 回溯天数，默认30天
            
        Returns:
            Dict: 组织基线数据
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始生成组织 {org_id} 的健康基线，目标日期: {target_date}")
        
        try:
            # 1. 首先尝试从t_health_baseline表中查询组织级基线数据
            org_baseline_records = db.session.query(HealthBaseline).filter(
                and_(
                    HealthBaseline.org_id == str(org_id),
                    HealthBaseline.baseline_date == target_date,
                    HealthBaseline.baseline_type == 'org',
                    HealthBaseline.is_current == 1,
                    HealthBaseline.is_deleted == 0
                )
            ).all()
            
            if org_baseline_records:
                # 转换为标准格式
                org_baselines = {}
                for record in org_baseline_records:
                    feature_name = record.feature_name
                    org_baselines[feature_name] = {
                        'identifier': org_id,
                        'feature_name': feature_name,
                        'baseline_date': target_date,
                        'mean_value': float(record.mean_value) if record.mean_value else 0.0,
                        'std_value': float(record.std_value) if record.std_value else 0.1,
                        'min_value': float(record.min_value) if record.min_value else 0.0,
                        'max_value': float(record.max_value) if record.max_value else 0.0,
                        'sample_count': record.sample_count or 0,
                        'quality_score': round((record.confidence_level or 0.95), 3),
                        'is_current': bool(record.is_current),
                        'baseline_type': 'org',
                        'generated_at': record.baseline_time.isoformat() if record.baseline_time else datetime.now().isoformat(),
                        'source': 'database_org'
                    }
                
                # 生成汇总信息
                summary = {
                    'org_id': org_id,
                    'target_date': target_date,
                    'data_source': 'database_org',
                    'features_processed': len(org_baselines),
                    'baseline_quality_score': self._calculate_baseline_quality(org_baselines),
                    'generated_at': datetime.now().isoformat(),
                    'execution_time': round(time.time() - start_time, 3)
                }
                
                logger.info(f"✅ 从数据库获取组织 {org_id} 基线: {len(org_baselines)} 个特征")
                
                return {
                    'success': True,
                    'data': {
                        'baselines': org_baselines,
                        'summary': summary,
                        'user_count': 0  # 组织级基线不直接统计用户数
                    },
                    'source': 'database_org'
                }
            
            # 2. 如果没有找到组织级基线，尝试汇总用户基线
            from .org import getUserIdsByOrgId
            user_ids = getUserIdsByOrgId(org_id)
            
            if not user_ids:
                return {
                    'success': False,
                    'error': f'组织 {org_id} 下没有找到用户',
                    'org_id': org_id,
                    'target_date': target_date
                }
            
            # 3. 获取所有用户的基线数据进行汇总
            user_baselines = {}
            valid_users = 0
            
            for user_id in user_ids:
                try:
                    user_baseline_result = self.generate_user_baseline_realtime(user_id, target_date, days_back)
                    if user_baseline_result.get('success') and user_baseline_result.get('data'):
                        user_baselines[user_id] = user_baseline_result['data']['baselines']
                        valid_users += 1
                except Exception as e:
                    logger.warning(f"⚠️ 用户 {user_id} 基线生成失败: {str(e)}")
                    continue
            
            if not user_baselines:
                return {
                    'success': False,
                    'error': f'组织 {org_id} 下没有用户生成有效的基线数据',
                    'org_id': org_id,
                    'target_date': target_date,
                    'total_users': len(user_ids),
                    'valid_users': 0
                }
            
            # 4. 汇总组织级基线
            org_baselines = self._aggregate_baselines(user_baselines, 'org')
            
            # 5. 计算质量评分
            quality_score = self._calculate_baseline_quality(org_baselines)
            
            # 6. 生成汇总信息
            summary = {
                'org_id': org_id,
                'target_date': target_date,
                'days_back': days_back,
                'data_source': 'realtime_aggregation',
                'total_users': len(user_ids),
                'valid_users': valid_users,
                'aggregated_features': len(org_baselines),
                'quality_score': quality_score,
                'generated_at': datetime.now().isoformat(),
                'execution_time': round(time.time() - start_time, 3)
            }
            
            logger.info(f"✅ 组织 {org_id} 基线生成完成: {valid_users}/{len(user_ids)} 用户，{len(org_baselines)} 个特征")
            
            return {
                'success': True,
                'data': {
                    'baselines': org_baselines,
                    'summary': summary,
                    'user_count': valid_users
                },
                'source': 'realtime_aggregation'
            }
            
        except Exception as e:
            logger.error(f"❌ 组织 {org_id} 基线生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'org_id': org_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }

    def generate_customer_baseline_realtime(self, customer_id: int, target_date: str = None, days_back: int = 30) -> Dict:
        """
        生成租户级基线数据 - 汇总租户下所有组织的基线
        
        Args:
            customer_id: 租户ID
            target_date: 目标日期，默认为昨天
            days_back: 回溯天数，默认30天
            
        Returns:
            Dict: 租户基线数据
        """
        start_time = time.time()
        
        if target_date is None:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 开始生成租户 {customer_id} 的健康基线，目标日期: {target_date}")
        
        try:
            # 1. 获取租户下的所有组织ID
            from .org import findAllDescendants
            org_ids = findAllDescendants(customer_id)
            
            if not org_ids:
                return {
                    'success': False,
                    'error': f'租户 {customer_id} 下没有找到组织',
                    'customer_id': customer_id,
                    'target_date': target_date
                }
            
            # 2. 获取所有组织的基线数据
            org_baselines = {}
            valid_orgs = 0
            total_users = 0
            
            for org_id in org_ids:
                try:
                    org_baseline_result = self.generate_org_baseline_realtime(org_id, target_date, days_back)
                    if org_baseline_result.get('success') and org_baseline_result.get('data'):
                        org_baselines[org_id] = org_baseline_result['data']['baselines']
                        valid_orgs += 1
                        total_users += org_baseline_result['data'].get('user_count', 0)
                except Exception as e:
                    logger.warning(f"⚠️ 组织 {org_id} 基线生成失败: {str(e)}")
                    continue
            
            if not org_baselines:
                return {
                    'success': False,
                    'error': f'租户 {customer_id} 下没有组织生成有效的基线数据',
                    'customer_id': customer_id,
                    'target_date': target_date,
                    'total_orgs': len(org_ids),
                    'valid_orgs': 0
                }
            
            # 3. 汇总租户级基线
            customer_baselines = self._aggregate_baselines(org_baselines, 'customer')
            
            # 4. 计算质量评分
            quality_score = self._calculate_baseline_quality(customer_baselines)
            
            # 5. 生成汇总信息
            summary = {
                'customer_id': customer_id,
                'target_date': target_date,
                'days_back': days_back,
                'data_source': 'realtime_aggregation',
                'total_orgs': len(org_ids),
                'valid_orgs': valid_orgs,
                'total_users': total_users,
                'aggregated_features': len(customer_baselines),
                'quality_score': quality_score,
                'generated_at': datetime.now().isoformat(),
                'execution_time': round(time.time() - start_time, 3)
            }
            
            logger.info(f"✅ 租户 {customer_id} 基线生成完成: {valid_orgs}/{len(org_ids)} 组织，{total_users} 用户，{len(customer_baselines)} 个特征")
            
            return {
                'success': True,
                'data': {
                    'baselines': customer_baselines,
                    'summary': summary,
                    'org_count': valid_orgs,
                    'user_count': total_users
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 租户 {customer_id} 基线生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'customer_id': customer_id,
                'target_date': target_date,
                'execution_time': round(time.time() - start_time, 3)
            }

    def _aggregate_baselines(self, baselines_dict: Dict, level: str) -> Dict:
        """
        汇总基线数据
        
        Args:
            baselines_dict: {entity_id: {feature: baseline_data}} 格式的基线数据
            level: 汇总级别 ('org' 或 'customer')
            
        Returns:
            Dict: 汇总后的基线数据
        """
        if not baselines_dict:
            return {}
        
        # 收集所有特征的数据
        feature_data = {}
        
        for entity_id, entity_baselines in baselines_dict.items():
            for feature, baseline_data in entity_baselines.items():
                if feature not in feature_data:
                    feature_data[feature] = {
                        'mean_values': [],
                        'std_values': [],
                        'min_values': [],
                        'max_values': [],
                        'sample_counts': []
                    }
                
                feature_data[feature]['mean_values'].append(baseline_data.get('mean_value', 0))
                feature_data[feature]['std_values'].append(baseline_data.get('std_value', 0))
                feature_data[feature]['min_values'].append(baseline_data.get('min_value', 0))
                feature_data[feature]['max_values'].append(baseline_data.get('max_value', 0))
                feature_data[feature]['sample_counts'].append(baseline_data.get('sample_count', 0))
        
        # 计算汇总基线
        aggregated_baselines = {}
        
        for feature, data in feature_data.items():
            try:
                # 使用加权平均（基于样本数量）
                total_samples = sum(data['sample_counts'])
                if total_samples == 0:
                    continue
                
                weights = [count / total_samples for count in data['sample_counts']]
                
                aggregated_mean = sum(mean * weight for mean, weight in zip(data['mean_values'], weights))
                aggregated_std = np.sqrt(sum((std ** 2) * weight for std, weight in zip(data['std_values'], weights)))
                aggregated_min = min(data['min_values'])
                aggregated_max = max(data['max_values'])
                
                aggregated_baselines[feature] = {
                    'feature_name': feature,
                    'mean_value': round(float(aggregated_mean), 4),
                    'std_value': max(round(float(aggregated_std), 4), self.MIN_STD_VALUES.get(feature, 0.1)),
                    'min_value': round(float(aggregated_min), 4),
                    'max_value': round(float(aggregated_max), 4),
                    'sample_count': total_samples,
                    'entity_count': len(data['sample_counts']),
                    'aggregation_level': level,
                    'baseline_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'source': f'realtime_{level}_aggregation'
                }
                
            except Exception as e:
                logger.warning(f"⚠️ 特征 {feature} 汇总失败: {str(e)}")
                continue
        
        return aggregated_baselines


# 全局实例
realtime_baseline_engine = RealTimeHealthBaselineEngine()


def get_user_baseline_realtime(user_id: int, target_date: str = None) -> Dict:
    """获取用户实时基线 - 对外接口"""
    return realtime_baseline_engine.generate_user_baseline_realtime(user_id, target_date)


def get_baseline_status(identifier: int, identifier_type: str = 'user', target_date: str = None) -> Dict:
    """获取基线状态 - 对外接口"""
    return realtime_baseline_engine.get_baseline_status(identifier, identifier_type, target_date)


# 新增组织和租户级基线生成方法
def get_org_baseline_realtime(org_id: int, target_date: str = None) -> Dict:
    """获取组织实时基线 - 对外接口"""
    return realtime_baseline_engine.generate_org_baseline_realtime(org_id, target_date)


def get_customer_baseline_realtime(customer_id: int, target_date: str = None) -> Dict:
    """获取租户实时基线 - 对外接口"""
    return realtime_baseline_engine.generate_customer_baseline_realtime(customer_id, target_date)