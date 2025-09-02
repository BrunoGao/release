#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试upload_common_event接口真实数据处理"""
import json,requests,time,mysql.connector
from datetime import datetime

def test_upload_common_event_real_data():
    """测试真实数据处理"""
    print("🧪 测试upload_common_event接口 - 真实数据验证")

    # 数据库配置
    db_config = {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'lj-06',
        'charset': 'utf8mb4'
    }

    # API基础URL
    base_url = "http://127.0.0.1:5001"

    # 用户提供的真实测试数据 - 优化为调用upload_health_data
    test_data = {
        "eventType": "com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
        "eventValue": "0",
        "deviceSn": "CRFTQ23409001890",
        "latitude": 22.540412,
        "longitude": 114.015103,
        "altitude": 0,
        "healthData": {  #修复拼写错误，使用正确的字段名
            "data": {
                "deviceSn": "CRFTQ23409001890",
                "heart_rate": 69,
                "blood_oxygen": 0,
                "body_temperature": "0.0",
                "step": 0,
                "distance": "0.0",
                "calorie": "0.0",
                "latitude": "22.540412",
                "longitude": "114.015103",
                "altitude": "0.0",
                "stress": 0,
                "upload_method": "wifi",
                "blood_pressure_systolic": 110,
                "blood_pressure_diastolic": 76,
                "sleepData": "null",
                "exerciseDailyData": "null",
                "exerciseWeekData": "null",
                "scientificSleepData": "null",
                "workoutData": "null",
                "timestamp": "2025-06-19 15:48:28"
            }
        }
    }

    device_sn = test_data["deviceSn"]

    # 记录测试开始时间
    test_start_time = datetime.now()
    print(f"📅 测试开始时间: {test_start_time}")
    print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")

    try:
        # 1. 发送API请求
        print(f"\n📤 发送API请求到 {base_url}/upload_common_event")

        response = requests.post(
            f"{base_url}/upload_common_event",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        print(f"📬 API响应状态码: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            api_response = response.json()
            print(f"📬 API响应内容: {json.dumps(api_response, ensure_ascii=False, indent=2)}")
        else:
            print(f"📬 API响应内容: {response.text}")

        # 等待异步处理完成
        print(f"\n⏳ 等待5秒让异步处理完成...")
        time.sleep(5)

        # 2. 连接数据库验证结果
        print(f"\n🔍 开始数据库验证...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # 3. 检查健康数据插入
        print(f"\n💾 检查健康数据表(t_user_health_data)...")
        cursor.execute("""
            SELECT *
            FROM t_user_health_data
            WHERE device_sn = %s AND create_time >= %s
            ORDER BY create_time DESC LIMIT 5
        """, (device_sn, test_start_time))

        health_records = cursor.fetchall()

        if health_records:
            print(f"✅ 找到 {len(health_records)} 条健康数据记录:")
            for i, record in enumerate(health_records, 1):
                print(f"   {i}. ID={record['id']}, 心率={record['heart_rate']}, 血氧={record['blood_oxygen']}")
                print(f"      收缩压={record['pressure_low']}, 舒张压={record['pressure_high']}")
                print(f"      坐标=({record['latitude']}, {record['longitude']})")
                print(f"      用户ID={record['user_id']}, 组织ID={record['org_id']}")
                print(f"      上传方式={record['upload_method']}, 创建时间={record['create_time']}")

            latest_health_id = health_records[0]['id']
            print(f"🎯 最新健康数据ID: {latest_health_id}")
        else:
            print("❌ 未找到健康数据记录")
            latest_health_id = None

        # 4. 检查告警记录插入
        print(f"\n🚨 检查告警记录表(t_alert_info)...")
        cursor.execute("""
            SELECT id, rule_id, alert_type, device_sn, alert_timestamp,
                   alert_desc, severity_level, alert_status, health_id,
                   user_id, org_id, latitude, longitude, create_time
            FROM t_alert_info
            WHERE device_sn = %s AND create_time >= %s
            ORDER BY create_time DESC LIMIT 5
        """, (device_sn, test_start_time))

        alert_records = cursor.fetchall()

        if alert_records:
            print(f"✅ 找到 {len(alert_records)} 条告警记录:")
            for i, record in enumerate(alert_records, 1):
                print(f"   {i}. ID={record['id']}, 规则ID={record['rule_id']}, 类型={record['alert_type']}")
                print(f"      描述={record['alert_desc']}")
                print(f"      严重级别={record['severity_level']}, 状态={record['alert_status']}")
                print(f"      健康数据ID={record['health_id']}, 用户ID={record['user_id']}")
                print(f"      坐标=({record['latitude']}, {record['longitude']})")
                print(f"      创建时间={record['create_time']}")

            latest_alert = alert_records[0]
            print(f"🎯 最新告警ID: {latest_alert['id']}")
            print(f"🔗 告警关联的健康数据ID: {latest_alert['health_id']}")
        else:
            print("❌ 未找到告警记录")
            latest_alert = None

        # 5. 检查事件队列处理状态
        print(f"\n📋 检查事件队列表(t_event_alarm_queue)...")
        cursor.execute("""
            SELECT id, event_type, device_sn, event_value, processing_status,
                   create_time
            FROM t_event_alarm_queue
            WHERE device_sn = %s AND create_time >= %s
            ORDER BY create_time DESC LIMIT 3
        """, (device_sn, test_start_time))

        queue_records = cursor.fetchall()

        if queue_records:
            print(f"✅ 找到 {len(queue_records)} 条队列记录:")
            for i, record in enumerate(queue_records, 1):
                print(f"   {i}. ID={record['id']}, 事件类型={record['event_type']}")
                print(f"      事件值={record['event_value']}, 处理状态={record['processing_status']}")
                print(f"      创建时间={record['create_time']}")
        else:
            print("⚠️ 未找到队列记录")

        # 6. 检查系统事件规则
        print(f"\n🔧 检查相关系统事件规则...")
        cursor.execute("""
            SELECT id, event_type, rule_type, alert_message, severity_level,
                   notification_type, is_active
            FROM t_system_event_rule
            WHERE event_type LIKE %s OR event_type = %s
            ORDER BY is_active DESC, id
        """, (f"%{test_data['eventType']}%", test_data['eventType']))

        rules = cursor.fetchall()

        if rules:
            print(f"📋 找到 {len(rules)} 条相关事件规则:")
            for i, rule in enumerate(rules, 1):
                status = "🟢启用" if rule['is_active'] else "🔴禁用"
                print(f"   {i}. {status} ID={rule['id']}, 事件类型={rule['event_type']}")
                print(f"      规则类型={rule['rule_type']}, 通知类型={rule['notification_type']}")
                print(f"      严重级别={rule['severity_level']}")
        else:
            print("⚠️ 未找到匹配的事件规则")

        # 7. 验证health_id关联
        print(f"\n🔗 验证health_id关联...")
        if latest_health_id and latest_alert and latest_alert['health_id']:
            if latest_health_id == latest_alert['health_id']:
                print(f"✅ health_id关联正确: 健康数据ID={latest_health_id} = 告警中的health_id={latest_alert['health_id']}")
            else:
                print(f"❌ health_id关联错误: 健康数据ID={latest_health_id} ≠ 告警中的health_id={latest_alert['health_id']}")
        elif latest_health_id and latest_alert and not latest_alert['health_id']:
            print(f"⚠️ 健康数据已插入(ID={latest_health_id})，但告警记录中health_id为空")
        elif not latest_health_id and latest_alert:
            print(f"⚠️ 告警记录已创建但健康数据未插入")
        elif latest_health_id and not latest_alert:
            print(f"⚠️ 健康数据已插入(ID={latest_health_id})但未创建告警记录")
        else:
            print(f"❌ 健康数据和告警记录都未正确创建")

        cursor.close()
        conn.close()

        # 8. 生成测试报告
        print(f"\n📊 测试结果总结:")
        print(f"   API调用: {'✅成功' if response.status_code == 200 else '❌失败'}")
        print(f"   健康数据插入: {'✅成功' if health_records else '❌失败'}")
        print(f"   告警记录插入: {'✅成功' if alert_records else '❌失败'}")
        print(f"   health_id关联: {'✅正确' if (latest_health_id and latest_alert and latest_health_id == latest_alert.get('health_id')) else '❌错误'}")
        print(f"   事件队列处理: {'✅正常' if queue_records else '⚠️异常'}")
        print(f"   事件规则配置: {'✅已配置' if rules else '⚠️未配置'}")
        print(f"   优化说明: healthData通过复用upload_health_data接口处理")

        return {
            'api_success': response.status_code == 200,
            'health_data_inserted': bool(health_records),
            'alert_inserted': bool(alert_records),
            'health_id_linked': bool(latest_health_id and latest_alert and latest_health_id == latest_alert.get('health_id')),
            'latest_health_id': latest_health_id,
            'latest_alert_id': latest_alert['id'] if latest_alert else None,
            'queue_processed': bool(queue_records),
            'rules_configured': bool(rules),
            'optimization': 'healthData processed via upload_health_data interface'
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ API请求失败: {e}")
        return {'error': f'API请求失败: {e}'}
    except mysql.connector.Error as e:
        print(f"❌ 数据库连接失败: {e}")
        return {'error': f'数据库连接失败: {e}'}
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'测试异常: {e}'}

if __name__ == "__main__":
    print("🚀 开始upload_common_event真实数据测试(优化版)")
    result = test_upload_common_event_real_data()

    if 'error' not in result:
        print(f"\n🎯 测试完成")
        if result['api_success'] and result['health_data_inserted']:
            print("🎉 核心功能测试通过!")
            print("🔧 优化效果: healthData通过复用upload_health_data接口处理")
        else:
            print("⚠️ 部分功能存在问题")
    else:
        print(f"\n💀 测试失败: {result['error']}")
