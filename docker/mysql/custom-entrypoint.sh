#!/bin/bash
set -eo pipefail
shopt -s nullglob

# 强制初始化模式：删除现有数据目录并重新初始化
if [ "$MYSQL_FORCE_INIT" = "1" ]; then
    echo "🔄 [LJWX] 强制初始化模式已启用"
    
    # 如果数据目录存在且非空，清空它
    if [ -d "/var/lib/mysql" ] && [ "$(ls -A /var/lib/mysql 2>/dev/null)" ]; then
        echo "🗑️  [LJWX] 清理现有MySQL数据目录..."
        rm -rf /var/lib/mysql/*
    fi
    
    echo "✅ [LJWX] 数据目录已清理，将执行完整初始化..."
fi

# 执行官方的Docker入口脚本
exec docker-entrypoint.sh "$@"