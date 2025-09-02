#!/usr/bin/env python3
"""验证数据查询结果"""

import requests
import json

def verify_data_details():
    response = requests.get('http://127.0.0.1:5001/health_data/page', params={
        'orgId': 1, 
        'startDate': '2025-05-01', 
        'endDate': '2025-06-01', 
        'page': 1, 
        'pageSize': 5
    }, timeout=30)
    
    data = response.json()
    print('📊 数据验证:')
    print(f'总记录数: {data["data"]["totalRecords"]}')
    print(f'查询策略: {data["data"]["queryStrategy"]}')
    print(f'性能: {data["performance"]}')
    print('\n📝 前5条数据:')
    
    for i, item in enumerate(data['data']['healthData'][:5], 1):
        print(f'{i}. 用户: {item["userName"]}, 设备: {item["deviceSn"]}, 时间: {item["timestamp"]}, 心率: {item["heart_rate"]}, 体温: {item["temperature"]}')

if __name__ == "__main__":
    verify_data_details() 