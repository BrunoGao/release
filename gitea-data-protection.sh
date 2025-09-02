#!/bin/bash

# Gitea 数据保护管理脚本
# 确保源代码永不丢失的全自动解决方案
# 使用方法: ./gitea-data-protection.sh [start|stop|backup|restore|health|auto-setup]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
COMPOSE_FILE="${PROJECT_ROOT}/docker/compose/gitea-compose.yml"
BACKUP_DIR="${PROJECT_ROOT}/backup/gitea"
DATA_PROTECTION_DIR="${PROJECT_ROOT}/data-protection/gitea"
LOG_FILE="${PROJECT_ROOT}/logs/gitea-protection.log"

# 创建必要的目录
mkdir -p "${BACKUP_DIR}" "${DATA_PROTECTION_DIR}" "$(dirname "${LOG_FILE}")"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "${LOG_FILE}"
}

# 获取实际的 Docker 卷名
get_gitea_volume() {
    docker-compose -f "${COMPOSE_FILE}" config --volumes | grep gitea-data || echo "gitea-data"
}

# 检查 Gitea 服务状态
check_gitea_status() {
    if docker-compose -f "${COMPOSE_FILE}" ps gitea | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# 自动化数据保护设置
auto_setup() {
    log "🔧 开始自动化数据保护设置..."
    
    # 1. 设置定时备份 cron 任务
    setup_cron_backup
    
    # 2. 创建数据保护配置
    create_protection_config
    
    # 3. 设置实时同步
    setup_real_time_sync
    
    # 4. 验证设置
    verify_setup
    
    log "✅ 数据保护设置完成"
}

# 设置定时备份
setup_cron_backup() {
    log "📅 设置定时备份任务..."
    
    # 创建 crontab 脚本
    cat > "${PROJECT_ROOT}/scripts/gitea-auto-backup.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
./gitea-data-protection.sh backup auto-$(date +%Y%m%d-%H%M%S)
EOF
    chmod +x "${PROJECT_ROOT}/scripts/gitea-auto-backup.sh"
    
    # 添加到 crontab (每6小时备份一次)
    (crontab -l 2>/dev/null; echo "0 */6 * * * ${PROJECT_ROOT}/scripts/gitea-auto-backup.sh") | crontab -
    
    log "✅ 定时备份任务已设置 (每6小时执行)"
}

# 创建数据保护配置
create_protection_config() {
    log "📋 创建数据保护配置..."
    
    cat > "${DATA_PROTECTION_DIR}/protection-config.yaml" << EOF
gitea_data_protection:
  version: "1.0"
  created: "$(date -Iseconds)"
  settings:
    backup_retention_days: 30
    backup_interval_hours: 6
    real_time_sync: true
    auto_recovery: true
    notification_enabled: true
  paths:
    compose_file: "${COMPOSE_FILE}"
    backup_dir: "${BACKUP_DIR}"
    data_protection_dir: "${DATA_PROTECTION_DIR}"
    log_file: "${LOG_FILE}"
  docker:
    volume_name: "$(get_gitea_volume)"
    container_name: "gitea"
    service_name: "gitea"
EOF
    
    log "✅ 数据保护配置已创建"
}

# 设置实时数据同步
setup_real_time_sync() {
    log "🔄 设置实时数据同步..."
    
    # 创建同步目录
    SYNC_DIR="${DATA_PROTECTION_DIR}/realtime-sync"
    mkdir -p "${SYNC_DIR}"
    
    # 创建同步脚本
    cat > "${DATA_PROTECTION_DIR}/sync-daemon.sh" << 'EOF'
#!/bin/bash

VOLUME_NAME="$1"
SYNC_DIR="$2"
LOG_FILE="$3"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SYNC] $1" >> "${LOG_FILE}"
}

# 使用 rsync 进行实时同步
while true; do
    if docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
        # 创建临时容器进行同步
        docker run --rm \
            -v "${VOLUME_NAME}:/source:ro" \
            -v "${SYNC_DIR}:/sync" \
            --name gitea-sync-temp \
            busybox \
            sh -c "rsync -av --delete /source/ /sync/ 2>/dev/null || cp -ru /source/* /sync/ 2>/dev/null || true"
        
        sleep 300  # 每5分钟同步一次
    else
        log "WARNING: Volume ${VOLUME_NAME} not found, retrying in 60s..."
        sleep 60
    fi
done
EOF
    chmod +x "${DATA_PROTECTION_DIR}/sync-daemon.sh"
    
    log "✅ 实时数据同步已设置"
}

