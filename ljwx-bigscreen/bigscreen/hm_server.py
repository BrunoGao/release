from random import randrange

from flask.json import jsonify
from flask import Flask, render_template, request

from datetime import datetime
import json
import mysql.connector
import pymysql.cursors
from pyecharts import options as opts
from pyecharts.charts import Line
from flask_cors import CORS
app = Flask(__name__, static_folder="templates")
CORS(app)
config = {
        'user': 'root',
        'password': '123456',
        'host': 'localhost',
        'database': 'hg_health',
        'raise_on_warnings': True
    }
    

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload_health_data", methods=['POST'])
def upload_health_data():
    # 接收客户端传来的JSON数据
    health_data = request.json  # 使用Flask的request对象获取JSON数据

    # 打印接收到的数据（可选，仅用于调试）
    print(health_data)
    
    # 从JSON数据中直接提取各项健康指标
 
    heartRate = health_data.get("heartRate")
    pressureHigh = health_data.get("pressureHigh")
    pressureLow = health_data.get("pressureLow")
    bloodOxygen = health_data.get("bloodOxygen")
    temperature = health_data.get("temperature")
    step = health_data.get("step")
    timestamp = health_data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deviceSerialNumber = health_data.get("serialNumber")
    distance = health_data.get("distance")
    calorie = health_data.get("calorie")
    
    # 存入数据库的逻辑
    save_health_data( heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSerialNumber, distance, calorie)
        
    # 响应客户端
    return jsonify({"status": "success", "message": "数据已接收并处理"})

@app.route("/upload_device_info", methods=['POST'])
def upload_device_info():
    device_info = request.json  # 获取JSON数据

    # 打印接收到的数据（可选，仅用于调试）
    print(device_info)

    # 从JSON数据中提取设备信息
    system_software_version = device_info.get("SystemSoftwareVersion")
    wifi_address = device_info.get("WifiAddress")
    bluetooth_address = device_info.get("BluetoothAddress")
    ip_address = device_info.get("IPAddress")
    network_access_mode = device_info.get("NetworkAccessMode")
    serial_number = device_info.get("SerialNumber")
    device_name = device_info.get("DeviceName")
    imei = device_info.get("IMEI")

    # 存入数据库的逻辑
    save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei)

    # 响应客户端
    return jsonify({"status": "success", "message": "设备信息已接收并处理"})

@app.route("/upload_watch_log", methods=['POST'])
def upload_watch_log():
    """接收并处理手表日志数据"""
    try:
        log_data = request.json  # 获取JSON数据
        print(f"收到手表日志数据: {log_data}")
        
        # 提取日志数据字段
        if 'data' in log_data:
            data = log_data['data']
            device_sn = data.get('deviceSn', '')
            timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            log_level = data.get('level', 'INFO')
            log_content = data.get('content', '')
            
            # 存入数据库
            save_watch_log(device_sn, timestamp, log_level, log_content)
            
            return jsonify({"status": "success", "message": "手表日志已接收并处理"})
        else:
            return jsonify({"status": "error", "message": "日志数据格式错误"}), 400
            
    except Exception as e:
        print(f"处理手表日志失败: {e}")
        return jsonify({"status": "error", "message": f"处理失败: {str(e)}"}), 500

def save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei):
    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # SQL query to insert or update data using an alias
        add_or_update_device_info = ("""
            INSERT INTO t_device_info 
            (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) AS new
            ON DUPLICATE KEY UPDATE
            system_software_version = new.system_software_version,
            wifi_address = new.wifi_address,
            bluetooth_address = new.bluetooth_address,
            ip_address = new.ip_address,
            network_access_mode = new.network_access_mode,
            device_name = new.device_name,
            imei = new.imei
        """)

        data = (system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei)

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

