#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试队列重试功能"""

import requests
import json

def test_retry_all_failed():
    """测试重试所有失败的队列项"""
    url = "http://localhost:5001/api/system-event/queue/retry-all-failed"
    
    try:
        response = requests.post(url)
        data = response.json()
        
        print("🔄 重试所有失败队列测试:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        return data.get('success', False)
    except Exception as e:
        print(f"❌ 重试失败: {e}")
        return False

def test_restart_processor():
    """测试重启事件处理器"""
    url = "http://localhost:5001/api/system-event/processor/restart"
    
    try:
        response = requests.post(url)
        data = response.json()
        
        print("🔧 重启事件处理器测试:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        return data.get('success', False)
    except Exception as e:
        print(f"❌ 重启失败: {e}")
        return False

def test_general_alert_config():
    """测试通用告警配置"""
    url = "http://localhost:5001/api/general-alert-config"
    
    # 测试获取配置
    try:
        response = requests.get(url)
        data = response.json()
        
        print("📋 获取通用告警配置测试:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 获取配置失败: {e}")
    
    # 测试保存配置
    config_data = {
        "messageReceiverType": "manager",
        "customReceivers": "1001,1002",
        "enableMessageAlert": True,
        "enableWechatAlert": True,
        "emergencyOnly": False
    }
    
    try:
        response = requests.post(url, json=config_data)
        data = response.json()
        
        print("💾 保存通用告警配置测试:")
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")

if __name__ == '__main__':
    print("🧪 系统事件管理API测试")
    print("=" * 50)
    
    # 测试通用告警配置
    test_general_alert_config()
    print()
    
    # 测试重启处理器  
    test_restart_processor()
    print()
    
    # 测试重试失败队列
    test_retry_all_failed()
    print()
    
    print("✅ 测试完成！") 