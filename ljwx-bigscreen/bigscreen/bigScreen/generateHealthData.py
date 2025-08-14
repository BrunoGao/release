import pandas as pd
import random
import json
from datetime import datetime, timedelta

# 定义时间范围和相关参数
start_date = datetime(2024, 12, 1)
end_date = datetime(2025, 1, 4)
time_delta = timedelta(minutes=1)
latitude_range = (22.518, 22.55)
longitude_range = (114.03, 114.10)
altitude_range = (0, 50)

# 存储数据和 SQL 语句的容器
data = []
sql_statements = []

# 工作时间段
work_hours = [(8, 12), (14, 18)]

# 生成数据
current_date = start_date

while current_date <= end_date:
    # 检查当前时间是否在工作时间段内
    if any(start <= current_date.hour < end for start, end in work_hours):
        # 如果是每天的第一个时间点，清零日累加值
        if current_date.hour == 8 and current_date.minute == 0:
            steps_daily = 0
            distance_daily = 0
            calorie_daily = 0

        heart_rate = random.randint(85, 110)
        blood_oxygen = random.randint(92, 99)
        temperature = round(random.uniform(36.1, 37.2), 1)
        pressure_high = random.randint(110, 140)
        pressure_low = random.randint(70, 90)
        steps_increment = random.randint(50, 200)  # 每分钟步数增长
        distance_increment = round(steps_increment * 0.8 / 1000, 1)  # 每分钟距离增长 (公里)
        calorie_increment = round(random.uniform(1, 5), 1)  # 每分钟卡路里增长

        # 累加每日数据
        steps_daily += steps_increment
        distance_daily = round(distance_daily + distance_increment, 1)  # 确保累计值保留 1 位小数
        calorie_daily = round(calorie_daily + calorie_increment, 1)    # 确保累计值保留 1 位小数

        # 地理位置
        latitude = round(random.uniform(*latitude_range), 6)
        longitude = round(random.uniform(*longitude_range), 6)
        altitude = random.choice([0, round(random.uniform(*altitude_range), 1)])

        # 睡眠数据
        sleep_data = {
            "code": 0,
            "data": [
                {"startTimeStamp": int((current_date - timedelta(hours=8)).timestamp() * 1000),
                 "endTimeStamp": int((current_date - timedelta(hours=6)).timestamp() * 1000),
                 "type": 1},
                {"startTimeStamp": int((current_date - timedelta(hours=6)).timestamp() * 1000),
                 "endTimeStamp": int((current_date - timedelta(hours=1)).timestamp() * 1000),
                 "type": 2}
            ],
            "name": "sleep",
            "type": "history"
        }

        # 每日运动数据
        exercise_daily_data = {
            "strengthTimes": random.randint(200, 500),
            "totalTime": random.randint(6, 10),
        }

        # 生成不同的 device_sn
        for device_sn_suffix in range(1893, 1900):
            device_sn = f"CRFTQ2340900{device_sn_suffix}"

            # 记录数据
            record = {
                "phone_number": f"1{random.randint(3000000000, 3999999999)}",
                "heart_rate": heart_rate,
                "pressure_high": pressure_high,
                "pressure_low": pressure_low,
                "blood_oxygen": blood_oxygen,
                "temperature": temperature,
                "step": steps_daily,
                "timestamp": current_date,
                "user_name": "heguang",
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "device_sn": device_sn,
                "distance": distance_daily,
                "calorie": calorie_daily,
                "sleep_data": json.dumps(sleep_data),
                "exercise_daily_data": json.dumps(exercise_daily_data),
                "is_deleted": 0,
                "create_user": "system",
                "create_user_id": 1,
                "update_user": "system",
                "update_user_id": 1
            }
            data.append(record)

            # 生成 SQL 插入语句
            sql = f"""
            INSERT INTO panis_boot.t_user_health_data 
            (phone_number, heart_rate, pressure_high, pressure_low, blood_oxygen, temperature, step, timestamp, user_name, latitude, longitude, altitude, device_sn, distance, calorie, sleep_data, exercise_daily_data, is_deleted, create_user, create_user_id, update_user, update_user_id) 
            VALUES 
            ('{record["phone_number"]}', {record["heart_rate"]}, {record["pressure_high"]}, {record["pressure_low"]}, {record["blood_oxygen"]}, {record["temperature"]}, {record["step"]}, '{record["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}', '{record["user_name"]}', {record["latitude"]}, {record["longitude"]}, {record["altitude"]}, '{record["device_sn"]}', {record["distance"]}, {record["calorie"]}, '{record["sleep_data"]}', '{record["exercise_daily_data"]}', {record["is_deleted"]}, '{record["create_user"]}', {record["create_user_id"]}, '{record["update_user"]}', {record["update_user_id"]});
            """
            sql_statements.append(sql.strip())

    # 增加时间
    current_date += time_delta

# 将 SQL 插入语句保存到文件
with open("insert_statements.sql", "w") as file:
    file.write("\n".join(sql_statements))

# 创建 DataFrame 用于输出到 Excel
df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")

# 保存到 Excel 文件
df.to_excel("health_data.xlsx", index=False)

print("数据生成成功！SQL 语句保存为 insert_statements.sql，数据保存为 health_data.xlsx")