#!/bin/bash

# Gitea Docker 命名卷恢复脚本
# 使用方法: ./restore-gitea-volume.sh <backup_file.tar.gz>

set -e

if [ $# -eq 0 ]; then
    echo "❌ 使用方法: $0 <backup_file.tar.gz>"
    echo "💡 示例: $0 backup/gitea/gitea-volume-20240718-225500.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VOLUME_NAME="compose_gitea-data"
COMPOSE_FILE="${PROJECT_ROOT}/docker/compose/gitea-compose.yml"

# 检查备份文件是否存在
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ 错误: 备份文件 '${BACKUP_FILE}' 不存在"
    exit 1
fi

echo "🔄 开始恢复 Gitea Docker 卷..."
echo "📦 卷名称: ${VOLUME_NAME}"
echo "📁 备份文件: ${BACKUP_FILE}"

# 确认操作
read -p "⚠️  这将覆盖现有数据，确定要继续吗？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 操作已取消"
    exit 1
fi

# 停止容器
echo "⏸️  停止 Gitea 容器..."
cd "${PROJECT_ROOT}/docker/compose"
docker-compose -f gitea-compose.yml down

# 删除现有卷（如果存在）
if docker volume inspect "${VOLUME_NAME}" >/dev/null 2>&1; then
    echo "🗑️  删除现有卷..."
    docker volume rm "${VOLUME_NAME}"
fi

# 创建新卷
echo "📦 创建新卷..."
docker volume create "${VOLUME_NAME}"

# 恢复数据
echo "📥 恢复数据..."
docker run --rm \
    -v "${VOLUME_NAME}:/target" \
    -v "$(dirname "${BACKUP_FILE}"):/backup:ro" \
    busybox \
    tar -xzf "/backup/$(basename "${BACKUP_FILE}")" -C /target

# 重启服务
echo "🚀 重启 Gitea 服务..."
docker-compose -f gitea-compose.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if curl -s http://localhost:3000/api/healthz >/dev/null; then
    echo "✅ 恢复完成！Gitea 服务正常运行"
    echo "🌐 访问地址: http://192.168.1.83:3000"
else
    echo "⚠️  服务可能还在启动中，请稍等片刻后检查"
fi

echo "🎉 恢复任务完成！" 