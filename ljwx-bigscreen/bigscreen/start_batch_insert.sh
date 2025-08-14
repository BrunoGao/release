#!/bin/bash
#批量数据插入启动脚本

echo "🚀 启动批量数据模拟..."
echo "📊 配置: 1000用户 × 30天 × 12小时/天 × 60分钟/小时 = 21,600,000条记录"
echo "⚠️  警告: 此操作将清空t_user_health_data表并插入大量数据"

read -p "确认继续? (y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ 操作已取消"
    exit 1
fi

#检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

#检查依赖包
python3 -c "import mysql.connector" 2>/dev/null || {
    echo "❌ mysql-connector-python未安装"
    echo "💡 安装命令: pip3 install mysql-connector-python"
    exit 1
}

#设置日志文件
LOG_FILE="batch_insert_$(date +%Y%m%d_%H%M%S).log"
echo "📝 日志文件: $LOG_FILE"

#启动批处理
echo "🔄 开始执行..."
python3 batch_insert_1000_users.py 2>&1 | tee "$LOG_FILE"

echo "✅ 批处理完成，日志已保存到 $LOG_FILE" 