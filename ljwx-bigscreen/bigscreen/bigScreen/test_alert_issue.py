#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试告警数据问题的脚本
"""

import requests
import json

def test_alert_issue():
    print("🔍 测试告警数据问题...")
    
    # 1. 测试原版接口
    print("\n1. 测试原版接口 /get_total_info")
    try:
        response = requests.get("http://127.0.0.1:5001/get_total_info?customer_id=1")
        data = response.json()
        alert_info = data.get('data', {}).get('alert_info')
        print(f"   原版告警数据: {type(alert_info)} - {'有数据' if alert_info else '无数据'}")
        if alert_info and isinstance(alert_info, dict):
            print(f"   告警数据键: {list(alert_info.keys())}")
    except Exception as e:
        print(f"   原版接口错误: {e}")
    
    # 2. 测试优化版接口
    print("\n2. 测试优化版接口 /get_total_info_optimized")
    try:
        response = requests.get("http://127.0.0.1:5001/get_total_info_optimized?customer_id=1")
        data = response.json()
        alert_info = data.get('data', {}).get('alert_info')
        print(f"   优化版告警数据: {type(alert_info)} - {'有数据' if alert_info else '无数据'}")
        if alert_info and isinstance(alert_info, dict):
            print(f"   告警数据键: {list(alert_info.keys())}")
    except Exception as e:
        print(f"   优化版接口错误: {e}")
        
    # 3. 直接测试告警接口
    print("\n3. 直接测试告警接口 /get_alerts_by_orgIdAndUserId")
    try:
        response = requests.get("http://127.0.0.1:5001/get_alerts_by_orgIdAndUserId?orgId=1")
        data = response.json()
        print(f"   直接告警数据: {type(data)} - 状态: {data.get('success', 'unknown')}")
        if isinstance(data, dict) and 'data' in data:
            alert_data = data['data']
            print(f"   告警数据内容: {type(alert_data)}")
            if isinstance(alert_data, dict):
                print(f"   告警数据键: {list(alert_data.keys())}")
                if 'alerts' in alert_data:
                    print(f"   告警条数: {len(alert_data['alerts'])}")
    except Exception as e:
        print(f"   直接告警接口错误: {e}")

    # 4. 比较数据格式
    print("\n4. 比较数据格式")
    print("   预期: 优化版应该提取告警数据的data部分")
    print("   问题: 如果告警函数返回{'success': True, 'data': {...}}格式")
    print("        extract_data应该返回data部分，而不是None")

if __name__ == "__main__":
    test_alert_issue() 