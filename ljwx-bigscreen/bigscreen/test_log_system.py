#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志采集系统测试脚本
测试手表日志上传和显示功能
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:5001"

def test_upload_watch_log():
    """测试手表日志上传接口"""
    print("🧪 测试手表日志上传接口...")
    
    # 模拟手表日志数据
    test_logs = [
        {
            "type": "watch_log",
            "data": {
                "deviceSn": "LJWX_TEST_001",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": "INFO",
                "content": "[BluetoothService] 蓝牙连接成功"
            }
        },
        {
            "type": "watch_log", 
            "data": {
                "deviceSn": "LJWX_TEST_001",
                "timestamp": (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "WARN",
                "content": "[HealthDataCollector] 心率传感器读取异常，正在重试"
            }
        },
        {
            "type": "watch_log",
            "data": {
                "deviceSn": "LJWX_TEST_002", 
                "timestamp": (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "ERROR",
                "content": "[NetworkManager] 网络连接失败，错误代码: -1001"
            }
        },
        {
            "type": "watch_log",
            "data": {
                "deviceSn": "LJWX_TEST_001",
                "timestamp": (datetime.now() - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "level": "DEBUG",
                "content": "[LogCollector] 日志缓存大小: 45/500"
            }
        }
    ]
    
    success_count = 0
    for i, log_data in enumerate(test_logs):
        try:
            response = requests.post(
                f"{BASE_URL}/upload_watch_log",
                json=log_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(f"  ✅ 日志 {i+1} 上传成功")
                    success_count += 1
                else:
                    print(f"  ❌ 日志 {i+1} 上传失败: {result.get('message', '未知错误')}")
            else:
                print(f"  ❌ 日志 {i+1} HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 日志 {i+1} 异常: {e}")
        
        time.sleep(0.5)  # 避免请求过快
    
    print(f"📊 上传结果: {success_count}/{len(test_logs)} 成功")
    return success_count == len(test_logs)

def test_query_watch_logs():
    """测试日志查询接口"""
    print("\n🔍 测试日志查询接口...")
    
    # 测试基本查询
    try:
        response = requests.get(
            f"{BASE_URL}/api/watch_logs",
            params={
                "page": 1,
                "pageSize": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result["data"]
                logs = data["logs"]
                print(f"  ✅ 基本查询成功，返回 {len(logs)} 条日志")
                print(f"  📈 总计: {data['total']} 条，第 {data['page']}/{data['totalPages']} 页")
                
                # 显示最新的几条日志
                if logs:
                    print("  📋 最新日志:")
                    for log in logs[:3]:
                        print(f"    [{log['log_level']}] {log['device_sn']} - {log['log_content'][:50]}...")
                
            else:
                print(f"  ❌ 查询失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"  ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 查询异常: {e}")
        return False
    
    # 测试筛选查询
    print("\n🎯 测试筛选查询...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/watch_logs",
            params={
                "deviceSn": "LJWX_TEST_001",
                "level": "INFO",
                "page": 1,
                "pageSize": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                logs = result["data"]["logs"]
                print(f"  ✅ 筛选查询成功，返回 {len(logs)} 条日志")
                return True
            else:
                print(f"  ❌ 筛选查询失败: {result.get('message')}")
                return False
        else:
            print(f"  ❌ 筛选查询HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 筛选查询异常: {e}")
        return False

def test_web_page():
    """测试日志显示页面"""
    print("\n🌐 测试日志显示页面...")
    
    try:
        response = requests.get(f"{BASE_URL}/watch_logs", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            if "手表日志监控系统" in content and "设备序列号" in content:
                print("  ✅ 日志显示页面加载成功")
                print(f"  📄 页面大小: {len(content)} 字符")
                return True
            else:
                print("  ❌ 页面内容不完整")
                return False
        else:
            print(f"  ❌ 页面HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 页面访问异常: {e}")
        return False

def generate_batch_test_logs():
    """生成批量测试日志"""
    print("\n🚀 生成批量测试日志...")
    
    devices = ["LJWX_TEST_001", "LJWX_TEST_002", "LJWX_TEST_003"]
    levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    log_templates = [
        "[BluetoothService] 蓝牙连接状态: {}",
        "[HealthDataCollector] 采集数据: 心率{}bpm",
        "[NetworkManager] 网络延迟: {}ms",
        "[LogCollector] 缓存状态: {}/500",
        "[SensorManager] 传感器读取: {}",
        "[BatteryManager] 电量状态: {}%"
    ]
    
    success_count = 0
    total_count = 20
    
    for i in range(total_count):
        device_sn = random.choice(devices)
        level = random.choice(levels)
        template = random.choice(log_templates)
        
        # 生成随机内容
        if "心率" in template:
            content = template.format(random.randint(60, 120))
        elif "延迟" in template:
            content = template.format(random.randint(10, 200))
        elif "缓存" in template:
            content = template.format(random.randint(1, 500))
        elif "电量" in template:
            content = template.format(random.randint(20, 100))
        elif "连接状态" in template:
            content = template.format(random.choice(["已连接", "断开", "重连中"]))
        else:
            content = template.format(random.choice(["正常", "异常", "警告"]))
        
        log_data = {
            "type": "watch_log",
            "data": {
                "deviceSn": device_sn,
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S"),
                "level": level,
                "content": content
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/upload_watch_log",
                json=log_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200 and response.json().get("status") == "success":
                success_count += 1
                if i % 5 == 0:
                    print(f"  📝 已生成 {i+1}/{total_count} 条日志...")
                    
        except Exception as e:
            print(f"  ⚠️ 第 {i+1} 条日志生成失败: {e}")
        
        time.sleep(0.1)  # 避免请求过快
    
    print(f"  ✅ 批量日志生成完成: {success_count}/{total_count} 成功")
    return success_count

def main():
    """主测试函数"""
    print("🎯 开始日志采集系统测试")
    print("=" * 50)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ 服务运行正常 (状态码: {response.status_code})")
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        print("请确保 ljwx-bigscreen 服务正在运行在 localhost:5001")
        return
    
    # 执行测试
    test_results = []
    
    # 1. 测试日志上传
    test_results.append(("日志上传", test_upload_watch_log()))
    
    # 2. 测试日志查询
    test_results.append(("日志查询", test_query_watch_logs()))
    
    # 3. 测试页面访问
    test_results.append(("页面访问", test_web_page()))
    
    # 4. 生成批量测试数据
    batch_count = generate_batch_test_logs()
    test_results.append(("批量生成", batch_count > 15))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎉 总体结果: {passed}/{len(test_results)} 项测试通过")
    
    if passed == len(test_results):
        print("🎊 所有测试通过！日志采集系统运行正常")
        print(f"🌐 访问 {BASE_URL}/watch_logs 查看日志界面")
    else:
        print("⚠️ 部分测试失败，请检查系统配置")

if __name__ == "__main__":
    main() 