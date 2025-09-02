#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试修复后的查询功能"""

import sys,os,json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ['FLASK_ENV'] = 'development'

def test_api_endpoint():
    """测试API端点"""
    import requests
    import time
    
    print("🧪 测试修复后的查询API...")
    
    try:
        # 测试get_total_info端点
        print("\n📊 测试总览数据API:")
        response = requests.get("http://localhost:8001/get_total_info?customerId=1", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功")
            print(f"   数据键: {list(result.get('data', {}).keys())}")
            print(f"   性能信息: {result.get('performance', {})}")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"   错误内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    try:
        # 测试设备查询端点
        print("\n🔧 测试设备查询API:")
        response = requests.get("http://localhost:8001/get_devices_by_orgIdAndUserId?orgId=1", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 设备API调用成功")
            print(f"   找到设备: {result.get('data', {}).get('totalDevices', 0)} 个")
            if result.get('data', {}).get('queryInfo'):
                print(f"   查询信息: {result['data']['queryInfo']}")
        else:
            print(f"❌ 设备API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 设备测试失败: {e}")

if __name__ == "__main__":
    test_api_endpoint() 