# 执行备份
backup() {
    BACKUP_NAME="${1:-gitea-$(date +%Y%m%d-%H%M%S)}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    
    log "🔄 开始备份 Gitea 数据: ${BACKUP_NAME}"
    
    VOLUME_NAME=$(get_gitea_volume)
    
    # 检查卷是否存在
    if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
        log "❌ 错误: Docker 卷 '${VOLUME_NAME}' 不存在"
        exit 1
    fi
    
    # 创建一致性备份
    if check_gitea_status; then
        log "⏸️ 临时停止 Gitea 服务以确保数据一致性..."
        docker-compose -f "${COMPOSE_FILE}" stop gitea
        RESTART_NEEDED=true
    fi
    
    # 执行备份
    log "📦 创建备份到: ${BACKUP_PATH}"
    docker run --rm \
        -v "${VOLUME_NAME}:/source:ro" \
        -v "${BACKUP_DIR}:/backup" \
        busybox \
        tar -czf "/backup/$(basename "${BACKUP_PATH}")" -C /source .
    
    # 重启服务
    if [[ "${RESTART_NEEDED}" == "true" ]]; then
        log "🚀 重启 Gitea 服务..."
        docker-compose -f "${COMPOSE_FILE}" start gitea
    fi
    
    # 验证备份
    if [[ -f "${BACKUP_PATH}" ]]; then
        BACKUP_SIZE=$(du -h "${BACKUP_PATH}" | cut -f1)
        log "✅ 备份完成: ${BACKUP_PATH} (大小: ${BACKUP_SIZE})"
        
        # 记录备份元数据
        cat > "${BACKUP_PATH}.meta" << EOF
backup_name: ${BACKUP_NAME}
backup_time: $(date -Iseconds)
backup_size: ${BACKUP_SIZE}
volume_name: ${VOLUME_NAME}
gitea_version: $(docker-compose -f "${COMPOSE_FILE}" exec -T gitea gitea --version 2>/dev/null | head -1 || echo "unknown")
EOF
    else
        log "❌ 备份失败"
        exit 1
    fi
    
    # 清理旧备份
    cleanup_old_backups
}

# 清理旧备份
cleanup_old_backups() {
    log "🧹 清理30天前的旧备份..."
    find "${BACKUP_DIR}" -name "gitea-*.tar.gz" -mtime +30 -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "gitea-*.meta" -mtime +30 -delete 2>/dev/null || true
}

# 恢复数据
restore() {
    BACKUP_FILE="$1"
    
    if [[ -z "${BACKUP_FILE}" ]]; then
        log "📋 可用的备份文件:"
        ls -lt "${BACKUP_DIR}"/gitea-*.tar.gz | head -10
        echo ""
        echo "使用方法: $0 restore <backup_file>"
        return 1
    fi
    
    if [[ ! -f "${BACKUP_FILE}" ]]; then
        BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE}"
        if [[ ! -f "${BACKUP_FILE}" ]]; then
            log "❌ 备份文件不存在: ${BACKUP_FILE}"
            return 1
        fi
    fi
    
    log "🔄 开始恢复 Gitea 数据从: $(basename "${BACKUP_FILE}")"
    
    VOLUME_NAME=$(get_gitea_volume)
    
    # 停止服务
    log "⏸️ 停止 Gitea 服务..."
    docker-compose -f "${COMPOSE_FILE}" down
    
    # 备份现有数据（以防万一）
    if docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
        SAFETY_BACKUP="${BACKUP_DIR}/safety-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
        log "💾 创建安全备份: $(basename "${SAFETY_BACKUP}")"
        docker run --rm \
            -v "${VOLUME_NAME}:/source:ro" \
            -v "${BACKUP_DIR}:/backup" \
            busybox \
            tar -czf "/backup/$(basename "${SAFETY_BACKUP}")" -C /source .
    fi
    
    # 删除旧卷并创建新卷
    docker volume rm "${VOLUME_NAME}" 2>/dev/null || true
    docker volume create "${VOLUME_NAME}"
    
    # 恢复数据
    log "📦 恢复数据..."
    docker run --rm \
        -v "${VOLUME_NAME}:/target" \
        -v "$(dirname "${BACKUP_FILE}"):/backup:ro" \
        busybox \
        tar -xzf "/backup/$(basename "${BACKUP_FILE}")" -C /target
    
    # 启动服务
    log "🚀 启动 Gitea 服务..."
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    # 等待服务启动并验证
    sleep 10
    if check_gitea_status; then
        log "✅ 数据恢复完成，服务正常运行"
    else
        log "⚠️ 服务启动可能有问题，请检查日志"
    fi
}

