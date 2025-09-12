#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2消息系统集成测试脚本
测试API修复和V2系统集成是否成功
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://192.168.1.83:5225"
CUSTOMER_ID = "1939964806110937090"

def test_api_fixes():
    """测试API修复"""
    print("🔧 测试API修复...")
    
    tests = [
        {
            "name": "健康评分API - 修复后的路径",
            "url": f"{BASE_URL}/api/health/score/comprehensive",
            "params": {"customerId": CUSTOMER_ID, "days": 7}
        },
        {
            "name": "消息查询API - 添加customerId参数",
            "url": f"{BASE_URL}/get_messages_by_orgIdAndUserId",
            "params": {
                "orgId": CUSTOMER_ID,
                "userId": "null",
                "messageType": "null",
                "customerId": CUSTOMER_ID
            }
        }
    ]
    
    for test in tests:
        print(f"\n📡 测试: {test['name']}")
        try:
            response = requests.get(test["url"], params=test["params"], timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 成功")
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'success' in data:
                        print(f"   响应: success={data.get('success')}")
                    else:
                        print(f"   响应长度: {len(str(data))} 字符")
                except:
                    print(f"   响应长度: {len(response.text)} 字符")
            elif response.status_code == 404:
                print("   ❌ 404 NOT FOUND - API路径可能仍有问题")
            elif response.status_code == 500:
                print("   ❌ 500 INTERNAL SERVER ERROR - 服务器内部错误")
                print(f"   错误信息: {response.text[:200]}...")
            else:
                print(f"   ⚠️  状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")

def test_v2_system_health():
    """测试V2系统健康状态"""
    print("\n🏥 测试V2系统健康状态...")
    
    health_endpoints = [
        f"{BASE_URL}/api/message/v2/health",
        f"{BASE_URL}/api/message/v2/stats",
        f"{BASE_URL}/api/message/v2/performance"
    ]
    
    for endpoint in health_endpoints:
        print(f"\n📡 测试: {endpoint}")
        try:
            response = requests.get(endpoint, timeout=5)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ V2端点响应正常")
            elif response.status_code == 404:
                print("   ⚠️  V2端点未注册或路径错误")
            else:
                print(f"   状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 请求失败: {e}")

def main():
    """主测试函数"""
    print("🚀 开始V2消息系统集成测试")
    print(f"测试目标: {BASE_URL}")
    print(f"客户ID: {CUSTOMER_ID}")
    print("=" * 50)
    
    # 测试基础连接
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print("⚠️  服务器连接异常")
    except:
        print("❌ 无法连接到服务器")
        return
    
    # 执行测试
    test_api_fixes()
    test_v2_system_health()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")

if __name__ == "__main__":
    main()