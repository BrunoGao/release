#!/usr/bin/env python3
"""模拟健康数据上传脚本"""
import requests,json,random,time,sys,os
from datetime import datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
import mysql.connector

# 配置
API_URL = "http://localhost:5001/upload_health_data"
BASELINE_API = "http://localhost:5001/api/baseline/generate"
DB_CONFIG = {'host':'127.0.0.1','user':'root','password':'123456','database':'lj-06','port':3306}

def get_all_users():
    """获取所有用户的device_sn"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id,user_name,device_sn FROM sys_user WHERE device_sn IS NOT NULL AND device_sn != '' AND device_sn != '-' AND is_deleted = 0")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        print(f"获取到{len(users)}个用户")
        return users
    except Exception as e:
        print(f"获取用户失败: {e}")
        return []

def generate_health_data(device_sn, timestamp):
    """生成模拟健康数据"""
    return {
        'data': {
            'id': device_sn,
            'upload_method': 'wifi',
            'heart_rate': random.randint(60, 120),
            'blood_oxygen': random.randint(95, 100),
            'body_temperature': f"{random.uniform(36.0, 37.5):.1f}",
            'blood_pressure_systolic': random.randint(90, 140),
            'blood_pressure_diastolic': random.randint(60, 90),
            'step': random.randint(500, 2000),
            'distance': f"{random.uniform(300, 1500):.1f}",
            'calorie': f"{random.uniform(20000, 60000):.1f}",
            'latitude': f"{random.uniform(22.5, 22.6):.14f}",
            'longitude': f"{random.uniform(114.0, 114.1):.14f}",
            'altitude': '0.0',
            'stress': random.randint(20, 80),
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'sleepData': '{"code":0,"data":[{"endTimeStamp":1747440420000,"startTimeStamp":1747418280000,"type":2}],"name":"sleep","type":"history"}',
            'exerciseDailyData': '{"code":0,"data":[{"strengthTimes":2,"totalTime":5}],"name":"daily","type":"history"}',
            'exerciseWeekData': 'null',
            'scientificSleepData': 'null',
            'workoutData': '{"code":0,"data":[],"name":"workout","type":"history"}'
        }
    }

def upload_data(data):
    """上传单条数据"""
    try:
        response = requests.post(API_URL, json=data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"上传失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"上传异常: {e}")
        return False

def simulate_user_data(user, start_date, end_date):
    """模拟单个用户的数据"""
    device_sn = user['device_sn']
    user_name = user['user_name']
    success_count = 0
    total_count = 0
    
    current_time = start_date
    while current_time <= end_date:
        # 每5分钟生成一条数据
        data = generate_health_data(device_sn, current_time)
        if upload_data(data):
            success_count += 1
        total_count += 1
        current_time += timedelta(minutes=5)
        
        # 每100条数据休息一下
        if total_count % 100 == 0:
            print(f"用户{user_name}({device_sn}): {success_count}/{total_count}")
            time.sleep(0.1)
    
    print(f"用户{user_name}完成: {success_count}/{total_count}")
    return success_count, total_count

def generate_baseline():
    """生成基线数据"""
    try:
        print("开始生成基线数据...")
        response = requests.post(BASELINE_API, json={}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"基线生成成功: {result}")
            return True
        else:
            print(f"基线生成失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"基线生成异常: {e}")
        return False

def main():
    """主函数"""
    print("开始模拟健康数据上传...")
    
    # 获取所有用户
    users = get_all_users()
    if not users:
        print("没有找到用户数据")
        return
    
    # 设置时间范围（过去一个月）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    print(f"时间范围: {start_date} 到 {end_date}")
    print(f"用户数量: {len(users)}")
    
    # 限制用户数量避免过载
    max_users = 5  # 限制最多5个用户
    if len(users) > max_users:
        users = users[:max_users]
        print(f"限制用户数量为{max_users}个")
    
    total_success = 0
    total_count = 0
    
    # 使用线程池并发处理
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for user in users:
            future = executor.submit(simulate_user_data, user, start_date, end_date)
            futures.append(future)
        
        # 等待所有任务完成
        for future in futures:
            success, count = future.result()
            total_success += success
            total_count += count
    
    print(f"\n数据上传完成: {total_success}/{total_count}")
    
    # 生成基线
    if total_success > 0:
        print("\n开始生成基线数据...")
        # 生成多个日期的基线
        for i in range(5):  # 生成最近5天的基线
            target_date = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')
            try:
                response = requests.post(BASELINE_API, json={'target_date': target_date}, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    print(f"基线生成成功({target_date}): {result}")
                else:
                    print(f"基线生成失败({target_date}): {response.status_code}")
            except Exception as e:
                print(f"基线生成异常({target_date}): {e}")
            time.sleep(1)
    
    print("\n模拟完成!")

if __name__ == "__main__":
    main() 