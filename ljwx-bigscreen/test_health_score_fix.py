#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康评分API修复验证测试
测试修复的 /api/health/score/comprehensive 端点
"""

import requests
import json
from datetime import datetime

def test_health_score_api():
    """测试健康评分API"""
    
    base_url = "http://localhost:5225"  # 本地调试端口
    
    # 测试数据
    test_cases = [
        {
            "name": "测试 customerId 参数",
            "url": f"{base_url}/api/health/score/comprehensive",
            "method": "GET", 
            "params": {
                "customerId": "1939964806110937090",
                "days": "7"
            }
        },
        {
            "name": "测试 deviceSn 参数",
            "url": f"{base_url}/api/health/score/comprehensive",
            "method": "GET",
            "params": {
                "deviceSn": "CRFTQ23409001890"
            }
        },
        {
            "name": "测试 POST 接口",
            "url": f"{base_url}/api/health/comprehensive/score", 
            "method": "POST",
            "data": {
                "deviceSn": "CRFTQ23409001890",
                "includePrediction": True,
                "includeFactors": True
            }
        }
    ]
    
    print("🧪 开始测试健康评分API修复...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print(f"🔗 URL: {test_case['url']}")
        
        try:
            if test_case['method'] == 'GET':
                response = requests.get(test_case['url'], params=test_case.get('params', {}), timeout=10)
            else:  # POST
                response = requests.post(
                    test_case['url'], 
                    json=test_case.get('data', {}), 
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ 响应成功: {data.get('success', False)}")
                    if data.get('data'):
                        print(f"📈 数据概览: {list(data['data'].keys())}")
                except:
                    print("⚠️ 响应不是JSON格式")
                    print(f"响应内容: {response.text[:200]}")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"❌ 400错误: {error_data.get('error', error_data.get('message', '未知错误'))}")
                except:
                    print(f"❌ 400错误: {response.text[:200]}")
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                print(f"响应: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误: 无法连接到服务器 (请确保bigscreen服务正在运行)")
        except requests.exceptions.Timeout:
            print("⏰ 请求超时")
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    print("\n💡 修复说明:")
    print("  1. 添加了缺失的 calculate_comprehensive_health_score 方法")
    print("  2. 添加了缺失的 calculate_comprehensive_score 方法")
    print("  3. 修复了 logger 引用问题")
    print("  4. API现在应该能正确处理 customerId 和 deviceSn 参数")

if __name__ == "__main__":
    test_health_score_api()