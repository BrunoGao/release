#!/bin/sh

# LJWX Admin Docker 入口脚本

echo "🚀 启动 LJWX Admin 前端服务..."

# 设置默认环境变量
export SERVER_NAME=${SERVER_NAME:-localhost}
export BACKEND_URL=${BACKEND_URL:-http://ljwx-boot:9998}
export BIGSCREEN_URL=${BIGSCREEN_URL:-http://ljwx-bigscreen:5000}

# 输出配置信息
echo "📋 服务配置:"
echo "   SERVER_NAME: $SERVER_NAME"
echo "   BACKEND_URL: $BACKEND_URL" 
echo "   BIGSCREEN_URL: $BIGSCREEN_URL"

# 检查 dist 目录
if [ ! -d "/usr/share/nginx/html" ] || [ -z "$(ls -A /usr/share/nginx/html)" ]; then
    echo "❌ 错误: 前端资源目录为空或不存在"
    echo "   请确保已正确构建前端应用"
    exit 1
fi

echo "✅ 前端资源检查通过"

# 创建健康检查文件
echo "healthy" > /usr/share/nginx/html/health

# 显示前端资源文件（调试用）
echo "📁 前端资源文件:"
find /usr/share/nginx/html -type f -name "*.html" -o -name "*.js" -o -name "*.css" | head -5

# 启动 Nginx
echo "🌐 启动 Nginx 服务器..."
exec nginx -g 'daemon off;'