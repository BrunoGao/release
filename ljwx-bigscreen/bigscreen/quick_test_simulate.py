#!/usr/bin/env python3
"""快速测试模拟脚本"""
import requests,json,random
from datetime import datetime,timedelta

# 配置
API_URL = "http://localhost:5001/upload_health_data"
BASELINE_API = "http://localhost:5001/api/baseline/generate"

def quick_test():
    """快速测试"""
    print("快速测试模拟数据上传...")
    
    # 测试设备
    test_devices = ['A5GTQ24B26000732', 'TEST001', 'TEST002']
    
    # 生成最近3天的数据
    for device_sn in test_devices:
        print(f"生成设备{device_sn}的数据...")
        
        for day in range(3):
            target_date = datetime.now() - timedelta(days=day)
            
            # 每天生成12条数据（每2小时一条）
            for hour in range(0, 24, 2):
                timestamp = target_date.replace(hour=hour, minute=0, second=0)
                
                data = {
                    'data': {
                        'id': device_sn,
                        'upload_method': 'wifi',
                        'heart_rate': random.randint(60, 120),
                        'blood_oxygen': random.randint(95, 100),
                        'body_temperature': f"{random.uniform(36.0, 37.5):.1f}",
                        'blood_pressure_systolic': random.randint(90, 140),
                        'blood_pressure_diastolic': random.randint(60, 90),
                        'step': random.randint(500, 2000),
                        'distance': f"{random.uniform(300, 1500):.1f}",
                        'calorie': f"{random.uniform(20000, 60000):.1f}",
                        'latitude': f"{random.uniform(22.5, 22.6):.14f}",
                        'longitude': f"{random.uniform(114.0, 114.1):.14f}",
                        'altitude': '0.0',
                        'stress': random.randint(20, 80),
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'sleepData': '{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}',
                        'exerciseDailyData': '{"code":0,"data":[{"strengthTimes":2,"totalTime":5}],"name":"daily","type":"history"}',
                        'exerciseWeekData': 'null',
                        'scientificSleepData': 'null',
                        'workoutData': '{"code":0,"data":[],"name":"workout","type":"history"}'
                    }
                }
                
                try:
                    response = requests.post(API_URL, json=data, timeout=5)
                    if response.status_code == 200:
                        print(f"✓ {device_sn} {timestamp.strftime('%m-%d %H:%M')}")
                    else:
                        print(f"✗ {device_sn} {timestamp.strftime('%m-%d %H:%M')} - {response.status_code}")
                except Exception as e:
                    print(f"✗ {device_sn} {timestamp.strftime('%m-%d %H:%M')} - {e}")
    
    # 生成基线
    print("\n生成基线数据...")
    for i in range(3):
        target_date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
        try:
            response = requests.post(BASELINE_API, json={'target_date': target_date}, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 基线生成({target_date}): {result}")
            else:
                print(f"✗ 基线生成失败({target_date}): {response.status_code}")
        except Exception as e:
            print(f"✗ 基线生成异常({target_date}): {e}")
    
    print("\n快速测试完成!")

if __name__ == "__main__":
    quick_test() 