#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查notification_type逻辑问题"""
import mysql.connector

def check_notification_logic():
    """检查数据库中的通知类型配置"""
    print("🔍 检查notification_type逻辑问题")
    
    # 数据库配置
    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'lj-06',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # 查看WEAR_STATUS_CHANGED相关规则
        print("\n📋 查看WEAR_STATUS_CHANGED事件规则:")
        cursor.execute("""
            SELECT id, event_type, rule_type, notification_type, is_active, alert_message
            FROM t_system_event_rule 
            WHERE event_type LIKE '%WEAR_STATUS%' 
            ORDER BY id
        """)
        
        wear_rules = cursor.fetchall()
        if wear_rules:
            for rule in wear_rules:
                print(f"   规则ID={rule['id']}")
                print(f"   事件类型={rule['event_type']}")
                print(f"   通知类型={rule['notification_type']}")
                print(f"   激活状态={rule['is_active']}")
                print(f"   告警消息={rule['alert_message']}")
                print()
        else:
            print("   ❌ 未找到WEAR_STATUS相关规则")
        
        # 查看所有事件规则的notification_type分布
        print("📊 所有事件规则的notification_type分布:")
        cursor.execute("""
            SELECT notification_type, COUNT(*) as count
            FROM t_system_event_rule 
            WHERE is_active = 1
            GROUP BY notification_type
        """)
        
        type_stats = cursor.fetchall()
        for stat in type_stats:
            print(f"   {stat['notification_type']}: {stat['count']}个规则")
        
        # 查看最近的告警记录
        print("\n🚨 查看最近的告警记录:")
        cursor.execute("""
            SELECT id, rule_id, alert_type, device_sn, alert_desc, severity_level,
                   health_id, create_time
            FROM t_alert_info 
            WHERE device_sn = 'CRFTQ23409001890'
            ORDER BY create_time DESC 
            LIMIT 5
        """)
        
        alerts = cursor.fetchall()
        if alerts:
            for alert in alerts:
                print(f"   告警ID={alert['id']}")
                print(f"   规则ID={alert['rule_id']}")
                print(f"   告警类型={alert['alert_type']}")
                print(f"   健康数据ID={alert['health_id']}")
                print(f"   创建时间={alert['create_time']}")
                # 查找对应的规则配置
                cursor.execute("SELECT notification_type FROM t_system_event_rule WHERE id = %s", (alert['rule_id'],))
                rule_config = cursor.fetchone()
                if rule_config:
                    print(f"   对应规则通知类型={rule_config['notification_type']}")
                print()
        else:
            print("   ❌ 未找到告警记录")
        
        # 查看最近的事件处理日志 - 按时间倒序，查看更多细节
        print("\n📝 查看最近的事件处理日志(详细):")
        cursor.execute("""
            SELECT id, device_sn, event_type, rule_id, notification_type, wechat_status, 
                   message_count, process_status, process_details, create_time
            FROM t_system_event_process_log 
            WHERE device_sn = 'CRFTQ23409001890'
            ORDER BY create_time DESC 
            LIMIT 3
        """)
        
        logs = cursor.fetchall()
        if logs:
            for log in logs:
                print(f"   日志ID={log['id']}")
                print(f"   事件类型={log['event_type']}")
                print(f"   规则ID={log['rule_id']}")
                print(f"   通知类型={log['notification_type']}")
                print(f"   微信状态={log['wechat_status']}")
                print(f"   消息数量={log['message_count']}")
                print(f"   处理状态={log['process_status']}")
                print(f"   处理详情={log['process_details']}")
                print(f"   创建时间={log['create_time']}")
                print()
        
        # 检查是否有both类型的规则
        print("🔍 检查是否有both类型的规则:")
        cursor.execute("""
            SELECT id, event_type, rule_type, notification_type, is_active
            FROM t_system_event_rule 
            WHERE notification_type = 'both' AND is_active = 1
        """)
        
        both_rules = cursor.fetchall()
        if both_rules:
            for rule in both_rules:
                print(f"   规则ID={rule['id']}, 事件类型={rule['event_type']}, 通知类型={rule['notification_type']}")
        else:
            print("   ✅ 没有both类型的规则")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_notification_logic() 