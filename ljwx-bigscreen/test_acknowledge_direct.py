#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
直接测试消息确认功能
"""

import requests
import json

def test_acknowledge_directly():
    """直接测试消息确认API"""
    
    url = "http://localhost:5225/DeviceMessage/acknowledge"
    
    test_data = {
        "message_id": "1",
        "device_sn": "TEST001",
        "acknowledgment_type": "read",
        "acknowledgment_message": "测试确认"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"解析后数据: {data}")
        
    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    test_acknowledge_directly()