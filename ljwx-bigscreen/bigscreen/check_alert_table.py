#!/usr/bin/env python3
import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='123456',
        database='lj-06',
        charset='utf8mb4'
    )
    
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE t_alert_info")
        columns = cursor.fetchall()
        
        print("=== t_alert_info 表结构 ===")
        for column in columns:
            print(f"{column[0]:<25} {column[1]:<15} {column[2]:<10} {column[3]:<10} {column[4] or 'NULL':<10} {column[5] or ''}")
            
        print("\n=== 检查是否存在org_id字段 ===")
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND COLUMN_NAME='org_id'")
        org_id_exists = cursor.fetchone()
        print(f"org_id字段存在: {org_id_exists is not None}")
        
except Exception as e:
    print(f"数据库连接错误: {e}")
finally:
    if 'connection' in locals():
        connection.close() 