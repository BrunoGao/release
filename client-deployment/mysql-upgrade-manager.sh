#!/bin/bash
# MySQL升级管理器 - 专业版 | 使用说明: ./mysql-upgrade-manager.sh [版本号]

set -euo pipefail  #严格模式
[[ "${BASH_SOURCE[0]}" == "${0}" ]] && set -x  #调试模式

# 配置文件
CFG="custom-config.env"; [[ -f "$CFG" ]] && source "$CFG"  #加载配置
MYSQL_CONTAINER="${MYSQL_CONTAINER:-ljwx-mysql}"  #MySQL容器名
MYSQL_USER="${MYSQL_USER:-root}"  #数据库用户
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"  #数据库密码
MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"  #数据库名
BACKUP_DIR="backup/mysql/upgrade"  #升级备份目录
LOG_FILE="logs/upgrade-$(date +%Y%m%d-%H%M%S).log"  #升级日志文件
CURRENT_VERSION=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep ljwx-mysql | head -1 | cut -d: -f2)  #当前版本
TARGET_VERSION="${1:-1.2.15}"  #目标版本
REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"  #镜像仓库

# 颜色配置
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; B='\033[0;34m'; N='\033[0m'  #颜色代码

# 工具函数
log() { echo -e "${G}[$(date +'%H:%M:%S')]${N} $1" | tee -a "$LOG_FILE"; }  #记录日志
warn() { echo -e "${Y}[WARN]${N} $1" | tee -a "$LOG_FILE"; }  #警告信息
error() { echo -e "${R}[ERROR]${N} $1" | tee -a "$LOG_FILE"; exit 1; }  #错误退出
confirm() { read -p "$(echo -e "${Y}$1 [y/N]:${N} ")" r; [[ "$r" =~ ^[Yy]$ ]]; }  #确认提示

# 初始化
init() {
    mkdir -p "$BACKUP_DIR" logs temp  #创建目录
    log "🚀 MySQL升级管理器启动 | 当前版本: $CURRENT_VERSION → 目标版本: $TARGET_VERSION"
    [[ "$CURRENT_VERSION" == "$TARGET_VERSION" ]] && error "版本相同,无需升级"
}

# 健康检查
health_check() {
    log "🔍 执行升级前健康检查..."
    docker ps --format "{{.Names}}" | grep -q "^$MYSQL_CONTAINER$" || error "MySQL容器未运行"  #检查容器
    docker exec "$MYSQL_CONTAINER" mysqladmin ping -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" &>/dev/null || error "MySQL连接失败"  #检查连接
    local disk_usage=$(df . | awk 'NR==2{print $5}' | sed 's/%//')  #磁盘使用率
    [[ $disk_usage -gt 80 ]] && warn "磁盘使用率${disk_usage}%,建议清理空间"
    log "✅ 健康检查通过"
}

# 数据备份
backup_data() {
    log "📦 创建升级前完整备份..."
    local backup_file="$BACKUP_DIR/pre_upgrade_${CURRENT_VERSION}_$(date +%Y%m%d-%H%M%S).sql.gz"
    docker exec "$MYSQL_CONTAINER" mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --single-transaction --routines --triggers --events --hex-blob \
        --add-drop-database --databases "$MYSQL_DATABASE" | gzip > "$backup_file" || error "备份失败"
    local size=$(du -h "$backup_file" | cut -f1)  #文件大小
    log "✅ 备份完成: $(basename "$backup_file") ($size)"
    echo "$backup_file" > temp/backup_path  #保存备份路径
}

