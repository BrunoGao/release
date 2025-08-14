#!/usr/bin/env python3
"""检查数据库表结构"""
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='lj-06'
    )

def check_table_structure():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables_to_check = [
        't_alert_info',
        't_device_message', 
        't_system_event_rule',
        't_user_health_data'
    ]
    
    print("🔍 数据库表结构检查")
    print("="*60)
    
    for table in tables_to_check:
        try:
            print(f"\n📋 表: {table}")
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            
            if columns:
                print("   字段结构:")
                for col in columns:
                    field, type_info, null, key, default, extra = col
                    print(f"   - {field}: {type_info} {key} {null}")
            else:
                print("   ❌ 表不存在或无字段")
                
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
    
    # 检查最近的数据
    print(f"\n📊 最近数据检查:")
    
    # 检查告警表
    try:
        cursor.execute("SELECT * FROM t_alert_info ORDER BY id DESC LIMIT 3")
        alerts = cursor.fetchall()
        print(f"   告警记录: {len(alerts)} 条")
        for alert in alerts:
            print(f"   - {alert}")
    except Exception as e:
        print(f"   告警记录查询失败: {e}")
    
    # 检查消息表
    try:
        cursor.execute("SELECT * FROM t_device_message ORDER BY id DESC LIMIT 3")  
        messages = cursor.fetchall()
        print(f"   设备消息: {len(messages)} 条")
        for msg in messages:
            print(f"   - {msg}")
    except Exception as e:
        print(f"   设备消息查询失败: {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_table_structure() 