import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math
import json

class HealthDataAnalyzer:
    def __init__(self, health_data_list):
        self.health_data_list = health_data_list
        # 定义健康指标基线值 - 扩展完整的健康指标
        self.baseline = {
            'heart_rate': {
                'normal_range': [60, 100], 
                'name': '心率',
                'unit': 'bpm',
                'weight': 1.5
            },
            'blood_oxygen': {
                'normal_range': [95, 100], 
                'name': '血氧',
                'unit': '%',
                'weight': 1.2
            },
            'temperature': {
                'normal_range': [36.3, 37.2], 
                'name': '体温',
                'unit': '°C',
                'weight': 1.0
            },
            'pressure_high': {
                'normal_range': [90, 140], 
                'name': '收缩压',
                'unit': 'mmHg',
                'weight': 1.3
            },
            'pressure_low': {
                'normal_range': [60, 90], 
                'name': '舒张压',
                'unit': 'mmHg',
                'weight': 1.1
            },
            'step': {
                'normal_range': [6000, 10000], 
                'name': '步数',
                'unit': '步',
                'weight': 0.8
            },
            'calorie': {
                'normal_range': [200, 600], 
                'name': '卡路里',
                'unit': 'kcal',
                'weight': 0.7
            },
            'stress': {
                'normal_range': [0, 30], 
                'name': '压力指数',
                'unit': '分',
                'weight': 1.2
            },
            'sleep': {
                'normal_range': [6, 9], 
                'name': '睡眠时长',
                'unit': '小时',
                'weight': 1.1
            },
            # 兼容旧的field名称
            'heartRate': {
                'normal_range': [60, 100], 
                'name': '心率',
                'unit': 'bpm',
                'weight': 1.5
            },
            'bloodOxygen': {
                'normal_range': [95, 100], 
                'name': '血氧',
                'unit': '%',
                'weight': 1.2
            },
            'bloodPressure': {
                'normal_range': [90, 140], 
                'name': '血压',
                'unit': 'mmHg',
                'weight': 1.3
            }
        }

    def analyze_data(self):
        """分析健康数据并返回完整的分析结果"""
        try:
            if not self.health_data_list:
                return {
                    'success': False,
                    'error': 'No health data available'
                }

            # 添加数据调试信息
            print(f"🔍 HealthDataAnalyzer 收到数据: {len(self.health_data_list)} 条")
            if self.health_data_list:
                # 按时间排序以查看数据时间范围
                sorted_data = sorted(self.health_data_list, key=lambda x: x.get('timestamp', ''))
                if sorted_data:
                    print(f"⏰ 数据时间范围: {sorted_data[0].get('timestamp')} 到 {sorted_data[-1].get('timestamp')}")

            # 获取所有分析结果
            dept_stats = self.calculate_department_stats()
            overall_stats = self.calculate_overall_stats()
            trends = self.analyze_trends()
            correlations = self.analyze_correlations()
            advanced_stats = self.calculate_advanced_stats()
            anomaly_detection = self.detect_anomalies()
            health_scores = self.calculate_health_scores()

            # 构建前端期望的数据结构
            summary_data = self.build_summary_data(health_scores)
            time_series_data = self.build_time_series_data()
            
            result = {
                'success': True,
                'data': {
                    'summary': summary_data,
                    'healthScores': health_scores,
                    'timeSeriesData': time_series_data,
                    'departmentStats': dept_stats,
                    'statistics': overall_stats,
                    'trends': trends,
                    'correlations': correlations,
                    'advancedStats': advanced_stats,
                    'anomalies': anomaly_detection,
                    'totalRecords': len(self.health_data_list)
                }
            }
            
            # 清理所有NaN值
            result = self._sanitize_dict(result)
            
            return result

        except Exception as e:
            print(f"Error in analyze_data: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_department_stats(self):
        """计算部门统计信息"""
        try:
            dept_stats = {}
            for data in self.health_data_list:
                dept_name = data.get('deptName', '未知部门')
                if dept_name not in dept_stats:
                    dept_stats[dept_name] = {
                        'deviceCount': 0,
                        'avgTemperature': 0,
                        'avgHeartRate': 0,
                        'avgBloodOxygen': 0,
                        'devices': []
                    }
                dept_stats[dept_name]['deviceCount'] += 1
                dept_stats[dept_name]['devices'].append(data.get('deviceSn', ''))
                
                # 使用字段映射适配器
                dept_stats[dept_name]['avgTemperature'] += self._get_field_value(data, 'temperature')
                dept_stats[dept_name]['avgHeartRate'] += self._get_field_value(data, 'heart_rate', 'heartRate')
                dept_stats[dept_name]['avgBloodOxygen'] += self._get_field_value(data, 'blood_oxygen', 'bloodOxygen')

            # 计算每个部门的平均值
            for dept in dept_stats.values():
                if dept['deviceCount'] > 0:
                    dept['avgTemperature'] /= dept['deviceCount']
                    dept['avgHeartRate'] /= dept['deviceCount']
                    dept['avgBloodOxygen'] /= dept['deviceCount']
                dept['devices'] = list(set(dept['devices']))  # 去重

            return dept_stats
        except Exception as e:
            print(f"Error in calculate_department_stats: {e}")
            return {}

    def calculate_overall_stats(self):
        """计算总体统计信息"""
        try:
            if not self.health_data_list:
                return {
                    'totalDevices': 0,
                    'devicesWithData': 0,
                    'averageStats': {
                        'avgTemperature': 0,
                        'avgHeartRate': 0,
                        'avgBloodOxygen': 0,
                    }
                }
            
            # 使用字段映射适配器
            temperature_sum = sum(self._get_field_value(d, 'temperature') for d in self.health_data_list)
            heart_rate_sum = sum(self._get_field_value(d, 'heart_rate', 'heartRate') for d in self.health_data_list)
            blood_oxygen_sum = sum(self._get_field_value(d, 'blood_oxygen', 'bloodOxygen') for d in self.health_data_list)
            
            count = len(self.health_data_list)
            stats = {
                'totalDevices': count,
                'devicesWithData': count,
                'averageStats': {
                    'avgTemperature': round(temperature_sum / count, 1) if count > 0 else 0,
                    'avgHeartRate': round(heart_rate_sum / count, 1) if count > 0 else 0,
                    'avgBloodOxygen': round(blood_oxygen_sum / count, 1) if count > 0 else 0,
                }
            }
            return stats
        except Exception as e:
            print(f"Error in calculate_overall_stats: {e}")
            return {}

    def analyze_trends(self):
        """分析健康指标趋势"""
        try:
            trends = {}
            # 字段映射：新格式 -> (旧格式回退)
            field_mapping = {
                'heart_rate': 'heartRate',
                'blood_oxygen': 'bloodOxygen', 
                'temperature': None,
                'step': None,
                'calorie': None
            }
            
            for primary_field, fallback_field in field_mapping.items():
                values = [self._get_field_value(data, primary_field, fallback_field) for data in self.health_data_list]
                valid_values = [v for v in values if v > 0]  # 过滤掉0值
                
                if len(valid_values) >= 2:
                    trend = self._calculate_trend(valid_values)
                    trends[primary_field] = {
                        'values': valid_values,
                        'trend': trend,
                        'change_rate': self._calculate_change_rate(valid_values)
                    }
                elif len(valid_values) == 1:
                    # 只有一个有效值的情况
                    trends[primary_field] = {
                        'values': valid_values,
                        'trend': {'direction': '数据不足', 'change_rate': 0, 'significance': 'none'},
                        'change_rate': 0
                    }
            return trends
        except Exception as e:
            print(f"Error in analyze_trends: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def analyze_correlations(self):
        """分析指标间的相关性"""
        try:
            metrics = ['heartRate', 'bloodOxygen', 'temperature', 'step', 'calorie']
            correlations = {}

            # 将列表数据转换为字典格式，方便访问
            data_dicts = []
            for item in self.health_data_list:
                try:
                    data_dict = {
                        'heartRate': float(item.get('heartRate', 0)),
                        'bloodOxygen': float(item.get('bloodOxygen', 0)),
                        'temperature': float(item.get('temperature', 0)),
                        'step': float(item.get('step', 0)),
                        'calorie': float(item.get('calorie', 0))
                    }
                    data_dicts.append(data_dict)
                except (ValueError, AttributeError) as e:
                    print(f"Error converting data: {e}")
                    continue

            # 计算相关性
            for i, metric1 in enumerate(metrics):
                for metric2 in metrics[i+1:]:
                    values1 = [d[metric1] for d in data_dicts]
                    values2 = [d[metric2] for d in data_dicts]
                    if values1 and values2:
                        correlation = self._calculate_correlation(values1, values2)
                        correlations[f"{metric1}_vs_{metric2}"] = {
                            'correlation': correlation,
                            'strength': self._get_correlation_strength(correlation)
                        }

            return correlations
        except Exception as e:
            print(f"Error in analyze_correlations: {e}")
            return {}

    def calculate_advanced_stats(self):
        """计算高级统计指标"""
        try:
            metrics = ['heartRate', 'bloodOxygen', 'temperature', 'step', 'calorie']
            advanced_stats = {}

            for metric in metrics:
                values = []
                for item in self.health_data_list:
                    try:
                        value = float(item.get(metric, 0))
                        values.append(value)
                    except (ValueError, TypeError):
                        continue

                if values:
                    sorted_values = sorted(values)
                    n = len(values)
                    median = sorted_values[n//2] if n % 2 else (sorted_values[n//2-1] + sorted_values[n//2])/2
                    q1 = sorted_values[n//4]
                    q3 = sorted_values[3*n//4]
                    
                    advanced_stats[metric] = {
                        'median': median,
                        'q1': q1,
                        'q3': q3,
                        'iqr': q3 - q1,
                        'min': min(values),
                        'max': max(values),
                        'variance': sum((x - sum(values)/n)**2 for x in values)/n
                    }

            return advanced_stats
        except Exception as e:
            print(f"Error in calculate_advanced_stats: {e}")
            return {}

    def detect_anomalies(self):
        """检测异常值"""
        try:
            metrics = ['heartRate', 'bloodOxygen', 'temperature', 'step', 'calorie']
            anomalies = {}

            for metric in metrics:
                values = []
                timestamps = []
                for item in self.health_data_list:
                    try:
                        value = float(item.get(metric, 0))
                        values.append(value)
                        timestamps.append(item.get('timestamp'))
                    except (ValueError, TypeError):
                        continue

                if values:
                    # 使用IQR方法检测异常值
                    q1 = np.percentile(values, 25)
                    q3 = np.percentile(values, 75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr

                    anomaly_points = []
                    for i, value in enumerate(values):
                        if value < lower_bound or value > upper_bound:
                            anomaly_points.append({
                                'timestamp': timestamps[i],
                                'value': value,
                                'type': 'low' if value < lower_bound else 'high'
                            })

                    anomalies[metric] = anomaly_points

            return anomalies
        except Exception as e:
            print(f"Error in detect_anomalies: {e}")
            return {}

    def calculate_health_scores(self) -> Dict[str, Any]:
        """计算健康分数"""
        try:
            print("开始计算区间内的健康分数...")
            
            scores = {
                'overall': 0,
                'factors': {},
                'details': {}
            }
            
            total_weighted_score = 0
            total_weight = 0
            
            # 遍历每个健康指标
            for metric, info in self.baseline.items():
                try:
                    # 收集区间内的所有有效值
                    values = []
                    timestamps = []
                    for data in self.health_data_list:
                        value = self._safe_float(data.get(metric))
                        if value > 0:
                            values.append(value)
                            timestamps.append(data.get('timestamp'))
                    
                    if not values:
                        print(f"指标 {metric} 在区间内没有有效值")
                        continue
                    
                    # 计算统计值
                    avg_value = np.mean(values)
                    max_value = max(values)
                    min_value = min(values)
                    std_dev = np.std(values) if len(values) > 1 else 0
                    
                    # 获取正常范围
                    min_normal, max_normal = info['normal_range']
                    
                    # 计算指标得分
                    # 1. 计算值的分布得分
                    in_range_values = [v for v in values if min_normal <= v <= max_normal]
                    range_score = (len(in_range_values) / len(values)) * 100
                    
                    # 2. 计算稳定性得分
                    if max_normal != min_normal:
                        stability_score = 100 - (std_dev / ((max_normal - min_normal) / 4)) * 100
                        stability_score = max(0, min(100, stability_score))
                    else:
                        stability_score = 100
                    
                    # 3. 计算趋势得分
                    trend = self._calculate_trend(values)
                    trend_score = 100 if trend['direction'] == '稳定' else (
                        80 if abs(trend['change_rate']) < 10 else 60
                    )
                    
                    # 综合得分 (分布60% + 稳定性30% + 趋势10%)
                    final_score = (range_score * 0.6) + (stability_score * 0.3) + (trend_score * 0.1)
                    final_score = max(0, min(100, final_score))
                    
                    # 从基线配置获取权重和单位
                    weight = info.get('weight', 1.0)
                    unit = info.get('unit', '')
                    name = info.get('name', metric)
                    
                    total_weighted_score += final_score * weight
                    total_weight += weight
                    
                    # 存储因子分析结果
                    scores['factors'][metric] = {
                        'name': name,
                        'score': round(final_score, 1),
                        'weight': weight,
                        'unit': unit,
                        'currentValue': round(avg_value, 1),  # 使用平均值
                        'normalRange': info['normal_range'],
                        'status': self._get_status_level(final_score),
                        'statistics': {
                            'average': round(avg_value, 1),
                            'maximum': round(max_value, 1),
                            'minimum': round(min_value, 1),
                            'standardDeviation': round(std_dev, 2),
                            'inRangeRate': round(len(in_range_values) / len(values) * 100, 1)
                        },
                        'trend': trend
                    }
                    
                    # 生成详细分析和建议
                    status = self._get_value_status(avg_value, min_normal, max_normal)
                    scores['details'][metric] = {
                        'status': status,
                        'message': self._generate_analysis_message(
                            metric, 
                            avg_value, 
                            min_value, 
                            max_value, 
                            '', 
                            min_normal, 
                            max_normal, 
                            trend
                        ),
                        'score': round(final_score, 1),
                        'suggestions': self._get_detailed_suggestions(
                            metric, 
                            status, 
                            trend, 
                            len(in_range_values) / len(values)
                        )
                    }
                    
                    print(f"指标 {metric} 计算完成: 得分={final_score}, 状态={status}")
                    
                except Exception as e:
                    print(f"计算指标 {metric} 时出错: {str(e)}")
                    continue
            
            # 计算总分
            if total_weight > 0:
                overall_score = round(total_weighted_score / total_weight, 1)
                scores['overall'] = overall_score
                scores['overallStatus'] = self._get_overall_status(overall_score)
                print(f"总体健康分数: {overall_score}")
            else:
                print("没有有效的指标数据用于计算总分")
                return None
            
            return scores
            
        except Exception as e:
            print(f"计算健康分数时出错: {str(e)}")
            return None

    def _generate_analysis_message(self, name: str, avg: float, min_val: float, 
                                 max_val: float, unit: str, normal_min: float, 
                                 normal_max: float, trend: Dict) -> str:
        """生成详细的分析消息"""
        # 基础状态描述
        if avg < normal_min:
            status_desc = f"{name}总体偏低"
        elif avg > normal_max:
            status_desc = f"{name}总体偏高"
        else:
            status_desc = f"{name}总体正常"
        
        # 数据范围描述
        range_desc = f"，区间内平均值{round(avg,1)}{unit}（最低{round(min_val,1)}，最高{round(max_val,1)}）"
        
        # 趋势描述
        if trend['direction'] != '稳定':
            trend_desc = f"，呈{trend['direction']}趋势（变化率{abs(trend['change_rate'])}%）"
        else:
            trend_desc = "，保持稳定"
        
        # 正常范围参考
        reference = f"，建议保持在{normal_min}-{normal_max}{unit}"
        
        return status_desc + range_desc + trend_desc + reference

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """计算数值趋势"""
        try:
            if len(values) < 2:
                return {'direction': '数据不足', 'change_rate': 0, 'significance': 'none'}
            
            # 计算整体变化率
            first_val = values[0]
            last_val = values[-1]
            change_rate = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
            
            # 使用线性回归分析趋势
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            
            # 判断趋势方向和显著性
            if abs(change_rate) < 5:
                direction = "稳定"
                significance = "low"
            else:
                direction = "上升" if slope > 0 else "下降"
                if abs(change_rate) > 20:
                    significance = "high"
                elif abs(change_rate) > 10:
                    significance = "medium"
                else:
                    significance = "low"
            
            return {
                'direction': direction,
                'change_rate': round(change_rate, 1),
                'significance': significance
            }
            
        except Exception as e:
            print(f"计算趋势时出错: {str(e)}")
            return {'direction': '未知', 'change_rate': 0, 'significance': 'none'}

    def _calculate_change_rate(self, values):
        """计算变化率"""
        if len(values) < 2:
            return 0
        return ((values[-1] - values[0]) / values[0]) * 100

    def _calculate_correlation(self, x, y):
        """计算相关系数"""
        if len(x) != len(y):
            return 0
        return np.corrcoef(x, y)[0, 1]

    def _get_correlation_strength(self, correlation):
        """获取相关性强度"""
        if abs(correlation) > 0.8:
            return 'strong'
        elif abs(correlation) > 0.5:
            return 'moderate'
        else:
            return 'weak'

    def _get_value_status(self, value: float, min_val: float, max_val: float) -> str:
        """获取数值状态"""
        if value < min_val:
            return 'low'
        elif value > max_val:
            return 'high'
        return 'normal'

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

    def _safe_float(self, value) -> float:
        """安全地转换为浮点数，避免NaN和Infinity"""
        try:
            if value is None or value == '' or value == 'None':
                return 0.0
            
            float_val = float(value)
            
            # 检查NaN和无穷大
            if math.isnan(float_val) or math.isinf(float_val):
                return 0.0
                
            return float_val
        except (ValueError, TypeError):
            return 0.0

    def _get_field_value(self, data: dict, primary_field: str, fallback_field: str = None) -> float:
        """
        字段映射适配器：优先使用新格式字段，回退到旧格式
        
        Args:
            data: 数据字典
            primary_field: 主要字段名（新格式，如'heart_rate'）
            fallback_field: 回退字段名（旧格式，如'heartRate'）
        """
        # 优先使用新格式字段
        value = data.get(primary_field)
        if value is not None:
            return self._safe_float(value)
        
        # 回退到旧格式字段
        if fallback_field:
            value = data.get(fallback_field)
            if value is not None:
                return self._safe_float(value)
        
        return 0.0

    def _get_detailed_suggestions(self, metric: str, status: str, trend: Dict, score: float) -> List[str]:
        """生成详细的健康建议"""
        suggestions = []
        
        if metric == 'heartRate':
            if status == 'high':
                suggestions = [
                    "您的心率偏高，建议进行深呼吸和放松练习来帮助调节",
                    "避免剧烈运动和情绪激动，保持心情平和",
                    "建议规律作息，保证7-8小时充足睡眠",
                    "可以尝试进行冥想或瑜伽等放松活动",
                    "如果持续偏高，建议及时就医检查"
                ]
            elif status == 'low':
                suggestions = [
                    "您的心率偏低，建议适度增加有氧运动强度",
                    "每天进行30分钟以上的快走或慢跑",
                    "注意保暖，避免受凉",
                    "可以适当补充能量，保持营养均衡",
                    "如果经常感觉疲劳，建议咨询医生"
                ]
        elif metric == 'step':
            if status == 'low':
                suggestions = [
                    "您的运动量不足，建议循序渐进地增加运动量",
                    "每天坚持步行30分钟，目标达到8000步",
                    "工作时每小时起来活动5分钟",
                    "可以选择步行代替短距离乘车",
                    "建议参加一些户外活动或运动社交"
                ]
        # ... 其他指标的详细建议

        return suggestions

    def _sanitize_numeric(self, value):
        """将NaN、Infinity等无效数值转换为有效的JSON数值"""
        if value is None:
            return 0
        
        try:
            # 转换为浮点数
            num_value = float(value)
            
            # 检查是否为NaN或无穷大
            if math.isnan(num_value) or math.isinf(num_value):
                return 0
            
            return num_value
        except (ValueError, TypeError):
            return 0

    def _sanitize_dict(self, data):
        """递归清理字典中的所有NaN值"""
        if isinstance(data, dict):
            return {key: self._sanitize_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_dict(item) for item in data]
        elif isinstance(data, (int, float)):
            return self._sanitize_numeric(data)
        else:
            return data

    def build_summary_data(self, health_scores):
        """构建前端期望的summary数据结构"""
        try:
            if not self.health_data_list:
                return {
                    'overallScore': 0,
                    'timeRange': {'start': '', 'end': ''},
                    'totalRecords': 0
                }
            
            # 按时间排序
            sorted_data = sorted(self.health_data_list, key=lambda x: x.get('timestamp', ''))
            
            return {
                'overallScore': health_scores.get('overall', 0),
                'timeRange': {
                    'start': sorted_data[0].get('timestamp', '') if sorted_data else '',
                    'end': sorted_data[-1].get('timestamp', '') if sorted_data else ''
                },
                'totalRecords': len(self.health_data_list)
            }
        except Exception as e:
            print(f"Error building summary data: {e}")
            return {
                'overallScore': 0,
                'timeRange': {'start': '', 'end': ''},
                'totalRecords': 0
            }

    def build_time_series_data(self):
        """构建前端期望的timeSeriesData数据结构"""
        try:
            if not self.health_data_list:
                return {
                    'timestamps': [],
                    'metrics': {},
                    'anomalies': {}
                }
            
            # 按时间排序
            sorted_data = sorted(self.health_data_list, key=lambda x: x.get('timestamp', ''))
            
            # 提取时间戳
            timestamps = [item.get('timestamp', '') for item in sorted_data]
            
            # 提取各指标数据
            metrics = {}
            anomalies = {}
            
            # 定义需要展示的指标
            metric_keys = ['heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low', 'stress', 'step', 'calorie']
            
            for metric in metric_keys:
                values = []
                anomaly_points = []
                
                for i, item in enumerate(sorted_data):
                    # 检查新格式和旧格式的字段名
                    value = self._safe_float(item.get(metric) or item.get(metric.replace('_', '').replace('heart_rate', 'heartRate').replace('blood_oxygen', 'bloodOxygen').replace('pressure_high', 'pressureHigh').replace('pressure_low', 'pressureLow')))
                    
                    if value > 0:
                        values.append(value)
                        
                        # 检查是否是异常值
                        if metric in self.baseline:
                            min_normal, max_normal = self.baseline[metric]['normal_range']
                            if value < min_normal or value > max_normal:
                                anomaly_points.append({
                                    'timestamp': timestamps[i],
                                    'value': value,
                                    'type': 'high' if value > max_normal else 'low'
                                })
                    else:
                        values.append(None)  # 保持时间序列完整性
                
                if any(v is not None for v in values):  # 只添加有数据的指标
                    metrics[metric] = values
                    if anomaly_points:
                        anomalies[metric] = anomaly_points
            
            return {
                'timestamps': timestamps,
                'metrics': metrics,
                'anomalies': anomalies
            }
        except Exception as e:
            print(f"Error building time series data: {e}")
            return {
                'timestamps': [],
                'metrics': {},
                'anomalies': {}
            }

def enhance_health_analysis(health_data_list):
    """增强版健康数据分析"""
    analyzer = HealthDataAnalyzer(health_data_list)
    
    # 计算健康分析
    analysis_result = analyzer.analyze_data()
    if not analysis_result['success']:
        return analysis_result
        
    health_data = analysis_result['data']
    
    # 计算部门基线
    dept_baselines = {}
    for data in health_data_list:
        dept_name = data['deptName']
        if dept_name not in dept_baselines:
            dept_baselines[dept_name] = {
                'profiles': [],
                'averageScores': {
                    'heartRate': 0,
                    'bloodOxygen': 0,
                    'temperature': 0,
                    'pressureHigh': 0,
                    'pressureLow': 0,
                    'step': 0,
                    'calorie': 0
                }
            }
        dept_baselines[dept_name]['profiles'].append(data)
    
    # 计算部门平均分
    for dept, data in dept_baselines.items():
        profiles = data['profiles']
        if profiles:
            dept_baselines[dept]['averageScores'] = {
                'heartRate': sum(float(p.get('heartRate', 0)) for p in profiles) / len(profiles),
                'bloodOxygen': sum(float(p.get('bloodOxygen', 0)) for p in profiles) / len(profiles),
                'temperature': sum(float(p.get('temperature', 0)) for p in profiles) / len(profiles),
                'pressureHigh': sum(float(p.get('pressureHigh', 0)) for p in profiles) / len(profiles),
                'pressureLow': sum(float(p.get('pressureLow', 0)) for p in profiles) / len(profiles),
                'step': sum(float(p.get('step', 0)) for p in profiles) / len(profiles),
                'calorie': sum(float(p.get('calorie', 0)) for p in profiles) / len(profiles)
            }

    return {
        'success': True,
        'data': {
            'healthAnalysis': health_data,
            'departmentBaselines': dept_baselines
        }
    }

class HealthTrendAnalyzer:
    """健康趋势分析器"""
    def __init__(self, health_data_list: List[Dict[str, Any]]):
        if not health_data_list:
            raise ValueError("Empty health data list")
            
        print(f"初始化 HealthTrendAnalyzer，数据条数: {len(health_data_list)}")  # 调试信息
        
        self.health_data_list = sorted(
            health_data_list,
            key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
        )
        
        print(f"数据时间范围: {self.health_data_list[0]['timestamp']} 到 {self.health_data_list[-1]['timestamp']}")  # 调试信息
        
        # 更新指标定义
        self.metrics = {
            'heartRate': {
                'name': '心率',
                'unit': 'bpm',
                'normal_range': (60, 100),
                'weight': 0.15,
                'importance': 'high'
            },
            'bloodOxygen': {
                'name': '血氧',
                'unit': '%',
                'normal_range': (95, 100),
                'weight': 0.15,
                'importance': 'high'
            },
            'temperature': {
                'name': '体温',
                'unit': '°C',
                'normal_range': (36.3, 37.2),
                'weight': 0.15,
                'importance': 'high'
            },
            'pressureHigh': {
                'name': '收缩压',
                'unit': 'mmHg',
                'normal_range': (90, 140),
                'weight': 0.15,
                'importance': 'high'
            },
            'pressureLow': {
                'name': '舒张压',
                'unit': 'mmHg',
                'normal_range': (60, 90),
                'weight': 0.15,
                'importance': 'high'
            },
            'stress': {
                'name': '压力指数',
                'unit': '',
                'normal_range': (0, 70),
                'weight': 0.1,
                'importance': 'medium'
            },
            'step': {
                'name': '步数',
                'unit': '步',
                'normal_range': (6000, 10000),
                'weight': 0.075,
                'importance': 'medium'
            },
            'calorie': {
                'name': '消耗热量',
                'unit': 'kcal',
                'normal_range': (200, 600),
                'weight': 0.075,
                'importance': 'medium'
            }
        }

    def analyze_time_series(self) -> Dict[str, Any]:
        """分析时间序列数据"""
        try:
            print("开始分析时间序列数据...")
            
            # 初始化时间序列数据结构
            time_series = {
                'timestamps': [],
                'metrics': {metric: [] for metric in self.metrics},
                'anomalies': {metric: [] for metric in self.metrics},
                'trends': {}
            }
            
            # 收集时间序列数据
            for data in self.health_data_list:
                timestamp = data.get('timestamp')
                if not timestamp:
                    continue
                
                time_series['timestamps'].append(timestamp)
                
                # 处理每个指标的数据
                for metric in self.metrics:
                    value = self._safe_float(data.get(metric))
                    time_series['metrics'][metric].append(value)
                    
                    # 检测异常值
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
            
            print("时间序列分析完成")
            return time_series
            
        except Exception as e:
            print(f"时间序列分析错误: {str(e)}")
            return None

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """计算趋势"""
        try:
            first_val = values[0]
            last_val = values[-1]
            change_rate = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
            
            # 使用简单线性回归计算趋势
            x = np.arange(len(values))
            slope, _ = np.polyfit(x, values, 1)
            
            # 确定趋势方向
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
            print(f"计算趋势错误: {str(e)}")
            return {
                'direction': "未知",
                'change_rate': 0,
                'significance': "low"
            }

    def calculate_health_scores(self) -> Dict[str, Any]:
        """计算健康分数"""
        try:
            print("开始计算健康分数...")  # 调试信息
            
            scores = {
                'overall': 0,
                'factors': {},
                'details': {}
            }
            
            total_weighted_score = 0
            total_weight = 0
            valid_metrics_count = 0
            
            for metric, info in self.metrics.items():
                try:
                    values = []
                    for data in self.health_data_list:
                        value = self._safe_float(data.get(metric))
                        if value > 0:
                            values.append(value)
                    
                    if not values:
                        print(f"指标 {metric} 没有有效值")
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
                    valid_metrics_count += 1
                    
                    # 存储分数
                    scores['factors'][metric] = {
                        'name': info['name'],
                        'score': round(final_score, 1),
                        'weight': weight,
                        'unit': info['unit'],
                        'currentValue': round(current_value, 1),
                        'normalRange': info['normal_range'],
                        'status': self._get_status_level(final_score)
                    }
                    
                    # 存储详细信息
                    status = self._get_value_status(current_value, min_val, max_val)
                    scores['details'][metric] = {
                        'status': status,
                        'message': self._generate_metric_message(info['name'], current_value, info['unit'], min_val, max_val),
                        'score': round(final_score, 1),
                        'suggestions': self._get_metric_suggestions(metric, status)
                    }
                    
                    print(f"指标 {metric} 计算完成: 分数={final_score}, 状态={status}")
                    
                except Exception as e:
                    print(f"计算指标 {metric} 分数时出错: {str(e)}")
                    continue
            
            if valid_metrics_count > 0 and total_weight > 0:
                overall_score = round(total_weighted_score / total_weight, 1)
                scores['overall'] = overall_score
                scores['overallStatus'] = self._get_overall_status(overall_score)
                print(f"总体健康分数: {overall_score}")
                return scores
            else:
                print("没有有效的指标数据用于计算总分")
                return None
            
        except Exception as e:
            print(f"计算健康分数时出错: {str(e)}")
            return None

    def _safe_float(self, value) -> float:
        """安全地转换为浮点数，避免NaN和Infinity"""
        try:
            if value is None or value == '' or value == 'None':
                return 0.0
            
            float_val = float(value)
            
            # 检查NaN和无穷大
            if math.isnan(float_val) or math.isinf(float_val):
                return 0.0
                
            return float_val
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
            'heartRate': {
                'high': ['保持情绪稳定', '避免剧烈运动', '规律作息'],
                'low': ['适度运动', '保持充足睡眠', '注意保暖'],
                'normal': ['保持规律运动', '维持健康作息']
            },
            'bloodOxygen': {
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
            'pressureHigh': {
                'high': ['限制盐分摄入', '保持心情舒畅', '规律作息', '必要时就医'],
                'low': ['适当补充盐分', '多休息', '必要时就医'],
                'normal': ['保持健康饮食', '规律运动', '避免熬夜']
            },
            'pressureLow': {
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
    
    def generate_visualization_data(self):
        """生成大屏可视化数据"""
        try:
            if not self.health_data_list:
                return {
                    'success': False,
                    'error': '没有可用的健康数据'
                }

            print("开始生成移动端数据...")  # 调试信息
            
            # 计算健康分数
            health_scores = self.calculate_health_scores()
            if not health_scores:
                print("健康分数计算失败")  # 调试信息
                return {
                    'success': False,
                    'error': '健康分数计算失败'
                }

            print(f"计算得到的健康分数: {health_scores}")  # 调试信息

            # 构建响应数据
            response_data = {
                'success': True,
                'data': {
                    'summary': {
                        'totalRecords': len(self.health_data_list),
                        'startTime': self.health_data_list[0].get('timestamp', ''),
                        'endTime': self.health_data_list[-1].get('timestamp', ''),
                        'healthScore': health_scores['overall'],
                        'healthStatus': health_scores['overallStatus'],
                        'lastUpdateTime': self.health_data_list[-1].get('timestamp', '')
                    },
                    'healthScores': health_scores
                }
            }

            print("数据生成完成")  # 调试信息
            return response_data

        except Exception as e:
            print(f"生成数据时出错: {str(e)}")  # 调试信息
            return {
                'success': False,
                'error': f'数据处理失败: {str(e)}'
            }
    def generate_mobile_visualization_data(self):
        """生成移动端可视化数据"""
        try:
            if not self.health_data_list:
                return {
                    'success': False,
                    'error': '没有可用的健康数据'
                }

            print("开始生成移动端数据...")  # 调试信息
            
            # 计算健康分数
            health_scores = self.calculate_health_scores()
            if not health_scores:
                print("健康分数计算失败")  # 调试信息
                return {
                    'success': False,
                    'error': '健康分数计算失败'
                }

            print(f"计算得到的健康分数: {health_scores}")  # 调试信息

            # 构建响应数据
            response_data = {
                'success': True,
                'data': {
                    'summary': {
                        'totalRecords': len(self.health_data_list),
                        'startTime': self.health_data_list[0].get('timestamp', ''),
                        'endTime': self.health_data_list[-1].get('timestamp', ''),
                        'healthScore': health_scores['overall'],
                        'healthStatus': health_scores['overallStatus'],
                        'lastUpdateTime': self.health_data_list[-1].get('timestamp', '')
                    },
                    'healthScores': health_scores
                }
            }

            print("数据生成完成")  # 调试信息
            return response_data

        except Exception as e:
            print(f"生成数据时出错: {str(e)}")  # 调试信息
            return {
                'success': False,
                'error': f'数据处理失败: {str(e)}'
            }

def analyze_health_trends(health_data_list: List[Dict[str, Any]]):
    """分析健康趋势并生成可视化数据"""
    try:
        if not health_data_list:
            return {
                'success': False,
                'error': 'Empty health data list'
            }

        analyzer = HealthTrendAnalyzer(health_data_list)
        return analyzer.generate_visualization_data()

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 