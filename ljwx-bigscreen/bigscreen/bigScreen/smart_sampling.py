"""
智能健康数据采样策略
优雅解决大数据量分析性能问题
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math

class HealthDataSampler:
    """健康数据智能采样器"""
    
    def __init__(self, target_size: int = 5000):
        """
        初始化采样器
        Args:
            target_size: 目标采样数据量，默认5000条
        """
        self.target_size = target_size
        
    def smart_sample(self, health_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        智能采样策略：
        1. 数据量 <= 目标量：返回全部数据
        2. 数据量 > 目标量：使用分层时间采样
        3. 保证重要时间点（如异常值）不被丢失
        """
        total_count = len(health_data_list)
        
        if total_count <= self.target_size:
            print(f"📊 数据量({total_count})在合理范围内，无需采样")
            return health_data_list
        
        print(f"📊 执行智能采样: {total_count} -> {self.target_size}")
        
        # 按时间排序
        sorted_data = sorted(health_data_list, key=lambda x: x.get('timestamp', ''))
        
        # 策略1: 时间分层采样
        sampled_data = self._time_stratified_sampling(sorted_data)
        
        # 策略2: 保留异常值
        sampled_data = self._preserve_anomalies(sorted_data, sampled_data)
        
        # 策略3: 均匀时间分布
        sampled_data = self._ensure_time_distribution(sorted_data, sampled_data)
        
        print(f"✅ 采样完成: {len(sampled_data)} 条数据")
        return sampled_data
    
    def _time_stratified_sampling(self, sorted_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分层时间采样：每个时间段采样相同比例"""
        try:
            if not sorted_data:
                return []
            
            # 计算采样比例
            sample_ratio = min(1.0, self.target_size / len(sorted_data))
            
            # 按天分组
            daily_groups = {}
            for data in sorted_data:
                timestamp = data.get('timestamp', '')
                if timestamp:
                    date_key = timestamp[:10]  # YYYY-MM-DD
                    if date_key not in daily_groups:
                        daily_groups[date_key] = []
                    daily_groups[date_key].append(data)
            
            # 每天采样
            sampled_data = []
            for date_key, daily_data in daily_groups.items():
                daily_sample_size = max(1, int(len(daily_data) * sample_ratio))
                daily_sample = random.sample(daily_data, min(daily_sample_size, len(daily_data)))
                sampled_data.extend(daily_sample)
                
            return sampled_data
            
        except Exception as e:
            print(f"⚠️ 分层采样失败: {e}")
            # 回退到简单随机采样
            return random.sample(sorted_data, min(self.target_size, len(sorted_data)))
    
    def _preserve_anomalies(self, original_data: List[Dict[str, Any]], sampled_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保留异常值：确保重要的异常数据点被包含"""
        try:
            # 定义异常检测规则
            anomaly_rules = {
                'heart_rate': (40, 150),      # 心率异常范围
                'blood_oxygen': (85, 100),    # 血氧异常范围  
                'temperature': (35.0, 38.5),  # 体温异常范围
                'pressure_high': (70, 180),   # 收缩压异常范围
                'pressure_low': (40, 110)     # 舒张压异常范围
            }
            
            # 找出异常值
            anomalies = []
            for data in original_data:
                is_anomaly = False
                for field, (min_val, max_val) in anomaly_rules.items():
                    value = self._safe_float(data.get(field))
                    if value > 0 and (value < min_val or value > max_val):
                        is_anomaly = True
                        break
                
                if is_anomaly:
                    anomalies.append(data)
            
            if anomalies:
                # 将异常值添加到采样数据中（去重）
                sampled_timestamps = {d.get('timestamp') for d in sampled_data}
                for anomaly in anomalies[:100]:  # 最多添加100个异常值
                    if anomaly.get('timestamp') not in sampled_timestamps:
                        sampled_data.append(anomaly)
                        
                print(f"🚨 保留 {min(len(anomalies), 100)} 个异常值")
            
            return sampled_data
            
        except Exception as e:
            print(f"⚠️ 异常值保留失败: {e}")
            return sampled_data
    
    def _ensure_time_distribution(self, original_data: List[Dict[str, Any]], sampled_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确保时间分布均匀：补充时间空白区域的数据"""
        try:
            if not original_data or not sampled_data:
                return sampled_data
            
            # 计算时间范围
            start_time = datetime.strptime(original_data[0]['timestamp'], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(original_data[-1]['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # 按小时分组检查覆盖度
            total_hours = int((end_time - start_time).total_seconds() / 3600) + 1
            sampled_hours = set()
            
            for data in sampled_data:
                timestamp = data.get('timestamp', '')
                if timestamp:
                    hour_key = timestamp[:13]  # YYYY-MM-DD HH
                    sampled_hours.add(hour_key)
            
            coverage = len(sampled_hours) / max(total_hours, 1)
            
            # 如果时间覆盖度不足60%，补充数据
            if coverage < 0.6:
                additional_needed = int(self.target_size * 0.1)  # 补充10%数据
                
                # 找出未覆盖的时间段
                all_hours = set()
                current = start_time
                while current <= end_time:
                    all_hours.add(current.strftime('%Y-%m-%d %H'))
                    current += timedelta(hours=1)
                
                missing_hours = all_hours - sampled_hours
                
                # 从缺失时间段补充数据
                additional_data = []
                for data in original_data:
                    timestamp = data.get('timestamp', '')
                    if timestamp and timestamp[:13] in missing_hours:
                        additional_data.append(data)
                        if len(additional_data) >= additional_needed:
                            break
                
                sampled_data.extend(additional_data)
                print(f"⏰ 补充时间覆盖度: {coverage:.1%} -> {len(sampled_hours + {d['timestamp'][:13] for d in additional_data}) / total_hours:.1%}")
            
            return sampled_data
            
        except Exception as e:
            print(f"⚠️ 时间分布优化失败: {e}")
            return sampled_data
    
    def _safe_float(self, value) -> float:
        """安全转换浮点数"""
        try:
            if value is None or value == '' or value == 'None':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0

def optimize_health_data_size(health_data_list: List[Dict[str, Any]], 
                             target_size: int = 5000) -> List[Dict[str, Any]]:
    """
    优化健康数据大小的便捷函数
    
    Args:
        health_data_list: 原始健康数据列表
        target_size: 目标数据量
        
    Returns:
        优化后的健康数据列表
    """
    sampler = HealthDataSampler(target_size)
    return sampler.smart_sample(health_data_list)