#!/usr/bin/env python3
"""详细调试配置加载过程"""

import mysql.connector
from mysql.connector import Error

def debug_config_loading():
    """调试配置加载过程"""
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
            
            # 1. 查看所有customer_id=1的配置
            print("\n📋 customer_id=1的所有配置:")
            cursor.execute("SELECT data_type, is_enabled FROM t_health_data_config WHERE customer_id = 1 ORDER BY data_type")
            all_configs = cursor.fetchall()
            
            config_dict = {}
            for data_type, is_enabled in all_configs:
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {data_type}: {is_enabled}")
                config_dict[data_type] = is_enabled
            
            # 2. 模拟get_health_data_config_by_org函数逻辑
            print(f"\n🔧 模拟配置加载函数:")
            enabled_metrics = [metric for metric, enabled in config_dict.items() if enabled]
            print(f"   启用的指标: {enabled_metrics}")
            
            # 3. 检查pressure相关配置
            pressure_configs = ['pressure', 'pressure_high', 'pressure_low']
            print(f"\n🩺 pressure相关配置:")
            for p_config in pressure_configs:
                is_enabled = config_dict.get(p_config, False)
                status = "✅" if is_enabled else "❌"
                print(f"   {status} {p_config}: {is_enabled}")
            
            # 4. 检查是否有重复配置
            print(f"\n🔍 检查重复配置:")
            cursor.execute("SELECT data_type, COUNT(*) as count FROM t_health_data_config WHERE customer_id = 1 GROUP BY data_type HAVING count > 1")
            duplicates = cursor.fetchall()
            
            if duplicates:
                for data_type, count in duplicates:
                    print(f"   ⚠️ 重复配置: {data_type} (数量: {count})")
                    # 显示重复配置的详细信息
                    cursor.execute("SELECT id, data_type, is_enabled, create_time FROM t_health_data_config WHERE customer_id = 1 AND data_type = %s ORDER BY create_time", (data_type,))
                    details = cursor.fetchall()
                    for detail in details:
                        print(f"      ID: {detail[0]}, 启用: {detail[2]}, 创建时间: {detail[3]}")
            else:
                print("   ✅ 没有重复配置")
            
            # 5. 检查pressure配置的创建时间
            print(f"\n⏰ pressure配置的创建时间:")
            cursor.execute("SELECT data_type, is_enabled, create_time FROM t_health_data_config WHERE customer_id = 1 AND data_type LIKE '%pressure%' ORDER BY create_time")
            pressure_times = cursor.fetchall()
            
            for data_type, is_enabled, create_time in pressure_times:
                print(f"   {data_type}: 启用={is_enabled}, 创建时间={create_time}")
                
    except Error as e:
        print(f"❌ 数据库错误: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    debug_config_loading() 