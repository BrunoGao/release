#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""upload_common_event接口告警插入测试脚本"""
import json,time,requests,os
from datetime import datetime

def test_upload_common_event_with_health_data():
    """测试带health_data的common_event是否正确插入t_alert_info"""
    print("🧪 测试upload_common_event接口 - 确保health_data时插入t_alert_info")
    
    base_url="http://127.0.0.1:5001"
    
    # 禁用代理设置
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    
    # 测试数据1：包含heatlhData的事件(使用正确的事件类型)
    event_with_health={
        "eventType":"com.tdtech.ohos.health.action.HEARTRATE_HIGH_ALERT",
        "eventValue":"120",
        "deviceSn":"A5GTQ24603000537",
        "latitude":22.54036796,
        "longitude":114.01508952,
        "altitude":0.0,
        "heatlhData":json.dumps({
            "data":{
                "timestamp":"2025-01-25 14:30:00",
                "heart_rate":120,
                "blood_oxygen":98,
                "body_temperature":36.5,
                "step":5000,
                "distance":3.2,
                "calorie":150,
                "stress":30,
                "blood_pressure_systolic":130,
                "blood_pressure_diastolic":85,
                "latitude":22.54036796,
                "longitude":114.01508952,
                "altitude":10.0,
                "upload_method":"system_event"
            }
        })
    }
    
    # 测试数据2：不包含heatlhData的事件(使用SOS事件)
    event_without_health={
        "eventType":"com.tdtech.ohos.health.action.SOS_EVENT",
        "eventValue":"emergency",
        "deviceSn":"A5GTQ24603000537",
        "latitude":22.54036796,
        "longitude":114.01508952,
        "altitude":0.0
    }
    
    try:
        # 创建session并禁用代理
        session = requests.Session()
        session.trust_env = False
        session.proxies = {'http': None, 'https': None}
        
        print("\n📊 测试1：带健康数据的事件")
        resp1=session.post(f"{base_url}/upload_common_event",json=event_with_health,timeout=30)
        print(f"响应状态:{resp1.status_code}")
        print(f"响应内容:{resp1.text}")
        
        if resp1.status_code==200:
            result=resp1.json()
            if result.get('status')=='success':
                print("✅ 带健康数据的事件上传成功")
                print(f"   事件类型:{result.get('event_type')}")
                print(f"   设备序列号:{result.get('device_sn')}")
                print(f"   处理状态:{result.get('processing')}")
            else:
                print(f"❌ 事件处理失败:{result.get('message')}")
        else:
            print(f"❌ 请求失败:{resp1.status_code}")
        
        time.sleep(2)  # 等待异步处理
        
        print("\n📊 测试2：不带健康数据的事件")
        resp2=session.post(f"{base_url}/upload_common_event",json=event_without_health,timeout=30)
        print(f"响应状态:{resp2.status_code}")
        print(f"响应内容:{resp2.text}")
        
        if resp2.status_code==200:
            result=resp2.json()
            if result.get('status')=='success':
                print("✅ 不带健康数据的事件上传成功")
                print(f"   事件类型:{result.get('event_type')}")
                print(f"   设备序列号:{result.get('device_sn')}")
                print(f"   处理状态:{result.get('processing')}")
            else:
                print(f"❌ 事件处理失败:{result.get('message')}")
        else:
            print(f"❌ 请求失败:{resp2.status_code}")
        
        time.sleep(5)  # 等待异步处理完成
        
        # 验证数据库记录
        print("\n📋 验证数据库记录...")
        verify_database_records()
        
    except Exception as e:
        print(f"❌ 测试异常:{e}")
        import traceback
        traceback.print_exc()

