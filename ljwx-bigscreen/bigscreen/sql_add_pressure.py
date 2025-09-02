#!/usr/bin/env python3
"""通过SQL直接添加血压配置"""

import mysql.connector
from mysql.connector import Error

def add_pressure_config_via_sql():
    """通过SQL直接添加血压配置"""
    connection = None
    try:
        # 连接数据库
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='lj-06',  # 修正数据库名
            user='root',
            password='123456'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ 数据库连接成功")
            
            # 检查现有配置
            cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1")
            existing_configs = cursor.fetchall()
            
            print("\n📋 当前配置:")
            for data_type, is_enabled in existing_configs:
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {data_type}: {is_enabled}")
            
            # 添加pressure相关配置
            pressure_configs = [
                ('pressure', True),
                ('pressure_high', True), 
                ('pressure_low', True)
            ]
            
            for data_type, is_enabled in pressure_configs:
                # 检查是否已存在
                cursor.execute(
                    "SELECT id FROM t_health_data_config WHERE customer_id = 1 AND data_type = %s",
                    (data_type,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 更新现有配置
                    cursor.execute(
                        "UPDATE t_health_data_config SET is_enabled = %s WHERE customer_id = 1 AND data_type = %s",
                        (is_enabled, data_type)
                    )
                    print(f"✅ 更新 {data_type} 配置为启用")
                else:
                    # 插入新配置
                    cursor.execute(
                        "INSERT INTO t_health_data_config (customer_id, data_type, is_enabled) VALUES (%s, %s, %s)",
                        (1, data_type, is_enabled)
                    )
                    print(f"➕ 添加 {data_type} 配置")
            
            connection.commit()
            print("\n🎉 血压配置更新成功！")
            
            # 再次查看配置
            cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1 ORDER BY data_type")
            all_configs = cursor.fetchall()
            
            print("\n📋 更新后的配置:")
            for data_type, is_enabled in all_configs:
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {data_type}: {is_enabled}")
                
    except Error as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    add_pressure_config_via_sql() 