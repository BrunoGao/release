#!/bin/bash
# Jenkins自动配置测试脚本

echo "🧪 测试Jenkins自动配置..."

# 测试登录
echo "1. 测试管理员登录..."
response=$(curl -s -c cookies.txt -d "j_username=admin&j_password=admin123" \
    -X POST "http://localhost:8081/j_spring_security_check")
if [[ $? -eq 0 ]]; then
    echo "✅ 管理员登录成功"
else
    echo "❌ 管理员登录失败"
fi

# 测试API访问
echo "2. 测试Jenkins API..."
crumb=$(curl -s -b cookies.txt "http://localhost:8081/crumbIssuer/api/json" | \
    grep -o '"crumb":"[^"]*' | cut -d'"' -f4)
if [[ -n "$crumb" ]]; then
    echo "✅ API访问正常"
else
    echo "❌ API访问失败"
fi

# 测试作业列表
echo "3. 检查预创建作业..."
jobs=$(curl -s -b cookies.txt "http://localhost:8081/api/json" | \
    grep -o '"name":"[^"]*' | cut -d'"' -f4)
if echo "$jobs" | grep -q "multiplatform-build-demo"; then
    echo "✅ 示例作业已创建"
else
    echo "❌ 示例作业缺失"
fi

# 清理
rm -f cookies.txt

echo "🎉 测试完成"
