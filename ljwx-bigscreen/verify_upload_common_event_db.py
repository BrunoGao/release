#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接验证upload_common_event功能的数据库脚本"""
import mysql.connector
from datetime import datetime,timedelta

def verify_upload_common_event_data():
    """验证upload_common_event在数据库中的数据"""
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
        cursor=conn.cursor(dictionary=True)
        
        device_sn='A5GTQ24603000537'
        
        print("🔍 验证upload_common_event接口数据插入情况")
        print(f"📱 目标设备: {device_sn}")
        
        # 查询最近24小时的健康数据记录
        print("\n🩺 查询最近24小时的健康数据记录...")
        cursor.execute("""
            SELECT id,device_sn,timestamp,heart_rate,blood_oxygen,temperature,user_id,org_id,upload_method
            FROM t_user_health_data 
            WHERE device_sn = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY id DESC LIMIT 10
        """,(device_sn,))
        health_records=cursor.fetchall()
        
        if health_records:
            print(f"✅ 找到{len(health_records)}条健康数据记录:")
            for record in health_records:
                upload_method=record.get('upload_method','未知')
                print(f"   ID:{record['id']}, 时间:{record['timestamp']}, 心率:{record['heart_rate']}")
                print(f"   体温:{record['temperature']}, 血氧:{record['blood_oxygen']}")
                print(f"   上传方式:{upload_method}, 用户ID:{record['user_id']}, 组织ID:{record['org_id']}")
        else:
            print("❌ 未找到最近24小时的健康数据记录")
        
        # 查询最近24小时的告警记录
        print("\n🚨 查询最近24小时的告警记录...")
        cursor.execute("""
            SELECT id,alert_type,device_sn,alert_desc,severity_level,health_id,user_id,org_id,alert_timestamp
            FROM t_alert_info 
            WHERE device_sn = %s AND alert_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY id DESC LIMIT 10
        """,(device_sn,))
        alert_records=cursor.fetchall()
        
        if alert_records:
            print(f"✅ 找到{len(alert_records)}条告警记录:")
            for record in alert_records:
                health_status="有关联" if record['health_id'] else "无关联"
                print(f"   ID:{record['id']}, 类型:{record['alert_type']}, 时间:{record['alert_timestamp']}")
                print(f"   健康ID:{record['health_id']} ({health_status}), 描述:{record['alert_desc']}")
                print(f"   级别:{record['severity_level']}, 用户ID:{record['user_id']}")
        else:
            print("❌ 未找到最近24小时的告警记录")
        
        # 查询最近24小时的设备消息记录
        print("\n💬 查询最近24小时的设备消息记录...")
        cursor.execute("""
            SELECT id,device_sn,message,message_type,create_time
            FROM t_device_message 
            WHERE device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY id DESC LIMIT 10
        """,(device_sn,))
        message_records=cursor.fetchall()
        
        if message_records:
            print(f"✅ 找到{len(message_records)}条设备消息记录:")
            for record in message_records:
                print(f"   ID:{record['id']}, 消息:{record['message']}")
                print(f"   时间:{record['create_time']}")
                print(f"   消息类型:{record['message_type']}")
        else:
            print("❌ 未找到最近24小时的设备消息记录")
        
        # 查询事件处理队列状态
        print("\n📊 查询最近24小时的事件队列状态...")
        cursor.execute("""
            SELECT processing_status,event_type,event_value,create_time,COUNT(*) as count 
            FROM t_event_alarm_queue 
            WHERE device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY processing_status,event_type,event_value
            ORDER BY create_time DESC
        """,(device_sn,))
        queue_status=cursor.fetchall()
        
        if queue_status:
            print("📈 队列状态统计:")
            for status in queue_status:
                print(f"   {status['processing_status']}: {status['count']}条")
                print(f"   事件类型:{status['event_type']}, 事件值:{status['event_value']}")
                print(f"   创建时间:{status['create_time']}")
        else:
            print("📊 队列中无最近24小时相关记录")
        
        # 分析关联性
        print("\n🔗 分析数据关联性...")
        if health_records and alert_records:
            health_linked_alerts=[r for r in alert_records if r['health_id']]
            unlinked_alerts=[r for r in alert_records if not r['health_id']]
            
            print(f"   ✅ 有health_id关联的告警: {len(health_linked_alerts)}条")
            print(f"   ⚠️  无health_id关联的告警: {len(unlinked_alerts)}条")
            
            for linked in health_linked_alerts:
                matching_health=[h for h in health_records if h['id']==linked['health_id']]
                if matching_health:
                    print(f"   🔗 告警ID:{linked['id']} ↔ 健康数据ID:{linked['health_id']}")
        
        cursor.close()
        conn.close()
        
        # 生成测试总结
        print("\n📋 验证结果总结:")
        has_health_data=len(health_records)>0 if health_records else False
        has_alerts=len(alert_records)>0 if alert_records else False
        has_messages=len(message_records)>0 if message_records else False
        has_queue_data=len(queue_status)>0 if queue_status else False
        
        if has_health_data:
            print("✅ 健康数据插入功能正常")
        else:
            print("❌ 健康数据插入可能有问题")
            
        if has_alerts:
            print("✅ 告警记录插入功能正常")
            if health_records and alert_records:
                health_linked_count=len([r for r in alert_records if r['health_id']])
                if health_linked_count>0:
                    print(f"✅ health_id关联功能正常({health_linked_count}条关联)")
                else:
                    print("⚠️  health_id关联可能有问题")
        else:
            print("❌ 告警记录插入可能有问题")
            
        if has_messages:
            print("✅ 设备消息插入功能正常")
        else:
            print("⚠️  设备消息插入可能有问题")
            
        if has_queue_data:
            print("✅ 事件队列处理功能正常")
        else:
            print("⚠️  事件队列处理可能有问题")
        
        # 检查事件规则配置
        print("\n🔧 检查相关事件规则...")
        cursor=mysql.connector.connect(**db_config).cursor(dictionary=True)
        cursor.execute("""
            SELECT id,event_type,rule_type,alert_message,severity_level,notification_type,is_active
            FROM t_system_event_rule 
            WHERE is_active=1 AND (event_type LIKE '%HEARTRATE_HIGH_ALERT%' OR event_type LIKE '%SOS_EVENT%')
            ORDER BY id
        """)
        active_rules=cursor.fetchall()
        
        if active_rules:
            print(f"✅ 找到{len(active_rules)}条活跃的相关事件规则")
            for rule in active_rules:
                print(f"   规则ID:{rule['id']}, 类型:{rule['rule_type']}")
                print(f"   通知方式:{rule['notification_type']}, 级别:{rule['severity_level']}")
        else:
            print("❌ 未找到活跃的相关事件规则")
        
        cursor.close()
        
        return {
            'health_data_count':len(health_records) if health_records else 0,
            'alert_count':len(alert_records) if alert_records else 0,
            'message_count':len(message_records) if message_records else 0,
            'queue_count':len(queue_status) if queue_status else 0,
            'active_rules_count':len(active_rules) if active_rules else 0
        }
        
    except Exception as e:
        print(f"❌ 数据库验证失败:{e}")
        import traceback
        traceback.print_exc()
        return None

if __name__=="__main__":
    print("🚀 开始upload_common_event数据库验证")
    result=verify_upload_common_event_data()
    if result:
        print(f"\n🎯 验证完成 - 健康数据:{result['health_data_count']}, 告警:{result['alert_count']}, 消息:{result['message_count']}, 队列:{result['queue_count']}, 规则:{result['active_rules_count']}")
    else:
        print("\n💀 验证失败") 