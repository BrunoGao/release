#!/usr/bin/env python3
"""调试批处理器错误"""
import os
os.environ['IS_DOCKER'] = 'false'
import requests
import json
import time

def debug_batch_processor():
    """调试批处理器"""
    print("🔍 调试批处理器错误...")
    
    # 1. 检查优化器状态
    try:
        response = requests.get('http://localhost:5001/optimizer_stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 优化器状态:")
            print(f"  已处理: {stats.get('processed', 0)}")
            print(f"  批次数: {stats.get('batches', 0)}")
            print(f"  错误数: {stats.get('errors', 0)}")
            print(f"  重复数: {stats.get('duplicates', 0)}")
            print(f"  队列大小: {stats.get('queue_size', 0)}")
            print(f"  已处理键数: {stats.get('processed_keys_count', 0)}")
        else:
            print(f"❌ 无法获取优化器状态: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取优化器状态异常: {e}")
    
    # 2. 测试简单数据上传
    print(f"\n🧪 测试简单数据上传...")
    test_data = {
        'data': {
            'deviceSn': 'CRFTQ23409001890',
            'heartRate': 75,
            'bloodOxygen': 99,
            'temperature': '36.5',
            'pressureHigh': 120,
            'pressureLow': 80,
            'sleepData': '{"test": "data"}',
            'exerciseDailyData': '{"daily": "test"}',
            'exerciseWeekData': '{"weekly": "test"}',
            'workoutData': '{"workout": "test"}',
            'scientificSleepData': '{"scientific": "test"}',
            'timestamp': '2025-05-27 17:00:00'
        }
    }
    
    try:
        response = requests.post('http://localhost:5001/upload_health_data', 
                               json=test_data, timeout=10)
        print(f"📊 上传响应: {response.status_code} - {response.text}")
        
        # 等待处理
        print("⏳ 等待3秒...")
        time.sleep(3)
        
        # 再次检查状态
        response = requests.get('http://localhost:5001/optimizer_stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 处理后状态:")
            print(f"  已处理: {stats.get('processed', 0)}")
            print(f"  错误数: {stats.get('errors', 0)}")
            print(f"  队列大小: {stats.get('queue_size', 0)}")
            
    except Exception as e:
        print(f"❌ 测试上传异常: {e}")

def check_table_structure():
    """检查表结构"""
    import pymysql
    from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print(f"\n📋 检查表结构...")
            
            # 检查每日表是否存在
            cursor.execute("SHOW TABLES LIKE 't_user_health_data_daily'")
            daily_exists = cursor.fetchone()
            print(f"每日表存在: {daily_exists is not None}")
            
            if daily_exists:
                cursor.execute("DESCRIBE t_user_health_data_daily")
                daily_columns = cursor.fetchall()
                print(f"每日表字段: {[col[0] for col in daily_columns]}")
            
            # 检查每周表是否存在
            cursor.execute("SHOW TABLES LIKE 't_user_health_data_weekly'")
            weekly_exists = cursor.fetchone()
            print(f"每周表存在: {weekly_exists is not None}")
            
            if weekly_exists:
                cursor.execute("DESCRIBE t_user_health_data_weekly")
                weekly_columns = cursor.fetchall()
                print(f"每周表字段: {[col[0] for col in weekly_columns]}")
                
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 开始调试批处理器...")
    print("=" * 50)
    
    # 1. 检查表结构
    check_table_structure()
    
    # 2. 调试批处理器
    debug_batch_processor()
    
    print("\n" + "=" * 50)
    print("调试完成") 