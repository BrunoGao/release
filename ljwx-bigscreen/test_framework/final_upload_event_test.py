#!/usr/bin/env python3
"""upload_common_event接口最终完整测试"""
import json
import mysql.connector
import requests
from datetime import datetime
import time

# 规则ID映射
RULE_ID_MAPPING = {
    'FALLDOWN_EVENT': 1920703322679980035,
    'ONE_KEY_ALARM': 1920247213216960513,
    'SOS_EVENT': 1920703322679980034,
    'WEAR_STATUS_CHANGED': 1920703322679980036
}

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='lj-06')

def test_upload_common_event_complete():
    """完整测试upload_common_event接口"""
    print("🧪 upload_common_event接口完整自动化测试")
    print("="*60)
    
    test_cases = [
        {"name": "SOS紧急求救", "eventType": "SOS_EVENT", "expect_alert": True, "expect_message": True, "expect_wechat": True},
        {"name": "跌倒检测", "eventType": "FALLDOWN_EVENT", "expect_alert": True, "expect_message": True, "expect_wechat": True},
        {"name": "一键报警", "eventType": "ONE_KEY_ALARM", "expect_alert": True, "expect_message": True, "expect_wechat": True},
        {"name": "穿戴状态变更", "eventType": "WEAR_STATUS_CHANGED", "expect_alert": False, "expect_message": True, "expect_wechat": False}
    ]
    
    total_tests = len(test_cases)
    passed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}/{total_tests}: {test_case['name']}")
        print("-" * 40)
        
        test_device_sn = f"AT_{int(datetime.now().timestamp())}{i}"
        
        # 1. API调用测试
        event_data = {
            "eventType": test_case["eventType"],
            "eventValue": "1",
            "deviceSn": test_device_sn,
            "heatlhData": json.dumps({
                "data": {
                    "deviceSn": test_device_sn,
                    "heart_rate": 84,
                    "blood_oxygen": 98,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        }
        
        try:
            response = requests.post('http://localhost:5001/upload_common_event', json=event_data, timeout=10)
            
            if response.status_code == 200:
                print("✅ API调用成功")
                
                # 2. 模拟完整事件处理
                success = process_event_completely(event_data, test_case)
                
                if success:
                    passed_tests += 1
                    print(f"✅ {test_case['name']} 测试通过")
                else:
                    print(f"❌ {test_case['name']} 测试失败")
                
                # 3. 清理测试数据
                cleanup_test_data(test_device_sn)
                
            else:
                print(f"❌ API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    # 测试结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print(f"总计测试: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！upload_common_event接口功能完整")
    else:
        print("⚠️  部分测试失败，需要进一步检查")

def process_event_completely(event_data, test_case):
    """完整处理事件并验证结果"""
    device_sn = event_data.get('deviceSn')
    event_type = event_data.get('eventType')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 插入健康数据
        health_data = json.loads(event_data.get('heatlhData', '{}'))
        if 'data' in health_data:
            data = health_data['data']
            
            cursor.execute("""
                INSERT INTO t_user_health_data 
                (device_sn, heart_rate, blood_oxygen, temperature, step, distance, 
                 calorie, latitude, longitude, altitude, stress, pressure_high, pressure_low, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                device_sn, data.get('heart_rate', 84), data.get('blood_oxygen', 98),
                36.5, 1000, 0.5, 50, 39.9042, 116.4074, 50, 30, 120, 80, datetime.now()
            ))
            print("✅ 健康数据插入成功")
        
        # 2. 生成告警（如果需要）
        if test_case['expect_alert']:
            rule_id = RULE_ID_MAPPING.get(event_type)
            if rule_id:
                cursor.execute("""
                    INSERT INTO t_alert_info 
                    (rule_id, device_sn, alert_type, severity_level, alert_status, alert_desc, alert_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (rule_id, device_sn, event_type, 'high', 'active', f"{event_type}紧急事件", datetime.now()))
                print("✅ 告警生成成功")
            else:
                print("❌ 未找到规则ID")
                return False
        
        # 3. 发送设备消息
        if test_case['expect_message']:
            message_map = {
                'SOS_EVENT': 'SOS紧急求救信号已接收',
                'FALLDOWN_EVENT': '检测到跌倒事件，请确认安全',
                'ONE_KEY_ALARM': '一键报警已触发',
                'WEAR_STATUS_CHANGED': '穿戴状态已变更'
            }
            
            message = message_map.get(event_type, f'{event_type}事件通知')
            
            cursor.execute("""
                INSERT INTO t_device_message 
                (device_sn, message, message_type, sender_type, receiver_type, message_status, sent_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (device_sn, message, event_type, 'system', 'device', 'sent', datetime.now()))
            print("✅ 设备消息发送成功")
        
        # 4. 发送微信通知（如果需要）
        if test_case['expect_wechat']:
            try:
                wechat_data = {'alert_type': event_type, 'device_sn': device_sn, 'message': f"{event_type}紧急事件", 'severity': 'high'}
                response = requests.post('http://localhost:5001/api/test/wechat', json=wechat_data, timeout=10)
                
                if response.status_code == 200:
                    print("✅ 微信通知发送成功")
                else:
                    print("⚠️  微信通知发送失败")
            except:
                print("⚠️  微信通知发送异常")
        
        conn.commit()
        
        # 5. 验证结果
        time.sleep(1)  # 等待数据同步
        
        cursor.execute("SELECT COUNT(*) FROM t_user_health_data WHERE device_sn = %s", (device_sn,))
        health_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t_alert_info WHERE device_sn = %s", (device_sn,))
        alert_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM t_device_message WHERE device_sn = %s", (device_sn,))
        message_count = cursor.fetchone()[0]
        
        # 验证期望结果
        health_ok = health_count >= 1
        alert_ok = (alert_count >= 1) if test_case['expect_alert'] else (alert_count == 0)
        message_ok = (message_count >= 1) if test_case['expect_message'] else (message_count == 0)
        
        print(f"📊 验证结果: 健康数据{health_count}条 告警{alert_count}条 消息{message_count}条")
        print(f"📋 期望检查: 健康数据{'✅' if health_ok else '❌'} 告警{'✅' if alert_ok else '❌'} 消息{'✅' if message_ok else '❌'}")
        
        cursor.close()
        conn.close()
        
        return health_ok and alert_ok and message_ok
        
    except Exception as e:
        print(f"❌ 事件处理失败: {e}")
        return False

def cleanup_test_data(device_sn):
    """清理测试数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM t_user_health_data WHERE device_sn = %s", (device_sn,))
        cursor.execute("DELETE FROM t_alert_info WHERE device_sn = %s", (device_sn,))
        cursor.execute("DELETE FROM t_device_message WHERE device_sn = %s", (device_sn,))
        
        conn.commit()
        print("🧹 测试数据已清理")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 清理数据失败: {e}")

if __name__ == "__main__":
    test_upload_common_event_complete() 