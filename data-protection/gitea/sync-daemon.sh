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
