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

def main():
    print("🔄 开始同步告警规则数据字典...")
    conn = pymysql.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cursor:
            # 获取告警规则数据
            cursor.execute("SELECT DISTINCT physical_sign, rule_type FROM t_alert_rules WHERE physical_sign IS NOT NULL AND rule_type IS NOT NULL")
            rules = cursor.fetchall()
            
            physical_signs = {r[0] for r in rules if r[0]}
            rule_types = {r[1] for r in rules if r[1]}
            
            print(f"📋 物理指标({len(physical_signs)}个): {sorted(physical_signs)}")
            print(f"📋 告警类型({len(rule_types)}个): {sorted(rule_types)}")
            
            # 中文名称映射
            physical_sign_map = {
                'heart_rate': '心率',
                'blood_pressure': '血压',
                'temperature': '体温',
                'stress': '压力',
                'blood_oxygen': '血氧',
                'sleep': '睡眠',
                'all': '全部指标',
                'event': '事件',
                'work_out': '运动'
            }
            
            rule_type_map = {
                'heart_rate': '心率告警',
                'blood_pressure': '血压告警',
                'temperature': '体温告警',
                'stress': '压力告警',
                'blood_oxygen': '血氧告警',
                'sleep': '睡眠告警',
                'fall_down': '跌倒告警',
                'one_key_alarm': '一键报警',
                'SOS_EVENT': 'SOS紧急事件',
                'FALLDOWN_EVENT': '跌倒事件',
                'COMMON_EVENT': '通用事件',
                'HEARTRATE_HIGH_ALERT': '心率高告警',
                'HEARTRATE_LOW_ALERT': '心率低告警',
                'PRESSURE_HIGH_ALERT': '血压高告警',
                'PRESSURE_LOW_ALERT': '血压低告警',
                'SPO2_LOW_ALERT': '血氧低告警',
                'STRESS_HIGH_ALERT': '压力高告警',
                'TEMPERATURE_HIGH_ALERT': '体温高告警',
                'TEMPERATURE_LOW_ALERT': '体温低告警',
                'WEAR_STATUS_CHANGED': '佩戴状态变化',
                'UI_SETTINGS_CHANGED': 'UI设置变化',
                'BOOT_COMPLETED': '设备启动完成',
                'CALL_STATE': '通话状态',
                'FUN_DOUBLE_CLICK': '功能双击'
            }
            
            # 1. 确保health_data_type字典存在
            cursor.execute("SELECT id FROM sys_dict WHERE code = 'health_data_type' AND is_deleted = 0")
            health_dict = cursor.fetchone()
            if not health_dict:
                cursor.execute("""INSERT INTO sys_dict (name, code, type, sort, description, create_user, create_time, status, is_deleted) 
                                 VALUES ('健康数据类型', 'health_data_type', '1', 1, '健康数据类型字典', 'system_sync', %s, '1', 0)""", (datetime.now(),))
                cursor.execute("SELECT LAST_INSERT_ID()")
                health_dict_id = cursor.fetchone()[0]
                print("✅ 创建健康数据类型字典")
            else:
                health_dict_id = health_dict[0]
            
            # 2. 确保alert_type字典存在
            cursor.execute("SELECT id FROM sys_dict WHERE code = 'alert_type' AND is_deleted = 0")
            alert_dict = cursor.fetchone()
            if not alert_dict:
                cursor.execute("""INSERT INTO sys_dict (name, code, type, sort, description, create_user, create_time, status, is_deleted) 
                                 VALUES ('告警类型', 'alert_type', '1', 2, '告警类型字典', 'system_sync', %s, '1', 0)""", (datetime.now(),))
                cursor.execute("SELECT LAST_INSERT_ID()")
                alert_dict_id = cursor.fetchone()[0]
                print("✅ 创建告警类型字典")
            else:
                alert_dict_id = alert_dict[0]
            
            # 3. 添加物理指标字典项
            new_physical_count = 0
            for sign in sorted(physical_signs):
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND value = %s AND is_deleted = 0", (health_dict_id, sign))
                if not cursor.fetchone():
                    zh_name = physical_sign_map.get(sign, sign.replace('_', ' ').title())
                    cursor.execute("""INSERT INTO sys_dict_item (dict_id, dict_code, value, zh_cn, type, sort, description, create_user, create_time, status, is_deleted) 
                                     VALUES (%s, 'health_data_type', %s, %s, '1', %s, '从告警规则同步', 'system_sync', %s, '1', 0)""", 
                                  (health_dict_id, sign, zh_name, new_physical_count + 1, datetime.now()))
                    print(f"  + 添加健康数据类型: {sign} -> {zh_name}")
                    new_physical_count += 1
                else:
                    print(f"  ✓ 已存在健康数据类型: {sign}")
            
            # 4. 添加告警类型字典项
            new_alert_count = 0
            for rtype in sorted(rule_types):
                cursor.execute("SELECT id FROM sys_dict_item WHERE dict_id = %s AND value = %s AND is_deleted = 0", (alert_dict_id, rtype))
                if not cursor.fetchone():
                    zh_name = rule_type_map.get(rtype, rtype.replace('_', ' ').title())
                    cursor.execute("""INSERT INTO sys_dict_item (dict_id, dict_code, value, zh_cn, type, sort, description, create_user, create_time, status, is_deleted) 
                                     VALUES (%s, 'alert_type', %s, %s, '1', %s, '从告警规则同步', 'system_sync', %s, '1', 0)""", 
                                  (alert_dict_id, rtype, zh_name, new_alert_count + 1, datetime.now()))
                    print(f"  + 添加告警类型: {rtype} -> {zh_name}")
                    new_alert_count += 1
                else:
                    print(f"  ✓ 已存在告警类型: {rtype}")
            
            conn.commit()
            print(f"\n🎉 数据字典同步完成!")
            print(f"📈 新增健康数据类型: {new_physical_count} 项")
            print(f"📈 新增告警类型: {new_alert_count} 项")
            print(f"💡 前端页面现在应该可以正确显示字典项了")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 同步失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
