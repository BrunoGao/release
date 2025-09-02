from random import uniform
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask import request, jsonify
from bigScreen.models import db, UserAlert
import random
import mysql.connector
import pymysql.cursors
app = Flask(__name__, static_folder='../static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:aV5mV7kQ@`localhost`/hg_health'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
CORS(app)

config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'database': 'hg_health',
    'raise_on_warnings': True
}
@app.route("/bigscreen")
def index():
    return render_template("bigscreen_new.html")

@app.route("/upload_health_data", methods=['POST'])
def upload_health_data():
    # 接收客户端传来的JSON数据
    health_data = request.json  # 使用Flask的request对象获取JSON数据

    # 打印接收到的数据（可选，仅用于调试）
    print(health_data)
    
    # 从JSON数据中直接提取各项健康指标
    phoneNumber = health_data.get("phoneNumber")
    heartRate = health_data.get("heartRate")
    pressureHigh = health_data.get("pressureHigh")
    pressureLow = health_data.get("pressureLow")
    bloodOxygen = health_data.get("bloodOxygen")
    temperature = health_data.get("temperature")
    step = health_data.get("step")
    timestamp = health_data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 存入数据库的逻辑
    save_health_data(phoneNumber, heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp)
        
    # 响应客户端
    return jsonify({"status": "success", "message": "数据已接收并处理"})
def save_health_data(phoneNumber, heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp):
    # Database connection parameters
    
    try:
        # Establishing a connection to the database
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
        # SQL query to insert data
        add_data = ("INSERT INTO t_user_health_data "
                    "(phoneNumber, heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
        
        data = (phoneNumber, heartRate, pressureHigh, pressureLow, bloodOxygen, temperature, step, timestamp)
        
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
    userName = request.args.get('userName')
    metric = request.args.get('metric')  # 'heartRate', 'temperature', 'bloodOxygen'
    start_date = request.args.get('startDate')  # 格式 "YYYY-MM-DD"
    end_date = request.args.get('endDate')  # 格式 "YYYY-MM-DD"
    
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
        
        

@app.route('/fetch_health_data', methods=['GET'])
def fetch_health_data():
    userName = request.args.get('userName')
    dimension = request.args.get('dimension')  # 'year', 'month', 'week', 'day', 'hour'
    
    if not dimension:
        return jsonify({"success": False, "error": "Missing required parameter: dimension"}), 400
    
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        sql_date_format = {
            'day': '%Y-%m-%d %H',  # 每日的每个小时
            'week': '%Y-%m-%d',    # 每周的每一日
            'month': '%Y-%m-%d',   # 每月的每一日
            'year': '%Y-%m'        # 每年的每一月
        }.get(dimension)
        
        if not sql_date_format:
            return jsonify({"success": False, "error": "Invalid dimension parameter"}), 400

        user_condition = f"WHERE userName = %s" if userName else ""
        sql = f"""
               SELECT 
                DATE_FORMAT(timestamp, '{sql_date_format}') as date,
                AVG(heartRate) as avgHeartRate,
                MAX(heartRate) as maxHeartRate,
                MIN(heartRate) as minHeartRate
            FROM t_user_health_data 
            {user_condition}
            GROUP BY DATE_FORMAT(timestamp, '{sql_date_format}')
            ORDER BY DATE_FORMAT(timestamp, '{sql_date_format}')
        """
        params = (userName,) if userName else ()
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        formatted_results = [{
            "date": result['date'] if dimension != 'hour' else result['date'] + ':00',  # Append ':00' to indicate the hour
            "avgHeartRate": result['avgHeartRate'],
            "maxHeartRate": result['maxHeartRate'],
            "minHeartRate": result['minHeartRate']
        } for result in results]
        cursor.close()

        return jsonify({"success": True, "data": formatted_results})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        connection.close()

@app.route('/fetch_user_names', methods=['GET'])
def fetch_user_names():
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()
        query = "SELECT DISTINCT userName FROM t_user_health_data"
        cursor.execute(query)
        user_names = [row[0] for row in cursor.fetchall()]
        return jsonify({'success': True, 'userNames': user_names})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/fetch_health_data_by_user_name', methods=['GET'])
def fetch_health_data_by_user_name():
    userName = request.args.get('userName')
    if not userName:
        return jsonify({'success': False, 'error': 'Missing userName parameter'}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT userName, heartRate, bloodOxygen, temperature, pressureHigh, pressureLow, step, latitude, longitude
            FROM t_user_health_data
            WHERE userName = %s
            ORDER BY timestamp DESC
            LIMIT 1
        """
        cursor.execute(query, (userName,))
        result = cursor.fetchone()
        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'error': 'No data found for user'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/fetch_demison_health_data', methods=['GET'])
def fetch_demison_health_data():
    userName = request.args.get('userName')
    dimension = request.args.get('dimension')  # 'day', 'week', 'month', 'year'
    type = request.args.get('type')  # 'heartRate', 'bloodOxygen', 'temperature'
    from datetime import datetime, timedelta

    if not dimension:
        return jsonify({"success": False, "error": "Missing required parameter: dimension"}), 400
    if not type or type not in ['heartRate', 'bloodOxygen', 'temperature', 'step']:
        return jsonify({"success": False, "error": "Invalid or missing type parameter"}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        current_date = datetime.now()
        date_filter = {
            'day': current_date.strftime('%Y-%m-%d'),
            'week': (current_date - timedelta(days=current_date.weekday())).strftime('%Y-%m-%d'),
            'month': current_date.strftime('%Y-%m'),
            'year': current_date.strftime('%Y')
        }
        sql_date_format = {
            'day': '%Y-%m-%d %H:00',  # For 'day', return data for each hour of the current day
            'week': '%Y-%m-%d',
            'month': '%Y-%m-%d',
            'year': '%Y-%m'
        }.get(dimension)

        if not sql_date_format:
            return jsonify({"success": False, "error": "Invalid dimension parameter"}), 400

        user_condition = f"AND userName = '{userName}'" if userName else ""
        date_condition = f"AND DATE_FORMAT(timestamp, '{sql_date_format}') BETWEEN '{date_filter['day']} 00:00:00' AND '{date_filter['day']} 23:59:59'" if dimension == 'day' else f"AND DATE_FORMAT(timestamp, '{sql_date_format}') >= '{date_filter[dimension]}'"
        sql = f"""
            SELECT 
                DATE_FORMAT(timestamp, '{sql_date_format}') as date,
                AVG({type}) as avgMetric
            FROM t_user_health_data
            WHERE 1=1 {user_condition} {date_condition}
            GROUP BY DATE_FORMAT(timestamp, '{sql_date_format}')
            ORDER BY DATE_FORMAT(timestamp, '{sql_date_format}')
        """
        cursor.execute(sql)
        results = cursor.fetchall()

        formatted_results = [{
            "date": result['date'],
            "avgMetric": result['avgMetric']
        } for result in results]

        return jsonify({"success": True, "data": formatted_results})
    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()




def main():
    context = ('cert.pem', 'key.pem') 
    
    app.run(host='0.0.0.0', port=8008, debug=True, ssl_context=context)
if __name__ == "__main__":
     main()
    
    
    
    
    