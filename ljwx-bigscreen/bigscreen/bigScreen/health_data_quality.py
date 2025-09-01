#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康数据质量控制机制
Health Data Quality Control System

实现全面的数据质量控制，包括数据验证、清洗、标准化和质量评估
- 实时数据验证：在数据入库前进行格式和范围验证
- 数据质量评分：基于完整性、准确性、一致性评估数据质量
- 异常检测：识别和标记异常数据
- 数据清洗：自动修复常见数据问题
- 质量报告：生成数据质量分析报告

Author: System
Date: 2025-09-01
Version: 1.0
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re
from statistics import mean, median, stdev
from sqlalchemy import text, func
import asyncio

from .models import db, UserHealthData, HealthBaseline, AlertInfo, Position

logger = logging.getLogger(__name__)

class DataQualityLevel(Enum):
    """数据质量等级"""
    EXCELLENT = "excellent"  # 优秀 (90-100分)
    GOOD = "good"           # 良好 (80-89分)
    FAIR = "fair"           # 一般 (70-79分)
    POOR = "poor"           # 较差 (60-69分)
    CRITICAL = "critical"   # 严重 (0-59分)

@dataclass
class HealthDataValidationRule:
    """健康数据验证规则"""
    field_name: str
    data_type: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    required: bool = False
    pattern: Optional[str] = None
    custom_validator: Optional[callable] = None

@dataclass
class DataQualityResult:
    """数据质量检查结果"""
    is_valid: bool
    quality_score: float
    quality_level: DataQualityLevel
    issues: List[str]
    warnings: List[str]
    cleaned_data: Optional[Dict] = None
    metadata: Optional[Dict] = None

