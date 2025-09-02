#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置测试用的系统事件规则"""
import mysql.connector

def setup_test_event_rules():
    """设置测试用的系统事件规则"""
    try:
        # 数据库连接配置
        db_config={
            'host':'127.0.0.1',
            'port':3306,
            'user':'root',
            'password':'123456',
            'database':'lj-06',
            'charset':'utf8mb4'
        }
        
        conn=mysql.connector.connect(**db_config)
        cursor=conn.cursor()
        
        print("🔧 检查现有系统事件规则...")
        
        # 显示所有活跃规则
        cursor.execute("""
            SELECT id,event_type,rule_type,alert_message,severity_level,notification_type
            FROM t_system_event_rule 
            WHERE is_active=1
            ORDER BY id
        """)
        rules=cursor.fetchall()
        
        print(f"\n📋 当前活跃的事件规则({len(rules)}条):")
        for rule in rules:
            print(f"   ID:{rule[0]}, 事件:{rule[1]}, 规则:{rule[2]}")
            print(f"   消息:{rule[3]}, 级别:{rule[4]}, 通知:{rule[5]}")
            print("   ---")
        
        # 检查我们需要的测试规则是否存在
        needed_rules=['HEARTRATE_HIGH_ALERT','SOS_EVENT','FALLDOWN_EVENT']
        existing_rules=[rule[1] for rule in rules]
        
        print(f"\n🔍 检查测试所需规则:")
        for needed in needed_rules:
            if needed in existing_rules:
                print(f"   ✅ {needed} - 已存在")
            else:
                print(f"   ❌ {needed} - 不存在")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 检查事件规则失败:{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__=="__main__":
    print("🚀 检查系统事件规则配置")
    success=setup_test_event_rules()
    if success:
        print("🎯 规则检查完成")
    else:
        print("💀 规则检查失败") 