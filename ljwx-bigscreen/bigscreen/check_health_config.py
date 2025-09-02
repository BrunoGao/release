#!/usr/bin/env python3
"""检查健康数据配置"""

import requests
import json

def check_health_config():
    print("🔧 检查健康数据配置...")
    
    # 先调用API看当前配置
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 1
    }, timeout=30)
    
    data = response.json()
    
    print("📊 当前配置分析:")
    print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
    print(f"查询字段: {data.get('data', {}).get('queryFields', [])}")
    
    # 检查是否包含pressure相关字段
    enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
    query_fields = data.get('data', {}).get('queryFields', [])
    
    print(f"\n🩺 血压配置检查:")
    print(f"- pressure_high 在启用指标中: {'pressure_high' in enabled_metrics}")
    print(f"- pressure_low 在启用指标中: {'pressure_low' in enabled_metrics}")
    print(f"- pressure_high 在查询字段中: {'pressure_high' in query_fields}")
    print(f"- pressure_low 在查询字段中: {'pressure_low' in query_fields}")
    
    print(f"\n📍 位置配置检查:")
    print(f"- location 在启用指标中: {'location' in enabled_metrics}")
    print(f"- latitude 在查询字段中: {'latitude' in query_fields}")
    print(f"- longitude 在查询字段中: {'longitude' in query_fields}")
    
    # 查看第一条数据的字段
    health_data = data.get('data', {}).get('healthData', [])
    if health_data:
        first_item = health_data[0]
        print(f"\n📝 第一条数据包含的字段:")
        for key in sorted(first_item.keys()):
            print(f"   {key}: {first_item[key]}")
        
        print(f"\n❌ 缺少的前端字段:")
        missing_fields = []
        if 'heartRate' not in first_item: missing_fields.append('heartRate (应为 heart_rate)')
        if 'bloodOxygen' not in first_item: missing_fields.append('bloodOxygen (应为 blood_oxygen)')
        if 'pressureHigh' not in first_item: missing_fields.append('pressureHigh (应为 pressure_high)')
        if 'pressureLow' not in first_item: missing_fields.append('pressureLow (应为 pressure_low)')
        if 'deptName' not in first_item: missing_fields.append('deptName')
        if 'orgId' not in first_item: missing_fields.append('orgId')
        if 'orgName' not in first_item: missing_fields.append('orgName')
        
        for field in missing_fields:
            print(f"   - {field}")

if __name__ == "__main__":
    check_health_config() 