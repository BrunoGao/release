#!/usr/bin/env python3
"""快速事件测试脚本 - 专门测试关键事件类型"""
import requests
import json
import time
from datetime import datetime

def test_emergency_events():
    """测试紧急事件"""
    base_url = "http://localhost:5001"
    test_device = f"EMERGENCY_TEST_{int(time.time())}"
    
    # 定义紧急事件测试用例
    emergency_events = [
        {
            "name": "SOS紧急求救",
            "eventType": "SOS_EVENT",
            "eventValue": "1"
        },
        {
            "name": "跌倒检测告警", 
            "eventType": "FALLDOWN_EVENT",
            "eventValue": "1"
        },
        {
            "name": "一键紧急报警",
            "eventType": "ONE_KEY_ALARM", 
            "eventValue": "1"
        }
    ]
    
    print(f"🚨 开始测试紧急事件处理")
    print(f"📱 测试设备: {test_device}")
    print(f"🌐 API地址: {base_url}")
    print("="*60)
    
    results = []
    
    for i, event in enumerate(emergency_events, 1):
        print(f"\n[{i}/3] 🧪 测试: {event['name']}")
        
        # 构建事件数据（使用您提供的数据结构）
        event_data = {
            "eventType": event["eventType"],
            "eventValue": event["eventValue"], 
            "deviceSn": test_device,
            "heatlhData": json.dumps({
                "data": {
                    "deviceSn": test_device,
                    "heart_rate": 84,
                    "blood_oxygen": 98,
                    "body_temperature": "36.5",
                    "step": 0,
                    "distance": "0.0",
                    "calorie": "0.0",
                    "latitude": "22.540368",
                    "longitude": "114.015090",
                    "altitude": "10",
                    "stress": 0,
                    "upload_method": "wifi",
                    "blood_pressure_systolic": 125,
                    "blood_pressure_diastolic": 86,
                    "sleepData": "null",
                    "exerciseDailyData": "null",
                    "exerciseWeekData": "null", 
                    "scientificSleepData": "null",
                    "workoutData": "null",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        }
        
        try:
            # 发送事件
            print(f"📡 发送事件数据...")
            response = requests.post(
                f"{base_url}/upload_common_event",
                json=event_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   响应: {result}")
                
                # 检查响应内容
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                processing = result.get('processing', 'No processing info')
                
                print(f"   ✅ 事件处理状态: {status}")
                print(f"   📝 处理信息: {message}")
                print(f"   ⚙️  后台处理: {processing}")
                
                results.append({
                    "event": event['name'],
                    "type": event['eventType'],
                    "success": status == 'success',
                    "response": result
                })
            else:
                print(f"   ❌ API调用失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                results.append({
                    "event": event['name'],
                    "type": event['eventType'],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
            results.append({
                "event": event['name'],
                "type": event['eventType'],
                "success": False,
                "error": str(e)
            })
        
        # 每次测试间隔
        time.sleep(3)
    
    # 生成简报
    print(f"\n{'='*60}")
    print(f"📊 测试总结:")
    successful = sum(1 for r in results if r['success'])
    print(f"   总测试数: {len(results)}")
    print(f"   成功数量: {successful}")
    print(f"   失败数量: {len(results) - successful}")
    print(f"   成功率: {successful/len(results)*100:.1f}%")
    
    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        print(f"   {i}. {result['event']} ({result['type']}) {status}")
        if not result['success'] and 'error' in result:
            print(f"      错误: {result['error']}")
    
    print(f"\n🔍 验证提醒:")
    print(f"   请手动检查以下内容:")
    print(f"   1. 微信是否收到了这3个紧急事件的告警消息")
    print(f"   2. t_alert_info表是否插入了对应的告警记录")
    print(f"   3. t_user_health_data表是否插入了健康数据")
    print(f"   4. 平台是否下发了对应的设备消息")
    
    return results

def test_normal_event():
    """测试普通事件（穿戴状态变化）"""
    base_url = "http://localhost:5001"
    test_device = f"NORMAL_TEST_{int(time.time())}"
    
    print(f"\n📱 测试普通事件: 穿戴状态变化")
    print(f"📱 测试设备: {test_device}")
    
    # 使用您提供的穿戴状态变化事件数据
    event_data = {
        "eventType": "com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
        "eventValue": "0",
        "deviceSn": test_device,
        "heatlhData": json.dumps({
            "data": {
                "deviceSn": test_device,
                "heart_rate": 84,
                "blood_oxygen": 98,
                "body_temperature": "0.0",
                "step": 0,
                "distance": "0.0", 
                "calorie": "0.0",
                "latitude": "0",
                "longitude": "0",
                "altitude": "0",
                "stress": 0,
                "upload_method": "wifi",
                "blood_pressure_systolic": 125,
                "blood_pressure_diastolic": 86,
                "sleepData": "null",
                "exerciseDailyData": "null",
                "exerciseWeekData": "null",
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": "2025-06-17 06:27:10"
            }
        })
    }
    
    try:
        print(f"📡 发送穿戴状态事件...")
        response = requests.post(
            f"{base_url}/upload_common_event",
            json=event_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {result}")
            print(f"   ✅ 普通事件处理成功")
            print(f"   📝 应该只下发平台消息，不发送微信告警")
        else:
            print(f"   ❌ 普通事件处理失败: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 普通事件测试异常: {e}")

if __name__ == "__main__":
    print("🚀 快速事件测试开始")
    print("="*60)
    
    # 测试紧急事件
    emergency_results = test_emergency_events()
    
    # 测试普通事件
    test_normal_event()
    
    print(f"\n🏁 所有测试完成")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 