#!/usr/bin/env python3
"""验证测试数据脚本 - 修复版（使用正确字段名）"""
import mysql.connector
from datetime import datetime, timedelta

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='lj-06'
    )

def check_test_results():
    """检查最新测试的结果"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查询时间范围（最近20分钟）
    time_threshold = datetime.now() - timedelta(minutes=20)
    
    print("🔍 upload_common_event 测试结果验证")
    print(f"⏰ 检查时间: {time_threshold.strftime('%Y-%m-%d %H:%M:%S')} 以后")
    print("="*80)
    
    # 1. 检查健康数据插入
    print("\n📊 1. 健康数据 (t_user_health_data) 验证:")
    try:
        cursor.execute("""
            SELECT device_sn, heart_rate, blood_oxygen, timestamp, user_name
            FROM t_user_health_data 
            WHERE timestamp >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY timestamp DESC
        """, (time_threshold,))
        
        health_records = cursor.fetchall()
        if health_records:
            print(f"   ✅ 找到 {len(health_records)} 条健康数据记录")
            for record in health_records:
                device_sn, heart_rate, blood_oxygen, timestamp, user_name = record
                print(f"   📱 {device_sn}: 心率={heart_rate}, 血氧={blood_oxygen}, 时间={timestamp}")
        else:
            print("   ❌ 未找到测试设备的健康数据记录")
    except Exception as e:
        print(f"   ❌ 健康数据查询失败: {e}")
    
    # 2. 检查告警记录 
    print("\n🚨 2. 告警记录 (t_alert_info) 验证:")
    try:
        cursor.execute("""
            SELECT device_sn, alert_type, severity_level, alert_status, alert_timestamp, alert_desc
            FROM t_alert_info 
            WHERE alert_timestamp >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY alert_timestamp DESC
        """, (time_threshold,))
        
        alert_records = cursor.fetchall()
        if alert_records:
            print(f"   ✅ 找到 {len(alert_records)} 条告警记录")
            for record in alert_records:
                device_sn, alert_type, severity, status, timestamp, desc = record
                print(f"   🚨 {device_sn}: 类型={alert_type}, 级别={severity}, 状态={status}")
                print(f"      时间: {timestamp}")
        else:
            print("   ❌ 未找到测试设备的告警记录")
            
        # 如果没有找到新记录，检查是否有最近的记录
        cursor.execute("""
            SELECT COUNT(*) as total_alerts
            FROM t_alert_info 
            WHERE alert_timestamp >= %s
        """, (time_threshold,))
        total_alerts = cursor.fetchone()[0]
        print(f"   📊 最近时间内总告警记录: {total_alerts} 条")
        
    except Exception as e:
        print(f"   ❌ 告警记录查询失败: {e}")
    
    # 3. 检查设备消息（使用正确的字段名）
    print("\n📱 3. 设备消息 (t_device_message) 验证:")
    try:
        cursor.execute("""
            SELECT device_sn, message, message_type, sent_time, message_status
            FROM t_device_message 
            WHERE sent_time >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY sent_time DESC
        """, (time_threshold,))
        
        message_records = cursor.fetchall()
        if message_records:
            print(f"   ✅ 找到 {len(message_records)} 条设备消息记录")
            for record in message_records:
                device_sn, message, msg_type, sent_time, status = record
                print(f"   📤 {device_sn}: 类型={msg_type}, 状态={status}")
                print(f"      消息: {str(message)[:80]}{'...' if len(str(message))>80 else ''}")
                print(f"      时间: {sent_time}")
        else:
            print("   ❌ 未找到测试设备的消息记录")
            
        # 检查是否有最近的消息记录
        cursor.execute("""
            SELECT COUNT(*) as total_messages
            FROM t_device_message 
            WHERE sent_time >= %s
        """, (time_threshold,))
        total_messages = cursor.fetchone()[0]
        print(f"   📊 最近时间内总消息记录: {total_messages} 条")
            
    except Exception as e:
        print(f"   ❌ 设备消息查询失败: {e}")
    
    # 4. 检查系统事件规则（使用正确的字段名）
    print("\n⚙️  4. 系统事件规则 (t_system_event_rule) 验证:")
    try:
        cursor.execute("""
            SELECT rule_type, is_active, is_emergency, notification_type, alert_message
            FROM t_system_event_rule 
            WHERE rule_type IN ('SOS_EVENT', 'FALLDOWN_EVENT', 'ONE_KEY_ALARM', 'WEAR_STATUS_CHANGED')
            ORDER BY rule_type
        """)
        
        rule_records = cursor.fetchall()
        if rule_records:
            print(f"   ✅ 找到 {len(rule_records)} 条事件规则")
            for record in rule_records:
                rule_type, is_active, is_emergency, notification_type, alert_message = record
                active_status = "启用" if is_active else "禁用"
                emergency_status = "紧急" if is_emergency else "普通"
                print(f"   📋 {rule_type}: {active_status}, {emergency_status}, 通知={notification_type}")
        else:
            print("   ❌ 未找到相关事件规则")
    except Exception as e:
        print(f"   ❌ 事件规则查询失败: {e}")
    
    # 5. 微信配置检查
    print("\n💬 5. 微信配置检查:")
    try:
        cursor.execute("""
            SELECT id, type, enabled, corp_id, appid
            FROM t_wechat_alarm_config 
            WHERE enabled = 1
            ORDER BY type
        """)
        
        wechat_configs = cursor.fetchall()
        if wechat_configs:
            print(f"   ✅ 找到 {len(wechat_configs)} 个启用的微信配置")
            for record in wechat_configs:
                config_id, config_type, enabled, corp_id, appid = record
                if config_type == 'enterprise':
                    print(f"   🏢 企业微信 (ID={config_id}): {'已配置' if corp_id else '未配置'}")
                elif config_type == 'official':
                    print(f"   📱 公众号 (ID={config_id}): {'已配置' if appid else '未配置'}")
        else:
            print("   ❌ 未找到启用的微信配置")
    except Exception as e:
        print(f"   ❌ 微信配置查询失败: {e}")
    
    # 6. 测试数据统计和验证结论
    print("\n📈 6. 测试验证总结:")
    try:
        # 统计测试设备产生的数据
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM t_user_health_data WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as health_count,
                (SELECT COUNT(*) FROM t_alert_info WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as alert_count,
                (SELECT COUNT(*) FROM t_device_message WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as message_count
        """)
        
        stats = cursor.fetchone()
        health_count, alert_count, message_count = stats
        
        print(f"   📊 测试数据统计:")
        print(f"      健康数据记录: {health_count} 条")
        print(f"      告警记录: {alert_count} 条")
        print(f"      设备消息: {message_count} 条")
        
        print(f"\n   🎯 测试预期与实际对比:")
        print(f"      测试事件: 4个 (3个紧急+1个普通)")
        print(f"      ✅ 健康数据: 期望4条 → 实际{health_count}条 {'✅' if health_count >= 4 else '❌'}")
        print(f"      🚨 告警记录: 期望3条 → 实际{alert_count}条 {'✅' if alert_count >= 3 else '❌'}")
        print(f"      📱 设备消息: 期望4条 → 实际{message_count}条 {'✅' if message_count >= 4 else '❌'}")
        
        # 验证结论
        if health_count >= 4:
            print(f"\n   ✅ 健康数据处理: 完全正常")
        else:
            print(f"\n   ❌ 健康数据处理: 可能存在问题")
            
        if alert_count >= 3:
            print(f"   ✅ 告警处理: 紧急事件告警生成正常")
        else:
            print(f"   ⚠️  告警处理: 紧急事件可能未触发告警或处理有延迟")
            
        if message_count >= 4:
            print(f"   ✅ 平台消息: 事件消息下发正常")
        else:
            print(f"   ⚠️  平台消息: 事件消息可能未下发或处理有延迟")
        
        # 总体评价
        success_rate = (int(health_count >= 4) + int(alert_count >= 3) + int(message_count >= 4)) / 3 * 100
        print(f"\n   🏆 总体测试成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"   🎉 upload_common_event接口功能基本正常!")
        elif success_rate >= 60:
            print(f"   ⚠️  upload_common_event接口部分功能正常，需要检查告警或消息处理")
        else:
            print(f"   ❌ upload_common_event接口存在较多问题，需要深入排查")
            
    except Exception as e:
        print(f"   ❌ 统计查询失败: {e}")
    
    cursor.close()
    conn.close()
    
    print(f"\n🔍 手动验证建议:")
    print(f"   1. 检查Flask应用日志，确认事件处理流程")
    print(f"   2. 验证微信是否收到SOS/跌倒/一键报警的告警消息")
    print(f"   3. 检查系统事件处理器的队列状态")
    print(f"   4. 确认数据库触发器或存储过程是否正常工作")
    
    print(f"\n🏁 验证完成")
    print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🔍 开始验证upload_common_event测试结果...")
    
    try:
        check_test_results()
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 