#!/bin/bash
# LJWX备份恢复管理器 - 跨平台版

# 配置
MYSQL_CONTAINER="ljwx-mysql"
REDIS_CONTAINER="ljwx-redis"
MYSQL_USER="root"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"
BACKUP_BASE_DIR="backup"
LOG_DIR="logs"
RETENTION_DAYS=7

# 颜色 - 兼容CentOS：动态检测终端支持
if [ -t 1 ] && [ "${TERM:-}" != "" ] && tput colors >/dev/null 2>&1; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else #CentOS兼容：无颜色支持时使用空值
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Darwin) OS="macOS" ;;
        Linux) 
            if [ -f /etc/centos-release ]; then OS="CentOS"
            elif [ -f /etc/ubuntu-release ] || grep -q "Ubuntu" /etc/os-release 2>/dev/null; then OS="Ubuntu"
            else OS="Linux"; fi ;;
        *) OS="Unknown" ;;
    esac
}

# 日志函数
log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_DIR/backup-restore.log"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_DIR/backup-restore.log"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_DIR/backup-restore.log"; }

# 初始化
init() {
    detect_os
    mkdir -p "$BACKUP_BASE_DIR"/{mysql,redis} "$LOG_DIR"
    log "🚀 LJWX备份恢复管理器启动 (OS: $OS)"
}

# 检查Docker容器状态
check_container() {
    local container=$1
    if ! docker ps --format "{{.Names}}" | grep -q "^$container$"; then
        error "容器 $container 未运行"
        return 1
    fi
    return 0
}

# MySQL备份
mysql_backup() {
    local type=${1:-manual}  # auto/manual
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/mysql/${MYSQL_DATABASE}_${type}_${timestamp}.sql.gz"
    
    log "🔄 开始MySQL${type}备份..."
    
    if ! check_container "$MYSQL_CONTAINER"; then return 1; fi
    
    # 执行备份
    if docker exec "$MYSQL_CONTAINER" mysqldump \
        -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --single-transaction --routines --triggers \
        --complete-insert --hex-blob \
        "$MYSQL_DATABASE" | gzip > "$backup_file"; then
        
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ MySQL备份成功: $(basename "$backup_file") ($size)"
        
        # 验证备份
        if gunzip -t "$backup_file" 2>/dev/null; then
            log "✅ MySQL备份文件验证通过"
            return 0
        else
            error "❌ MySQL备份文件验证失败"
            rm -f "$backup_file"
            return 1
        fi
    else
        error "❌ MySQL备份失败"
        return 1
    fi
}

# Redis备份
redis_backup() {
    local type=${1:-manual}  # auto/manual
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_BASE_DIR/redis/redis_${type}_${timestamp}.rdb"
    local redis_password="${REDIS_PASSWORD:-123456}"
    
    log "🔄 开始Redis${type}备份..."
    
    if ! check_container "$REDIS_CONTAINER"; then return 1; fi
    
    # 触发Redis保存并复制RDB文件
    if docker exec "$REDIS_CONTAINER" sh -c "redis-cli -a '$redis_password' BGSAVE" 2>/dev/null && \
       sleep 3 && \
       docker exec "$REDIS_CONTAINER" cat /data/dump.rdb > "$backup_file"; then
        
        local size=$(du -h "$backup_file" | cut -f1)
        log "✅ Redis备份成功: $(basename "$backup_file") ($size)"
        return 0
    else
        error "❌ Redis备份失败"
        return 1
    fi
}

