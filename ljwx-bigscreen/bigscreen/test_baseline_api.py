#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过API接口测试健康基线生成
"""

import requests
import json
from datetime import datetime, timedelta

def test_baseline_api():
    """测试健康基线API接口"""
    base_url = "http://localhost:8001"  # 默认端口
    
    print("🏥 健康基线API测试")
    print("=" * 50)
    
    # 1. 测试基线状态API
    print("1️⃣ 测试获取基线状态...")
    try:
        response = requests.get(f"{base_url}/api/health-baseline/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 状态获取成功:")
            if data.get('success'):
                status_data = data.get('data', {})
                print(f"   调度器运行状态: {status_data.get('scheduler_running')}")
                print(f"   个人基线数量: {status_data.get('personal_baselines')}")
                print(f"   组织基线数量: {status_data.get('org_baselines')}")
                print(f"   最新个人基线: {status_data.get('latest_personal_baseline')}")
                print(f"   最新组织基线: {status_data.get('latest_org_baseline')}")
                
                schedule_info = status_data.get('schedule_info', {})
                print(f"   调度配置:")
                print(f"     - 个人基线: 每日{schedule_info.get('daily_personal')}")
                print(f"     - 组织基线: 每日{schedule_info.get('daily_org')}")
                print(f"     - 健康评分: 每日{schedule_info.get('daily_score')}")
                print(f"     - 周基线: {schedule_info.get('weekly')}")
            else:
                print(f"❌ 状态获取失败: {data.get('message')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"   响应内容: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败: 服务器可能未启动，请先启动应用")
        print(f"   命令: python3 run.py")
        return False
    except Exception as e:
        print(f"❌ 状态获取异常: {e}")
    
    print()
    
    # 2. 测试手动生成基线API
    print("2️⃣ 测试手动生成基线...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 测试数据
    test_cases = [
        {
            "name": "生成昨天的基线数据",
            "data": {
                "startDate": yesterday,
                "endDate": yesterday
            }
        },
        {
            "name": "生成最近7天的基线数据",
            "data": {
                "startDate": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                "endDate": yesterday
            }
        },
        {
            "name": "生成特定组织基线",
            "data": {
                "orgId": 1,
                "startDate": yesterday,
                "endDate": yesterday
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   🧪 测试案例{i}: {test_case['name']}")
        try:
            response = requests.post(
                f"{base_url}/api/health-baseline/generate",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ 请求成功:")
                if data.get('success'):
                    result_data = data.get('data', {})
                    print(f"      个人基线: {result_data.get('personal', 0)} 个")
                    print(f"      组织基线: {result_data.get('org', 0)} 个")
                    if result_data.get('errors'):
                        print(f"      错误信息: {result_data['errors']}")
                    print(f"      消息: {data.get('message', '无')}")
                else:
                    print(f"   ❌ 生成失败: {data.get('message')}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                print(f"      响应: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏱️ 请求超时（30秒），基线生成可能需要更长时间")
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    return True

def test_baseline_with_curl():
    """使用curl命令测试（作为备用方案）"""
    print("\n🔧 Curl命令测试方案:")
    print("=" * 30)
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    commands = [
        f"# 获取基线状态",
        f"curl -X GET http://localhost:8001/api/health-baseline/status",
        f"",
        f"# 手动生成基线",
        f"curl -X POST http://localhost:8001/api/health-baseline/generate \\",
        f"  -H 'Content-Type: application/json' \\",
        f"  -d '{{\"startDate\": \"{yesterday}\", \"endDate\": \"{yesterday}\"}}'",
    ]
    
    for cmd in commands:
        print(cmd)

if __name__ == "__main__":
    success = test_baseline_api()
    if not success:
        test_baseline_with_curl()
    print("\n🎯 测试完成")