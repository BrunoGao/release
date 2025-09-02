#!/bin/bash
# 安全镜像测试脚本

set -e

IMAGE_NAME=${1:-"ljwx-bigscreen-secure:latest"}
TEST_PORT=${2:-"18001"}

echo "🧪 开始测试安全镜像: $IMAGE_NAME"

# 检查镜像是否存在
if ! docker images | grep -q "${IMAGE_NAME%:*}"; then
    echo "❌ 镜像不存在: $IMAGE_NAME"
    echo "请先运行: ./build-secure.sh"
    exit 1
fi

echo "✅ 发现镜像: $IMAGE_NAME"

# 安全性测试
echo ""
echo "🔐 安全性测试："

echo "1. 检查源码文件..."
SOURCE_COUNT=$(docker run --rm $IMAGE_NAME find /app -name "*.py" -not -path "*/__pycache__/*" -not -name "start_app.py" 2>/dev/null | wc -l)
if [ "$SOURCE_COUNT" -eq 0 ]; then
    echo "✅ 未发现源码文件"
else
    echo "⚠️  发现 $SOURCE_COUNT 个源码文件"
    docker run --rm $IMAGE_NAME find /app -name "*.py" -not -path "*/__pycache__/*" -not -name "start_app.py"
fi

echo "2. 检查字节码文件..."
BYTECODE_COUNT=$(docker run --rm $IMAGE_NAME find /app -name "*.pyc" 2>/dev/null | wc -l)
echo "✅ 发现 $BYTECODE_COUNT 个字节码文件"

echo "3. 检查运行用户..."
USER_INFO=$(docker run --rm $IMAGE_NAME whoami 2>/dev/null)
if [ "$USER_INFO" = "ljwx" ]; then
    echo "✅ 使用非特权用户: $USER_INFO"
else
    echo "⚠️  运行用户: $USER_INFO"
fi

echo "4. 检查文件权限..."
docker run --rm $IMAGE_NAME ls -la /app | head -10

echo "5. 检查敏感目录..."
SENSITIVE_DIRS=(".git" "logs" "cache" "venv" "__pycache__")
for dir in "${SENSITIVE_DIRS[@]}"; do
    if docker run --rm $IMAGE_NAME test -d "/app/$dir" 2>/dev/null; then
        echo "⚠️  发现敏感目录: $dir"
    else
        echo "✅ 未发现敏感目录: $dir"
    fi
done

# 功能测试
echo ""
echo "🚀 功能测试："

echo "1. 启动容器..."
CONTAINER_ID=$(docker run -d -p $TEST_PORT:8001 --name test-secure-$(date +%s) $IMAGE_NAME)
echo "✅ 容器启动: $CONTAINER_ID"

# 等待服务启动
echo "2. 等待服务启动..."
sleep 10

# 检查容器状态
if docker ps | grep -q $CONTAINER_ID; then
    echo "✅ 容器运行正常"
else
    echo "❌ 容器启动失败"
    docker logs $CONTAINER_ID
    docker rm $CONTAINER_ID
    exit 1
fi

# 检查端口监听
echo "3. 检查端口监听..."
if nc -z localhost $TEST_PORT 2>/dev/null; then
    echo "✅ 端口 $TEST_PORT 监听正常"
else
    echo "❌ 端口 $TEST_PORT 无法连接"
fi

# HTTP测试
echo "4. HTTP连接测试..."
if curl -s -f http://localhost:$TEST_PORT/ >/dev/null 2>&1; then
    echo "✅ HTTP连接成功"
else
    echo "⚠️  HTTP连接失败（可能需要数据库）"
fi

# 检查容器日志
echo "5. 检查容器日志..."
LOG_LINES=$(docker logs $CONTAINER_ID 2>&1 | wc -l)
echo "✅ 日志行数: $LOG_LINES"

if [ $LOG_LINES -gt 0 ]; then
    echo "最近日志："
    docker logs $CONTAINER_ID 2>&1 | tail -5
fi

# 安全渗透测试
echo ""
echo "🛡️  安全渗透测试："

echo "1. 尝试进入容器..."
if docker exec $CONTAINER_ID /bin/bash -c "echo 'test'" 2>/dev/null; then
    echo "⚠️  可以执行bash命令"
else
    echo "✅ 无法执行bash命令"
fi

echo "2. 检查文件系统权限..."
if docker exec $CONTAINER_ID touch /app/test_write 2>/dev/null; then
    echo "⚠️  可以写入文件"
    docker exec $CONTAINER_ID rm -f /app/test_write
else
    echo "✅ 文件系统只读"
fi

echo "3. 检查网络权限..."
if docker exec $CONTAINER_ID ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "✅ 网络连接正常"
else
    echo "⚠️  网络连接受限"
fi

# 性能测试
echo ""
echo "📊 性能测试："

echo "1. 内存使用..."
MEMORY_USAGE=$(docker stats $CONTAINER_ID --no-stream --format "{{.MemUsage}}")
echo "✅ 内存使用: $MEMORY_USAGE"

echo "2. CPU使用..."
CPU_USAGE=$(docker stats $CONTAINER_ID --no-stream --format "{{.CPUPerc}}")
echo "✅ CPU使用: $CPU_USAGE"

echo "3. 镜像大小..."
IMAGE_SIZE=$(docker images $IMAGE_NAME --format "{{.Size}}")
echo "✅ 镜像大小: $IMAGE_SIZE"

# 清理测试容器
echo ""
echo "🧹 清理测试环境..."
docker stop $CONTAINER_ID >/dev/null
docker rm $CONTAINER_ID >/dev/null
echo "✅ 测试容器已清理"

# 测试总结
echo ""
echo "📋 测试总结："
echo "  镜像名称: $IMAGE_NAME"
echo "  源码文件: $SOURCE_COUNT 个"
echo "  字节码文件: $BYTECODE_COUNT 个"
echo "  运行用户: $USER_INFO"
echo "  镜像大小: $IMAGE_SIZE"
echo "  内存使用: $MEMORY_USAGE"
echo "  CPU使用: $CPU_USAGE"

if [ "$SOURCE_COUNT" -eq 0 ] && [ "$USER_INFO" = "ljwx" ]; then
    echo ""
    echo "🎉 安全测试通过！镜像符合安全要求。"
    exit 0
else
    echo ""
    echo "⚠️  安全测试发现问题，请检查上述输出。"
    exit 1
fi 