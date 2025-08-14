#!/usr/bin/env python3
"""检查分区视图定义"""
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

def check_partition_view():
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print('📊 检查分区视图定义:')
            cursor.execute('SHOW CREATE VIEW t_user_health_data_partitioned')
            result = cursor.fetchone()
            print('分区视图定义:')
            print(result[1])
            
            print('\n📊 检查各个分区表的数据:')
            # 检查各个月度分区表
            partition_tables = [
                't_user_health_data_202411',
                't_user_health_data_202412', 
                't_user_health_data_202501',
                't_user_health_data_202502',
                't_user_health_data_202503',
                't_user_health_data_202504',
                't_user_health_data_202505'
            ]
            
            for table in partition_tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE org_id = 2')
                    count = cursor.fetchone()[0]
                    print(f'{table}: {count}条数据')
                except Exception as e:
                    print(f'{table}: 表不存在或查询失败 - {e}')
                    
            print('\n📊 检查主表最新数据的时间分布:')
            cursor.execute("""
                SELECT DATE_FORMAT(timestamp, '%Y-%m') as month, COUNT(*) as count
                FROM t_user_health_data 
                WHERE org_id = 2 
                GROUP BY DATE_FORMAT(timestamp, '%Y-%m')
                ORDER BY month DESC
            """)
            month_data = cursor.fetchall()
            for row in month_data:
                print(f'{row[0]}: {row[1]}条数据')
                
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_partition_view() 