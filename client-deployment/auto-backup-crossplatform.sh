#!/bin/bash
# 自动备份定时任务脚本 - 跨平台版本
# 支持: CentOS, macOS, Ubuntu, Debian

# 检测操作系统类型
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        OS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
    elif [[ -f /etc/centos-release ]] || [[ -f /etc/redhat-release ]]; then
        OS_TYPE="centos"
        OS_VERSION=$(cat /etc/centos-release 2>/dev/null | grep -o '[0-9]\+\.[0-9]\+' | head -1 || echo "unknown")
    elif [[ -f /etc/debian_version ]]; then
        if grep -q "Ubuntu" /etc/os-release 2>/dev/null; then
            OS_TYPE="ubuntu"
            OS_VERSION=$(grep VERSION_ID /etc/os-release | cut -d'"' -f2 || echo "unknown")
        else
            OS_TYPE="debian"
            OS_VERSION=$(cat /etc/debian_version 2>/dev/null || echo "unknown")
        fi
    else
        OS_TYPE="linux"
        OS_VERSION="unknown"
    fi
}

# 跨平台命令适配
get_compression_cmd() {
    case $OS_TYPE in
        "macos")
            echo "gunzip -c"  # macOS使用gunzip避免zcat问题
            ;;
        "centos"|"ubuntu"|"debian"|"linux")
            if command -v zcat >/dev/null 2>&1; then
                echo "zcat"  # Linux优先使用zcat
            else
                echo "gunzip -c"  # 备选gunzip
            fi
            ;;
        *)
            echo "gunzip -c"  # 默认使用gunzip
            ;;
    esac
}

# 跨平台文件大小获取
get_file_size() {
    local file="$1"
    case $OS_TYPE in
        "macos")
            ls -lh "$file" | awk '{print $5}'
            ;;
        "centos"|"ubuntu"|"debian"|"linux")
            ls -lh "$file" | awk '{print $5}'
            ;;
        *)
            ls -lh "$file" | awk '{print $5}'
            ;;
    esac
}

# 跨平台日期命令
get_timestamp() {
    case $OS_TYPE in
        "macos")
            date +%Y%m%d_%H%M%S
            ;;
        "centos"|"ubuntu"|"debian"|"linux")
            date +%Y%m%d_%H%M%S
            ;;
        *)
            date +%Y%m%d_%H%M%S
            ;;
    esac
}

# 初始化系统检测
detect_os
DECOMPRESS_CMD=$(get_compression_cmd)

# 配置变量
MYSQL_CONTAINER="ljwx-mysql"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
MYSQL_DATABASE="lj-06"
BACKUP_DIR="./backups"
VOLUME_NAME="client-deployment_mysql_data"
LOG_FILE="$BACKUP_DIR/auto_backup.log"

# 创建备份目录和日志文件
mkdir -p "$BACKUP_DIR"/{sql,volume,config,logs}
touch "$LOG_FILE"

# 日志记录函数
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$OS_TYPE] - $1" | tee -a "$LOG_FILE"
}

# 检查Docker和MySQL状态
check_services() {
    if ! docker info >/dev/null 2>&1; then
        log_message "❌ Docker服务未运行"
        return 1
    fi
    
    if ! docker ps | grep -q $MYSQL_CONTAINER; then
        log_message "❌ MySQL容器未运行"
        return 1
    fi
    
    if ! docker exec $MYSQL_CONTAINER mysqladmin ping -u $MYSQL_USER -p$MYSQL_PASSWORD >/dev/null 2>&1; then
        log_message "❌ MySQL连接失败"
        return 1
    fi
    
    return 0
}

# 创建SQL备份
create_sql_backup() {
    local backup_type=$1
    local timestamp=$(get_timestamp)
    local backup_file="$BACKUP_DIR/sql/ljwx_${backup_type}_${timestamp}.sql"
    
    log_message "📦 开始创建${backup_type}SQL备份"
    
    if docker exec $MYSQL_CONTAINER mysqldump \
        -u $MYSQL_USER -p$MYSQL_PASSWORD \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --add-drop-database \
        --databases $MYSQL_DATABASE > "$backup_file" 2>/dev/null; then
        
        # 压缩备份文件
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        
        # 计算文件大小
        local file_size=$(get_file_size "$backup_file")
        
        log_message "✅ SQL备份创建成功: $(basename "$backup_file") ($file_size)"
        
        # 记录备份信息
        echo "$(date '+%Y-%m-%d %H:%M:%S'),$backup_type,SQL,$backup_file,$file_size" >> "$BACKUP_DIR/backup_history.csv"
        
        return 0
    else
        log_message "❌ SQL备份失败"
        return 1
    fi
}

# 创建数据卷备份
create_volume_backup() {
    local backup_type=$1
    local timestamp=$(get_timestamp)
    local backup_file="$BACKUP_DIR/volume/mysql_${backup_type}_${timestamp}.tar.gz"
    
    log_message "🗃️  开始创建${backup_type}数据卷备份"
    
    if docker run --rm \
        -v $VOLUME_NAME:/source:ro \
        -v "$(pwd)/$BACKUP_DIR/volume":/backup \
        alpine:latest \
        tar -czf "/backup/mysql_${backup_type}_${timestamp}.tar.gz" -C /source . 2>/dev/null; then
        
        local file_size=$(get_file_size "$backup_file")
        
        log_message "✅ 数据卷备份创建成功: $(basename "$backup_file") ($file_size)"
        
        # 记录备份信息
        echo "$(date '+%Y-%m-%d %H:%M:%S'),$backup_type,VOLUME,$backup_file,$file_size" >> "$BACKUP_DIR/backup_history.csv"
        
        return 0
    else
        log_message "❌ 数据卷备份失败"
        return 1
    fi
}

