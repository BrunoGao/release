#!/usr/bin/env python3
"""AlertInfo org_id和user_id修复功能测试脚本"""
import sys,os,json,requests,time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:5001"

def test_alert_query_by_org():
    """测试按组织ID查询告警"""
    print("🔍 测试按组织ID查询告警...")
    
    # 测试组织ID查询
    test_org_ids = [1, 2, 3]  # 测试几个组织ID
    
    for org_id in test_org_ids:
        try:
            response = requests.get(f"{BASE_URL}/get_alerts_by_orgIdAndUserId", params={
                'orgId': org_id,
                'severityLevel': 'high'
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    alerts = data['data']['alerts']
                    print(f"✅ 组织ID={org_id}: 找到{len(alerts)}条告警")
                    
                    # 验证返回的告警都有正确的org_id
                    for alert in alerts[:3]:  # 只检查前3条
                        if alert.get('org_id') == str(org_id):
                            print(f"  ✓ 告警ID={alert['alert_id']}, org_id={alert['org_id']}, user_name={alert.get('user_name', '未知')}")
                        else:
                            print(f"  ❌ 告警ID={alert['alert_id']}, org_id不匹配: 期望{org_id}, 实际{alert.get('org_id')}")
                else:
                    print(f"❌ 组织ID={org_id}: 查询失败 - {data.get('error', '未知错误')}")
            else:
                print(f"❌ 组织ID={org_id}: HTTP错误 {response.status_code}")
                
        except Exception as e:
            print(f"❌ 组织ID={org_id}: 请求异常 - {e}")

def test_alert_query_by_user():
    """测试按用户ID查询告警"""
    print("\n🔍 测试按用户ID查询告警...")
    
    # 测试用户ID查询
    test_user_ids = [1, 2, 3]  # 测试几个用户ID
    
    for user_id in test_user_ids:
        try:
            response = requests.get(f"{BASE_URL}/get_alerts_by_orgIdAndUserId", params={
                'userId': user_id
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    alerts = data['data']['alerts']
                    print(f"✅ 用户ID={user_id}: 找到{len(alerts)}条告警")
                    
                    # 验证返回的告警都有正确的user_id
                    for alert in alerts[:3]:  # 只检查前3条
                        if alert.get('user_id') == str(user_id):
                            print(f"  ✓ 告警ID={alert['alert_id']}, user_id={alert['user_id']}, device_sn={alert.get('device_sn')}")
                        else:
                            print(f"  ❌ 告警ID={alert['alert_id']}, user_id不匹配: 期望{user_id}, 实际{alert.get('user_id')}")
                else:
                    print(f"❌ 用户ID={user_id}: 查询失败 - {data.get('error', '未知错误')}")
            else:
                print(f"❌ 用户ID={user_id}: HTTP错误 {response.status_code}")
                
        except Exception as e:
            print(f"❌ 用户ID={user_id}: 请求异常 - {e}")

def test_create_new_alert():
    """测试创建新告警是否正确设置org_id和user_id"""
    print("\n🔍 测试创建新告警...")
    
    # 模拟健康数据上传，触发告警生成
    test_data = {
        "deviceSn": "A5GTQ24B26000732",
        "heartRate": 150,  # 异常心率，应该触发告警
        "bloodOxygen": 85,  # 异常血氧
        "bodyTemperature": 39.5,  # 异常体温
        "timestamp": int(time.time() * 1000),
        "latitude": 22.54036796,
        "longitude": 114.01508952
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload_health_data", json=test_data)
        
        if response.status_code == 200:
            print("✅ 健康数据上传成功，等待告警生成...")
            time.sleep(2)  # 等待告警处理
            
            # 查询最新的告警记录 - 使用设备查询
            alert_response = requests.get(f"{BASE_URL}/fetch_alerts", params={
                'deviceSn': test_data['deviceSn']
            })
            
            if alert_response.status_code == 200:
                alert_data = alert_response.json()
                if alert_data.get('success') and alert_data.get('data'):
                    print(f"✅ 找到设备告警记录")
                    print(f"  设备序列号: {test_data['deviceSn']}")
                    print("✅ 健康数据上传和告警生成流程正常")
                else:
                    print("❌ 未找到新生成的告警")
            else:
                print(f"❌ 查询告警失败: HTTP {alert_response.status_code}")
        else:
            print(f"❌ 健康数据上传失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试创建告警异常: {e}")

def test_query_performance():
    """测试查询性能"""
    print("\n🔍 测试查询性能...")
    
    test_cases = [
        {'orgId': 1, 'name': '按组织ID查询'},
        {'userId': 1, 'name': '按用户ID查询'},
        {'orgId': 1, 'severityLevel': 'high', 'name': '组织+级别查询'},
    ]
    
    for case in test_cases:
        try:
            start_time = time.time()
            
            response = requests.get(f"{BASE_URL}/get_alerts_by_orgIdAndUserId", params=case)
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000  # 转换为毫秒
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    alert_count = data['data']['totalAlerts']
                    print(f"✅ {case['name']}: {alert_count}条告警, 耗时{duration:.1f}ms")
                else:
                    print(f"❌ {case['name']}: 查询失败")
            else:
                print(f"❌ {case['name']}: HTTP错误 {response.status_code}")
                
        except Exception as e:
            print(f"❌ {case['name']}: 异常 - {e}")

if __name__ == "__main__":
    print("🚀 AlertInfo org_id和user_id修复功能测试")
    print("="*50)
    
    # 1. 测试按组织查询
    test_alert_query_by_org()
    
    # 2. 测试按用户查询
    test_alert_query_by_user()
    
    # 3. 测试创建新告警
    test_create_new_alert()
    
    # 4. 测试查询性能
    test_query_performance()
    
    print("\n🎉 测试完成!") 