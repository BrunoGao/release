#!/bin/bash
# -*- coding: utf-8 -*-

# 消息系统V2迁移执行脚本
# 
# 使用方法:
# 1. 预演模式: ./run_message_v2_migration.sh --dry-run
# 2. 正式迁移: ./run_message_v2_migration.sh --migrate
# 3. 查看状态: ./run_message_v2_migration.sh --status
# 4. 回滚迁移: ./run_message_v2_migration.sh --rollback /path/to/backup.sql

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "消息系统V2迁移脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --dry-run              预演模式（不执行实际操作）"
    echo "  --migrate              执行正式迁移"
    echo "  --force                强制迁移（即使已完成）"
    echo "  --status               查看迁移状态"
    echo "  --rollback BACKUP_PATH 回滚到指定备份"
    echo "  --config CONFIG_FILE   指定配置文件（默认：migration_config.json）"
    echo "  --database-url URL     数据库连接URL"
    echo "  --log-level LEVEL      日志级别（DEBUG|INFO|WARN|ERROR）"
    echo "  --help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --dry-run                                    # 预演迁移"
    echo "  $0 --migrate                                    # 执行迁移"
    echo "  $0 --migrate --force                            # 强制重新迁移"
    echo "  $0 --status                                     # 查看状态"
    echo "  $0 --rollback ./backups/backup_20250911.sql    # 回滚迁移"
    echo "  $0 --migrate --database-url mysql://user:pass@host:3306/db  # 指定数据库"
    echo ""
}

# 检查Python环境
check_python_env() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python3"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python版本: $python_version"
    
    # 检查必需的Python包
    required_packages=("sqlalchemy" "pymysql" "redis" "psutil")
    missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            missing_packages+=($package)
        fi
    done
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        log_warn "以下Python包未安装: ${missing_packages[*]}"
        log_info "正在安装缺失的包..."
        
        for package in "${missing_packages[@]}"; do
            log_info "安装 $package..."
            pip3 install "$package" || {
                log_error "安装 $package 失败"
                exit 1
            }
        done
    fi
    
    log_info "✅ Python环境检查通过"
}

