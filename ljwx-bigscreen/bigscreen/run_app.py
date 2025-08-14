#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 解决相对导入问题
"""
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入并运行应用
if __name__ == '__main__':
    from bigScreen.bigScreen import app, socketio
    
    # 启动应用
    print("启动智能穿戴演示大屏...")
    print("访问地址: http://localhost:5001")
    print("大屏地址: http://localhost:5001/bigscreen_main")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"启动失败: {e}")
        # 尝试普通Flask启动
        app.run(host='0.0.0.0', port=5001, debug=True) 