#!/usr/bin/env python3
"""
测试 upload_common_event 接口的调试脚本
模拟手表端发送的实际数据结构
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

# 模拟手表端发送的 upload_common_event 数据
# 基于之前观察到的实际数据结构
test_data = {
    "eventType": "com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
    "eventValue": "1",
    "deviceSn": "CRFTQ23409001890", 
    "timestamp": "2025-08-24 16:25:00",
    "latitude": 22.540281,
    "longitude": 114.015168,
    "altitude": 0,
    
    # 这是关键的健康数据部分 - 使用我们修改后的格式
    "healthData": {
        "data": {
            "deviceSn": "CRFTQ23409001890",
            "heart_rate": 75,
            "blood_oxygen": 98,
            "body_temperature": "36.5",
            "step": 1250,
            "distance": "0.8",
            "calorie": "45.2",
            "latitude": "22.540281",
            "longitude": "114.015168", 
            "altitude": "0",
            "stress": 30,
            "upload_method": "common_event",  # 设置为 common_event
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "sleepData": "null",
            "exerciseDailyData": "null",
            "exerciseWeekData": "null",
            "scientificSleepData": "null",
            "workoutData": "null",
            "timestamp": "2025-08-24 16:25:00"
        }
    }
}

def test_upload_common_event():
    """测试上传通用事件"""
    print("🚀 开始测试 upload_common_event 接口...")
    print(f"📡 发送数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload_common_event",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📊 响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"📊 响应内容 (非JSON): {response.text}")
        
        if response.status_code == 200:
            print("✅ 请求成功发送")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False

def test_alternative_structure():
    """测试替代的数据结构（如果第一种格式不正确）"""
    print("\n🔄 测试替代数据结构...")
    
    # 尝试不嵌套 data 的结构
    alt_data = test_data.copy()
    alt_data["healthData"] = {
        "deviceSn": "CRFTQ23409001890",
        "heart_rate": 82,
        "blood_oxygen": 97,
        "body_temperature": "36.8",
        "step": 1500,
        "upload_method": "common_event",
        "timestamp": "2025-08-24 16:26:00"
    }
    
    print(f"📡 发送替代数据: {json.dumps(alt_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload_common_event",
            json=alt_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 替代测试响应状态码: {response.status_code}")
        try:
            response_data = response.json()
            print(f"📊 替代测试响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"📊 替代测试响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 替代测试失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 upload_common_event 调试测试")
    print("=" * 60)
    
    # 测试主要数据结构
    success = test_upload_common_event()
    
    # 等待一秒后测试替代结构
    time.sleep(1)
    test_alternative_structure()
    
    print("\n" + "=" * 60)
    print("💡 请查看大屏系统控制台输出的调试信息")
    print("💡 关注以 🏥 开头的健康数据处理日志")
    print("=" * 60)