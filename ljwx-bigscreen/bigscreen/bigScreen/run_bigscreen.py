#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大屏系统启动脚本 - 解决相对导入问题
修复时间: 2025-05-30
"""

import sys
import os

# 添加项目路径到sys.path，解决相对导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 设置工作目录
os.chdir(current_dir)

if __name__ == '__main__':
    try:
        # 直接导入bigScreen模块
        import bigScreen
        
        print(f"🚀 大屏系统启动中...")
        print(f"📍 服务地址: http://{bigScreen.APP_HOST}:{bigScreen.APP_PORT}")
        print(f"🔧 调试模式: {'开启' if bigScreen.DEBUG else '关闭'}")
        print(f"📁 工作目录: {current_dir}")
        
        # 启动Flask应用
        bigScreen.app.run(
            host=bigScreen.APP_HOST,
            port=bigScreen.APP_PORT,
            debug=bigScreen.DEBUG,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("💡 请确保所有依赖包已安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1) 