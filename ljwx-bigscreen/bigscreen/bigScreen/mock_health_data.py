import random
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import math
import os

config = {
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'host': os.getenv('MYSQL_HOST', 'mysql' if os.getenv('IS_DOCKER', 'false').lower() == 'true' else '127.0.0.1'),
    'database': os.getenv('MYSQL_DATABASE', 'lj-06'),
    'raise_on_warnings': True
}

def decimal_round(value, places=6):
    """将浮点数转换为指定精度的Decimal"""
    try:
        if isinstance(value, (int, float)):
            value = str(value)
        return Decimal(value).quantize(Decimal('0.' + '0' * places), rounding=ROUND_HALF_UP)
    except:
        return Decimal('0.000000')

class MovementSimulator:
    def __init__(self, start_lat, start_lng, route_type="circle", department=""):
        # 确保初始坐标在有效范围内
        self.current_lat = max(min(float(start_lat), 90.0), -90.0)
        self.current_lng = max(min(float(start_lng), 180.0), -180.0)
        self.route_type = route_type
        self.department = department
        self.angle = 0
        self.radius = 0.0003
        self.step = 0
        
        # 更新预定义路线的坐标，确保在有效范围内
        self.predefined_routes = {
            "开采队": [
                (22.543100, 114.045000),
                (22.543300, 114.045200),
                (22.543500, 114.045400),
                (22.543300, 114.045200),
                (22.543100, 114.045000)
            ],
            "通风队": [
                (22.544000, 114.046000),
                (22.544200, 114.046200),
                (22.544400, 114.046000),
                (22.544200, 114.045800),
                (22.544000, 114.046000)
            ],
            "安全监察队": [
                (22.545000, 114.047000),
                (22.545500, 114.047500),
                (22.546000, 114.047000),
                (22.545500, 114.046500),
                (22.545000, 114.047000)
            ]
        }
        
        self.current_route = self.predefined_routes[department] if department in self.predefined_routes else self.predefined_routes["开采队"]
        self.route_index = 0
        self.progress = 0.0

    def get_next_position(self):
        try:
            new_lat = float(self.current_lat)
            new_lng = float(self.current_lng)

            if len(self.current_route) > 1:
                current_point = self.current_route[self.route_index]
                next_point = self.current_route[(self.route_index + 1) % len(self.current_route)]
                
                self.progress += 0.05
                if self.progress >= 1.0:
                    self.progress = 0.0
                    self.route_index = (self.route_index + 1) % len(self.current_route)
                
                new_lat = current_point[0] + (next_point[0] - current_point[0]) * self.progress
                new_lng = current_point[1] + (next_point[1] - current_point[1]) * self.progress

            # 确保坐标在有效范围内
            new_lat = max(min(new_lat, 90.0), -90.0)
            new_lng = max(min(new_lng, 180.0), -180.0)
            
            self.current_lat = new_lat
            self.current_lng = new_lng
            
            base_speed = 1.2
            if self.department == "安全监察队":
                base_speed = 1.5
            elif self.department == "开采队":
                base_speed = 1.0
                
            speed = float(random.uniform(base_speed, base_speed + 0.3))
            distance = speed * 5 / 1000
            
            return {
                'latitude': decimal_round(str(new_lat)),
                'longitude': decimal_round(str(new_lng)),
                'altitude': decimal_round(str(random.uniform(10, 100))),
                'distance': decimal_round(str(distance)),
                'speed': decimal_round(str(speed))
            }
        except Exception as e:
            print(f"Error in get_next_position: {e}")
            return {
                'latitude': decimal_round('22.543100'),
                'longitude': decimal_round('114.045000'),
                'altitude': decimal_round('10.0'),
                'distance': decimal_round('0.001'),
                'speed': decimal_round('1.2')
            }

def generate_health_data(movement_data, department):
    try:
        speed = float(movement_data['speed'])
        base_heart_rate = 60
        if department == "开采队":
            base_heart_rate = 75
        elif department == "通风队":
            base_heart_rate = 70
        
        heart_rate = random.randint(base_heart_rate, base_heart_rate + int(speed * 10))
        
        return {
            'heart_rate': heart_rate,
            'pressure_high': random.randint(90, 140),
            'pressure_low': random.randint(60, 90),
            'blood_oxygen': random.randint(95, 100),
            'temperature': decimal_round(str(random.uniform(36.3, 37.2))),
            'stress': random.randint(1, 100),
            'step': int(speed * 60),
            'distance': movement_data['distance'],
            'calorie': decimal_round(str(speed * 0.8)),
            'latitude': movement_data['latitude'],
            'longitude': movement_data['longitude'],
            'altitude': movement_data['altitude']
        }
    except Exception as e:
        print(f"Error in generate_health_data: {e}")
        return {
            'heart_rate': 70,
            'pressure_high': 120,
            'pressure_low': 80,
            'blood_oxygen': 98,
            'temperature': decimal_round('36.5'),
            'stress': 50,
            'step': 100,
            'distance': decimal_round('0.001'),
            'calorie': decimal_round('1.0'),
            'latitude': movement_data.get('latitude', decimal_round('22.543100')),
            'longitude': movement_data.get('longitude', decimal_round('114.045000')),
            'altitude': movement_data.get('altitude', decimal_round('10.0'))
        }

