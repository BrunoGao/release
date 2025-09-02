#!/bin/bash
# ljwx测试框架快速启动脚本

echo "🚀 ljwx标准化测试框架"
echo "======================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 进入测试目录
cd "$(dirname "$0")/tests" || exit 1

case "$1" in
    "web")
        echo "🌐 启动Web界面..."
        echo "访问地址: http://localhost:5001/test"
        cd ../bigscreen && python app.py
        ;;
    "cli")
        echo "💻 命令行模式"
        python -m cli.runner "${@:2}"
        ;;
    "list")
        echo "📋 可用测试列表:"
        python -m cli.runner list
        ;;
    "run")
        echo "🧪 运行测试: $2"
        python -m cli.runner run "$2"
        ;;
    "all")
        echo "🚀 运行所有测试..."
        python -m cli.runner run --all --parallel
        ;;
    "report")
        echo "📊 生成测试报告..."
        python -m cli.runner report --format html
        ;;
    *)
        echo "使用方法:"
        echo "  $0 web      - 启动Web界面"
        echo "  $0 cli      - 命令行模式"
        echo "  $0 list     - 列出测试"
        echo "  $0 run <名称> - 运行指定测试"
        echo "  $0 all      - 运行所有测试"
        echo "  $0 report   - 生成报告"
        ;;
esac
