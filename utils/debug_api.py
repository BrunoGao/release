#!/usr/bin/env python3
import requests
import json
from api_tester import APITester
from db_config import load_db_config

def debug_single_request():
    print("Debug API 请求")
    print("=" * 50)
    
    # 获取测试数据
    tester = APITester("http://192.168.1.83:5001")
    
    db_config = load_db_config()
    if not db_config.connect():
        print("数据库连接失败")
        return
    
    devices = db_config.get_devices(1)
    if not devices:
        print("未找到设备数据")
        return
    
    device_sn = devices[0]['device_sn']
    print(f"使用设备序列号: {device_sn}")
    
    # 测试每个接口
    endpoints = [
        ('upload_health_data', tester.generate_health_data(device_sn)),
        ('upload_device_info', tester.generate_device_info(device_sn)),
        ('upload_common_event', tester.generate_common_event(device_sn))
    ]
    
    for endpoint, test_data in endpoints:
        print(f"\n--- 测试 {endpoint} ---")
        url = f"http://192.168.1.83:5001/{endpoint}"
        
        print(f"URL: {url}")
        print(f"数据: {json.dumps(test_data, indent=2, ensure_ascii=False)[:500]}...")
        
        try:
            response = requests.post(url, json=test_data, timeout=10)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                print("✅ 请求成功")
            else:
                print(f"❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    db_config.disconnect()

if __name__ == "__main__":
    debug_single_request()