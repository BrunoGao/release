#!/bin/bash
# LJWX系统启动脚本

echo "🚀 启动LJWX系统..."

# 1. 加载配置
echo "📋 加载配置..."
source ljwx.env

# 2. 创建必要目录
echo "📁 创建目录..."
mkdir -p data/mysql data/redis logs/ljwx-boot logs/ljwx-bigscreen logs/mysql logs/nginx

# 3. 启动服务
echo "🐳 启动Docker服务..."
docker-compose --env-file ljwx.env up -d

# 4. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 5. 检查服务状态
echo "✅ 检查服务状态..."
docker-compose ps

echo ""
echo "🎉 LJWX系统启动完成！"
echo ""
echo "📊 服务地址:"
echo "   管理后台: http://localhost:$ADMIN_PORT"
echo "   大屏系统: http://localhost:$BIGSCREEN_PORT"
echo "   后端API:  http://localhost:$BOOT_PORT"
echo ""
echo "🔍 常用命令:"
echo "   查看日志: docker-compose logs -f [service_name]"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart [service_name]"