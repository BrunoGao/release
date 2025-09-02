#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import requests
import json
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bigScreen'))

def test_health_api():
    """测试健康数据API"""
    print("=== 测试健康数据API ===")
    
    # 测试参数
    base_url = "http://localhost:5001"
    test_params = {
        'orgId': '1',
        'startDate': '2025-05-28',
        'endDate': '2025-06-03'
    }
    
    # 测试URL
    url = f"{base_url}/get_all_health_data_by_orgIdAndUserId"
    
    print(f"请求URL: {url}")
    print(f"请求参数: {test_params}")
    
    try:
        # 发送请求
        response = requests.get(url, params=test_params, timeout=10)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应成功: {data.get('success', False)}")
            print(f"响应消息: {data.get('message', 'N/A')}")
            
            if data.get('success') and data.get('data'):
                print("=== 数据结构分析 ===")
                data_keys = list(data['data'].keys())
                print(f"顶层字段: {data_keys}")
                
                # 检查每个字段
                for key in data_keys:
                    value = data['data'][key]
                    if isinstance(value, dict):
                        print(f"{key}: {type(value).__name__} -> {list(value.keys())}")
                    elif isinstance(value, list):
                        print(f"{key}: {type(value).__name__} -> 长度: {len(value)}")
                    else:
                        print(f"{key}: {type(value).__name__} -> {value}")
                
                # 详细分析summary字段
                if 'summary' in data['data']:
                    summary = data['data']['summary']
                    print(f"\nSummary字段详情: {json.dumps(summary, ensure_ascii=False, indent=2)}")
                
                # 详细分析healthScores字段
                if 'healthScores' in data['data']:
                    health_scores = data['data']['healthScores']
                    print(f"\nHealthScores字段详情: {json.dumps(health_scores, ensure_ascii=False, indent=2)[:500]}...")
                
                # 详细分析timeSeriesData字段
                if 'timeSeriesData' in data['data']:
                    time_series = data['data']['timeSeriesData']
                    print(f"\nTimeSeriesData字段详情: {json.dumps(time_series, ensure_ascii=False, indent=2)[:500]}...")
                    
                print("\n=== 前端兼容性检查 ===")
                expected_fields = ['summary', 'healthScores', 'timeSeriesData']
                missing_fields = [field for field in expected_fields if field not in data['data']]
                if missing_fields:
                    print(f"缺少的字段: {missing_fields}")
                else:
                    print("所有必需字段都存在!")
                    
            else:
                print(f"API返回失败或无数据: {data}")
                
        else:
            print(f"HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

def test_direct_function():
    """直接测试函数调用"""
    print("\n=== 直接测试函数调用 ===")
    
    try:
        from bigScreen.user_health_data import fetch_all_health_data_by_orgIdAndUserId
        
        result = fetch_all_health_data_by_orgIdAndUserId(
            orgId='1',
            startDate='2025-05-28',
            endDate='2025-06-03'
        )
        
        print(f"函数调用结果: {json.dumps(result, ensure_ascii=False, indent=2, default=str)}")
        
    except Exception as e:
        print(f"函数调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_health_api()
    test_direct_function() 