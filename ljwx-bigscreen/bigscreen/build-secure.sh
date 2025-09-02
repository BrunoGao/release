#!/bin/bash
# 安全Docker镜像构建脚本

set -e

echo "🔐 开始构建源码保护的Docker镜像..."

# 配置变量
IMAGE_NAME="ljwx-bigscreen-secure"
TAG=${1:-"latest"}
REGISTRY=${REGISTRY:-"crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"}

echo "📋 构建配置："
echo "  镜像名称: ${IMAGE_NAME}"
echo "  标签: ${TAG}"
echo "  仓库: ${REGISTRY}"
echo "  完整镜像: ${REGISTRY}/${IMAGE_NAME}:${TAG}"

# 检查必要文件
echo "🔍 检查必要文件..."
required_files=(
    "Dockerfile.protected"
    "requirements-docker.txt"
    "run.py"
    "config.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
    echo "✅ 发现文件: $file"
done

# 构建镜像
echo "🔨 开始构建镜像..."
docker build \
    -f Dockerfile.protected \
    -t ${IMAGE_NAME}:${TAG} \
    -t ${REGISTRY}/${IMAGE_NAME}:${TAG} \
    --no-cache \
    .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功！"
else
    echo "❌ 镜像构建失败！"
    exit 1
fi

# 验证镜像
echo "🔍 验证镜像安全性..."
echo "检查镜像大小："
docker images ${IMAGE_NAME}:${TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "🔐 安全验证："
echo "1. 检查是否包含源码文件..."
SOURCE_FILES=$(docker run --rm ${IMAGE_NAME}:${TAG} find /app -name "*.py" -not -path "*/__pycache__/*" -not -name "start_app.py" | wc -l)
if [ "$SOURCE_FILES" -eq 0 ]; then
    echo "✅ 未发现源码文件"
else
    echo "⚠️  发现 $SOURCE_FILES 个源码文件"
fi

echo "2. 检查字节码文件..."
BYTECODE_FILES=$(docker run --rm ${IMAGE_NAME}:${TAG} find /app -name "*.pyc" | wc -l)
echo "✅ 发现 $BYTECODE_FILES 个字节码文件"

echo "3. 检查用户权限..."
USER_INFO=$(docker run --rm ${IMAGE_NAME}:${TAG} whoami)
echo "✅ 运行用户: $USER_INFO"

# 功能测试
echo ""
echo "🧪 功能测试..."
echo "启动容器测试（5秒后停止）..."
CONTAINER_ID=$(docker run -d -p 18001:8001 ${IMAGE_NAME}:${TAG})
sleep 5

if docker ps | grep -q $CONTAINER_ID; then
    echo "✅ 容器启动成功"
    docker stop $CONTAINER_ID >/dev/null
    docker rm $CONTAINER_ID >/dev/null
else
    echo "❌ 容器启动失败"
    docker logs $CONTAINER_ID
    docker rm $CONTAINER_ID >/dev/null
    exit 1
fi

# 推送选项
echo ""
echo "🚀 构建完成！"
echo ""
echo "📋 后续操作："
echo "1. 本地测试："
echo "   docker run -d -p 8001:8001 --name ljwx-bigscreen-secure ${IMAGE_NAME}:${TAG}"
echo ""
echo "2. 推送到仓库："
echo "   docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}"
echo ""
echo "3. 安全验证："
echo "   docker run --rm ${IMAGE_NAME}:${TAG} ls -la /app"
echo ""

# 询问是否推送
read -p "是否立即推送到仓库？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 推送镜像到仓库..."
    docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
    echo "✅ 推送完成！"
fi

echo "🎉 安全镜像构建流程完成！" 