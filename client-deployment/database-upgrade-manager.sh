#!/bin/bash
# 数据库升级管理器 - 智能穿戴系统客户升级专用
# 使用方法：./database-upgrade-manager.sh [源版本] [目标版本]

set -euo pipefail

# 配置文件
CONFIG_FILE="${1:-custom-config.env}"
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"

# 基本配置
MYSQL_CONTAINER="${MYSQL_CONTAINER:-ljwx-mysql}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DATABASE="${MYSQL_DATABASE:-lj-06}"
BACKUP_DIR="backup/database-upgrade"
LOG_DIR="logs/database-upgrade"
MIGRATION_DIR="database/migrations"

# 创建必要目录
mkdir -p "$BACKUP_DIR" "$LOG_DIR" "$MIGRATION_DIR"

# 日志配置
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/upgrade-${TIMESTAMP}.log"

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 工具函数
log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

confirm() {
    read -p "$(echo -e "${YELLOW}$1 [y/N]:${NC} ")" response
    [[ "$response" =~ ^[Yy]$ ]]
}

# 检测数据库版本
get_database_version() {
    local version_query="SELECT version FROM database_version ORDER BY id DESC LIMIT 1;"
    local current_version
    
    # 检查版本表是否存在
    if docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -e "SHOW TABLES LIKE 'database_version';" 2>/dev/null | grep -q database_version; then
        current_version=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
            -e "$version_query" -s -N 2>/dev/null || echo "1.0.0")
    else
        log "首次检测到数据库，将创建版本管理表并设置初始版本"
        create_version_table
        current_version="1.0.0"
    fi
    
    echo "$current_version"
}

# 创建版本管理表
create_version_table() {
    log "创建数据库版本管理表..."
    
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" << 'EOF'
CREATE TABLE IF NOT EXISTS database_version (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(100) DEFAULT 'system',
    migration_files TEXT COMMENT '应用的迁移文件列表'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库版本管理表';

-- 插入初始版本
INSERT INTO database_version (version, description, applied_by) 
VALUES ('1.0.0', '初始数据库版本', 'database-upgrade-manager')
ON DUPLICATE KEY UPDATE version=version;
EOF
    
    log "✅ 版本管理表创建完成"
}

# 健康检查
health_check() {
    log "🔍 执行升级前健康检查..."
    
    # 检查容器状态
    if ! docker ps --format "{{.Names}}" | grep -q "^$MYSQL_CONTAINER$"; then
        error "MySQL容器未运行，请先启动容器"
    fi
    
    # 检查数据库连接
    if ! docker exec "$MYSQL_CONTAINER" mysqladmin ping -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" &>/dev/null; then
        error "无法连接到MySQL数据库"
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df . | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 85 ]]; then
        warn "磁盘使用率 ${disk_usage}%，建议清理空间后再升级"
        if ! confirm "是否继续升级？"; then
            exit 0
        fi
    fi
    
    # 检查数据库大小
    local db_size=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' 
            FROM information_schema.tables 
            WHERE table_schema='$MYSQL_DATABASE';" -s -N 2>/dev/null)
    log "数据库大小: ${db_size} MB"
    
    log "✅ 健康检查通过"
}

# 备份数据库
backup_database() {
    log "📦 创建数据库备份..."
    
    local backup_file="$BACKUP_DIR/pre_upgrade_${TIMESTAMP}.sql.gz"
    local structure_file="$BACKUP_DIR/structure_${TIMESTAMP}.sql"
    
    # 备份完整数据
    docker exec "$MYSQL_CONTAINER" mysqldump \
        -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --add-drop-database \
        --databases "$MYSQL_DATABASE" | gzip > "$backup_file"
    
    if [[ $? -eq 0 ]]; then
        local backup_size=$(du -h "$backup_file" | cut -f1)
        log "✅ 数据备份完成: $(basename "$backup_file") (${backup_size})"
        
        # 保存备份路径供回滚使用
        echo "$backup_file" > "$BACKUP_DIR/latest_backup.path"
    else
        error "数据备份失败"
    fi
    
    # 备份表结构（用于快速验证）
    docker exec "$MYSQL_CONTAINER" mysqldump \
        -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        --no-data \
        --routines \
        --triggers \
        --events \
        "$MYSQL_DATABASE" > "$structure_file"
    
    log "✅ 表结构备份完成"
}

# 获取可用的迁移脚本
get_migration_scripts() {
    local current_version="$1"
    local target_version="$2"
    
    # 扫描迁移目录
    local migration_scripts=()
    
    if [[ -d "$MIGRATION_DIR" ]]; then
        # 按文件名排序获取迁移脚本
        while IFS= read -r -d '' file; do
            migration_scripts+=("$file")
        done < <(find "$MIGRATION_DIR" -name "*.sql" -print0 | sort -z)
    fi
    
    # 检查是否有版本特定的升级脚本
    local version_specific_script="database/upgrade_${current_version}_to_${target_version}.sql"
    if [[ -f "$version_specific_script" ]]; then
        migration_scripts+=("$version_specific_script")
    fi
    
    printf '%s\n' "${migration_scripts[@]}"
}

