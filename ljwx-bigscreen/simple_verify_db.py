#!/usr/bin/env python3
"""简化的upload_common_event数据库验证脚本"""
import mysql.connector

def verify_data():
    try:
        conn=mysql.connector.connect(host='127.0.0.1',port=3306,user='root',password='123456',database='lj-06',charset='utf8mb4')
        cursor=conn.cursor(dictionary=True)
        
        device_sn='A5GTQ24603000537'
        print(f"📱 验证设备: {device_sn}")
        
        # 查询健康数据
        cursor.execute("SELECT COUNT(*) as count FROM t_user_health_data WHERE device_sn = %s AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",(device_sn,))
        health_count=cursor.fetchone()['count']
        print(f"🩺 24小时内健康数据: {health_count}条")
        
        # 查询告警记录
        cursor.execute("SELECT COUNT(*) as count FROM t_alert_info WHERE device_sn = %s AND alert_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",(device_sn,))
        alert_count=cursor.fetchone()['count']
        print(f"🚨 24小时内告警记录: {alert_count}条")
        
        # 查询设备消息
        cursor.execute("SELECT COUNT(*) as count FROM t_device_message WHERE device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",(device_sn,))
        message_count=cursor.fetchone()['count']
        print(f"💬 24小时内设备消息: {message_count}条")
        
        # 查询队列记录
        cursor.execute("SELECT COUNT(*) as count FROM t_event_alarm_queue WHERE device_sn = %s AND create_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",(device_sn,))
        queue_count=cursor.fetchone()['count']
        print(f"📊 24小时内队列记录: {queue_count}条")
        
        # 查询有health_id关联的告警
        cursor.execute("SELECT COUNT(*) as count FROM t_alert_info WHERE device_sn = %s AND health_id IS NOT NULL AND alert_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)",(device_sn,))
        linked_alert_count=cursor.fetchone()['count']
        print(f"🔗 24小时内关联健康数据的告警: {linked_alert_count}条")
        
        # 查询事件规则
        cursor.execute("SELECT COUNT(*) as count FROM t_system_event_rule WHERE is_active=1 AND (event_type LIKE '%HEARTRATE_HIGH_ALERT%' OR event_type LIKE '%SOS_EVENT%')")
        rules_count=cursor.fetchone()['count']
        print(f"🔧 相关活跃事件规则: {rules_count}条")
        
        cursor.close()
        conn.close()
        
        print("\n📋 验证结果:")
        if health_count>0:print("✅ 健康数据插入功能正常")
        else:print("❌ 健康数据插入可能有问题")
        
        if alert_count>0:print("✅ 告警记录插入功能正常")
        else:print("❌ 告警记录插入可能有问题")
        
        if message_count>0:print("✅ 设备消息插入功能正常")
        else:print("⚠️  设备消息插入可能有问题")
        
        if linked_alert_count>0:print(f"✅ health_id关联功能正常({linked_alert_count}条)")
        else:print("⚠️  health_id关联可能有问题")
        
        print(f"\n🎯 总结: 健康数据{health_count}条, 告警{alert_count}条, 消息{message_count}条, 队列{queue_count}条, 关联{linked_alert_count}条, 规则{rules_count}条")
        
    except Exception as e:
        print(f"❌ 验证失败:{e}")

if __name__=="__main__":
    print("🚀 开始简化验证")
    verify_data()
    print("🎯 验证完成") 