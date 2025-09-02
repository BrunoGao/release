#!/bin/bash
# 大屏性能优化测试脚本
# 用于快速验证1000用户环境下的性能提升效果

echo "🚀 大屏性能优化测试工具"
echo "========================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到python3，请先安装Python3"
    exit 1
fi

# 检查requests模块
if ! python3 -c "import requests" &> /dev/null; then
    echo "❌ 未找到requests模块，正在安装..."
    pip3 install requests
fi

# 检查Flask服务是否运行
echo "🔍 检查Flask服务状态..."
if curl -s http://127.0.0.1:5001/api/statistics/overview?orgId=1 > /dev/null; then
    echo "✅ Flask服务运行正常"
else
    echo "❌ Flask服务未运行，请先启动bigscreen服务"
    echo "💡 启动命令: cd ljwx-bigscreen/bigscreen && python3 bigScreen.py"
    exit 1
fi

# 显示菜单
echo ""
echo "请选择测试模式:"
echo "1. 快速测试 (推荐)"
echo "2. 详细测试"  
echo "3. 仅测试优化版本"
echo "4. 退出"
echo ""

read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo "🔄 启动快速性能测试..."
        python3 quick_test_optimization.py
        ;;
    2)
        echo "🔄 启动详细性能测试..."
        python3 test_performance_optimization.py
        ;;
    3)
        echo "🔄 仅测试优化版本..."
        echo "测试优化版本API..."
        start_time=$(date +%s.%N)
        response=$(curl -s "http://127.0.0.1:5001/get_total_info_optimized?customer_id=1")
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        
        if [[ $response == *"success"* ]]; then
            echo "✅ 优化版本测试成功!"
            echo "⏱️  响应时间: ${duration}秒"
            echo "📊 响应数据: ${response:0:200}..."
        else
            echo "❌ 优化版本测试失败"
        fi
        ;;
    4)
        echo "👋 退出测试"
        exit 0
        ;;
    *)
        echo "❌ 无效选择，请重新运行脚本"
        exit 1
        ;;
esac

echo ""
echo "📖 更多信息:"
echo "- 技术文档: README.md 性能优化章节"
echo "- 源码地址: bigScreen.py (line 1982: get_total_info_optimized)"
echo "- 优化技术: N+1查询优化、并发处理、Redis缓存、自动优化" 