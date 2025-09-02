#!/bin/bash
# 自动备份定时任务脚本 - 支持每日/每周备份策略

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
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
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
    local timestamp=$(date +%Y%m%d_%H%M%S)
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
        local file_size=$(ls -lh "$backup_file" | awk '{print $5}')
        
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
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/volume/mysql_${backup_type}_${timestamp}.tar.gz"
    
    log_message "🗃️  开始创建${backup_type}数据卷备份"
    
    if docker run --rm \
        -v $VOLUME_NAME:/source:ro \
        -v "$(pwd)/$BACKUP_DIR/volume":/backup \
        alpine:latest \
        tar -czf "/backup/mysql_${backup_type}_${timestamp}.tar.gz" -C /source . 2>/dev/null; then
        
        local file_size=$(ls -lh "$backup_file" | awk '{print $5}')
        
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
    
    # 清理SQL备份
    find "$BACKUP_DIR/sql" -name "ljwx_daily_*.sql.gz" -mtime +$sql_retention_days -delete 2>/dev/null
    
    # 清理数据卷备份
    find "$BACKUP_DIR/volume" -name "mysql_weekly_*.tar.gz" -mtime +$volume_retention_days -delete 2>/dev/null
    
    # 清理日志文件（保留最近1000行）
    if [ -f "$LOG_FILE" ]; then
        tail -1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
    fi
}

# 主执行逻辑
main() {
    local backup_mode=${1:-"daily"}
    
    log_message "🚀 开始自动备份任务 - 模式: $backup_mode"
    
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
            ;;
        "manual")
            create_sql_backup "manual"
            create_volume_backup "manual"
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
LJWX MySQL自动备份工具

使用方法:
  $0 [模式]

备份模式:
  daily   - 每日备份（仅SQL备份）
  weekly  - 每周备份（SQL + 数据卷备份）
  manual  - 手动备份（完整备份）

定时任务设置:
  # 每日凌晨2点执行SQL备份
  0 2 * * * /path/to/auto-backup.sh daily

  # 每周日凌晨3点执行完整备份
  0 3 * * 0 /path/to/auto-backup.sh weekly

示例:
  ./auto-backup.sh daily    # 每日备份
  ./auto-backup.sh weekly   # 每周备份
  ./auto-backup.sh manual   # 手动完整备份

日志文件: $BACKUP_DIR/auto_backup.log
备份目录: $BACKUP_DIR/
EOF
    exit 0
fi

# 执行主程序
main "$@" 
