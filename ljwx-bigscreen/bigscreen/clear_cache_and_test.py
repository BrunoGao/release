#!/usr/bin/env python3
"""清除缓存并测试修复后的API"""

import requests
import json
import time

def clear_cache_and_test():
    print("🧹 清除缓存并测试修复后的API...")
    
    # 首先清除缓存 - 使用不同的cache key版本
    print("1. 测试修复后的API (v6缓存版本)")
    
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 3,
        '_v': int(time.time())  # 强制跳过缓存
    }, timeout=30)
    
    data = response.json()
    
    print("📊 修复后的API响应:")
    print(f"状态: {response.status_code}")
    print(f"总记录数: {data.get('data', {}).get('totalRecords', 0)}")
    print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
    print(f"缓存版本: v6")
    
    # 检查第一条数据
    health_data = data.get('data', {}).get('healthData', [])
    if health_data:
        first_item = health_data[0]
        print(f"\n📝 第一条数据字段检查:")
        
        # 检查前端期望的字段
        frontend_fields = {
            'heartRate': first_item.get('heartRate'),
            'bloodOxygen': first_item.get('bloodOxygen'),
            'pressureHigh': first_item.get('pressureHigh'),
            'pressureLow': first_item.get('pressureLow'),
            'deptName': first_item.get('deptName'),
            'orgId': first_item.get('orgId'),
            'orgName': first_item.get('orgName'),
            'temperature': first_item.get('temperature'),
            'stress': first_item.get('stress'),
            'step': first_item.get('step')
        }
        
        print("🔍 前端字段检查:")
        for field, value in frontend_fields.items():
            status = "✅" if value is not None and str(value) != "0" and str(value) != "-" else "❌"
            print(f"   {status} {field}: {value}")
        
        print(f"\n📋 完整数据结构:")
        for key in sorted(first_item.keys()):
            print(f"   {key}: {first_item[key]}")
    
    print(f"\n🔧 性能信息: {data.get('performance', {})}")

if __name__ == "__main__":
    clear_cache_and_test() 