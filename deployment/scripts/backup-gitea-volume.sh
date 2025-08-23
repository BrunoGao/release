#!/bin/bash

# Gitea Docker 命名卷备份脚本
# 使用方法: ./backup-gitea-volume.sh [backup_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backup/gitea"
VOLUME_NAME="compose_gitea-data"
COMPOSE_FILE="${PROJECT_ROOT}/docker/compose/gitea-compose.yml"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 生成备份名称
BACKUP_NAME="${1:-gitea-volume-$(date +%Y%m%d-%H%M%S)}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "🔄 开始备份 Gitea Docker 卷..."
echo "📦 卷名称: ${VOLUME_NAME}"
echo "💾 备份到: ${BACKUP_PATH}.tar.gz"

# 检查卷是否存在
if ! docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
    echo "❌ 错误: Docker 卷 '${VOLUME_NAME}' 不存在"
    exit 1
fi

# 停止容器（确保数据一致性）
echo "⏸️  停止 Gitea 容器..."
cd "${PROJECT_ROOT}/docker/compose"
docker-compose -f gitea-compose.yml stop gitea

# 使用临时容器备份卷数据
echo "📦 创建备份..."
docker run --rm \
    -v "${VOLUME_NAME}:/source:ro" \
    -v "${BACKUP_DIR}:/backup" \
    busybox \
    tar -czf "/backup/${BACKUP_NAME}.tar.gz" -C /source .

# 重启容器
echo "🚀 重启 Gitea 容器..."
docker-compose -f gitea-compose.yml start gitea

echo "✅ 备份完成: ${BACKUP_PATH}.tar.gz"
echo "📊 备份大小: $(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)"

# 显示卷信息
echo "📋 卷信息:"
docker volume inspect "${VOLUME_NAME}" --format "{{.Mountpoint}}"

# 清理旧备份（保留最近5个）
echo "🧹 清理旧备份..."
cd "${BACKUP_DIR}"
ls -t gitea-volume-*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

echo "🎉 备份任务完成！" 