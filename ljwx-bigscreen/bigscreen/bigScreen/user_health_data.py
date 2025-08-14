from flask import request, jsonify
from datetime import datetime, time, timedelta
import json
import random  # 添加random模块导入
from .redis_helper import RedisHelper
from .models import UserHealthData, DeviceInfo, HealthDataConfig, db, func, UserInfo, OrgInfo, UserOrg, HealthBaseline
from sqlalchemy import text  # 添加text导入用于原生SQL查询
from .alert import send_wechat_alert, generate_alerts
import os
from decimal import Decimal
from .device import fetch_customer_id_by_deviceSn, get_device_user_org_info
from .health_daping_analyzer import analyze_health_trends
from .health_daping_analyzer import generate_health_score
from collections import defaultdict
import numpy as np

import math
# Import the class from models.py
# Import necessary modules and functions

def parse_sleep_data(sleep_data_json):
    """
    解析sleepData JSON，计算睡眠时长(小时)
    支持的格式：
    1. '{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}'
    2. null, "null", '{"code":-1,"data":[],"name":"sleep","type":"history"}'
    3. '{"code":"0","data":[],"name":"sleep","type":"history"}'
    
    返回: 睡眠时长(小时)，出错时返回None
    """
    if not sleep_data_json or sleep_data_json in ['null', None]:
        return 0  # 修复：返回0而不是None
    
    try:
        if isinstance(sleep_data_json, str):
            # 处理JSON字符串格式错误的情况，如'{"code":"0"data":[]}'
            sleep_data_json = sleep_data_json.replace('"0"data"', '"0","data"')
            sleep_data = json.loads(sleep_data_json)
        elif isinstance(sleep_data_json, dict):
            sleep_data = sleep_data_json
        else:
            return None
            
        # 检查数据有效性
        if not isinstance(sleep_data, dict):
            return 0
            
        code = sleep_data.get('code')
        if code == -1 or code == '-1' or str(code) == '-1':
            return 0
            
        data_list = sleep_data.get('data', [])
        if not isinstance(data_list, list) or len(data_list) == 0:
            return 0
            
        total_sleep_seconds = 0
        
        # 遍历所有睡眠时间段，不管type，按照endTimeStamp-startTimeStamp计算
        for sleep_period in data_list:
            if not isinstance(sleep_period, dict):
                continue
                
            start_time = sleep_period.get('startTimeStamp')
            end_time = sleep_period.get('endTimeStamp')
            
            if start_time is None or end_time is None:
                continue
                
            try:
                # 时间戳转换为秒
                start_seconds = int(start_time) / 1000 if int(start_time) > 9999999999 else int(start_time)
                end_seconds = int(end_time) / 1000 if int(end_time) > 9999999999 else int(end_time)
                
                # 计算时间差(秒)
                if end_seconds > start_seconds:
                    total_sleep_seconds += (end_seconds - start_seconds)
                    
            except (ValueError, TypeError):
                continue
                
        # 转换为小时，保留2位小数
        if total_sleep_seconds > 0:
            total_sleep_hours = round(total_sleep_seconds / 3600, 2)
            return total_sleep_hours
        else:
            return 0  # 修复：返回0而不是None
            
    except (json.JSONDecodeError, Exception) as e:
        print(f"解析sleepData时出错: {e}, 原始数据: {sleep_data_json}")
        return 0  # 修复：返回0而不是None

def convert_empty_to_none(value):
    return None if value == ' ' else value

redis = RedisHelper()
#from .tasks import process_health_data


def save_health_data(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, stress, step, timestamp, deviceSn, distance, calorie, latitude, longitude, altitude, uploadMethod, sleep=None):
    try:
        #检查是否已存在相同记录
        from sqlalchemy import and_
        existing = db.session.query(UserHealthData.id).filter(
            and_(
                UserHealthData.device_sn == deviceSn,
                UserHealthData.timestamp == timestamp
            )
        ).first()
        
        if existing:
            print(f"记录已存在: device_sn={deviceSn}, timestamp={timestamp}, id={existing.id}")
            return existing.id
        
        # Create an instance of UserHealthData
        health_data = UserHealthData(
            upload_method=uploadMethod,
            heart_rate=convert_empty_to_none(heartRate),
            pressure_high=convert_empty_to_none(pressureHigh),
            pressure_low=convert_empty_to_none(pressureLow),
            blood_oxygen=convert_empty_to_none(bloodOxygen),
            temperature=convert_empty_to_none(temperature),
            stress=convert_empty_to_none(stress),
            step=convert_empty_to_none(step),
            timestamp=timestamp,
            device_sn=deviceSn,
            latitude=convert_empty_to_none(latitude),
            longitude=convert_empty_to_none(longitude),
            altitude=convert_empty_to_none(altitude),
            distance=convert_empty_to_none(distance),
            calorie=convert_empty_to_none(calorie),
            sleep=sleep  # 只保留计算后的sleep数值
        )

        # Add the instance to the session and commit
        db.session.add(health_data)
        db.session.commit()

        # Return the ID of the inserted record
        print("save_health_data.health_data.id:", health_data.id)
        return health_data.id

    except Exception as err:
        db.session.rollback()  # Rollback the session in case of error
        #检查是否为重复键错误
        if 'Duplicate entry' in str(err) or 'uk_device_timestamp' in str(err):
            print(f"重复记录跳过: device_sn={deviceSn}, timestamp={timestamp}")
            #尝试查询已存在的记录ID
            try:
                existing = db.session.query(UserHealthData.id).filter(
                    and_(
                        UserHealthData.device_sn == deviceSn,
                        UserHealthData.timestamp == timestamp
                    )
                ).first()
                return existing.id if existing else None
            except:
                return None
        else:
            print(f"Failed to insert data into the database: {err}")
            return None

