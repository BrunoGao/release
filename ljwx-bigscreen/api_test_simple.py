#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的API测试脚本 - 验证基础接口功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5225"

def test_basic_apis():
    """测试基础API"""
    
    print("🔍 测试基础API接口")
    print("=" * 50)
    
    # 测试1: 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ 服务健康检查: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 服务健康检查失败: {e}")
    
    # 测试2: 消息接收API
    print("\n🔍 测试消息接收API")
    try:
        response = requests.get(f"{BASE_URL}/DeviceMessage/receive?deviceSn=TEST001", timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应长度: {len(response.text)} 字符")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   JSON解析成功: {data.get('success', 'unknown')}")
                if data.get('success'):
                    messages = data.get('data', {}).get('messages', [])
                    print(f"   消息数量: {len(messages)}")
            except json.JSONDecodeError:
                print(f"   响应内容前200字符: {response.text[:200]}")
        else:
            print(f"   错误响应: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ 消息接收API测试失败: {e}")
    
    # 测试3: 消息发送API
    print("\n🔍 测试消息发送API")
    message_data = {
        "device_sn": "TEST001",
        "message": "API测试消息",
        "message_type": "notification",
        "sender_type": "system",
        "receiver_type": "device"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/DeviceMessage/save_message",
            json=message_data,
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:500]}")
        
    except Exception as e:
        print(f"❌ 消息发送API测试失败: {e}")
    
    # 测试4: 消息确认API
    print("\n🔍 测试消息确认API")
    ack_data = {
        "message_id": "1",
        "device_sn": "TEST001",
        "acknowledgment_type": "read"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/DeviceMessage/acknowledge",
            json=ack_data,
            timeout=10
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:300]}")
        
    except Exception as e:
        print(f"❌ 消息确认API测试失败: {e}")
    
    # 测试5: 手表端摘要API
    print("\n🔍 测试手表端摘要API")
    try:
        response = requests.get(f"{BASE_URL}/DeviceMessage/watch_summary?deviceSn=TEST001", timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:300]}")
        
    except Exception as e:
        print(f"❌ 手表端摘要API测试失败: {e}")

if __name__ == "__main__":
    test_basic_apis()