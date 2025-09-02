#!/bin/bash
echo "🔧 快速修复定制Logo..."
source custom-config.env # 加载配置
if [ "$VITE_CUSTOM_LOGO" = "true" ] && [ -f "custom-logo.svg" ]; then
    ./replace-logo-correctly.sh
else
    echo "❌ Logo配置未启用或文件不存在"
fi 
