#!/usr/bin/env python3
"""调试数据结构问题"""

import requests
import json

def debug_data_structure():
    print("🔍 调试数据结构问题...")
    
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 3
    }, timeout=30)
    
    data = response.json()
    
    print("📊 响应结构分析:")
    print(f"状态: {response.status_code}")
    print(f"总记录数: {data.get('data', {}).get('totalRecords', 0)}")
    print(f"启用指标: {data.get('data', {}).get('enabledMetrics', [])}")
    print(f"查询字段: {data.get('data', {}).get('queryFields', [])}")
    
    print("\n📝 详细数据结构:")
    for i, item in enumerate(data.get('data', {}).get('healthData', [])[:2], 1):
        print(f"\n{i}. 记录 #{i}:")
        for key, value in item.items():
            print(f"   {key}: {value}")
    
    print(f"\n🔧 性能信息: {data.get('performance', {})}")

if __name__ == "__main__":
    debug_data_structure() 