users = [
    {
        'phone_number': '18944444444', 
        'user_name': 'user7', 
        'device_sn': 'A5GTQ24603000537',
        'department': '煤矿集团总部',
        'simulator': MovementSimulator(22.543100, 114.045000, "predefined", "煤矿集团总部")
    },
    {
        'phone_number': '13888888888', 
        'user_name': 'demo', 
        'device_sn': 'CRFTQ23409001890',
        'department': '开采队',
        'simulator': MovementSimulator(22.544000, 114.046000, "predefined", "开采队")
    },
    {
        'phone_number': '18115485994', 
        'user_name': 'test1', 
        'device_sn': 'A5GTQ24A17000135',
        'department': '煤矿集团总部',
        'simulator': MovementSimulator(22.545000, 114.047000, "predefined", "煤矿集团总部")
    },
    {
        'phone_number': '18944444444', 
        'user_name': 'user6', 
        'device_sn': 'A5GTQ24B26000732',
        'department': '煤矿集团总部',
        'simulator': MovementSimulator(22.544000, 114.046000, "predefined", "煤矿集团总部")
    },
    {
        'phone_number': '18966666666', 
        'user_name': 'admin1', 
        'device_sn': 'A5GTQ24919001193',
        'department': '煤矿集团总部',
        'simulator': MovementSimulator(22.544000, 114.046000, "predefined", "煤矿集团总部")
    }
]

def main():
    try:
        db = mysql.connector.connect(**config)
        cursor = db.cursor()
        
        # 获取所有设备SN
        device_sns = [user['device_sn'] for user in users]
        
        # 计算时间范围：从30天前到现在
        now = datetime.now()
        start_time = now - timedelta(days=90)
        
        # 删除这个时间范围内的旧数据
        delete_sql = f"""
        DELETE FROM t_user_health_data 
        WHERE device_sn IN ({','.join(['%s'] * len(device_sns))})
        AND timestamp BETWEEN %s AND %s
        """
        cursor.execute(delete_sql, device_sns + [start_time, now])
        db.commit()
        print(f"Deleted {cursor.rowcount} records")

        # 准备批量插入
        insert_sql = """
            INSERT INTO t_user_health_data (
                phone_number, heart_rate, pressure_high, pressure_low, 
                blood_oxygen, temperature, stress, step, timestamp, 
                user_name, latitude, longitude, altitude, device_sn, 
                distance, calorie, create_time, update_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        batch_size = 100  # 减小批量大小以便于定位错误
        insert_data = []
        total_records = 0
        
        print(f"Starting data generation from {start_time} to {now}")
        
        # 生成所有时间点的数据
        current_time = start_time
        while current_time <= now:
            hour = current_time.hour
            
            for user in users:
                try:
                    # 获取位置数据
                    movement_data = user['simulator'].get_next_position()
                    
                    # 确保坐标值格式正确
                    lat = float(movement_data['latitude'])
                    lng = float(movement_data['longitude'])
                    
                    # 限制坐标范围
                    lat = max(min(lat, 90.0), -90.0)
                    lng = max(min(lng, 180.0), -180.0)
                    
                    # 计算当天已过的分钟数
                    minutes_passed = (current_time.hour * 60 + current_time.minute)
                    total_minutes = 24 * 60
                    step_total = 20000
                    step_now = int(step_total * minutes_passed / total_minutes + random.randint(-10,10))
                    step_now = max(step_now, 0)
                    distance_now = round(step_now * 0.7 + random.uniform(-5,5), 1)
                    calorie_now = round(step_now * 0.04 + random.uniform(-0.5,0.5), 1)
                    
                    # 生成健康数据
                    health_data = generate_health_data(movement_data, user['department'])
                    health_data['step'] = step_now
                    health_data['distance'] = distance_now
                    health_data['calorie'] = calorie_now
                    
                    # 根据时间段调整数据
                    if 0 <= hour < 6:
                        health_data['heart_rate'] = random.randint(50, 65)
                        health_data['blood_oxygen'] = random.randint(95, 98)
                        health_data['step'] = 0
                        health_data['calorie'] = decimal_round('0')
                    
                    data = (
                        user['phone_number'],
                        health_data['heart_rate'],
                        health_data['pressure_high'],
                        health_data['pressure_low'],
                        health_data['blood_oxygen'],
                        float(health_data['temperature']),  # 确保温度是浮点数
                        health_data['stress'],
                        health_data['step'],
                        current_time,
                        user['user_name'],
                        float(lat),  # 确保使用浮点数
                        float(lng),  # 确保使用浮点数
                        float(health_data['altitude']),  # 确保使用浮点数
                        user['device_sn'],
                        float(health_data['distance']),  # 确保使用浮点数
                        float(health_data['calorie']),   # 确保使用浮点数
                        current_time,
                        current_time
                    )
                    
                    insert_data.append(data)
                    total_records += 1

                    # 批量提交数据
                    if len(insert_data) >= batch_size:
                        try:
                            cursor.executemany(insert_sql, insert_data)
                            db.commit()
                            print(f"Inserted {len(insert_data)} records, total: {total_records}, time: {current_time}")
                            insert_data = []
                        except mysql.connector.Error as err:
                            print(f"Error inserting batch: {err}")
                            print(f"First record in batch: {insert_data[0]}")
                            db.rollback()
                            insert_data = []
                            
                except Exception as e:
                    print(f"Error generating data for user {user['user_name']}: {e}")
                    continue

            current_time += timedelta(minutes=5)

        # 提交剩余的数据
        if insert_data:
            try:
                cursor.executemany(insert_sql, insert_data)
                db.commit()
                print(f"Inserted final {len(insert_data)} records")
            except mysql.connector.Error as err:
                print(f"Error inserting final batch: {err}")
                db.rollback()

        print(f"Total records inserted: {total_records}")

    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
        print("Database connection closed")

if __name__ == "__main__":
    main() 