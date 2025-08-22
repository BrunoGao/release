#!/usr/bin/env python3
"""
简化的ljwx-watch接口测试
"""

import requests
import json
import time
import random
from datetime import datetime

def test_health_data_upload():
    """测试健康数据上传接口"""
    print("🏥 测试健康数据上传接口...")
    
    data = {
        "data": {
            "deviceSn": "LJWX001",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "heart_rate": 75,
            "blood_oxygen": 98,
            "body_temperature": 36.5,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "stress": 50,
            "step": 8000,
            "distance": 5.2,
            "calorie": 350
        }
    }
    
    try:
        response = requests.post("http://localhost:5001/upload_health_data", 
                               json=data, 
                               timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def test_device_info_upload():
    """测试设备信息上传接口"""
    print("📱 测试设备信息上传接口...")
    
    data = {
        "deviceSn": "LJWX001",
        "deviceName": "LJWX智能手表_001",
        "deviceType": "smartwatch",
        "firmwareVersion": "1.2.3",
        "batteryLevel": 85,
        "status": "online"
    }
    
    try:
        response = requests.post("http://localhost:5001/upload_device_info", 
                               json=data, 
                               timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def test_common_event_upload():
    """测试通用事件上传接口"""
    print("⚡ 测试通用事件上传接口...")
    
    data = {
        "deviceSn": "LJWX001",
        "eventType": "com.ljwx.watch.event.HEART_RATE_ABNORMAL",
        "eventTime": int(datetime.now().timestamp() * 1000),
        "eventData": json.dumps({
            "severity": "medium",
            "value": 120,
            "location": {"lat": 39.9042, "lng": 116.4074}
        })
    }
    
    try:
        response = requests.post("http://localhost:5001/upload_common_event", 
                               json=data, 
                               timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False

def test_batch_upload():
    """测试批量上传"""
    print("\n📦 测试批量上传...")
    
    success_count = 0
    total_count = 9  # 3个接口 × 3次
    
    for i in range(3):
        print(f"\n第 {i+1} 轮测试:")
        
        if test_health_data_upload():
            success_count += 1
        time.sleep(0.5)
        
        if test_device_info_upload():
            success_count += 1
        time.sleep(0.5)
        
        if test_common_event_upload():
            success_count += 1
        time.sleep(0.5)
    
    print(f"\n📊 批量测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

def main():
    print("🚀 ljwx-watch 接口简单测试")
    print("="*50)
    
    # 测试各个接口
    results = []
    results.append(test_health_data_upload())
    time.sleep(1)
    results.append(test_device_info_upload()) 
    time.sleep(1)
    results.append(test_common_event_upload())
    time.sleep(1)
    
    # 批量测试
    results.append(test_batch_upload())
    
    print(f"\n🎯 总体测试结果: {sum(results)}/{len(results)} 通过")
    
    if all(results):
        print("✅ 所有测试通过！ljwx-bigscreen批处理系统正常工作")
    else:
        print("❌ 部分测试失败，请检查系统配置")

if __name__ == "__main__":
    main()