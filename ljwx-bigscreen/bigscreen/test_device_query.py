#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立测试优化后的设备查询"""

import sys,os,json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量确保Flask app可以正确初始化
os.environ['FLASK_ENV'] = 'development'

from bigScreen.models import db
from bigScreen.device import fetch_devices_by_orgIdAndUserId
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI

def test_device_query():
    """测试优化后的设备查询"""
    print("🧪 开始测试优化设备查询...")
    
    # 创建Flask应用上下文
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("\n📝 测试场景1: 查询组织1下的所有设备")
        try:
            result1 = fetch_devices_by_orgIdAndUserId(orgId=1, userId=None)
            print(f"✅ 查询结果: {json.dumps(result1, indent=2, ensure_ascii=False, default=str)}")
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n📝 测试场景2: 查询用户1的设备")
        try:
            result2 = fetch_devices_by_orgIdAndUserId(orgId=None, userId=1)
            print(f"✅ 查询结果: {json.dumps(result2, indent=2, ensure_ascii=False, default=str)}")
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n📝 测试场景3: 查询不存在的组织")
        try:
            result3 = fetch_devices_by_orgIdAndUserId(orgId=999, userId=None)
            print(f"✅ 查询结果: {json.dumps(result3, indent=2, ensure_ascii=False, default=str)}")
        except Exception as e:
            print(f"❌ 查询失败: {e}")

def main():
    """主函数"""
    test_device_query()

if __name__ == "__main__":
    main() 