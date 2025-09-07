#!/bin/bash

# 自动化数据上传脚本 - 上传过去30天的数据，每5分钟一次
# 作者: Claude Code AI Assistant
# 日期: 2025-09-07

echo "🚀 自动化数据上传工具 - 30天历史数据"
echo "======================================"
echo ""

# 检查Python环境
if [ ! -d "test_env" ]; then
    echo "❌ 虚拟环境不存在，请先运行 python3 -m venv test_env"
    exit 1
fi

# 激活虚拟环境
source test_env/bin/activate

echo "📊 即将开始上传过去30天的数据："
echo "   • 时间间隔: 每5分钟一次"
echo "   • 预计操作数: ~25,920 次"
echo "   • 预计耗时: 3-4 小时"
echo "   • 支持中断恢复"
echo ""

# 检查是否有进度文件
if [ -f "progress_state.json" ]; then
    echo "🔄 发现进度文件，将从上次中断处继续"
    python background_uploader.py status
    echo ""
fi

echo "选择运行方式:"
echo "1. 前台运行（可以看到实时日志）"
echo "2. 后台运行（nohup方式）"
echo "3. 查看当前进度状态"
echo "4. 重置进度（重新开始）"
echo "5. 开始持续上传（当前数据）"
echo ""

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "🖥️  前台运行模式"
        echo "💡 按 Ctrl+C 可以安全中断并保存进度"
        echo ""
        sleep 2
        python background_uploader.py start 30
        ;;
    2)
        echo "📡 后台运行模式"
        nohup python background_uploader.py start 30 > upload_30days.log 2>&1 &
        PID=$!
        echo "✅ 后台任务已启动 (PID: $PID)"
        echo "📄 日志文件: upload_30days.log"
        echo "📊 查看进度: python background_uploader.py status"
        echo "🛑 停止任务: kill $PID"
        echo ""
        echo "监控命令:"
        echo "  tail -f upload_30days.log         # 实时查看日志"
        echo "  python background_uploader.py status  # 查看进度"
        ;;
    3)
        echo "📊 当前进度状态:"
        python background_uploader.py status
        ;;
    4)
        echo "🗑️  重置进度..."
        python background_uploader.py reset
        echo "✅ 进度已重置，可以重新开始"
        ;;
    5)
        echo "🔄 持续上传模式（每5分钟上传当前数据）"
        echo "💡 按 Ctrl+C 停止"
        python background_uploader.py continuous
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 操作完成"