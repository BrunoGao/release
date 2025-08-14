#!/usr/bin/env python3
import sys,os
sys.path.append('../..')
from config import MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASSWORD,MYSQL_DATABASE
import pymysql

conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE)
with conn.cursor() as cursor:
    #查找包含sleepData或sleep_data的表
    cursor.execute("SHOW TABLES")
    tables=cursor.fetchall()
    
    found_tables=[]
    for table in tables:
        table_name=table[0]
        try:
            cursor.execute(f"DESCRIBE {table_name}")
            columns=cursor.fetchall()
            for col in columns:
                col_name=col[0]
                if 'sleep' in col_name.lower():
                    found_tables.append((table_name,col_name,col[1]))
        except Exception as e:
            print(f"检查表{table_name}失败: {e}")
    
    print("包含sleep相关字段的表:")
    for table_name,col_name,col_type in found_tables:
        print(f"- {table_name}.{col_name} ({col_type})")
    
    #特别检查每日和每周表
    for table_name in ['t_user_health_data_daily','t_user_health_data_weekly']:
        try:
            cursor.execute(f"DESCRIBE {table_name}")
            columns=cursor.fetchall()
            print(f"\n{table_name} 表结构:")
            for col in columns:
                print(f"- {col[0]} | {col[1]}")
        except Exception as e:
            print(f"表{table_name}不存在: {e}")

conn.close() 