# 健康检查
health_check() {
    log "🏥 开始健康检查..."
    
    # 检查服务状态
    if check_gitea_status; then
        log "✅ Gitea 服务运行正常"
    else
        log "❌ Gitea 服务未运行"
        return 1
    fi
    
    # 检查数据卷
    VOLUME_NAME=$(get_gitea_volume)
    if docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
        log "✅ 数据卷 ${VOLUME_NAME} 存在"
        
        # 检查数据完整性
        REPO_COUNT=$(docker run --rm \
            -v "${VOLUME_NAME}:/data:ro" \
            busybox \
            find /data -name "*.git" -type d | wc -l)
        log "📊 发现 ${REPO_COUNT} 个 Git 仓库"
    else
        log "❌ 数据卷不存在"
        return 1
    fi
    
    # 检查备份状态
    RECENT_BACKUPS=$(find "${BACKUP_DIR}" -name "gitea-*.tar.gz" -mtime -1 | wc -l)
    log "📈 最近24小时内的备份: ${RECENT_BACKUPS} 个"
    
    if [[ ${RECENT_BACKUPS} -eq 0 ]]; then
        log "⚠️ 警告: 最近24小时内无备份"
    fi
    
    log "✅ 健康检查完成"
}

# 验证设置
verify_setup() {
    log "🔍 验证数据保护设置..."
    
    # 检查备份目录
    if [[ -d "${BACKUP_DIR}" ]]; then
        log "✅ 备份目录存在: ${BACKUP_DIR}"
    else
        log "❌ 备份目录不存在"
        return 1
    fi
    
    # 检查定时任务
    if crontab -l 2>/dev/null | grep -q "gitea-auto-backup"; then
        log "✅ 定时备份任务已设置"
    else
        log "⚠️ 未发现定时备份任务"
    fi
    
    # 检查配置文件
    if [[ -f "${DATA_PROTECTION_DIR}/protection-config.yaml" ]]; then
        log "✅ 数据保护配置文件存在"
    else
        log "❌ 数据保护配置文件不存在"
        return 1
    fi
    
    log "✅ 设置验证完成"
}

# 启动数据保护
start() {
    log "🚀 启动 Gitea 数据保护服务..."
    
    # 启动 Gitea
    docker-compose -f "${COMPOSE_FILE}" up -d
    
    # 等待服务启动
    sleep 10
    
    # 启动同步守护进程
    if [[ -f "${DATA_PROTECTION_DIR}/sync-daemon.sh" ]]; then
        VOLUME_NAME=$(get_gitea_volume)
        SYNC_DIR="${DATA_PROTECTION_DIR}/realtime-sync"
        nohup "${DATA_PROTECTION_DIR}/sync-daemon.sh" "${VOLUME_NAME}" "${SYNC_DIR}" "${LOG_FILE}" > /dev/null 2>&1 &
        echo $! > "${DATA_PROTECTION_DIR}/sync-daemon.pid"
        log "✅ 实时同步守护进程已启动 (PID: $(cat "${DATA_PROTECTION_DIR}/sync-daemon.pid"))"
    fi
    
    health_check
}

# 停止数据保护
stop() {
    log "⏸️ 停止 Gitea 数据保护服务..."
    
    # 停止同步守护进程
    if [[ -f "${DATA_PROTECTION_DIR}/sync-daemon.pid" ]]; then
        PID=$(cat "${DATA_PROTECTION_DIR}/sync-daemon.pid")
        if kill "${PID}" 2>/dev/null; then
            log "✅ 同步守护进程已停止"
        fi
        rm -f "${DATA_PROTECTION_DIR}/sync-daemon.pid"
    fi
    
    # 停止 Gitea
    docker-compose -f "${COMPOSE_FILE}" down
    
    log "✅ 服务已停止"
}

# 主函数
main() {
    case "${1:-help}" in
        "auto-setup")
            auto_setup
            ;;
        "start")
            start
            ;;
        "stop")
            stop
            ;;
        "backup")
            backup "$2"
            ;;
        "restore")
            restore "$2"
            ;;
        "health")
            health_check
            ;;
        "help"|*)
            echo "Gitea 数据保护管理脚本"
            echo ""
            echo "使用方法:"
            echo "  $0 auto-setup          # 自动化数据保护设置"
            echo "  $0 start               # 启动数据保护服务"
            echo "  $0 stop                # 停止数据保护服务"
            echo "  $0 backup [name]       # 创建备份"
            echo "  $0 restore <backup>    # 恢复数据"
            echo "  $0 health              # 健康检查"
            echo "  $0 help                # 显示帮助"
            echo ""
            echo "数据保护特性:"
            echo "  ✅ 自动定时备份 (每6小时)"
            echo "  ✅ 实时数据同步"
            echo "  ✅ 一键恢复"
            echo "  ✅ 健康监控"
            echo "  ✅ 备份元数据记录"
            echo "  ✅ 自动清理旧备份"
            ;;
    esac
}

# 创建 scripts 目录
mkdir -p "${PROJECT_ROOT}/scripts"

main "$@"