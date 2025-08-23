#!/bin/bash
# 测试Registry单独部署

echo "🧪 测试Registry部署修复..."

# 清理现有的Registry容器
echo "1. 清理现有容器..."
docker stop registry registry-ui 2>/dev/null || true
docker rm registry registry-ui 2>/dev/null || true

# 创建网络
echo "2. 创建网络..."
docker network create cicd-network 2>/dev/null || true

# 尝试启动Registry
echo "3. 启动Registry服务..."
cd docker/compose
docker-compose -f registry-simple.yml up -d

# 等待启动
echo "4. 等待服务启动..."
sleep 10

# 检查服务状态
echo "5. 检查服务状态..."
docker ps | grep registry

# 测试API响应
echo "6. 测试API响应..."
if curl -s http://localhost:35001/v2/ | grep "repositories"; then
    echo "✅ Registry API正常响应"
else
    echo "❌ Registry API异常"
    docker logs registry --tail 10
fi

# 测试UI响应
echo "7. 测试UI响应..."
if curl -s http://localhost:35002 >/dev/null; then
    echo "✅ Registry UI正常响应"
else
    echo "❌ Registry UI异常"
    docker logs registry-ui --tail 10
fi

echo ""
echo "🎉 Registry测试完成！"
echo "如果测试通过，您可以运行完整部署："
echo "   ./build-infra.sh --full-auto"