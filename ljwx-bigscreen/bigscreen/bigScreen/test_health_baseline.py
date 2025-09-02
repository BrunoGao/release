#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康基线生成测试脚本
用于测试和验证健康基线生成功能
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_baseline_api():
    """测试健康基线API"""
    base_url = "http://localhost:5001"
    
    print("🧪 开始测试健康基线API")
    print("-" * 50)
    
    # 1. 获取基线状态
    print("1️⃣ 测试获取基线状态...")
    try:
        response = requests.get(f"{base_url}/api/health-baseline/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ 状态获取成功:")
            print(f"   调度器运行状态: {data['data']['scheduler_running']}")
            print(f"   个人基线数量: {data['data']['personal_baselines']}")
            print(f"   组织基线数量: {data['data']['org_baselines']}")
            print(f"   最新个人基线: {data['data']['latest_personal_baseline']}")
            print(f"   最新组织基线: {data['data']['latest_org_baseline']}")
        else:
            print(f"❌ 状态获取失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 状态获取异常: {e}")
    
    print()
    
    # 2. 手动生成基线（测试用例）
    print("2️⃣ 测试手动生成基线...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    test_data = {
        "startDate": yesterday,
        "endDate": yesterday
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/health-baseline/generate",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 基线生成请求成功:")
            print(f"   个人基线生成: {data['data']['personal']}")
            print(f"   组织基线生成: {data['data']['org']}")
            if data['data']['errors']:
                print(f"   错误信息: {data['data']['errors']}")
        else:
            print(f"❌ 基线生成失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 基线生成异常: {e}")
    
    print()
    
    # 3. 特定用户基线生成测试
    print("3️⃣ 测试特定用户基线生成...")
    user_test_data = {
        "userId": 1939964960343883777,  # 测试用户ID
        "startDate": yesterday,
        "endDate": yesterday
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/health-baseline/generate",
            json=user_test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 用户基线生成成功:")
            print(f"   结果: {data['message']}")
        else:
            print(f"❌ 用户基线生成失败: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ 用户基线生成异常: {e}")

def direct_test():
    """直接测试基线生成功能"""
    print("🔧 直接测试基线生成功能")
    print("-" * 50)
    
    try:
        from bigScreen import app
        from bigScreen.health_baseline_scheduler import get_health_baseline_scheduler
        from datetime import date
        
        with app.app_context():
            scheduler = get_health_baseline_scheduler(app)
            
            # 测试获取活跃用户
            users = scheduler._get_active_users()
            print(f"📊 找到活跃用户: {len(users)}")
            if users:
                print(f"   示例用户: {users[0]}")
            
            # 测试获取活跃组织
            orgs = scheduler._get_active_orgs()
            print(f"🏢 找到活跃组织: {len(orgs)}")
            if orgs:
                print(f"   示例组织: {orgs[0]}")
            
            # 测试单个用户基线生成
            if users:
                print(f"\n🧪 测试用户 {users[0]['user_id']} 基线生成...")
                yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
                result = scheduler._generate_user_baseline(users[0], yesterday, yesterday)
                print(f"   结果: {'✅ 成功' if result else '❌ 失败'}")
    
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🏥 健康基线生成系统测试")
    print("=" * 60)
    
    # 选择测试方式
    test_type = input("选择测试方式 (1: API测试, 2: 直接测试, 3: 全部): ").strip()
    
    if test_type in ['1', '3']:
        test_baseline_api()
        print()
    
    if test_type in ['2', '3']:
        direct_test()
    
    print("🎯 测试完成")