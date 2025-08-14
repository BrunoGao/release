#!/usr/bin/env python3
"""验证测试数据脚本 - 检查事件处理结果"""
import mysql.connector
from datetime import datetime, timedelta
import json

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='lj-06'
    )

def check_recent_test_data():
    """检查最近的测试数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 查询时间范围（最近10分钟）
    time_threshold = datetime.now() - timedelta(minutes=10)
    
    print("🔍 数据库验证报告")
    print(f"⏰ 检查时间: {time_threshold.strftime('%Y-%m-%d %H:%M:%S')} 以后")
    print("="*80)
    
    # 1. 检查健康数据插入
    print("\n📊 1. 健康数据表 (t_user_health_data) 检查:")
    try:
        cursor.execute("""
            SELECT device_sn, heart_rate, blood_oxygen, timestamp, latitude, longitude
            FROM t_user_health_data 
            WHERE timestamp >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY timestamp DESC
            LIMIT 10
        """, (time_threshold,))
        
        health_records = cursor.fetchall()
        if health_records:
            print(f"   ✅ 找到 {len(health_records)} 条健康数据记录")
            for record in health_records:
                device_sn, heart_rate, blood_oxygen, timestamp, lat, lng = record
                print(f"   📱 {device_sn}: 心率={heart_rate}, 血氧={blood_oxygen}, 时间={timestamp}")
        else:
            print("   ❌ 未找到健康数据记录")
    except Exception as e:
        print(f"   ❌ 健康数据查询失败: {e}")
    
    # 2. 检查告警记录
    print("\n🚨 2. 告警信息表 (t_alert_info) 检查:")
    try:
        cursor.execute("""
            SELECT device_sn, alert_type, severity_level, alert_status, alert_timestamp, alert_desc
            FROM t_alert_info 
            WHERE alert_timestamp >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY alert_timestamp DESC
            LIMIT 10
        """, (time_threshold,))
        
        alert_records = cursor.fetchall()
        if alert_records:
            print(f"   ✅ 找到 {len(alert_records)} 条告警记录")
            for record in alert_records:
                device_sn, alert_type, severity, status, timestamp, desc = record
                print(f"   🚨 {device_sn}: 类型={alert_type}, 级别={severity}, 状态={status}")
                print(f"      描述: {desc}")
                print(f"      时间: {timestamp}")
        else:
            print("   ❌ 未找到告警记录")
    except Exception as e:
        print(f"   ❌ 告警记录查询失败: {e}")
    
    # 3. 检查设备消息
    print("\n📱 3. 设备消息表 (t_device_message) 检查:")
    try:
        cursor.execute("""
            SELECT device_sn, message, message_type, send_time, status
            FROM t_device_message 
            WHERE send_time >= %s 
            AND (device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%')
            ORDER BY send_time DESC
            LIMIT 10
        """, (time_threshold,))
        
        message_records = cursor.fetchall()
        if message_records:
            print(f"   ✅ 找到 {len(message_records)} 条设备消息记录")
            for record in message_records:
                device_sn, message, msg_type, send_time, status = record
                print(f"   📤 {device_sn}: 类型={msg_type}, 状态={status}")
                print(f"      消息: {message[:100]}{'...' if len(str(message))>100 else ''}")
                print(f"      时间: {send_time}")
        else:
            print("   ❌ 未找到设备消息记录")
    except Exception as e:
        print(f"   ❌ 设备消息查询失败: {e}")
    
    # 4. 检查系统事件规则
    print("\n⚙️  4. 系统事件规则表 (t_system_event_rule) 检查:")
    try:
        cursor.execute("""
            SELECT rule_type, enabled, wechat_enabled, platform_msg_enabled, description
            FROM t_system_event_rule 
            WHERE rule_type IN ('SOS_EVENT', 'FALLDOWN_EVENT', 'ONE_KEY_ALARM', 'WEAR_STATUS_CHANGED')
            ORDER BY rule_type
        """)
        
        rule_records = cursor.fetchall()
        if rule_records:
            print(f"   ✅ 找到 {len(rule_records)} 条事件规则")
            for record in rule_records:
                rule_type, enabled, wechat_enabled, platform_enabled, desc = record
                wechat_status = "启用" if wechat_enabled else "禁用"
                platform_status = "启用" if platform_enabled else "禁用"
                rule_status = "启用" if enabled else "禁用"
                print(f"   📋 {rule_type}: 规则={rule_status}, 微信={wechat_status}, 平台={platform_status}")
        else:
            print("   ❌ 未找到事件规则")
    except Exception as e:
        print(f"   ❌ 事件规则查询失败: {e}")
    
    # 5. 检查微信配置
    print("\n💬 5. 微信告警配置 (t_wechat_alarm_config) 检查:")
    try:
        cursor.execute("""
            SELECT id, type, enabled, corp_id, appid, secret, appsecret
            FROM t_wechat_alarm_config 
            WHERE enabled = 1
            ORDER BY type
        """)
        
        wechat_configs = cursor.fetchall()
        if wechat_configs:
            print(f"   ✅ 找到 {len(wechat_configs)} 个启用的微信配置")
            for record in wechat_configs:
                config_id, config_type, enabled, corp_id, appid, secret, appsecret = record
                if config_type == 'enterprise':
                    print(f"   🏢 企业微信 (ID={config_id}): corp_id={'已配置' if corp_id else '未配置'}, secret={'已配置' if secret else '未配置'}")
                elif config_type == 'official':
                    print(f"   📱 公众号 (ID={config_id}): appid={'已配置' if appid else '未配置'}, appsecret={'已配置' if appsecret else '未配置'}")
        else:
            print("   ❌ 未找到启用的微信配置")
    except Exception as e:
        print(f"   ❌ 微信配置查询失败: {e}")
    
    # 6. 统计摘要
    print("\n📈 6. 统计摘要:")
    try:
        # 统计测试设备数据
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM t_user_health_data WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as health_count,
                (SELECT COUNT(*) FROM t_alert_info WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as alert_count,
                (SELECT COUNT(*) FROM t_device_message WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%') as message_count
        """)
        
        stats = cursor.fetchone()
        health_count, alert_count, message_count = stats
        
        print(f"   📊 测试产生的数据统计:")
        print(f"      健康数据记录: {health_count} 条")
        print(f"      告警记录: {alert_count} 条") 
        print(f"      设备消息: {message_count} 条")
        
        # 验证逻辑
        print(f"\n   🔍 验证结果:")
        
        # 健康数据应该有4条（3个紧急事件 + 1个普通事件）
        if health_count >= 4:
            print(f"      ✅ 健康数据插入正常 ({health_count}条)")
        else:
            print(f"      ❌ 健康数据可能缺失 (期望≥4条，实际{health_count}条)")
        
        # 告警记录应该有3条（只有紧急事件产生告警）
        if alert_count >= 3:
            print(f"      ✅ 告警记录生成正常 ({alert_count}条)")
        else:
            print(f"      ⚠️  告警记录可能不足 (期望≥3条，实际{alert_count}条)")
        
        # 设备消息应该有4条（所有事件都应该有平台消息）
        if message_count >= 4:
            print(f"      ✅ 设备消息下发正常 ({message_count}条)")
        else:
            print(f"      ⚠️  设备消息可能不足 (期望≥4条，实际{message_count}条)")
            
    except Exception as e:
        print(f"   ❌ 统计查询失败: {e}")
    
    cursor.close()
    conn.close()
    
    print(f"\n🏁 验证完成")
    print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def cleanup_test_data():
    """清理测试数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\n🧹 清理测试数据...")
        
        # 清理健康数据
        cursor.execute("DELETE FROM t_user_health_data WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%'")
        health_deleted = cursor.rowcount
        
        # 清理告警记录
        cursor.execute("DELETE FROM t_alert_info WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%'")
        alert_deleted = cursor.rowcount
        
        # 清理设备消息
        cursor.execute("DELETE FROM t_device_message WHERE device_sn LIKE 'EMERGENCY_TEST_%' OR device_sn LIKE 'NORMAL_TEST_%'")
        message_deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"   ✅ 清理完成:")
        print(f"      健康数据: {health_deleted} 条")
        print(f"      告警记录: {alert_deleted} 条")
        print(f"      设备消息: {message_deleted} 条")
        
    except Exception as e:
        print(f"   ❌ 清理失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔍 开始验证测试数据...")
    
    try:
        # 检查数据
        check_recent_test_data()
        
        # 询问是否清理
        print(f"\n💭 是否需要清理测试数据？")
        print(f"   输入 'yes' 清理，其他键跳过")
        choice = input("请选择: ").strip().lower()
        
        if choice == 'yes':
            cleanup_test_data()
        else:
            print("   跳过清理，测试数据保留")
            
    except KeyboardInterrupt:
        print("\n⚠️  验证被用户中断")
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc() 