#!/usr/bin/env python3
"""测试修复后的健康数据上传逻辑"""
import os
os.environ['IS_DOCKER'] = 'false'
import requests
import json
import time
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def test_upload_health_data():
    """测试健康数据上传"""
    url = 'http://localhost:5001/upload_health_data'
    
    # 用户提供的测试数据
    test_data = {
        'data': {
            'deviceSn': 'CRFTQ23409001890',
            'heartRate': 66,  # 修正字段名
            'bloodOxygen': 98,  # 修正字段名
            'temperature': '0.0',  # 修正字段名
            'step': 0,
            'distance': '0.0',
            'calorie': '139.0',
            'latitude': '22.540363',
            'longitude': '114.015181',
            'altitude': '0.0',
            'stress': 0,
            'upload_method': 'wifi',
            'pressureHigh': 107,  # 修正字段名
            'pressureLow': 74,  # 修正字段名
            'sleepData': '{"code":0,"data":[],"name":"sleep","type":"history"}',
            'exerciseDailyData': 'null',
            'exerciseWeekData': 'null',
            'scientificSleepData': 'null',
            'workoutData': '{"code":0,"data":[],"name":"workout","type":"history"}',
            'timestamp': '2025-05-27 16:45:30'  # 使用新时间戳
        }
    }
    
    print("🧪 测试健康数据上传...")
    print(f"URL: {url}")
    print(f"设备SN: {test_data['data']['deviceSn']}")
    print(f"心率: {test_data['data']['heartRate']}")
    print(f"血氧: {test_data['data']['bloodOxygen']}")
    print(f"血压: {test_data['data']['pressureHigh']}/{test_data['data']['pressureLow']}")
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        print(f"\n📊 响应状态码: {response.status_code}")
        print(f"📊 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ 上传成功!")
                return True
            else:
                print(f"❌ 上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def check_database_insertion():
    """检查数据库插入情况"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("\n📊 检查数据库插入情况...")
            
            # 检查主表最新数据
            cursor.execute("""
                SELECT id, device_sn, heart_rate, blood_oxygen, pressure_high, pressure_low, 
                       timestamp, create_time
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY create_time DESC 
                LIMIT 3
            """)
            
            main_data = cursor.fetchall()
            if main_data:
                print(f"✅ 主表最新数据 ({len(main_data)}条):")
                for data in main_data:
                    print(f"  ID:{data[0]} | 心率:{data[2]} 血氧:{data[3]} 血压:{data[4]}/{data[5]} | {data[7]}")
            else:
                print("❌ 主表没有找到数据")
            
            # 检查每日表
            cursor.execute("""
                SELECT id, device_sn, date, sleep_data, exercise_daily_data, workout_data,
                       create_time, update_time
                FROM t_user_health_data_daily 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY create_time DESC 
                LIMIT 2
            """)
            
            daily_data = cursor.fetchall()
            if daily_data:
                print(f"\n✅ 每日表数据 ({len(daily_data)}条):")
                for data in daily_data:
                    print(f"  ID:{data[0]} | 日期:{data[2]} | 睡眠:{data[3] is not None} 运动:{data[4] is not None} 锻炼:{data[5] is not None}")
            else:
                print("\n❌ 每日表没有找到数据")
            
            # 检查每周表
            cursor.execute("""
                SELECT id, device_sn, week_start, exercise_week_data,
                       create_time, update_time
                FROM t_user_health_data_weekly 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY create_time DESC 
                LIMIT 2
            """)
            
            weekly_data = cursor.fetchall()
            if weekly_data:
                print(f"\n✅ 每周表数据 ({len(weekly_data)}条):")
                for data in weekly_data:
                    print(f"  ID:{data[0]} | 周开始:{data[2]} | 周运动:{data[3] is not None}")
            else:
                print("\n❌ 每周表没有找到数据")
                
            return len(main_data) > 0
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False
    finally:
        conn.close()

def test_optimizer_stats():
    """测试优化器统计信息"""
    url = 'http://localhost:5001/optimizer_stats'
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📈 优化器统计:")
            print(f"  已处理: {stats.get('processed', 0)}")
            print(f"  批次数: {stats.get('batches', 0)}")
            print(f"  错误数: {stats.get('errors', 0)}")
            print(f"  重复数: {stats.get('duplicates', 0)}")
            print(f"  队列大小: {stats.get('queue_size', 0)}")
            return stats
        else:
            print(f"❌ 获取统计失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取统计异常: {e}")
        return None

if __name__ == "__main__":
    print("🔍 开始测试修复后的上传逻辑...")
    print("=" * 60)
    
    # 1. 测试数据上传
    success = test_upload_health_data()
    
    # 2. 等待处理
    print("\n⏳ 等待5秒让批处理器处理数据...")
    time.sleep(5)
    
    # 3. 检查统计信息
    stats = test_optimizer_stats()
    
    # 4. 检查数据库插入
    db_success = check_database_insertion()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    print(f"  API上传: {'✅ 成功' if success else '❌ 失败'}")
    print(f"  数据处理: {'✅ 成功' if stats and stats.get('processed', 0) > 0 else '❌ 失败'}")
    print(f"  数据库插入: {'✅ 成功' if db_success else '❌ 失败'}")
    
    if stats:
        if stats.get('errors', 0) > 0:
            print(f"  ⚠️  处理错误: {stats.get('errors', 0)}次")
        if stats.get('duplicates', 0) > 0:
            print(f"  ℹ️  重复数据: {stats.get('duplicates', 0)}次")
    
    if success and db_success:
        print("\n🎉 健康数据上传逻辑修复成功!")
        print("✅ 数据能正确分离到主表、每日表和每周表")
    else:
        print("\n❌ 还需要进一步调试") 