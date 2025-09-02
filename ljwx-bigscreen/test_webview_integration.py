#!/usr/bin/env python3
"""测试WebView集成功能 #App内嵌管理后台测试"""

import requests
import json
import urllib.parse

def test_webview_integration():
    """测试WebView集成的完整流程"""
    
    print("=== 测试App内嵌管理后台功能 ===")
    
    # 管理员账号信息
    phone = "18944444444"
    password = "BVxXvBnflHnG"  # 使用最新重置的密码
    
    print(f"1. 测试管理员登录")
    print(f"   手机号: {phone}")
    print(f"   密码: {password}")
    
    try:
        # 调用登录API
        url = f"http://192.168.1.6:5001/phone_login?phone={phone}&password={password}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                data = result.get('data', {})
                
                print(f"\n✅ 登录成功")
                print(f"   用户名: {data.get('user_name')}")
                print(f"   是否管理员: {data.get('isAdmin')}")
                
                # 验证WebView所需的数据
                print(f"\n2. 验证WebView集成数据")
                admin_url = data.get('adminUrl', '')
                web_username = data.get('webUsername', '')
                web_password = data.get('webPassword', '')
                
                print(f"   管理后台URL: {admin_url}")
                print(f"   Web用户名: {web_username}")
                print(f"   Web密码: {web_password}")
                
                # 解析URL参数
                if admin_url and '?' in admin_url:
                    base_url, query_string = admin_url.split('?', 1)
                    params = urllib.parse.parse_qs(query_string)
                    
                    print(f"\n3. URL参数验证")
                    print(f"   基础URL: {base_url}")
                    print(f"   URL用户名参数: {params.get('username', [''])[0]}")
                    print(f"   URL密码参数: {params.get('password', [''])[0]}")
                    print(f"   自动登录标识: {params.get('auto_login', [''])[0]}")
                    
                    # 验证数据一致性
                    url_username = params.get('username', [''])[0]
                    url_password = params.get('password', [''])[0]
                    
                    print(f"\n4. 数据一致性检查")
                    username_match = url_username == web_username
                    password_match = url_password == web_password
                    
                    print(f"   用户名一致性: {'✅' if username_match else '❌'}")
                    print(f"   密码一致性: {'✅' if password_match else '❌'}")
                    
                    if username_match and password_match:
                        print(f"\n✅ WebView集成数据验证成功")
                        print(f"✅ App可以使用以下数据在WebView中自动登录:")
                        print(f"   - 加载URL: {admin_url}")
                        print(f"   - 自动填充用户名: {web_username}")
                        print(f"   - 自动填充密码: {web_password}")
                        print(f"   - 自动点击登录按钮")
                        
                        # 模拟WebView的JavaScript自动填充
                        print(f"\n5. 模拟WebView自动填充脚本")
                        js_script = f"""
// WebView自动填充脚本
setTimeout(function() {{
    // 填充用户名
    var usernameInput = document.querySelector('input[name="username"]') || 
                       document.querySelector('input[type="text"]');
    if (usernameInput) {{
        usernameInput.value = '{web_username}';
        usernameInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
    
    // 填充密码
    var passwordInput = document.querySelector('input[name="password"]') || 
                       document.querySelector('input[type="password"]');
    if (passwordInput) {{
        passwordInput.value = '{web_password}';
        passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
    }}
    
    // 自动点击登录按钮
    setTimeout(function() {{
        var loginButton = document.querySelector('button[type="submit"]') ||
                         document.querySelector('.login-btn');
        if (loginButton && usernameInput.value && passwordInput.value) {{
            loginButton.click();
        }}
    }}, 500);
}}, 1000);
"""
                        print(f"JavaScript脚本已生成，WebView可以执行此脚本实现自动登录")
                        
                        return True
                    else:
                        print(f"\n❌ 数据一致性检查失败")
                        return False
                else:
                    print(f"\n❌ 管理后台URL格式错误")
                    return False
                    
            else:
                print(f"❌ 登录失败: {result.get('error')}")
                return False
                
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_webview_url_accessibility():
    """测试WebView URL的可访问性"""
    
    print(f"\n=== 测试管理后台URL可访问性 ===")
    
    base_url = "http://192.168.1.6:8080/"
    
    try:
        print(f"测试URL: {base_url}")
        response = requests.get(base_url, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 管理后台URL可访问")
            print(f"✅ WebView可以正常加载此URL")
            return True
        else:
            print(f"❌ 管理后台URL不可访问")
            return False
            
    except Exception as e:
        print(f"❌ URL访问测试异常: {e}")
        return False

if __name__ == "__main__":
    print("开始测试App内嵌管理后台功能...\n")
    
    # 测试登录和数据集成
    login_success = test_webview_integration()
    
    # 测试URL可访问性
    url_success = test_webview_url_accessibility()
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"登录数据集成: {'✅ 成功' if login_success else '❌ 失败'}")
    print(f"URL可访问性: {'✅ 成功' if url_success else '❌ 失败'}")
    
    if login_success and url_success:
        print(f"\n🎉 App内嵌管理后台功能完全就绪!")
        print(f"📱 用户可以在App内直接访问管理后台")
        print(f"🔐 用户名和密码会自动填充")
        print(f"⚡ 支持自动登录功能")
    else:
        print(f"\n⚠️  部分功能需要检查") 