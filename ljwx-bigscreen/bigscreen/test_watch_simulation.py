#!/usr/bin/env python3
"""
ljwx-watch 模拟测试脚本
基于watch端的逻辑设计测试方案，验证三个接口的正常上传和断点续传功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
import random
from datetime import datetime, timedelta
from bigScreen.models import DeviceInfo, db
from bigScreen.bigScreen import app

def get_existing_device_sns():
    """获取系统中现有的手表设备序列号"""
    print("🔍 获取系统中现有手表设备序列号...")
    
    with app.app_context():
        devices = DeviceInfo.query.limit(10).all()
        device_sns = []
        print("   序列号\t\t设备名称\t\t创建时间")
        print("   " + "-" * 60)
        for device in devices:
            print(f"   {device.serial_number:<15} {device.device_name or 'N/A':<15} {device.created_at}")
            device_sns.append(device.serial_number)
        
        if not device_sns:
            # 如果没有设备，创建测试设备序列号
            test_sns = ["LJWX001", "LJWX002", "LJWX003"]
            print("⚠️  数据库中没有设备，使用测试序列号:")
            for sn in test_sns:
                print(f"   {sn}")
            return test_sns
            
        return device_sns

def simulate_watch_health_data(device_sn):
    """模拟手表健康数据 - 参考ljwx-watch逻辑"""
    now = datetime.now()
    
    # 参考watch端的数据结构
    health_data = {
        "data": {
            "deviceSn": device_sn,
            "timestamp": int(now.timestamp() * 1000),
            "heart_rate": random.randint(60, 100),
            "blood_oxygen": random.randint(95, 99),
            "body_temperature": round(36.0 + random.random() * 1.5, 1),
            "blood_pressure_systolic": random.randint(110, 140),
            "blood_pressure_diastolic": random.randint(70, 90),
            "stress": random.randint(1, 100),
            "step": random.randint(1000, 15000),
            "distance": round(random.uniform(0.5, 10.0), 2),
            "calorie": random.randint(200, 800),
            "latitude": 39.9042 + random.uniform(-0.01, 0.01),
            "longitude": 116.4074 + random.uniform(-0.01, 0.01),
            "altitude": random.randint(10, 100),
            "sleepData": json.dumps({
                "deep_sleep": random.randint(120, 300),
                "light_sleep": random.randint(200, 400),
                "rem_sleep": random.randint(60, 120)
            })
        }
    }
    return health_data

def simulate_watch_device_info(device_sn):
    """模拟手表设备信息 - 参考ljwx-watch逻辑"""
    return {
        "deviceSn": device_sn,
        "deviceName": f"LJWX智能手表_{device_sn}",
        "deviceType": "smartwatch",
        "firmwareVersion": "1.2.3",
        "hardwareVersion": "V2.0",
        "batteryLevel": random.randint(20, 100),
        "signalStrength": random.randint(-80, -40),
        "lastSyncTime": int(datetime.now().timestamp() * 1000),
        "status": "online"
    }

def simulate_watch_common_event(device_sn):
    """模拟手表通用事件 - 参考ljwx-watch逻辑"""
    event_types = [
        "com.ljwx.watch.event.FALL_DETECTED",
        "com.ljwx.watch.event.SOS_TRIGGERED", 
        "com.ljwx.watch.event.LOW_BATTERY",
        "com.ljwx.watch.event.GEOFENCE_EXIT",
        "com.ljwx.watch.event.HEART_RATE_ABNORMAL"
    ]
    
    return {
        "deviceSn": device_sn,
        "eventType": random.choice(event_types),
        "eventTime": int(datetime.now().timestamp() * 1000),
        "eventData": json.dumps({
            "severity": random.choice(["low", "medium", "high"]),
            "value": random.randint(1, 100),
            "location": {
                "lat": 39.9042 + random.uniform(-0.01, 0.01),
                "lng": 116.4074 + random.uniform(-0.01, 0.01)
            }
        }),
        "processed": False
    }

class WatchSimulator:
    """手表模拟器 - 模拟ljwx-watch的行为"""
    
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.device_sns = get_existing_device_sns()
        self.cache = {
            "health_data": [],
            "device_info": [],
            "common_event": []
        }
        
    def add_to_cache(self, data_type, data):
        """添加数据到缓存 - 模拟HealthDataCache.addToCache()"""
        if data_type not in self.cache:
            self.cache[data_type] = []
        
        # 环形缓存，最大100条
        if len(self.cache[data_type]) >= 100:
            self.cache[data_type].pop(0)
        
        self.cache[data_type].append(json.dumps(data))
        print(f"📦 [{data_type}] 数据已添加到缓存，当前大小: {len(self.cache[data_type])}")
        
    def upload_with_cache(self, endpoint, data_type, data):
        """带缓存的上传 - 模拟HttpService.uploadDataWithCache()"""
        try:
            # 先尝试直接上传
            response = requests.post(f"{self.base_url}{endpoint}", 
                                   json=data, 
                                   timeout=5,
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"✅ [{data_type}] 直接上传成功: {result.get('message', '')}")
                    return True
                else:
                    print(f"❌ [{data_type}] 服务器返回错误: {result.get('message', '')}")
                    
        except Exception as e:
            print(f"🔥 [{data_type}] 网络异常: {e}")
        
        # 上传失败，添加到缓存
        self.add_to_cache(data_type, data)
        return False
        
    def retry_cached_data(self):
        """重试缓存数据 - 模拟HttpService.checkAndRetryCachedData()"""
        endpoints = {
            "health_data": "/upload_health_data",
            "device_info": "/upload_device_info", 
            "common_event": "/upload_common_event"
        }
        
        for data_type, endpoint in endpoints.items():
            cached_data = self.cache[data_type].copy()
            if not cached_data:
                continue
                
            print(f"🔄 [{data_type}] 开始重试缓存数据，共 {len(cached_data)} 条")
            
            success_count = 0
            for i, data_str in enumerate(cached_data):
                try:
                    data = json.loads(data_str)
                    response = requests.post(f"{self.base_url}{endpoint}", 
                                           json=data, 
                                           timeout=5,
                                           headers={'Content-Type': 'application/json'})
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('status') == 'success':
                            # 上传成功，从缓存中移除
                            self.cache[data_type].remove(data_str)
                            success_count += 1
                            print(f"   ✅ [{data_type}] 缓存数据 {i+1} 重试成功")
                        else:
                            print(f"   ❌ [{data_type}] 缓存数据 {i+1} 服务器错误: {result.get('message', '')}")
                    else:
                        print(f"   ❌ [{data_type}] 缓存数据 {i+1} HTTP错误: {response.status_code}")
                        
                except Exception as e:
                    print(f"   🔥 [{data_type}] 缓存数据 {i+1} 重试异常: {e}")
                    
            print(f"🔄 [{data_type}] 重试完成，成功: {success_count}/{len(cached_data)}，剩余缓存: {len(self.cache[data_type])}")

def test_interface_normal_upload():
    """测试三个接口的正常上传"""
    print("\n" + "="*60)
    print("🧪 测试阶段1: 三个接口正常上传测试")
    print("="*60)
    
    simulator = WatchSimulator()
    
    for device_sn in simulator.device_sns[:3]:  # 取前3个设备进行测试
        print(f"\n📱 测试设备: {device_sn}")
        
        # 1. 测试健康数据上传
        health_data = simulate_watch_health_data(device_sn)
        simulator.upload_with_cache("/upload_health_data", "health_data", health_data)
        time.sleep(1)
        
        # 2. 测试设备信息上传
        device_info = simulate_watch_device_info(device_sn)
        simulator.upload_with_cache("/upload_device_info", "device_info", device_info)
        time.sleep(1)
        
        # 3. 测试通用事件上传
        common_event = simulate_watch_common_event(device_sn)
        simulator.upload_with_cache("/upload_common_event", "common_event", common_event)
        time.sleep(1)

def test_network_interruption_and_recovery():
    """测试网络中断和恢复的断点续传"""
    print("\n" + "="*60)
    print("🧪 测试阶段2: 网络中断与断点续传测试")
    print("="*60)
    
    simulator = WatchSimulator()
    device_sn = simulator.device_sns[0] if simulator.device_sns else "LJWX001"
    
    # 模拟网络中断期间的数据积累
    print(f"\n🔌 模拟网络中断，数据开始缓存到本地...")
    simulator.base_url = "http://invalid-url-for-test:9999"  # 故意设置错误URL模拟网络中断
    
    # 生成多条数据，模拟网络中断期间的数据积累
    for i in range(5):
        print(f"\n📊 生成第 {i+1} 批数据...")
        
        # 健康数据
        health_data = simulate_watch_health_data(device_sn)
        simulator.upload_with_cache("/upload_health_data", "health_data", health_data)
        
        # 设备信息
        device_info = simulate_watch_device_info(device_sn)
        simulator.upload_with_cache("/upload_device_info", "device_info", device_info)
        
        # 通用事件
        common_event = simulate_watch_common_event(device_sn)
        simulator.upload_with_cache("/upload_common_event", "common_event", common_event)
        
        time.sleep(0.5)
    
    # 显示缓存状态
    print("\n📦 当前缓存状态:")
    for data_type, cache_list in simulator.cache.items():
        print(f"   {data_type}: {len(cache_list)} 条数据")
    
    # 模拟网络恢复
    print(f"\n🌐 网络恢复，开始断点续传...")
    simulator.base_url = "http://localhost:5001"  # 恢复正确URL
    
    # 执行断点续传
    simulator.retry_cached_data()

def test_batch_processing_performance():
    """测试批处理性能"""
    print("\n" + "="*60)
    print("🧪 测试阶段3: 批处理性能测试")
    print("="*60)
    
    simulator = WatchSimulator()
    device_sns = simulator.device_sns[:2] if len(simulator.device_sns) >= 2 else ["LJWX001", "LJWX002"]
    
    start_time = time.time()
    total_requests = 0
    
    # 并发上传多个设备的数据
    for round_num in range(3):  # 3轮测试
        print(f"\n🔄 第 {round_num + 1} 轮批量上传测试...")
        
        for device_sn in device_sns:
            # 每个设备上传3种类型的数据
            for i in range(2):  # 每种类型2条数据
                # 健康数据
                health_data = simulate_watch_health_data(device_sn)
                simulator.upload_with_cache("/upload_health_data", "health_data", health_data)
                total_requests += 1
                
                # 设备信息
                device_info = simulate_watch_device_info(device_sn)  
                simulator.upload_with_cache("/upload_device_info", "device_info", device_info)
                total_requests += 1
                
                # 通用事件
                common_event = simulate_watch_common_event(device_sn)
                simulator.upload_with_cache("/upload_common_event", "common_event", common_event)
                total_requests += 1
                
                time.sleep(0.1)  # 短暂间隔模拟真实情况
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 性能测试结果:")
    print(f"   总请求数: {total_requests}")
    print(f"   总耗时: {duration:.2f} 秒")
    print(f"   平均每请求耗时: {(duration/total_requests)*1000:.2f} ms")
    print(f"   QPS: {total_requests/duration:.2f}")

def main():
    """主测试函数"""
    print("🚀 ljwx-watch 模拟测试开始")
    print("基于watch端逻辑设计，验证bigscreen批处理系统")
    
    try:
        # 测试1: 正常上传
        test_interface_normal_upload()
        
        # 测试2: 断点续传
        test_network_interruption_and_recovery()
        
        # 测试3: 批处理性能
        test_batch_processing_performance()
        
        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()