# MySQL恢复
mysql_restore() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        # 自动选择最新备份
        backup_file=$(ls -t "$BACKUP_BASE_DIR/mysql"/*.sql.gz 2>/dev/null | head -1)
        if [ -z "$backup_file" ]; then
            error "未找到MySQL备份文件"
            return 1
        fi
        log "自动选择最新备份: $(basename "$backup_file")"
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "备份文件不存在: $backup_file"
        return 1
    fi
    
    log "🔄 开始MySQL恢复..."
    
    if ! check_container "$MYSQL_CONTAINER"; then return 1; fi
    
    # 创建恢复前备份
    local pre_restore_backup="$BACKUP_BASE_DIR/mysql/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
    log "📦 创建恢复前备份: $(basename "$pre_restore_backup")"
    mysql_backup "pre_restore" >/dev/null 2>&1
    
    # 根据操作系统选择解压命令
    local decompress_cmd
    case "$OS" in
        macOS) decompress_cmd="gunzip -c" ;;
        *) decompress_cmd="zcat" ;;
    esac
    
    # 执行恢复
    if $decompress_cmd "$backup_file" | docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"; then
        log "✅ MySQL恢复成功"
        return 0
    else
        error "❌ MySQL恢复失败"
        return 1
    fi
}

# Redis恢复
redis_restore() {
    local backup_file="$1"
    local redis_password="${REDIS_PASSWORD:-123456}"
    
    if [ -z "$backup_file" ]; then
        # 自动选择最新备份
        backup_file=$(ls -t "$BACKUP_BASE_DIR/redis"/*.rdb 2>/dev/null | head -1)
        if [ -z "$backup_file" ]; then
            error "未找到Redis备份文件"
            return 1
        fi
        log "自动选择最新备份: $(basename "$backup_file")"
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "备份文件不存在: $backup_file"
        return 1
    fi
    
    log "🔄 开始Redis恢复..."
    
    if ! check_container "$REDIS_CONTAINER"; then return 1; fi
    
    # 创建恢复前备份
    log "📦 创建恢复前备份"
    redis_backup "pre_restore" >/dev/null 2>&1
    
    # 清空Redis数据并恢复
    log "🗑️ 清空Redis现有数据..."
    if docker exec "$REDIS_CONTAINER" sh -c "redis-cli -a '$redis_password' FLUSHALL" 2>/dev/null; then
        log "✅ Redis数据清空成功"
        
        # 停止Redis，替换RDB文件，重启Redis
        log "📁 替换RDB文件..."
        if docker stop "$REDIS_CONTAINER" && \
           cat "$backup_file" | docker exec -i "$REDIS_CONTAINER" tee /data/dump.rdb >/dev/null && \
           docker start "$REDIS_CONTAINER"; then
            
            log "✅ Redis恢复成功"
            sleep 5  # 等待Redis重启
            
            # 验证恢复
            if docker exec "$REDIS_CONTAINER" sh -c "redis-cli -a '$redis_password' ping" >/dev/null 2>&1; then
                log "✅ Redis服务验证成功"
                return 0
            else
                warn "⚠️ Redis服务验证失败，但恢复过程已完成"
                return 0
            fi
        else
            error "❌ Redis恢复失败"
            return 1
        fi
    else
        error "❌ Redis数据清空失败"
        return 1
    fi
}

# 清理旧备份
cleanup_backups() {
    log "🧹 清理${RETENTION_DAYS}天前的备份..."
    
    local deleted=0
    for dir in mysql redis; do
        # 兼容CentOS sh：避免进程替换，使用临时文件
        local temp_file="/tmp/backup_cleanup_$$"
        find "$BACKUP_BASE_DIR/$dir" -type f -mtime +$RETENTION_DAYS -print0 2>/dev/null > "$temp_file"
        while IFS= read -r -d '' file; do
            if [ -n "$file" ]; then
                rm -f "$file"
                deleted=$((deleted + 1))
                log "🗑️ 删除旧备份: $(basename "$file")"
            fi
        done < "$temp_file"
        rm -f "$temp_file"
    done
    
    log "📊 清理完成，删除 $deleted 个文件"
}

# 列出备份文件
list_backups() {
    echo -e "${BLUE}📋 MySQL备份文件:${NC}"
    if ls "$BACKUP_BASE_DIR/mysql"/*.sql.gz >/dev/null 2>&1; then
        local mysql_files=($(ls -t "$BACKUP_BASE_DIR/mysql"/*.sql.gz))
        i=0 #兼容CentOS sh：避免数组索引循环
        for file in "${mysql_files[@]}"; do
            local size=$(du -h "$file" | cut -f1)
            local date=$(ls -lh "$file" | awk "{print \$6, \$7, \$8}")
            echo "  $((i+1)). $(basename "$file") ($size, $date)"
            i=$((i+1))
        done
    else
        echo "  无备份文件"
    fi

    echo -e "${BLUE}📋 Redis备份文件:${NC}"
    if ls "$BACKUP_BASE_DIR/redis"/*.rdb >/dev/null 2>&1; then
        local redis_files=($(ls -t "$BACKUP_BASE_DIR/redis"/*.rdb))
        i=0 #兼容CentOS sh：避免数组索引循环
        for file in "${redis_files[@]}"; do
            local size=$(du -h "$file" | cut -f1)
            local date=$(ls -lh "$file" | awk "{print \$6, \$7, \$8}")
            echo "  $((i+1)). $(basename "$file") ($size, $date)"
            i=$((i+1))
        done
    else
        echo "  无备份文件"
    fi
}

# 自动化备份(用于定时任务)
auto_backup() {
    log "🤖 开始自动化备份任务..."
    
    local success=0
    if mysql_backup "auto"; then success=$((success + 1)); fi
    if redis_backup "auto"; then success=$((success + 1)); fi
    
    if [ $success -eq 2 ]; then
        log "🎯 自动化备份完成 (MySQL✅ Redis✅)"
        cleanup_backups
    else
        error "❌ 自动化备份部分失败"
        exit 1
    fi
}

# 显示菜单
show_menu() {
    echo -e "${BLUE}
╔══════════════════════════════════════╗
║      LJWX 备份恢复管理器 v2.0        ║
║            OS: $OS                    ║
╠══════════════════════════════════════╣
║  1. MySQL手动备份                    ║
║  2. Redis手动备份                    ║
║  3. 全量手动备份 (MySQL+Redis)       ║
║  4. MySQL恢复                        ║
║  5. Redis恢复                        ║
║  6. 列出备份文件                     ║
║  7. 清理旧备份                       ║
║  8. 自动化备份 (用于定时任务)        ║
║  9. 退出                             ║
╚══════════════════════════════════════╝${NC}"
}

# 主函数
main() {
    init
    
    if [ $# -eq 0 ]; then
        # 交互模式
        while true; do
            show_menu
            read -p "请选择操作 [1-9]: " choice
            case $choice in
                1) mysql_backup "manual" ;;
                2) redis_backup "manual" ;;
                3) 
                    log "🔄 开始全量备份..."
                    mysql_backup "manual" && redis_backup "manual"
                    ;;
                4) 
                    list_backups
                    read -p "请输入MySQL备份文件序号或路径 (回车自动选择最新): " input
                    if echo "$input" | grep -q '^[0-9][0-9]*$'; then #兼容CentOS sh：避免双方括号和正则匹配
                        # 序号选择
                        files=($(ls -t "$BACKUP_BASE_DIR/mysql"/*.sql.gz 2>/dev/null))
                        if [ "$input" -ge 1 ] && [ "$input" -le "${#files[@]}" ]; then
                            mysql_restore "${files[$((input-1))]}"
                        else
                            error "备份文件序号无效: $input (有效范围: 1-${#files[@]})"
                        fi
                    else
                        # 路径选择
                        mysql_restore "$input"
                    fi
                    ;;
                5)
                    list_backups
                    read -p "请输入Redis备份文件序号或路径 (回车自动选择最新): " input
                    if echo "$input" | grep -q '^[0-9][0-9]*$'; then #兼容CentOS sh：避免双方括号和正则匹配
                        # 序号选择
                        files=($(ls -t "$BACKUP_BASE_DIR/redis"/*.rdb 2>/dev/null))
                        if [ "$input" -ge 1 ] && [ "$input" -le "${#files[@]}" ]; then
                            redis_restore "${files[$((input-1))]}"
                        else
                            error "备份文件序号无效: $input (有效范围: 1-${#files[@]})"
                        fi
                    else
                        # 路径选择
                        redis_restore "$input"
                    fi
                    ;;
                6) list_backups ;;
                7) cleanup_backups ;;
                8) auto_backup ;;
                9) log "👋 退出备份恢复管理器"; exit 0 ;;
                *) warn "无效选择，请重新输入" ;;
            esac
            echo
        done
    else
        # 命令行模式
        case "$1" in
            mysql-backup) mysql_backup "manual" ;;
            redis-backup) redis_backup "manual" ;;
            full-backup) mysql_backup "manual" && redis_backup "manual" ;;
            mysql-restore) mysql_restore "$2" ;;
            redis-restore) redis_restore "$2" ;;
            auto-backup) auto_backup ;;
            list) list_backups ;;
            cleanup) cleanup_backups ;;
            *) 
                echo "用法: $0 [mysql-backup|redis-backup|full-backup|mysql-restore|redis-restore|auto-backup|list|cleanup]"
                exit 1
                ;;
        esac
    fi
}

main "$@"
