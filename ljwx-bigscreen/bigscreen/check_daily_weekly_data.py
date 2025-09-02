#!/usr/bin/env python3
"""检查每日表和每周表数据"""
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_daily_weekly_data():
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print('📊 检查每日表数据:')
            cursor.execute('SELECT COUNT(*) FROM t_user_health_data_daily WHERE device_sn = "CRFTQ23409001890"')
            daily_count = cursor.fetchone()[0]
            print(f'每日表数据: {daily_count}条')
            
            if daily_count > 0:
                cursor.execute("""
                    SELECT date, sleep_data, exercise_daily_data, workout_data 
                    FROM t_user_health_data_daily 
                    WHERE device_sn = "CRFTQ23409001890" 
                    ORDER BY date DESC 
                    LIMIT 3
                """)
                daily_data = cursor.fetchall()
                for row in daily_data:
                    sleep_preview = row[1][:50] + '...' if row[1] and len(row[1]) > 50 else row[1]
                    exercise_preview = row[2][:30] + '...' if row[2] and len(row[2]) > 30 else row[2]
                    print(f'  日期:{row[0]}, 睡眠:{sleep_preview}, 运动:{exercise_preview}')
            
            print('\n📊 检查每周表数据:')
            cursor.execute('SELECT COUNT(*) FROM t_user_health_data_weekly WHERE device_sn = "CRFTQ23409001890"')
            weekly_count = cursor.fetchone()[0]
            print(f'每周表数据: {weekly_count}条')
            
            if weekly_count > 0:
                cursor.execute("""
                    SELECT week_start, exercise_week_data 
                    FROM t_user_health_data_weekly 
                    WHERE device_sn = "CRFTQ23409001890" 
                    ORDER BY week_start DESC 
                    LIMIT 3
                """)
                weekly_data = cursor.fetchall()
                for row in weekly_data:
                    week_preview = row[1][:50] + '...' if row[1] and len(row[1]) > 50 else row[1]
                    print(f'  周开始:{row[0]}, 每周运动:{week_preview}')
            
            # 检查表结构
            print('\n📊 检查每日表结构:')
            cursor.execute('DESCRIBE t_user_health_data_daily')
            daily_columns = cursor.fetchall()
            daily_field_names = [col[0] for col in daily_columns]
            print(f'每日表字段: {daily_field_names}')
            
            print('\n📊 检查每周表结构:')
            cursor.execute('DESCRIBE t_user_health_data_weekly')
            weekly_columns = cursor.fetchall()
            weekly_field_names = [col[0] for col in weekly_columns]
            print(f'每周表字段: {weekly_field_names}')
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_daily_weekly_data() 