#!/bin/bash

# 异步健康数据处理系统压力测试启动脚本

set -e

echo "🚀 异步健康数据处理系统压力测试"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖包..."
python3 -c "import asyncio, aiohttp, statistics" 2>/dev/null || {
    echo "❌ 缺少必要的依赖包，正在安装..."
    pip3 install aiohttp statistics
}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 确保日志目录存在
mkdir -p logs

echo "📍 当前目录: $PWD"
echo "📝 日志目录: $PWD/logs"
echo ""

# 显示测试选项菜单
show_menu() {
    echo "📊 选择测试场景:"
    echo "1) 快速验证测试 (100台设备, 5分钟)"
    echo "2) 中等负载测试 (500台设备, 8分钟)" 
    echo "3) 高并发压力测试 (1000台设备, 10分钟) ⭐ 推荐"
    echo "4) 极限负载测试 (2000台设备, 15分钟)"
    echo "5) 批量处理专项测试 (批量优化验证)"
    echo "6) 系统集成测试 (测试异步组件状态)"
    echo "7) 自定义参数测试"
    echo "8) 退出"
    echo ""
}

# 运行测试的函数
run_test() {
    local devices=$1
    local concurrent=$2
    local duration=$3
    local interval=$4
    local url=${5:-"http://localhost:5225"}
    local extra_args=$6
    
    echo "🎯 开始压力测试..."
    echo "   设备数: $devices 台"
    echo "   并发数: $concurrent"
    echo "   时长: $duration 分钟"
    echo "   间隔: $interval 秒"
    echo "   URL: $url"
    echo ""
    
    # 运行测试
    python3 async_health_stress_test.py \
        --devices "$devices" \
        --concurrent "$concurrent" \
        --duration "$duration" \
        --interval "$interval" \
        --url "$url" \
        $extra_args
}

# 检查ljwx-bigscreen服务状态
check_service_status() {
    local url=${1:-"http://localhost:5225"}
    
    echo "🔍 检查服务状态: $url"
    
    # 检查健康检查端点
    if curl -s -f "$url/health" >/dev/null 2>&1; then
        echo "✅ 服务运行正常"
        return 0
    elif curl -s -f "$url/api/health" >/dev/null 2>&1; then
        echo "✅ 服务运行正常 (通过备用端点)"
        return 0
    else
        echo "⚠️  警告: 无法连接到服务，请确保 ljwx-bigscreen 正在运行"
        echo "   请检查服务是否在 $url 上运行"
        return 1
    fi
}

# 主菜单循环
main() {
    echo "🏥 欢迎使用异步健康数据处理系统压力测试工具!"
    echo ""
    
    # 默认URL检测
    DEFAULT_URL="http://localhost:5225"
    if ! check_service_status "$DEFAULT_URL"; then
        echo ""
        echo "💡 如果服务运行在其他端口，请选择自定义参数测试"
    fi
    echo ""
    
    while true; do
        show_menu
        read -p "请选择 (1-8): " choice
        echo ""
        
        case $choice in
            1)
                echo "🏃 快速验证测试"
                run_test 100 50 5 1.0
                ;;
            2)
                echo "🏋️ 中等负载测试"
                run_test 500 80 8 0.8
                ;;
            3)
                echo "🚀 高并发压力测试 (推荐)"
                echo "这是测试1000台手表并发的主要测试场景"
                run_test 1000 100 10 0.5
                ;;
            4)
                echo "🔥 极限负载测试"
                echo "⚠️  这将对系统产生极大压力，确保系统资源充足"
                read -p "确认继续? (y/N): " confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    run_test 2000 150 15 0.3
                else
                    echo "已取消"
                fi
                ;;
            5)
                echo "📦 批量处理专项测试"
                run_test 500 50 5 2.0
                ;;
            6)
                echo "🔧 系统集成测试"
                python3 async_health_stress_test.py --integration-test
                ;;
            7)
                echo "⚙️  自定义参数测试"
                read -p "设备数量 (默认: 1000): " devices
                read -p "并发数 (默认: 100): " concurrent  
                read -p "测试时长/分钟 (默认: 10): " duration
                read -p "上传间隔/秒 (默认: 0.5): " interval
                read -p "服务URL (默认: http://localhost:5225): " url
                
                devices=${devices:-1000}
                concurrent=${concurrent:-100}
                duration=${duration:-10}
                interval=${interval:-0.5}
                url=${url:-"http://localhost:5225"}
                
                run_test "$devices" "$concurrent" "$duration" "$interval" "$url"
                ;;
            8)
                echo "👋 退出测试工具"
                exit 0
                ;;
            *)
                echo "❌ 无效选择，请重新选择"
                ;;
        esac
        
        echo ""
        echo "=========================================="
        echo "💡 测试完成，查看上方日志了解详细结果"
        echo "📁 详细日志保存在: $PWD/logs/"
        echo "=========================================="
        echo ""
        
        read -p "按回车键继续，或输入 'q' 退出: " continue
        if [[ $continue =~ ^[Qq]$ ]]; then
            echo "👋 退出测试工具"
            break
        fi
        
        clear
    done
}

# 检查是否有命令行参数
if [ $# -eq 0 ]; then
    # 交互式模式
    main
else
    # 命令行模式
    case "$1" in
        "quick")
            echo "🏃 快速验证测试"
            run_test 100 50 5 1.0 "http://localhost:5225"
            ;;
        "standard")
            echo "🚀 标准1000台压力测试"
            run_test 1000 100 10 0.5 "http://localhost:5225"
            ;;
        "extreme")
            echo "🔥 极限2000台压力测试"
            run_test 2000 150 15 0.3 "http://localhost:5225"
            ;;
        "integration")
            echo "🔧 系统集成测试"
            python3 async_health_stress_test.py --integration-test
            ;;
        *)
            echo "用法: $0 [quick|standard|extreme|integration]"
            echo "或直接运行 $0 进入交互模式"
            exit 1
            ;;
    esac
fi