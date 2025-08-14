from random import uniform
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask import request, jsonify
from .models import db, UserAlert, CustomerConfig,DeviceMessage, UserInfo, HealthDataConfig, DeviceInfo, AlertInfo, AlertLog
from datetime import datetime, timedelta
import random
import mysql.connector
import pymysql.cursors
from redis import Redis
import requests  # 用于发送HTTP请求
import json
import threading
import time
from flask_socketio import SocketIO, emit
import re
import os
from decimal import Decimal
from .redis_helper import RedisHelper

app = Flask(__name__, static_folder='../static')
socketio = SocketIO(app, cors_allowed_origins="*") 
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:aV5mV7kQ@localhost:3306/hg_health'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:aV5mV7kQ%21%40%23@localhost:3306/panis_boot'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'panis_boot',
    'raise_on_warnings': True
}

# Initialize RedisHelper
redis_helper = RedisHelper()

app_id = 'wx10dcc9f0235e1d77'
app_secret = 'b7e9088f3f5fe18a9cfb990c641138b3'
# WeChat API configuration
WECHAT_API_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}"
WECHAT_ACCESS_TOKEN = "84__0GoGXHi168Njqn5lusnGWqaDatlAL5b3Exi_oxD6ChSO9gvogZovkb7Yklb_Ukikp8NxjUePftYxvsko3XQl6K1hfTGN3FpjyzbOWnAUwd_JrorYXLZebUhhgYKPHiABAEJB"  # Replace with your actual access token
WECHAT_TEMPLATE_ID = "_auSzj17oy_Q5rvsQ3CXTqSVodx9xShJYyPCyxJTp2k"  # Replace with your actual template ID
WECHAT_USER_OPENID = "ofYhV6W_mDuDnm8lVbgVbgEMtvWc"  # Replace with the actual user's openid

def get_access_token(app_id, app_secret):
    # 微信公众号的 access_token 获取 URL
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"

    # 发送请求
    response = requests.get(url)

    # 将响应结果解析为 JSON
    data = response.json()

    # 检查是否成功获取 access_token
    if "access_token" in data:
        access_token = data['access_token']
        expires_in = data['expires_in']
        print(f"Access Token: {access_token}")
        print(f"Expires in: {expires_in} seconds")
        return access_token
    else:
        # 如果请求失败，打印错误信息
        print(f"Failed to get access_token: {data}")
        return None
    
    
def send_wechat_alert(alert_type, user_openid, user_name, severity_level):
    # Debug prints to check values
    print(f"Sending alert for user: {user_name}, alertType: {alert_type}, severityLevel: {severity_level}")
    message = {
        "touser": user_openid,
        "template_id": WECHAT_TEMPLATE_ID,
        "data": {
            "user": {
                "value": user_name,
                "color": "#FF0000"
            },
            "alert_type": {
                "value": alert_type,
                "color": "#173177"
            },
            "severity_level": {
                "value": severity_level,
                "color": "#173177"
            },
            "remark": {
                "value": "请尽快就医。",
                "color": "#173177"
            }
        }
    }
    response = requests.post(WECHAT_API_URL.format(ACCESS_TOKEN=WECHAT_ACCESS_TOKEN), json=message)
    print(response.status_code)
    return response.json()

@app.route("/personal")
def bigscreen_index():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    #personalInfo = get_personal_info(deviceSn)  # Get the userName from query parameters
    print("deviceSn", deviceSn)
    #print("personalInfo", personalInfo)
    # You can now use deviceSn in your logic or pass it to the template
    #return render_template("bigscreen_new.html", deviceSn=deviceSn, userName=userName)
    return render_template("personal.html", deviceSn=deviceSn)

@app.route("/personal_old")
def personal_old():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    #personalInfo = get_personal_info(deviceSn)  # Get the userName from query parameters
    print("deviceSn", deviceSn)
    #print("personalInfo", personalInfo)
    # You can now use deviceSn in your logic or pass it to the template
    #return render_template("bigscreen_new.html", deviceSn=deviceSn, userName=userName)
    return render_template("bigscreen_new.html", deviceSn=deviceSn)

@app.route("/main")
def main_index():
    customerId = request.args.get('customerId')  # Get the deviceSn from query parameters
    print("customerId", customerId)
    return render_template("bigscreen_main.html", customerId=customerId)

@app.route("/alert")
def alert_index():
    return render_template("alert.html")

@app.route("/message")
def message_index():
    return render_template("message.html")

@app.route("/chart")
def chart_index():
    return render_template("chart.html")

def redis_update_health_data(channel, data):
    print("redis_update_health_data", data)
    redis_helper.publish(channel, data)
    
@app.route('/getUserInfo', methods=['GET'])
def get_user_info(deviceSn):
    # 从查询参数获取 deviceSn
    print("get_user_names", deviceSn)
    user = UserInfo.query.filter_by(device_sn=deviceSn).first()
    
    if user:
        user_name = user.real_name
        user_phone = user.phone  # Assuming user_phone is a field in UserInfo
        # Store in Redis
        redis_helper.hset_data(f"user_info:{deviceSn}", {"real_name": user_name, "phone": user_phone})
        redis_update_health_data("user_info_channel", deviceSn)
        return user_name
    else:
        return "No user found"



