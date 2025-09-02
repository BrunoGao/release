#!/usr/bin/env python3
"""简化的应用启动脚本 - 无Redis监听器"""
import os

# 设置默认环境变量
if 'IS_DOCKER' not in os.environ:
    os.environ['IS_DOCKER'] = 'false'
if 'MYSQL_HOST' not in os.environ:
    os.environ['MYSQL_HOST'] = '127.0.0.1'
if 'MYSQL_PORT' not in os.environ:
    os.environ['MYSQL_PORT'] = '3306'
if 'MYSQL_USER' not in os.environ:
    os.environ['MYSQL_USER'] = 'root'
if 'MYSQL_PASSWORD' not in os.environ:
    os.environ['MYSQL_PASSWORD'] = '123456'
if 'MYSQL_DATABASE' not in os.environ:
    os.environ['MYSQL_DATABASE'] = 'lj-06'
if 'REDIS_HOST' not in os.environ:
    os.environ['REDIS_HOST'] = '127.0.0.1'
if 'REDIS_PORT' not in os.environ:
    os.environ['REDIS_PORT'] = '6379'
if 'REDIS_PASSWORD' not in os.environ:
    os.environ['REDIS_PASSWORD'] = '123456'

print("🚀 启动简化版Bigscreen应用")
print(f"📊 数据库: {os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DATABASE']}")
print(f"🔧 Redis: {os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}")
print(f"🌐 端口: {os.environ.get('APP_PORT', '5002')}") 
print("🛡️  无Redis监听器版本")
print("-" * 50)

# 导入应用，但不启动监听器
from bigScreen.bigScreen import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('APP_PORT', 5002))  # 使用不同端口避免冲突
    print(f"✅ 在端口 {port} 启动应用...")
    
    try:
        # 使用Flask的简单服务器，不启动socketio
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 提示: 检查端口是否被占用") 