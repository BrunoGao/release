#!/bin/bash

# AI集成测试脚本
echo "🔍 开始AI集成测试..."

# 检查Ollama服务状态
echo "📡 检查Ollama服务状态..."
OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://192.168.1.83:11434/api/tags)
if [ "$OLLAMA_STATUS" = "200" ]; then
    echo "✅ Ollama服务运行正常 (HTTP $OLLAMA_STATUS)"
else
    echo "❌ Ollama服务连接失败 (HTTP $OLLAMA_STATUS)"
    exit 1
fi

# 检查健康模型是否存在
echo "🧠 检查ljwx-health-enhanced模型..."
MODEL_EXISTS=$(curl -s http://192.168.1.83:11434/api/tags | grep -c "ljwx-health-enhanced:latest")
if [ "$MODEL_EXISTS" -gt 0 ]; then
    echo "✅ ljwx-health-enhanced:latest 模型已加载"
else
    echo "❌ ljwx-health-enhanced:latest 模型未找到"
    echo "📋 可用模型列表:"
    curl -s http://192.168.1.83:11434/api/tags | python3 -c "import sys, json; models = json.load(sys.stdin)['models']; [print(f'  - {m[\"name\"]}') for m in models]"
    exit 1
fi

# 测试模型响应
echo "🧪 测试模型响应..."
RESP=$(curl -s -X POST http://192.168.1.83:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ljwx-health-enhanced:latest",
    "prompt": "简单回答：你好",
    "stream": false
  }')

if echo "$RESP" | grep -q '"done":true'; then
    echo "✅ 模型响应正常"
    RESPONSE_TEXT=$(echo "$RESP" | python3 -c "import sys, json; print(json.load(sys.stdin)['response'][:100] + '...')")
    echo "📝 响应内容: $RESPONSE_TEXT"
else
    echo "❌ 模型响应异常"
    echo "🔍 错误详情: $RESP"
    exit 1
fi

# 检查ljwx-boot是否运行
echo "🚀 检查ljwx-boot服务..."
if pgrep -f "ljwx-boot" > /dev/null; then
    echo "✅ ljwx-boot服务正在运行"
    BOOT_PID=$(pgrep -f "ljwx-boot")
    echo "📋 进程ID: $BOOT_PID"
else
    echo "⚠️ ljwx-boot服务未运行"
    echo "💡 请使用以下命令启动服务:"
    echo "   cd ljwx-boot && ./run-local.sh start"
fi

echo ""
echo "🎉 AI集成测试完成！"
echo ""
echo "📖 使用说明:"
echo "1. 确保ljwx-boot服务运行: cd ljwx-boot && ./run-local.sh start"
echo "2. 启动前端服务: cd ljwx-admin && npm run dev"
echo "3. 访问健康预测页面并点击'AI预测'按钮"
echo "4. 测试AI健康预测和建议功能"
echo ""
echo "🔗 相关链接:"
echo "- Ollama服务: http://192.168.1.83:11434"
echo "- 后端API: http://localhost:9998/t_health_prediction/ai/health"
echo "- 前端页面: http://localhost:3000/#/health/prediction"
