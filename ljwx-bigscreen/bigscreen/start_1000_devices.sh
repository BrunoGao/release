#!/bin/bash
# 1000台手表批量模拟启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMULATOR="$SCRIPT_DIR/device_batch_simulator.py"

echo "🚀 1000台手表批量数据模拟器"
echo "=================================="

# 检查依赖
python3 -c "import requests,mysql.connector" 2>/dev/null || {
    echo "❌ 缺少Python依赖，正在安装..."
    pip3 install requests mysql-connector-python
}

# 检查大屏服务
echo "🔍 检查大屏服务状态..."
if curl -s http://localhost:5001/main?customerId=1 >/dev/null 2>&1; then
    echo "✅ 大屏服务运行正常"
else
    echo "❌ 大屏服务未运行，请先启动："
    echo "   cd ljwx-bigscreen/bigscreen && python3 run.py"
    exit 1
fi

show_menu() {
    echo ""
    echo "请选择操作模式："
    echo "1. 完整模拟 (注册设备+创建用户+持续上传)"
    echo "2. 仅上传模式 (使用已有设备数据)"
    echo "3. 快速测试 (10台设备)"
    echo "4. 自定义设置"
    echo "5. 帮助信息"
    echo "0. 退出"
    echo ""
    read -p "请输入选项 [1-5,0]: " choice
}

case "${1:-menu}" in
    "full"|"1")
        echo "🔄 启动完整模拟流程 (1000台设备)"
        python3 "$SIMULATOR" --count 1000 --interval 10
        ;;
    "upload"|"2")
        echo "📊 启动仅上传模式"
        python3 "$SIMULATOR" --upload-only --count 1000 --interval 10
        ;;
    "test"|"3")
        echo "🧪 启动快速测试 (10台设备)"
        python3 "$SIMULATOR" --count 10 --interval 5
        ;;
    "custom"|"4")
        echo "⚙️ 自定义设置模式"
        read -p "设备数量 [默认1000]: " count
        read -p "上传间隔(秒) [默认10]: " interval
        read -p "跳过设备注册? (y/N): " skip_reg
        read -p "跳过用户创建? (y/N): " skip_user
        
        args=""
        [ -n "$count" ] && args="$args --count $count"
        [ -n "$interval" ] && args="$args --interval $interval"
        [[ "$skip_reg" =~ ^[Yy]$ ]] && args="$args --skip-register"
        [[ "$skip_user" =~ ^[Yy]$ ]] && args="$args --skip-users"
        
        echo "🔧 启动自定义模拟: $args"
        python3 "$SIMULATOR" $args
        ;;
    "help"|"5")
        echo "📖 使用说明："
        echo ""
        echo "完整流程包括："
        echo "1. 📱 注册1000台设备到数据库"
        echo "2. 👥 创建1000个用户记录"
        echo "3. 🔗 建立用户-组织关系"
        echo "4. 📊 每10秒上传1000条健康数据"
        echo ""
        echo "命令行用法："
        echo "  $0 full          # 完整模拟"
        echo "  $0 upload        # 仅上传"
        echo "  $0 test          # 快速测试"
        echo "  $0 custom        # 自定义"
        echo ""
        echo "Python脚本直接调用："
        echo "  python3 device_batch_simulator.py --help"
        ;;
    "menu"|*)
        while true; do
            show_menu
            case $choice in
                1) $0 full; break ;;
                2) $0 upload; break ;;
                3) $0 test; break ;;
                4) $0 custom; break ;;
                5) $0 help ;;
                0) echo "👋 退出程序"; exit 0 ;;
                *) echo "❌ 无效选项，请重新选择" ;;
            esac
        done
        ;;
esac 