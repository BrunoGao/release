#!/usr/bin/env python3
import pymysql
from datetime import datetime
import random

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'lj-06',
    'charset': 'utf8mb4'
}

def generate_id():
    return int(datetime.now().timestamp() * 1000000) + random.randint(1000, 9999)

def main():
    print("🔄 开始同步告警规则数据字典...")
    conn = pymysql.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cursor:
            # 获取数据
            cursor.execute("SELECT DISTINCT physical_sign, rule_type FROM t_alert_rules WHERE physical_sign IS NOT NULL AND rule_type IS NOT NULL")
            rules = cursor.fetchall()
            
            # 只处理missing的项目
            missing_physical = ['event', 'work_out']  # 确定缺少的项
            missing_alert = ['BOOT_COMPLETED', 'CALL_STATE', 'COMMON_EVENT', 'FALLDOWN_EVENT', 'FUN_DOUBLE_CLICK', 
                           'HEARTRATE_HIGH_ALERT', 'HEARTRATE_LOW_ALERT', 'PRESSURE_HIGH_ALERT', 'PRESSURE_LOW_ALERT', 
                           'SOS_EVENT', 'SPO2_LOW_ALERT', 'STRESS_HIGH_ALERT', 'TEMPERATURE_HIGH_ALERT', 
                           'TEMPERATURE_LOW_ALERT', 'UI_SETTINGS_CHANGED', 'WEAR_STATUS_CHANGED', 'fall_down', 'one_key_alarm']
            
            # 名称映射
            physical_map = {'event': '事件', 'work_out': '运动'}
            alert_map = {
                'BOOT_COMPLETED': '设备启动完成', 'CALL_STATE': '通话状态', 'COMMON_EVENT': '通用事件',
                'FALLDOWN_EVENT': '跌倒事件', 'FUN_DOUBLE_CLICK': '功能双击', 'HEARTRATE_HIGH_ALERT': '心率高告警',
                'HEARTRATE_LOW_ALERT': '心率低告警', 'PRESSURE_HIGH_ALERT': '血压高告警', 'PRESSURE_LOW_ALERT': '血压低告警',
                'SOS_EVENT': 'SOS紧急事件', 'SPO2_LOW_ALERT': '血氧低告警', 'STRESS_HIGH_ALERT': '压力高告警',
                'TEMPERATURE_HIGH_ALERT': '体温高告警', 'TEMPERATURE_LOW_ALERT': '体温低告警',
                'UI_SETTINGS_CHANGED': 'UI设置变化', 'WEAR_STATUS_CHANGED': '佩戴状态变化',
                'fall_down': '跌倒告警', 'one_key_alarm': '一键报警'
            }
            
            # 获取字典ID
            cursor.execute("SELECT id FROM sys_dict WHERE code = 'health_data_type'")
            health_dict_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT id FROM sys_dict WHERE code = 'alert_type'")
            alert_dict_id = cursor.fetchone()[0]
            
            # 添加缺失的physical_sign项
            for sign in missing_physical:
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND value = %s", (health_dict_id, sign))
                if not cursor.fetchone():
                    item_id = generate_id()
                    zh_name = physical_map.get(sign, sign)
                    cursor.execute("""INSERT INTO sys_dict_item 
                                     (id, dict_id, dict_code, value, zh_cn, type, sort, description, create_user, create_user_id, create_time, status, is_deleted) 
                                     VALUES (%s, %s, 'health_data_type', %s, %s, '1', 1, '从告警规则同步', 'system_sync', 1, %s, '1', 0)""", 
                                  (item_id, health_dict_id, sign, zh_name, datetime.now()))
                    print(f"+ 添加健康数据类型: {sign} -> {zh_name}")
            
            # 添加缺失的rule_type项
            for rtype in missing_alert:
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND value = %s", (alert_dict_id, rtype))
                if not cursor.fetchone():
                    item_id = generate_id()
                    zh_name = alert_map.get(rtype, rtype)
                    cursor.execute("""INSERT INTO sys_dict_item 
                                     (id, dict_id, dict_code, value, zh_cn, type, sort, description, create_user, create_user_id, create_time, status, is_deleted) 
                                     VALUES (%s, %s, 'alert_type', %s, %s, '1', 1, '从告警规则同步', 'system_sync', 1, %s, '1', 0)""", 
                                  (item_id, alert_dict_id, rtype, zh_name, datetime.now()))
                    print(f"+ 添加告警类型: {rtype} -> {zh_name}")
            
            conn.commit()
            print("✅ 数据字典更新完成!")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 同步失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
