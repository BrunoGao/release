#!/bin/bash
# LJWX快速恢复脚本 - 紧急恢复工具

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

# 配置
MYSQL_CONTAINER="ljwx-mysql"
REDIS_CONTAINER="ljwx-redis"
MYSQL_USER="root"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"
BACKUP_BASE_DIR="backup"

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

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 快速恢复菜单
show_restore_menu() {
    echo -e "${RED}
╔══════════════════════════════════════╗
║         🚨 LJWX 紧急恢复工具         ║
║             OS: $OS                  ║
╠══════════════════════════════════════╣
║  1. 快速恢复MySQL (最新备份)         ║
║  2. 快速恢复Redis (最新备份)         ║
║  3. 全量快速恢复 (MySQL+Redis)       ║
║  4. 选择特定MySQL备份恢复            ║
║  5. 选择特定Redis备份恢复            ║
║  6. 查看可用备份文件                 ║
║  7. 退出                             ║
╚══════════════════════════════════════╝${NC}"
}

# 检查容器状态
check_containers() {
    log "🔍 检查容器状态..."
    
    local mysql_running=false
    local redis_running=false
    
    if docker ps --format "{{.Names}}" | grep -q "^$MYSQL_CONTAINER$"; then
        mysql_running=true
        log "✅ MySQL容器运行中"
    else
        warn "❌ MySQL容器未运行"
    fi
    
    if docker ps --format "{{.Names}}" | grep -q "^$REDIS_CONTAINER$"; then
        redis_running=true
        log "✅ Redis容器运行中"
    else
        warn "❌ Redis容器未运行"
    fi
    
    if ! $mysql_running || ! $redis_running; then
        warn "⚠️  部分容器未运行，是否启动服务?"
        read -p "启动Docker Compose服务? [y/N]: " start_services
        if [[ $start_services =~ ^[Yy]$ ]]; then
            log "🚀 启动Docker Compose服务..."
            if [ -f "docker-compose-optimized.yml" ]; then
                docker-compose -f docker-compose-optimized.yml up -d
            else
                docker-compose up -d
            fi
            sleep 10
        fi
    fi
}

