#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from typing import Dict, List, Tuple, Optional,Any
from collections import defaultdict
import logging

class HealthIndicatorAnalyzer:
    """健康指标分析器 - 支持从数据库配置读取指标和权重"""
    
    def __init__(self, customer_id: str = None, db_session=None):
        """
        初始化健康指标分析器
        
        Args:
            customer_id: 客户ID，用于从数据库读取配置
            db_session: 数据库会话对象
        """
        # 设置日志 - 必须在其他方法调用之前初始化
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.customer_id = customer_id
        self.db_session = db_session
        self.metrics = self._load_metrics_config()
    
    def _load_metrics_config(self) -> Dict:
        """从数据库加载指标配置和权重"""
        
        # 默认指标配置（作为备用）
        default_metrics = {
            'heart_rate': {
                'name': '心率',
                'unit': 'bpm',
                'normal_range': (60, 100),
                'weight': 1.5,
                'importance': 'high'
            },
            'blood_oxygen': {
                'name': '血氧',
                'unit': '%',
                'normal_range': (95, 100),
                'weight': 1.2,
                'importance': 'high'
            },
            'temperature': {
                'name': '体温',
                'unit': '°C',
                'normal_range': (36.3, 37.2),
                'weight': 1.0,
                'importance': 'high'
            },
            'pressure_high': {
                'name': '收缩压',
                'unit': 'mmHg',
                'normal_range': (90, 140),
                'weight': 1.3,
                'importance': 'high'
            },
            'pressure_low': {
                'name': '舒张压',
                'unit': 'mmHg',
                'normal_range': (60, 90),
                'weight': 1.3,
                'importance': 'high'
            },
            'stress': {
                'name': '压力指数',
                'unit': '',
                'normal_range': (0, 70),
                'weight': 1.1,
                'importance': 'medium'
            },
            'step': {
                'name': '步数',
                'unit': '步',
                'normal_range': (6000, 10000),
                'weight': 0.8,
                'importance': 'medium'
            },
            'distance': {
                'name': '距离',
                'unit': 'm',
                'normal_range': (3, 8),
                'weight': 0.7,
                'importance': 'medium'
            },
            'calorie': {
                'name': '消耗热量',
                'unit': 'cal',
                'normal_range': (200, 600),
                'weight': 0.6,
                'importance': 'medium'
            },
            'sleep': {
                'name': '睡眠时长',
                'unit': '小时',
                'normal_range': (7, 9),
                'weight': 2.0,
                'importance': 'high'
            }
        }
        
        # 如果没有提供customer_id或db_session，返回默认配置
        if not self.customer_id or not self.db_session:
            self.logger.warning("未提供customer_id或db_session，使用默认指标配置")
            return default_metrics
        
        try:
            # 从数据库加载配置
            from .models import HealthDataConfig
            
            configs = self.db_session.query(HealthDataConfig).filter(
                HealthDataConfig.customer_id == self.customer_id,
                HealthDataConfig.is_enabled == True
            ).all()
            
            if not configs:
                self.logger.warning(f"未找到customer_id={self.customer_id}的配置，使用默认配置")
                return default_metrics
            
            # 构建从数据库读取的配置
            db_metrics = {}
            for config in configs:
                data_type = config.data_type
                if data_type in default_metrics:
                    # 复制默认配置
                    metric_config = default_metrics[data_type].copy()
                    
                    # 更新权重（如果有配置）
                    if config.weight:
                        metric_config['weight'] = float(config.weight)
                    
                    # 更新告警阈值（如果有配置）
                    if config.warning_high and config.warning_low:
                        metric_config['normal_range'] = (
                            float(config.warning_low), 
                            float(config.warning_high)
                        )
                    
                    db_metrics[data_type] = metric_config
            
            self.logger.info(f"成功加载{len(db_metrics)}个指标配置 (customer_id={self.customer_id})")
            return db_metrics if db_metrics else default_metrics
            
        except Exception as e:
            self.logger.error(f"从数据库加载指标配置失败: {e}")
            return default_metrics
    
    def get_supported_metrics(self) -> List[str]:
        """获取支持的指标列表"""
        return list(self.metrics.keys())
    
    def get_metric_config(self, metric_name: str) -> Optional[Dict]:
        """获取特定指标的配置"""
        return self.metrics.get(metric_name)
    
    def get_metric_weight(self, metric_name: str) -> float:
        """获取指标权重"""
        metric_config = self.metrics.get(metric_name)
        return metric_config['weight'] if metric_config else 1.0
    
    def calculate_health_score(self, user_metrics: Dict[str, float]) -> Dict:
        """
        计算用户健康评分
        
        Args:
            user_metrics: 用户指标数据 {metric_name: value}
            
        Returns:
            Dict: 包含总分、各指标得分和状态的字典
        """
        try:
            scores = {}
            weights = {}
            status_summary = defaultdict(int)
            
            total_weighted_score = 0
            total_weight = 0
            
            for metric_name, value in user_metrics.items():
                if metric_name not in self.metrics:
                    continue
                
                metric_config = self.metrics[metric_name]
                weight = metric_config['weight']
                normal_range = metric_config['normal_range']
                
                # 计算单项评分
                score, status = self._calculate_metric_score(value, normal_range)
                scores[metric_name] = {
                    'score': score,
                    'value': value,
                    'status': status,
                    'weight': weight,
                    'name': metric_config['name'],
                    'unit': metric_config['unit']
                }
                
                weights[metric_name] = weight
                status_summary[status] += 1
                
                total_weighted_score += score * weight
                total_weight += weight
            
            # 计算加权总分
            overall_score = round(total_weighted_score / total_weight, 1) if total_weight > 0 else 0
            
            return {
                'overall_score': overall_score,
                'total_metrics': len(scores),
                'normal_count': status_summary.get('正常', 0),
                'warning_count': status_summary.get('注意', 0),
                'risk_count': status_summary.get('风险', 0),
                'metric_scores': scores,
                'metric_weights': weights,
                'health_level': self._get_health_level(overall_score),
                'calculation_method': 'database_config'
            }
            
        except Exception as e:
            self.logger.error(f"计算健康评分失败: {e}")
            return self._get_empty_result()
    
    def _calculate_metric_score(self, value: float, normal_range: Tuple[float, float]) -> Tuple[float, str]:
        """计算单项指标评分"""
        min_val, max_val = normal_range
        
        if min_val <= value <= max_val:
            return 100.0, '正常'
        elif value < min_val:
            # 低于正常值
            deviation = (min_val - value) / min_val
            score = max(60 - deviation * 40, 0)  # 最低0分
            status = '注意' if score >= 40 else '风险'
        else:
            # 高于正常值
            deviation = (value - max_val) / max_val
            score = max(60 - deviation * 40, 0)  # 最低0分
            status = '注意' if score >= 40 else '风险'
        
        return round(score, 1), status
    
    def _get_health_level(self, score: float) -> str:
        """根据评分获取健康等级"""
        if score >= 90:
            return '优秀'
        elif score >= 80:
            return '良好'
        elif score >= 70:
            return '一般'
        elif score >= 60:
            return '注意'
        else:
            return '风险'
    
    def _get_empty_result(self) -> Dict:
        """返回空结果"""
        return {
            'overall_score': 0,
            'total_metrics': 0,
            'normal_count': 0,
            'warning_count': 0,
            'risk_count': 0,
            'metric_scores': {},
            'metric_weights': {},
            'health_level': '未知',
            'calculation_method': 'error'
        }

    def analyze_time_series(self, health_data_list: List[Dict]) -> Dict:
        """分析时间序列数据"""
        try:
            time_series = {
                'timestamps': [],
                'metrics': {metric: [] for metric in self.metrics},
                'anomalies': {metric: [] for metric in self.metrics},
                'trends': {}
            }
            
            # 排序数据
            sorted_data = sorted(
                health_data_list,
                key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
            )
            
            for data in sorted_data:
                timestamp = data.get('timestamp')
                if not timestamp:
                    continue
                
                time_series['timestamps'].append(timestamp)
                
                for metric in self.metrics:
                    value = self._safe_float(data.get(metric))
                    time_series['metrics'][metric].append(value)
                    
                    if value > 0:
                        normal_range = self.metrics[metric]['normal_range']
                        if value < normal_range[0] or value > normal_range[1]:
                            time_series['anomalies'][metric].append({
                                'timestamp': timestamp,
                                'value': value,
                                'type': 'low' if value < normal_range[0] else 'high'
                            })
            
            # 计算趋势
            for metric in self.metrics:
                values = time_series['metrics'][metric]
                valid_values = [v for v in values if v > 0]
                
                if len(valid_values) >= 2:
                    trend = self._calculate_trend(valid_values)
                    time_series['trends'][metric] = {
                        'direction': trend['direction'],
                        'change_rate': trend['change_rate'],
                        'significance': trend['significance']
                    }
            
            return time_series
            
        except Exception as e:
            self.logger.error(f"时间序列分析错误: {str(e)}")
            return {
                'timestamps': [],
                'metrics': {},
                'anomalies': {},
                'trends': {}
            }
    
    def calculate_health_scores_legacy(self, health_data_list: List[Dict]) -> Dict:
        """计算健康分数（兼容旧接口）"""
        try:
            if not health_data_list:
                return self._get_empty_legacy_result()
            
            # 排序数据
            sorted_data = sorted(
                health_data_list,
                key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
            )
            
            scores = {
                'overall': 0,
                'factors': {},
                'details': {},
                'overallStatus': {}
            }
            
            total_weighted_score = 0
            total_weight = 0
            
            # 定义缺失指标的默认值
            default_values = {
                'stress': 15.0,        # 压力指数默认15（正常范围0-70）
                'sleep': 7.5,          # 睡眠时长默认7.5小时（正常范围7-9）
                'step': 8000.0,        # 步数默认8000步（正常范围6000-10000）
                'distance': 5.0,       # 距离默认5km（正常范围3-8）
                'calorie': 400.0,      # 卡路里默认400（正常范围200-600）
                'pressure_high': 120.0, # 收缩压默认120（从heart_rate估算）
                'pressure_low': 80.0,   # 舒张压默认80（从heart_rate估算）
                'temperature': 36.8     # 体温默认36.8°C
            }
            
            for metric, info in self.metrics.items():
                try:
                    values = []
                    for data in sorted_data:
                        value = self._safe_float(data.get(metric))
                        if value > 0:
                            values.append(value)
                    
                    # 如果没有实际数据，使用默认值
                    if not values:
                        # 如果是血压，可以从心率估算
                        if metric in ['pressure_high', 'pressure_low'] and 'heart_rate' in [d.keys() for d in sorted_data]:
                            heart_rate_values = [self._safe_float(d.get('heart_rate')) for d in sorted_data if self._safe_float(d.get('heart_rate')) > 0]
                            if heart_rate_values:
                                avg_hr = sum(heart_rate_values) / len(heart_rate_values)
                                if metric == 'pressure_high':
                                    values = [avg_hr + 35]  # 估算收缩压
                                else:  # pressure_low
                                    values = [max(avg_hr - 5, 60)]  # 估算舒张压
                        
                        # 如果仍然没有值，使用预定义的默认值
                        if not values and metric in default_values:
                            values = [default_values[metric]]
                            self.logger.info(f"指标 {metric} 无数据，使用默认值: {default_values[metric]}")
                    
                    if not values:
                        self.logger.warning(f"指标 {metric} 跳过：无有效数据且无默认值")
                        continue
                    
                    current_value = values[-1]
                    min_val, max_val = info['normal_range']
                    
                    # 计算基础分数
                    if min_val <= current_value <= max_val:
                        base_score = 90 + (10 * (1 - abs(current_value - (min_val + max_val) / 2) / ((max_val - min_val) / 2)))
                    else:
                        if current_value < min_val:
                            deviation = (min_val - current_value) / min_val
                        else:
                            deviation = (current_value - max_val) / max_val
                        base_score = max(40, 80 - (deviation * 40))
                    
                    # 计算稳定性分数
                    if len(values) > 1:
                        std_dev = np.std(values)
                        mean_val = np.mean(values)
                        cv = std_dev / mean_val if mean_val != 0 else 0
                        stability_score = max(0, 100 - (cv * 100))
                        final_score = (base_score * 0.8) + (stability_score * 0.2)
                    else:
                        final_score = base_score
                    
                    final_score = max(0, min(100, final_score))
                    
                    weight = info['weight']
                    total_weighted_score += final_score * weight
                    total_weight += weight
                    
                    scores['factors'][metric] = {
                        'name': info['name'],
                        'score': round(final_score, 1),
                        'weight': weight,
                        'unit': info['unit'],
                        'currentValue': round(current_value, 1),
                        'normalRange': info['normal_range'],
                        'status': self._get_status_level(final_score)
                    }
                    
                    status = self._get_value_status(current_value, min_val, max_val)
                    scores['details'][metric] = {
                        'status': status,
                        'message': self._generate_metric_message(info['name'], current_value, info['unit'], min_val, max_val),
                        'score': round(final_score, 1),
                        'suggestions': self._get_metric_suggestions(metric, status)
                    }
                    
                    self.logger.info(f"指标 {metric} 计算完成: 得分={final_score:.1f}, 当前值={current_value}")
                    
                except Exception as e:
                    self.logger.error(f"计算指标 {metric} 分数时出错: {str(e)}")
                    continue
            
            if total_weight > 0:
                overall_score = round(total_weighted_score / total_weight, 1)
                scores['overall'] = overall_score
                scores['overallStatus'] = self._get_overall_status(overall_score)
                self.logger.info(f"总体健康分数计算完成: {overall_score} (共{len(scores['factors'])}个指标)")
            
            return scores
            
        except Exception as e:
            self.logger.error(f"计算健康分数时出错: {str(e)}")
            return self._get_empty_legacy_result()
    
    def _calculate_trend(self, values: List[float]) -> Dict:
        """计算趋势"""
        try:
            first_val = values[0]
            last_val = values[-1]
            change_rate = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
            
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            
            if abs(change_rate) < 5:
                direction = "稳定"
                significance = "low"
            else:
                direction = "上升" if slope > 0 else "下降"
                significance = "high" if abs(change_rate) > 20 else "medium"
            
            return {
                'direction': direction,
                'change_rate': round(change_rate, 2),
                'significance': significance
            }
            
        except Exception as e:
            self.logger.error(f"计算趋势错误: {str(e)}")
            return {
                'direction': "未知",
                'change_rate': 0,
                'significance': "low"
            }
    
    def _safe_float(self, value) -> float:
        """安全地转换为浮点数"""
        try:
            if value is None or value == '' or value == 'None':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _get_status_level(self, score: float) -> str:
        """根据分数获取状态级别"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'normal'
        elif score >= 60:
            return 'warning'
        else:
            return 'danger'
    
    def _get_value_status(self, value: float, min_val: float, max_val: float) -> str:
        """获取数值状态"""
        if value < min_val:
            return 'low'
        elif value > max_val:
            return 'high'
        return 'normal'
    
    def _generate_metric_message(self, name: str, value: float, unit: str, min_val: float, max_val: float) -> str:
        """生成指标消息"""
        if value < min_val:
            return f"{name}偏低，当前{value}{unit}，建议值{min_val}-{max_val}{unit}"
        elif value > max_val:
            return f"{name}偏高，当前{value}{unit}，建议值{min_val}-{max_val}{unit}"
        return f"{name}正常，当前{value}{unit}"
    
    def _get_overall_status(self, score: float) -> dict:
        """获取总体健康状况评估"""
        status = self._get_status_level(score)
        
        status_messages = {
            'excellent': '您的健康状况非常好，请继续保持！',
            'good': '您的健康状况良好，建议继续保持健康的生活方式。',
            'normal': '您的健康状况正常，建议适当增加运动和注意作息。',
            'warning': '您的健康状况需要注意，建议及时调整生活习惯。',
            'danger': '您的健康状况需要关注，建议尽快就医检查。'
        }
        
        return {
            'level': status,
            'score': score,
            'message': status_messages.get(status, '暂无评估信息'),
            'color': {
                'excellent': '#52c41a',
                'good': '#1890ff',
                'normal': '#faad14',
                'warning': '#ff7a45',
                'danger': '#f5222d'
            }.get(status, '#666666')
        }
    
    def _get_metric_suggestions(self, metric: str, status: str) -> list:
        """获取指标改善建议"""
        suggestions = {
            'heart_rate': {
                'high': ['保持情绪稳定', '避免剧烈运动', '规律作息'],
                'low': ['适度运动', '保持充足睡眠', '注意保暖'],
                'normal': ['保持规律运动', '维持健康作息']
            },
            'blood_oxygen': {
                'high': ['保持正常呼吸', '无需特别干预'],
                'low': ['保持空气流通', '做深呼吸运动', '必要时就医'],
                'normal': ['保持环境通风', '适度运动']
            },
            'temperature': {
                'high': ['多休息', '注意降温', '必要时就医'],
                'low': ['注意保暖', '适当运动', '保持充足睡眠'],
                'normal': ['保持作息规律', '适度运动']
            },
            'step': {
                'high': ['注意适度', '保持运动强度均衡'],
                'low': ['增加日常运动量', '建议每天步行30分钟'],
                'normal': ['保持当前运动量', '适当增加运动强度']
            },
            'calorie': {
                'high': ['注意饮食均衡', '控制运动强度'],
                'low': ['适当增加运动量', '注意营养均衡'],
                'normal': ['保持健康的饮食习惯', '维持运动量']
            },
            'pressure_high': {
                'high': ['限制盐分摄入', '保持心情舒畅', '规律作息', '必要时就医'],
                'low': ['适当补充盐分', '多休息', '必要时就医'],
                'normal': ['保持健康饮食', '规律运动', '避免熬夜']
            },
            'pressure_low': {
                'high': ['控制饮食', '规律作息', '必要时就医'],
                'low': ['补充营养', '适度运动', '作息规律'],
                'normal': ['保持当前生活方式', '适度运动']
            },
            'stress': {
                'high': ['保持心情舒畅', '适当运动放松', '规律作息', '必要时寻求心理咨询'],
                'low': ['保持良好心态', '继续保持'],
                'normal': ['保持当前状态', '适度运动放松']
            }
        }
        
        return suggestions.get(metric, {}).get(status, ['维持当前状态'])
    
    def _get_empty_legacy_result(self) -> Dict:
        """返回空的传统格式结果"""
        return {
            'overall': 0,
            'factors': {},
            'details': {},
            'overallStatus': {
                'level': 'unknown',
                'score': 0,
                'message': '暂无数据',
                'color': '#666666'
            }
        }

def analyze_health_trends(health_data_list: List[Dict[str, Any]], customer_id: str = None, db_session=None):
    """分析健康趋势并生成可视化数据"""
    try:
        if not health_data_list:
            return {
                'success': False,
                'message': '健康数据为空',
                'data': None
            }

        analyzer = HealthIndicatorAnalyzer(customer_id=customer_id, db_session=db_session)
        
        # 计算健康分数（使用兼容接口）
        health_scores = analyzer.calculate_health_scores_legacy(health_data_list)
        if not health_scores:
            return {
                'success': False,
                'message': '健康分数计算失败',
                'data': None
            }

        # 分析时间序列数据
        time_series = analyzer.analyze_time_series(health_data_list)
        if not time_series:
            return {
                'success': False,
                'message': '时间序列分析失败',
                'data': None
            }

        # 生成返回数据 - 修复字段名与前端期望一致
        result_data = {
            'summary': {
                'timeRange': {  # 修改为timeRange与前端一致
                    'start': health_data_list[-1].get('timestamp', ''),
                    'end': health_data_list[0].get('timestamp', '')
                },
                'totalRecords': len(health_data_list),  # 添加总记录数
                'overallScore': health_scores['overall']
            },
            'healthScores': health_scores,
            'timeSeriesData': time_series,  # 修改为timeSeriesData与前端一致
            'recommendations': _generate_recommendations(health_scores, time_series)
        }

        return {
            'success': True,
            'message': '健康趋势分析完成',
            'data': result_data
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'健康趋势分析错误: {str(e)}',
            'error': str(e)
        }

def generate_health_score(health_data_list: List[Dict[str, Any]], customer_id: str = None, db_session=None):
    """分析健康趋势并生成可视化数据"""
    try:
        if not health_data_list:
            return {
                'success': False,
                'message': '健康数据为空',
                'data': None
            }

        analyzer = HealthIndicatorAnalyzer(customer_id=customer_id, db_session=db_session)
        
        # 计算健康分数（使用兼容接口）
        health_scores = analyzer.calculate_health_scores_legacy(health_data_list)
        if not health_scores:
            return {
                'success': False,
                'message': '健康分数计算失败',
                'data': None
            }

        # 生成返回数据
        result_data = {
            'summary': {
                'dataRange': {
                    'start': health_data_list[-1].get('timestamp', ''),
                    'end': health_data_list[0].get('timestamp', '')
                },
                'overallScore': health_scores['overall'],
                'status': health_scores['overallStatus']
            },
            'healthScores': health_scores,
            'recommendations': _generate_recommendations(health_scores, {})
        }

        return {
            'success': True,
            'message': '健康评分计算完成',
            'data': result_data
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'健康评分计算错误: {str(e)}',
            'error': str(e)
        } 

def _generate_recommendations(health_scores: Dict, time_series: Dict) -> List[Dict]:
    """生成健康建议"""
    recommendations = []
    
    try:
        if not health_scores or 'factors' not in health_scores:
            return []
        
        # 基于各项指标分数生成建议
        for metric, factor in health_scores.get('factors', {}).items():
            score = factor.get('score', 0)
            status = factor.get('status', '')
            name = factor.get('name', metric)
            
            if score < 70:  # 需要改善的指标
                recommendation = {
                    'metric': metric,
                    'name': name,
                    'current_score': score,
                    'status': status,
                    'priority': 'high' if score < 50 else 'medium',
                    'suggestions': health_scores.get('details', {}).get(metric, {}).get('suggestions', ['保持健康生活方式'])
                }
                recommendations.append(recommendation)
        
        # 基于趋势分析添加建议
        if time_series and 'trends' in time_series:
            for metric, trend in time_series['trends'].items():
                if trend.get('direction') == '下降' and trend.get('significance') == 'high':
                    recommendations.append({
                        'metric': metric,
                        'name': f"{metric}趋势",
                        'type': 'trend',
                        'priority': 'high',
                        'message': f"{metric}呈明显下降趋势，建议及时关注",
                        'suggestions': ['定期监测', '调整生活方式', '必要时咨询医生']
                    })
        
        # 按优先级排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        
        return recommendations[:5]  # 最多返回5个建议
        
    except Exception as e:
        print(f"生成健康建议失败: {e}")
        return [] 

# 使用示例
if __name__ == "__main__":
    # 示例1：使用数据库配置
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 模拟数据库会话（实际使用时请替换为真实的数据库配置）
    # engine = create_engine('mysql://user:pass@localhost/db')
    # Session = sessionmaker(bind=engine)
    # db_session = Session()
    
    # 示例健康数据
    sample_health_data = [
        {
            'timestamp': '2025-06-03 10:00:00',
            'heart_rate': 72,
            'blood_oxygen': 98,
            'temperature': 36.5,
            'pressure_high': 120,
            'pressure_low': 80,
            'stress': 35,
            'step': 8000,
            'distance': 6.5,
            'calorie': 350,
            'sleep': 7.5
        },
        {
            'timestamp': '2025-06-03 09:00:00',
            'heart_rate': 75,
            'blood_oxygen': 97,
            'temperature': 36.7,
            'pressure_high': 125,
            'pressure_low': 82,
            'stress': 40,
            'step': 6000,
            'distance': 4.8,
            'calorie': 280,
            'sleep': 7.0
        }
    ]
    
    # 示例1：不使用数据库配置（使用默认配置）
    print("=== 示例1：使用默认配置 ===")
    analyzer_default = HealthIndicatorAnalyzer()
    
    # 单次评分
    user_metrics = {
        'heart_rate': 72,
        'blood_oxygen': 98,
        'temperature': 36.5,
        'pressure_high': 120,
        'pressure_low': 80,
        'stress': 35,
        'step': 8000,
        'calorie': 350
    }
    score_result = analyzer_default.calculate_health_score(user_metrics)
    print(f"健康评分: {score_result['overall_score']}")
    print(f"健康等级: {score_result['health_level']}")
    print(f"指标数量: {score_result['total_metrics']}")
    
    # 趋势分析
    trend_result = analyze_health_trends(sample_health_data)
    print(f"趋势分析结果: {trend_result['success']}")
    
    # 示例2：使用数据库配置（需要实际数据库连接）
    print("\n=== 示例2：使用数据库配置 ===")
    print("需要传入customer_id和db_session参数：")
    print("analyzer_db = HealthIndicatorAnalyzer(customer_id='1', db_session=db_session)")
    print("trend_result = analyze_health_trends(sample_health_data, customer_id='1', db_session=db_session)")
    
    # 示例3：查看支持的指标
    print(f"\n=== 支持的指标 ===")
    print(f"支持的指标: {analyzer_default.get_supported_metrics()}")
    print(f"心率权重: {analyzer_default.get_metric_weight('heart_rate')}")
    print(f"血氧配置: {analyzer_default.get_metric_config('blood_oxygen')}")
