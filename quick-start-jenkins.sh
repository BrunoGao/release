#!/bin/bash
# Jenkins快速启动脚本

echo "🚀 启动Jenkins服务..."
cd /Users/brunogao/work/infra/docker/compose
docker-compose -f jenkins-compose.yml up -d

echo "⏳ 等待Jenkins启动..."
sleep 10

echo "🔑 获取管理员密码..."
password=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "已初始化")
echo "管理员密码: $password"

echo "🌐 打开Jenkins..."
open http://localhost:8081/jenkins

echo "📖 查看配置指南..."
echo "配置指南位置: docker/compose/jenkins/CONFIG_GUIDE.md"
