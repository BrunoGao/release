import random
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import math

config = {
    'user': 'root',
    'password': '123456',
    'host': '127.0.0.1',
    'database': 'lj-06',
    'raise_on_warnings': True
}

def decimal_round(value, places=6):
    """将浮点数转换为指定精度的Decimal"""
    try:
        if isinstance(value, (int, float)):
            value = str(value)
        return Decimal(value).quantize(Decimal('0.' + '0' * places), rounding=ROUND_HALF_UP)
    except:
        return Decimal('0.' + '0' * places)

class MovementSimulator:
    def __init__(self, start_lat, start_lng, route_type="circle", department=""):
        self.current_lat = float(start_lat)
        self.current_lng = float(start_lng)
        self.route_type = route_type
        self.department = department
        self.angle = 0
        self.radius = 0.0003
        self.step = 0
        
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
        'phone_number': '18911111111', 
        'user_name': '张三', 
        'device_sn': 'A5GTQ24603000537',
        'department': '开采队',
        'simulator': MovementSimulator(22.543100, 114.045000, "predefined", "开采队")
    },
    {
        'phone_number': '18922222222', 
        'user_name': '李四', 
        'device_sn': 'CRFTQ23409001890',
        'department': '通风队',
        'simulator': MovementSimulator(22.544000, 114.046000, "predefined", "通风队")
    },
    {
        'phone_number': '18933333333', 
        'user_name': '王五', 
        'device_sn': 'A5GTQ24A17000135',
        'department': '安全监察队',
        'simulator': MovementSimulator(22.545000, 114.047000, "predefined", "安全监察队")
    },
    {
        'phone_number': '18944444444', 
        'user_name': '赵六', 
        'device_sn': 'A5GTQ24A17000177',
        'department': '通风队',
        'simulator': MovementSimulator(22.544000, 114.046000, "predefined", "通风队")
    }
]

def main():
    try:
        db = mysql.connector.connect(**config)
        cursor = db.cursor()
        
        # 获取所有设备SN
        device_sns = [user['device_sn'] for user in users]
        
        # 计算时间范围：从3天前到现在
        now = datetime.now()
        start_time = now - timedelta(days=3)
        
        # 删除这个时间范围内的旧数据
        delete_sql = f"""
        DELETE FROM t_user_health_data 
        WHERE device_sn IN ({','.join(['%s'] * len(device_sns))})
        AND timestamp BETWEEN %s AND %s
        """
        cursor.execute(delete_sql, device_sns + [start_time, now])
        db.commit()
        print(f"Deleted {cursor.rowcount} records from the past 3 days")

        # 准备批量插入
        insert_sql = """
            INSERT INTO t_user_health_data (
                phone_number, heart_rate, pressure_high, pressure_low, 
                blood_oxygen, temperature, stress, step, timestamp, 
                user_name, latitude, longitude, altitude, device_sn, 
                distance, calorie, create_time, update_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        batch_size = 1000
        insert_data = []
        total_records = 0
        
        print(f"Starting data generation from {start_time} to {now}")
        
        # 生成所有时间点的数据
        current_time = start_time
        while current_time <= now:
            hour = current_time.hour
            
            for user in users:
                # 模拟不同时间段的活动状态
                if 0 <= hour < 6:
                    # 夜间休息时段
                    movement_data = {
                        'latitude': user['simulator'].current_lat,
                        'longitude': user['simulator'].current_lng,
                        'altitude': decimal_round(str(random.uniform(10, 100))),
                        'distance': decimal_round('0'),
                        'speed': decimal_round('0')
                    }
                elif 6 <= hour < 8 or 17 <= hour < 19:
                    # 早晚通勤时段
                    movement_data = user['simulator'].get_next_position()
                    movement_data['speed'] = decimal_round(str(float(movement_data['speed']) * 1.5))
                else:
                    # 正常工作时段
                    movement_data = user['simulator'].get_next_position()

                health_data = generate_health_data(movement_data, user['department'])
                
                # 根据时间段调整健康数据
                if 0 <= hour < 6:
                    # 睡眠时段的生理指标
                    health_data['heart_rate'] = random.randint(50, 65)
                    health_data['blood_oxygen'] = random.randint(95, 98)
                    health_data['step'] = 0
                    health_data['calorie'] = decimal_round('0')
                elif 6 <= hour < 8 or 17 <= hour < 19:
                    # 通勤时段的生理指标
                    health_data['heart_rate'] = random.randint(80, 100)
                    health_data['step'] = int(float(health_data['step']) * 1.5)
                    health_data['calorie'] = decimal_round(str(float(health_data['calorie']) * 1.5))

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
                    current_time,
                    current_time
                )
                insert_data.append(data)
                total_records += 1

                # 批量提交数据
                if len(insert_data) >= batch_size:
                    cursor.executemany(insert_sql, insert_data)
                    db.commit()
                    print(f"Inserted {len(insert_data)} records, total: {total_records}, current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    insert_data = []

            current_time += timedelta(seconds=5)

        # 提交剩余的数据
        if insert_data:
            cursor.executemany(insert_sql, insert_data)
            db.commit()
            print(f"Inserted final {len(insert_data)} records")

        print(f"Total records inserted: {total_records}")
        print(f"Data generation completed from {start_time} to {now}")

    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()
        print("Data insertion completed")

if __name__ == "__main__":
    main()