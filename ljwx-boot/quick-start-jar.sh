#!/bin/bash
# ljwx-boot 快速启动脚本 - JAR方式运行

set -e

echo "==================== ljwx-boot 快速启动 ===================="
echo "模式: JAR方式运行 + 宿主机MySQL/Redis"

# 检查必要工具
echo ""
echo "==================== 环境检查 ===================="

# 检查Java
if command -v java > /dev/null 2>&1; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
    echo "✅ Java版本: $JAVA_VERSION"
    if [ "$JAVA_VERSION" -lt 17 ]; then
        echo "❌ Java版本过低，需要Java 17+"
        exit 1
    fi
else
    echo "❌ Java未安装"
    exit 1
fi

# 检查宿主机服务
echo ""
echo "==================== 宿主机服务检查 ===================="
./host-services.sh check

# 如果服务未运行，尝试启动
if ! ./host-services.sh check > /dev/null 2>&1; then
    echo ""
    echo "🔄 尝试启动宿主机服务..."
    ./host-services.sh start
    sleep 5
fi

# 测试服务连接
echo ""
echo "==================== 连接测试 ===================="
./host-services.sh test

# 构建和运行JAR
echo ""
echo "==================== 启动应用 ===================="
echo "正在启动ljwx-boot JAR应用..."
echo ""
echo "🚀 启动后访问地址:"
echo "   - 应用服务: http://localhost:9998"
echo "   - 监控端点: http://localhost:9999/actuator"
echo ""

# 启动JAR应用
./run-jar.sh 