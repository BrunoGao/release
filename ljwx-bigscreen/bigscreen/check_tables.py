#!/usr/bin/env python3
"""检查数据库表结构"""
import os
os.environ['IS_DOCKER'] = 'false'
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_tables():
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    with conn.cursor() as cursor:
        # 检查所有健康数据相关表
        cursor.execute('SHOW TABLES LIKE "%health%"')
        tables = cursor.fetchall()
        print('健康数据相关表:')
        for table in tables:
            print(f'  {table[0]}')
            # 检查每个表的数据量
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'    数据量: {count}')
        
        # 检查分区表
        cursor.execute('SHOW TABLES LIKE "%partitioned%"')
        partitioned_tables = cursor.fetchall()
        print('\n分区表:')
        for table in partitioned_tables:
            print(f'  {table[0]}')
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'    数据量: {count}')
            
        # 检查每日和每周表
        cursor.execute('SHOW TABLES LIKE "%daily%"')
        daily_tables = cursor.fetchall()
        print('\n每日表:')
        for table in daily_tables:
            print(f'  {table[0]}')
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'    数据量: {count}')
            
        cursor.execute('SHOW TABLES LIKE "%weekly%"')
        weekly_tables = cursor.fetchall()
        print('\n每周表:')
        for table in weekly_tables:
            print(f'  {table[0]}')
            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
            count = cursor.fetchone()[0]
            print(f'    数据量: {count}')
            
        # 检查主表的时间范围
        print('\n主表时间范围分析:')
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM t_user_health_data')
        time_range = cursor.fetchone()
        print(f'  时间范围: {time_range[0]} ~ {time_range[1]}')
        
        # 检查2025年2-5月的数据
        cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE timestamp BETWEEN '2025-02-01' AND '2025-05-28' AND org_id = 1")
        count_2025 = cursor.fetchone()[0]
        print(f'  2025年2-5月org_id=1数据: {count_2025}')
        
        # 检查分区表是否有2025年数据
        if partitioned_tables:
            for table in partitioned_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]} WHERE timestamp BETWEEN '2025-02-01' AND '2025-05-28' AND org_id = 1")
                    count_part = cursor.fetchone()[0]
                    print(f'  {table[0]}中2025年2-5月org_id=1数据: {count_part}')
                except Exception as e:
                    print(f'  {table[0]}查询失败: {e}')
    
    conn.close()

if __name__ == "__main__":
    check_tables() 