# 清理旧备份
cleanup_old_backups() {
    local sql_retention_days=7
    local volume_retention_days=30
    
    log_message "🧹 开始清理旧备份文件"
    
    # 跨平台find命令
    case $OS_TYPE in
        "macos"|"centos"|"ubuntu"|"debian"|"linux")
            # 清理SQL备份
            find "$BACKUP_DIR/sql" -name "ljwx_daily_*.sql.gz" -mtime +$sql_retention_days -delete 2>/dev/null
            
            # 清理数据卷备份
            find "$BACKUP_DIR/volume" -name "mysql_weekly_*.tar.gz" -mtime +$volume_retention_days -delete 2>/dev/null
            ;;
    esac
    
    # 清理日志文件（保留最近1000行）
    if [ -f "$LOG_FILE" ]; then
        tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
}

# 生成备份报告
generate_backup_report() {
    log_message "📊 生成备份状态报告"
    
    local report_file="$BACKUP_DIR/backup_report_$(date +%Y%m%d).txt"
    
    cat > "$report_file" << EOF
LJWX MySQL备份状态报告 - $OS_TYPE $OS_VERSION
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
================================

📁 备份文件统计:
SQL备份文件数量: $(ls "$BACKUP_DIR/sql/"*.sql.gz 2>/dev/null | wc -l | tr -d ' ')
数据卷备份文件数量: $(ls "$BACKUP_DIR/volume/"*.tar.gz 2>/dev/null | wc -l | tr -d ' ')

💾 存储空间使用:
SQL备份总大小: $(du -sh "$BACKUP_DIR/sql" 2>/dev/null | cut -f1 || echo "0B")
数据卷备份总大小: $(du -sh "$BACKUP_DIR/volume" 2>/dev/null | cut -f1 || echo "0B")
总备份大小: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "0B")

📈 最近备份记录:
$(tail -5 "$BACKUP_DIR/backup_history.csv" 2>/dev/null || echo "暂无备份记录")

🔍 最新备份文件:
最新SQL备份: $(ls -t "$BACKUP_DIR/sql/"*.sql.gz 2>/dev/null | head -1 | xargs basename || echo "无")
最新数据卷备份: $(ls -t "$BACKUP_DIR/volume/"*.tar.gz 2>/dev/null | head -1 | xargs basename || echo "无")

📊 数据库状态:
数据库: $MYSQL_DATABASE
表数量: $(docker exec $MYSQL_CONTAINER mysql -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" 2>/dev/null | tail -1 || echo "未知")

🖥️ 系统信息:
操作系统: $OS_TYPE $OS_VERSION
解压命令: $DECOMPRESS_CMD

================================
EOF
    
    log_message "📄 备份报告已生成: $report_file"
}

# 主执行逻辑
main() {
    local backup_mode=${1:-"daily"}
    
    log_message "🚀 开始自动备份任务 - 模式: $backup_mode (系统: $OS_TYPE)"
    
    # 检查服务状态
    if ! check_services; then
        log_message "❌ 服务检查失败，备份任务终止"
        exit 1
    fi
    
    case $backup_mode in
        "daily")
            create_sql_backup "daily"
            cleanup_old_backups
            ;;
        "weekly")
            create_sql_backup "weekly"
            create_volume_backup "weekly"
            cleanup_old_backups
            generate_backup_report
            ;;
        "manual")
            create_sql_backup "manual"
            create_volume_backup "manual"
            generate_backup_report
            ;;
        *)
            log_message "❌ 无效的备份模式: $backup_mode"
            echo "使用方法: $0 [daily|weekly|manual]"
            exit 1
            ;;
    esac
    
    log_message "🎉 自动备份任务完成"
}

# 显示使用帮助
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF
LJWX MySQL自动备份工具 - 跨平台版本
支持: CentOS, macOS, Ubuntu, Debian

当前系统: $OS_TYPE $OS_VERSION

使用方法:
  $0 [模式]

备份模式:
  daily   - 每日备份（仅SQL备份）
  weekly  - 每周备份（SQL + 数据卷备份）
  manual  - 手动备份（完整备份）

定时任务设置:
  # 每日凌晨2点执行SQL备份
  0 2 * * * /path/to/auto-backup-crossplatform.sh daily

  # 每周日凌晨3点执行完整备份
  0 3 * * 0 /path/to/auto-backup-crossplatform.sh weekly

示例:
  ./auto-backup-crossplatform.sh daily    # 每日备份
  ./auto-backup-crossplatform.sh weekly   # 每周备份
  ./auto-backup-crossplatform.sh manual   # 手动完整备份

日志文件: $BACKUP_DIR/auto_backup.log
备份目录: $BACKUP_DIR/
EOF
    exit 0
fi

# 执行主程序
main "$@" 