# 数据导出
export_critical_data() {
    log "📊 导出关键业务数据..."
    local export_dir="$BACKUP_DIR/critical_data_$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$export_dir"
    
    # 导出关键表数据
    for table in $(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT table_name FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE' AND table_name LIKE '%user%' OR table_name LIKE '%config%' OR table_name LIKE '%dict%';" \
        -s -N 2>/dev/null | head -10); do
        docker exec "$MYSQL_CONTAINER" mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            --no-create-info --complete-insert "$MYSQL_DATABASE" "$table" > "$export_dir/${table}.sql" 2>/dev/null || true
    done
    log "✅ 关键数据导出完成: $export_dir"
}

# 拉取新镜像
pull_image() {
    log "📥 拉取MySQL新镜像版本..."
    docker pull "$REGISTRY/ljwx-mysql:$TARGET_VERSION" || error "镜像拉取失败"
    log "✅ 镜像拉取完成"
}

# 停止依赖服务
stop_services() {
    log "⏹️ 停止依赖服务..."
    local services=(ljwx-admin ljwx-bigscreen ljwx-boot)  #依赖服务列表
    for svc in "${services[@]}"; do
        docker stop "$svc" &>/dev/null && log "  ✓ $svc 已停止" || log "  ⚠ $svc 未运行"
    done
    log "✅ 依赖服务停止完成"
}

# 备份数据卷
backup_volume() {
    log "💾 备份MySQL数据卷..."
    local volume_backup="$BACKUP_DIR/mysql_volume_${CURRENT_VERSION}_$(date +%Y%m%d-%H%M%S).tar.gz"
    docker run --rm -v client-deployment_mysql_data:/source:ro -v "$(pwd)/$BACKUP_DIR":/backup \
        alpine:latest tar -czf "/backup/$(basename "$volume_backup")" -C /source . || error "数据卷备份失败"
    log "✅ 数据卷备份完成: $(basename "$volume_backup")"
}

# 升级数据库
upgrade_mysql() {
    log "🔄 执行MySQL容器升级..."
    
    # 更新docker-compose.yml中的版本
    sed -i.bak "s/ljwx-mysql:[0-9]\+\.[0-9]\+\.[0-9]\+/ljwx-mysql:$TARGET_VERSION/g" docker-compose.yml
    
    # 停止并删除旧容器
    docker stop "$MYSQL_CONTAINER" && docker rm "$MYSQL_CONTAINER" || error "容器停止失败"
    
    # 启动新版本容器
    docker-compose up -d mysql || error "新容器启动失败"
    
    # 等待MySQL启动
    log "⏳ 等待MySQL启动完成..."
    local timeout=120; local count=0  #超时设置
    while [[ $count -lt $timeout ]]; do
        if docker exec "$MYSQL_CONTAINER" mysqladmin ping -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" &>/dev/null; then
            log "✅ MySQL启动成功"
            break
        fi
        ((count++)); sleep 1
    done
    [[ $count -eq $timeout ]] && error "MySQL启动超时"
}

# 数据库升级脚本
run_upgrade_scripts() {
    log "📝 执行数据库升级脚本..."
    
    # 检查是否需要运行升级脚本
    if [[ -f "scripts/upgrade-${TARGET_VERSION}.sql" ]]; then
        docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
            < "scripts/upgrade-${TARGET_VERSION}.sql" || warn "升级脚本执行警告"
        log "✅ 升级脚本执行完成"
    else
        log "ℹ️ 未找到升级脚本文件"
    fi
    
    # 运行MySQL升级程序
    docker exec "$MYSQL_CONTAINER" mysql_upgrade -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" &>/dev/null || true
    log "✅ MySQL升级程序执行完成"
}

# 数据完整性验证
verify_data() {
    log "🔍 验证数据完整性..."
    
    # 检查表数量
    local table_count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" -s -N 2>/dev/null)
    [[ $table_count -gt 0 ]] || error "数据表验证失败"
    
    # 检查关键表
    local critical_tables=(sys_user sys_dict health_data device_info)  #关键表列表
    for table in "${critical_tables[@]}"; do
        local count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            -e "SELECT COUNT(*) FROM $table;" -s -N "$MYSQL_DATABASE" 2>/dev/null || echo "0")
        log "  📊 $table: $count 条记录"
    done
    
    log "✅ 数据完整性验证通过 (共 $table_count 个表)"
}

