#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 环境配置 - 必须在所有其他导入之前
import env_production

# 调试控制 - 批量禁用print输出
from debug_control import debug_controller

# 应用启动信息
import os
import sys
import traceback

# 设置默认环境变量
if 'IS_DOCKER' not in os.environ:
    os.environ['IS_DOCKER'] = 'true'  # Docker环境
if 'APP_PORT' not in os.environ:
    os.environ['APP_PORT'] = '5225'   # 确保使用5225端口
if 'MYSQL_HOST' not in os.environ:
    os.environ['MYSQL_HOST'] = 'mysql'
if 'MYSQL_PORT' not in os.environ:
    os.environ['MYSQL_PORT'] = '3306'
if 'MYSQL_USER' not in os.environ:
    os.environ['MYSQL_USER'] = 'root'
if 'MYSQL_PASSWORD' not in os.environ:
    os.environ['MYSQL_PASSWORD'] = '123456'
if 'MYSQL_DATABASE' not in os.environ:
    os.environ['MYSQL_DATABASE'] = 'lj-06'
if 'REDIS_HOST' not in os.environ:
    os.environ['REDIS_HOST'] = 'redis'
if 'REDIS_PORT' not in os.environ:
    os.environ['REDIS_PORT'] = '6379'
if 'REDIS_PASSWORD' not in os.environ:
    os.environ['REDIS_PASSWORD'] = '123456'

print("🚀 启动LJWX Bigscreen应用")
print(f"📊 数据库: {os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}")
print(f"🔧 Redis: {os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}")
print(f"🌐 端口: {os.environ.get('APP_PORT', '5225')}")
print("-" * 50)

try:
    print("📦 开始导入bigScreen模块...")
    
    # 🔥简化架构：直接使用bigScreen模块的app实例 #极致码高尔夫风格#
    from bigScreen import bigScreen
    from bigScreen.bigScreen import app  #直接使用模块级app实例#
    print("✅ bigScreen模块及app实例导入成功")
    
    print("🚀 应用启动准备完成")
    
    # 验证系统事件处理器状态
    try:
        from bigScreen.system_event_alert import get_processor
        processor = get_processor()
        if processor.is_running:
            print("✅ 系统事件处理器运行正常")
        else:
            print("⚠️ 系统事件处理器未运行，尝试启动...")
            with app.app_context():
                processor.start(worker_count=3)
                print("✅ 系统事件处理器已手动启动")
    except Exception as e:
        print(f"⚠️ 系统事件处理器状态检查失败: {e}")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print(f"📍 错误详情: {traceback.format_exc()}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 应用启动失败: {e}")
    print(f"📍 错误详情: {traceback.format_exc()}")
    sys.exit(1)

if __name__ == '__main__':
    try:
        print("🌟 启动Web服务器...")
        # 🔥关键修复：直接启动Flask应用，而不是使用bigScreen.main()
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('APP_PORT', '5225')),
            debug=False,  # 生产环境关闭debug
            threaded=True,  # 启用多线程
            use_reloader=False  # 关闭重载器避免重复初始化
        )
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        print(f"📍 错误详情: {traceback.format_exc()}")
        sys.exit(1)