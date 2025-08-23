#!/bin/bash
# Jenkins快速启动脚本 - 简化版

set -e
BASE_DIR="/Users/brunogao/work/infra"
COMPOSE_DIR="$BASE_DIR/docker/compose"

echo "🚀 启动Jenkins CI/CD环境..."

# 创建必要目录（不设置权限）
mkdir -p "$BASE_DIR"/{data,backup}/jenkins

# 创建网络
echo "创建Docker网络..."
docker network create cicd-network 2>/dev/null || echo "网络已存在"

# 启动服务
echo "启动Jenkins和Registry..."
cd "$COMPOSE_DIR"
docker-compose -f jenkins-compose.yml up -d

echo "等待Jenkins启动..."
for i in {1..60}; do
    if curl -sf "http://localhost:8081/jenkins/login" &>/dev/null; then
        echo "✅ Jenkins启动成功！"
        break
    fi
    sleep 3
    echo -n "."
done

echo ""
echo "🎉 Jenkins环境启动完成！"
echo ""
echo "=============== 访问信息 ==============="
echo "Jenkins URL: http://localhost:8081/jenkins"
echo "Registry URL: http://localhost:5001"
echo "======================================"
echo ""
echo "📋 后续步骤:"
echo "1. 获取初始管理员密码:"
echo "   docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"
echo ""
echo "2. 访问Jenkins完成初始化配置"
echo "3. 安装推荐插件"
echo "4. 创建管理员用户"
echo ""
echo "💡 查看服务状态:"
echo "   docker-compose -f $COMPOSE_DIR/jenkins-compose.yml ps" 