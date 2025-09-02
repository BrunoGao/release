from random import uniform
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask import request, jsonify
from bigScreen.models import db, UserAlert
from datetime import datetime, timedelta
import random
import mysql.connector
import pymysql.cursors
from redis import Redis
import requests  # 用于发送HTTP请求
import json
import threading
import time
from flask_socketio import SocketIO
from .models import DeviceMessage  
import re
import os
from decimal import Decimal

app = Flask(__name__, static_folder='../static')
socketio = SocketIO(app)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:aV5mV7kQ@localhost:3306/hg_health'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:aV5mV7kQ%21%40%23@192.168.1.83:3306/1112'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

config = {
    'user': 'root',
    'password': '123456',
    'host': '192.168.1.83',
    'database': 'customer_config',
    'raise_on_warnings': True
}

# Initialize Redis connection
redis_client = Redis(host='localhost', port=6379, db=0)
pubsub = redis_client.pubsub()
def redis_listener():
    pubsub = redis_client.pubsub()
    pubsub.subscribe('health_data_channel', 'device_info_channel', 'user_info_channel', 'message_info_channel', 'alert_info_channel')
    
    with app.app_context():
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    # Ensure the message data is not empty
                    if message['data']:
                        data = json.loads(message['data'])
                        # Process the data as needed
                        #print("Received data:", data)
                    else:
                        print("Received empty message data")
                except json.JSONDecodeError as e:
                    print(f"Failed to decode JSON: {e}")
# Start the Redis listener in a separate thread
threading.Thread(target=redis_listener, daemon=True).start()