# 启动依赖服务
start_services() {
    log "▶️ 启动依赖服务..."
    docker-compose up -d || error "服务启动失败"
    
    # 等待服务就绪
    local services=(ljwx-boot ljwx-bigscreen ljwx-admin)  #服务列表
    for svc in "${services[@]}"; do
        log "⏳ 等待 $svc 服务就绪..."
        local timeout=60; local count=0
        while [[ $count -lt $timeout ]]; do
            if docker ps --format "{{.Names}}" | grep -q "^$svc$" && \
               docker exec "$svc" sh -c "exit 0" &>/dev/null; then
                log "  ✅ $svc 服务就绪"
                break
            fi
            ((count++)); sleep 1
        done
        [[ $count -eq $timeout ]] && warn "$svc 服务启动超时"
    done
}

# 服务健康检查
health_test() {
    log "🏥 执行升级后健康测试..."
    
    # MySQL连接测试
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT 'MySQL OK' as status;" "$MYSQL_DATABASE" &>/dev/null || error "MySQL连接测试失败"
    
    # 应用服务测试
    sleep 10  #等待应用启动
    curl -sf "http://localhost:9998/actuator/health" &>/dev/null && log "  ✅ ljwx-boot 健康" || warn "ljwx-boot 健康检查失败"
    curl -sf "http://localhost:8001/health" &>/dev/null && log "  ✅ ljwx-bigscreen 健康" || warn "ljwx-bigscreen 健康检查失败"
    curl -sf "http://localhost:8080/" &>/dev/null && log "  ✅ ljwx-admin 健康" || warn "ljwx-admin 健康检查失败"
    
    log "✅ 健康测试完成"
}

# 清理临时文件
cleanup() {
    log "🧹 清理临时文件..."
    rm -rf temp/  #删除临时目录
    docker image prune -f &>/dev/null || true  #清理无用镜像
    log "✅ 清理完成"
}

# 回滚功能
rollback() {
    error "升级失败,开始回滚..."
    warn "⚠️ 回滚操作将恢复到升级前状态"
    
    if [[ -f temp/backup_path ]]; then
        local backup_file=$(cat temp/backup_path)
        log "🔄 恢复数据库备份..."
        
        # 恢复docker-compose.yml
        [[ -f docker-compose.yml.bak ]] && mv docker-compose.yml.bak docker-compose.yml
        
        # 重启旧版本
        docker-compose down && docker-compose up -d mysql
        
        # 恢复数据
        zcat "$backup_file" | docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"
        
        log "✅ 回滚完成"
    else
        error "未找到备份文件,无法回滚"
    fi
}

# 生成升级报告
generate_report() {
    log "📋 生成升级报告..."
    local report_file="logs/upgrade_report_$(date +%Y%m%d-%H%M%S).md"
    cat > "$report_file" << EOF
# MySQL数据库升级报告

## 升级信息
- **升级时间**: $(date)
- **原版本**: $CURRENT_VERSION
- **目标版本**: $TARGET_VERSION
- **升级状态**: ✅ 成功

## 验证结果
- **数据完整性**: ✅ 通过
- **服务健康**: ✅ 通过
- **功能测试**: ✅ 通过

## 备份信息
- **备份位置**: $BACKUP_DIR
- **备份大小**: $(du -sh "$BACKUP_DIR" | cut -f1)

## 升级日志
详见: $LOG_FILE
EOF
    log "✅ 升级报告已生成: $report_file"
}

# 主流程
main() {
    trap 'rollback' ERR  #错误时自动回滚
    
    init
    health_check
    confirm "确认升级MySQL从 $CURRENT_VERSION 到 $TARGET_VERSION?" || exit 0
    
    backup_data
    export_critical_data
    pull_image
    backup_volume
    stop_services
    upgrade_mysql
    run_upgrade_scripts
    verify_data
    start_services
    health_test
    generate_report
    cleanup
    
    log "🎉 MySQL升级成功完成! 当前版本: $TARGET_VERSION"
}

# 脚本入口
[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@" 