@app.route('/deviceMessages/send', methods=['POST'])
def send_message():
    data = request.get_json()
    print("send_message", data)

    # Check if all required fields are present
    required_fields = ['device_sn','id', 'message', 'message_type', 'sender_type', 'receiver_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if message_id is present to update the existing message
    message_id = data.get('id')
    if message_id:
        message = DeviceMessage.query.get(id)
        if message:
            message.device_sn = data['device_sn']
            message.message = data['message']
            message.message_type = data['message_type']
            message.sender_type = data['sender_type']
            message.receiver_type = data['receiver_type']
            message.message_status = data['message_status']

            # Convert sent_time and received_time to MySQL compatible format
            sent_time_str = data.get('sent_time')
            received_time_str = data.get('received_time')
            if sent_time_str:
                message.sent_time = datetime.strptime(sent_time_str, '%a, %d %b %Y %H:%M:%S GMT')
            if received_time_str:
                message.received_time = datetime.fromisoformat(received_time_str.replace('Z', '+00:00'))

            db.session.commit()
            return jsonify({'message': 'Message updated successfully', 'id': message.id}), 200
        else:
            return jsonify({'error': 'Message not found'}), 404
    else:
        # Create a new message if message_id is not provided
        message = DeviceMessage(
            device_sn=data['device_sn'],
            message=data['message'],
            message_type=data['message_type'],
            sender_type=data['sender_type'],
            receiver_type=data['receiver_type'],
            message_status=data['message_status']
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({'message': 'Message sent successfully', 'message_id': message.id}), 201

@app.route('/deviceMessages/received/<string:device_sn>', methods=['GET'])
def get_received_messages(device_sn):
    messages = DeviceMessage.query.filter_by(device_sn=device_sn, message_status='pending').all()
    return jsonify([{
        'id': m.id,
        'device_sn': m.device_sn,
        'message': m.message,
        'message_type': m.message_type,
        'sender_type': m.sender_type,
        'receiver_type': m.receiver_type,
        'message_status': m.message_status,
        'sent_time': m.sent_time,
        'received_time': m.received_time
    } for m in messages])

@app.route('/deviceMessages/status/<int:id>', methods=['PUT'])
def update_message_status(id):
    status = request.args.get('status')
    message = DeviceMessage.query.get_or_404(id)
    message.message_status = status
    message.update_time = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Status updated successfully', 'id': id, 'message_status': status})

# Initialize the heart_rate_timestamps list
@app.route("/query_health_data_config", methods=['GET'])
def query_health_data_config(deviceSn):
    # Check if config is in Redis cache
    cached_config = redis_helper.get_data(f"config:{deviceSn}")
    if cached_config:
        # Decode bytes to string and then parse JSON
        return json.loads(cached_config.decode('utf-8'))

    # If not in cache, query the database
    customer_id = db.session.query(DeviceInfo.customer_id).filter_by(serial_number=deviceSn).first()
    
    if not customer_id:
        return {"error": "Device not found"}
    
    # Query the HealthDataConfig table for the given customerId
    records = db.session.query(HealthDataConfig).filter_by(customer_id=customer_id).all()
    
    # Create a dictionary to store the is_enabled status for each data_type
    config = {record.data_type: record.is_enabled for record in records}
    
    # Store the config in Redis cache with an expiration time (e.g., 3600 seconds)
    redis_helper.set_data(f"config:{deviceSn}", 3600, json.dumps(config))
    
    return config

@app.route("/upload_device_info", methods=['POST'])
def handle_device_info():
    return upload_device_info()

def upload_health_data():
    heart_rate_timestamps = []
    heart_rate_high_count = 0
    heart_rate_low_count = 0
    # 接收客户端传来的JSON数据
    health_data = request.get_json()  # 使用Flask的request对象获JSON数据

    # 打印接收到的数据（可选，仅用于调试）
    print(health_data)

    # 从JSON数据中提取各健康标
    data = health_data.get("data", {})
    heartRate = data.get("heart_rate")
    pressureHigh = data.get("blood_pressure_systolic")
    pressureLow = data.get("blood_pressure_diastolic")
    bloodOxygen = data.get("blood_oxygen")
    temperature = data.get("body_temperature")
    timestamp = data.get("cjsj") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deviceSn = data.get("id")
    
    # Query the is_enabled flags for each metric from thealth_data_config
    config = query_health_data_config(deviceSn)  # Assume this function returns a dictionary with is_enabled flags

    # Conditionally retrieve values based on individual is_enabled flags
    step = data.get("step") if config.get("step", False) else None
    distance = data.get("distance") if config.get("distance", False) else None
    calorie = data.get("calorie") if config.get("calorie", False) else None
    if(config.get("location", False)):
        latitude = data.get("latitude",0) 
        longitude = data.get("longitude",0) 
        altitude = data.get("altitude", 0)
    else:
        latitude = None
        longitude = None
    sleepData = data.get("sleepData") if config.get("sleep", False) else None
    exerciseDailyData = data.get("exerciseDailyData") if config.get("exercise_daily", False) else None
    exerciseDailyWeekData = data.get("exerciseDailyWeekData") if config.get("exercise_daily_week", False) else None
    scientificSleepData = data.get("scientificSleepData") if config.get("scientific_sleep", False) else None
    


    # 存入数据库的逻辑
    def convert_empty_to_none(value):
        return None if value == ' ' else value

    # Convert empty strings to None
    heartRate = convert_empty_to_none(heartRate)
    pressureHigh = convert_empty_to_none(pressureHigh)
    pressureLow = convert_empty_to_none(pressureLow)
    bloodOxygen = convert_empty_to_none(bloodOxygen)
    temperature = convert_empty_to_none(temperature)
    step = convert_empty_to_none(step)
    timestamp = convert_empty_to_none(timestamp)
    deviceSn = convert_empty_to_none(deviceSn)
    distance = convert_empty_to_none(distance)
    calorie = convert_empty_to_none(calorie)
    latitude = convert_empty_to_none(latitude)
    longitude = convert_empty_to_none(longitude)
    altitude = convert_empty_to_none(altitude)
    sleepData = convert_empty_to_none(sleepData)
    exerciseDailyData = convert_empty_to_none(exerciseDailyData)
    exerciseDailyWeekData = convert_empty_to_none(exerciseDailyWeekData)
    scientificSleepData = convert_empty_to_none(scientificSleepData)

    save_health_data(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, altitude, sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData)
   # Helper function to convert None to a string
    def safe_str(value):
        return str(value) if value is not None else ''
    # 入Redis并设置1分钟超时
    #print("storing data in redis", health_data)
    health_data_new = {
        "heartRate": safe_str(heartRate),
        "pressureHigh": safe_str(pressureHigh),
        "pressureLow": safe_str(pressureLow),
        "bloodOxygen": safe_str(bloodOxygen),
        "temperature": safe_str(temperature),
        "step": safe_str(step),
        "timestamp": safe_str(timestamp),
        "deviceSn": safe_str(deviceSn),
        "distance": safe_str(distance),
        "calorie": safe_str(calorie),
        "latitude": safe_str(latitude),
        "longitude": safe_str(longitude),
        "altitude": safe_str(altitude),
        "sleepData": json.dumps(sleepData) if sleepData else '',
        "exerciseDailyData": json.dumps(exerciseDailyData) if exerciseDailyData else '',
        "exerciseDailyWeekData": json.dumps(exerciseDailyWeekData) if exerciseDailyWeekData else '',
        "scientificSleepData": json.dumps(scientificSleepData) if scientificSleepData else ''
    }

    # 使用 redis_client.hset 存储数据
    redis_helper.hset_data(f"health_data:{deviceSn}", mapping=health_data_new)
    print("redis_client.hset", redis_helper.hgetall_data(f"health_data:{deviceSn}"))

    # 更新 Redis 中的健康数据
    
    redis_update_health_data("health_data_channel", deviceSn)

    # Initialize counters for heart rate alerts
    heart_rate_high_count = 0
    heart_rate_low_count = 0

    # Check for abnormal heart rate and send WeChat alert
    if heartRate:
        current_time = datetime.now()
        heart_rate_timestamps.append(current_time)

        # Remove timestamps older than 10 minutes
        heart_rate_timestamps = [timestamp for timestamp in heart_rate_timestamps if (current_time - timestamp).total_seconds() <= 600]

        if heartRate > 100:
            heart_rate_high_count += 1
        elif heartRate < 60:
            heart_rate_low_count += 1

        # Check if there are 10 occurrences within the last 10 minutes
        if heart_rate_high_count >= 10 or heart_rate_low_count >= 10:
            print("triggering wechat alert...")
            send_wechat_alert(heartRate, WECHAT_USER_OPENID, deviceSn)
            # Reset counters after sending alert
            heart_rate_high_count = 0
            heart_rate_low_count = 0

    # 响应客户端
    return jsonify({"status": "success", "message": "数据已接收并处理"})

def extract_model(system_software_version):
    # Use regex to extract the model part
    match = re.match(r"([A-Z]+-[A-Z]+\d+)", system_software_version)
    if match:
        return match.group(1)
    return None

@app.route("/upload_device_info", methods=['POST'])
def upload_device_info():
    device_info = request.json  # 获取JSON数据

    # 印接收到的数据（可选，仅用于调试）
    print(device_info)

    # 从JSON数据中取设备信息
    system_software_version = device_info.get("System Software Version")
    model = extract_model(system_software_version)  # Extract the model

    # Debug print to check the extracted model
    print(f"Extracted model: {model}")

    wifi_address = device_info.get("Wifi Address")
    bluetooth_address = device_info.get("Bluetooth Address")
    ip_address = device_info.get("IP Address")
    # Extract only the IPv4 address
    ipv4_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', ip_address)
    if ipv4_match:
        ip_address = ipv4_match.group(0)
    else:
        ip_address = None  # or handle the case where no IPv4 is found
    network_access_mode = device_info.get("Network Access Mode")
    serial_number = device_info.get("SerialNumber")
    device_name = device_info.get("Device Name")
    imei = device_info.get("IMEI")
    battery_level = device_info.get("batteryLevel")
    wearable_status = device_info.get("wearState")
    status = device_info.get("status")
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if int(wearable_status) == 1:
        wearable_status = "WORN"
    else:
        wearable_status = "NOT_WORN"
    customer_id = device_info.get("customerId")
    print("wearable_status", wearable_status)
    if not battery_level or battery_level.strip() == "":
        battery_level = "-"
    
    # Map charging status
    charging_status = device_info.get("chargingStatus")

    if charging_status == "NONE":
        charging_status = "NOT_CHARGING"
    elif charging_status == "ENABLE":
        charging_status = "CHARGING"
    else:
        charging_status = "-"
    

    # 存入数据库的逻辑
    save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status, update_time)

    # 响客户端
    return jsonify({"status": "success", "message": "设备信息已接收并处理"})




@app.route("/fetchConfig", methods=['GET'])
def fetch_config():
    global config  # Ensure the module-level config is used
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tDeviceConfig")
        result = cursor.fetchall()

        # Assuming there's only one row in the table
        if result:
            row = result[0]
            config_data = {
                'spo2MeasurePeriod': row['spo2MeasurePeriod'],
                'stressMeasurePeriod': row['stressMeasurePeriod'],
                'bodyTemperatureMeasurePeriod': row['bodyTemperatureMeasurePeriod'],
                'heartRateWarningHigh': row['heartRateWarningHigh'],
                'heartRateWarningLow': row['heartRateWarningLow'],
                'spo2Warning': row['spo2Warning'],
                'stressWarning': row['stressWarning'],
                'bodyTemperatureHighWarning': row['bodyTemperatureHighWarning'],
                'httpUrl': row['httpUrl'],
                'logo': row['logo'],
                'uiType': row['uiType'],
                'bodyTemperatureLowWarning': row['bodyTemperatureLowWarning']
            }
            return jsonify(config_data)
        else:
            return jsonify({"success": False, "error": "No configuration found"}), 404
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()

def save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status, update_time):
    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # SQL query to insert or update data using an alias
        add_or_update_device_info = ("""
            INSERT INTO t_device_info 
            (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status, update_time) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) AS new
            ON DUPLICATE KEY UPDATE
            system_software_version = new.system_software_version,
            wifi_address = new.wifi_address,
            bluetooth_address = new.bluetooth_address,
            ip_address = new.ip_address,
            network_access_mode = new.network_access_mode,
            serial_number = new.serial_number,
            device_name = new.device_name,
            imei = new.imei,
            battery_level = new.battery_level,
            charging_status = new.charging_status,
            wearable_status = new.wearable_status,
            customer_id = new.customer_id,
            status = new.status,
            update_time = new.update_time
        """)

        data = (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status, update_time)

        # Executing the query
        cursor.execute(add_or_update_device_info, data)

        # Committing the transaction
        cnx.commit()

        # Store device_info in Redis
        device_info = {
            "system_software_version": system_software_version,
            "wifi_address": wifi_address,
            "bluetooth_address": bluetooth_address,
            "ip_address": ip_address,
            "network_access_mode": network_access_mode,
            "serial_number": serial_number,
            "device_name": device_name,
            "imei": imei,
            "battery_level": battery_level,
            "charging_status": charging_status,
            "wearable_status": wearable_status,
            "customer_id": customer_id,
            "status": status,
            "update_time": update_time
        }
        redis_helper.hset_data(f"device_info:{serial_number}", device_info)
        redis_update_health_data("device_info_channel", serial_number)

    except mysql.connector.Error as err:
        print(f"Failed to insert or update data in MySQL table: {err}")
    finally:
        # Closing the cursor and connection
        if cnx.is_connected():
            cursor.close()
            cnx.close()
            print("MySQL connection is closed")

