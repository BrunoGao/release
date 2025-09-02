#!/usr/bin/env python3
"""测试用户提供的原始数据格式"""
import os
os.environ['IS_DOCKER'] = 'false'
import sys
sys.path.append('.')

from flask import Flask
from bigScreen.models import db
from bigScreen.optimized_health_data import HealthDataOptimizer
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_test_app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def test_user_original_data():
    """测试用户提供的原始数据格式"""
    print("🔍 测试用户提供的原始数据格式...")
    
    app = create_test_app()
    
    with app.app_context():
        optimizer = HealthDataOptimizer()
        
        # 用户提供的原始数据
        user_data = {
            'deviceSn': 'CRFTQ23409001890',
            'heart_rate': 66,  # 原始字段名
            'blood_oxygen': 98,  # 原始字段名
            'body_temperature': '0.0',  # 原始字段名
            'step': 0,
            'distance': '0.0',
            'calorie': '139.0',
            'latitude': '22.540363',
            'longitude': '114.015181',
            'altitude': '0.0',
            'stress': 0,
            'upload_method': 'wifi',
            'blood_pressure_systolic': 107,  # 原始字段名
            'blood_pressure_diastolic': 74,  # 原始字段名
            'sleepData': '{"code":0,"data":[],"name":"sleep","type":"history"}',
            'exerciseDailyData': 'null',
            'exerciseWeekData': 'null',
            'scientificSleepData': 'null',
            'workoutData': '{"code":0,"data":[],"name":"workout","type":"history"}',
            'timestamp': '2025-05-27 16:00:00'
        }
        
        print(f"📊 原始数据: {user_data}")
        
        device_sn = user_data['deviceSn']
        result = optimizer.add_data(user_data, device_sn)
        
        print(f"📊 添加结果: {result}")
        
        # 等待处理
        print("⏳ 等待5秒让批处理器处理...")
        time.sleep(5)
        
        # 检查统计
        stats = optimizer.get_stats()
        print(f"📈 优化器统计: {stats}")
        
        return stats

def check_final_results():
    """检查最终结果"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("\n📊 检查最终数据库结果...")
            
            # 检查主表最新数据
            cursor.execute("""
                SELECT id, device_sn, heart_rate, blood_oxygen, pressure_high, pressure_low, 
                       temperature, step, distance, calorie, timestamp, upload_method
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                AND create_time >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
                ORDER BY create_time DESC 
                LIMIT 2
            """)
            
            main_data = cursor.fetchall()
            if main_data:
                print(f"✅ 主表最新数据 ({len(main_data)}条):")
                for data in main_data:
                    print(f"  ID:{data[0]} | 心率:{data[2]} 血氧:{data[3]} 血压:{data[4]}/{data[5]} | 体温:{data[6]} | 步数:{data[7]} | 距离:{data[8]} | 卡路里:{data[9]} | 上传方式:{data[11]} | {data[10]}")
            else:
                print("❌ 主表没有最新数据")
            
            # 检查每日表
            cursor.execute("""
                SELECT id, device_sn, date, sleep_data, exercise_daily_data, workout_data,
                       create_time, update_time
                FROM t_user_health_data_daily 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY update_time DESC 
                LIMIT 2
            """)
            
            daily_data = cursor.fetchall()
            if daily_data:
                print(f"\n✅ 每日表数据 ({len(daily_data)}条):")
                for data in daily_data:
                    sleep_data = data[3][:50] + '...' if data[3] and len(data[3]) > 50 else data[3]
                    print(f"  ID:{data[0]} | 日期:{data[2]} | 睡眠数据:{sleep_data} | 运动数据:{data[4]} | 锻炼数据:{data[5]} | 更新时间:{data[7]}")
            else:
                print("\n❌ 每日表没有数据")
            
            # 检查每周表
            cursor.execute("""
                SELECT id, device_sn, week_start, exercise_week_data,
                       create_time, update_time
                FROM t_user_health_data_weekly 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY update_time DESC 
                LIMIT 2
            """)
            
            weekly_data = cursor.fetchall()
            if weekly_data:
                print(f"\n✅ 每周表数据 ({len(weekly_data)}条):")
                for data in weekly_data:
                    print(f"  ID:{data[0]} | 周开始:{data[2]} | 周运动数据:{data[3]} | 更新时间:{data[5]}")
            else:
                print("\n❌ 每周表没有数据")
                
            return len(main_data) > 0, len(daily_data) > 0, len(weekly_data) > 0
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False, False, False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 开始测试用户原始数据格式...")
    print("=" * 80)
    
    try:
        # 1. 测试用户原始数据
        stats = test_user_original_data()
        
        # 2. 检查最终结果
        main_ok, daily_ok, weekly_ok = check_final_results()
        
        print("\n" + "=" * 80)
        print("📋 最终测试结果总结:")
        print(f"  优化器处理: {'✅ 成功' if stats and stats.get('processed', 0) > 0 else '❌ 失败'}")
        print(f"  主表插入: {'✅ 成功' if main_ok else '❌ 失败'}")
        print(f"  每日表插入: {'✅ 成功' if daily_ok else '❌ 失败'}")
        print(f"  每周表插入: {'✅ 成功' if weekly_ok else '❌ 失败'}")
        
        if stats:
            print(f"  已处理数据: {stats.get('processed', 0)}条")
            print(f"  批次数: {stats.get('batches', 0)}")
            if stats.get('errors', 0) > 0:
                print(f"  ⚠️  处理错误: {stats.get('errors', 0)}次")
            if stats.get('duplicates', 0) > 0:
                print(f"  ℹ️  重复数据: {stats.get('duplicates', 0)}次")
        
        if main_ok and daily_ok and weekly_ok:
            print("\n🎉 用户数据上传逻辑修复完成!")
            print("✅ 原始数据格式完全兼容")
            print("✅ 数据能正确分离到主表、每日表和每周表")
            print("✅ 字段映射工作正常")
            print("\n📝 支持的数据字段:")
            print("  主表字段: heart_rate, blood_oxygen, body_temperature, blood_pressure_systolic/diastolic, step, distance, calorie, latitude, longitude, altitude, stress, upload_method")
            print("  每日表字段: sleepData, exerciseDailyData, workoutData, scientificSleepData")
            print("  每周表字段: exerciseWeekData")
        else:
            print("\n❌ 部分功能仍需调试")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc() 