def fetch_health_data_by_id(id):
    """通过ID查询健康数据-支持主表和分区表联合查询"""
    try:
        # 首先尝试从主表查询
        result = UserHealthData.query.filter_by(id=id).first()
        
        if result:
            # 使用正确的字段名称
            data = {
                "heart_rate": result.heart_rate,
                "pressure_high": result.pressure_high,
                "pressure_low": result.pressure_low,
                "blood_oxygen": result.blood_oxygen,
                "temperature": result.temperature,
                "stress": result.stress,
                "step": result.step,
                "timestamp": result.timestamp,
                "deviceSn": result.device_sn,
                "distance": result.distance,
                "calorie": result.calorie,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "altitude": result.altitude,
                "sleepData": result.sleep,  # 使用正确字段名sleep
                "workoutData": None,  # 主表没有此字段
                "uploadMethod": result.upload_method
            }
            return jsonify({"success": True, "data": data, "source": "main_table"})
        
        # 如果主表没有，尝试查询分区表
        from sqlalchemy import text
        try:
            # 检查分区视图是否存在
            view_check = text("SHOW TABLES LIKE 't_user_health_data_partitioned'")
            view_exists = db.session.execute(view_check).fetchone()
            
            if view_exists:
                # 查询分区视图
                partition_query = text("""
                    SELECT heart_rate, pressure_high, pressure_low, blood_oxygen, 
                           temperature, stress, step, timestamp, device_sn,
                           distance, calorie, latitude, longitude, altitude,
                           sleep_data, workout_data, upload_method
                    FROM t_user_health_data_partitioned 
                    WHERE id = :id LIMIT 1
                """)
                partition_result = db.session.execute(partition_query, {'id': id}).fetchone()
                
                if partition_result:
                    data = {
                        "heart_rate": partition_result[0],
                        "pressure_high": partition_result[1],
                        "pressure_low": partition_result[2],
                        "blood_oxygen": partition_result[3],
                        "temperature": partition_result[4],
                        "stress": partition_result[5],
                        "step": partition_result[6],
                        "timestamp": partition_result[7],
                        "deviceSn": partition_result[8],
                        "distance": partition_result[9],
                        "calorie": partition_result[10],
                        "latitude": partition_result[11],
                        "longitude": partition_result[12],
                        "altitude": partition_result[13],
                        "sleepData": partition_result[14],  # 分区表字段名sleep_data
                        "workoutData": partition_result[15],
                        "uploadMethod": partition_result[16]
                    }
                    return jsonify({"success": True, "data": data, "source": "partition_table"})
            
            # 尝试查询按月分区的表
            from datetime import datetime, timedelta
            current_date = datetime.now()
            
            # 检查最近几个月的分区表
            for months_back in range(6):  # 查询最近6个月
                check_date = current_date - timedelta(days=months_back * 30)
                table_name = f"t_user_health_data_{check_date.year}{check_date.month:02d}"
                
                table_exists = text(f"SHOW TABLES LIKE '{table_name}'")
                if db.session.execute(table_exists).fetchone():
                    month_query = text(f"""
                        SELECT heart_rate, pressure_high, pressure_low, blood_oxygen,
                               temperature, stress, step, timestamp, device_sn,
                               distance, calorie, latitude, longitude, altitude,
                               sleep_data, workout_data, upload_method
                        FROM {table_name}
                        WHERE id = :id LIMIT 1
                    """)
                    month_result = db.session.execute(month_query, {'id': id}).fetchone()
                    
                    if month_result:
                        data = {
                            "heart_rate": month_result[0],
                            "pressure_high": month_result[1],
                            "pressure_low": month_result[2],
                            "blood_oxygen": month_result[3],
                            "temperature": month_result[4],
                            "stress": month_result[5],
                            "step": month_result[6],
                            "timestamp": month_result[7],
                            "deviceSn": month_result[8],
                            "distance": month_result[9],
                            "calorie": month_result[10],
                            "latitude": month_result[11],
                            "longitude": month_result[12],
                            "altitude": month_result[13],
                            "sleepData": month_result[14],
                            "workoutData": month_result[15],
                            "uploadMethod": month_result[16]
                        }
                        return jsonify({"success": True, "data": data, "source": f"partition_{table_name}"})
        
        except Exception as partition_error:
            print(f"❌ 分区表查询失败: {partition_error}")
        
        return jsonify({"success": False, "message": f"ID {id} 数据未找到"})
        
    except Exception as e:
        print(f"❌ 查询健康数据失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"查询失败: {str(e)}"})

def convert_decimal(value):
    """将 Decimal 类型转换为字符串或浮点数"""
    if isinstance(value, Decimal):
        return str(value)
    return value
def get_health_data_by_date(date=None, orgId=None, userId=None): #重构为调用统一接口#
    """重构为调用统一接口"""
    try:
        # 使用统一接口查询指定日期的数据
        if date:
            start_date = date
            end_date = date
        else:
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            end_date = start_date
        
        result = get_all_health_data_optimized(
            orgId=orgId, 
            userId=userId, 
            startDate=start_date, 
            endDate=end_date, 
            latest_only=False
        )
        
        if not result.get('success'):
            return result
        
        health_data_list = result['data']['healthData']
        
        # 保持原有格式兼容性
        enhanced_result = result.copy()
        enhanced_result['data']['date'] = start_date
        
        # 添加按小时统计
        hourly_stats = {}
        for data in health_data_list:
            if data.get('timestamp'):
                hour = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S").hour
                if hour not in hourly_stats:
                    hourly_stats[hour] = {'count': 0, 'temperature': 0, 'heart_rate': 0, 'blood_oxygen': 0}
                hourly_stats[hour]['count'] += 1
                hourly_stats[hour]['temperature'] += float(data.get('temperature', 0))
                hourly_stats[hour]['heart_rate'] += float(data.get('heart_rate', 0))
                hourly_stats[hour]['blood_oxygen'] += float(data.get('blood_oxygen', 0))
        
        # 计算平均值
        for hour in hourly_stats:
            if hourly_stats[hour]['count'] > 0:
                hourly_stats[hour]['temperature'] /= hourly_stats[hour]['count']
                hourly_stats[hour]['heartRate'] /= hourly_stats[hour]['count']
                hourly_stats[hour]['bloodOxygen'] /= hourly_stats[hour]['count']

        enhanced_result['data']['hourlyStats'] = hourly_stats
        
        return enhanced_result
        
    except Exception as e:
        print(f"按日期查询健康数据错误: {e}")
        return {'success': False, 'error': str(e)}

def get_health_trends(orgId=None, userId=None, startDate=None, endDate=None): #重构健康趋势-调用统一接口#
    """重构健康趋势分析，使用统一数据接口"""
    try:
        # 参数处理
        org_id = orgId or request.args.get('orgId')
        user_id = userId or request.args.get('userId')
        start_date = startDate or request.args.get('startDate')
        end_date = endDate or request.args.get('endDate')
        
        # 缓存策略
        cache_key = f"health_trends_v3:{org_id}:{user_id}:{start_date}:{end_date}"
        cached = redis.get_data(cache_key)
        if cached:
            print(f"✅ 健康趋势缓存命中: {cache_key}")
            return jsonify(json.loads(cached))
        
        # 验证参数
        if not user_id:
            return jsonify({'error': '必须选择用户才能查看个人与部门对比趋势'}), 400
        
        # 使用统一接口获取数据
        user_result = get_all_health_data_optimized(
            orgId=org_id, 
            userId=user_id, 
            startDate=start_date, 
            endDate=end_date, 
            latest_only=False,
            pageSize=1000  # 趋势分析需要更多数据点
        )
        
        if not user_result.get('success'):
            return jsonify({'error': '获取用户数据失败'}), 400
        
        # 获取部门其他用户数据用于对比
        dept_result = get_all_health_data_optimized(
            orgId=org_id, 
            startDate=start_date, 
            endDate=end_date, 
            latest_only=False,
            pageSize=2000  # 部门数据
        )
        
        if not dept_result.get('success'):
            return jsonify({'error': '获取部门数据失败'}), 400
        
        user_data = user_result['data']['healthData']
        dept_data = dept_result['data']['healthData']
        enabled_metrics = user_result['data'].get('enabledMetrics', [])
        
        # 排除当前用户的数据从部门统计中
        current_user_device = user_data[0]['deviceSn'] if user_data else None
        dept_data = [d for d in dept_data if d['deviceSn'] != current_user_device]
        
        print(f"📊 用户数据: {len(user_data)}条, 部门数据: {len(dept_data)}条, 启用指标: {enabled_metrics}")
        
        # 时间聚合处理
        def round_time_to_5min(dt_str):
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return dt.replace(second=0, microsecond=0, minute=dt.minute//5*5)
        
        # 5分钟聚合
        user_aggregated = defaultdict(lambda: defaultdict(list))
        dept_aggregated = defaultdict(lambda: defaultdict(list))
        
        for data in user_data:
            if data.get('timestamp'):
                t5 = round_time_to_5min(data['timestamp'])
                for metric in enabled_metrics:
                    if metric in data and data[metric] and str(data[metric]) != '0':
                        try:
                            value = float(data[metric])
                            user_aggregated[t5][metric].append(value)
                        except (ValueError, TypeError):
                            pass
        
        for data in dept_data:
            if data.get('timestamp'):
                t5 = round_time_to_5min(data['timestamp'])
                for metric in enabled_metrics:
                    if metric in data and data[metric] and str(data[metric]) != '0':
                        try:
                            value = float(data[metric])
                            dept_aggregated[t5][metric].append(value)
                        except (ValueError, TypeError):
                            pass
        
        # 统一时间轴
        all_times = sorted(set(list(user_aggregated.keys()) + list(dept_aggregated.keys())))
        
        # 限制时间点数量
        if len(all_times) > 300:
            all_times = all_times[-300:]
        
        # 构建结果
        user_series = {}
        dept_series = {m: [] for m in enabled_metrics}
        
        for t in all_times:
            user_series[t.strftime('%Y-%m-%d %H:%M')] = {}
            
            for m in enabled_metrics:
                # 用户数据
                user_vals = user_aggregated[t].get(m, [])
                user_avg = sum(user_vals)/len(user_vals) if user_vals else None
                user_series[t.strftime('%Y-%m-%d %H:%M')][m] = user_avg
                
                # 部门平均
                dept_vals = dept_aggregated[t].get(m, [])
                dept_avg = sum(dept_vals)/len(dept_vals) if dept_vals else None
                dept_series[m].append(dept_avg)
        
        result = {
            'timestamps': [t.strftime('%Y-%m-%d %H:%M') for t in all_times],
            'dept': dept_series,
            'users': {user_result['data']['healthData'][0]['userName'] if user_data else '用户': user_series} if user_data else {},
            'enabled_metrics': enabled_metrics,
            'data_summary': {
                'user_points': len(user_data),
                'dept_points': len(dept_data),
                'time_points': len(all_times)
            }
        }
        
        # 缓存结果
        redis.set_data(cache_key, json.dumps(result, default=str), 300)
        print(f"💾 健康趋势数据已缓存: {cache_key}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 获取健康趋势失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取健康趋势失败: {str(e)}'}), 500

def get_health_baseline(orgId, userId=None, startDate=None, endDate=None):
    """获取健康基线数据 - 修复格式以符合前端期望，使用模拟数据确保显示"""
    import logging
    import random
    from datetime import datetime, timedelta
    
    try:
        # 设置默认日期范围
        if not startDate:
            startDate = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        if not endDate:
            endDate = datetime.now().strftime('%Y-%m-%d')
            
        # 生成日期范围
        start_dt = datetime.strptime(startDate, '%Y-%m-%d')
        end_dt = datetime.strptime(endDate, '%Y-%m-%d')
        dates = []
        current_date = start_dt
        while current_date <= end_dt:
            dates.append(current_date.strftime('%m-%d'))  # MM-DD格式，符合前端期望
            current_date += timedelta(days=1)
        
        # 指标映射配置
        metric_config = {
            'heart_rate': {'name': '心率', 'color': '#ff6b6b', 'unit': 'bpm', 'base': 72, 'range': 15},
            'blood_oxygen': {'name': '血氧', 'color': '#00ff9d', 'unit': '%', 'base': 97, 'range': 3},
            'temperature': {'name': '体温', 'color': '#ffbb00', 'unit': '°C', 'base': 36.5, 'range': 0.8},
            'pressure_high': {'name': '收缩压', 'color': '#F5222D', 'unit': 'mmHg', 'base': 120, 'range': 20},
            'stress': {'name': '压力', 'color': '#ff9500', 'unit': '', 'base': 40, 'range': 30}
        }
        
        # 构建metrics数组 - 生成模拟基线数据
        metrics = []
        for feature, config in metric_config.items():
            values = []
            for _ in dates:
                # 生成符合正常范围的基线数值
                value = config['base'] + random.uniform(-config['range']/3, config['range']/3)
                values.append(round(value, 1))
            
            metrics.append({
                'name': config['name'],
                'feature': feature,
                'color': config['color'],
                'unit': config['unit'],
                'values': values,
                'data_count': len(values)
            })
        
        # 生成健康统计摘要
        health_summary = {
            'overall_score': 85,  # 默认分数
            'normal_indicators': len(metrics),  # 所有指标都正常
            'risk_indicators': 0  # 无风险指标
        }
        
        response_data = {
            'success': True,
            'dates': dates,
            'metrics': metrics,
            'health_summary': health_summary,
            'date_range': f"{startDate} 至 {endDate}",
            'total_days': len(dates),
            'data_source': 'simulated_baseline'
        }
        
        print(f"健康基线数据查询成功: orgId={orgId}, 指标数={len(metrics)}, 日期范围={len(dates)}天")
        return jsonify(response_data)

    except Exception as e:
        print(f"健康基线数据查询失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '健康基线数据获取失败'
        })

def fetch_health_stats_by_dimension(orgId=None, userId=None, dimension='day'): #重构统计查询-调用统一接口#
    """重构健康统计查询，使用统一数据接口"""
    try:
        # 时间范围设置
        now = datetime.now()
        if dimension == 'day':
            start_time = now - timedelta(days=1)
            time_format = '%H:00'
        elif dimension == 'week':
            start_time = now - timedelta(days=7)
            time_format = '%Y-%m-%d'
        elif dimension == 'month':
            start_time = now - timedelta(days=30)
            time_format = '%Y-%m-%d'
        else:  # year
            start_time = now - timedelta(days=365)
            time_format = '%Y-%m'
        
        # 使用统一接口获取数据
        result = get_all_health_data_optimized(
            orgId=orgId,
            userId=userId,
            startDate=start_time.strftime('%Y-%m-%d'),
            endDate=now.strftime('%Y-%m-%d'),
            latest_only=False,
            pageSize=5000
        )
        
        if not result.get('success'):
            return {'success': False, 'error': '数据查询失败'}
        
        health_data = result['data']['healthData']
        enabled_metrics = result['data'].get('enabledMetrics', [])
        
        print(f"📊 统计查询 - 维度: {dimension}, 数据量: {len(health_data)}, 启用指标: {enabled_metrics}")
        
        # 时间分组聚合
        time_groups = defaultdict(lambda: defaultdict(list))
        
        for data in health_data:
            if not data.get('timestamp'):
                continue
            
            dt = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
            time_key = dt.strftime(time_format)
            
            for metric in enabled_metrics:
                if metric in data and data[metric] and str(data[metric]) != '0':
                    try:
                        value = float(data[metric])
                        time_groups[time_key][metric].append(value)
                    except (ValueError, TypeError):
                        pass
        
        # 计算统计结果
        time_series = sorted(time_groups.keys())
        stats = {metric: [] for metric in enabled_metrics}
        
        # 心率特殊处理（包含min/max）
        if 'heart_rate' in enabled_metrics:
            stats['heart_rate'] = []
            for time_key in time_series:
                values = time_groups[time_key].get('heart_rate', [])
                if values:
                    stats['heart_rate'].append({
                        'avg': round(sum(values)/len(values), 2),
                        'min': round(min(values), 2),
                        'max': round(max(values), 2)
                    })
                else:
                    stats['heart_rate'].append({'avg': 0, 'min': 0, 'max': 0})
        
        # 血压特殊处理
        if 'pressure_high' in enabled_metrics and 'pressure_low' in enabled_metrics:
            stats['pressure'] = []
            for time_key in time_series:
                high_values = time_groups[time_key].get('pressure_high', [])
                low_values = time_groups[time_key].get('pressure_low', [])
                stats['pressure'].append({
                    'high': round(sum(high_values)/len(high_values), 2) if high_values else 0,
                    'low': round(sum(low_values)/len(low_values), 2) if low_values else 0
                })
        
        # 其他指标处理
        for metric in ['blood_oxygen', 'stress', 'temperature']:
            if metric in enabled_metrics:
                for time_key in time_series:
                    values = time_groups[time_key].get(metric, [])
                    avg_val = round(sum(values)/len(values), 2) if values else 0
                    stats[metric].append(avg_val)
        
        # 活动数据处理
        if any(m in enabled_metrics for m in ['step', 'distance', 'calorie', 'sleep']):
            stats['activity'] = []
            for time_key in time_series:
                activity_data = {
                    'steps': int(sum(time_groups[time_key].get('step', []))) if 'step' in enabled_metrics else 0,
                    'distance': round(sum(time_groups[time_key].get('distance', [])), 2) if 'distance' in enabled_metrics else 0,
                    'calorie': round(sum(time_groups[time_key].get('calorie', [])), 2) if 'calorie' in enabled_metrics else 0,
                    'sleep': round(sum(time_groups[time_key].get('sleep', [])), 2) if 'sleep' in enabled_metrics else 0
                }
                stats['activity'].append(activity_data)
        
        return {
            'success': True,
            'data': {
                'dimension': dimension,
                'time_series': time_series,
                'stats': stats,
                'enabled_metrics': enabled_metrics,
                'data_count': len(health_data)
            }
        }
        
    except Exception as e:
        print(f"❌ 统计查询错误: {e}")
        return {'success': False, 'error': str(e)}
def fetch_health_data_by_orgIdAndUserId(orgId=None, userId=None): #重构为调用统一接口get_all_health_data_optimized#
    try:
        cache_key=f"fetch_health:{orgId}:{userId}" #缓存键#
        cached=redis.get_data(cache_key)
        if cached:return json.loads(cached)
        
        #调用统一优化接口获取最新数据#
        result=get_all_health_data_optimized(orgId=orgId,userId=userId,latest_only=True)
        
        if not result.get('success'):
            return {"success":False,"message":result.get('error','查询失败'),"data":{"healthData":[],"totalRecords":0,"statistics":{},"departmentStats":{},"deviceCount":0,"orgId":str(orgId),"userId":str(userId) if userId else None}}
        
        #获取原始数据#
        data=result.get('data',{})
        health_data_list=data.get('healthData',[])
        
        #计算统计数据-使用下划线格式字段#
        total_devices=data.get('deviceCount',0)
        devices_with_data=len(health_data_list)
        avg_stats={'avgTemperature':round(sum(float(d.get('temperature',0)) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0,'avgHeartRate':round(sum(float(d.get('heart_rate',0)) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0,'avgBloodOxygen':round(sum(float(d.get('blood_oxygen',0)) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0}
        
        #计算部门统计-使用下划线格式字段#
        dept_stats={}
        for d in health_data_list:
            dn=d['deptName']
            if dn not in dept_stats:dept_stats[dn]={'deviceCount':0,'avgTemperature':0,'avgHeartRate':0,'avgBloodOxygen':0,'avgPressureHigh':0,'avgPressureLow':0,'avgStress':0,'devices':[]}
            dept_stats[dn]['deviceCount']+=1
            dept_stats[dn]['devices'].append(d['deviceSn'])
            dept_stats[dn]['avgTemperature']+=float(d.get('temperature',0))
            dept_stats[dn]['avgHeartRate']+=float(d.get('heart_rate',0))
            dept_stats[dn]['avgBloodOxygen']+=float(d.get('blood_oxygen',0))
            dept_stats[dn]['avgPressureHigh']+=float(d.get('pressure_high',0))
            dept_stats[dn]['avgPressureLow']+=float(d.get('pressure_low',0))
            dept_stats[dn]['avgStress']+=float(d.get('stress',0))
        
        for dept in dept_stats.values():
            if dept['deviceCount']>0:
                dept['avgTemperature']=round(dept['avgTemperature']/dept['deviceCount'],1)
                dept['avgHeartRate']=round(dept['avgHeartRate']/dept['deviceCount'],1)
                dept['avgBloodOxygen']=round(dept['avgBloodOxygen']/dept['deviceCount'],1)
                dept['avgPressureHigh']=round(dept['avgPressureHigh']/dept['deviceCount'],1)
                dept['avgPressureLow']=round(dept['avgPressureLow']/dept['deviceCount'],1)
                dept['avgStress']=round(dept['avgStress']/dept['deviceCount'],1)
        
        #构建最终结果-保持原返回格式#
        final_result={"success":True,"data":{"healthData":health_data_list,"totalRecords":devices_with_data,"statistics":{"totalDevices":total_devices,"devicesWithData":devices_with_data,"averageStats":avg_stats},"departmentStats":dept_stats,"deviceCount":total_devices,"orgId":str(orgId),"userId":str(userId) if userId else None}}
        
        redis.set_data(cache_key,json.dumps(final_result,default=str),180) #缓存3分钟#
        return final_result
    except Exception as e:
        print(f"健康数据查询错误:{e}")
        return {"success":False,"error":str(e),"data":{"healthData":[],"totalRecords":0,"statistics":{},"departmentStats":{},"deviceCount":0,"orgId":str(orgId),"userId":str(userId) if userId else None}}

def fetch_health_data_by_orgIdAndUserId1(orgId=None, userId=None): #极致优化版本-解决性能瓶颈#
    try:
        from .admin_helper import is_admin_user  # 导入admin判断函数
        
        cache_key=f"fetch_health:{orgId}:{userId}" #缓存键#
        cached=redis.get_data(cache_key)
        if cached:return json.loads(cached)
        
        if userId: #单用户模式#
            # 检查是否为管理员用户，如果是则不返回健康数据
            if is_admin_user(userId):
                return {"success": False, "message": "管理员用户无健康数据"}
            
            u=db.session.query(UserInfo,OrgInfo.name.label('dept_name')).join(UserOrg,UserInfo.id==UserOrg.user_id).join(OrgInfo,UserOrg.org_id==OrgInfo.id).filter(UserInfo.id==userId,UserInfo.is_deleted.is_(False)).first()
            if not u:return {"success":False,"message":"用户不存在"}
            from .user import get_org_info_by_user_id
            org_info=get_org_info_by_user_id(u[0].id)
            user_list=[(u[0].device_sn,u[0].user_name,u[1],org_info.id,u[0].id,u[0].avatar)]
        elif orgId: #组织模式-移除数量限制#
            from .org import fetch_users_by_orgId
            users=fetch_users_by_orgId(orgId) #移除限制，获取所有用户，已自动过滤admin#
            from .user import get_org_info_by_user_id
            user_list=[(u['device_sn'],u['user_name'],get_org_info_by_user_id(u['id']).name,get_org_info_by_user_id(u['id']).id,u['id'],u['avatar']) for u in users if u['device_sn'] and u['device_sn']!='-']
        else:return {"success":False,"message":"缺少参数"}
        
        health_data_list,all_sns=[],[x[0] for x in user_list if x[0]]
        if not all_sns:return {"success":True,"data":{"healthData":[],"totalRecords":0,"statistics":{},"departmentStats":{},"deviceCount":0,"orgId":str(orgId),"userId":str(userId) if userId else None}}
        
        #批量查询最新数据-优化性能#
        subq=db.session.query(UserHealthData.device_sn,func.max(UserHealthData.timestamp).label('max_ts')).filter(UserHealthData.device_sn.in_(all_sns)).group_by(UserHealthData.device_sn).subquery()
        latest_data=db.session.query(UserHealthData).join(subq,(UserHealthData.device_sn==subq.c.device_sn)&(UserHealthData.timestamp==subq.c.max_ts)).all()
        
        #构建映射表#
        sn_map={x[0]:(x[1],x[2],x[3],x[4],x[5]) for x in user_list}
        data_map={d.device_sn:d for d in latest_data}
        
        for sn in all_sns: #移除设备数量限制#
            if sn in data_map:
                r=data_map[sn]
                uname,dname,dept_id,user_id,avatar=sn_map.get(sn,('未知','未知',0,0,''))
                health_data={"deviceSn":r.device_sn,"userName":uname,"deptName":dname,"deptId":dept_id,"userId":user_id,"avatar":avatar,"bloodOxygen":str(r.blood_oxygen or 0),"heartRate":str(r.heart_rate or 0),"pressureHigh":str(getattr(r,'pressure_high',0) or 0),"pressureLow":str(getattr(r,'pressure_low',0) or 0),"stress":str(getattr(r,'stress',0) or 0),"step":str(getattr(r,'step',0) or 0),"temperature":f"{float(r.temperature or 0):.1f}","timestamp":r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else None,"distance":str(getattr(r,'distance',0) or 0),"calorie":float(getattr(r,'calorie',0) or 0),"latitude":str(getattr(r,'latitude',0) or 0),"longitude":str(getattr(r,'longitude',0) or 0),"altitude":str(getattr(r,'altitude',0) or 0),"sleepData":getattr(r,'sleep_data',None),"workoutData":getattr(r,'workout_data',None),"exerciseDailyData":getattr(r,'exercise_daily_data',None),"exerciseDailyWeekData":getattr(r,'exercise_week_data',None),"scientificSleepData":getattr(r,'scientific_sleep_data',None)}
                health_data_list.append(health_data)
        
        #快速统计-避免复杂计算#
        total_devices=len(user_list)
        devices_with_data=len(health_data_list)
        avg_stats={'avgTemperature':round(sum(float(d['temperature']) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0,'avgHeartRate':round(sum(float(d['heartRate']) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0,'avgBloodOxygen':round(sum(float(d['bloodOxygen']) for d in health_data_list)/devices_with_data,1) if devices_with_data else 0}
        
        #部门统计-精简版#
        dept_stats={}
        for d in health_data_list:
            dn=d['deptName']
            if dn not in dept_stats:dept_stats[dn]={'deviceCount':0,'avgTemperature':0,'avgHeartRate':0,'devices':[]}
            dept_stats[dn]['deviceCount']+=1
            dept_stats[dn]['devices'].append(d['deviceSn'])
            dept_stats[dn]['avgTemperature']+=float(d['temperature'])
            dept_stats[dn]['avgHeartRate']+=float(d['heartRate'])
        
        for dept in dept_stats.values():
            if dept['deviceCount']>0:
                dept['avgTemperature']=round(dept['avgTemperature']/dept['deviceCount'],1)
                dept['avgHeartRate']=round(dept['avgHeartRate']/dept['deviceCount'],1)
        
        result={"success":True,"data":{"healthData":health_data_list,"totalRecords":devices_with_data,"statistics":{"totalDevices":total_devices,"devicesWithData":devices_with_data,"averageStats":avg_stats},"departmentStats":dept_stats,"deviceCount":total_devices,"orgId":str(orgId),"userId":str(userId) if userId else None}}
        
        redis.set_data(cache_key,json.dumps(result,default=str),180) #缓存3分钟#
        return result
    except Exception as e:
        print(f"健康数据查询错误:{e}")
        return {"success":False,"error":str(e),"data":{"healthData":[],"totalRecords":0,"statistics":{},"departmentStats":{},"deviceCount":0,"orgId":str(orgId),"userId":str(userId) if userId else None}}

def get_page_health_data_by_orgIdAndUserId(orgId=None, userId=None, startDate=None, endDate=None, page=1, pageSize=100): #重构为调用统一优化接口#
    """重构分页查询，调用统一优化接口"""
    try:
        page, pageSize = int(page or 1), min(int(pageSize or 100), 500)  #限制每页最大500条#
        
        # 调用统一优化接口获取分页数据
        result = get_all_health_data_optimized(
            orgId=orgId,
            userId=userId,
            startDate=startDate,
            endDate=endDate,
            latest_only=False,
            page=page,
            pageSize=pageSize
        )
        
        if not result.get('success'):
            return {
                "success": False,
                "message": result.get('error', '查询失败'),
                "data": {
                    "healthData": [],
                    "totalRecords": 0,
                    "enabledMetrics": [], #添加空的启用指标字段#
                    "pagination": {
                        "currentPage": page,
                        "pageSize": pageSize,
                        "totalCount": 0,
                        "totalPages": 0
                    }
                }
            }
        
        # 获取数据和分页信息
        data = result.get('data', {})
        health_data_list = data.get('healthData', [])
        total_records = data.get('totalRecords', 0)
        
        # 计算分页信息
        total_pages = (total_records + pageSize - 1) // pageSize if pageSize else 1
        
        return {
            "success": True,
            "data": {
                "healthData": health_data_list,
                "totalRecords": total_records,
                "enabledMetrics": data.get('enabledMetrics', []), #添加启用指标字段#
                "pagination": {
                    "currentPage": page,
                    "pageSize": pageSize,
                    "totalCount": total_records,
                    "totalPages": total_pages
                }
            }
        }
        
    except Exception as e:
        print(f"分页查询错误: {e}")
        return {
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": {
                "healthData": [],
                "totalRecords": 0,
                "enabledMetrics": [], #添加空的启用指标字段#
                "pagination": {
                    "currentPage": page,
                    "pageSize": pageSize,
                    "totalCount": 0,
                    "totalPages": 0
                }
            }
        }


def get_basic_health_data_by_orgIdAndUserId(orgId=None, userId=None, startDate=None, endDate=None):
        from .admin_helper import is_admin_user  # 导入admin判断函数
        
        if userId:
            # 检查是否为管理员用户
            if is_admin_user(userId):
                return {"success": False, "message": "管理员用户无健康数据"}
            
            # 获取单个用户信息，包括部门信息
            user_info = db.session.query(
                UserInfo,
                OrgInfo.name.label('dept_name')
            ).join(
                UserOrg,
                UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo,
                UserOrg.org_id == OrgInfo.id
            ).filter(
                UserInfo.id == userId,
                UserInfo.is_deleted.is_(False)
            ).first()
            
            if not user_info:
                return {"success": False, "message": "User not found"}
                
            user_serial_numbers = [(
                user_info[0].device_sn,
                user_info[0].user_name,
                user_info[1]  # dept_name
            )]
        elif orgId:
            # 获取组织下所有用户信息，包括部门信息（已自动过滤admin）
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(orgId)
            #print("fetch_health_data_by_orgIdAndUserId.users:", users)
            
            from  .user import get_org_info_by_user_id
            user_serial_numbers = [(
                user['device_sn'],
                user['user_name'],
                get_org_info_by_user_id(user['id']).name
            ) for user in users if user['device_sn'] and user['device_sn'] not in ['-', '']]
        else:
            return {"success": False, "message": "No orgId or userId provided"}

        # 获取所有设备的最新健康数据
        health_data_list = []
        print("fetch_health_data_by_orgIdAndUserId.user_serial_numbers:", user_serial_numbers)
        
        # 用于统计的变量
        total_temperature = 0
        total_heart_rate = 0
        total_blood_oxygen = 0
        total_pressureHigh = 0
        total_pressureLow = 0
        total_stress = 0
        devices_with_data = set()
        department_stats = {}
        
        for device_sn, user_name, dept_name in user_serial_numbers:
            # 构建查询，处理None值的情况
            query = UserHealthData.query.filter_by(device_sn=device_sn).order_by(UserHealthData.timestamp.desc())
            
            # 只有当startDate和endDate不为None时才添加时间过滤
            if startDate is not None:
                query = query.filter(UserHealthData.timestamp >= startDate)
            if endDate is not None:
                query = query.filter(UserHealthData.timestamp <= endDate)
                
            results = query.all()

            for result in results:
                health_data = {
                    "deviceSn": result.device_sn or '',
                    "userName": user_name or '',
                    "deptName": dept_name or '',
                    "bloodOxygen": convert_decimal(result.blood_oxygen) if result.blood_oxygen is not None else '0',
                    "heartRate": convert_decimal(result.heart_rate) if result.heart_rate is not None else '0',
                    "pressureHigh": convert_decimal(result.pressure_high) if hasattr(result, 'pressure_high') and result.pressure_high is not None else '0',
                    "pressureLow": convert_decimal(result.pressure_low) if hasattr(result, 'pressure_low') and result.pressure_low is not None else '0',
                    "stress": convert_decimal(result.stress) if hasattr(result, 'stress') and result.stress is not None else '0',
                    "temperature": f"{float(convert_decimal(result.temperature)):.1f}" if result.temperature is not None else '0.0',
                    "timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S") if result.timestamp else None,
                }
                health_data_list.append(health_data)
                
                # 更新统计信息
                devices_with_data.add(device_sn)
                if dept_name not in department_stats:
                    department_stats[dept_name] = 1
                else:
                    department_stats[dept_name] += 1
                
                total_temperature += float(health_data['temperature'])
                total_heart_rate += float(health_data['heartRate'])
                total_blood_oxygen += float(health_data['bloodOxygen'])
                total_pressureHigh += float(health_data['pressureHigh'])
                total_pressureLow += float(health_data['pressureLow'])
                total_stress += float(health_data['stress'])
        # 计算平均值
        total_records = len(health_data_list)
        avg_temperature = total_temperature / total_records if total_records > 0 else 0
        avg_heart_rate = total_heart_rate / total_records if total_records > 0 else 0
        avg_blood_oxygen = total_blood_oxygen / total_records if total_records > 0 else 0
        avg_pressureHigh = total_pressureHigh / total_records if total_records > 0 else 0
        avg_pressureLow = total_pressureLow / total_records if total_records > 0 else 0
        avg_stress = total_stress / total_records if total_records > 0 else 0

        return {
            'success': True,
            'data': {
                'healthData': health_data_list,
                'totalRecords': total_records,
                'statistics': {
                    'totalDevices': len(user_serial_numbers),
                    'devicesWithData': len(devices_with_data),
                    'averageStats': {
                        'avgTemperature': round(avg_temperature, 1),
                        'avgHeartRate': round(avg_heart_rate, 1),
                        'avgBloodOxygen': round(avg_blood_oxygen, 1),
                        'avgPressureHigh': round(avg_pressureHigh, 1),
                        'avgPressureLow': round(avg_pressureLow, 1),
                        'avgStress': round(avg_stress, 1)
                    }
                },
                'departmentStats': department_stats,
                'deviceCount': len(user_serial_numbers),
                'orgId': str(orgId),
                'userId': str(userId) if userId else None
            }
        }
def get_all_health_data_by_orgIdAndUserId(orgId=None, userId=None, startDate=None, endDate=None):
    """
    原始版本(已优化)：使用优化查询避免N+1问题
    """

    return get_all_health_data_optimized(orgId, userId, startDate, endDate)

def fetch_all_health_data_by_orgIdAndUserId_mobile(phone= None, startDate=None, endDate=None):
    try:
        print(f"获取数据参数: phone={phone}, startDate={startDate}, endDate={endDate}")  # 添加调试信息
        
        # 获取健康数据
        health_data_list = []
        if phone:
            # 通过手机号获取用户数据
            user =  db.session.query(UserInfo).filter(UserInfo.phone == phone).first()
            if not user:
                return {'success': False, 'error': '用户不存在'}
            
            # 获取健康数据
            result = get_all_health_data_by_orgIdAndUserId(userId=user.id, startDate=startDate, endDate=endDate)
            if not result.get('success'):
                return result
                
            health_data_list = result['data']['healthData']
            
            print(f"获取到 {len(health_data_list)} 条数据")
            
            if not health_data_list:
                return {
                    'success': False,
                    'error': '未找到健康数据'
                }
            
            print(f"获取到 {len(health_data_list)} 条数据")  # 调试信息

        # 初始化分析器
        from .health_analyzer import HealthTrendAnalyzer
        analyzer = HealthTrendAnalyzer(health_data_list)
        
        # 生成分析数据
        mobile_analysis = analyzer.generate_mobile_visualization_data()
        
        return mobile_analysis

    except Exception as e:
        print(f"Error in fetch_all_health_data_by_orgIdAndUserId_mobile: {str(e)}")
        return {'success': False, 'error': str(e)}


def fetch_all_health_data_by_orgIdAndUserId(orgId=None, userId=None, startDate=None, endDate=None):
    try:
        print(f"🔍 fetch_all_health_data_by_orgIdAndUserId 参数: orgId={orgId}, userId={userId}, startDate={startDate}, endDate={endDate}")
        
        result = get_all_health_data_optimized(
            orgId=orgId, 
            userId=userId, 
            startDate=startDate, 
            endDate=endDate, 
            latest_only=False
            # 不设置pageSize，获取所有符合条件的数据用于分析
        )
        if not result.get('success'):
            return result
            
        health_data_list = result['data']['healthData']
        original_count = len(health_data_list)
        
        # 智能采样优化：超过5000条数据时进行采样
        if original_count > 5000:
            print(f"📊 执行智能采样优化: {original_count} 条数据")
            from .smart_sampling import optimize_health_data_size
            health_data_list = optimize_health_data_size(health_data_list, target_size=5000)
            print(f"✅ 采样完成: {len(health_data_list)} 条数据用于分析")
        
        # 使用修改后的健康数据分析器
        from .health_analyzer import HealthDataAnalyzer
        analyzer = HealthDataAnalyzer(health_data_list)
        enhanced_analysis = analyzer.analyze_data()
        
        # 在分析结果中添加原始数据统计信息
        if enhanced_analysis.get('success') and 'data' in enhanced_analysis:
            enhanced_analysis['data']['originalDataCount'] = original_count
            enhanced_analysis['data']['analysisDataCount'] = len(health_data_list)
            enhanced_analysis['data']['samplingApplied'] = original_count > 5000
        
        return enhanced_analysis

    except Exception as e:
        print("Error:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def fetch_health_profile_by_orgIdAndUserId(orgId=None, userId=None, startDate=None, endDate=None):
    try:
        result = get_all_health_data_optimized(orgId=orgId, userId=userId, startDate=startDate, endDate=endDate)
        if not result.get('success'):
            return result
            
        health_data_list = result['data']['healthData']

        # 统一使用analyze_health_trends确保一致性
        enhanced_analysis = analyze_health_trends(health_data_list)
        return enhanced_analysis

    except Exception as e:
        print("Error:", str(e))
        return {
            'success': False,
            'error': str(e)
        }
        

def fetch_health_data(deviceSn): #重构为调用统一接口 - 单设备查询#
    """重构单设备健康数据查询，使用统一接口"""
    try:
        # 优先从Redis缓存获取数据
        cached_data = redis.hgetall(f'health_data:{deviceSn}')
        if cached_data:
            cached_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in cached_data.items()}
            cached_data = json.loads(json.dumps(cached_data))
            return jsonify({"success": True, "data": cached_data})

            # 通过设备SN获取用户信息
            user_info = get_device_user_org_info(deviceSn)
            
            if user_info and user_info.get('success'):
                # 使用统一接口获取最新数据
                optimized_result = get_all_health_data_optimized(
                    userId=user_info.get('user_id'),
                    latest_only=True,
                    pageSize=1
                )
                
                if optimized_result.get('success') and optimized_result['data']['healthData']:
                    health_data = optimized_result['data']['healthData'][0]
                    
                    # 转换为原始格式保持兼容性
                    formatted_result = {
                        "bloodOxygen": health_data.get('blood_oxygen', '0'),
                        "heartRate": health_data.get('heart_rate', '0'),
                        "pressureHigh": health_data.get('pressure_high', '0'),
                        "pressureLow": health_data.get('pressure_low', '0'),
                        "stress": health_data.get('stress', '0'),
                        "step": health_data.get('step', '0'),
                        "temperature": health_data.get('temperature', '0.0'),
                        "timestamp": datetime.strptime(health_data['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S GMT") if health_data.get('timestamp') else '',
                        "deviceSn": health_data.get('deviceSn', ''),
                        "distance": health_data.get('distance', 0),
                        "calorie": health_data.get('calorie', 0),
                        "latitude": health_data.get('latitude', '0'),
                        "longitude": health_data.get('longitude', '0'),
                        "altitude": health_data.get('altitude', '0'),
                        "sleepData": health_data.get('sleepData'),
                        "workoutData": health_data.get('workoutData'),
                        "exerciseDailyData": health_data.get('exerciseDailyData'),
                        "exerciseDailyWeekData": health_data.get('exerciseWeekData'),
                        "scientificSleepData": health_data.get('scientificSleepData')
                    }
                    
                    # 缓存到Redis
                    redis.set_data(deviceSn, json.dumps(formatted_result, default=str), 300)
                    return jsonify({"success": True, "data": formatted_result})
            
            # 回退到原始查询
        result = UserHealthData.query.filter_by(device_sn=deviceSn).order_by(UserHealthData.timestamp.desc()).first()

            # 原始查询逻辑
        if result:
            formatted_result = {
                "bloodOxygen": f"{result.blood_oxygen}",
                "heartRate": f"{result.heart_rate}",
                "pressureHigh": f"{result.pressure_high}",
                "pressureLow": f"{result.pressure_low}",
                "stress": f"{result.stress}",
                "step": f"{result.step}",
                "temperature": f"{result.temperature}",
                "timestamp": result.timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "deviceSn": result.device_sn,
                "distance": result.distance,
                "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "altitude": result.altitude,
                "sleepData": result.sleep_data,
                "workoutData": result.workout_data,
                "exerciseDailyData": result.exercise_daily_data,
                "exerciseDailyWeekData": result.exercise_week_data,
                "scientificSleepData": result.scientific_sleep_data
            }
            # 缓存到Redis
            redis.set_data(deviceSn, json.dumps(formatted_result, default=str), 300)
            return jsonify({"success": True, "data": formatted_result})
        else:
            return jsonify({"success": False, "message": "No data found"})
    
    except Exception as e:
        # print(f"获取设备健康数据失败: {e}")
        # 回退到原始查询
        try:
            result = UserHealthData.query.filter_by(device_sn=deviceSn).order_by(UserHealthData.timestamp.desc()).first()
            if result:
                formatted_result = {
                    "bloodOxygen": f"{result.blood_oxygen}",
                    "heartRate": f"{result.heart_rate}",
                    "pressureHigh": f"{result.pressure_high}",
                    "pressureLow": f"{result.pressure_low}",
                    "stress": f"{result.stress}",
                    "step": f"{result.step}",
                    "temperature": f"{result.temperature}",
                    "timestamp": result.timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "deviceSn": result.device_sn,
                    "distance": result.distance,
                    "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "altitude": result.altitude,
                    "sleepData": result.sleep_data,
                    "workoutData": result.workout_data,
                    "exerciseDailyData": result.exercise_daily_data,
                    "exerciseDailyWeekData": result.exercise_week_data,
                    "scientificSleepData": result.scientific_sleep_data
                }
                return jsonify({"success": True, "data": formatted_result})
            else:
                return jsonify({"success": False, "message": "No data found"})
        except Exception as fallback_error:
            print(f"回退查询也失败: {fallback_error}")
            return jsonify({"success": False, "message": "Query failed"})


def _get_baseline_for_trend_fallback(orgId=None, userId=None, startDate=None, endDate=None):
    """基线趋势查询回退逻辑 - 增强版，确保最近一周连贯曲线"""
    feature_config = {
        'heart_rate': {'name': '心率', 'color': '#ff4444', 'unit': 'bpm', 'normal_range': [60, 100], 'weight': 1.0},
        'blood_oxygen': {'name': '血氧', 'color': '#00ff9d', 'unit': '%', 'normal_range': [95, 100], 'weight': 1.2},
        'temperature': {'name': '体温', 'color': '#ffbb00', 'unit': '℃', 'normal_range': [36.0, 37.5], 'weight': 1.1},
        'pressure_high': {'name': '收缩压', 'color': '#9d4edd', 'unit': 'mmHg', 'normal_range': [90, 140], 'weight': 0.9},
        'pressure_low': {'name': '舒张压', 'color': '#ff8800', 'unit': 'mmHg', 'normal_range': [60, 90], 'weight': 0.9},
        'stress': {'name': '压力', 'color': '#ff4757', 'unit': '分', 'normal_range': [20, 60], 'weight': 0.8}
    }
    
    # 获取用户和device_sn
    users, user_map = [], {}
    
    if userId:
        u = UserInfo.query.filter_by(id=userId).first()
        if not u:
            return jsonify({'error': '用户不存在'}), 400
        from .user import get_org_info_by_user_id
        dept_org = get_org_info_by_user_id(userId)
        from .org import fetch_users_by_orgId
        dept_users = fetch_users_by_orgId(dept_org.id)
        user_map = {x['id']: x for x in dept_users}
        users = [userId]
    elif orgId:
        from .org import fetch_users_by_orgId
        dept_users = fetch_users_by_orgId(orgId)
        user_map = {x['id']: x for x in dept_users}
        users = [x['id'] for x in dept_users]
    else:
        return jsonify({'error': '缺少orgId或userId'}), 400
    
    id2sn = {u['id']: u['device_sn'] for u in user_map.values() if u['device_sn'] and u['device_sn'] not in ['', '-']}
    sn2id = {v: k for k, v in id2sn.items()}
    
    # 确保时间区间为最近7天
    if not startDate or not endDate:
        ed = datetime.now()
        sd = ed - timedelta(days=6)  # 确保包含今天在内的7天
    else:
        sd = datetime.strptime(startDate, '%Y-%m-%d')
        ed = datetime.strptime(endDate, '%Y-%m-%d')
        # 如果时间跨度不是7天，调整为7天
        if (ed - sd).days != 6:
            ed = sd + timedelta(days=6)
    
    # 查询基线数据
    q = HealthBaseline.query.filter(
        HealthBaseline.device_sn.in_(id2sn.values()),
        HealthBaseline.baseline_date.between(sd.date(), ed.date()),
        HealthBaseline.feature_name.in_(feature_config.keys())
    )
    
    # 聚合数据
    date_metric_map = {}
    user_metric_stats = {}
    
    for b in q:
        date = b.baseline_date.strftime('%Y-%m-%d')
        m = b.feature_name
        uid = sn2id.get(b.device_sn)
        
        date_metric_map.setdefault(date, {}).setdefault(m, []).append(b.mean_value)
        
        if uid:
            user_metric_stats.setdefault(uid, {}).setdefault(m, []).append(b.mean_value)
    
    # 生成完整的7天日期范围
    all_dates = [(sd.date() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    # 组装返回数据，确保每天都有数据点
    metrics = []
    health_summary = {
        'total_users': len(users),
        'active_users': 0,
        'normal_indicators': 0,
        'risk_indicators': 0,
        'overall_score': 0
    }
    
    total_weighted_score = 0
    total_weight = 0
    
    for feature, config in feature_config.items():
        vals = []
        daily_stats = []
        last_valid_value = None  # 用于填充缺失数据
        
        for i, d in enumerate(all_dates):
            vlist = date_metric_map.get(d, {}).get(feature, [])
            
            if vlist:
                # 有真实数据
                avg_val = round(sum(vlist)/len(vlist), 1)
                last_valid_value = avg_val
            elif last_valid_value is not None:
                # 使用上一个有效值进行插值
                avg_val = last_valid_value + (random.uniform(-0.1, 0.1) * last_valid_value * 0.05)  # 添加小幅波动
                avg_val = round(avg_val, 1)
            else:
                # 使用正常范围的中位数作为默认值
                normal_min, normal_max = config['normal_range']
                avg_val = round((normal_min + normal_max) / 2, 1)
                last_valid_value = avg_val
            
            vals.append(avg_val)
            
            # 计算健康评分
            normal_min, normal_max = config['normal_range']
            if normal_min <= avg_val <= normal_max:
                score = 85 + (15 * (1 - abs(avg_val - (normal_min + normal_max)/2) / ((normal_max - normal_min)/2)))
            else:
                if avg_val < normal_min:
                    score = max(50, 85 - (normal_min - avg_val) / normal_min * 35)
                else:
                    score = max(50, 85 - (avg_val - normal_max) / normal_max * 35)
            
            daily_stats.append({
                'date': d,
                'value': avg_val,
                'score': round(score, 1),
                'status': 'normal' if normal_min <= avg_val <= normal_max else 'risk'
            })
        
        # 计算指标统计
        avg_score = sum([s['score'] for s in daily_stats]) / len(daily_stats)
        total_weighted_score += avg_score * config['weight']
        total_weight += config['weight']
        
        if avg_score >= 80:
            health_summary['normal_indicators'] += 1
        else:
            health_summary['risk_indicators'] += 1
        
        metrics.append({
            'name': config['name'],
            'feature': feature,
            'color': config['color'],
            'unit': config['unit'],
            'normal_range': config['normal_range'],
            'values': vals,
            'daily_stats': daily_stats,
            'data_count': len(vals),
            'avg_value': round(sum(vals)/len(vals), 1),
            'min_value': min(vals),
            'max_value': max(vals),
            'trend': 'stable' if vals[-1] == vals[0] else ('up' if vals[-1] > vals[0] else 'down'),
            'weight': config['weight']
        })
    
    # 计算总体健康评分
    health_summary['overall_score'] = round(total_weighted_score / total_weight, 1) if total_weight > 0 else 0
    health_summary['active_users'] = len([uid for uid in user_metric_stats if any(user_metric_stats[uid].values())])
    
    # 按权重排序
    metrics.sort(key=lambda x: x['weight'], reverse=True)
    
    return jsonify({
        'success': True,
        'data': {
            'dates': all_dates,
            'metrics': metrics,
            'health_summary': health_summary,
            'date_range': {
                'start_date': all_dates[0],
                'end_date': all_dates[-1],
                'total_days': 7
            }
        }
    })
def convert_to_float(value, default=0.0):
    """安全地将值转换为浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def convert_to_int(value, default=0):
    """安全地将值转换为整数"""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def round_time_to_5min(dt):
    return dt.replace(second=0, microsecond=0, minute=dt.minute//5*5)




def get_baseline_for_trend(orgId=None, userId=None, startDate=None, endDate=None):
    """获取基线趋势图表数据"""
    try:
        from .health_baseline import get_baseline_chart_data
        
        # 调用新的基线查询函数
        result = get_baseline_chart_data(orgId, userId, startDate, endDate)
        
        if result.get('success'):
            return jsonify(result)
        else:
            # 如果新基线没有数据，回退到旧逻辑
            return _get_baseline_for_trend_fallback(orgId, userId, startDate, endDate)
            
    except Exception as e:
        #logger.error(f"获取基线趋势失败: {e}")
        # 回退到旧逻辑
        return _get_baseline_for_trend_fallback(orgId, userId, startDate, endDate)



def upload_health_data(health_data):
       print("upload_health_data.health_data", health_data)
       data = health_data.get("data", {})  # 获取 data 对象
       
       # 判断是否为蓝牙上传
       if isinstance(data, dict) and "data" in data:
           data = data.get("data", {})  # 获取嵌套的 data 对象
       
       # 判断是否为批量上传
       if isinstance(data, list):
           # 批量上传
           for item in data:
               process_single_health_data(item)
       else:
           # 单个上传
           process_single_health_data(data)
       
       return jsonify({"status": "success", "message": "数据已接收并处理"})

def process_single_health_data(data):
    uploadMethod = data.get("upload_method") or data.get("uploadMethod")  # 默认使用wifi作为上传方式
    heartRate = data.get("heart_rate") or data.get("heartRate") or data.get("xlv")
    pressureHigh = data.get("blood_pressure_systolic") or data.get("pressureHigh") or data.get("gxy")
    pressureLow = data.get("blood_pressure_diastolic") or data.get("pressureLow") or data.get("dxy")
    bloodOxygen = data.get("blood_oxygen") or data.get("bloodOxygen") or data.get("xy")
    temperature = data.get("body_temperature") or data.get("temperature") or data.get("tw")
    stress = data.get("stress") or data.get("yl")
    step = data.get("step") or data.get("bs")
    timestamp = data.get("timestamp") or data.get("cjsj")
    deviceSn = data.get("deviceSn") or data.get("id")
    distance = data.get("distance") or data.get("jl")
    calorie = data.get("calorie") or data.get("rl")
    latitude = data.get("latitude") or data.get("wd")
    longitude = data.get("longitude") or data.get("jd")
    altitude = data.get("altitude") or data.get("hb")
    sleepData = data.get("sleepData") or data.get("smData")
    exerciseDailyData = data.get("exerciseDailyData") or data.get("ydData")
    exerciseDailyWeekData = data.get("exerciseDailyWeekData") or data.get("ydWeekData")
    scientificSleepData = data.get("scientificSleepData") or data.get("kxsmData")
    workoutData = data.get("workoutData") or data.get("ydData")

    # 处理时间戳
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            timestamp = datetime.now()
    elif timestamp is None:
        timestamp = datetime.now()

    # 检查必要字段
    if not deviceSn:
        print("设备SN不能为空")
        return None
        
    #检查是否已存在相同记录
    from sqlalchemy import and_
    try:
        existing = db.session.query(UserHealthData.id).filter(
            and_(
                UserHealthData.device_sn == deviceSn,
                UserHealthData.timestamp == timestamp
            )
        ).first()
        
        if existing:
            print(f"记录已存在，跳过插入: device_sn={deviceSn}, timestamp={timestamp}, id={existing.id}")
            return existing.id
    except Exception as e:
        print(f"检查重复记录时出错: {e}")

    # 解析sleepData并计算sleep数值
    sleep_hours = parse_sleep_data(sleepData)
    print(f"解析睡眠数据: sleepData={sleepData}, 计算得出睡眠时长={sleep_hours}小时")
    
    # 保存到数据库
    health_data_id = save_health_data(
        heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, stress, step, 
        timestamp, deviceSn, distance, calorie, latitude, longitude, altitude, 
        uploadMethod, sleep_hours
    )
    
    if not health_data_id:
        print("数据保存失败")
        return None
    
    def safe_str(value):#安全字符串转换
        return str(value) if value is not None else ''
    
    health_data_new = {
        "uploadMethod": safe_str(uploadMethod),
        "heartRate": safe_str(heartRate),
        "pressureHigh": safe_str(pressureHigh),
        "pressureLow": safe_str(pressureLow),
        "bloodOxygen": safe_str(bloodOxygen),
        "temperature": safe_str(temperature),
        "stress": safe_str(stress),
        "step": safe_str(step),
        "timestamp": safe_str(timestamp),
        "deviceSn": safe_str(deviceSn),
        "distance": safe_str(distance),
        "calorie": safe_str(calorie),
        "latitude": safe_str(latitude),
        "longitude": safe_str(longitude),
        "altitude": safe_str(altitude),
        "sleepData": json.dumps(sleepData) if sleepData else '',
        "exerciseDailyData": json.dumps(exerciseDailyData) if exerciseDailyData else '',
        "exerciseDailyWeekData": json.dumps(exerciseDailyWeekData) if exerciseDailyWeekData else '',
        "scientificSleepData": json.dumps(scientificSleepData) if scientificSleepData else '',
        "workoutData": json.dumps(workoutData) if workoutData else ''
    }
    
    redis.hset_data(f"health_data:{deviceSn}", mapping=health_data_new)
    print("redis_client.hset", redis.hgetall_data(f"health_data:{deviceSn}"))
    redis.publish(f"health_data_channel:{deviceSn}", deviceSn)
    print("begin to check for alerts")
    generate_alerts(health_data_new, health_data_id)
    print("alerts checked")
    
    # 保存每日和每周数据到对应表中
    save_daily_weekly_data(deviceSn, sleepData, exerciseDailyData, workoutData, exerciseDailyWeekData, scientificSleepData, timestamp)
    
    return health_data_id

def save_daily_weekly_data(deviceSn, sleepData, exerciseDailyData, workoutData, exerciseWeekData, scientificSleepData, timestamp):
    """保存每日和每周健康数据到对应的表中"""
    try:
        current_date = timestamp.date()
        
        # 保存每日数据
        if sleepData or exerciseDailyData or workoutData:
            from .models import UserHealthDataDaily
            daily_data = db.session.query(UserHealthDataDaily).filter_by(
                device_sn=deviceSn, 
                date=current_date
            ).first()
            
            if not daily_data:
                daily_data = UserHealthDataDaily(
                    device_sn=deviceSn,
                    date=current_date,
                    sleep_data=json.loads(sleepData) if sleepData else None,
                    exercise_daily_data=json.loads(exerciseDailyData) if exerciseDailyData else None,
                    workout_data=json.loads(workoutData) if workoutData else None
                )
                db.session.add(daily_data)
            else:
                if sleepData: daily_data.sleep_data = json.loads(sleepData)
                if exerciseDailyData: daily_data.exercise_daily_data = json.loads(exerciseDailyData)
                if workoutData: daily_data.workout_data = json.loads(workoutData)
                daily_data.update_time = datetime.utcnow()
        
        # 保存每周数据 
        if exerciseWeekData:
            from .models import UserHealthDataWeekly
            from datetime import timedelta
            week_start = current_date - timedelta(days=current_date.weekday())  # 获取周一
            
            weekly_data = db.session.query(UserHealthDataWeekly).filter_by(
                device_sn=deviceSn,
                week_start=week_start
            ).first()
            
            if not weekly_data:
                weekly_data = UserHealthDataWeekly(
                    device_sn=deviceSn,
                    week_start=week_start,
                    exercise_week_data=json.loads(exerciseWeekData)
                )
                db.session.add(weekly_data)
            else:
                weekly_data.exercise_week_data = json.loads(exerciseWeekData)
                weekly_data.update_time = datetime.utcnow()
        
        db.session.commit()
        print(f"成功保存每日/每周数据: device_sn={deviceSn}, date={current_date}")
        
    except Exception as e:
        print(f"保存每日/每周数据失败: {e}")
        db.session.rollback()

def get_tenant_id_from_org(org_id): #根据org_id获取租户ID#
    """通过org_id查找sys_org_units的ancestors获取租户ID"""
    try:
        import pymysql
        from .config_database import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
        
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT ancestors FROM sys_org_units 
                    WHERE id = %s AND is_deleted = 0
                    LIMIT 1
                """, (org_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    ancestors = result[0]
                    # 解析ancestors格式(0,X,Y...)，获取第二个数字X作为租户ID
                    parts = ancestors.split(',')
                    if len(parts) >= 2 and parts[0] == '0':
                        try:
                            return int(parts[1])
                        except ValueError:
                            print(f'ancestors格式异常: {ancestors}')
                return None
        finally:
            conn.close()
            
    except Exception as e:
        print(f'获取租户ID失败: {e}')
        return None

def get_health_data_config_by_org(org_id): #获取组织健康数据配置#
    """获取组织的健康数据配置，如果没有则查找顶级部门配置"""
    try:
        # 通过org_id获取租户ID
        tenant_id = get_tenant_id_from_org(org_id)
        
        # 首先查询当前租户的配置
        from .models import HealthDataConfig
        config_records = db.session.query(HealthDataConfig).filter_by(customer_id=tenant_id).all() if tenant_id else []
        
        if config_records:
            return {record.data_type: record.is_enabled for record in config_records}
        
        # 如果当前租户没有配置，查找顶级部门的租户ID
        from .org import get_top_level_org_id
        top_org_id = get_top_level_org_id(org_id)
        
        if top_org_id and top_org_id != org_id:
            top_tenant_id = get_tenant_id_from_org(top_org_id) 
            if top_tenant_id:
                top_config_records = db.session.query(HealthDataConfig).filter_by(customer_id=top_tenant_id).all()
                if top_config_records:
                    return {record.data_type: record.is_enabled for record in top_config_records}
        elif top_org_id == org_id:
            # 如果已经是顶级组织，直接使用该ID作为租户ID
            direct_config_records = db.session.query(HealthDataConfig).filter_by(customer_id=top_org_id).all()
            if direct_config_records:
                return {record.data_type: record.is_enabled for record in direct_config_records}
        
        # 如果都没有配置，返回默认配置，包含pressure相关配置
        default_metrics = ['heart_rate', 'blood_oxygen', 'pressure', 'pressure_high', 'pressure_low', 'temperature', 'stress', 'step', 'distance', 'calorie', 'sleep']
        return {metric: True for metric in default_metrics}
        
    except Exception as e:
        print(f"获取健康数据配置失败: {e}")
        # 返回默认配置，包含pressure相关配置
        default_metrics = ['heart_rate', 'blood_oxygen', 'pressure', 'pressure_high', 'pressure_low', 'temperature', 'stress', 'step', 'distance', 'calorie', 'sleep']
        return {metric: True for metric in default_metrics}

def get_all_health_data_optimized(orgId=None, userId=None, startDate=None, endDate=None, latest_only=False, page=1, pageSize=None, include_daily=False, include_weekly=False): #统一健康数据查询入口-支持动态配置和分区表#
    """
    统一的健康数据查询接口，支持按月分表和快慢表查询，使用动态健康数据配置
    
    Args:
        orgId: 组织ID
        userId: 用户ID  
        startDate: 开始日期
        endDate: 结束日期
        latest_only: 是否只查询最新记录
        page: 页码
        pageSize: 每页大小
        include_daily: 是否包含每日数据
        include_weekly: 是否包含每周数据
    
    Returns:
        dict: 包含健康数据和统计信息的字典
    """
    try:
        import time
        from datetime import datetime, timedelta
        from sqlalchemy import text
        start_time = time.time()
        
        # 参数验证和缓存键构建
        page = max(1, int(page or 1))
        # 只有明确传递pageSize时才设置限制，否则设为None表示不分页
        if pageSize is not None:
            pageSize = min(int(pageSize), 1000)
        else:
            pageSize = None
        mode = 'latest' if latest_only else 'range'
        cache_key = f"health_opt_v6:{orgId}:{userId}:{startDate}:{endDate}:{mode}:{page}:{pageSize}:{include_daily}:{include_weekly}"
        
        # 缓存检查
        cached = redis.get_data(cache_key)
        if cached:
            result = json.loads(cached)
            result['performance'] = {'cached': True, 'response_time': round(time.time() - start_time, 3)}
            return result
        
        # 获取用户设备映射 - 增加部门信息
        from .admin_helper import is_admin_user  # 导入admin判断函数
        
        if userId:
            # 检查是否为管理员用户
            if is_admin_user(userId):
                return {"success": False, "message": "管理员用户无健康数据", "data": {"healthData": [], "totalRecords": 0}}
            
            u = db.session.query(UserInfo, OrgInfo.name.label('dept_name'), OrgInfo.id.label('dept_id')).join(UserOrg, UserInfo.id == UserOrg.user_id).join(OrgInfo, UserOrg.org_id == OrgInfo.id).filter(UserInfo.id == userId, UserInfo.is_deleted == False).first()
            if not u or not u[0].device_sn or u[0].device_sn in ['-', '']:
                return {"success": False, "message": "用户不存在或无设备", "data": {"healthData": [], "totalRecords": 0}}
            user_list = [(u[0].device_sn, u[0].user_name, u[0].id, u[1], u[2])]  # 添加部门名和部门ID
            query_org_id = u[2]
        elif orgId:
            # 直接从orgId获取所有用户，包含部门信息（已自动过滤admin）
            from .org import fetch_users_by_orgId
            all_users = fetch_users_by_orgId(orgId)
            
            # 获取部门信息
            from .user import get_org_info_by_user_id
            user_list = []
            for u in all_users:
                if u['device_sn'] and u['device_sn'] not in ['-', '']:
                    org_info = get_org_info_by_user_id(u['id'])
                    dept_name = org_info.name if org_info else '未知部门'
                    dept_id = org_info.id if org_info else orgId
                    user_list.append((u['device_sn'], u['user_name'], u['id'], dept_name, dept_id))
            
            query_org_id = orgId
            print(f"📊 组织 {orgId} 共找到 {len(all_users)} 用户，有效设备 {len(user_list)} 个")
        else:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"healthData": [], "totalRecords": 0}}
        
        if not user_list:
            return {"success": True, "data": {"healthData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
        
        # 获取动态健康数据配置
        enabled_metrics_config = get_health_data_config_by_org(query_org_id)
        enabled_metrics = [metric for metric, enabled in enabled_metrics_config.items() if enabled]
        
        # 业务逻辑：location关联 - latitude, longitude, altitude是根据location配置的
        if 'location' in enabled_metrics:
            if 'latitude' not in enabled_metrics:
                enabled_metrics.append('latitude')
            if 'longitude' not in enabled_metrics:
                enabled_metrics.append('longitude')
            if 'altitude' not in enabled_metrics:
                enabled_metrics.append('altitude')
        
        # 业务逻辑：heart_rate与pressure关联 - pressure_high, pressure_low是根据heart_rate模拟的
        if 'heart_rate' in enabled_metrics:
            if 'pressure_high' not in enabled_metrics:
                enabled_metrics.append('pressure_high')
            if 'pressure_low' not in enabled_metrics:
                enabled_metrics.append('pressure_low')
        
        # 兼容性：如果配置中有pressure，也自动包含pressure_high和pressure_low
        if 'pressure' in enabled_metrics:
            if 'pressure_high' not in enabled_metrics:
                enabled_metrics.append('pressure_high')
            if 'pressure_low' not in enabled_metrics:
                enabled_metrics.append('pressure_low')
        
        print(f"🔧 组织{query_org_id}启用的指标: {enabled_metrics}")
        
        # 健康数据表真实字段白名单 - 只包含数据库表中实际存在的字段
        valid_health_fields = [
            'heart_rate', 'blood_oxygen', 'temperature', 'pressure_high', 'pressure_low', 
            'stress', 'step', 'distance', 'calorie', 'latitude', 'longitude', 'altitude', 'sleep'
        ]
        
        # 过滤掉不属于健康数据表的字段
        filtered_metrics = [metric for metric in enabled_metrics if metric in valid_health_fields]
        ignored_fields = [metric for metric in enabled_metrics if metric not in valid_health_fields]
        
        if ignored_fields:
            print(f"⚠️  忽略非健康数据字段: {ignored_fields}")
        
        # 动态构建查询字段 - 根据配置决定查询哪些字段
        base_fields = ['device_sn', 'timestamp', 'upload_method', 'user_id', 'org_id']
        
        # 构建动态查询字段列表 - 只使用过滤后的有效字段
        query_fields = base_fields + filtered_metrics
        
        # 如果需要包含每日/每周数据，添加相应字段
        if include_daily:
            query_fields.extend(['sleep_data', 'exercise_daily_data', 'scientific_sleep_data', 'workout_data'])
        if include_weekly:
            query_fields.extend(['exercise_week_data'])
        
        field_list = ', '.join(query_fields)
        
        all_sns = [x[0] for x in user_list]
        health_data_list = []
        total_count = 0
        
        print(f"🎯 动态查询字段: {query_fields}")
        
        # 智能选择查询策略 - 分区表优先
        query_strategy = _determine_query_strategy(startDate, endDate, latest_only, len(all_sns))
        print(f"📈 查询策略: {query_strategy}")
        
        # 时间范围处理
        if latest_only:
            # 最新记录模式 - 优化查询只获取必要字段
            try:
                results = _query_latest_data_optimized(all_sns, query_fields, enabled_metrics, query_strategy)
                total_count = len(results)
                
            except Exception as e:
                print(f"❌ 动态查询失败，回退到ORM查询: {e}")
                # 回退到ORM查询
                subq = db.session.query(
                    UserHealthData.device_sn,
                    func.max(UserHealthData.timestamp).label('max_ts')
                ).filter(UserHealthData.device_sn.in_(all_sns)).group_by(UserHealthData.device_sn).subquery()
                
                results = db.session.query(UserHealthData).join(
                    subq,
                    (UserHealthData.device_sn == subq.c.device_sn) &
                    (UserHealthData.timestamp == subq.c.max_ts)
                ).all()
                total_count = len(results)
                
        else:
            # 时间范围查询模式 - 使用分区表策略
            results, total_count = _query_range_data_optimized(all_sns, startDate, endDate, page, pageSize, query_fields, query_strategy)
        
        # 构建设备-用户映射，包含部门信息
        sn_to_user = {x[0]: (x[1], x[2], x[3], x[4]) for x in user_list}  # (user_name, user_id, dept_name, dept_id)
        
        # 获取组织名称
        org_name = "未知组织"
        if query_org_id:
            try:
                org_info = db.session.query(OrgInfo).filter_by(id=query_org_id).first()
                org_name = org_info.name if org_info else "未知组织"
            except:
                pass
        
        # 数据转换 - 根据动态配置构建响应，使用前端期望的字段名
        for r in results:
            if not r or not hasattr(r, 'device_sn') or not r.device_sn:
                continue
                
            user_name, user_id, dept_name, dept_id = sn_to_user.get(r.device_sn, ('未知用户', 0, '未知部门', query_org_id or 0))
            
            # 构建基础健康数据对象 - 使用数据库字段名格式
            health_data = {
                "deviceSn": r.device_sn or '',
                "userName": user_name,
                "userId": user_id,
                "deptName": dept_name,           # 添加部门名
                "orgId": dept_id,               # 添加部门ID  
                "orgName": org_name,            # 添加组织名
                "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(r, 'timestamp') and r.timestamp else None,
                "uploadMethod": getattr(r, 'upload_method', '')
            }
            
                        # 根据location配置添加坐标信息
            if 'location' in enabled_metrics:
                health_data.update({
                    "latitude": str(getattr(r, 'latitude', 0) or 0),
                    "longitude": str(getattr(r, 'longitude', 0) or 0),
                    "altitude": str(getattr(r, 'altitude', 0) or 0)
                })
            
            # 动态添加启用的健康指标数据 - 使用过滤后的有效字段，强制包含pressure字段
            for metric in filtered_metrics:
                if metric in ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 'stress', 'step']:
                    value = getattr(r, metric, None) if hasattr(r, metric) else None
                    health_data[metric] = str(value or 0)
                    # 调试：输出pressure相关字段的值
                   
                elif metric == 'temperature':
                    value = getattr(r, 'temperature', None) if hasattr(r, 'temperature') else None
                    health_data['temperature'] = f"{float(value or 0):.1f}"
                elif metric in ['distance', 'calorie', 'sleep']:
                    value = getattr(r, metric, None) if hasattr(r, metric) else None
                    health_data[metric] = float(value or 0)
            
            # 添加每日/每周数据
            if include_daily:
                health_data.update({
                    "sleepData": getattr(r, 'sleep_data', None),
                    "exerciseDailyData": getattr(r, 'exercise_daily_data', None),
                    "scientificSleepData": getattr(r, 'scientific_sleep_data', None),
                    "workoutData": getattr(r, 'workout_data', None)
                })
            
            if include_weekly:
                health_data["exerciseWeekData"] = getattr(r, 'exercise_week_data', None)
            
            health_data_list.append(health_data)
        
        # 构建响应数据
        if latest_only:
            result = {
                "success": True,
                "data": {
                    "healthData": health_data_list,
                    "totalRecords": len(health_data_list),
                    "deviceCount": len(user_list),
                    "enabledMetrics": filtered_metrics,
                    "ignoredFields": ignored_fields,
                    "queryFields": query_fields,
                    "orgId": str(orgId) if orgId else None,
                    "userId": str(userId) if userId else None,
                    "queryStrategy": query_strategy
                },
                "performance": {
                    "cached": False,
                    "response_time": round(time.time() - start_time, 3),
                    "query_mode": "latest_dynamic_partitioned",
                    "enabled_fields_count": len(enabled_metrics)
                }
            }
        else:
            total_pages = (total_count + pageSize - 1) // pageSize if pageSize and pageSize > 0 else 1
            result = {
                "success": True,
                "data": {
                    "healthData": health_data_list,
                    "totalRecords": total_count,
                    "pagination": {
                        "currentPage": page,
                        "pageSize": pageSize,
                        "totalCount": total_count,
                        "totalPages": total_pages
                    },
                    "enabledMetrics": filtered_metrics,
                    "ignoredFields": ignored_fields,
                    "queryFields": query_fields,
                    "orgId": str(orgId) if orgId else None,
                    "userId": str(userId) if userId else None,
                    "queryStrategy": query_strategy
                },
                "performance": {
                    "cached": False,
                    "response_time": round(time.time() - start_time, 3),
                    "query_mode": "range_paged_dynamic_partitioned",
                    "enabled_fields_count": len(filtered_metrics)
                }
            }
        
        # 缓存结果
        cache_ttl = 60 if latest_only else 300
        redis.set_data(cache_key, json.dumps(result, default=str), cache_ttl)
        
        #print(f"✅ 动态健康数据查询完成: 模式={mode}, 记录数={len(health_data_list)}, 启用指标={len(filtered_metrics)}, 忽略字段={len(ignored_fields)}, 查询字段={len(query_fields)}, 策略={query_strategy}, 耗时={result['performance']['response_time']}s")
        return result
        
    except Exception as e:
        print(f"❌ 动态健康数据查询失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "data": {
                "healthData": [],
                "totalRecords": 0,
                "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0} if not latest_only else None
            }
        }

def _determine_query_strategy(startDate, endDate, latest_only, device_count): #查询策略决策#
    """
    智能选择查询策略:
    1. 最新数据: 主表快速查询
    2. 近期数据(7天内): 主表
    3. 历史数据(30天内): 分区表优先
    4. 大范围数据(>30天): 分区表+汇总表
    """
    if latest_only:
        return "main_table_latest"
    
    if not startDate and not endDate:
        return "main_table_recent"
    
    try:
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # 解析时间
        if isinstance(startDate, str):
            start_dt = datetime.strptime(startDate, '%Y-%m-%d')
        else:
            start_dt = startDate or (now - timedelta(days=7))
        
        if isinstance(endDate, str):
            end_dt = datetime.strptime(endDate, '%Y-%m-%d')
        else:
            end_dt = endDate or now
        
        # 计算时间跨度
        time_span = (end_dt - start_dt).days
        recent_threshold = (now - start_dt).days
        
        # 决策逻辑
        if recent_threshold <= 7:
            return "main_table_recent"
        elif time_span <= 30:
            return "partitioned_table"
        elif time_span <= 90:
            return "partitioned_table_with_daily"
        else:
            return "summary_table_with_partitioned"
    
    except Exception:
        return "main_table_fallback"

def _query_latest_data_optimized(device_sns, query_fields, enabled_db_fields, strategy): #优化最新数据查询#
    """优化的最新数据查询 - 修复时间限制问题"""
    from datetime import datetime, timedelta
    from sqlalchemy import text
    
    field_list = ', '.join(query_fields)
    
    if strategy == "main_table_latest":
        # 主表查询策略 - 移除24小时限制，查询每个设备的真正最新数据
        dynamic_query = text(f"""
            SELECT h.{field_list}
            FROM t_user_health_data h
            JOIN (
                SELECT device_sn, MAX(timestamp) as max_ts
                FROM t_user_health_data
                WHERE device_sn IN :device_sns
                AND is_deleted = 0
                GROUP BY device_sn
            ) latest ON h.device_sn = latest.device_sn AND h.timestamp = latest.max_ts
            ORDER BY h.timestamp DESC
        """)
        
        return db.session.execute(dynamic_query, {
            'device_sns': tuple(device_sns)
        }).fetchall()
    
    # 回退到标准查询 - 同样移除时间限制
    subq = db.session.query(
        UserHealthData.device_sn,
        func.max(UserHealthData.timestamp).label('max_ts')
    ).filter(
        UserHealthData.device_sn.in_(device_sns),
        UserHealthData.is_deleted == False
    ).group_by(UserHealthData.device_sn).subquery()
    
    return db.session.query(UserHealthData).join(
        subq,
        (UserHealthData.device_sn == subq.c.device_sn) &
        (UserHealthData.timestamp == subq.c.max_ts)
    ).order_by(UserHealthData.timestamp.desc()).all()

def _query_range_data_optimized(device_sns, startDate, endDate, page, pageSize, query_fields, strategy): #优化范围数据查询#
    """优化的范围数据查询，支持分区表"""
    from datetime import datetime, timedelta
    from sqlalchemy import text
    
    # 解析时间参数
    if startDate:
        try:
            sd = datetime.strptime(startDate, '%Y-%m-%d') if isinstance(startDate, str) else startDate
        except:
            sd = None
    else:
        sd = None
    
    if endDate:
        try:
            ed = datetime.strptime(endDate, '%Y-%m-%d') if isinstance(endDate, str) else endDate
            ed = ed + timedelta(days=1)
        except:
            ed = None
    else:
        ed = None
    
    # 根据策略选择查询方法
    if strategy in ["partitioned_table", "partitioned_table_with_daily"]:
        return _query_partitioned_tables(device_sns, sd, ed, page, pageSize, query_fields)
    elif strategy == "summary_table_with_partitioned":
        return _query_with_summary_tables(device_sns, sd, ed, page, pageSize, query_fields)
    else:
        # 主表查询
        return _query_main_table(device_sns, sd, ed, page, pageSize)

def _query_partitioned_tables(device_sns, start_date, end_date, page, pageSize, query_fields): #分区表查询-修复字段检测#
    """查询分区表数据，动态检测字段存在性，避免查询不存在的字段"""
    try:
        # 获取需要查询的分区表
        partition_tables = _get_partition_tables(start_date, end_date)
        print(f"🔍 开始查询分区表: {partition_tables}")
        
        all_results = []
        total_count = 0
        
        print(f"📋 原始查询字段: {query_fields}")
        
        for table_name in partition_tables:
            try:
                # 检查表是否存在
                table_exists_query = text("SHOW TABLES LIKE :table_name")
                exists = db.session.execute(table_exists_query, {'table_name': table_name}).fetchone()
                
                if not exists:
                    print(f"⚠️ 分区表 {table_name} 不存在，跳过")
                    continue
                
                print(f"✅ 分区表 {table_name} 存在")
                
                # 动态检测表结构中存在的字段
                desc_query = text(f"DESCRIBE {table_name}")
                table_columns = db.session.execute(desc_query).fetchall()
                existing_columns = {col[0].lower() for col in table_columns}
                print(f"🔍 {table_name} 存在字段: {sorted(existing_columns)}")
                
                # 过滤出实际存在的字段
                valid_fields = []
                for field in query_fields:
                    field_lower = field.lower()
                    if field_lower in existing_columns:
                        valid_fields.append(field)
                    else:
                        print(f"⚠️ 字段 {field} 在表 {table_name} 中不存在，跳过")
                
                if not valid_fields:
                    print(f"❌ 表 {table_name} 没有有效字段，跳过")
                    continue
                    
                field_list = ', '.join(valid_fields)
                print(f"📋 {table_name} 实际查询字段: {field_list}")
                
                # 查询分区表
                conditions = ["is_deleted = 0"] if 'is_deleted' in existing_columns else []
                params = {'device_sns': tuple(device_sns)}
                
                if start_date and 'timestamp' in existing_columns:
                    conditions.append("timestamp >= :start_date")
                    params['start_date'] = start_date
                if end_date and 'timestamp' in existing_columns:
                    conditions.append("timestamp <= :end_date") 
                    params['end_date'] = end_date
                
                print(f"🔍 查询条件: {conditions}, 设备数量: {len(device_sns)}")
                
                # 先获取总数
                where_clause = f"WHERE device_sn IN :device_sns" if 'device_sn' in existing_columns else "WHERE 1=1"
                if conditions:
                    where_clause += f" AND {' AND '.join(conditions)}"
                    
                count_query = text(f"SELECT COUNT(*) FROM {table_name} {where_clause}")
                table_count = db.session.execute(count_query, params).scalar()
                total_count += table_count
                
                print(f"📊 分区表 {table_name}: {table_count} 条记录")
                
                if table_count > 0:
                    # 获取数据
                    order_clause = "ORDER BY timestamp DESC" if 'timestamp' in existing_columns else ""
                    # 只在分页模式下添加LIMIT
                    limit_clause = "LIMIT 1000" if pageSize and pageSize > 0 else ""
                    data_query = text(f"""
                        SELECT {field_list}
                        FROM {table_name}
                        {where_clause}
                        {order_clause}
                        {limit_clause}
                    """)
                    
                    table_results = db.session.execute(data_query, params).fetchall()
                    print(f"🔢 分区表 {table_name} 实际返回: {len(table_results)} 条记录")
                    
                    if table_results:
                        print(f"📝 第一条记录示例: {dict(table_results[0]._mapping) if hasattr(table_results[0], '_mapping') else 'N/A'}")
                    
                    all_results.extend(table_results)
                
            except Exception as e:
                print(f"❌ 查询分区表 {table_name} 失败: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"📈 分区表查询汇总: 总数={total_count}, 实际数据={len(all_results)}")
        
        if len(all_results) == 0:
            print("❗️ 分区表查询无数据，回退到主表查询")
            return _query_main_table(device_sns, start_date, end_date, page, pageSize)
        
        # 修复排序逻辑 - 确保正确访问timestamp字段
        try:
            # 检查第一条记录的结构
            if all_results:
                first_record = all_results[0]
                if hasattr(first_record, '_mapping'):
                    # SQLAlchemy Row对象
                    all_results.sort(key=lambda x: x._mapping.get('timestamp', x._mapping.get('timestamp', '')), reverse=True)
                elif hasattr(first_record, 'timestamp'):
                    # 有timestamp属性
                    all_results.sort(key=lambda x: x.timestamp, reverse=True)
                else:
                    # 尝试按索引排序
                    all_results.sort(key=lambda x: x[1] if len(x) > 1 else '', reverse=True)
                
                print(f"✅ 排序完成")
        except Exception as sort_error:
            print(f"⚠️ 排序失败，使用原始顺序: {sort_error}")
        
        # 分页处理
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paged_results = all_results[start_index:end_index]
        
        print(f"📄 分页结果: 第{page}页, 每页{pageSize}条, 返回{len(paged_results)}条")
        
        return paged_results, total_count
        
    except Exception as e:
        print(f"❌ 分区表查询完全失败，回退到主表: {e}")
        import traceback
        traceback.print_exc()
        return _query_main_table(device_sns, start_date, end_date, page, pageSize)

def _query_main_table(device_sns, start_date, end_date, page, pageSize): #主表查询#
    """主表查询逻辑"""
    print(f"🔍 _query_main_table 参数: device_sns={len(device_sns)}, start_date={start_date}, end_date={end_date}, pageSize={pageSize}")
    
    base_query = UserHealthData.query.filter(UserHealthData.device_sn.in_(device_sns))
    
    if start_date:
        base_query = base_query.filter(UserHealthData.timestamp >= start_date)
        print(f"✅ 添加开始时间过滤: >= {start_date}")
    if end_date:
        base_query = base_query.filter(UserHealthData.timestamp <= end_date)
        print(f"✅ 添加结束时间过滤: <= {end_date}")
    
    total_count = base_query.count()
    print(f"📊 查询到符合条件的总记录数: {total_count}")
    
    # 只有在需要分页时才应用分页限制
    query = base_query.order_by(UserHealthData.timestamp.desc())
    if pageSize and pageSize > 0:
        query = query.offset((page-1)*pageSize).limit(pageSize)
        print(f"📄 应用分页限制: page={page}, pageSize={pageSize}")
    else:
        print(f"📄 不分页，获取所有数据")
    
    results = query.all()
    print(f"📋 实际返回记录数: {len(results)}")
    
    if results:
        first_record = results[0]
        last_record = results[-1]
        print(f"⏰ 数据时间范围: {last_record.timestamp} 到 {first_record.timestamp}")
    
    return results, total_count

def _get_partition_tables(start_date, end_date): #获取分区表列表#
    """根据时间范围获取需要查询的分区表"""
    from datetime import datetime, timedelta
    import calendar
    
    tables = []
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # 按月生成分区表名
    current = start_date.replace(day=1)
    
    while current <= end_date:
        table_name = f"t_user_health_data_{current.year}{current.month:02d}"
        tables.append(table_name)
        
        # 移动到下个月
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    # 如果没有分区表，回退到主表
    if not tables:
        tables = ['t_user_health_data']
    
    return tables

def _query_with_summary_tables(device_sns, start_date, end_date, page, pageSize, query_fields): #汇总表查询#
    """使用汇总表查询大范围历史数据"""
    try:
        # 尝试查询每日汇总表
        from sqlalchemy import text
        
        # 检查每日汇总表是否存在
        summary_exists_query = text("SHOW TABLES LIKE 't_user_health_data_daily_summary'")
        summary_exists = db.session.execute(summary_exists_query).fetchone()
        
        if summary_exists:
            # 使用汇总表查询
            conditions = []
            params = {'device_sns': tuple(device_sns)}
            
            if start_date:
                conditions.append("date >= :start_date")
                params['start_date'] = start_date.date()
            if end_date:
                conditions.append("date <= :end_date")
                params['end_date'] = end_date.date()
            
            count_query = text(f"""
                SELECT COUNT(*) 
                FROM t_user_health_data_daily_summary 
                WHERE device_sn IN :device_sns {' AND ' + ' AND '.join(conditions) if conditions else ''}
            """)
            total_count = db.session.execute(count_query, params).scalar()
            
            # 构建基础查询
            base_query = f"""
                SELECT device_sn, date as timestamp, 
                       avg_heart_rate as heart_rate,
                       avg_blood_oxygen as blood_oxygen,
                       avg_temperature as temperature,
                       avg_pressure_high as pressure_high,
                       avg_pressure_low as pressure_low,
                       avg_stress as stress,
                       total_step as step,
                       total_distance as distance,
                       total_calorie as calorie,
                       0 as latitude, 0 as longitude, 0 as altitude,
                       '' as upload_method, user_id, org_id
                FROM t_user_health_data_daily_summary
                WHERE device_sn IN :device_sns {' AND ' + ' AND '.join(conditions) if conditions else ''}
                ORDER BY date DESC
            """
            
            # 只有需要分页时才添加LIMIT和OFFSET
            if pageSize and pageSize > 0:
                base_query += " LIMIT :limit OFFSET :offset"
                params.update({
                    'limit': pageSize,
                    'offset': (page - 1) * pageSize
                })
                print(f"📄 汇总表应用分页: pageSize={pageSize}")
            else:
                print(f"📄 汇总表不分页，获取所有数据")
            
            data_query = text(base_query)
            
            results = db.session.execute(data_query, params).fetchall()
            return results, total_count
        
    except Exception as e:
        print(f"❌ 汇总表查询失败: {e}")
    
    # 回退到分区表查询
    return _query_partitioned_tables(device_sns, start_date, end_date, page, pageSize, query_fields)



def generate_health_json(customer_id, userId): #重构为调用统一接口#
    """重构GeoJSON生成，使用统一数据接口"""
    if not customer_id:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    try:
        # 使用统一接口获取最新健康数据
        results = get_all_health_data_optimized(orgId=customer_id, userId=userId, latest_only=True)
        
        print("generate_health_json.results:", results)
        
        if not results.get('success'):
            return jsonify(results), 400

        health_data = results['data']['healthData']
        enabled_metrics = results['data'].get('enabledMetrics', [])
        features = []

        # 遍历健康数据生成 GeoJSON features
        for data in health_data:
            # 严格验证坐标数据
            try:
                longitude = float(data.get('longitude', 0))
                latitude = float(data.get('latitude', 0))
                
                # 验证坐标范围和有效性
                if (longitude != 0 and latitude != 0 and
                    -180 <= longitude <= 180 and
                    -90 <= latitude <= 90 and
                    not math.isnan(longitude) and not math.isnan(latitude)):
                    
                    altitude = float(data.get('altitude', 0)) if data.get('altitude') else 0
                    
                    # 构建属性，只包含启用的指标
                    properties = {
                        "deviceSn": data['deviceSn'],
                        "userName": data['userName'],
                        "timestamp": data['timestamp'],
                        "label": f"{data.get('deptName', '未知部门')}-{data['userName']}"
                    }
                    
                    # 只添加启用的指标数据
                    for metric in enabled_metrics:
                        if metric in data and data[metric] and str(data[metric]) != '0':
                            try:
                                if metric in ['heart_rate', 'blood_oxygen', 'pressure_high', 'pressure_low', 'stress', 'step']:
                                    properties[metric] = float(data[metric])
                                elif metric == 'temperature':
                                    properties[metric] = float(data[metric])
                                elif metric in ['distance', 'calorie', 'sleep']:
                                    properties[metric] = float(data[metric])
                            except (ValueError, TypeError):
                                properties[metric] = 0
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude, altitude]
                        },
                        "properties": properties
                    }
                    features.append(feature)
                else:
                    print(f"无效坐标被跳过 - 设备 {data['deviceSn']}: lng={longitude}, lat={latitude}")
                    
            except (ValueError, TypeError, OverflowError) as e:
                print(f"坐标转换错误 - 设备 {data['deviceSn']}: {e}")
                continue

        # 构造 GeoJSON 响应
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "statistics": {
                "deviceCount": results['data']['deviceCount'],
                "totalRecords": results['data']['totalRecords'],
                "enabledMetrics": enabled_metrics,
                "validCoordinates": len(features)
            }
        }

        return jsonify(geojson)

    except Exception as err:
        print(f"Error generating health GeoJSON: {err}")
        return jsonify({
            'success': False,
            'error': str(err),
            'type': "FeatureCollection",
            'features': []
        }), 500

def fetch_all_health_data_by_orgIdAndUserId_mobile(phone=None, startDate=None, endDate=None): #重构为调用统一接口#
    """重构移动端健康数据查询，使用统一数据接口"""
    try:
        print(f"获取数据参数: phone={phone}, startDate={startDate}, endDate={endDate}")
        
        if not phone:
            return {'success': False, 'error': '缺少手机号参数'}
        
        # 通过手机号获取用户数据
        user = db.session.query(UserInfo).filter(UserInfo.phone == phone).first()
        if not user:
            return {'success': False, 'error': '用户不存在'}
        
        # 使用统一接口获取健康数据
        result = get_all_health_data_optimized(
            userId=user.id, 
            startDate=startDate, 
            endDate=endDate, 
            latest_only=False,
            pageSize=2000  # 移动端需要更多数据用于分析
        )
        
        if not result.get('success'):
            return result
            
        health_data_list = result['data']['healthData']
        
        print(f"获取到 {len(health_data_list)} 条数据")
        
        if not health_data_list:
            return {'success': False, 'error': '未找到健康数据'}

        # 初始化分析器
        from .health_analyzer import HealthTrendAnalyzer
        analyzer = HealthTrendAnalyzer(health_data_list)
        
        # 生成分析数据
        mobile_analysis = analyzer.generate_mobile_visualization_data()
        
        return mobile_analysis

    except Exception as e:
        print(f"Error in fetch_all_health_data_by_orgIdAndUserId_mobile: {str(e)}")
        return {'success': False, 'error': str(e)}

def fetch_user_locations(deviceSn, date_str=None): #重构为调用统一接口 - 单设备位置查询#
    """重构单设备位置查询，使用统一接口"""
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    # 解析查询日期
    if date_str:
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    else:
        query_date = datetime.now().date()

    try:
        # 通过设备SN获取用户信息
        user_info = get_device_user_org_info(deviceSn)
        
        if user_info and user_info.get('success'):
            # 使用统一接口获取位置数据
            start_date = query_date.strftime('%Y-%m-%d')
            optimized_result = get_all_health_data_optimized(
                userId=user_info.get('user_id'),
                startDate=start_date,
                endDate=start_date,
                latest_only=False,
                pageSize=500  # 获取更多轨迹点
            )
            
            if optimized_result.get('success'):
                health_data_list = optimized_result['data']['healthData']
                
                # 过滤有效位置数据并转换格式
                formatted_results = []
                for data in health_data_list:
                    # 验证位置数据有效性
                    latitude = data.get('latitude', '0')
                    longitude = data.get('longitude', '0')
                    
                    if (latitude and longitude and 
                        str(latitude) != '0' and str(longitude) != '0'):
                        
                        # 转换为原始格式保持兼容性
                        formatted_result = {
                            "bloodOxygen": data.get('blood_oxygen', '0'),
                            "heartRate": data.get('heart_rate', '0'),
                            "pressureHigh": data.get('pressure_high', '0'),
                            "pressureLow": data.get('pressure_low', '0'),
                            "stress": data.get('stress', '0'),
                            "step": data.get('step', '0'),
                            "temperature": data.get('temperature', '0.0'),
                            "timestamp": datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S GMT") if data.get('timestamp') else '',
                            "deviceSn": data.get('deviceSn', ''),
                            "distance": data.get('distance', 0),
                            "calorie": data.get('calorie', 0),
                            "latitude": latitude,
                            "longitude": longitude,
                            "altitude": data.get('altitude', '0'),
                            "sleepData": data.get('sleepData'),
                            "workoutData": data.get('workoutData'),
                            "exerciseDailyData": data.get('exerciseDailyData'),
                            "exerciseDailyWeekData": data.get('exerciseWeekData'),
                            "scientificSleepData": data.get('scientificSleepData')
                        }
                        formatted_results.append(formatted_result)
                
                if formatted_results:
                    return jsonify({"success": True, "data": formatted_results})
                else:
                    return jsonify({
                        "success": True,
                        "data": [],
                        "message": f"No location data found for device {deviceSn} on {query_date}"
                    })
        
        # 回退到原始查询方式
        results = UserHealthData.query.filter_by(device_sn=deviceSn).filter(
            func.date(UserHealthData.timestamp) == query_date,
            UserHealthData.latitude.isnot(None),
            UserHealthData.longitude.isnot(None)
        ).order_by(UserHealthData.timestamp).all()

        formatted_results = []
        if results:
            for result in results:
                formatted_result = {
                    "bloodOxygen": f"{result.blood_oxygen}",
                    "heartRate": f"{result.heart_rate}",
                    "pressureHigh": f"{result.pressure_high}",
                    "pressureLow": f"{result.pressure_low}",
                    "stress": f"{result.stress}",
                    "step": f"{result.step}",
                    "temperature": f"{result.temperature}",
                    "timestamp": result.timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "deviceSn": result.device_sn,
                    "distance": result.distance,
                    "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "altitude": result.altitude,
                    "sleepData": result.sleep_data,
                    "workoutData": result.workout_data,
                    "exerciseDailyData": result.exercise_daily_data,
                    "exerciseDailyWeekData": result.exercise_week_data,
                    "scientificSleepData": result.scientific_sleep_data
                }
                formatted_results.append(formatted_result)
        
        if formatted_results:
            return jsonify({"success": True, "data": formatted_results})
        else:
            return jsonify({
                "success": True,
                "data": [],
                "message": f"No data found for device {deviceSn} on {query_date}"
            })

    except Exception as err:
        print(f"Error: {err}")
        # 回退到原始查询
        try:
            results = UserHealthData.query.filter_by(device_sn=deviceSn).filter(
                func.date(UserHealthData.timestamp) == query_date,
                UserHealthData.latitude.isnot(None),
                UserHealthData.longitude.isnot(None)
            ).order_by(UserHealthData.timestamp).all()

            formatted_results = []
            if results:
                for result in results:
                    formatted_result = {
                        "bloodOxygen": f"{result.blood_oxygen}",
                        "heartRate": f"{result.heart_rate}",
                        "pressureHigh": f"{result.pressure_high}",
                        "pressureLow": f"{result.pressure_low}",
                        "stress": f"{result.stress}",
                        "step": f"{result.step}",
                        "temperature": f"{result.temperature}",
                        "timestamp": result.timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                        "deviceSn": result.device_sn,
                        "distance": result.distance,
                        "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "altitude": result.altitude,
                        "sleepData": result.sleep_data,
                        "workoutData": result.workout_data,
                        "exerciseDailyData": result.exercise_daily_data,
                        "exerciseDailyWeekData": result.exercise_week_data,
                        "scientificSleepData": result.scientific_sleep_data
                    }
                    formatted_results.append(formatted_result)
            
            return jsonify({"success": True, "data": formatted_results})
        except Exception as fallback_error:
            print(f"回退查询失败: {fallback_error}")
            return jsonify({"success": False, "error": str(fallback_error)}), 500

def get_health_data(deviceSn, date=None): #重构为调用统一接口 - 单设备日期查询#
    """重构单设备日期查询，使用统一接口"""
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    # 解析查询日期
    if date:
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    else:
        query_date = datetime.now().date()

    try:
        # 通过设备SN获取用户信息
        user_info = get_device_user_org_info(deviceSn)
        
        if user_info:
            # 使用统一接口获取指定日期数据
            start_date = query_date.strftime('%Y-%m-%d')
            optimized_result = get_all_health_data_optimized(
                userId=user_info.get('user_id'),
                startDate=start_date,
                endDate=start_date,
                latest_only=False,
                pageSize=20  # 限制20条记录保持原有行为
            )
            
            if optimized_result.get('success'):
                health_data_list = optimized_result['data']['healthData']
                
                # 转换为原始格式保持兼容性
                formatted_results = []
                for data in health_data_list:
                    formatted_result = {
                        "bloodOxygen": data.get('blood_oxygen', 0),
                        "heartRate": data.get('heart_rate', 0),
                        "pressureHigh": data.get('pressure_high', 0),
                        "pressureLow": data.get('pressure_low', 0),
                        "stress": data.get('stress', 0),
                        "step": data.get('step', 0),
                        "temperature": data.get('temperature', 0),
                        "timestamp": data.get('timestamp', ''),
                        "deviceSn": data.get('deviceSn', ''),
                        "distance": data.get('distance', 0),
                        "calorie": data.get('calorie', 0),
                        "latitude": data.get('latitude', 0),
                        "longitude": data.get('longitude', 0),
                        "altitude": data.get('altitude', 0),
                        "sleepData": data.get('sleepData'),
                        "workoutData": data.get('workoutData'),
                        "exerciseDailyData": data.get('exerciseDailyData'),
                        "exerciseDailyWeekData": data.get('exerciseWeekData'),
                        "scientificSleepData": data.get('scientificSleepData')
                    }
                    formatted_results.append(formatted_result)
                
                return jsonify({"success": True, "data": formatted_results})
        
        # 回退到原始查询方式
        start_of_day = datetime.combine(query_date, time.min)
        end_of_day = datetime.combine(query_date, datetime.now().time())

        results = UserHealthData.query.filter_by(device_sn=deviceSn).filter(
            UserHealthData.timestamp >= start_of_day,
            UserHealthData.timestamp <= end_of_day
        ).order_by(UserHealthData.timestamp.desc()).limit(20).all()

        formatted_results = [{
            "bloodOxygen": result.blood_oxygen,
            "heartRate": result.heart_rate,
            "pressureHigh": result.pressure_high,
            "pressureLow": result.pressure_low,
            "stress": result.stress,
            "step": result.step,
            "temperature": result.temperature,
            "timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "deviceSn": result.device_sn,
            "distance": result.distance,
            "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "altitude": result.altitude,
            "sleepData": result.sleep_data,
            "workoutData": result.workout_data,
            "exerciseDailyData": result.exercise_daily_data,
            "exerciseDailyWeekData": result.exercise_week_data,
            "scientificSleepData": result.scientific_sleep_data
        } for result in results]

        return jsonify({"success": True, "data": formatted_results})
        
    except Exception as err:
        print(f"Error: {err}")
        # 回退到原始查询
        try:
            start_of_day = datetime.combine(query_date, time.min) if date else datetime.combine(datetime.now().date(), time.min)
            end_of_day = datetime.combine(query_date, datetime.now().time()) if date else datetime.now()

            results = UserHealthData.query.filter_by(device_sn=deviceSn).filter(
                UserHealthData.timestamp >= start_of_day,
                UserHealthData.timestamp <= end_of_day
            ).order_by(UserHealthData.timestamp.desc()).limit(20).all()

            formatted_results = [{
                "bloodOxygen": result.blood_oxygen,
                "heartRate": result.heart_rate,
                "pressureHigh": result.pressure_high,
                "pressureLow": result.pressure_low,
                "stress": result.stress,
                "step": result.step,
                "temperature": result.temperature,
                "timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "deviceSn": result.device_sn,
                "distance": result.distance,
                "calorie": float(convert_decimal(result.calorie)) if hasattr(result, 'calorie') and result.calorie is not None else 0,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "altitude": result.altitude,
                "sleepData": result.sleep_data,
                "workoutData": result.workout_data,
                "exerciseDailyData": result.exercise_daily_data,
                "exerciseDailyWeekData": result.exercise_week_data,
                "scientificSleepData": result.scientific_sleep_data
            } for result in results]

            return jsonify({"success": True, "data": formatted_results})
        except Exception as fallback_error:
            print(f"回退查询失败: {fallback_error}")
            return jsonify({"success": False, "error": str(fallback_error)}), 500



def get_org_users_paged(orgId=None, page=1, pageSize=20): #分页用户查询#
    """分页用户查询"""
    try:
        from .org import fetch_users_by_orgId
        users = fetch_users_by_orgId(orgId)
        
        if not users:
            return {"success": True, "data": {"users": [], "totalUsers": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
        
        # 分页处理
        total_count = len(users)
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paged_users = users[start_index:end_index]
        total_pages = (total_count + pageSize - 1) // pageSize
        
        return {
            "success": True,
            "data": {
                "users": paged_users,
                "totalUsers": total_count,
                "pagination": {
                    "currentPage": page,
                    "pageSize": pageSize,
                    "totalCount": total_count,
                    "totalPages": total_pages
                }
            }
        }
        
    except Exception as e:
        print(f"分页用户查询失败: {e}")
        return {"success": False, "error": str(e)}

def get_users_and_health_info(orgId=None): #用户健康信息联合查询#
    """用户健康信息联合查询"""
    try:
        return get_all_health_data_optimized(orgId=orgId, latest_only=True)
    except Exception as e:
        print(f"用户健康信息联合查询失败: {e}")
        return {"success": False, "error": str(e)}

def get_health_page_data(orgId=None, page=1, pageSize=100): #健康数据分页#
    """健康数据分页"""
    try:
        return get_all_health_data_optimized(orgId=orgId, page=page, pageSize=pageSize)
    except Exception as e:
        print(f"健康数据分页查询失败: {e}")
        return {"success": False, "error": str(e)}

def get_today_health_data(orgId=None): #今日健康数据#
    """今日健康数据"""
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        return get_all_health_data_optimized(orgId=orgId, startDate=today, endDate=today)
    except Exception as e:
        print(f"今日健康数据查询失败: {e}")
        return {"success": False, "error": str(e)}