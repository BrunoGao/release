#!/usr/bin/env python3
"""配置化健康数据上传测试脚本"""
import requests
import json
import time
from datetime import datetime,timedelta

# 测试配置
BASE_URL = "http://localhost:5001"
TEST_DEVICE_SN = "TEST_DEVICE_001"
TEST_CUSTOMER_ID = 1

def test_health_config_upload():
    """测试配置化健康数据上传功能"""
    print("🚀 开始测试配置化健康数据上传功能...")
    
    # 1. 测试单条数据上传
    print("\n1. 测试单条数据上传")
    single_data = {
        "data": {
            "deviceSn": TEST_DEVICE_SN,
            "heartRate": 75,
            "bloodOxygen": 98,
            "temperature": 36.5,
            "pressureHigh": 120,
            "pressureLow": 80,
            "stress": 45,
            "step": 1000,
            "distance": 0.8,
            "calorie": 50.5,
            "latitude": 22.543100,
            "longitude": 114.045000,
            "altitude": 10.0,
            "sleepData": {"duration": 480, "quality": "good", "deep_sleep": 120},
            "exerciseDailyData": {"total_time": 60, "calories_burned": 200},
            "workoutData": {"type": "running", "duration": 30},
            "exerciseWeekData": {"total_workouts": 5, "total_time": 300},
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    response = requests.post(f"{BASE_URL}/upload_health_data", json=single_data)
    print(f"单条上传响应: {response.status_code} - {response.json()}")
    
    # 2. 测试批量数据上传
    print("\n2. 测试批量数据上传")
    batch_data = {
        "data": []
    }
    
    # 生成5条测试数据
    for i in range(5):
        timestamp = datetime.now() + timedelta(minutes=i)
        data_item = {
            "deviceSn": f"{TEST_DEVICE_SN}_{i}",
            "heartRate": 70 + i,
            "bloodOxygen": 95 + i,
            "temperature": 36.0 + i * 0.1,
            "pressureHigh": 115 + i,
            "pressureLow": 75 + i,
            "stress": 40 + i * 2,
            "step": 1000 + i * 100,
            "sleepData": {"duration": 480 + i * 10, "quality": "good"},
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        batch_data["data"].append(data_item)
    
    response = requests.post(f"{BASE_URL}/upload_health_data", json=batch_data)
    print(f"批量上传响应: {response.status_code} - {response.json()}")
    
    # 3. 测试优化器统计
    print("\n3. 获取优化器统计信息")
    time.sleep(2)  # 等待处理完成
    response = requests.get(f"{BASE_URL}/optimizer/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"优化器统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    else:
        print(f"获取统计失败: {response.status_code}")
    
    # 4. 测试配置字段查询
    print("\n4. 测试健康配置查询")
    response = requests.get(f"{BASE_URL}/get_health_config?customerId={TEST_CUSTOMER_ID}")
    if response.status_code == 200:
        config = response.json()
        print(f"健康配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
    else:
        print(f"获取配置失败: {response.status_code}")
    
    # 5. 测试错误处理
    print("\n5. 测试错误处理")
    invalid_data = {
        "data": {
            "heartRate": 75,  # 缺少deviceSn
            "bloodOxygen": 98
        }
    }
    
    response = requests.post(f"{BASE_URL}/upload_health_data", json=invalid_data)
    print(f"错误处理响应: {response.status_code} - {response.json()}")
    
    print("\n✅ 配置化健康数据上传测试完成!")

def test_performance():
    """性能测试"""
    print("\n🔥 开始性能测试...")
    
    # 生成大量测试数据
    batch_data = {"data": []}
    for i in range(100):
        timestamp = datetime.now() + timedelta(seconds=i)
        data_item = {
            "deviceSn": f"PERF_TEST_{i % 10}",  # 10个设备
            "heartRate": 70 + (i % 30),
            "bloodOxygen": 95 + (i % 5),
            "temperature": 36.0 + (i % 10) * 0.1,
            "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        batch_data["data"].append(data_item)
    
    # 记录开始时间
    start_time = time.time()
    
    # 发送请求
    response = requests.post(f"{BASE_URL}/upload_health_data", json=batch_data)
    
    # 计算耗时
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"性能测试结果:")
    print(f"- 数据量: 100条")
    print(f"- 响应状态: {response.status_code}")
    print(f"- 处理时间: {duration:.3f}秒")
    print(f"- 平均速度: {100/duration:.1f}条/秒")
    
    if response.status_code == 200:
        result = response.json()
        print(f"- 响应消息: {result.get('message', 'N/A')}")

def test_field_filtering():
    """测试字段过滤功能"""
    print("\n🎯 测试字段过滤功能...")
    
    # 发送包含所有字段的数据
    full_data = {
        "data": {
            "deviceSn": "FILTER_TEST_001",
            "heartRate": 75,
            "bloodOxygen": 98,
            "temperature": 36.5,
            "pressureHigh": 120,
            "pressureLow": 80,
            "stress": 45,
            "step": 1000,
            "distance": 0.8,
            "calorie": 50.5,
            "latitude": 22.543100,
            "longitude": 114.045000,
            "altitude": 10.0,
            "sleepData": {"duration": 480, "quality": "good"},
            "exerciseDailyData": {"total_time": 60},
            "workoutData": {"type": "running"},
            "exerciseWeekData": {"total_workouts": 5},
            "scientificSleepData": {"rem_sleep": 90},
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    response = requests.post(f"{BASE_URL}/upload_health_data", json=full_data)
    print(f"字段过滤测试响应: {response.status_code} - {response.json()}")
    
    print("✅ 字段过滤测试完成!")

if __name__ == "__main__":
    try:
        # 基础功能测试
        test_health_config_upload()
        
        # 字段过滤测试
        test_field_filtering()
        
        # 性能测试
        test_performance()
        
        print("\n🎉 所有测试完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保大屏服务正在运行 (http://localhost:5001)")
    except Exception as e:
        print(f"❌ 测试失败: {e}") 