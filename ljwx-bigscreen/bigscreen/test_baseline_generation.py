#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'bigScreen'))

import requests
import json
from datetime import datetime, timedelta

def test_baseline_api():
    """测试baseline生成API"""
    print("=== 测试Baseline生成API ===")
    
    base_url = "http://localhost:5001"
    
    # 1. 检查baseline状态
    print("1. 检查当前baseline状态...")
    try:
        response = requests.get(f"{base_url}/api/baseline/status?orgId=1", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 状态检查成功: {json.dumps(status_data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态检查异常: {e}")
    
    # 2. 触发baseline生成
    print("\n2. 触发baseline生成...")
    try:
        payload = {
            'orgId': '1',
            'days': 3  # 生成最近3天的基线
        }
        response = requests.post(
            f"{base_url}/api/baseline/generate", 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            generate_data = response.json()
            print(f"✅ 生成请求成功: {json.dumps(generate_data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 生成请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 生成请求异常: {e}")
    
    # 3. 再次检查baseline状态
    print("\n3. 再次检查baseline状态...")
    try:
        response = requests.get(f"{base_url}/api/baseline/status?orgId=1", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ 状态检查成功: {json.dumps(status_data, ensure_ascii=False, indent=2)}")
        else:
            print(f"❌ 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 状态检查异常: {e}")

def test_baseline_direct():
    """直接测试baseline生成函数"""
    print("\n=== 直接测试Baseline生成函数 ===")
    
    try:
        # 导入Flask应用上下文
        from bigScreen import app
        from bigScreen.health_baseline import HealthBaselineGenerator
        from bigScreen.models import db, HealthBaseline
        from datetime import date
        
        with app.app_context():
            print("1. 检查数据库连接...")
            try:
                baseline_count = db.session.query(HealthBaseline).count()
                print(f"✅ 数据库连接正常，当前t_health_baseline记录数: {baseline_count}")
            except Exception as e:
                print(f"❌ 数据库连接失败: {e}")
                return
            
            print("\n2. 创建HealthBaselineGenerator实例...")
            generator = HealthBaselineGenerator()
            print("✅ 生成器创建成功")
            
            print("\n3. 生成用户基线数据...")
            target_date = date.today() - timedelta(days=1)  # 昨天
            user_result = generator.generate_daily_user_baseline(target_date)
            print(f"用户基线生成结果: {json.dumps(user_result, ensure_ascii=False, indent=2, default=str)}")
            
            print("\n4. 生成组织基线数据...")
            org_result = generator.generate_daily_org_baseline(target_date)
            print(f"组织基线生成结果: {json.dumps(org_result, ensure_ascii=False, indent=2, default=str)}")
            
            print("\n5. 再次检查数据库记录数...")
            try:
                new_baseline_count = db.session.query(HealthBaseline).count()
                print(f"✅ 处理后t_health_baseline记录数: {new_baseline_count}")
                print(f"新增记录数: {new_baseline_count - baseline_count}")
            except Exception as e:
                print(f"❌ 数据库查询失败: {e}")
                
    except Exception as e:
        print(f"❌ 直接测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_health_data_query():
    """测试健康数据查询"""
    print("\n=== 测试健康数据查询 ===")
    
    try:
        from bigScreen import app
        from bigScreen.models import db, UserHealthData
        from datetime import date
        
        with app.app_context():
            print("1. 查询最近的健康数据...")
            
            # 查询最近一天的数据
            target_date = date.today()
            health_data = db.session.query(UserHealthData)\
                .filter(db.func.date(UserHealthData.create_time) == target_date)\
                .filter(UserHealthData.is_deleted == False)\
                .limit(10).all()
            
            print(f"✅ 今天的健康数据记录数: {len(health_data)}")
            
            if health_data:
                sample = health_data[0]
                print(f"样本数据:")
                print(f"  用户ID: {sample.user_id}")
                print(f"  设备SN: {sample.device_sn}")
                print(f"  心率: {sample.heart_rate}")
                print(f"  血氧: {sample.blood_oxygen}")
                print(f"  体温: {sample.temperature}")
                print(f"  创建时间: {sample.create_time}")
            
            # 查询昨天的数据
            yesterday = date.today() - timedelta(days=1)
            yesterday_data = db.session.query(UserHealthData)\
                .filter(db.func.date(UserHealthData.create_time) == yesterday)\
                .filter(UserHealthData.is_deleted == False)\
                .limit(10).all()
            
            print(f"✅ 昨天的健康数据记录数: {len(yesterday_data)}")
            
            # 查询有数据的用户列表
            users_with_data = db.session.query(UserHealthData.user_id, UserHealthData.device_sn)\
                .filter(db.func.date(UserHealthData.create_time) == yesterday)\
                .filter(UserHealthData.is_deleted == False)\
                .filter(UserHealthData.user_id.isnot(None))\
                .distinct().all()
            
            print(f"✅ 昨天有数据的用户数: {len(users_with_data)}")
            if users_with_data:
                print(f"样本用户: {users_with_data[:3]}")
                
    except Exception as e:
        print(f"❌ 健康数据查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_health_data_query()
    test_baseline_direct()
    test_baseline_api() 