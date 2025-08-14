#!/usr/bin/env python3
"""测试数据库连接脚本"""
from config import MYSQL_HOST,MYSQL_PASSWORD,MYSQL_DATABASE #导入配置
import pymysql

def test_db_connection(): #测试数据库连接
    """测试修改后的配置是否能连接数据库"""
    try:
        conn=pymysql.connect(host=MYSQL_HOST,user='root',password=MYSQL_PASSWORD,database=MYSQL_DATABASE,port=3306)
        cursor=conn.cursor()
        
        #检查告警记录数
        cursor.execute('SELECT COUNT(*) FROM t_alert_info')
        count=cursor.fetchone()[0]
        print(f'✅ 数据库连接成功，告警记录数：{count}')
        
        #检查表结构
        cursor.execute('DESCRIBE t_alert_info')
        fields=[row[0] for row in cursor.fetchall()]
        has_user_id='user_id' in fields
        has_org_id='org_id' in fields
        
        print(f'✅ user_id字段存在：{has_user_id}')
        print(f'✅ org_id字段存在：{has_org_id}')
        print(f'📊 配置信息: 主机={MYSQL_HOST}, 数据库={MYSQL_DATABASE}')
        
        conn.close()
        return True
    except Exception as e:
        print(f'❌ 连接失败：{e}')
        return False

if __name__=='__main__':
    test_db_connection() 