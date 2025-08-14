#!/usr/bin/env python3
"""最终修复pressure配置 - 使用正确密码"""

import mysql.connector
from mysql.connector import Error

def fix_pressure_config_final():
    """使用正确密码最终修复pressure配置"""
    connection = None
    try:
        # 使用正确的数据库密码连接 - 修改为127.0.0.1
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            database='lj-06',
            user='root',
            password='123456'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ 数据库连接成功（使用正确密码）")
            
            # 1. 检查当前pressure配置状态
            print("\n🔍 检查当前pressure配置状态:")
            cursor.execute("SELECT customer_id, data_type, is_enabled FROM t_health_data_config WHERE data_type LIKE '%pressure%' ORDER BY customer_id, data_type")
            existing_pressure = cursor.fetchall()
            
            if existing_pressure:
                print("📋 现有pressure配置:")
                for customer_id, data_type, is_enabled in existing_pressure:
                    status = "✅" if is_enabled else "❌"
                    print(f"   {status} Customer {customer_id}: {data_type} = {is_enabled}")
            else:
                print("❌ 没有找到任何pressure配置")
            
            # 2. 获取所有customer_id
            print("\n📊 获取所有customer_id:")
            cursor.execute("SELECT DISTINCT customer_id FROM t_health_data_config ORDER BY customer_id")
            customer_ids = [row[0] for row in cursor.fetchall()]
            print(f"   找到 {len(customer_ids)} 个customer: {customer_ids}")
            
            # 3. 获取heart_rate配置作为参考
            print("\n📋 获取heart_rate配置作为参考:")
            cursor.execute("SELECT customer_id, frequency_interval, is_realtime, is_enabled, is_default FROM t_health_data_config WHERE data_type = 'heart_rate' LIMIT 1")
            heart_rate_config = cursor.fetchone()
            
            if heart_rate_config:
                customer_id, freq_interval, is_realtime, is_enabled, is_default = heart_rate_config
                print(f"   参考配置: frequency_interval={freq_interval}, is_realtime={is_realtime}, is_enabled={is_enabled}, is_default={is_default}")
            else:
                # 默认配置
                freq_interval, is_realtime, is_enabled, is_default = 1800000, 1, 1, 0
                print(f"   使用默认配置: frequency_interval={freq_interval}, is_realtime={is_realtime}, is_enabled={is_enabled}, is_default={is_default}")
            
            # 4. 为每个customer添加pressure配置
            pressure_configs = ['pressure', 'pressure_high', 'pressure_low']
            success_count = 0
            
            for customer_id in customer_ids:
                print(f"\n🔧 为Customer {customer_id} 添加pressure配置:")
                
                for pressure_type in pressure_configs:
                    # 检查是否已存在
                    cursor.execute("SELECT id FROM t_health_data_config WHERE customer_id = %s AND data_type = %s", 
                                 (customer_id, pressure_type))
                    existing = cursor.fetchone()
                    
                    if existing:
                        print(f"   ⚠️ {pressure_type} 已存在 (ID: {existing[0]})")
                        continue
                    
                    # 插入新配置
                    insert_sql = """
                        INSERT INTO t_health_data_config 
                        (customer_id, data_type, frequency_interval, is_realtime, is_enabled, is_default, create_time, update_user) 
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), '管理员')
                    """
                    
                    cursor.execute(insert_sql, (
                        customer_id, 
                        pressure_type, 
                        freq_interval, 
                        is_realtime, 
                        is_enabled, 
                        is_default
                    ))
                    
                    print(f"   ✅ 成功添加 {pressure_type}")
                    success_count += 1
            
            # 5. 提交事务
            connection.commit()
            print(f"\n🎉 成功添加 {success_count} 个pressure配置")
            
            # 6. 验证插入结果
            print("\n🔍 验证插入结果:")
            cursor.execute("SELECT customer_id, data_type, is_enabled FROM t_health_data_config WHERE data_type LIKE '%pressure%' ORDER BY customer_id, data_type")
            final_pressure = cursor.fetchall()
            
            print(f"📊 最终pressure配置总数: {len(final_pressure)}")
            for customer_id, data_type, is_enabled in final_pressure:
                status = "✅" if is_enabled else "❌"
                print(f"   {status} Customer {customer_id}: {data_type} = {is_enabled}")
                
    except Error as e:
        print(f"❌ 数据库操作错误: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    fix_pressure_config_final() 