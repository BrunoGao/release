#!/usr/bin/env python3
"""直接查询数据库验证pressure数据"""

import mysql.connector
from mysql.connector import Error
import requests
import time

def verify_pressure_data():
    """验证数据库中的压力数据和API配置"""
    connection = None
    try:
        # 连接数据库
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='lj-06',
            user='root',
            password='123456'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ 数据库连接成功")
            
            # 1. 检查配置表
            print("\n📋 检查配置表:")
            cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1 AND data_type LIKE '%pressure%'")
            pressure_configs = cursor.fetchall()
            
            for data_type, is_enabled in pressure_configs:
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {data_type}: {is_enabled}")
            
            # 2. 检查实际数据 - 查找有pressure数据的记录
            print("\n🔍 检查实际数据:")
            cursor.execute("""
                SELECT device_sn, pressure_high, pressure_low, heart_rate, blood_oxygen, timestamp 
                FROM t_user_health_data 
                WHERE pressure_high IS NOT NULL AND pressure_high > 0 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            pressure_data = cursor.fetchall()
            
            if pressure_data:
                print("✅ 找到有pressure数据的记录:")
                for device_sn, ph, pl, hr, bo, ts in pressure_data:
                    print(f"   设备: {device_sn}, 高压: {ph}, 低压: {pl}, 心率: {hr}, 血氧: {bo}, 时间: {ts}")
            else:
                print("❌ 未找到有pressure数据的记录")
            
            # 3. 测试API配置是否生效
            print(f"\n🔧 测试API配置...")
            try:
                # 强制跳过缓存
                timestamp = int(time.time())
                response = requests.get('http://127.0.0.1:5001/health_data/page', params={
                    'orgId': 1,
                    'pageSize': 1,
                    'v': timestamp,
                    'nocache': 'true'
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    enabled_metrics = data.get('data', {}).get('enabledMetrics', [])
                    
                    print(f"📊 API启用的指标: {enabled_metrics}")
                    
                    # 检查pressure是否在启用列表中
                    pressure_in_metrics = any('pressure' in metric for metric in enabled_metrics)
                    status = "✅" if pressure_in_metrics else "❌"
                    print(f"{status} pressure相关指标在API中: {pressure_in_metrics}")
                    
                    # 检查实际数据
                    health_data = data.get('data', {}).get('healthData', [])
                    if health_data:
                        first_item = health_data[0]
                        print(f"\n📝 API返回的第一条数据:")
                        print(f"   pressureHigh: {first_item.get('pressureHigh')}")
                        print(f"   pressureLow: {first_item.get('pressureLow')}")
                        print(f"   heartRate: {first_item.get('heartRate')}")
                        print(f"   bloodOxygen: {first_item.get('bloodOxygen')}")
                
                else:
                    print(f"❌ API请求失败: {response.status_code}")
                    
            except Exception as api_error:
                print(f"❌ API测试失败: {api_error}")
                
    except Error as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    verify_pressure_data() 