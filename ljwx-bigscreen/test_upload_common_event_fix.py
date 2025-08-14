#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试upload_common_event接口修复效果"""
import json,requests,time
from datetime import datetime

def test_upload_common_event_fix():
    """测试upload_common_event接口修复"""
    print("🧪 测试upload_common_event接口修复效果")
    print("=" * 60)
    
    #模拟用户原始数据(与用户日志中的数据格式一致)
    test_data={
        "eventType":"com.tdtech.ohos.action.WEAR_STATUS_CHANGED",
        "eventValue":"0",
        "deviceSn":"CRFTQ23409001890",
        "latitude":22.5404,
        "longitude":114.015072,
        "altitude":0,
        "healthData":json.dumps({
            "data":{
                "deviceSn":"CRFTQ23409001890",
                "heart_rate":86,
                "blood_oxygen":98,
                "body_temperature":"0.0",
                "step":0,
                "distance":"0.0",
                "calorie":"0.0",
                "latitude":"0",
                "longitude":"0",
                "altitude":"0",
                "stress":0,
                "upload_method":"wifi",
                "blood_pressure_systolic":127,
                "blood_pressure_diastolic":87,
                "sleepData":"null",
                "exerciseDailyData":"null",
                "exerciseWeekData":"null",
                "scientificSleepData":"null",
                "workoutData":"null",
                "timestamp":"2025-06-19 14:09:27"
            }
        })
    }
    
    print("📤 测试数据:")
    print(json.dumps(test_data,indent=2,ensure_ascii=False))
    print()
    
    #测试本地服务
    test_urls=[
        "http://localhost:8001/upload_common_event",
        "http://127.0.0.1:8001/upload_common_event",
        "http://192.168.1.6:8001/upload_common_event"
    ]
    
    for url in test_urls:
        try:
            print(f"🌐 测试地址: {url}")
            start_time=time.time()
            
            response=requests.post(url,json=test_data,timeout=10)
            elapsed=time.time()-start_time
            
            print(f"   ✅ 状态码: {response.status_code}")
            print(f"   ⏱️  响应时间: {elapsed:.3f}秒")
            
            if response.status_code==200:
                result=response.json()
                print(f"   📋 响应内容: {json.dumps(result,indent=4,ensure_ascii=False)}")
                
                if result.get('status')=='success':
                    print(f"   🎉 测试成功! 消息: {result.get('message')}")
                else:
                    print(f"   ⚠️  业务失败: {result.get('message')}")
            else:
                print(f"   ❌ HTTP错误: {response.text}")
                
        except requests.exceptions.ConnectRefusedError:
            print(f"   ❌ 连接被拒绝 - 服务可能未启动")
        except requests.exceptions.Timeout:
            print(f"   ❌ 请求超时")
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
        
        print()

if __name__=='__main__':
    test_upload_common_event_fix() 