app_id = 'wx10dcc9f0235e1d77'
app_secret = 'b7e9088f3f5fe18a9cfb990c641138b3'
# WeChat API configuration
WECHAT_API_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}"
WECHAT_ACCESS_TOKEN = "84__0GoGXHi168Njqn5lusnGWqaDatlAL5b3Exi_oxD6ChSO9gvogZovkb7Yklb_Ukikp8NxjUePftYxvsko3XQl6K1hfTGN3FpjyzbOWnAUwd_JrorYXLZebUhhgYKPHiABAEJB"  # Replace with your actual access token
WECHAT_TEMPLATE_ID = "efhb2xrKbIs4rk2Anx6aGAiabehEFmewSm3ktQUM0vY"  # Replace with your actual template ID
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
    
    
def send_wechat_alert(heart_rate, user_openid, user_name):
    # Debug prints to check values
    print(f"Sending alert for user: {user_name}, heart rate: {heart_rate}")
    message = {
        "touser": user_openid,
        "template_id": WECHAT_TEMPLATE_ID,
        "data": {
            "user": {
                "value": user_name,
                "color": "#FF0000"
            },
            "heartRate": {
                "value": heart_rate,
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

@app.route("/main")
def index():
    deviceSn = request.args.get('deviceSn')  # Get the deviceSn from query parameters
    print("deviceSn", deviceSn)
    # You can now use deviceSn in your logic or pass it to the template
    return render_template("main.html", deviceSn=deviceSn)

def redis_update_health_data(data):
    print("redis_update_health_data", data)
    redis_client.publish('health_data_channel', json.dumps(data))
    


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


@app.route("/upload_health_data", methods=['POST'])

def upload_health_data():
    heart_rate_timestamps = []
    heart_rate_high_count = 0
    heart_rate_low_count = 0
    # 接收客户端传来的JSON数据
    health_data = request.get_json()  # 使用Flask的request对象获取JSON数据

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
    
    # Assuming other fields are not provided in the new format
    step = None
    distance = None
    calorie = None
    latitude = None
    longitude = None
    sleepData = None
    exerciseDailyData = None
    exerciseDailyWeekData = None
    scientificSleepData = None
   

    print("latitude", latitude)
    print("longitude", longitude)

    # 存入数据库的逻辑
    save_health_data(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData)

    # 存入Redis并设置1分钟超时
    print("storing data in redis", health_data)
    redis_client.setex(deviceSn, 60, jsonify(health_data).get_data(as_text=True))
    redis_update_health_data(health_data)

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

@app.route("/upload_device_info", methods=['POST'])
def upload_device_info():
    device_info = request.json  # 获取JSON数据

    # 打印接收到的数据（可选，仅用于调试）
    print(device_info)

    # 从JSON数据中提取设备信息
    system_software_version = device_info.get("System Software Version")
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
    save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status,update_time)

    # 响应客户端
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

def save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status,update_time):
    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # SQL query to insert or update data using an alias
        add_or_update_device_info = ("""
            INSERT INTO t_device_info 
            (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status,update_time) 
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

        data = (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, customer_id, status,update_time)

        # Executing the query
        cursor.execute(add_or_update_device_info, data)

        # Committing the transaction
        cnx.commit()

    except mysql.connector.Error as err:
        print(f"Failed to insert or update data in MySQL table: {err}")
    finally:
        # Closing the cursor and connection
        if cnx.is_connected():
            cursor.close()
            cnx.close()
            print("MySQL connection is closed")

def save_health_data(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude,  sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData):
    # Database connection parameters

    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # SQL query to insert data
        add_data = ("INSERT INTO t_user_health_data "
                    "(heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude,  sleepData, exerciseDailyData, exerciseDailyWeekData, scientificSleepData) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        
        
        def prepare_value(value):
            if value is None:
                return None  # MySQL 会将 None 视为 NULL
            elif isinstance(value, list):
                return json.dumps(value)  # 将列表转换为 JSON 字符串
            return value

        data = tuple(prepare_value(value) for value in [
            heartRate, pressureHigh, pressureLow, bloodOxygen, temperature,
            step, timestamp, deviceSn, distance, calorie, latitude, longitude,
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

    # 尝试从Redis中获取数据
    cached_data = redis_client.get(deviceSn)
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
            SELECT heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSn, distance, calorie, latitude, longitude, customerId
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
                    "customerId": result['customerId']
                }
                # 缓存到Redis
                redis_client.set(deviceSn, jsonify(formatted_result).get_data(as_text=True))
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
            'userName': user.userName,
            'phoneNumber': user.phoneNumber,
            'alertType': user.alertType,
            'latitude': user.latitude,
            'longitude': user.longitude,
            'timestamp': user.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify({'success': True, 'user': user_data})
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/fetch_alerts', methods=['GET'])
def fetch_alerts():
    userName = request.args.get('userName')

    try:
        if userName:
            alerts = UserAlert.query.filter_by(userName=userName).all()
        else:
            alerts = UserAlert.query.all()
        alerts_data = [{
            'id': alert.id,
            'userName': alert.userName,
            'phoneNumber': alert.phoneNumber,
            'alertType': alert.alertType,
            'latitude': alert.latitude,
            'longitude': alert.longitude,
            'timestamp': alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for alert in alerts]

        return jsonify({'success': True, 'alerts': alerts_data})
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
    start_date = request.args.get('startDate')  # 格式 "YYYY-MM-DD"
    end_date = request.args.get('endDate')  # 格 "YYYY-MM-DD"

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
        
        # Query to get the latest record for each deviceSn from t_device_info associated with the customer_id
        sql = """
            SELECT t1.deviceSn, t1.heartRate, t1.pressureHigh, t1.pressureLow, 
                   t1.bloodOxygen, t1.temperature, t1.latitude, t1.longitude
            FROM t_user_health_data t1
            INNER JOIN (
                SELECT deviceSn, MAX(timestamp) as max_timestamp
                FROM t_user_health_data
                WHERE deviceSn IN (
                    SELECT serial_number FROM t_device_info WHERE customer_id = %s
                )
                GROUP BY deviceSn
            ) t2 ON t1.deviceSn = t2.deviceSn AND t1.timestamp = t2.max_timestamp
        """
        cursor.execute(sql, (customer_id,))
        results = cursor.fetchall()

        # Format the results into the specified JSON structure
        features = []
        for result in results:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(result['longitude']), float(result['latitude'])]
                },
                "properties": {
                    "deviceSn": result['deviceSn'],
                    "heartRate": float(result['heartRate']),
                    "pressureHigh": float(result['pressureHigh']),
                    "pressureLow": float(result['pressureLow']),
                    "bloodOxygen": float(result['bloodOxygen']),
                    "temperature": float(result['temperature'])
                }
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        # Ensure the data directory exists
        os.makedirs('data', exist_ok=True)

        # Write the JSON data to a file
        with open('data/healthData.json', 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=4)

        return jsonify({'success': True, 'message': 'Data written to data/healthData.json'})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

def main():
    #context = ('cert.pem', 'key.pem')

    #app.run(host='0.0.0.0', port=3003, debug=True, ssl_context=context)
    app.run(host='0.0.0.0', port=4001, debug=True)
if __name__ == "__main__":
     main()





