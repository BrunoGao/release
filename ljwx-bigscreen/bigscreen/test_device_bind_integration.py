#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设备绑定功能集成测试"""
import requests, json, time, threading
from bigScreen.bigScreen import app

def start_test_server():
    """启动测试服务器"""
    print("🚀 启动测试服务器...")
    app.run(host='127.0.0.1', port=5002, debug=False, use_reloader=False, threaded=True)

def test_device_bind_apis():
    """测试设备绑定API"""
    time.sleep(2)  # 等待服务器启动
    
    base_url = "http://127.0.0.1:5002"
    
    print("\n📋 设备绑定API测试:")
    print("-" * 50)
    
    # 测试用例
    test_cases = [
        {"name": "绑定申请列表", "url": f"{base_url}/api/device/bind/requests", "method": "GET"},
        {"name": "绑定操作日志", "url": f"{base_url}/api/device/bind/logs", "method": "GET"},
        {"name": "设备管理页面", "url": f"{base_url}/device_bind", "method": "GET"},
        {"name": "生成二维码", "url": f"{base_url}/api/device/TEST001/qrcode", "method": "GET"},
    ]
    
    for test in test_cases:
        try:
            response = requests.get(test["url"], timeout=5)
            status = "✅ 成功" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{test['name']:<15} {status}")
            
            if response.status_code == 200 and 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                print(f"               └─ 响应数据: {json.dumps(data, ensure_ascii=False)[:100]}...")
            elif response.status_code == 200:
                print(f"               └─ HTML响应长度: {len(response.text)} 字符")
                
        except Exception as e:
            print(f"{test['name']:<15} ❌ 错误: {e}")
    
    print(f"\n🎯 测试完成！")

if __name__ == "__main__":
    # 在子线程中启动服务器
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    
    # 在主线程中运行测试
    test_device_bind_apis() 