import random
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import time
import math

config = {
    'user': 'root',
    'password': '123456',
    'host': '127.0.0.1',
    'database': 'lj-03',
    'raise_on_warnings': True
}

def delete_today_data(cursor, device_sns):
    """删除当天的数据"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # 构建设备SN的占位符
    placeholders = ','.join(['%s'] * len(device_sns))
    
    delete_sql = f"""
    DELETE FROM t_user_health_data 
    WHERE device_sn IN ({placeholders}) 
    AND DATE(timestamp) = %s
    """
    
    # 准备参数：设备SN列表 + 日期
    params = device_sns + [today]
    
    # 执行删除
    cursor.execute(delete_sql, params)
    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} records for today")

def decimal_round(value, places=6):
    """将浮点数转换为指定精度的Decimal"""
    try:
        # 确保输入值是字符串或数字
        if isinstance(value, (int, float)):
            value = str(value)
        return Decimal(value).quantize(Decimal('0.' + '0' * places), rounding=ROUND_HALF_UP)
    except (TypeError, ValueError, decimal.InvalidOperation):
        # 如果转换失败，返回0
        return Decimal('0.' + '0' * places)

class MovementSimulator:
    def __init__(self, start_lat, start_lng, route_type="circle", department=""):
        self.current_lat = float(start_lat)
        self.current_lng = float(start_lng)
        self.route_type = route_type
        self.department = department
        self.angle = 0
        self.radius = 0.0003  # 约30米
        self.step = 0
        
        # 为不同部门设置不同的路线
        self.predefined_routes = {
            "开采队": [
                # 模拟采矿作业路线，较小范围往返移动
                (22.543100, 114.045000),
                (22.543300, 114.045200),
                (22.543500, 114.045400),
                (22.543300, 114.045200),
                (22.543100, 114.045000)
            ],
            "通风队": [
                # 模拟通风检查路线，环形路线
                (22.544000, 114.046000),
                (22.544200, 114.046200),
                (22.544400, 114.046000),
                (22.544200, 114.045800),
                (22.544000, 114.046000)
            ],
            "安全监察队": [
                # 模拟巡检路线，较大范围移动
                (22.545000, 114.047000),
                (22.545500, 114.047500),
                (22.546000, 114.047000),
                (22.545500, 114.046500),
                (22.545000, 114.047000)
            ]
        }
        
        # 根据部门选择路线
        if department in self.predefined_routes:
            self.current_route = self.predefined_routes[department]
        else:
            # 默认路线
            self.current_route = self.predefined_routes["开采队"]
        
        self.route_index = 0
        self.progress = 0.0

    def get_next_position(self):
        try:
            new_lat = float(self.current_lat)
            new_lng = float(self.current_lng)

            if len(self.current_route) > 1:
                current_point = self.current_route[self.route_index]
                next_point = self.current_route[(self.route_index + 1) % len(self.current_route)]
                
                # 计算两点之间的平滑移动
                self.progress += 0.05  # 降低移动速度
                if self.progress >= 1.0:
                    self.progress = 0.0
                    self.route_index = (self.route_index + 1) % len(self.current_route)
                
                # 线性插值计算当前位置
                new_lat = current_point[0] + (next_point[0] - current_point[0]) * self.progress
                new_lng = current_point[1] + (next_point[1] - current_point[1]) * self.progress

            self.current_lat = new_lat
            self.current_lng = new_lng
            
            # 根据部门调整移动速度
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
        # 根据部门调整基础心率和其他生理指标
        base_heart_rate = 60
        if department == "开采队":
            base_heart_rate = 75  # 体力劳动强度大
        elif department == "通风队":
            base_heart_rate = 70  # 中等强度
        
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

# 测试用户数据
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
        
        # 先删除当天数据
        delete_today_data(cursor, device_sns)
        db.commit()
        print("Successfully deleted today's data")
        
        # 生成1分钟的新数据
        now = datetime.now()
        end_time = now + timedelta(minutes=1)
        
        # 每5秒插入一次数据
        current_time = now
        while current_time <= end_time:
            for user in users:
                movement_data = user['simulator'].get_next_position()
                health_data = generate_health_data(movement_data, user['department'])
                
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
                
                cursor.execute("""
                    INSERT INTO t_user_health_data (
                        phone_number, heart_rate, pressure_high, pressure_low, 
                        blood_oxygen, temperature, stress, step, timestamp, 
                        user_name, latitude, longitude, altitude, device_sn, 
                        distance, calorie, create_time, update_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, data)
            
            db.commit()
            print(f"Inserted data at {current_time.strftime('%H:%M:%S')}")
            
            current_time += timedelta(seconds=5)
            time_to_wait = (current_time - datetime.now()).total_seconds()
            if time_to_wait > 0:
                time.sleep(time_to_wait)

    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()
        print("Data insertion completed")

if __name__ == "__main__":
    main()