# 列出备份文件
list_available_backups() {
    echo -e "${BLUE}📋 可用的MySQL备份文件:${NC}"
    if ls "$BACKUP_BASE_DIR/mysql"/*.sql.gz >/dev/null 2>&1; then
        ls -lah "$BACKUP_BASE_DIR/mysql"/*.sql.gz | nl | awk '{print "  " $1 ". " $10 " (" $6 ", " $7 " " $8 ")"}'
    else
        echo "  无可用备份文件"
    fi
    
    echo -e "${BLUE}📋 可用的Redis备份文件:${NC}"
    if ls "$BACKUP_BASE_DIR/redis"/*.rdb >/dev/null 2>&1; then
        ls -lah "$BACKUP_BASE_DIR/redis"/*.rdb | nl | awk '{print "  " $1 ". " $10 " (" $6 ", " $7 " " $8 ")"}'
    else
        echo "  无可用备份文件"
    fi
}

# 快速恢复MySQL
quick_mysql_restore() {
    local backup_file=$(ls -t "$BACKUP_BASE_DIR/mysql"/*.sql.gz 2>/dev/null | head -1)
    
    if [ -z "$backup_file" ]; then
        error "❌ 未找到MySQL备份文件"
        return 1
    fi
    
    log "🔄 快速恢复MySQL ($(basename "$backup_file"))..."
    
    # 检查容器
    if ! docker ps --format "{{.Names}}" | grep -q "^$MYSQL_CONTAINER$"; then
        error "❌ MySQL容器未运行"
        return 1
    fi
    
    # 选择解压命令
    local decompress_cmd
    case "$OS" in
        macOS) decompress_cmd="gunzip -c" ;;
        *) decompress_cmd="zcat" ;;
    esac
    
    # 执行恢复
    if $decompress_cmd "$backup_file" | docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"; then
        log "✅ MySQL快速恢复成功"
        return 0
    else
        error "❌ MySQL快速恢复失败"
        return 1
    fi
}

# 快速恢复Redis
quick_redis_restore() {
    local backup_file=$(ls -t "$BACKUP_BASE_DIR/redis"/*.rdb 2>/dev/null | head -1)
    
    if [ -z "$backup_file" ]; then
        error "❌ 未找到Redis备份文件"
        return 1
    fi
    
    log "🔄 快速恢复Redis ($(basename "$backup_file"))..."
    
    # 检查容器
    if ! docker ps --format "{{.Names}}" | grep -q "^$REDIS_CONTAINER$"; then
        error "❌ Redis容器未运行"
        return 1
    fi
    
    # 停止Redis写入并恢复数据
    if docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL && \
       cat "$backup_file" | docker exec -i "$REDIS_CONTAINER" tee /data/dump.rdb >/dev/null && \
       docker restart "$REDIS_CONTAINER"; then
        
        log "✅ Redis快速恢复成功"
        sleep 3  # 等待Redis重启
        return 0
    else
        error "❌ Redis快速恢复失败"
        return 1
    fi
}

# 选择特定备份恢复
select_mysql_backup() {
    echo -e "${BLUE}📋 选择MySQL备份文件:${NC}"
    
    local backups=($(ls -t "$BACKUP_BASE_DIR/mysql"/*.sql.gz 2>/dev/null))
    if [ ${#backups[@]} -eq 0 ]; then
        error "❌ 未找到MySQL备份文件"
        return 1
    fi
    
    for i in "${!backups[@]}"; do
        local file="${backups[$i]}"
        local size=$(du -h "$file" | cut -f1)
        local date=$(date -r "$file" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2)
        echo "  $((i+1)). $(basename "$file") ($size, $date)"
    done
    
    read -p "请选择备份文件编号 [1-${#backups[@]}]: " choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#backups[@]}" ]; then
        local selected_file="${backups[$((choice-1))]}"
        log "🔄 恢复MySQL备份: $(basename "$selected_file")"
        
        # 选择解压命令
        local decompress_cmd
        case "$OS" in
            macOS) decompress_cmd="gunzip -c" ;;
            *) decompress_cmd="zcat" ;;
        esac
        
        # 执行恢复
        if $decompress_cmd "$selected_file" | docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"; then
            log "✅ MySQL恢复成功"
        else
            error "❌ MySQL恢复失败"
        fi
    else
        error "❌ 无效选择"
    fi
}

# 选择特定Redis备份恢复
select_redis_backup() {
    echo -e "${BLUE}📋 选择Redis备份文件:${NC}"
    
    local backups=($(ls -t "$BACKUP_BASE_DIR/redis"/*.rdb 2>/dev/null))
    if [ ${#backups[@]} -eq 0 ]; then
        error "❌ 未找到Redis备份文件"
        return 1
    fi
    
    for i in "${!backups[@]}"; do
        local file="${backups[$i]}"
        local size=$(du -h "$file" | cut -f1)
        local date=$(date -r "$file" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2)
        echo "  $((i+1)). $(basename "$file") ($size, $date)"
    done
    
    read -p "请选择备份文件编号 [1-${#backups[@]}]: " choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#backups[@]}" ]; then
        local selected_file="${backups[$((choice-1))]}"
        log "🔄 恢复Redis备份: $(basename "$selected_file")"
        
        # 执行恢复
        if docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL && \
           cat "$selected_file" | docker exec -i "$REDIS_CONTAINER" tee /data/dump.rdb >/dev/null && \
           docker restart "$REDIS_CONTAINER"; then
            
            log "✅ Redis恢复成功"
            sleep 3  # 等待Redis重启
        else
            error "❌ Redis恢复失败"
        fi
    else
        error "❌ 无效选择"
    fi
}

# 主函数
main() {
    detect_os
    echo -e "${RED}🚨 LJWX紧急恢复工具启动 (OS: $OS)${NC}"
    
    check_containers
    
    while true; do
        show_restore_menu
        read -p "请选择操作 [1-7]: " choice
        
        case $choice in
            1) quick_mysql_restore ;;
            2) quick_redis_restore ;;
            3) 
                log "🔄 开始全量快速恢复..."
                quick_mysql_restore && quick_redis_restore
                ;;
            4) select_mysql_backup ;;
            5) select_redis_backup ;;
            6) list_available_backups ;;
            7) log "👋 退出紧急恢复工具"; exit 0 ;;
            *) warn "无效选择，请重新输入" ;;
        esac
        echo
        read -p "按回车键继续..."
    done
}

main "$@"
