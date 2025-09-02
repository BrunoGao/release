#!/bin/bash
# 1000台手表完整演示脚本

echo "🚀 1000台华为手表批量数据模拟演示"
echo "=================================="
echo "本演示将完整展示1000台手表的："
echo "1. 📱 批量设备注册"
echo "2. 👥 用户账户创建" 
echo "3. 🔗 组织关系建立"
echo "4. 📊 实时健康数据上传"
echo "5. 📈 性能监控与分析"
echo ""

# 检查服务状态
echo "🔍 检查大屏服务状态..."
if ! curl -s http://localhost:5001/main?customerId=1 >/dev/null 2>&1; then
    echo "❌ 大屏服务未运行！请先启动："
    echo "   cd ljwx-bigscreen/bigscreen && python3 run.py"
    exit 1
fi
echo "✅ 大屏服务运行正常"

echo ""
read -p "⚠️  警告：这将向数据库插入1000台设备和1000个用户，是否继续？(y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "取消演示"
    exit 0
fi

echo ""
echo "🎬 开始演示流程..."

# 启动性能监控(后台)
echo "📊 启动性能监控..."
python3 performance_monitor.py --interval 60 > performance_report.log 2>&1 &
MONITOR_PID=$!
echo "性能监控已启动 (PID: $MONITOR_PID)"

# 等待3秒
sleep 3

# 启动1000台设备模拟
echo ""
echo "🚀 启动1000台设备模拟..."
echo "参数: --count 1000 --interval 10"
echo "预估时间: 设备注册约2分钟，用户创建约1分钟"
echo ""

python3 device_batch_simulator.py --count 1000 --interval 10 &
SIMULATOR_PID=$!

echo "设备模拟器已启动 (PID: $SIMULATOR_PID)"
echo ""
echo "📱 正在进行设备注册和用户创建..."

# 等待初始化完成(约3分钟)
sleep 180

echo ""
echo "📊 生成性能报告..."
python3 performance_monitor.py --once

echo ""
echo "📈 查看实时日志统计..."
echo "最近设备日志:"
tail -5 logs/device_text.log

echo ""
echo "最近健康数据日志:"
tail -5 logs/health_data_text.log

echo ""
echo "📋 数据库统计查询..."
python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='127.0.0.1', port=3306, user='root', 
        password='123456', database='lj-06'
    )
    cursor = conn.cursor()
    
    # 统计新增设备
    cursor.execute(\"SELECT COUNT(*) FROM t_device_info WHERE device_sn LIKE 'A5GTQ24B26%'\")
    device_count = cursor.fetchone()[0]
    
    # 统计新增用户
    cursor.execute(\"SELECT COUNT(*) FROM sys_user WHERE device_sn LIKE 'A5GTQ24B26%'\")
    user_count = cursor.fetchone()[0]
    
    # 统计今日健康数据
    cursor.execute(\"SELECT COUNT(*) FROM t_user_health_data WHERE DATE(create_time) = CURDATE()\")
    health_count = cursor.fetchone()[0]
    
    print(f'📱 模拟设备数量: {device_count:,}')
    print(f'👥 创建用户数量: {user_count:,}')  
    print(f'📊 今日健康数据: {health_count:,}')
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f'查询失败: {e}')
" 2>/dev/null || echo "数据库查询失败"

echo ""
echo "🌐 大屏访问地址:"
echo "http://localhost:5001/main?customerId=1"

echo ""
echo "⏱️  演示运行中..."
echo "💡 提示:"
echo "   - 每10秒上传1000条健康数据"
echo "   - 使用 Ctrl+C 停止演示"
echo "   - 查看日志: tail -f logs/system_text.log"
echo "   - 性能监控: tail -f performance_report.log"

# 等待用户中断
trap 'echo ""; echo "🛑 停止演示..."; kill $SIMULATOR_PID 2>/dev/null; kill $MONITOR_PID 2>/dev/null; echo "演示已结束"; exit 0' INT

# 持续显示统计信息
while true; do
    sleep 30
    echo ""
    echo "⏰ $(date '+%H:%M:%S') - 演示进行中..."
    
    # 快速统计
    latest_count=$(python3 -c "
import mysql.connector
try:
    conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='lj-06')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM t_user_health_data WHERE create_time >= DATE_SUB(NOW(), INTERVAL 1 MINUTE)')
    print(cursor.fetchone()[0])
    cursor.close()
    conn.close()
except:
    print(0)
" 2>/dev/null)
    
    echo "📊 最近1分钟新增数据: $latest_count 条"
done 