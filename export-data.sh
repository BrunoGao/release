#!/bin/bash
# MySQL数据导出脚本
# 用于导出测试数据库到data.sql文件，供Docker镜像构建使用

set -e

# 默认数据库配置
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="3306"
DEFAULT_USER="root"
DEFAULT_PASSWORD="123456"
DEFAULT_DATABASE="test"
OUTPUT_FILE="data.sql"

# 获取配置参数（支持环境变量或命令行参数）
DB_HOST=${DB_HOST:-$DEFAULT_HOST}
DB_PORT=${DB_PORT:-$DEFAULT_PORT}
DB_USER=${DB_USER:-$DEFAULT_USER}
DB_PASSWORD=${DB_PASSWORD:-$DEFAULT_PASSWORD}
DB_NAME=${DB_NAME:-$DEFAULT_DATABASE}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            DB_HOST="$2"
            shift 2
            ;;
        --port)
            DB_PORT="$2"
            shift 2
            ;;
        --user)
            DB_USER="$2"
            shift 2
            ;;
        --password)
            DB_PASSWORD="$2"
            shift 2
            ;;
        --database)
            DB_NAME="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "MySQL数据导出脚本"
            echo ""
            echo "用法:"
            echo "  $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --host HOST       数据库主机 (默认: $DEFAULT_HOST)"
            echo "  --port PORT       数据库端口 (默认: $DEFAULT_PORT)"
            echo "  --user USER       数据库用户名 (默认: $DEFAULT_USER)"
            echo "  --password PASS   数据库密码 (默认: $DEFAULT_PASSWORD)"
            echo "  --database DB     数据库名称 (默认: $DEFAULT_DATABASE)"
            echo "  --output FILE     输出文件名 (默认: $OUTPUT_FILE)"
            echo "  --help, -h        显示此帮助信息"
            echo ""
            echo "环境变量支持:"
            echo "  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME"
            echo ""
            echo "示例:"
            echo "  $0                                    # 使用默认配置"
            echo "  $0 --host 192.168.1.100 --database prod"
            echo "  DB_PASSWORD=mypass $0 --database prod"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

echo "🗄️ MySQL数据导出工具"
echo "📋 导出配置:"
echo "   主机: $DB_HOST:$DB_PORT"
echo "   数据库: $DB_NAME"
echo "   用户: $DB_USER"
echo "   输出文件: $OUTPUT_FILE"
echo ""

# 检查mysqldump命令是否可用
if ! command -v mysqldump >/dev/null 2>&1; then
    echo "❌ 错误: 未找到 mysqldump 命令"
    echo "💡 请安装 MySQL 客户端工具"
    exit 1
fi

# 检查数据库连接
echo "🔍 检查数据库连接..."
if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" 2>/dev/null; then
    echo "❌ 错误: 无法连接到数据库"
    echo "💡 请检查数据库配置和网络连接"
    exit 1
fi
echo "✅ 数据库连接成功"

# 检查数据库是否有数据
echo "📊 检查数据库内容..."
table_count=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';" --silent --skip-column-names)

if [ "$table_count" -eq 0 ]; then
    echo "⚠️ 警告: 数据库 '$DB_NAME' 中没有找到任何表"
    echo "💡 确认数据库名称是否正确？"
    read -p "是否继续导出空数据库? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "已取消导出"
        exit 0
    fi
else
    echo "✅ 发现 $table_count 个表"
fi

# 备份现有的data.sql文件
if [ -f "$OUTPUT_FILE" ]; then
    backup_file="${OUTPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📁 备份现有文件: $OUTPUT_FILE → $backup_file"
    cp "$OUTPUT_FILE" "$backup_file"
fi

# 执行数据导出
echo "🚀 开始导出数据..."
echo "⏱️  正在导出，请稍候..."

# 使用mysqldump导出数据，包含结构和数据
mysqldump \
    -h"$DB_HOST" \
    -P"$DB_PORT" \
    -u"$DB_USER" \
    -p"$DB_PASSWORD" \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --complete-insert \
    --extended-insert \
    --hex-blob \
    --default-character-set=utf8mb4 \
    --add-drop-database \
    --add-drop-table \
    --create-options \
    --disable-keys \
    --lock-tables=false \
    "$DB_NAME" > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 数据导出成功!"
    echo "📁 输出文件: $OUTPUT_FILE"
    
    # 显示文件信息
    file_size=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo "📊 文件大小: $file_size"
    
    # 显示内容统计
    line_count=$(wc -l < "$OUTPUT_FILE")
    echo "📋 文件行数: $line_count"
    
    # 检查导出内容的简要统计
    echo ""
    echo "📈 导出内容统计:"
    echo "   表结构: $(grep -c "CREATE TABLE" "$OUTPUT_FILE") 个"
    echo "   插入语句: $(grep -c "INSERT INTO" "$OUTPUT_FILE") 个"
    echo "   视图: $(grep -c "CREATE.*VIEW" "$OUTPUT_FILE") 个"
    echo "   存储过程: $(grep -c "CREATE.*PROCEDURE" "$OUTPUT_FILE") 个"
    echo "   函数: $(grep -c "CREATE.*FUNCTION" "$OUTPUT_FILE") 个"
    
else
    echo "❌ 数据导出失败"
    exit 1
fi

echo ""
echo "🎉 数据导出完成!"
echo "💡 现在可以运行 Docker 构建命令来创建包含数据的 MySQL 镜像"