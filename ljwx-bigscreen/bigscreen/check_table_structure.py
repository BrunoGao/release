#!/usr/bin/env python3
import sys,os
sys.path.append('../..')
from config import MYSQL_HOST,MYSQL_PORT,MYSQL_USER,MYSQL_PASSWORD,MYSQL_DATABASE
import pymysql

conn=pymysql.connect(host=MYSQL_HOST,port=MYSQL_PORT,user=MYSQL_USER,password=MYSQL_PASSWORD,database=MYSQL_DATABASE)
with conn.cursor() as cursor:
    cursor.execute('DESCRIBE t_user_health_data')
    columns=cursor.fetchall()
    print('t_user_health_data 表结构:')
    for col in columns:
        print(f'- {col[0]} | {col[1]} | {col[2]} | {col[3]}')
conn.close() 