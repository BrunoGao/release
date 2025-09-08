#!/usr/bin/env python3
"""
测试认证接口的独立脚本
用于验证认证URL和凭据是否正确
"""

import requests
import json

def test_auth():
    auth_url = "http://192.168.1.83:3333/proxy-default/auth/user_name"
    
    auth_payload = {
        "userName": "admin", 
        "password": "80a3d119ee1501354755dfc3c4638d74c67c801689efbed4f25f06cb4b1cd776"
    }
    
    print("🔐 测试身份认证...")
    print(f"URL: {auth_url}")
    print(f"请求数据: {json.dumps(auth_payload, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(
            auth_url,
            json=auth_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容:")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 查找可能的token字段
                token_fields = ['token', 'access_token', 'accessToken', 'data', 'result']
                for field in token_fields:
                    if field in data:
                        print(f"\n🔑 找到可能的token字段: {field}")
                        if isinstance(data[field], str):
                            print(f"Token值: {data[field][:50]}...")
                        else:
                            print(f"字段值: {data[field]}")
                            
            except json.JSONDecodeError:
                print("响应不是有效的JSON格式")
                print(response.text)
        else:
            print(response.text)
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_auth()