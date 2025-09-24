#!/usr/bin/env python3
"""
测试运动数据上传脚本
"""

import json
import requests
import time
from datetime import datetime, timedelta
from upload_monthly_health_data import HealthDataUploader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    uploader = HealthDataUploader()
    
    # 生成一条包含运动数据的测试记录
    test_time = datetime(2025, 9, 23, 14, 30, 0)  # 下午2:30，确保生成运动数据
    health_data = uploader.generate_realistic_health_data(test_time)
    
    print("🏃 测试运动数据上传")
    print("=" * 50)
    print(f"时间: {health_data['timestamp']}")
    print(f"设备: {health_data['deviceSn']}")
    print(f"用户: {health_data['userId']}")
    
    # 检查运动数据
    if health_data.get('exerciseDailyData'):
        exercise_data = json.loads(health_data['exerciseDailyData'])
        print(f"✅ 日常运动数据: {len(exercise_data['data'])} 条记录")
        print(f"   示例: {exercise_data['data'][0] if exercise_data['data'] else 'None'}")
    
    if health_data.get('exerciseWeekData'):
        weekly_data = json.loads(health_data['exerciseWeekData'])
        print(f"✅ 周运动数据: {len(weekly_data['data'])} 条记录")
        print(f"   示例: {weekly_data['data'][0] if weekly_data['data'] else 'None'}")
        
    if health_data.get('workoutData'):
        workout_data = json.loads(health_data['workoutData'])
        print(f"✅ 锻炼数据: {len(workout_data['data'])} 条记录")
        print(f"   示例: {workout_data['data'][0] if workout_data['data'] else 'None'}")
    
    # 上传数据
    print("\n🚀 开始上传...")
    success = uploader.upload_health_data(health_data)
    
    if success:
        print("✅ 上传成功！")
        print("\n💡 请检查数据库查询结果，运动数据应该能正常显示了")
    else:
        print("❌ 上传失败")

if __name__ == "__main__":
    main()