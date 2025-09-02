#!/usr/bin/env python3
"""检查查询数据问题"""
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_query_data():
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print('📊 检查组织ID=2的数据:')
            cursor.execute("""
                SELECT COUNT(*) FROM t_user_health_data 
                WHERE org_id = 2 
                AND timestamp >= '2025-02-01' 
                AND timestamp <= '2025-05-28'
            """)
            count = cursor.fetchone()[0]
            print(f'组织ID=2在时间范围内的数据: {count}条')
            
            print('\n📊 检查设备CRFTQ23409001890的数据:')
            cursor.execute("""
                SELECT user_id, org_id, timestamp, heart_rate, blood_oxygen 
                FROM t_user_health_data 
                WHERE device_sn = 'CRFTQ23409001890' 
                ORDER BY create_time DESC 
                LIMIT 5
            """)
            data = cursor.fetchall()
            for row in data:
                print(f'用户ID:{row[0]}, 组织ID:{row[1]}, 时间:{row[2]}, 心率:{row[3]}, 血氧:{row[4]}')
                
            print('\n📊 检查分区视图是否存在:')
            cursor.execute("SHOW TABLES LIKE 't_user_health_data_partitioned'")
            partitioned_exists = cursor.fetchone()
            print(f'分区视图存在: {bool(partitioned_exists)}')
            
            if partitioned_exists:
                print('\n📊 检查分区视图中组织ID=2的数据:')
                cursor.execute("""
                    SELECT COUNT(*) FROM t_user_health_data_partitioned 
                    WHERE org_id = 2 
                    AND timestamp >= '2025-02-01' 
                    AND timestamp <= '2025-05-28'
                """)
                partition_count = cursor.fetchone()[0]
                print(f'分区视图中组织ID=2的数据: {partition_count}条')
            
            print('\n📊 检查最近上传的数据:')
            cursor.execute("""
                SELECT device_sn, user_id, org_id, timestamp, heart_rate, blood_oxygen
                FROM t_user_health_data 
                WHERE create_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY create_time DESC
                LIMIT 10
            """)
            recent_data = cursor.fetchall()
            print(f'最近1小时上传的数据: {len(recent_data)}条')
            for row in recent_data:
                print(f'  设备:{row[0]}, 用户ID:{row[1]}, 组织ID:{row[2]}, 时间:{row[3]}, 心率:{row[4]}, 血氧:{row[5]}')
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_query_data() 