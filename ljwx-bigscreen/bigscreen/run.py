#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 环境配置 - 必须最先加载.env文件
import os
from dotenv import load_dotenv

# 立即加载.env文件，确保环境变量优先级
load_dotenv(override=True) # 强制覆盖现有环境变量#

import env_production

# 调试控制 - 批量禁用print输出
from debug_control import debug_controller

# 应用启动信息（使用专业日志而非print）
from logging_config import system_logger
system_logger.info("🚀 启动Bigscreen应用")

# run.py
import sys
import traceback

# 环境变量已从.env文件加载，无需硬编码默认值#

print("🚀 启动Bigscreen应用")
print(f"📊 数据库: {os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}")
print(f"🔧 Redis: {os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}")
print(f"🌐 端口: {os.environ.get('APP_PORT', '5001')}")
print("-" * 50)

try:
    print("📦 开始导入bigScreen模块...")
    from bigScreen import app
    print("✅ bigScreen.app 导入成功")
    
    from bigScreen import bigScreen
    print("✅ bigScreen.bigScreen 导入成功")
    
    print("🚀 应用启动准备完成")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print(f"📍 错误详情: {traceback.format_exc()}")
    system_logger.error(f"导入错误: {e}", exc_info=True)
    sys.exit(1)
except Exception as e:
    print(f"❌ 应用启动失败: {e}")
    print(f"📍 错误详情: {traceback.format_exc()}")
    system_logger.error(f"应用启动失败: {e}", exc_info=True)
    sys.exit(1)

if __name__ == '__main__':
    try:
        print("🌟 启动Web服务器...")
        bigScreen.main()  # 使用socketio.run()启动，移除重复的app.run()调用避免端口冲突
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        print(f"📍 错误详情: {traceback.format_exc()}")
        system_logger.error(f"服务器启动失败: {e}", exc_info=True)
        sys.exit(1)
