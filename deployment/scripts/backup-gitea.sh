#!/bin/bash

# Gitea 数据备份脚本
# 使用方法: ./backup-gitea.sh [backup_name]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/gitea"
BACKUP_DIR="${PROJECT_ROOT}/backup/gitea"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 生成备份名称
BACKUP_NAME="${1:-gitea-$(date +%Y%m%d-%H%M%S)}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "🔄 开始备份 Gitea 数据..."
echo "📂 源目录: ${DATA_DIR}"
echo "💾 备份到: ${BACKUP_PATH}"

# 停止容器（可选）
read -p "是否停止 Gitea 容器以确保数据一致性？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  停止 Gitea 容器..."
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f gitea-compose.yml stop gitea
    RESTART_CONTAINER=true
fi

# 执行备份
echo "📦 创建备份..."
tar -czf "${BACKUP_PATH}.tar.gz" -C "${PROJECT_ROOT}/data" gitea

# 重启容器（如果之前停止了）
if [[ "${RESTART_CONTAINER}" == "true" ]]; then
    echo "🚀 重启 Gitea 容器..."
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f gitea-compose.yml start gitea
fi

echo "✅ 备份完成: ${BACKUP_PATH}.tar.gz"
echo "📊 备份大小: $(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)"

# 清理旧备份（保留最近5个）
echo "🧹 清理旧备份..."
cd "${BACKUP_DIR}"
ls -t gitea-*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

echo "🎉 备份任务完成！" 