def save_health_data(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, altitude, sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData):
    # Database connection parameters

    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # SQL query to insert data
        add_data = ("INSERT INTO t_user_health_data "
                    "(heart_rate, pressure_high, pressure_low, blood_oxygen, temperature, step, timestamp, device_sn, distance, calorie, latitude, longitude, altitude, sleep_data, exercise_daily_data, exercise_week_data, scientific_sleep_data) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        
        
        def prepare_value(value):
            if value is None:
                return None  # MySQL 会将 None 视为 NULL
            elif isinstance(value, list):
                return json.dumps(value)  # 将列表转换为 JSON 字符串
            return value

        data = tuple(prepare_value(value) for value in [
            heartRate, pressureHigh, pressureLow, bloodOxygen, temperature,
            step, timestamp, deviceSn, distance, calorie, latitude, longitude, altitude,
            sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData
])

        #data = ( heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, customerId, sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData)

        # Executing the query
        cursor.execute(add_data, data)

        # Committing the transaction
        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Failed to insert data into MySQL table: {err}")
    finally:
        # Closing the cursor and connection
        if cnx.is_connected():
            cursor.close()
            cnx.close()
            print("MySQL connection is closed")

@app.route('/fetch_health_data', methods=['GET'])
def fetch_health_data():
    global config  # Ensure the module-level config is used
    deviceSn = request.args.get('deviceSn')

    # 从Redis中获数据
    cached_data = redis_helper.get_data(deviceSn)
    if cached_data:
        # Decode bytes to string and then parse JSON
        cached_data = cached_data.decode('utf-8')
        cached_data = json.loads(cached_data)
        return jsonify({"success": True, "data": cached_data})

    connection = mysql.connector.connect(**config)
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Query to fetch the latest record
            sql = """
            SELECT heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, altitude
            FROM t_user_health_data
            WHERE deviceSn = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """
            cursor.execute(sql, (deviceSn,))
            result = cursor.fetchone()
            print("result", result['timestamp'].strftime("%a, %d %b %Y %H:%M:%S GMT"))

            if result:
                formatted_result = {
                    "bloodOxygen": f"{result['bloodOxygen']}",
                    "heartRate": f"{result['heartRate']}",
                    "pressureHigh": f"{result['pressureHigh']}",
                    "pressureLow": f"{result['pressureLow']}",
                    "step": f"{result['step']}",
                    "temperature": f"{result['temperature']}",
                    "timestamp": result['timestamp'].strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "deviceSn": result['deviceSn'],
                    "distance": result['distance'],
                    "calorie": result['calorie'],
                    "latitude": result['latitude'],
                    "longitude": result['longitude'],
                    "altitude": result['altitude']
                }
                # 缓存到Redis
                redis_helper.set_data(deviceSn, jsonify(formatted_result).get_data(as_text=True))
                return jsonify({"success": True, "data": formatted_result})
            else:
                return jsonify({"success": False, "message": "No data found"})
    finally:
        connection.close()
@app.route('/fetch_alertType_stats', methods=['GET'])
def fetch_alertType_stats():
    userName = request.args.get('userName')
    try:
        from sqlalchemy import func
        from datetime import datetime

        # Base query for alert type counts
        query = db.session.query(UserAlert.alertType, func.count(UserAlert.alertType).label('count'))

        if userName:
            query = query.filter(UserAlert.userName == userName)

        alert_type_counts = query.group_by(UserAlert.alertType).all()

        # Convert query results to dictionary list
        alert_type_data = [{'name': alert_type, 'value': count} for alert_type, count in alert_type_counts]

        # Calculate total number of alerts
        total_alerts_query = db.session.query(func.count(UserAlert.id))
        if userName:
            total_alerts_query = total_alerts_query.filter(UserAlert.userName == userName)
        total_alerts = total_alerts_query.scalar()

        # Calculate number of alerts added this month
        start_of_month = datetime(datetime.now().year, datetime.now().month, 1)
        monthly_alerts_query = db.session.query(func.count(UserAlert.id)).filter(UserAlert.timestamp >= start_of_month)
        if userName:
            monthly_alerts_query = monthly_alerts_query.filter(UserAlert.userName == userName)
        monthly_alerts = monthly_alerts_query.scalar()

        return jsonify({
            'success': True,
            'alertTypeStats': alert_type_data,
            'totalAlerts': total_alerts,
            'monthlyAlerts': monthly_alerts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/fetch_user_info', methods=['GET'])
def fetch_user_info():
    userName = request.args.get('userName')
    if not userName:
        return jsonify({'success': False, 'error': 'Missing userName parameter'}), 400

    user = UserAlert.query.filter_by(userName=userName).first()
    if user:
        user_data = {
            'id': user.id,
            'real_name': user.real_name,
            'phone': user.phone,
            'device_sn': user.device_sn,
            'customer_id': user.customer_id,
            'avatar': user.avatar
        }
        return jsonify({'success': True, 'user': user_data})
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404


@app.route('/fetch_alerts', methods=['GET'])
def fetch_alerts(deviceSn=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    print("deviceSn:", deviceSn)

    try:
        if deviceSn is None:
            alerts = AlertInfo.query.all()
        else:
            alerts = AlertInfo.query.filter_by(deviceSn=deviceSn).all()
    
       
       
        alerts_data = [{
            'id': alert.id,
            'deviceSn': alert.device_sn,
            'alertType': alert.alert_type,
            'latitude': alert.latitude,
            'longitude': alert.longitude,
            'timestamp': alert.alert_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'severityLevel': alert.severity_level,
            'alertStatus': alert.alert_status,
            'userName': get_user_info(alert.device_sn) 
        } for alert in alerts]
        
        #print("alerts_data:", alerts_data)

        # Calculate total number of alerts
        total_alerts = len(alerts)

        # Calculate total number of unique alert types
        unique_alert_types = len(set(alert.alert_type for alert in alerts))

        response_data = {
            'success': True,
            'alerts': alerts_data,
            'totalAlerts': total_alerts,
            'uniqueAlertTypes': unique_alert_types
        }
        
        #print("response_data:", response_data)

        # Serialize the alerts_data list to a JSON string
        alerts_data_json = json.dumps(alerts_data)

        # Cache the response data in Redis with an expiration time (e.g., 60 seconds)
        redis_helper.hset_data(f"alert_info:{deviceSn}", "alerts", alerts_data_json)
    
        if deviceSn is None:
            redis_update_health_data("alert_info_channel", "alert_info")
        else:
            redis_update_health_data("alert_info_channel", deviceSn)
        
        print("response_data:", response_data)

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/upload_alerts', methods=['POST'])
def upload_alerts():
    data = request.json
    userName = data.get('userName')
    phoneNumber = data.get('phoneNumber')
    alertType = data.get('alertType')
    timestamp = data.get('timestamp')
    latitude = data.get('latitude', random.uniform(-90, 90))
    longitude = data.get('longitude', random.uniform(-180, 180))

    new_alert = UserAlert(
        userName=userName,
        phoneNumber=phoneNumber,
        alertType=alertType,
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp
    )
    db.session.add(new_alert)
    db.session.commit()

    return jsonify({'message': 'Alert uploaded successfully'}), 201


@app.route('/fetch_health_metrics', methods=['GET'])
def fetch_health_metrics():
    global config  # Ensure the module-level config is used
    userName = request.args.get('userName')
    metric = request.args.get('metric')  # 'heartRate', 'temperature', 'bloodOxygen'
    start_date = request.args.get('startDate')  # 格 "YYYY-MM-DD"
    end_date = request.args.get('endDate')  #  "YYYY-MM-DD"

    if not all([userName, metric, start_date, end_date]):
        return jsonify({"success": False, "error": "Missing required parameters"}), 400

    valid_metrics = ['heartRate', 'temperature', 'bloodOxygen']
    if metric not in valid_metrics:
        return jsonify({"success": False, "error": "Invalid metric parameter"}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        sql = f"""
            SELECT
                DATE(timestamp) as date,
                MAX({metric}) as maxMetric,
                MIN({metric}) as minMetric
            FROM t_user_health_data
            WHERE userName = %s AND timestamp BETWEEN %s AND %s
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        """
        cursor.execute(sql, (userName, start_date, end_date))
        results = cursor.fetchall()

        formatted_results = [{
            "date": result['date'].strftime("%Y-%m-%d"),
            "maxMetric": result['maxMetric'],
            "minMetric": result['minMetric']
        } for result in results]

        cursor.close()
        return jsonify({"success": True, "data": formatted_results})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        connection.close()
@app.route('/test_wechat_alert', methods=['GET'])
def test_wechat_alert():
    # 测试数据
    test_heart_rate = 140
    test_user_openid = WECHAT_USER_OPENID
    test_user_name = "测试用户"
    
    # Debug prints to check values
    print(f"Testing alert for user: {test_user_name}, heart rate: {test_heart_rate}")

    # 调用 send_wechat_alert 函数
    response = send_wechat_alert(test_heart_rate, test_user_openid, test_user_name)

    # 返回响应结果
    return jsonify(response)

def refresh_access_token():
    global WECHAT_ACCESS_TOKEN
    while True:
        WECHAT_ACCESS_TOKEN = get_access_token(app_id, app_secret)
        time.sleep(7200)  # Sleep for 2 hours (7200 seconds)

# Start the background thread to refresh the access token
threading.Thread(target=refresh_access_token, daemon=True).start()

@app.route('/fetch_user_locations', methods=['GET'])
def fetch_user_locations():
    deviceSn = request.args.get('deviceSn')
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    # Get the current date
    current_date = datetime.now().date()
    print(current_date)
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT latitude, longitude, timestamp
            FROM t_user_health_data
            WHERE deviceSn = %s AND DATE(timestamp) = %s
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY timestamp
        """
        cursor.execute(sql, (deviceSn, current_date))
        results = cursor.fetchall()

        formatted_results = [{
            "latitude": result['latitude'],
            "longitude": result['longitude'],
            "timestamp": result['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        } for result in results]

        cursor.close()
        return jsonify({"success": True, "data": formatted_results})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        connection.close()

@app.route('/checkLicense', methods=['GET'])
def check_license():
    customerId = request.args.get('customerId')
    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()

        # Query to count unique deviceSn for the given customer_id
        cursor.execute("""
            SELECT COUNT(DISTINCT serial_number) 
            FROM t_device_info
            WHERE customer_id = %s
        """, (customerId,))
        device_count = cursor.fetchone()[0]

        # Query to get the license_key for the given customer_id
        cursor.execute("""
            SELECT license_key 
            FROM t_customer_config 
            WHERE id = %s
            """, (customerId,))
        license_key = cursor.fetchone()

        if license_key is None:
            return jsonify({'success': False, 'error': 'Customer not found'}), 404

        # Compare device count with license key
        is_exceeded = device_count > license_key[0]

        return jsonify({
            'success': True,
            'isExceeded': is_exceeded,
            'license_key': license_key[0]  # Include license_key in the response
        })
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/upload_common_event', methods=['POST'])
def upload_common_event():
    # Get JSON data from the request
    data = request.json 
    print("begin upload_common_event")
    print(data)

    # Extract the wear_status from the data
    wear_status = data.get("com.tdtech.ohos.action.WEAR_STATUS_CHANGED")

    # Debug print to check the received wear_status
    print(f"Received wear_status: {wear_status}")

    # Implement any logic you need with the wear_status here
    # For example, you might want to store it in a database or perform some action

    # Return a success response
    return jsonify({"status": "success", "message": "Common event received and processed"})



@app.route('/generateHealthJson', methods=['GET'])
def generate_health_json():
    customer_id = request.args.get('customerId')
    if not customer_id:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Updated query to join with t_device_info and t_sys_user to select additional fields
        sql = """
            SELECT t1.device_sn, t1.heart_rate, t1.pressure_high, t1.pressure_low, 
                   t1.blood_oxygen, t1.temperature, t1.latitude, t1.longitude, t1.altitude,
                   t3.battery_level, t3.wearable_status, t3.charging_status, t3.status,
                   t4.real_name, t4.phone
            FROM t_user_health_data t1
            INNER JOIN (
                SELECT device_sn, MAX(timestamp) as max_timestamp
                FROM t_user_health_data
                WHERE device_sn IN (
                    SELECT serial_number FROM t_device_info WHERE customer_id = %s
                )
                GROUP BY device_sn
            ) t2 ON t1.device_sn = t2.device_sn AND t1.timestamp = t2.max_timestamp
                 INNER JOIN t_device_info t3 ON t1.device_sn COLLATE utf8mb4_unicode_520_ci = t3.serial_number COLLATE utf8mb4_unicode_520_ci
            LEFT JOIN sys_user t4 ON t1.device_sn COLLATE utf8mb4_unicode_520_ci = t4.device_sn COLLATE utf8mb4_unicode_520_ci

        """
        cursor.execute(sql, (customer_id,))
        results = cursor.fetchall()

        # Format the results into the specified JSON structure
        features = []
        for result in results:
            if result['latitude'] is not None and result['longitude'] is not None:
                # Map the status fields to their Chinese meanings
                wearable_status = "佩戴" if result['wearable_status'] == "WORN" else "未佩戴"
                charging_status = "正在充电" if result['charging_status'] == "CHARGING" else "未充电"
                status = "在线" if result['status'] == "ACTIVE" else "离线"

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(result['longitude']), float(result['latitude']), float(result['altitude'])]
                    },
                    "properties": {
                        "deviceSn": result['device_sn'],
                        "heartRate": float(result['heart_rate']),
                        "pressureHigh": float(result['pressure_high']),
                        "pressureLow": float(result['pressure_low']),
                        "bloodOxygen": float(result['blood_oxygen']),
                        "temperature": float(result['temperature']),
                        "batteryLevel": result['battery_level'],
                        "wearableStatus": wearable_status,
                        "chargingStatus": charging_status,
                        "status": status,
                        "userName": result.get('real_name', 'N/A'),
                        "phoneNumber": result.get('phone', 'N/A')
                    }
                }
                features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Ensure the data directory exists
        os.makedirs('static/data', exist_ok=True)

        # Write the JSON data to a file
        with open('static/data/healthData.json', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=4)

       
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()
    return jsonify(geojson)

@app.route('/generateAlertJson', methods=['GET'])
def generate_alert_json():
    severityLevel = request.args.get('severityLevel')  # Get the severityLevel from query parameters


    # Build the query using SQLAlchemy ORM
    query = AlertInfo.query.filter_by(severity_level=severityLevel, alert_status='pending')

    alerts = query.all()
    

    # Format the alerts into the desired JSON structure
    features = []
    for alert in alerts:
        userName = get_user_info(alert.device_sn)
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [ alert.latitude, alert.longitude]
            },
            "properties": {
                "id": alert.id,
                "deviceSn": alert.device_sn,  # Assuming 'id' is used as a unique identifier
                "alertType": alert.alert_type,
                "alertDesc": alert.alert_desc,
                "status": alert.alert_status,
                "severityLevel": alert.severity_level,
                "userName": userName,
                "timestamp": alert.alert_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        features.append(feature)

    # Create the final JSON structure
    alert_json = {
        "type": "FeatureCollection",
        "features": features
    }


    # Return the JSON response
    return jsonify(alert_json)

@app.route('/generateAlertChart', methods=['GET'])
def generate_alert_chart():
    customerId = request.args.get('customerId')
    timeDimension = request.args.get('timeDimension')  # New parameter for time dimension

    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    # Connect to the database
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    # Base query
    query = """
    SELECT 
        COUNT(id) as alertCount,
        severityLevel,
    """

    # Modify query based on time dimension
    if timeDimension == 'day':
        query += "HOUR(timestamp) as timeUnit "
    elif timeDimension == 'week':
        query += "DAYOFWEEK(timestamp) as timeUnit "
    elif timeDimension == 'month':
        query += "DAY(timestamp) as timeUnit "
    else:
        return jsonify({'success': False, 'error': 'Invalid timeDimension parameter'}), 400

    query += """
    FROM t_user_alerts
    WHERE customerId = %s
    """
    params = [customerId]

    query += " GROUP BY timeUnit, severityLevel ORDER BY timeUnit"

    cursor.execute(query, params)
    alert_counts = cursor.fetchall()

    # Close the database connection
    cursor.close()
    connection.close()

    # Return the JSON response
    return jsonify({'success': True, 'data': alert_counts})
@app.route('/generateAlertTypeChart', methods=['GET'])
def generate_alert_chart_by_type():
    customerId = request.args.get('customerId')

    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    # Connect to the database
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor(dictionary=True)

    # Base query
    query = """
    SELECT 
        COUNT(id) as alertCount,
        alertType
    FROM t_user_alerts
    WHERE customerId = %s
    GROUP BY alertType
    ORDER BY alertType
    """
    params = [customerId]

    cursor.execute(query, params)
    alert_counts = cursor.fetchall()

    # Close the database connection
    cursor.close()
    connection.close()

    # Return the JSON response
    return jsonify({'success': True, 'data': alert_counts})

@app.route('/fetch_alert', methods=['GET'])
def fetch_alert():
    deviceSn = request.args.get('deviceSn')
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        sql = """
            SELECT alert_type, severity_level, alert_status,alert_timestamp
            FROM t_alert_info
            WHERE deviceSn = %s
        """
        cursor.execute(sql, (deviceSn,))
        alerts = cursor.fetchall()

        # Format the results into a list of dictionaries
        alert_data = [{
            'alert_type': alert['alert_type'],
            'severity_level': alert['severity_level'],
            'alert_status': alert['alert_status'],
            'alert_time': alert['alert_timestamp']
        } for alert in alerts]

        return jsonify({'success': True, 'data': alert_data})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

def redis_change_listener():
    pubsub = redis_helper.pubsub()
    pubsub.subscribe('health_data_channel', 'device_info_channel', 'user_info_channel', 'message_channel', 'alert_channel')
    
    with app.app_context():  # Set up the application context
        for message in pubsub.listen():
            if message['type'] == 'message':
                #print("message", message)
                deviceSn = message['data'].decode('utf-8')
                data = get_personal_info(deviceSn)
                #print("personal_info_update::data", data)
                socketio.emit('personal_info_update', data)
            

# Start the Redis change listener in a separate thread
threading.Thread(target=redis_change_listener, daemon=True).start()
@app.route('/get_personal_info', methods=['GET'])
def get_personal_info(deviceSn=None):
    if not deviceSn:
        deviceSn = request.args.get('deviceSn')
    if not deviceSn:
        return jsonify({'success': False, 'error': 'Missing deviceSn parameter'}), 400

    # Strip any leading or trailing whitespace from deviceSn
    deviceSn = deviceSn.strip()

    # Fetch data from Redis
    health_data = redis_helper.hgetall_data(f"health_data:{deviceSn}")
    device_info = redis_helper.hgetall_data(f"device_info:{deviceSn}")
    user_info = redis_helper.hgetall_data(f"user_info:{deviceSn}")
    if not user_info:
        get_user_info(deviceSn)
        user_info = redis_helper.hgetall_data(f"user_info:{deviceSn}")
    
    get_user_message(deviceSn)
    message_info = redis_helper.hget(f"message_info:{deviceSn}", "messages")
    if message_info:
        # Decode the JSON string to a Python object
        message_info = json.loads(message_info.decode('utf-8'))    
    # Fetch alert_info as a string and parse it
    fetch_alerts(deviceSn)
    alerts_data_json = redis_helper.hget(f"alert_info:{deviceSn}", "alerts")
    if alerts_data_json:
        # Decode the JSON string to a Python object
        alert_info = json.loads(alerts_data_json.decode('utf-8'))

    # Convert bytes to string for JSON serialization
    def decode_redis_data(data):
        if isinstance(data, dict):
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        return data  # Return data as is if it's not a dictionary

    # Decode all fetched data
    health_data = decode_redis_data(health_data)
    device_info = decode_redis_data(device_info)
    user_info = decode_redis_data(user_info)
    message_info = decode_redis_data(message_info)
    
 
    return {
        'success': True,
        'data': {
            'health_data': health_data,
            'device_info': device_info,
            'user_info': user_info,
            'message_info': message_info,
            'alert_info': alert_info
        }
    }
@app.route('/fetch_messages', methods=['GET'])
def fetch_messages(deviceSn=None):
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')
    print("deviceSn:", deviceSn)

    try:
        if deviceSn is None:
            messages = DeviceMessage.query.all()
        else:
            messages = DeviceMessage.query.filter_by(deviceSn=deviceSn).all()
    
       
       
        messages_data = [{
            'id': message.id,
            'device_sn': message.device_sn,
            'message': message.message,
            'message_type': message.message_type,
            'message_status': message.message_status,
            'sent_time': message.sent_time.strftime("%Y-%m-%d %H:%M:%S") if message.sent_time else None,
            'received_time': message.received_time.strftime("%Y-%m-%d %H:%M:%S") if message.received_time else None
        } for message in messages]
        
        #print("alerts_data:", alerts_data)

        # Calculate total number of alerts
        total_messages = len(messages)

        # Calculate total number of unique alert types
        unique_message_types = len(set(message.message_type for message in messages))

        response_data = {
            'success': True,
            'messages': messages_data,
            'totalMessages': total_messages,
            'uniqueMessageTypes': unique_message_types
        }
        
        #print("response_data:", response_data)

        # Serialize the alerts_data list to a JSON string
        messages_data_json = json.dumps(messages_data)

        # Cache the response data in Redis with an expiration time (e.g., 60 seconds)
        redis_helper.hset_data(f"message_info:{deviceSn}", "messages", messages_data_json)
    
        if deviceSn is None:
            redis_update_health_data("message_info_channel", "message_info")
        else:
            redis_update_health_data("message_info_channel", deviceSn)
        
        #print("response_data:", response_data)

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def get_user_message(deviceSn):
    if not deviceSn:
        print("Error: deviceSn is None")
        return None

    # Query the DeviceMessage table to get messages for the given deviceSn
    messages = DeviceMessage.query.filter_by(device_sn=deviceSn).all()
    
    # Convert the messages to a list of dictionaries
    message_list = [{
        'message': message.message,
        'message_type': message.message_type,
        'message_status': message.message_status,
        'sent_time': message.sent_time.strftime("%Y-%m-%d %H:%M:%S") if message.sent_time else None,
        'received_time': message.received_time.strftime("%Y-%m-%d %H:%M:%S") if message.received_time else None
    } for message in messages]
    
    # Convert the message list to a JSON string
    message_json = json.dumps(message_list)
    print("message_json", message_json)
    
    if message_json is None:
        print("Error: message_json is None")
        return None
    
    # Check the type of the key and delete if necessary
    if redis_helper.exists(f"message_info:{deviceSn}"):
        if redis_helper.type(f"message_info:{deviceSn}") != b'hash':
            redis_helper.delete(f"message_info:{deviceSn}")
    
    # Store the JSON string in Redis as a single field
    redis_helper.hset_data(f"message_info:{deviceSn}", "messages", message_json)
    
    redis_update_health_data("message_info_channel", deviceSn) 
    
    return message_json
@app.route('/gather_device_info', methods=['GET'])
def gather_device_info(customer_id=None):
    if customer_id is None:
        customer_id = request.args.get('customer_id')
    print("customer_id:", customer_id)
    # Filter devices by customer_id
    devices = DeviceInfo.query.filter_by(customer_id=customer_id).all()

    # Initialize statistics
    system_software_versions = {}
    wearable_status_count = {'WORN': 0, 'NOT_WORN': 0}
    charging_status_count = {'CHARGING': 0, 'NOT_CHARGING': 0}
    assigned_devices_count = 0
    active_devices_count = 0  # Initialize active devices count
    total_devices_count = len(devices)  # Calculate total number of devices

    # Fetch the os_version for the customer
    customer_config = CustomerConfig.query.filter_by(id=customer_id).first()
    os_version = customer_config.os_version if customer_config else None

    # Initialize the counter for devices with version equal to os_version
    matching_version_count = 0

    # Gather statistics
    for device in devices:
        # Count system software versions
        version = device.system_software_version
        if version in system_software_versions:
            system_software_versions[version] += 1
        else:
            system_software_versions[version] = 1

        # Determine if an upgrade is needed
        if os_version and version != os_version:
            print(f"Device {device.serial_number} needs an upgrade from {version} to {os_version}")
        else:
            # Increment the counter if the version matches os_version
            matching_version_count += 1

        # Count wearable status
        if device.wearable_status in wearable_status_count:
            wearable_status_count[device.wearable_status] += 1

        # Count charging status
        if device.charging_status in charging_status_count:
            charging_status_count[device.charging_status] += 1

        # Check if the device is assigned to a user
        if UserInfo.query.filter_by(device_sn=device.serial_number).first():
            assigned_devices_count += 1

        # Check if the device is active
        if device.update_time and (datetime.now() - device.update_time).total_seconds() <= 600:
            active_devices_count += 1

    # Print or store the count of matching versions
    print(f"Number of devices with version matching os_version: {matching_version_count}")

    # Prepare the data to be stored in Redis
    device_info_data = {
        'system_software_versions': system_software_versions,
        'wearable_status_count': wearable_status_count,
        'charging_status_count': charging_status_count,
        'assigned_devices_count': assigned_devices_count,
        'active_devices_count': active_devices_count,  # Include active devices count
        'total_devices_count': total_devices_count  # Include total devices count
    }

    # Convert the data to JSON format
    device_info_json = json.dumps(device_info_data)

    # Store the JSON data in Redis with the key "device_info:{customer_id}"
    redis_key = f"device_info:{customer_id}"
    redis_helper.set_data(redis_key, device_info_json)

    # Return the gathered statistics
    return device_info_data

@app.route('/gather_total_info', methods=['GET'])
def gather_total_info(customer_id=None):
    if customer_id is None:
        customer_id = request.args.get('customer_id')
    print("customer_id:", customer_id)

    # Gather device info
    device_info = gather_device_info(customer_id)

    # Fetch messages and ensure they return JSON-serializable data
    message_response = fetch_messages()
    message_info = message_response.get_json() if isinstance(message_response, Response) else message_response

    # Fetch alerts and ensure they return JSON-serializable data
    alert_response = fetch_alerts()
    alert_info = alert_response.get_json() if isinstance(alert_response, Response) else alert_response

    # Combine all information into a single JSON response
    total_info = {
        'device_info': device_info,
        'message_info': message_info,
        'alert_info': alert_info
    }

    return jsonify(total_info)
@app.route('/deal_alerts', methods=['GET'])
def dealAlerts(alertId=None):
    if alertId is None:
        alertId = request.args.get('alertId')
    # Find the alert in the database
    alert = AlertInfo.query.filter_by(id=alertId).first()
    userName = get_user_info(alert.device_sn)
    print("userName:", userName)
    response = send_wechat_alert(alert.alert_type, WECHAT_USER_OPENID, userName, alert.severity_level)
    print("response:", response)
    
    # Determine the result and handling method
    result = 'success' if response and response.get('errcode') == 0 else 'failed'
    handled_via = 'WeChat'  # Assuming the handling method is WeChat

    # Create a new alert log entry
    alert_log = AlertLog(
        alert_id=alertId,
        action='deal_alert',
        action_user=userName,  # Assuming userName is the operator
        action_user_id=None,  # Replace with actual user ID if available
        details=f"Alert dealt with via {handled_via}",
        handled_via=handled_via,
        result=result
    )
    db.session.add(alert_log)
    
    if alert and response and response.get('errcode') == 0:
        # Update the alert status to 'responded'
        alert.alert_status = 'responded'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Alert dealt with successfully'})
    else:
        print("Failed to send alert or update alert status")
        db.session.commit()  # Commit the log entry even if the alert handling fails
        return jsonify({'success': False, 'message': 'Failed to deal with alert'}), 500

def main():
    #context = ('cert.pem', 'key.pem')

    #app.run(host='0.0.0.0', port=3003, debug=True, ssl_context=context)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
if __name__ == "__main__":
     main()





