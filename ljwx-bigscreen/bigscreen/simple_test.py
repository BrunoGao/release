#!/usr/bin/env python3
"""简单测试修复后的API"""

import requests
import json

def simple_test():
    print("🔧 简单测试修复后的API...")
    
    try:
        response = requests.get('http://127.0.0.1:5001/health_data/page', params={
            'orgId': 1, 
            'pageSize': 1  # 只要1条记录，减少处理时间
        }, timeout=60)
        
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API请求成功")
            print(f"总记录数: {data.get('data', {}).get('totalRecords', 0)}")
            print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
            
            # 检查第一条数据
            health_data = data.get('data', {}).get('healthData', [])
            if health_data:
                first_item = health_data[0]
                print(f"\n📝 第一条数据字段:")
                print(f"   pressureHigh: {first_item.get('pressureHigh')}")
                print(f"   pressureLow: {first_item.get('pressureLow')}")
                print(f"   heartRate: {first_item.get('heartRate')}")
                print(f"   bloodOxygen: {first_item.get('bloodOxygen')}")
                print(f"   deptName: {first_item.get('deptName')}")
                print(f"   orgName: {first_item.get('orgName')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    simple_test() 