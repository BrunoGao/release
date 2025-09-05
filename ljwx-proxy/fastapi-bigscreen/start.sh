#!/bin/bash

echo "🚀 启动FastAPI大屏服务..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 启动服务
echo "🌟 启动FastAPI服务..."
echo "📊 大屏页面: http://localhost:8888/bigscreen"
echo "👤 个人页面: http://localhost:8888/personal"
echo "📖 API文档: http://localhost:8888/docs"
echo "⚡ 交互文档: http://localhost:8888/redoc"
echo ""

python main.py