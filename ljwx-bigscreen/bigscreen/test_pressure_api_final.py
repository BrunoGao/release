#!/usr/bin/env python3
"""最终测试pressure API"""

import requests
import time
import json
import mysql.connector

def test_pressure_api_final():
    """最终测试pressure API"""
    print("🔧 最终测试pressure API...")
    
    # 1. 验证数据库中的pressure数据
    print("\n📊 1. 验证数据库pressure数据...")
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            database='lj-06',
            user='root',
            password='123456'
        )
        
        cursor = connection.cursor()
        
        # 查找最新的有pressure数据的记录
        cursor.execute("""
            SELECT device_sn, pressure_high, pressure_low, heart_rate, blood_oxygen, timestamp 
            FROM t_user_health_data 
            WHERE pressure_high IS NOT NULL AND pressure_high > 0 
            ORDER BY timestamp DESC 
            LIMIT 3
        """)
        pressure_data = cursor.fetchall()
        
        print("📋 数据库中最新的pressure数据:")
        for device_sn, ph, pl, hr, bo, ts in pressure_data:
            print(f"   设备: {device_sn}, 高压: {ph}, 低压: {pl}, 心率: {hr}, 血氧: {bo}")
        
        # 找到有pressure数据的设备对应的用户
        cursor.execute("""
            SELECT u.id, u.user_name, h.device_sn, h.pressure_high, h.pressure_low
            FROM t_user_health_data h
            JOIN sys_user u ON h.device_sn = u.device_sn
            WHERE h.pressure_high IS NOT NULL AND h.pressure_high > 0
            ORDER BY h.timestamp DESC
            LIMIT 1
        """)
        user_with_pressure = cursor.fetchone()
        
        if user_with_pressure:
            user_id, user_name, device_sn, ph, pl = user_with_pressure
            print(f"\n👤 找到有pressure数据的用户: ID={user_id}, 姓名={user_name}, 设备={device_sn}, 高压={ph}, 低压={pl}")
        else:
            print("❌ 未找到有pressure数据的用户")
            return
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        return
    
    # 2. 测试API
    print(f"\n🔧 2. 测试API (使用用户ID: {user_id})...")
    try:
        # 测试不同参数组合
        test_cases = [
            {'orgId': 1, 'pageSize': 1},  # 组织查询
            {'orgId': 1, 'userId': user_id, 'pageSize': 1},  # 特定用户查询
        ]
        
        for i, params in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {params}")
            
            # 添加缓存破坏参数
            timestamp = int(time.time())
            params.update({
                'v': timestamp,
                'nocache': 'true',
                '_t': timestamp
            })
            
            response = requests.get('http://127.0.0.1:5001/health_data/page', 
                                  params=params, 
                                  timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查启用指标
                enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
                pressure_enabled = any('pressure' in metric for metric in enabled_metrics)
                print(f"   📊 Pressure启用状态: {'✅' if pressure_enabled else '❌'} {pressure_enabled}")
                
                # 检查返回的健康数据
                health_data = data.get('data', {}).get('healthData', [])
                print(f"   📝 返回记录数: {len(health_data)}")
                
                if health_data:
                    for j, item in enumerate(health_data[:3]):  # 只检查前3条
                        print(f"      记录 {j+1}:")
                        print(f"         设备: {item.get('deviceSn')}")
                        print(f"         用户: {item.get('userName')}")
                        print(f"         pressureHigh: {item.get('pressureHigh')} (类型: {type(item.get('pressureHigh'))})")
                        print(f"         pressureLow: {item.get('pressureLow')} (类型: {type(item.get('pressureLow'))})")
                        print(f"         heartRate: {item.get('heartRate')}")
                        print(f"         bloodOxygen: {item.get('bloodOxygen')}")
                        print(f"         timestamp: {item.get('timestamp')}")
                        
                        # 特别检查是否是我们期望的设备
                        if item.get('deviceSn') == device_sn:
                            print(f"         🎯 这是有pressure数据的设备!")
                
            else:
                print(f"   ❌ API请求失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
    
    except Exception as e:
        print(f"❌ API测试失败: {e}")

if __name__ == "__main__":
    test_pressure_api_final() 