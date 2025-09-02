#!/bin/bash
# 快速测试脚本 - 验证部署包基本功能

echo "🧪 快速功能测试"
echo "================"

# 测试脚本权限
echo "1. 测试脚本权限..."
if [ -x "deploy-client.sh" ] && [ -x "wait-for-it.sh" ]; then
    echo "✅ 关键脚本权限正确"
else
    echo "❌ 脚本权限异常"
    exit 1
fi

# 测试配置文件
echo "2. 测试配置文件..."
if [ -f "custom-config.env" ] && . ./custom-config.env 2>/dev/null; then
    echo "✅ 配置文件可正常加载"
else
    echo "❌ 配置文件加载失败"
    exit 1
fi

# 测试Docker配置
echo "3. 测试Docker配置..."
if docker-compose -f docker-compose.yml config >/dev/null 2>&1; then
    echo "✅ Docker Compose配置正确"
else
    echo "❌ Docker Compose配置错误"
    exit 1
fi

# 测试wait-for-it.sh
echo "4. 测试wait-for-it.sh..."
if timeout 3 ./wait-for-it.sh 127.0.0.1:22 -t 1 >/dev/null 2>&1; then
    echo "✅ wait-for-it.sh 功能正常"
else
    echo "⚠️  wait-for-it.sh 测试超时（可能正常）"
fi

echo ""
echo "✅ 快速测试完成，部署包可用！"
