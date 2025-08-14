#!/usr/bin/env python3
"""Redis连接测试脚本"""
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
    from bigScreen.RedisHelper import RedisHelper
    
    print("🔧 Redis配置:")
    print(f"  主机: {REDIS_HOST}")
    print(f"  端口: {REDIS_PORT}")
    print(f"  数据库: {REDIS_DB}")
    print(f"  密码: {'***' if REDIS_PASSWORD else '无'}")
    
    # 测试连接
    print("\n📡 测试Redis连接...")
    redis_helper = RedisHelper(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD
    )
    
    # 测试基本操作
    print("🔧 测试基本Redis操作...")
    redis_helper.set('test_key', 'test_value')
    value = redis_helper.get('test_key')
    
    print(f"   设置的值: test_value")
    print(f"   获取的值: {value}")
    print(f"   值类型: {type(value)}")
    
    if str(value).replace("b'", "").replace("'", "") == 'test_value' or value == 'test_value':
        print("✅ Redis连接成功!")
    else:
        print("❌ Redis连接失败 - 值不匹配")
    
    # 清理测试数据
    redis_helper.delete('test_key')
    print("🧹 测试数据已清理")
    
except Exception as e:
    print(f"❌ Redis连接失败: {e}")
    sys.exit(1) 