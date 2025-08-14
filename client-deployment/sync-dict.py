#!/usr/bin/env python3
import pymysql
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'lj-06',
    'charset': 'utf8mb4'
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def main():
    print("🔄 开始同步告警规则数据字典...")
    conn = get_connection()
    
    try:
        with conn.cursor() as cursor:
            # 获取数据
            cursor.execute("SELECT DISTINCT physical_sign, rule_type FROM t_alert_rules WHERE physical_sign IS NOT NULL AND rule_type IS NOT NULL")
            rules = cursor.fetchall()
            
            physical_signs = {r[0] for r in rules if r[0]}
            rule_types = {r[1] for r in rules if r[1]}
            
            print(f"📋 物理指标: {sorted(physical_signs)}")
            print(f"📋 告警类型: {sorted(rule_types)}")
            
            # 映射表
            sign_map = {
                'heart_rate': '心率',
                'blood_pressure': '血压',
                'temperature': '体温',
                'stress': '压力',
                'blood_oxygen': '血氧'
            }
            
            type_map = {
                'heart_rate': '心率告警',
                'blood_pressure': '血压告警',
                'temperature': '体温告警',
                'stress': '压力告警',
                'blood_oxygen': '血氧告警'
            }
            
            # 确保health_data_type字典存在
            cursor.execute("SELECT id FROM sys_dict WHERE dict_code = 'health_data_type'")
            health_dict = cursor.fetchone()
            if not health_dict:
                cursor.execute("INSERT INTO sys_dict (dict_name, dict_code, description, status, del_flag) VALUES ('健康数据类型', 'health_data_type', '健康数据类型字典', 1, 0)")
                cursor.execute("SELECT LAST_INSERT_ID()")
                health_dict_id = cursor.fetchone()[0]
            else:
                health_dict_id = health_dict[0]
            
            # 确保alert_type字典存在
            cursor.execute("SELECT id FROM sys_dict WHERE dict_code = 'alert_type'")
            alert_dict = cursor.fetchone()
            if not alert_dict:
                cursor.execute("INSERT INTO sys_dict (dict_name, dict_code, description, status, del_flag) VALUES ('告警类型', 'alert_type', '告警类型字典', 1, 0)")
                cursor.execute("SELECT LAST_INSERT_ID()")
                alert_dict_id = cursor.fetchone()[0]
            else:
                alert_dict_id = alert_dict[0]
            
            # 添加物理指标项
            for sign in physical_signs:
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND item_value = %s", (health_dict_id, sign))
                if not cursor.fetchone():
                    display_name = sign_map.get(sign, sign.title())
                    cursor.execute("INSERT INTO sys_dict_item (dict_id, item_text, item_value, status, del_flag) VALUES (%s, %s, %s, 1, 0)", (health_dict_id, display_name, sign))
                    print(f"+ 添加健康数据类型: {sign} -> {display_name}")
            
            # 添加告警类型项
            for rtype in rule_types:
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND item_value = %s", (alert_dict_id, rtype))
                if not cursor.fetchone():
                    display_name = type_map.get(rtype, rtype.title())
                    cursor.execute("INSERT INTO sys_dict_item (dict_id, item_text, item_value, status, del_flag) VALUES (%s, %s, %s, 1, 0)", (alert_dict_id, display_name, rtype))
                    print(f"+ 添加告警类型: {rtype} -> {display_name}")
            
            conn.commit()
            print("✅ 数据字典同步完成!")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 同步失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
