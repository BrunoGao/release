import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
import json
from functools import lru_cache

class DeepseekHealthAnalyzer:
    def __init__(self, health_data_list: List[Dict[str, Any]]):
        if not health_data_list:
            raise ValueError("Empty health data list")
            
        self.health_data_list = sorted(
            health_data_list,
            key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
        )
        
        # 定义健康指标基线值（与原始分析器相同）
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

# 1. 添加超时设置
def _call_deepseek(self, prompt: str) -> Dict:
    try:
        url = "http://192.168.1.83:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "lingjingwanxiang:70b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        # 添加超时设置
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return json.loads(result['response'])
    except requests.Timeout:
        print("调用 deepseek-r1 超时")
        return None
    except Exception as e:
        print(f"调用 deepseek-r1 失败: {str(e)}")
        return None

# 2. 添加重试机制
def _call_deepseek_with_retry(self, prompt: str, max_retries: int = 3) -> Dict:
    for attempt in range(max_retries):
        result = self._call_deepseek(prompt)
        if result is not None:
            return result
        print(f"重试第 {attempt + 1} 次")
    return None

# 3. 添加缓存机制
from functools import lru_cache

@lru_cache(maxsize=100)
def _call_deepseek_cached(self, prompt: str) -> Dict:
    return self._call_deepseek(prompt)

def analyze_time_series(self) -> Dict[str, Any]:
        """使用 deepseek-r1 分析时间序列数据"""
        try:
            # 准备数据
            data_for_analysis = {
                'metrics': {},
                'timestamps': []
            }
            
            for metric in self.metrics:
                data_for_analysis['metrics'][metric] = []
            
            for data in self.health_data_list:
                data_for_analysis['timestamps'].append(data.get('timestamp'))
                for metric in self.metrics:
                    value = self._safe_float(data.get(metric))
                    data_for_analysis['metrics'][metric].append(value)
            
            # 构建 prompt
            prompt = f"""
            作为一个专业的健康数据分析专家，请分析以下健康数据的时间序列趋势：
            
            数据：{json.dumps(data_for_analysis, ensure_ascii=False)}
            
            请提供以下JSON格式的分析结果：
            1. 每个指标的趋势方向（上升/下降/稳定）
            2. 变化率
            3. 趋势显著性（high/medium/low）
            4. 异常值检测
            
            返回格式示例：
            {{
                "trends": {{
                    "metric_name": {{
                        "direction": "上升/下降/稳定",
                        "change_rate": 数值,
                        "significance": "high/medium/low"
                    }}
                }},
                "anomalies": {{
                    "metric_name": [
                        {{
                            "timestamp": "时间戳",
                            "value": 数值,
                            "type": "high/low"
                        }}
                    ]
                }}
            }}
            """
            
            result = self._call_deepseek(prompt)
            if not result:
                return self._fallback_time_series_analysis()
                
            return result
            
        except Exception as e:
            print(f"时间序列分析错误: {str(e)}")
            return self._fallback_time_series_analysis()

def calculate_health_scores(self) -> Dict[str, Any]:
        """使用 deepseek-r1 计算健康分数"""
        try:
            # 准备最新数据
            latest_data = {metric: self._safe_float(self.health_data_list[-1].get(metric)) 
                          for metric in self.metrics}
            
            # 构建 prompt
            prompt = f"""
            作为一个专业的健康数据分析专家，请根据以下健康数据计算综合健康评分：

            当前数据：{json.dumps(latest_data, ensure_ascii=False)}
            
            指标参考范围：{json.dumps(self.metrics, ensure_ascii=False)}
            
            请提供以下JSON格式的分析结果：
            {{
                "overall": 总分（0-100）,
                "factors": {{
                    "指标名": {{
                        "name": "中文名称",
                        "score": 分数,
                        "weight": 权重,
                        "unit": "单位",
                        "currentValue": 当前值,
                        "normalRange": [最小值, 最大值],
                        "status": "状态级别"
                    }}
                }},
                "details": {{
                    "指标名": {{
                        "status": "状态",
                        "message": "评估信息",
                        "score": 分数,
                        "suggestions": ["建议1", "建议2"]
                    }}
                }},
                "overallStatus": {{
                    "level": "状态级别",
                    "score": 分数,
                    "message": "总体评估信息",
                    "color": "颜色代码"
                }}
            }}
            """
            
            result = self._call_deepseek(prompt)
            if not result:
                return self._fallback_health_scores()
                
            return result
            
        except Exception as e:
            print(f"计算健康分数时出错: {str(e)}")
            return self._fallback_health_scores()

def _fallback_time_series_analysis(self) -> Dict[str, Any]:
        """当 deepseek-r1 调用失败时的后备分析方法"""
        analyzer = HealthDapingAnalyzer(self.health_data_list)
        return analyzer.analyze_time_series()

def _fallback_health_scores(self) -> Dict[str, Any]:
        """当 deepseek-r1 调用失败时的后备评分方法"""
        analyzer = HealthDapingAnalyzer(self.health_data_list)
        return analyzer.calculate_health_scores()

