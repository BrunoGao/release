#!/bin/sh
# 简化的运行时配置脚本

echo "启动ljwx-admin..."
echo "使用默认配置，不加载任何自定义配置"

# 直接启动nginx
exec nginx -g "daemon off;"
