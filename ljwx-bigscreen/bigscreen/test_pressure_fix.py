#!/usr/bin/env python3
"""强制清除缓存测试血压修复"""

import requests
import json
import time

def test_pressure_fix():
    print("🩺 强制清除缓存测试血压修复...")
    
    # 使用不同的缓存key并添加时间戳强制跳过缓存
    timestamp = int(time.time())
    
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 2,
        'v': timestamp,  # 添加版本参数强制跳过缓存
        'nocache': 'true'  # 添加无缓存参数
    }, timeout=30)
    
    data = response.json()
    
    print("📊 强制无缓存响应:")
    print(f"状态: {response.status_code}")
    print(f"总记录数: {data.get('data', {}).get('totalRecords', 0)}")
    print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
    print(f"查询字段: {data.get('data', {}).get('queryFields', [])}")
    
    # 检查是否包含pressure相关配置
    enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
    query_fields = data.get('data', {}).get('queryFields', [])
    
    print(f"\n🩺 血压配置检查:")
    print(f"- pressure 在启用指标中: {'pressure' in enabled_metrics}")
    print(f"- pressure_high 在启用指标中: {'pressure_high' in enabled_metrics}")
    print(f"- pressure_low 在启用指标中: {'pressure_low' in enabled_metrics}")
    print(f"- pressure_high 在查询字段中: {'pressure_high' in query_fields}")
    print(f"- pressure_low 在查询字段中: {'pressure_low' in query_fields}")
    
    # 检查数据
    health_data = data.get('data', {}).get('healthData', [])
    if health_data:
        first_item = health_data[0]
        print(f"\n📝 血压字段检查:")
        print(f"   pressureHigh: {first_item.get('pressureHigh')}")
        print(f"   pressureLow: {first_item.get('pressureLow')}")
        
        # 检查所有字段
        print(f"\n📋 所有字段:")
        for key in sorted(first_item.keys()):
            print(f"   {key}: {first_item[key]}")
    
    print(f"\n🔧 性能信息: {data.get('performance', {})}")

if __name__ == "__main__":
    test_pressure_fix() 