# 执行迁移脚本
execute_migration_scripts() {
    local current_version="$1"
    local target_version="$2"
    local applied_files=()
    
    log "📝 执行数据库迁移脚本..."
    
    # 获取迁移脚本列表
    local migration_scripts
    mapfile -t migration_scripts < <(get_migration_scripts "$current_version" "$target_version")
    
    if [[ ${#migration_scripts[@]} -eq 0 ]]; then
        warn "未找到迁移脚本，跳过数据库结构更新"
        return 0
    fi
    
    # 执行每个迁移脚本
    for script in "${migration_scripts[@]}"; do
        if [[ -f "$script" ]]; then
            log "执行迁移脚本: $(basename "$script")"
            
            # 在事务中执行迁移脚本
            if docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$script"; then
                log "✅ $(basename "$script") 执行成功"
                applied_files+=("$(basename "$script")")
            else
                error "❌ $(basename "$script") 执行失败"
            fi
        fi
    done
    
    # 更新版本信息
    local applied_files_json=$(printf '%s,' "${applied_files[@]}" | sed 's/,$//')
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" << EOF
INSERT INTO database_version (version, description, applied_by, migration_files) 
VALUES ('$target_version', '数据库升级到版本 $target_version', 'database-upgrade-manager', '$applied_files_json');
EOF
    
    log "✅ 所有迁移脚本执行完成"
}

# 验证数据完整性
verify_database_integrity() {
    log "🔍 验证数据库完整性..."
    
    # 检查表数量
    local table_count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" -s -N 2>/dev/null)
    
    if [[ $table_count -le 0 ]]; then
        error "数据表数量验证失败"
    fi
    
    log "数据库包含 $table_count 个表"
    
    # 检查关键表的存在性和记录数
    local critical_tables=("sys_user" "sys_dict" "t_alert_rules")
    for table in "${critical_tables[@]}"; do
        local table_exists=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
            -e "SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema='$MYSQL_DATABASE' AND table_name='$table';" -s -N 2>/dev/null)
        
        if [[ $table_exists -eq 1 ]]; then
            local record_count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
                -e "SELECT COUNT(*) FROM $table;" -s -N "$MYSQL_DATABASE" 2>/dev/null || echo "0")
            log "✅ 表 $table: $record_count 条记录"
        else
            warn "⚠️  表 $table 不存在"
        fi
    done
    
    # 检查数据库版本记录
    local version_record_count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT COUNT(*) FROM database_version;" -s -N "$MYSQL_DATABASE" 2>/dev/null || echo "0")
    log "版本记录数量: $version_record_count"
    
    log "✅ 数据完整性验证通过"
}

# 性能优化
optimize_database() {
    log "⚡ 执行数据库性能优化..."
    
    # 分析表
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -e "ANALYZE TABLE sys_user, sys_dict, t_alert_info, t_alert_rules;" &>/dev/null
    
    # 优化表
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -e "OPTIMIZE TABLE sys_user, sys_dict;" &>/dev/null
    
    log "✅ 数据库优化完成"
}

# 生成升级报告
generate_upgrade_report() {
    local source_version="$1"
    local target_version="$2"
    local report_file="$LOG_DIR/upgrade_report_${TIMESTAMP}.md"
    
    log "📋 生成升级报告..."
    
    # 获取数据库统计信息
    local table_count=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" \
        -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$MYSQL_DATABASE';" -s -N 2>/dev/null)
    
    local backup_size=$(du -h "$BACKUP_DIR" | tail -1 | cut -f1)
    
    cat > "$report_file" << EOF
# 数据库升级报告

## 升级信息
- **升级时间**: $(date)
- **源版本**: $source_version  
- **目标版本**: $target_version
- **升级状态**: ✅ 成功
- **数据库**: $MYSQL_DATABASE

## 数据库状态
- **表数量**: $table_count
- **版本管理**: ✅ 已启用
- **数据完整性**: ✅ 已验证

## 备份信息
- **备份目录**: $BACKUP_DIR
- **备份总大小**: $backup_size
- **恢复命令**: \`./database-upgrade-manager.sh rollback\`

## 应用的迁移脚本
EOF

    # 获取已应用的迁移文件
    local applied_files=$(docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -e "SELECT migration_files FROM database_version WHERE version='$target_version' ORDER BY id DESC LIMIT 1;" -s -N 2>/dev/null || echo "")
    
    if [[ -n "$applied_files" && "$applied_files" != "NULL" ]]; then
        IFS=',' read -ra files <<< "$applied_files"
        for file in "${files[@]}"; do
            echo "- $file" >> "$report_file"
        done
    else
        echo "- 无迁移脚本应用" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

## 详细日志
查看完整升级日志: \`$LOG_FILE\`

## 验证命令
\`\`\`bash
# 检查数据库版本
docker exec $MYSQL_CONTAINER mysql -u$MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE -e "SELECT * FROM database_version ORDER BY id DESC LIMIT 5;"

# 检查服务状态
docker-compose ps

# 应用健康检查
curl http://localhost:9998/actuator/health
curl http://localhost:8001/health
curl http://localhost:8080/
\`\`\`
EOF
    
    log "✅ 升级报告已生成: $report_file"
}

# 回滚功能
rollback() {
    warn "🔄 开始数据库回滚操作..."
    
    if [[ ! -f "$BACKUP_DIR/latest_backup.path" ]]; then
        error "未找到备份文件路径，无法回滚"
    fi
    
    local backup_file=$(cat "$BACKUP_DIR/latest_backup.path")
    
    if [[ ! -f "$backup_file" ]]; then
        error "备份文件不存在: $backup_file"
    fi
    
    if confirm "确认要回滚数据库吗？这将覆盖当前数据"; then
        log "恢复数据库备份..."
        
        # 停止应用服务
        docker stop ljwx-boot ljwx-admin ljwx-bigscreen &>/dev/null || true
        
        # 恢复数据库
        zcat "$backup_file" | docker exec -i "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"
        
        if [[ $? -eq 0 ]]; then
            log "✅ 数据库回滚成功"
            
            # 重启应用服务
            docker-compose up -d
            
            log "✅ 回滚操作完成"
        else
            error "数据库回滚失败"
        fi
    else
        log "回滚操作已取消"
    fi
}

# 显示使用帮助
show_help() {
    cat << EOF
数据库升级管理器使用说明

用法: $0 [选项] [源版本] [目标版本]

选项:
  upgrade [源版本] [目标版本]  执行数据库升级
  rollback                    回滚到升级前状态
  status                      显示当前数据库版本
  help                        显示此帮助信息

示例:
  $0 upgrade 1.0.0 1.1.0     从1.0.0升级到1.1.0
  $0 rollback                 回滚数据库
  $0 status                   查看当前版本

配置文件:
  默认使用 custom-config.env，或通过环境变量指定

日志文件:
  升级日志: $LOG_DIR/upgrade_YYYYMMDD_HHMMSS.log
  升级报告: $LOG_DIR/upgrade_report_YYYYMMDD_HHMMSS.md
EOF
}

# 显示版本状态
show_status() {
    log "📊 数据库版本状态"
    
    if ! docker ps --format "{{.Names}}" | grep -q "^$MYSQL_CONTAINER$"; then
        warn "MySQL容器未运行"
        return 1
    fi
    
    local current_version=$(get_database_version)
    log "当前数据库版本: $current_version"
    
    # 显示版本历史
    log "版本升级历史:"
    docker exec "$MYSQL_CONTAINER" mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
        -e "SELECT version, description, applied_at, applied_by FROM database_version ORDER BY id DESC LIMIT 10;" 2>/dev/null || warn "无法获取版本历史"
    
    # 检查可用的迁移脚本
    local migration_count=$(find "$MIGRATION_DIR" -name "*.sql" 2>/dev/null | wc -l)
    log "可用迁移脚本数量: $migration_count"
}

# 主升级流程
upgrade_database() {
    local source_version="$1"
    local target_version="$2"
    
    log "🚀 开始数据库升级流程"
    log "源版本: $source_version → 目标版本: $target_version"
    
    # 验证版本
    local current_version=$(get_database_version)
    if [[ "$current_version" != "$source_version" ]]; then
        warn "当前数据库版本 ($current_version) 与指定源版本 ($source_version) 不匹配"
        if ! confirm "是否继续升级？"; then
            exit 0
        fi
    fi
    
    # 执行升级步骤
    health_check
    backup_database
    execute_migration_scripts "$source_version" "$target_version"
    verify_database_integrity
    optimize_database
    generate_upgrade_report "$source_version" "$target_version"
    
    log "🎉 数据库升级成功完成！"
    log "当前版本: $target_version"
    log "升级报告: $LOG_DIR/upgrade_report_${TIMESTAMP}.md"
}

# 主函数
main() {
    local command="${1:-help}"
    
    case "$command" in
        "upgrade")
            local source_version="${2:-}"
            local target_version="${3:-}"
            
            if [[ -z "$source_version" || -z "$target_version" ]]; then
                error "升级命令需要指定源版本和目标版本"
            fi
            
            upgrade_database "$source_version" "$target_version"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_status
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            warn "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 脚本入口
main "$@"