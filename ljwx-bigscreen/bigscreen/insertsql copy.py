import random
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP

config = {
    'user': 'root',
    'password': '123456',
    'host': '192.168.1.83',
    'database': 'lj-03',
    'raise_on_warnings': True
}

def generate_timestamp(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, 0)

def decimal_round(value, places=6):
    """将浮点数转换为指定精度的Decimal"""
    return Decimal(str(value)).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)

def generate_health_data():
    return {
        'heart_rate': random.randint(60, 100),  # 正常心率范围
        'pressure_high': random.randint(90, 140),  # 收缩压范围
        'pressure_low': random.randint(60, 90),  # 舒张压范围
        'blood_oxygen': random.randint(95, 100),  # 血氧范围
        'temperature': decimal_round(random.uniform(36.3, 37.2), 2),  # 体温范围
        'stress': random.randint(1, 100),  # 压力指数
        'step': random.randint(0, 100),  # 每分钟步数
        'distance': decimal_round(random.uniform(0, 0.1), 3),  # 每分钟距离（公里）
        'calorie': decimal_round(random.uniform(0, 5), 2),  # 每分钟消耗卡路里
        'latitude': decimal_round(random.uniform(22.543100, 22.556000)),
        'longitude': decimal_round(random.uniform(114.045000, 114.060000)),
        'altitude': decimal_round(random.uniform(10, 100), 2)
    }

db = mysql.connector.connect(**config)
cursor = db.cursor()

sql_template = """
INSERT INTO t_user_health_data (
    phone_number, heart_rate, pressure_high, pressure_low, 
    blood_oxygen, temperature, stress, step, timestamp, 
    user_name, latitude, longitude, altitude, device_sn, 
    distance, calorie, create_time, update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""

# 测试用户数据
users = [
    {'phone_number': '18911111111', 'user_name': 'user7', 'device_sn': 'A5GTQ24603000537'},
    {'phone_number': '18922222222', 'user_name': 'user10', 'device_sn': 'CRFTQ23409001890'}
]

try:
    # 生成过去24小时的数据
    now = datetime.now()
    start_time = now - timedelta(days=1)
    
    # 每分钟插入一次数据
    current_time = start_time
    while current_time <= now:
        for user in users:
            health_data = generate_health_data()
            
            # 准备插入数据
            data = (
                user['phone_number'],
                health_data['heart_rate'],
                health_data['pressure_high'],
                health_data['pressure_low'],
                health_data['blood_oxygen'],
                health_data['temperature'],
                health_data['stress'],
                health_data['step'],
                current_time,
                user['user_name'],
                health_data['latitude'],
                health_data['longitude'],
                health_data['altitude'],
                user['device_sn'],
                health_data['distance'],
                health_data['calorie'],
                current_time,  # create_time
                current_time   # update_time
            )
            
            # 执行插入
            cursor.execute(sql_template, data)
        
        # 提交每分钟的数据
        db.commit()
        current_time += timedelta(seconds=5)
        if current_time.minute == 0:  # 每小时打印一次进度
            print(f"Inserted data for {current_time}")

except Exception as e:
    print(f"Error occurred: {e}")
    db.rollback()

finally:
    cursor.close()
    db.close()
    print("Data insertion completed")
