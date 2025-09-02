# -*- coding: utf-8 -*-
"""
手表日志处理模块
处理手表日志的上传、存储、查询和显示功能
"""

from flask import request, jsonify, render_template
from datetime import datetime
import mysql.connector
from config import SQLALCHEMY_DATABASE_URI
import re

def get_db_config():
    """从SQLALCHEMY_DATABASE_URI解析数据库配置"""
    uri = SQLALCHEMY_DATABASE_URI
    pattern = r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, uri)
    
    if match:
        user, password, host, port, database = match.groups()
        return {
            'user': user,
            'password': password,
            'host': host,
            'port': int(port),
            'database': database,
            'raise_on_warnings': True,
            'charset': 'utf8mb4'
        }
    else:
        return {
            'user': 'root',
            'password': '123456',
            'host': 'localhost',
            'port': 3306,
            'database': 'hg_health',
            'raise_on_warnings': True,
            'charset': 'utf8mb4'
        }

def upload_watch_log():
    """接收并处理手表日志数据"""
    try:
        log_data = request.json
        print(f"收到手表日志数据: {log_data}")
        
        if 'data' in log_data:
            data = log_data['data']
            device_sn = data.get('deviceSn', '')
            timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            log_level = data.get('level', 'INFO')
            log_content = data.get('content', '')
            
            save_watch_log(device_sn, timestamp, log_level, log_content)
            
            return jsonify({"status": "success", "message": "手表日志已接收并处理"})
        else:
            return jsonify({"status": "error", "message": "日志数据格式错误"}), 400
            
    except Exception as e:
        print(f"处理手表日志失败: {e}")
        return jsonify({"status": "error", "message": f"处理失败: {str(e)}"}), 500

def save_watch_log(device_sn, timestamp, log_level, log_content):
    """保存手表日志到数据库"""
    try:
        config = get_db_config()
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()
        
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
        
        insert_sql = """
        INSERT INTO t_watch_logs (device_sn, timestamp, log_level, log_content)
        VALUES (%s, %s, %s, %s)
        """
        
        data = (device_sn, timestamp, log_level, log_content)
        cursor.execute(insert_sql, data)
        cnx.commit()
        print(f"手表日志已保存: {device_sn} - {log_level} - {timestamp}")
        
    except mysql.connector.Error as err:
        print(f"保存手表日志失败: {err}")
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()

def watch_logs_page():
    """手表日志显示页面"""
    return render_template('watch_logs.html')

def get_watch_logs():
    """获取手表日志数据API"""
    try:
        device_sn = request.args.get('deviceSn', '')
        log_level = request.args.get('level', '')
        start_time = request.args.get('startTime', '')
        end_time = request.args.get('endTime', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 50))
        
        config = get_db_config()
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        
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
        
        count_sql = f"SELECT COUNT(*) as total FROM t_watch_logs{where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
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

def get_watch_log_stats():
    """获取手表日志统计信息"""
    try:
        config = get_db_config()
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor(dictionary=True)
        
        stats_sql = """
        SELECT 
            log_level,
            COUNT(*) as count,
            MAX(created_at) as latest_time
        FROM t_watch_logs 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        GROUP BY log_level
        ORDER BY count DESC
        """
        
        cursor.execute(stats_sql)
        level_stats = cursor.fetchall()
        
        device_sql = """
        SELECT 
            COUNT(DISTINCT device_sn) as device_count,
            COUNT(*) as total_logs
        FROM t_watch_logs 
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        
        cursor.execute(device_sql)
        device_stats = cursor.fetchone()
        
        return jsonify({
            "success": True,
            "data": {
                "level_stats": level_stats,
                "device_count": device_stats['device_count'],
                "total_logs": device_stats['total_logs']
            }
        })
        
    except mysql.connector.Error as err:
        print(f"获取日志统计失败: {err}")
        return jsonify({"success": False, "message": f"统计失败: {str(err)}"})
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
