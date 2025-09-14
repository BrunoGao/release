#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试设备信息API字段修改
"""

import requests
import json

def test_device_info_api():
    """测试设备信息API返回的字段"""
    
    url = "http://localhost:5225/api/device/info?deviceSn=CRFTQ23409001890"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API返回成功!")
            print(f"响应结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 检查字段变化
            if 'data' in data and 'deviceData' in data['data'] and data['data']['deviceData']:
                device = data['data']['deviceData'][0]
                print("\n🔍 字段检查:")
                
                # 检查新字段
                if 'org_id' in device:
                    print(f"✅ org_id: {device['org_id']}")
                else:
                    print("❌ 缺少 org_id 字段")
                
                if 'org_name' in device:
                    print(f"✅ org_name: {device['org_name']}")
                else:
                    print("❌ 缺少 org_name 字段")
                
                if 'customer_id' in device:
                    print(f"✅ customer_id: {device['customer_id']}")
                else:
                    print("❌ 缺少 customer_id 字段")
                
                if 'user_id' in device:
                    print(f"✅ user_id: {device['user_id']}")
                else:
                    print("❌ 缺少 user_id 字段")
                
                # 检查旧字段是否还存在
                if 'dept_id' in device:
                    print(f"⚠️  仍有 dept_id: {device['dept_id']} (应该已移除)")
                else:
                    print("✅ dept_id 字段已正确移除")
                
                if 'dept_name' in device:
                    print(f"⚠️  仍有 dept_name: {device['dept_name']} (应该已移除)")
                else:
                    print("✅ dept_name 字段已正确移除")
        else:
            print(f"API调用失败: {response.text}")
    
    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    test_device_info_api()