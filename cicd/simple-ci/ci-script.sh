#!/bin/bash

# 简单的 CI/CD 脚本

PROJECT_DIR="/path/to/your/project"
REGISTRY="localhost:5001"
IMAGE_NAME="myapp"

echo "=== 开始 CI/CD 流程 ==="

# 1. 拉取最新代码
cd "$PROJECT_DIR"
git pull origin main

# 2. 运行测试
echo "运行测试..."
python -m pytest tests/ -v
if [ $? -ne 0 ]; then
    echo "测试失败，停止构建"
    exit 1
fi

# 3. 构建镜像
echo "构建 Docker 镜像..."
COMMIT_SHA=$(git rev-parse --short HEAD)
docker build -t "$IMAGE_NAME:$COMMIT_SHA" .

# 4. 推送镜像
echo "推送镜像到 Registry..."
docker tag "$IMAGE_NAME:$COMMIT_SHA" "$REGISTRY/$IMAGE_NAME:$COMMIT_SHA"
docker push "$REGISTRY/$IMAGE_NAME:$COMMIT_SHA"

# 5. 部署 (可选)
echo "部署应用..."
# kubectl apply -f deployment.yaml
# docker-compose up -d

echo "=== CI/CD 流程完成 ===" 