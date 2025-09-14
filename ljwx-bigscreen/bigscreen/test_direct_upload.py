#!/usr/bin/env python3
"""
直接测试upload_health_data数据插入问题
"""

import json
import time
import pymysql
import requests
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_database_before_and_after():
    """测试上传前后的数据库状态"""
    
    # 测试数据
    test_data = {
        'data': {
            'deviceSn': 'TEST_DEBUG_001',
            'customerId': 1939964806110937090,
            'orgId': 1939964806110937090,
            'userId': '1940034481851260929',
            'heart_rate': 92,
            'blood_oxygen': 96,
            'body_temperature': '36.9',
            'step': 600,
            'distance': '0.7',
            'calorie': '25.0',
            'latitude': '22.533270802543',
            'longitude': '113.92727390719',
            'altitude': '0.0',
            'stress': 52,
            'upload_method': '4g',
            'blood_pressure_systolic': 128,
            'blood_pressure_diastolic': 85,
            'sleepData': 'null',
            'exerciseDailyData': 'null',
            'exerciseWeekData': 'null',
            'scientificSleepData': 'null',
            'workoutData': 'null',
            'timestamp': '2025-09-02 17:00:00'
        }
    }
    
    print("=== 健康数据上传调试测试 ===")
    
    # 连接数据库
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            # 1. 检查上传前的状态
            print("\n1. 检查上传前数据库状态:")
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn = %s", ('TEST_DEBUG_001',))
            before_count = cursor.fetchone()[0]
            print(f"   上传前记录数: {before_count}")
            
            # 2. 执行上传
            print("\n2. 执行数据上传:")
            print(f"   测试数据: {json.dumps(test_data, ensure_ascii=False, indent=4)}")
            
            try:
                response = requests.post('http://localhost:5225/upload_health_data', json=test_data, timeout=15)
                print(f"   HTTP状态: {response.status_code}")
                print(f"   响应内容: {response.text}")
            except Exception as e:
                print(f"   ❌ 上传失败: {e}")
                return
            
            # 3. 等待批处理器处理
            print("\n3. 等待批处理器处理 (10秒)...")
            for i in range(10):
                time.sleep(1)
                cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn = %s", ('TEST_DEBUG_001',))
                current_count = cursor.fetchone()[0]
                if current_count > before_count:
                    print(f"   ✅ 第{i+1}秒: 检测到新记录! 总记录数: {current_count}")
                    break
                else:
                    print(f"   ⏳ 第{i+1}秒: 记录数无变化: {current_count}")
            
            # 4. 最终检查
            print("\n4. 最终数据库状态:")
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn = %s", ('TEST_DEBUG_001',))
            after_count = cursor.fetchone()[0]
            print(f"   最终记录数: {after_count}")
            print(f"   新增记录数: {after_count - before_count}")
            
            if after_count > before_count:
                # 显示新插入的记录
                cursor.execute("""
                    SELECT device_sn, heart_rate, step, timestamp, create_time 
                    FROM t_user_health_data 
                    WHERE device_sn = %s 
                    ORDER BY create_time DESC 
                    LIMIT 3
                """, ('TEST_DEBUG_001',))
                records = cursor.fetchall()
                print("\n   ✅ 新插入的记录:")
                for i, record in enumerate(records):
                    print(f"   {i+1}. device_sn={record[0]}, heart_rate={record[1]}, step={record[2]}, timestamp={record[3]}, create_time={record[4]}")
            else:
                print("\n   ❌ 没有新记录插入 - 存在问题!")
                
                # 检查最近的所有插入
                cursor.execute("""
                    SELECT COUNT(*) FROM t_user_health_data 
                    WHERE create_time > DATE_SUB(NOW(), INTERVAL 15 MINUTE)
                """)
                recent_all = cursor.fetchone()[0]
                print(f"   最近15分钟所有设备插入数: {recent_all}")
                
    finally:
        conn.close()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    check_database_before_and_after()