def save_health_data( heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSerialNumber, distance, calorie):
    # Database connection parameters
    
    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        # SQL query to insert data
        add_data = ("INSERT INTO t_user_health_data "
                    "( heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSerialNumber, distance, calorie) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        
        data = ( heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSerialNumber, distance, calorie)
        
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

def save_watch_log(device_sn, timestamp, log_level, log_content):
    """保存手表日志到数据库"""
    try:
        # 建立数据库连接
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        # 创建日志表（如果不存在）
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS t_watch_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_sn VARCHAR(100) NOT NULL,
            timestamp DATETIME NOT NULL,
            log_level VARCHAR(20) NOT NULL,
            log_content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_device_timestamp (device_sn, timestamp),
            INDEX idx_level (log_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        cursor.execute(create_table_sql)
        
        # 插入日志数据
        insert_sql = """
        INSERT INTO t_watch_logs (device_sn, timestamp, log_level, log_content)
        VALUES (%s, %s, %s, %s)
        """
        
        data = (device_sn, timestamp, log_level, log_content)
        cursor.execute(insert_sql, data)
        
        # 提交事务
        cnx.commit()
        print(f"手表日志已保存: {device_sn} - {log_level} - {timestamp}")
        
    except mysql.connector.Error as err:
        print(f"保存手表日志失败: {err}")
    finally:
        # 关闭连接
        if cnx.is_connected():
            cursor.close()
            cnx.close()

@app.route('/fetch_health_data', methods=['GET'])
def fetch_health_data():
    deviceSerialNumber = request.args.get('deviceSerialNumber')

    connection = mysql.connector.connect(**config)
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Query to fetch the latest record
            sql = """
            SELECT 
                heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp, deviceSerialNumber, distance, calorie
            FROM t_user_health_data 
            WHERE deviceSerialNumber = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """
            cursor.execute(sql, (deviceSerialNumber,))
            result = cursor.fetchone()
            
            if result:
                formatted_result = {
                    "bloodOxygen": f"{result['bloodOxygen']}",
                    "heartRate": f"{result['heartRate']}",
                    "pressureHigh": f"{result['pressureHigh']}",
                    "pressureLow": f"{result['pressureLow']}",
                    "step": f"{result['step']}",
                    "temperature": f"{result['temperature']}",
                    "timestamp": result['timestamp'].strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "deviceSerialNumber": result['deviceSerialNumber'],
                    "distance": result['distance'],
                    "calorie": result['calorie']
                }
                return jsonify({"success": True, "data": formatted_result})
            else:
                return jsonify({"success": False, "message": "No data found"})
    finally:
        connection.close()



@app.route('/fetch_combined_health_data', methods=['GET'])
def fetch_combined_health_data():
    phone_number = request.args.get('phone_number')
    date = request.args.get('timestamp').split(' ')[0]  # Assuming the timestamp is in the format "YYYY-MM-DD"

    connection = mysql.connector.connect(**config)
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Query to fetch individual and average data
            sql = """
            SELECT 
                heartrate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp,
                AVG(heartrate) OVER (PARTITION BY timestamp) AS avg_heartrate, 
                AVG(pressureHigh) OVER (PARTITION BY timestamp) AS avg_pressureHigh,
                AVG(pressureLow) OVER (PARTITION BY timestamp) AS avg_pressureLow,
                AVG(bloodOxygen) OVER (PARTITION BY timestamp) AS avg_bloodOxygen,
                AVG(temperature) OVER (PARTITION BY timestamp) AS avg_temperature,
                AVG(step) OVER (PARTITION BY timestamp) AS avg_step
            FROM health_data 
            WHERE phone_number = %s AND DATE(timestamp) = %s
            ORDER BY timestamp
            """
            cursor.execute(sql, (phone_number, date))
            results = cursor.fetchall()
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "bloodOxygen": f"{result['bloodOxygen']},{result['avg_bloodOxygen']}",
                    "heartrate": f"{result['heartrate']},{result['avg_heartrate']}",
                    "pressureHigh": f"{result['pressureHigh']},{result['avg_pressureHigh']}",
                    "pressureLow": f"{result['pressureLow']},{result['avg_pressureLow']}",
                    "step": f"{result['step']},{result['avg_step']}",
                    "temperature": f"{result['temperature']},{result['avg_temperature']}",
                    "timestamp": result['timestamp'].strftime("%a, %d %b %Y %H:%M:%S GMT")
                })

            return jsonify({"success": True, "data": formatted_results})
    finally:
        connection.close()

@app.route("/lineDynamicData")
def update_line_data():
    global idx
    idx = idx + 1
    return jsonify({"name": idx, "value": randrange(50, 80)})

@app.route('/getAverageHealthData', methods=['GET'])
def get_average_health_data():
    try:
        # 连接数据库
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        # 查询平均健康数据
        query = """
        SELECT 
            AVG(heartRate) as avg_heart_rate,
            AVG(pressureHigh) as avg_pressure_high,
            AVG(pressureLow) as avg_pressure_low,
            AVG(bloodOxygen) as avg_blood_oxygen,
            AVG(temperature) as avg_temperature,
            AVG(step) as avg_step,
            COUNT(*) as total_records
        FROM t_user_health_data
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            return jsonify({
                "success": True,
                "data": {
                    "avg_heart_rate": round(result['avg_heart_rate'] or 0, 1),
                    "avg_pressure_high": round(result['avg_pressure_high'] or 0, 1),
                    "avg_pressure_low": round(result['avg_pressure_low'] or 0, 1),
                    "avg_blood_oxygen": round(result['avg_blood_oxygen'] or 0, 1),
                    "avg_temperature": round(result['avg_temperature'] or 0, 1),
                    "avg_step": round(result['avg_step'] or 0, 1),
                    "total_records": result['total_records']
                }
            })
        else:
            return jsonify({"success": False, "message": "No data found"})
            
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({"success": False, "message": "Database error"})
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/watch_logs')
def watch_logs_page():
    """手表日志显示页面"""
    return render_template('watch_logs.html')

@app.route('/api/watch_logs', methods=['GET'])
def get_watch_logs():
    """获取手表日志数据API"""
    try:
        device_sn = request.args.get('deviceSn', '')
        log_level = request.args.get('level', '')
        start_time = request.args.get('startTime', '')
        end_time = request.args.get('endTime', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 50))
        
        # 建立数据库连接
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if device_sn:
            where_conditions.append("device_sn = %s")
            params.append(device_sn)
            
        if log_level:
            where_conditions.append("log_level = %s")
            params.append(log_level)
            
        if start_time:
            where_conditions.append("timestamp >= %s")
            params.append(start_time)
            
        if end_time:
            where_conditions.append("timestamp <= %s")
            params.append(end_time)
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM t_watch_logs{where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询日志数据
        offset = (page - 1) * page_size
        query_sql = f"""
        SELECT device_sn, timestamp, log_level, log_content, created_at
        FROM t_watch_logs
        {where_clause}
        ORDER BY timestamp DESC, created_at DESC
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query_sql, params + [page_size, offset])
        logs = cursor.fetchall()
        
        # 格式化时间戳
        for log in logs:
            if log['timestamp']:
                log['timestamp'] = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            if log['created_at']:
                log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "total": total,
                "page": page,
                "pageSize": page_size,
                "totalPages": (total + page_size - 1) // page_size
            }
        })
        
    except mysql.connector.Error as err:
        print(f"查询手表日志失败: {err}")
        return jsonify({"success": False, "message": f"查询失败: {str(err)}"})
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=8008, ssl_context=('cert.pem', 'key.pem'))
    app.run(host='0.0.0.0', port=8008)