# 检查数据库连接
check_database_connection() {
    local database_url="$1"
    
    if [ -z "$database_url" ]; then
        # 从配置文件读取
        if [ -f "migrations/migration_config.json" ]; then
            database_url=$(python3 -c "
import json
with open('migrations/migration_config.json', 'r') as f:
    config = json.load(f)
print(config.get('database_url', ''))
" 2>/dev/null || echo "")
        fi
    fi
    
    if [ -z "$database_url" ]; then
        log_error "未指定数据库连接URL，请在配置文件中设置或使用 --database-url 参数"
        exit 1
    fi
    
    log_info "检查数据库连接: $database_url"
    
    # 使用Python检查连接
    python3 -c "
import sys
from sqlalchemy import create_engine, text
try:
    engine = create_engine('$database_url')
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('✅ 数据库连接正常')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    sys.exit(1)
" || exit 1
}

# 检查MySQL工具
check_mysql_tools() {
    log_info "检查MySQL工具..."
    
    if ! command -v mysqldump &> /dev/null; then
        log_warn "mysqldump 未找到，备份功能可能无法使用"
        log_info "请安装MySQL客户端工具: apt-get install mysql-client 或 yum install mysql"
    else
        log_info "✅ mysqldump 可用"
    fi
    
    if ! command -v mysql &> /dev/null; then
        log_warn "mysql 客户端未找到，回滚功能可能无法使用"
    else
        log_info "✅ mysql 客户端可用"
    fi
}

# 创建备份目录
ensure_backup_directory() {
    local backup_dir="./backups"
    
    if [ ! -d "$backup_dir" ]; then
        log_info "创建备份目录: $backup_dir"
        mkdir -p "$backup_dir"
    fi
    
    # 检查目录权限
    if [ ! -w "$backup_dir" ]; then
        log_error "备份目录无写权限: $backup_dir"
        exit 1
    fi
}

# 执行迁移
run_migration() {
    local mode="$1"
    local extra_args="$2"
    
    log_info "开始执行消息系统V2迁移..."
    log_info "模式: $mode"
    
    # 构建Python命令
    python_cmd="python3 migrations/message_v2_migration.py"
    
    if [ "$mode" = "dry-run" ]; then
        python_cmd="$python_cmd --dry-run"
        log_info "🔍 预演模式：将显示要执行的操作但不实际执行"
    elif [ "$mode" = "migrate" ]; then
        log_info "🚀 正式迁移模式：将执行实际的数据库操作"
    fi
    
    if [ -n "$extra_args" ]; then
        python_cmd="$python_cmd $extra_args"
    fi
    
    # 执行迁移命令
    log_info "执行命令: $python_cmd"
    
    if $python_cmd; then
        log_info "✅ 迁移执行完成"
        
        if [ "$mode" = "migrate" ]; then
            # 显示迁移后的状态
            log_info "📊 迁移后状态:"
            python3 migrations/message_v2_migration.py --status
        fi
        
        return 0
    else
        log_error "❌ 迁移执行失败"
        
        # 显示可能的解决方案
        log_info "💡 可能的解决方案:"
        log_info "1. 检查数据库连接配置"
        log_info "2. 确保数据库用户有足够权限"
        log_info "3. 检查磁盘空间是否充足"
        log_info "4. 查看详细日志: cat migration.log"
        
        return 1
    fi
}

# 主函数
main() {
    local mode=""
    local extra_args=""
    local database_url=""
    local config_file=""
    local rollback_path=""
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                mode="dry-run"
                shift
                ;;
            --migrate)
                mode="migrate"
                shift
                ;;
            --force)
                extra_args="$extra_args --force"
                shift
                ;;
            --status)
                mode="status"
                shift
                ;;
            --rollback)
                mode="rollback"
                rollback_path="$2"
                shift 2
                ;;
            --config)
                config_file="$2"
                extra_args="$extra_args --config $2"
                shift 2
                ;;
            --database-url)
                database_url="$2"
                extra_args="$extra_args --database-url $2"
                shift 2
                ;;
            --log-level)
                extra_args="$extra_args --log-level $2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定模式，显示帮助
    if [ -z "$mode" ]; then
        show_help
        exit 1
    fi
    
    log_info "🚀 消息系统V2迁移工具启动"
    log_info "时间: $(date)"
    log_info "工作目录: $(pwd)"
    
    # 环境检查
    if [ "$mode" != "status" ]; then
        check_python_env
        check_database_connection "$database_url"
        check_mysql_tools
        ensure_backup_directory
    fi
    
    # 根据模式执行操作
    case "$mode" in
        "dry-run")
            log_info "🔍 开始预演迁移..."
            run_migration "dry-run" "$extra_args"
            ;;
        "migrate")
            # 确认操作
            if [ -t 0 ]; then  # 检查是否在交互终端
                echo ""
                log_warn "⚠️  即将执行数据库迁移操作，这将修改数据库结构！"
                log_warn "   建议先执行 --dry-run 预览操作"
                echo ""
                read -p "确认继续？(y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "操作已取消"
                    exit 0
                fi
            fi
            
            log_info "🚀 开始正式迁移..."
            run_migration "migrate" "$extra_args"
            ;;
        "status")
            log_info "📊 查看迁移状态..."
            python3 migrations/message_v2_migration.py --status
            ;;
        "rollback")
            if [ -z "$rollback_path" ]; then
                log_error "回滚操作需要指定备份文件路径"
                exit 1
            fi
            
            if [ ! -f "$rollback_path" ]; then
                log_error "备份文件不存在: $rollback_path"
                exit 1
            fi
            
            # 确认回滚操作
            if [ -t 0 ]; then
                echo ""
                log_warn "⚠️  即将回滚数据库到备份状态！"
                log_warn "   这将丢失备份时间点之后的所有数据！"
                log_warn "   备份文件: $rollback_path"
                echo ""
                read -p "确认回滚？(y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    log_info "回滚操作已取消"
                    exit 0
                fi
            fi
            
            log_info "🔄 开始回滚迁移..."
            python3 migrations/message_v2_migration.py --rollback "$rollback_path"
            ;;
    esac
    
    log_info "✅ 操作完成"
}

# 设置错误处理
trap 'log_error "脚本执行出错，退出码: $?"; exit 1' ERR

# 执行主函数
main "$@"