#!/usr/bin/env python3
"""直接测试优化器逻辑"""
import os
os.environ['IS_DOCKER'] = 'false'
import sys
sys.path.append('.')

# 设置Flask应用上下文
from flask import Flask
from bigScreen.models import db
from bigScreen.optimized_health_data import HealthDataOptimizer
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_test_app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def test_optimizer_direct():
    """直接测试优化器"""
    print("🔍 直接测试优化器逻辑...")
    
    # 创建应用上下文
    app = create_test_app()
    
    with app.app_context():
        # 创建优化器实例
        optimizer = HealthDataOptimizer()
        
        # 测试数据
        test_data = {
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
            'timestamp': '2025-05-27 17:30:00'
        }
        
        print(f"📊 测试数据: {test_data}")
        
        # 添加数据到优化器
        device_sn = test_data['deviceSn']
        result = optimizer.add_data(test_data, device_sn)
        
        print(f"📊 添加结果: {result}")
        
        # 等待处理
        print("⏳ 等待5秒让批处理器处理...")
        time.sleep(5)
        
        # 检查统计
        stats = optimizer.get_stats()
        print(f"📈 优化器统计: {stats}")
        
        return stats

def check_database_results():
    """检查数据库结果"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("\n📊 检查数据库结果...")
            
            # 检查主表
            cursor.execute("""
                SELECT id, device_sn, heart_rate, blood_oxygen, pressure_high, pressure_low, 
                       timestamp, create_time
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                AND create_time >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
                ORDER BY create_time DESC 
                LIMIT 3
            """)
            
            main_data = cursor.fetchall()
            if main_data:
                print(f"✅ 主表新数据 ({len(main_data)}条):")
                for data in main_data:
                    print(f"  ID:{data[0]} | 心率:{data[2]} 血氧:{data[3]} 血压:{data[4]}/{data[5]} | {data[7]}")
            else:
                print("❌ 主表没有新数据")
            
            # 检查每日表
            cursor.execute("""
                SELECT id, device_sn, date, sleep_data, exercise_daily_data, workout_data,
                       create_time, update_time
                FROM t_user_health_data_daily 
                WHERE device_sn = 'CRFTQ23409001890'
                AND create_time >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
                ORDER BY create_time DESC 
                LIMIT 2
            """)
            
            daily_data = cursor.fetchall()
            if daily_data:
                print(f"\n✅ 每日表新数据 ({len(daily_data)}条):")
                for data in daily_data:
                    print(f"  ID:{data[0]} | 日期:{data[2]} | 睡眠:{data[3] is not None} 运动:{data[4] is not None} 锻炼:{data[5] is not None}")
            else:
                print("\n❌ 每日表没有新数据")
            
            # 检查每周表
            cursor.execute("""
                SELECT id, device_sn, week_start, exercise_week_data,
                       create_time, update_time
                FROM t_user_health_data_weekly 
                WHERE device_sn = 'CRFTQ23409001890'
                AND create_time >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
                ORDER BY create_time DESC 
                LIMIT 2
            """)
            
            weekly_data = cursor.fetchall()
            if weekly_data:
                print(f"\n✅ 每周表新数据 ({len(weekly_data)}条):")
                for data in weekly_data:
                    print(f"  ID:{data[0]} | 周开始:{data[2]} | 周运动:{data[3] is not None}")
            else:
                print("\n❌ 每周表没有新数据")
                
            return len(main_data) > 0, len(daily_data) > 0, len(weekly_data) > 0
            
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return False, False, False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 开始直接测试优化器...")
    print("=" * 60)
    
    try:
        # 1. 测试优化器
        stats = test_optimizer_direct()
        
        # 2. 检查数据库结果
        main_ok, daily_ok, weekly_ok = check_database_results()
        
        print("\n" + "=" * 60)
        print("📋 测试结果总结:")
        print(f"  优化器处理: {'✅ 成功' if stats and stats.get('processed', 0) > 0 else '❌ 失败'}")
        print(f"  主表插入: {'✅ 成功' if main_ok else '❌ 失败'}")
        print(f"  每日表插入: {'✅ 成功' if daily_ok else '❌ 失败'}")
        print(f"  每周表插入: {'✅ 成功' if weekly_ok else '❌ 失败'}")
        
        if stats:
            if stats.get('errors', 0) > 0:
                print(f"  ⚠️  处理错误: {stats.get('errors', 0)}次")
            if stats.get('duplicates', 0) > 0:
                print(f"  ℹ️  重复数据: {stats.get('duplicates', 0)}次")
        
        if main_ok and daily_ok and weekly_ok:
            print("\n🎉 健康数据上传逻辑完全正常!")
            print("✅ 数据能正确分离到主表、每日表和每周表")
        elif main_ok:
            print("\n⚠️  主表插入正常，但每日/每周表有问题")
        else:
            print("\n❌ 数据处理存在问题")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc() 