class HealthDataQualityController:
    """健康数据质量控制器"""
    
    def __init__(self):
        """初始化质量控制器"""
        self._init_validation_rules()
        self._init_quality_thresholds()
        self._init_cleaning_rules()
        
        # 质量统计
        self.quality_stats = {
            'total_validated': 0,
            'total_passed': 0,
            'total_failed': 0,
            'total_cleaned': 0,
            'quality_scores': []
        }

    def _init_validation_rules(self):
        """初始化验证规则"""
        self.validation_rules = {
            # 基础生理指标验证规则
            'heart_rate': HealthDataValidationRule(
                field_name='heart_rate',
                data_type='float',
                min_value=30.0,
                max_value=220.0,
                required=False
            ),
            'blood_pressure_systolic': HealthDataValidationRule(
                field_name='blood_pressure_systolic',
                data_type='float',
                min_value=70.0,
                max_value=250.0,
                required=False
            ),
            'blood_pressure_diastolic': HealthDataValidationRule(
                field_name='blood_pressure_diastolic',
                data_type='float',
                min_value=40.0,
                max_value=150.0,
                required=False
            ),
            'spo2': HealthDataValidationRule(
                field_name='spo2',
                data_type='float',
                min_value=70.0,
                max_value=100.0,
                required=False
            ),
            'temperature': HealthDataValidationRule(
                field_name='temperature',
                data_type='float',
                min_value=30.0,
                max_value=45.0,
                required=False
            ),
            'step_count': HealthDataValidationRule(
                field_name='step_count',
                data_type='int',
                min_value=0,
                max_value=100000,
                required=False
            ),
            'user_id': HealthDataValidationRule(
                field_name='user_id',
                data_type='int',
                required=True
            ),
            'customer_id': HealthDataValidationRule(
                field_name='customer_id',
                data_type='int',
                required=True
            ),
            'device_sn': HealthDataValidationRule(
                field_name='device_sn',
                data_type='str',
                pattern=r'^[A-Za-z0-9-_]{6,32}$',
                required=False
            )
        }

    def _init_quality_thresholds(self):
        """初始化质量阈值"""
        self.quality_thresholds = {
            'completeness_weight': 0.3,    # 完整性权重
            'accuracy_weight': 0.4,        # 准确性权重
            'consistency_weight': 0.2,     # 一致性权重
            'timeliness_weight': 0.1,      # 时效性权重
            
            # 各维度阈值
            'completeness_threshold': 0.8,  # 完整性最低要求
            'accuracy_threshold': 0.9,      # 准确性最低要求
            'consistency_threshold': 0.85,  # 一致性最低要求
            'timeliness_threshold': 0.95,   # 时效性最低要求
            
            # 异常检测阈值
            'outlier_std_multiplier': 3.0,  # 3倍标准差为异常
            'duplicate_time_window': 300,   # 5分钟内重复数据检测
        }

    def _init_cleaning_rules(self):
        """初始化数据清洗规则"""
        self.cleaning_rules = {
            # 心率数据清洗
            'heart_rate': {
                'outlier_replacement': 'median',  # 异常值用中位数替代
                'smooth_window': 5,               # 5点平滑窗口
                'interpolation_method': 'linear'   # 缺失值线性插值
            },
            # 血压数据清洗
            'blood_pressure': {
                'systolic_diastolic_ratio_check': True,  # 收缩压/舒张压比例检查
                'min_ratio': 1.2,                        # 最小比例
                'max_ratio': 3.0,                        # 最大比例
                'correlation_check': True                 # 收缩压舒张压相关性检查
            },
            # 血氧数据清洗
            'spo2': {
                'outlier_replacement': 'previous_valid',  # 异常值用前一个有效值替代
                'trend_check': True,                      # 趋势一致性检查
                'sudden_drop_threshold': 10               # 突降阈值(%)
            },
            # 步数数据清洗
            'step_count': {
                'daily_max_limit': 50000,       # 日最大步数限制
                'increment_check': True,        # 递增性检查
                'reset_detection': True         # 重置检测（跨天/设备重启）
            }
        }

    async def validate_health_data(self, data: Dict[str, Any]) -> DataQualityResult:
        """验证健康数据质量"""
        try:
            issues = []
            warnings = []
            quality_scores = {}
            
            # 1. 基础字段验证
            field_validation_result = self._validate_fields(data)
            issues.extend(field_validation_result['issues'])
            warnings.extend(field_validation_result['warnings'])
            quality_scores['field_validation'] = field_validation_result['score']
            
            # 2. 数据完整性检查
            completeness_result = self._check_data_completeness(data)
            quality_scores['completeness'] = completeness_result['score']
            if completeness_result['issues']:
                issues.extend(completeness_result['issues'])
            
            # 3. 数据准确性检查
            accuracy_result = await self._check_data_accuracy(data)
            quality_scores['accuracy'] = accuracy_result['score']
            if accuracy_result['issues']:
                issues.extend(accuracy_result['issues'])
            
            # 4. 数据一致性检查
            consistency_result = await self._check_data_consistency(data)
            quality_scores['consistency'] = consistency_result['score']
            if consistency_result['issues']:
                warnings.extend(consistency_result['issues'])
            
            # 5. 时效性检查
            timeliness_result = self._check_data_timeliness(data)
            quality_scores['timeliness'] = timeliness_result['score']
            if timeliness_result['issues']:
                warnings.extend(timeliness_result['issues'])
            
            # 6. 计算综合质量分数
            overall_score = self._calculate_overall_quality_score(quality_scores)
            quality_level = self._determine_quality_level(overall_score)
            
            # 7. 数据清洗（如果需要）
            cleaned_data = None
            if len(issues) == 0 and len(warnings) > 0:
                cleaned_data = await self._clean_health_data(data, warnings)
            
            # 更新统计
            self.quality_stats['total_validated'] += 1
            if len(issues) == 0:
                self.quality_stats['total_passed'] += 1
            else:
                self.quality_stats['total_failed'] += 1
            
            if cleaned_data:
                self.quality_stats['total_cleaned'] += 1
            
            self.quality_stats['quality_scores'].append(overall_score)
            
            return DataQualityResult(
                is_valid=(len(issues) == 0),
                quality_score=overall_score,
                quality_level=quality_level,
                issues=issues,
                warnings=warnings,
                cleaned_data=cleaned_data,
                metadata={
                    'validation_time': datetime.now().isoformat(),
                    'quality_breakdown': quality_scores
                }
            )
            
        except Exception as e:
            logger.error(f"数据质量验证失败: {e}")
            return DataQualityResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQualityLevel.CRITICAL,
                issues=[f"验证过程异常: {str(e)}"],
                warnings=[]
            )

    def _validate_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """字段验证"""
        issues = []
        warnings = []
        valid_fields = 0
        total_fields = len(self.validation_rules)
        
        for field_name, rule in self.validation_rules.items():
            value = data.get(field_name)
            
            # 必填字段检查
            if rule.required and (value is None or value == ''):
                issues.append(f"必填字段 {field_name} 缺失")
                continue
            
            # 跳过空值的可选字段
            if value is None and not rule.required:
                continue
            
            # 数据类型检查
            if not self._check_data_type(value, rule.data_type):
                issues.append(f"字段 {field_name} 数据类型错误，期望 {rule.data_type}")
                continue
            
            # 数值范围检查
            if rule.min_value is not None or rule.max_value is not None:
                if not self._check_value_range(value, rule.min_value, rule.max_value):
                    issues.append(f"字段 {field_name} 数值超出范围 [{rule.min_value}, {rule.max_value}]")
                    continue
            
            # 正则表达式检查
            if rule.pattern and not re.match(rule.pattern, str(value)):
                warnings.append(f"字段 {field_name} 格式不符合规范")
                continue
            
            # 自定义验证器
            if rule.custom_validator:
                try:
                    if not rule.custom_validator(value):
                        warnings.append(f"字段 {field_name} 未通过自定义验证")
                        continue
                except Exception as e:
                    warnings.append(f"字段 {field_name} 自定义验证异常: {e}")
                    continue
            
            valid_fields += 1
        
        score = (valid_fields / total_fields) * 100 if total_fields > 0 else 0
        
        return {
            'score': score,
            'issues': issues,
            'warnings': warnings,
            'valid_fields': valid_fields,
            'total_fields': total_fields
        }

    def _check_data_type(self, value: Any, expected_type: str) -> bool:
        """检查数据类型"""
        if value is None:
            return True
        
        try:
            if expected_type == 'int':
                int(value)
                return True
            elif expected_type == 'float':
                float(value)
                return True
            elif expected_type == 'str':
                return isinstance(value, str)
            elif expected_type == 'bool':
                return isinstance(value, bool)
            else:
                return True
        except (ValueError, TypeError):
            return False

    def _check_value_range(self, value: Any, min_val: Optional[float], 
                          max_val: Optional[float]) -> bool:
        """检查数值范围"""
        try:
            num_value = float(value)
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    def _check_data_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据完整性"""
        issues = []
        
        # 核心健康指标检查
        core_metrics = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'spo2']
        present_metrics = sum(1 for metric in core_metrics if data.get(metric) is not None)
        
        completeness_ratio = present_metrics / len(core_metrics)
        
        if completeness_ratio < self.quality_thresholds['completeness_threshold']:
            issues.append(f"核心健康指标完整性不足: {completeness_ratio:.2%}")
        
        # 设备信息完整性
        if not data.get('device_sn'):
            issues.append("设备序列号缺失")
        
        # 时间戳完整性
        if not data.get('create_time') and not data.get('measure_time'):
            issues.append("测量时间缺失")
        
        score = completeness_ratio * 100
        
        return {
            'score': score,
            'issues': issues,
            'completeness_ratio': completeness_ratio,
            'present_metrics': present_metrics,
            'total_metrics': len(core_metrics)
        }

    async def _check_data_accuracy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据准确性"""
        issues = []
        accuracy_checks = []
        
        try:
            # 1. 生理指标相关性检查
            if data.get('blood_pressure_systolic') and data.get('blood_pressure_diastolic'):
                systolic = float(data['blood_pressure_systolic'])
                diastolic = float(data['blood_pressure_diastolic'])
                
                # 收缩压应高于舒张压
                if systolic <= diastolic:
                    issues.append("收缩压不应低于或等于舒张压")
                    accuracy_checks.append(0)
                else:
                    # 正常比例检查 (1.2-3.0)
                    ratio = systolic / diastolic
                    if ratio < 1.2 or ratio > 3.0:
                        issues.append(f"血压比例异常: {ratio:.2f}")
                        accuracy_checks.append(0.5)
                    else:
                        accuracy_checks.append(1)
            
            # 2. 心率与血氧相关性检查
            if data.get('heart_rate') and data.get('spo2'):
                heart_rate = float(data['heart_rate'])
                spo2 = float(data['spo2'])
                
                # 低血氧通常伴随高心率
                if spo2 < 90 and heart_rate < 60:
                    issues.append("低血氧时心率偏低，可能存在测量误差")
                    accuracy_checks.append(0.3)
                else:
                    accuracy_checks.append(1)
            
            # 3. 异常组合检查
            extreme_count = 0
            if data.get('heart_rate'):
                hr = float(data['heart_rate'])
                if hr > 150 or hr < 50:
                    extreme_count += 1
            
            if data.get('blood_pressure_systolic'):
                sys_bp = float(data['blood_pressure_systolic'])
                if sys_bp > 180 or sys_bp < 90:
                    extreme_count += 1
            
            if data.get('spo2'):
                spo2 = float(data['spo2'])
                if spo2 < 95:
                    extreme_count += 1
            
            # 多个极端值同时出现可能是设备故障
            if extreme_count >= 3:
                issues.append("多个极端生理指标同时出现，建议检查设备状态")
                accuracy_checks.append(0.2)
            else:
                accuracy_checks.append(1)
            
            # 4. 与用户历史基线对比检查
            user_id = data.get('user_id')
            customer_id = data.get('customer_id')
            
            if user_id and customer_id:
                baseline_check = await self._check_against_baseline(data, user_id, customer_id)
                accuracy_checks.append(baseline_check['score'])
                if baseline_check['issues']:
                    issues.extend(baseline_check['issues'])
            
            # 计算准确性分数
            score = (sum(accuracy_checks) / len(accuracy_checks)) * 100 if accuracy_checks else 50
            
            return {
                'score': score,
                'issues': issues,
                'accuracy_checks_count': len(accuracy_checks),
                'passed_checks': sum(accuracy_checks)
            }
            
        except Exception as e:
            logger.error(f"数据准确性检查失败: {e}")
            return {
                'score': 0,
                'issues': [f"准确性检查异常: {str(e)}"],
                'accuracy_checks_count': 0,
                'passed_checks': 0
            }

    async def _check_against_baseline(self, data: Dict[str, Any], 
                                    user_id: int, customer_id: int) -> Dict[str, Any]:
        """与用户基线对比检查"""
        try:
            issues = []
            
            # 获取用户最新基线
            baseline_query = db.session.query(HealthBaseline).filter(
                HealthBaseline.user_id == user_id,
                HealthBaseline.customer_id == customer_id,
                HealthBaseline.is_current == 1,
                HealthBaseline.is_deleted == 0
            )
            
            baselines = {b.feature_name: b for b in baseline_query.all()}
            
            if not baselines:
                return {'score': 0.8, 'issues': ["用户基线数据缺失，无法进行基线对比"]}
            
            deviation_scores = []
            
            for field_name in ['heart_rate', 'blood_pressure_systolic', 
                             'blood_pressure_diastolic', 'spo2', 'temperature']:
                if field_name in data and data[field_name] is not None:
                    value = float(data[field_name])
                    baseline = baselines.get(field_name)
                    
                    if baseline and baseline.mean_value and baseline.std_dev:
                        mean_val = float(baseline.mean_value)
                        std_val = float(baseline.std_dev)
                        
                        # Z-Score计算
                        z_score = abs((value - mean_val) / std_val) if std_val > 0 else 0
                        
                        if z_score > 3.0:
                            issues.append(f"{field_name} 严重偏离个人基线 (Z-Score: {z_score:.2f})")
                            deviation_scores.append(0.2)
                        elif z_score > 2.0:
                            issues.append(f"{field_name} 明显偏离个人基线 (Z-Score: {z_score:.2f})")
                            deviation_scores.append(0.6)
                        else:
                            deviation_scores.append(1.0)
            
            score = (sum(deviation_scores) / len(deviation_scores)) if deviation_scores else 0.8
            
            return {
                'score': score,
                'issues': issues,
                'baseline_checks': len(deviation_scores)
            }
            
        except Exception as e:
            logger.error(f"基线对比检查失败: {e}")
            return {'score': 0.5, 'issues': [f"基线对比异常: {str(e)}"]}

    async def _check_data_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据一致性"""
        try:
            issues = []
            consistency_checks = []
            
            user_id = data.get('user_id')
            device_sn = data.get('device_sn')
            
            if not user_id or not device_sn:
                return {'score': 0.5, 'issues': ["用户ID或设备序列号缺失，无法进行一致性检查"]}
            
            # 1. 检查用户-设备绑定一致性
            recent_time = datetime.now() - timedelta(hours=1)
            
            recent_data_query = db.session.query(UserHealthData).filter(
                UserHealthData.user_id == user_id,
                UserHealthData.device_sn == device_sn,
                UserHealthData.create_time >= recent_time,
                UserHealthData.is_deleted == 0
            ).order_by(UserHealthData.create_time.desc()).limit(10)
            
            recent_records = recent_data_query.all()
            
            if recent_records:
                # 2. 数据趋势一致性检查
                heart_rates = [r.heart_rate for r in recent_records if r.heart_rate]
                if len(heart_rates) >= 3:
                    trend_consistency = self._check_trend_consistency(heart_rates)
                    consistency_checks.append(trend_consistency)
                    if trend_consistency < 0.7:
                        issues.append("心率趋势一致性较差")
                
                # 3. 设备数据稳定性检查
                device_consistency = self._check_device_data_stability(recent_records)
                consistency_checks.append(device_consistency)
                if device_consistency < 0.8:
                    issues.append("设备数据稳定性较差")
            
            # 4. 重复数据检查
            duplicate_check = await self._check_duplicate_data(data)
            consistency_checks.append(duplicate_check['score'])
            if duplicate_check['is_duplicate']:
                issues.append("检测到重复数据")
            
            score = (sum(consistency_checks) / len(consistency_checks)) * 100 if consistency_checks else 80
            
            return {
                'score': score,
                'issues': issues,
                'consistency_checks': len(consistency_checks)
            }
            
        except Exception as e:
            logger.error(f"数据一致性检查失败: {e}")
            return {'score': 50, 'issues': [f"一致性检查异常: {str(e)}"]}

    def _check_trend_consistency(self, values: List[float]) -> float:
        """检查趋势一致性"""
        if len(values) < 3:
            return 1.0
        
        try:
            # 计算变化率
            changes = [abs(values[i] - values[i-1]) / values[i-1] 
                      for i in range(1, len(values)) if values[i-1] != 0]
            
            if not changes:
                return 1.0
            
            # 变化率的标准差，越小越一致
            change_std = stdev(changes)
            change_mean = mean(changes)
            
            # 变异系数
            cv = change_std / change_mean if change_mean > 0 else 0
            
            # 变异系数越小，一致性越好
            consistency_score = max(0, 1 - min(cv, 1))
            
            return consistency_score
            
        except Exception as e:
            logger.error(f"趋势一致性计算失败: {e}")
            return 0.5

    def _check_device_data_stability(self, records: List[UserHealthData]) -> float:
        """检查设备数据稳定性"""
        if len(records) < 2:
            return 1.0
        
        try:
            stability_scores = []
            
            # 检查各指标的稳定性
            for field in ['heart_rate', 'spo2', 'temperature']:
                values = [getattr(r, field) for r in records if getattr(r, field) is not None]
                if len(values) >= 2:
                    # 计算变异系数
                    mean_val = mean(values)
                    std_val = stdev(values) if len(values) > 1 else 0
                    cv = std_val / mean_val if mean_val > 0 else 0
                    
                    # 变异系数阈值（根据指标类型调整）
                    thresholds = {
                        'heart_rate': 0.15,     # 15%
                        'spo2': 0.05,           # 5%
                        'temperature': 0.02     # 2%
                    }
                    
                    threshold = thresholds.get(field, 0.1)
                    stability = max(0, 1 - (cv / threshold))
                    stability_scores.append(stability)
            
            return mean(stability_scores) if stability_scores else 0.8
            
        except Exception as e:
            logger.error(f"设备稳定性检查失败: {e}")
            return 0.5

    async def _check_duplicate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查重复数据"""
        try:
            user_id = data.get('user_id')
            device_sn = data.get('device_sn')
            
            if not user_id or not device_sn:
                return {'score': 1.0, 'is_duplicate': False}
            
            # 检查时间窗口内的重复数据
            window_seconds = self.quality_thresholds['duplicate_time_window']
            window_start = datetime.now() - timedelta(seconds=window_seconds)
            
            duplicate_query = db.session.query(UserHealthData).filter(
                UserHealthData.user_id == user_id,
                UserHealthData.device_sn == device_sn,
                UserHealthData.create_time >= window_start,
                UserHealthData.is_deleted == 0
            )
            
            existing_records = duplicate_query.all()
            
            # 检查是否有完全相同的数据
            for record in existing_records:
                if (record.heart_rate == data.get('heart_rate') and
                    record.blood_pressure_systolic == data.get('blood_pressure_systolic') and
                    record.blood_pressure_diastolic == data.get('blood_pressure_diastolic') and
                    record.spo2 == data.get('spo2')):
                    return {'score': 0.0, 'is_duplicate': True}
            
            return {'score': 1.0, 'is_duplicate': False}
            
        except Exception as e:
            logger.error(f"重复数据检查失败: {e}")
            return {'score': 0.8, 'is_duplicate': False}

    def _check_data_timeliness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据时效性"""
        issues = []
        
        try:
            # 获取数据时间戳
            data_time = None
            if data.get('create_time'):
                if isinstance(data['create_time'], str):
                    data_time = datetime.fromisoformat(data['create_time'].replace('Z', '+00:00'))
                elif isinstance(data['create_time'], datetime):
                    data_time = data['create_time']
            elif data.get('measure_time'):
                if isinstance(data['measure_time'], str):
                    data_time = datetime.fromisoformat(data['measure_time'].replace('Z', '+00:00'))
                elif isinstance(data['measure_time'], datetime):
                    data_time = data['measure_time']
            
            if not data_time:
                issues.append("无法确定数据时间戳")
                return {'score': 50, 'issues': issues}
            
            # 计算时间差
            now = datetime.now()
            time_diff = abs((now - data_time).total_seconds())
            
            # 时效性评分
            if time_diff <= 300:      # 5分钟内
                score = 100
            elif time_diff <= 1800:   # 30分钟内
                score = 90
            elif time_diff <= 3600:   # 1小时内
                score = 80
            elif time_diff <= 86400:  # 24小时内
                score = 60
            else:                     # 超过24小时
                score = 30
                issues.append(f"数据时效性差，距离当前时间 {time_diff/3600:.1f} 小时")
            
            return {
                'score': score,
                'issues': issues,
                'time_diff_seconds': time_diff
            }
            
        except Exception as e:
            logger.error(f"时效性检查失败: {e}")
            return {'score': 70, 'issues': [f"时效性检查异常: {str(e)}"]}

    def _calculate_overall_quality_score(self, quality_scores: Dict[str, float]) -> float:
        """计算综合质量分数"""
        try:
            weights = self.quality_thresholds
            
            weighted_score = (
                quality_scores.get('completeness', 0) * weights['completeness_weight'] +
                quality_scores.get('accuracy', 0) * weights['accuracy_weight'] +
                quality_scores.get('consistency', 0) * weights['consistency_weight'] +
                quality_scores.get('timeliness', 0) * weights['timeliness_weight']
            )
            
            return round(weighted_score, 2)
            
        except Exception as e:
            logger.error(f"综合质量分数计算失败: {e}")
            return 0.0

    def _determine_quality_level(self, score: float) -> DataQualityLevel:
        """确定质量等级"""
        if score >= 90:
            return DataQualityLevel.EXCELLENT
        elif score >= 80:
            return DataQualityLevel.GOOD
        elif score >= 70:
            return DataQualityLevel.FAIR
        elif score >= 60:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL

    async def _clean_health_data(self, data: Dict[str, Any], warnings: List[str]) -> Dict[str, Any]:
        """清洗健康数据"""
        try:
            cleaned_data = data.copy()
            
            # 1. 血压数据清洗
            if (cleaned_data.get('blood_pressure_systolic') and 
                cleaned_data.get('blood_pressure_diastolic')):
                
                systolic = float(cleaned_data['blood_pressure_systolic'])
                diastolic = float(cleaned_data['blood_pressure_diastolic'])
                
                # 修复收缩压舒张压倒置
                if systolic < diastolic:
                    cleaned_data['blood_pressure_systolic'] = diastolic
                    cleaned_data['blood_pressure_diastolic'] = systolic
                    logger.info(f"修复血压数值倒置: {systolic}/{diastolic} -> {diastolic}/{systolic}")
            
            # 2. 心率数据平滑
            if cleaned_data.get('heart_rate'):
                heart_rate = float(cleaned_data['heart_rate'])
                if heart_rate > 200:  # 极端高心率
                    # 使用合理范围内的值替代
                    cleaned_data['heart_rate'] = 150
                    logger.info(f"修复极端心率: {heart_rate} -> 150")
            
            # 3. 血氧数据修复
            if cleaned_data.get('spo2'):
                spo2 = float(cleaned_data['spo2'])
                if spo2 > 100:  # 血氧不能超过100%
                    cleaned_data['spo2'] = 100
                    logger.info(f"修复血氧超限: {spo2} -> 100")
            
            # 4. 设备序列号标准化
            if cleaned_data.get('device_sn'):
                device_sn = str(cleaned_data['device_sn']).strip().upper()
                cleaned_data['device_sn'] = device_sn
            
            # 5. 添加清洗标记
            cleaned_data['_quality_cleaned'] = True
            cleaned_data['_cleaning_time'] = datetime.now().isoformat()
            cleaned_data['_cleaning_warnings'] = warnings
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return data

    # ==================== 批量质量检查 ====================
    
    async def batch_validate_health_data(self, data_list: List[Dict[str, Any]]) -> List[DataQualityResult]:
        """批量验证健康数据质量"""
        try:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(10)
            
            async def validate_with_semaphore(data):
                async with semaphore:
                    return await self.validate_health_data(data)
            
            tasks = [validate_with_semaphore(data) for data in data_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤异常结果
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"批量验证第 {i} 条数据失败: {result}")
                    valid_results.append(DataQualityResult(
                        is_valid=False,
                        quality_score=0.0,
                        quality_level=DataQualityLevel.CRITICAL,
                        issues=[f"验证异常: {str(result)}"],
                        warnings=[]
                    ))
                else:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            logger.error(f"批量数据质量验证失败: {e}")
            return []

    # ==================== 质量报告 ====================
    
    def generate_quality_report(self, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """生成数据质量报告"""
        try:
            stats = self.quality_stats
            
            # 基础统计
            total_validated = stats['total_validated']
            pass_rate = (stats['total_passed'] / total_validated * 100) if total_validated > 0 else 0
            cleaning_rate = (stats['total_cleaned'] / total_validated * 100) if total_validated > 0 else 0
            
            # 质量分数统计
            quality_scores = stats['quality_scores']
            avg_quality = mean(quality_scores) if quality_scores else 0
            
            # 质量等级分布
            quality_distribution = {}
            for score in quality_scores:
                level = self._determine_quality_level(score)
                quality_distribution[level.value] = quality_distribution.get(level.value, 0) + 1
            
            report = {
                'report_time': datetime.now().isoformat(),
                'customer_id': customer_id,
                'summary': {
                    'total_validated': total_validated,
                    'pass_rate_percent': round(pass_rate, 2),
                    'cleaning_rate_percent': round(cleaning_rate, 2),
                    'average_quality_score': round(avg_quality, 2)
                },
                'quality_distribution': quality_distribution,
                'performance_stats': self.get_performance_stats() if hasattr(self, 'performance_stats') else {},
                'recommendations': self._generate_quality_recommendations(pass_rate, avg_quality)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成质量报告失败: {e}")
            return {'error': str(e)}

    def _generate_quality_recommendations(self, pass_rate: float, avg_quality: float) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        if pass_rate < 80:
            recommendations.append("数据通过率较低，建议检查设备校准和数据采集配置")
        
        if avg_quality < 75:
            recommendations.append("平均质量分数偏低，建议加强设备维护和用户操作培训")
        
        if self.quality_stats['total_cleaned'] / max(self.quality_stats['total_validated'], 1) > 0.3:
            recommendations.append("数据清洗频率较高，建议优化数据采集流程")
        
        if len(recommendations) == 0:
            recommendations.append("数据质量良好，继续保持当前标准")
        
        return recommendations

    async def cleanup_expired_quality_cache(self):
        """清理过期的质量缓存"""
        try:
            cleanup_count = 0
            
            for cache_type in self.cache_config.keys():
                count = await self.invalidate_cache(cache_type, "*expired*")
                cleanup_count += count
            
            logger.info(f"清理过期质量缓存: {cleanup_count} 个键")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0


# 全局数据质量控制器实例
health_data_quality = HealthDataQualityController()


if __name__ == "__main__":
    # 测试数据质量控制
    import asyncio
    
    async def test_data_quality():
        """测试数据质量控制"""
        try:
            # 测试数据
            test_data = {
                'user_id': 1001,
                'customer_id': 1001,
                'device_sn': 'TEST-DEVICE-001',
                'heart_rate': 75.5,
                'blood_pressure_systolic': 120.0,
                'blood_pressure_diastolic': 80.0,
                'spo2': 98.5,
                'temperature': 36.8,
                'step_count': 8500,
                'create_time': datetime.now().isoformat()
            }
            
            # 验证数据质量
            result = await health_data_quality.validate_health_data(test_data)
            
            print(f"验证结果: {'通过' if result.is_valid else '失败'}")
            print(f"质量分数: {result.quality_score}")
            print(f"质量等级: {result.quality_level.value}")
            
            if result.issues:
                print(f"问题: {result.issues}")
            
            if result.warnings:
                print(f"警告: {result.warnings}")
            
            if result.cleaned_data:
                print(f"清洗后数据: {result.cleaned_data}")
            
            # 生成质量报告
            report = health_data_quality.generate_quality_report()
            print(f"质量报告: {json.dumps(report, indent=2, ensure_ascii=False)}")
            
            print("✅ 数据质量控制测试完成")
            
        except Exception as e:
            print(f"❌ 数据质量控制测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_data_quality())