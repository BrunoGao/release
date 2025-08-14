#!/usr/bin/env python3
"""测试批量插入和查询接口"""
import os
os.environ['IS_DOCKER'] = 'false'
import requests
import json
import time
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_uploaded_data():
    """检查已上传的数据"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("📊 检查已上传的数据...")
            
            # 检查设备CRFTQ23409001890的数据
            cursor.execute("""
                SELECT id, device_sn, user_id, org_id, heart_rate, blood_oxygen, 
                       pressure_high, pressure_low, timestamp, create_time
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                ORDER BY create_time DESC 
                LIMIT 5
            """)
            
            data = cursor.fetchall()
            if data:
                print(f"✅ 设备CRFTQ23409001890数据 ({len(data)}条):")
                for row in data:
                    print(f"  ID:{row[0]} | 用户ID:{row[2]} | 组织ID:{row[3]} | 心率:{row[4]} | 血氧:{row[5]} | 血压:{row[6]}/{row[7]} | 时间:{row[8]} | 创建:{row[9]}")
                
                # 返回第一条数据的用户ID和组织ID
                return row[2], row[3]
            else:
                print("❌ 没有找到设备CRFTQ23409001890的数据")
                return None, None
                
    except Exception as e:
        print(f"❌ 检查数据失败: {e}")
        return None, None
    finally:
        conn.close()

def test_batch_upload():
    """测试批量上传接口"""
    print("\n🧪 测试批量上传接口...")
    
    url = 'http://localhost:5001/upload_health_data'
    
    # 批量测试数据
    batch_data = {
        'data': [
            {
                'deviceSn': 'CRFTQ23409001890',
                'heart_rate': 72,
                'blood_oxygen': 97,
                'body_temperature': '36.8',
                'blood_pressure_systolic': 115,
                'blood_pressure_diastolic': 78,
                'step': 1200,
                'distance': '800.0',
                'calorie': '150.0',
                'latitude': '22.540363',
                'longitude': '114.015181',
                'stress': 25,
                'upload_method': 'wifi',
                'sleepData': '{"code":0,"data":[{"duration":420}],"name":"sleep","type":"history"}',
                'exerciseDailyData': '{"steps":1200,"calories":150}',
                'workoutData': '{"type":"running","duration":30}',
                'timestamp': '2025-05-27 18:00:00'
            },
            {
                'deviceSn': 'CRFTQ23409001890',
                'heart_rate': 68,
                'blood_oxygen': 99,
                'body_temperature': '36.6',
                'blood_pressure_systolic': 110,
                'blood_pressure_diastolic': 75,
                'step': 1500,
                'distance': '1000.0',
                'calorie': '180.0',
                'latitude': '22.541000',
                'longitude': '114.016000',
                'stress': 20,
                'upload_method': 'wifi',
                'sleepData': '{"code":0,"data":[{"duration":450}],"name":"sleep","type":"history"}',
                'exerciseDailyData': '{"steps":1500,"calories":180}',
                'workoutData': '{"type":"walking","duration":45}',
                'timestamp': '2025-05-27 19:00:00'
            }
        ]
    }
    
    try:
        response = requests.post(url, json=batch_data, timeout=10)
        print(f"📊 批量上传响应: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("✅ 批量上传成功!")
                return True
            else:
                print(f"❌ 批量上传失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 批量上传异常: {e}")
        return False

def test_query_interface(user_id, org_id):
    """测试查询接口"""
    print(f"\n🔍 测试查询接口 (用户ID:{user_id}, 组织ID:{org_id})...")
    
    # 测试不同的查询参数
    test_cases = [
        {
            'name': '按组织ID查询',
            'url': f'http://localhost:5001/get_all_health_data_by_orgIdAndUserId?orgId={org_id}&startDate=2025-02-01&endDate=2025-05-28'
        },
        {
            'name': '按用户ID查询',
            'url': f'http://localhost:5001/get_all_health_data_by_orgIdAndUserId?userId={user_id}&startDate=2025-02-01&endDate=2025-05-28'
        },
        {
            'name': '按组织ID和用户ID查询',
            'url': f'http://localhost:5001/get_all_health_data_by_orgIdAndUserId?orgId={org_id}&userId={user_id}&startDate=2025-02-01&endDate=2025-05-28'
        },
        {
            'name': '今日数据查询',
            'url': f'http://localhost:5001/get_all_health_data_by_orgIdAndUserId?orgId={org_id}&startDate=2025-05-27&endDate=2025-05-27'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}:")
        print(f"URL: {test_case['url']}")
        
        try:
            response = requests.get(test_case['url'], timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        health_data = result.get('data', {}).get('healthData', [])
                        data_count = len(health_data)
                        print(f"✅ 查询成功: 返回{data_count}条数据")
                        
                        if data_count > 0:
                            # 显示前几条数据
                            health_data = result.get('data', {}).get('healthData', [])
                            sample_count = min(3, len(health_data))
                            for i in range(sample_count):
                                item = health_data[i]
                                print(f"  数据{i+1}: 心率:{item.get('heartRate')} 血氧:{item.get('bloodOxygen')} 时间:{item.get('timestamp')}")
                        
                        # 检查数据源
                        statistics = result.get('data', {}).get('statistics', {})
                        data_source = statistics.get('dataSource', 'unknown')
                        print(f"数据源: {data_source}")
                    else:
                        print(f"❌ 查询失败: {result.get('error', '未知错误')}")
                except json.JSONDecodeError:
                    print(f"❌ JSON解析失败: {response.text[:200]}...")
            else:
                print(f"❌ HTTP错误: {response.status_code} - {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ 查询异常: {e}")

def check_database_after_batch():
    """检查批量插入后的数据库状态"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("\n📊 检查批量插入后的数据库状态...")
            
            # 检查最近插入的数据
            cursor.execute("""
                SELECT COUNT(*) as total_count
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                AND create_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            
            total_count = cursor.fetchone()[0]
            print(f"最近1小时插入数据: {total_count}条")
            
            # 检查今日数据
            cursor.execute("""
                SELECT COUNT(*) as today_count
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
                AND DATE(timestamp) = '2025-05-27'
            """)
            
            today_count = cursor.fetchone()[0]
            print(f"今日数据总数: {today_count}条")
            
            # 检查数据时间范围
            cursor.execute("""
                SELECT MIN(timestamp) as min_time, MAX(timestamp) as max_time
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890'
            """)
            
            time_range = cursor.fetchone()
            print(f"数据时间范围: {time_range[0]} 到 {time_range[1]}")
            
            return total_count, today_count
            
    except Exception as e:
        print(f"❌ 检查数据库状态失败: {e}")
        return 0, 0
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 开始测试批量插入和查询接口...")
    print("=" * 80)
    
    # 1. 检查现有数据
    user_id, org_id = check_uploaded_data()
    
    if not user_id or not org_id:
        print("❌ 没有找到测试数据，请先运行上传测试")
        exit(1)
    
    # 2. 测试批量上传
    batch_success = test_batch_upload()
    
    if batch_success:
        print("\n⏳ 等待5秒让批处理器处理数据...")
        time.sleep(5)
        
        # 3. 检查批量插入后的状态
        total_count, today_count = check_database_after_batch()
    
    # 4. 测试查询接口
    test_query_interface(user_id, org_id)
    
    print("\n" + "=" * 80)
    print("📋 测试完成")
    
    if batch_success and today_count > 0:
        print("✅ 批量插入和查询功能正常")
    else:
        print("❌ 存在问题需要进一步调试") 