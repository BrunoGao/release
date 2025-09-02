#!/usr/bin/env python3
"""为所有customer添加pressure配置"""

import mysql.connector
from mysql.connector import Error

def fix_pressure_config_for_all_customers():
    """为所有customer添加pressure配置，参考heart_rate配置"""
    connection = None
    try:
        # 连接数据库
        connection = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='lj-06',
            user='root',
            password='123456'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ 数据库连接成功")
            
            # 1. 查看所有customer_id
            cursor.execute("SELECT DISTINCT customer_id FROM t_health_data_config ORDER BY customer_id")
            customer_ids = [row[0] for row in cursor.fetchall()]
            print(f"\n📋 找到的customer_id: {customer_ids}")
            
            # 2. 查看heart_rate的配置作为参考
            cursor.execute("SELECT customer_id, data_type, is_enabled FROM t_health_data_config WHERE data_type = 'heart_rate'")
            heart_rate_configs = cursor.fetchall()
            print(f"\n❤️ heart_rate配置参考:")
            for customer_id, data_type, is_enabled in heart_rate_configs:
                print(f"   customer_id: {customer_id}, is_enabled: {is_enabled}")
            
            # 3. 为每个customer添加pressure配置
            total_added = 0
            total_updated = 0
            
            for customer_id in customer_ids:
                print(f"\n🔧 处理customer_id: {customer_id}")
                
                # 检查是否已存在pressure配置
                cursor.execute(
                    "SELECT id, is_enabled FROM t_health_data_config WHERE customer_id = %s AND data_type = 'pressure'",
                    (customer_id,)
                )
                existing_pressure = cursor.fetchone()
                
                if existing_pressure:
                    # 更新现有配置为启用
                    cursor.execute(
                        "UPDATE t_health_data_config SET is_enabled = TRUE WHERE customer_id = %s AND data_type = 'pressure'",
                        (customer_id,)
                    )
                    print(f"   ✅ 更新pressure配置为启用")
                    total_updated += 1
                else:
                    # 添加新的pressure配置，参考heart_rate的启用状态
                    cursor.execute(
                        "SELECT is_enabled FROM t_health_data_config WHERE customer_id = %s AND data_type = 'heart_rate'",
                        (customer_id,)
                    )
                    heart_rate_enabled = cursor.fetchone()
                    
                    # 默认启用pressure，如果heart_rate存在则参考其状态
                    is_enabled = heart_rate_enabled[0] if heart_rate_enabled else True
                    
                    cursor.execute(
                        "INSERT INTO t_health_data_config (customer_id, data_type, is_enabled) VALUES (%s, %s, %s)",
                        (customer_id, 'pressure', is_enabled)
                    )
                    print(f"   ➕ 添加pressure配置，启用状态: {is_enabled}")
                    total_added += 1
                
                # 同时检查并添加pressure_high和pressure_low配置（用于直接查询）
                for pressure_field in ['pressure_high', 'pressure_low']:
                    cursor.execute(
                        "SELECT id FROM t_health_data_config WHERE customer_id = %s AND data_type = %s",
                        (customer_id, pressure_field)
                    )
                    existing_field = cursor.fetchone()
                    
                    if not existing_field:
                        cursor.execute(
                            "INSERT INTO t_health_data_config (customer_id, data_type, is_enabled) VALUES (%s, %s, %s)",
                            (customer_id, pressure_field, True)
                        )
                        print(f"   ➕ 添加{pressure_field}配置")
            
            connection.commit()
            print(f"\n🎉 配置更新完成！")
            print(f"📊 统计: 新增{total_added}个pressure配置, 更新{total_updated}个pressure配置")
            
            # 4. 验证所有customer的pressure配置
            print(f"\n📋 验证所有customer的pressure配置:")
            cursor.execute("""
                SELECT customer_id, data_type, is_enabled 
                FROM t_health_data_config 
                WHERE data_type IN ('pressure', 'pressure_high', 'pressure_low') 
                ORDER BY customer_id, data_type
            """)
            
            all_pressure_configs = cursor.fetchall()
            current_customer = None
            
            for customer_id, data_type, is_enabled in all_pressure_configs:
                if customer_id != current_customer:
                    print(f"\n   Customer {customer_id}:")
                    current_customer = customer_id
                
                status = "✅" if is_enabled else "❌"
                print(f"     {status} {data_type}: {is_enabled}")
                
    except Error as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    fix_pressure_config_for_all_customers() 