def verify_database_records():
    """验证数据库中的记录"""
    try:
        import mysql.connector
        
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
        
        # 查询最近的health_data记录 - 使用正确的表名和设备SN
        print("\n🔍 查询最近的健康数据记录...")
        cursor.execute("""
            SELECT id,device_sn,timestamp,heart_rate,blood_oxygen,body_temperature,user_id,org_id
            FROM t_user_health_data 
            WHERE device_sn = 'A5GTQ24603000537'
            ORDER BY id DESC LIMIT 5
        """)
        health_records=cursor.fetchall()
        
        if health_records:
            print(f"✅ 找到{len(health_records)}条健康数据记录:")
            for record in health_records:
                print(f"   ID:{record['id']}, 设备:{record['device_sn']}, 心率:{record['heart_rate']}, 时间:{record['timestamp']}")
                health_id=record['id']
        else:
            print("❌ 未找到健康数据记录")
            health_id=None
        
        # 查询最近的告警记录
        print("\n🔍 查询最近的告警记录...")
        cursor.execute("""
            SELECT id,alert_type,device_sn,alert_desc,severity_level,health_id,user_id,org_id,alert_timestamp
            FROM t_alert_info 
            WHERE device_sn = 'A5GTQ24603000537'
            ORDER BY id DESC LIMIT 5
        """)
        alert_records=cursor.fetchall()
        
        if alert_records:
            print(f"✅ 找到{len(alert_records)}条告警记录:")
            for record in alert_records:
                health_status="有关联" if record['health_id'] else "无关联"
                print(f"   ID:{record['id']}, 类型:{record['alert_type']}, 设备:{record['device_sn']}")
                print(f"   健康ID:{record['health_id']} ({health_status}), 描述:{record['alert_desc']}")
                print(f"   时间:{record['alert_timestamp']}")
        else:
            print("❌ 未找到告警记录")
        
        # 查询最近的设备消息记录 - 修正查询条件
        print("\n🔍 查询最近的设备消息记录...")
        cursor.execute("""
            SELECT id,device_sn,message,message_type,health_id,create_time
            FROM t_device_message 
            WHERE device_sn = 'A5GTQ24603000537'
            ORDER BY id DESC LIMIT 5
        """)
        message_records=cursor.fetchall()
        
        if message_records:
            print(f"✅ 找到{len(message_records)}条设备消息记录:")
            for record in message_records:
                health_status="有关联" if record['health_id'] else "无关联"
                print(f"   ID:{record['id']}, 设备:{record['device_sn']}, 消息:{record['message']}")
                print(f"   健康ID:{record['health_id']} ({health_status}), 时间:{record['create_time']}")
        else:
            print("❌ 未找到设备消息记录")
        
        # 查询事件处理队列状态
        print("\n🔍 查询事件队列状态...")
        cursor.execute("""
            SELECT processing_status,COUNT(*) as count 
            FROM t_event_alarm_queue 
            WHERE device_sn = 'A5GTQ24603000537'
            GROUP BY processing_status
        """)
        queue_status=cursor.fetchall()
        
        if queue_status:
            print("📊 队列状态统计:")
            for status in queue_status:
                print(f"   {status['processing_status']}: {status['count']}条")
        else:
            print("📊 队列中无相关记录")
        
        cursor.close()
        conn.close()
        
        # 生成测试报告
        print("\n📋 测试结果总结:")
        has_health_data=len(health_records)>0 if health_records else False
        has_alerts=len(alert_records)>0 if alert_records else False
        has_messages=len(message_records)>0 if message_records else False
        
        if has_health_data and has_alerts:
            print("✅ 测试成功：带health_data的事件正确插入了健康数据和告警记录")
        elif has_alerts and not has_health_data:
            print("✅ 测试成功：不带health_data的事件正确插入了告警记录（无健康数据）")
        else:
            print("❌ 测试异常：未找到预期的数据库记录")
        
        # 检查health_id关联
        if has_health_data and has_alerts:
            health_linked_alerts=[r for r in alert_records if r['health_id']]
            if health_linked_alerts:
                print(f"✅ 发现{len(health_linked_alerts)}条告警记录正确关联了health_id")
            else:
                print("⚠️  告警记录未正确关联health_id")
                
    except Exception as e:
        print(f"❌ 数据库验证失败:{e}")
        import traceback
        traceback.print_exc()

def check_system_event_rules():
    """检查系统事件规则配置"""
    try:
        import mysql.connector
        
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
        
        print("\n🔍 检查系统事件规则配置...")
        cursor.execute("""
            SELECT id,event_type,rule_type,alert_message,severity_level,notification_type,is_active
            FROM t_system_event_rule 
            WHERE is_active=1 AND (event_type LIKE '%HEARTRATE_HIGH_ALERT%' OR event_type LIKE '%SOS_EVENT%')
            ORDER BY id
        """)
        rules=cursor.fetchall()
        
        if rules:
            print(f"✅ 找到{len(rules)}条相关活跃的事件规则:")
            for rule in rules:
                print(f"   ID:{rule['id']}, 事件:{rule['event_type']}, 规则:{rule['rule_type']}")
                print(f"   通知:{rule['notification_type']}, 级别:{rule['severity_level']}")
        else:
            print("❌ 未找到相关活跃的事件规则")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 规则检查失败:{e}")

if __name__=="__main__":
    print("🚀 开始upload_common_event告警插入测试")
    
    # 先检查系统事件规则
    check_system_event_rules()
    
    # 运行测试
    test_upload_common_event_with_health_data()
    
    print("\n🎯 测试完成") 