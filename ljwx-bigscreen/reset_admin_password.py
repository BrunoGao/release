#!/usr/bin/env python3
"""重置管理员密码脚本"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'bigScreen'))

def reset_admin_password():
    phone = '18944444444'
    print(f"正在重置手机号 {phone} 的密码...")
    
    try:
        # 导入Flask应用和相关模块
        from bigScreen.bigScreen import app
        from bigScreen.user import reset_password_by_phone
        
        # 在应用上下文中执行
        with app.app_context():
            result = reset_password_by_phone(phone)
            print('重置密码结果:', result)
            
            if result.get('success'):
                new_password = result.get('data', {}).get('password')
                print(f"新密码: {new_password}")
                print("请使用新密码登录")
            else:
                print(f"重置失败: {result.get('error')}")
                
    except Exception as e:
        print(f"重置异常: {e}")

if __name__ == "__main__":
    reset_admin_password() 