def _safe_float(self, value) -> float:
        """安全地转换为浮点数"""
        try:
            if value is None or value == '' or value == 'None':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
def analyze_health_trends(health_data_list: List[Dict[str, Any]]):
    """使用 deepseek-r1 分析健康趋势并生成可视化数据"""
    try:
        if not health_data_list:
            return {
                'success': False,
                'error': 'Empty health data list'
            }

        analyzer = DeepseekHealthAnalyzer(health_data_list)
        
        # 计算健康分数
        health_scores = analyzer.calculate_health_scores()
        if not health_scores:
            return {
                'success': False,
                'error': '健康分数计算失败'
            }

        # 分析时间序列数据
        time_series = analyzer.analyze_time_series()
        if not time_series:
            return {
                'success': False,
                'error': '时间序列分析失败'
            }

        return {
            'success': True,
            'data': {
                'summary': {
                    'totalRecords': len(health_data_list),
                    'timeRange': {
                        'start': health_data_list[0].get('timestamp', ''),
                        'end': health_data_list[-1].get('timestamp', '')
                    },
                    'overallScore': health_scores['overall'],
                    'status': health_scores['overallStatus']
                },
                'healthScores': health_scores,
                'timeSeriesData': time_series
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        
def test_deepseek_analyzer():
    # 准备测试数据
    test_data = [
        {
            "timestamp": "2024-03-20 10:00:00",
            "heartRate": "75",
            "bloodOxygen": "98",
            "temperature": "36.5",
            "pressureHigh": "120",
            "pressureLow": "80",
            "stress": "50",
            "step": "10000",
            "calorie": "200",
            "sleep": "8"
        },
        {
            "timestamp": "2024-03-20 10:00:00",
            "heartRate": "78",
            "bloodOxygen": "99",
            "temperature": "36.6",
            "pressureHigh": "121",
            "pressureLow": "81",
            "stress": "51",
            "step": "10001",
            "calorie": "201",
            "sleep": "8.1"
        }
        # ... 更多测试数据
    ]
    
    # 创建分析器实例
    analyzer = DeepseekHealthAnalyzer(test_data)
    
    # 测试时间序列分析
    time_series = analyzer.analyze_time_series()
    assert time_series is not None
    
    # 测试健康评分计算
    scores = analyzer.calculate_health_scores()
    assert scores is not None
    
    # 测试完整分析流程
    result = analyze_health_trends(test_data)
    assert result['success'] is True
class HealthDapingAnalyzer:
    def __init__(self, health_data_list: List[Dict[str, Any]]):
        if not health_data_list:
            raise ValueError("Empty health data list")
            
        self.health_data_list = sorted(
            health_data_list,
            key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
        )
        
        # 定义健康指标基线值
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
            time_series = {
                'timestamps': [],
                'metrics': {metric: [] for metric in self.metrics},
                'anomalies': {metric: [] for metric in self.metrics},
                'trends': {}
            }
            
            for data in self.health_data_list:
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
            print(f"时间序列分析错误: {str(e)}")
            return None

    def calculate_health_scores(self) -> Dict[str, Any]:
        """计算健康分数"""
        try:
            scores = {
                'overall': 0,
                'factors': {},
                'details': {}
            }
            
            total_weighted_score = 0
            total_weight = 0
            
            for metric, info in self.metrics.items():
                try:
                    values = []
                    for data in self.health_data_list:
                        value = self._safe_float(data.get(metric))
                        if value > 0:
                            values.append(value)
                    
                    if not values:
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
                    
                except Exception as e:
                    print(f"计算指标 {metric} 分数时出错: {str(e)}")
                    continue
            
            if total_weight > 0:
                overall_score = round(total_weighted_score / total_weight, 1)
                scores['overall'] = overall_score
                scores['overallStatus'] = self._get_overall_status(overall_score)
            
            return scores
            
        except Exception as e:
            print(f"计算健康分数时出错: {str(e)}")
            return None

    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
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
            print(f"计算趋势错误: {str(e)}")
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

def analyze_health_trends(health_data_list: List[Dict[str, Any]]):
    """分析健康趋势并生成可视化数据"""
    try:
        if not health_data_list:
            return {
                'success': False,
                'error': 'Empty health data list'
            }

        analyzer = HealthDapingAnalyzer(health_data_list)
        
        # 计算健康分数
        health_scores = analyzer.calculate_health_scores()
        if not health_scores:
            return {
                'success': False,
                'error': '健康分数计算失败'
            }

        # 分析时间序列数据
        time_series = analyzer.analyze_time_series()
        if not time_series:
            return {
                'success': False,
                'error': '时间序列分析失败'
            }

        return {
            'success': True,
            'data': {
                'summary': {
                    'totalRecords': len(health_data_list),
                    'timeRange': {
                        'start': health_data_list[0].get('timestamp', ''),
                        'end': health_data_list[-1].get('timestamp', '')
                    },
                    'overallScore': health_scores['overall'],
                    'status': health_scores['overallStatus']
                },
                'healthScores': health_scores,
                'timeSeriesData': time_series
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 