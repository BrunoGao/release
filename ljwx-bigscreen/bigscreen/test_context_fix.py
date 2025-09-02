#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试应用上下文修复脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_context_fix():
    """测试应用上下文修复"""
    try:
        print("📝 开始测试应用上下文修复...")
        
        # 导入必要模块
        from bigScreen import create_app
        from bigScreen.optimized_health_data import optimized_upload_health_data
        
        # 创建应用
        app = create_app()
        
        with app.app_context():
            print("✅ 应用上下文创建成功")
            
            # 测试数据
            test_data = {
                'data': {
                    'deviceSn': 'TEST_CONTEXT_FIX',
                    'heart_rate': 72,
                    'blood_oxygen': 98,
                    'body_temperature': '36.5',
                    'timestamp': '2025-05-29 22:00:00'
                }
            }
            
            print("📤 测试健康数据上传...")
            result = optimized_upload_health_data(test_data)
            print(f"📋 上传结果: {result.get_json() if hasattr(result, 'get_json') else result}")
            
            print("✅ 应用上下文修复测试通过")
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_context_fix()
    if success:
        print("\n🎉 应用上下文修复验证成功！")
        print("💡 generate_alerts函数现在应该能在应用上下文中正常运行")
    else:
        print("\n⚠️ 测试失败，需要进一步检查")
    
    sys.exit(0 if success else 1) 