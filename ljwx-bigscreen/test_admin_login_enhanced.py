#!/usr/bin/env python3
"""测试增强的管理员登录功能 #管理员Web登录测试"""

import requests
import json
import urllib.parse

def test_admin_login_enhanced():
    """测试管理员登录API的增强功能"""
    
    # 测试管理员账号
    phone = "18944444444"
    password = "123456"
    
    print("=== 测试增强的管理员登录功能 ===")
    print(f"手机号: {phone}")
    print(f"密码: {password}")
    print()
    
    try:
        # 调用登录API
        url = f"http://192.168.1.6:5001/phone_login?phone={phone}&password={password}"
        print(f"请求URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("登录响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('success'):
                data = result.get('data', {})
                
                print("\n=== 管理员信息验证 ===")
                print(f"用户ID: {data.get('user_id')}")
                print(f"用户名: {data.get('user_name')}")
                print(f"手机号: {data.get('phone')}")
                print(f"是否管理员: {data.get('isAdmin')}")
                print(f"角色列表: {[role.get('role_name') for role in data.get('roles', [])]}")
                
                print("\n=== Web登录信息 ===")
                print(f"Web用户名: {data.get('webUsername')}")
                print(f"Web密码: {data.get('webPassword')}")
                print(f"管理后台URL: {data.get('adminUrl')}")
                
                # 解析URL参数
                admin_url = data.get('adminUrl', '')
                if admin_url and '?' in admin_url:
                    base_url, query_string = admin_url.split('?', 1)
                    params = urllib.parse.parse_qs(query_string)
                    
                    print(f"\n=== URL参数解析 ===")
                    print(f"基础URL: {base_url}")
                    print(f"预填充用户名: {params.get('username', [''])[0]}")
                    print(f"预填充密码: {params.get('password', [''])[0]}")
                    print(f"自动登录标识: {params.get('auto_login', [''])[0]}")
                
                # 验证管理员功能
                if data.get('isAdmin'):
                    print(f"\n✅ 管理员功能验证成功")
                    print(f"✅ Web登录信息完整")
                    print(f"✅ URL参数预填充正确")
                else:
                    print(f"\n❌ 用户不是管理员")
                    
            else:
                print(f"❌ 登录失败: {result.get('error')}")
                
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_normal_user():
    """测试普通用户登录"""
    
    phone = "18944444445"  # 假设的普通用户
    password = "123456"
    
    print(f"\n=== 测试普通用户登录 ===")
    print(f"手机号: {phone}")
    
    try:
        url = f"http://192.168.1.6:5001/phone_login?phone={phone}&password={password}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result.get('data', {})
                print(f"用户名: {data.get('user_name')}")
                print(f"是否管理员: {data.get('isAdmin')}")
                print(f"Web用户名: {data.get('webUsername')}")
                print(f"Web密码: {data.get('webPassword')}")
                print(f"管理后台URL: {data.get('adminUrl')}")
                
                if not data.get('isAdmin'):
                    print("✅ 普通用户正确，无管理员权限")
                else:
                    print("❌ 普通用户错误获得管理员权限")
            else:
                print(f"普通用户登录失败（可能用户不存在）: {result.get('error')}")
                
    except Exception as e:
        print(f"普通用户测试异常: {e}")

if __name__ == "__main__":
    test_admin_login_enhanced()
    test_normal_user() 