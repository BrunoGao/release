#!/bin/bash
# MySQL每日定时备份脚本 - 极致优化版

CONTAINER_NAME="ljwx-mysql"
MYSQL_USER="root"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"
BACKUP_DIR="backup/mysql"
LOG_FILE="logs/mysql-backup.log"
BACKUP_RETENTION_DAYS=7 #保留7天备份

log() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"; }  #日志函数

create_backup() {  #创建备份
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/ljwx_daily_${timestamp}.sql.gz"
    
    log "🔄 开始MySQL每日备份..."
    
    # 检查容器状态
    if ! docker ps --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
        log "❌ MySQL容器未运行"
        return 1
    fi
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"
    
    # 执行备份
    if docker exec "$CONTAINER_NAME" mysqldump \
        -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --complete-insert \
        "$MYSQL_DATABASE" | gzip > "$backup_file"; then
        
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ 备份成功: $backup_file ($size)"
        
        # 验证备份文件
        if gunzip -t "$backup_file" 2>/dev/null; then
            log "✅ 备份文件验证通过"
        else
            log "❌ 备份文件验证失败"
            rm -f "$backup_file"
            return 1
        fi
    else
        log "❌ 备份失败"
        return 1
    fi
}

cleanup_old_backups() {  #清理旧备份
    log "�� 清理${BACKUP_RETENTION_DAYS}天前的备份..."
    
    local deleted=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        deleted=$((deleted + 1))
        log "🗑️ 删除旧备份: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "ljwx_daily_*.sql.gz" -mtime +$BACKUP_RETENTION_DAYS -print0 2>/dev/null)
    
    log "📊 清理完成，删除 $deleted 个文件"
}

# 主执行流程
main() {
    if create_backup; then
        cleanup_old_backups
        log "🎯 每日备份任务完成"
    else
        log "❌ 备份任务失败"
        exit 1
    fi
}

main "$@"
