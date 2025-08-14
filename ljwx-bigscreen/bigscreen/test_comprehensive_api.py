#!/usr/bin/env python3
"""全面的API测试脚本"""

import requests
import json
import time

def test_cache_hit():
    print('🔄 测试缓存命中...')
    url = "http://127.0.0.1:5001/health_data/page"
    params = {'orgId': 1, 'userId': '', 'startDate': '2025-05-01', 'endDate': '2025-06-01', 'page': 1, 'pageSize': 100}
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    print(f'⚡ 缓存命中: {data.get("performance", {}).get("cached", False)}')
    print(f'⏱️ 响应时间: {data.get("performance", {}).get("response_time", "N/A")}s')

def test_single_user():
    print('\n👤 测试单用户查询...')
    url = "http://127.0.0.1:5001/health_data/page"
    params = {'orgId': '', 'userId': '1923279171228076912', 'startDate': '2025-05-01', 'endDate': '2025-06-01', 'page': 1, 'pageSize': 10}
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    print(f'📊 状态: {response.status_code}')
    print(f'📈 总记录数: {data.get("data", {}).get("totalRecords", 0)}')
    print(f'📄 返回数据: {len(data.get("data", {}).get("healthData", []))}条')

def test_recent_data():
    print('\n📅 测试最近数据查询...')
    url = "http://127.0.0.1:5001/health_data/page"
    params = {'orgId': 1, 'userId': '', 'startDate': '2025-05-30', 'endDate': '2025-05-31', 'page': 1, 'pageSize': 50}
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    print(f'📊 状态: {response.status_code}')
    print(f'🔧 查询策略: {data.get("data", {}).get("queryStrategy", "N/A")}')
    print(f'📈 总记录数: {data.get("data", {}).get("totalRecords", 0)}')

def test_latest_only():
    print('\n🔥 测试最新数据查询...')
    url = "http://127.0.0.1:5001/health_data/latest"
    params = {'orgId': 1, 'userId': ''}
    
    response = requests.get(url, params=params, timeout=30)
    data = response.json()
    print(f'📊 状态: {response.status_code}')
    if response.status_code == 200:
        print(f'📈 总记录数: {data.get("data", {}).get("totalRecords", 0)}')
        print(f'📄 返回数据: {len(data.get("data", {}).get("healthData", []))}条')
        print(f'🔧 查询策略: {data.get("data", {}).get("queryStrategy", "N/A")}')
    else:
        print(f'❌ 错误: {response.text}')

if __name__ == "__main__":
    print("🚀 开始全面API测试...\n")
    
    try:
        test_cache_hit()
        test_single_user()
        test_recent_data()
        test_latest_only()
        print("\n✅ 所有测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}") 