#!/bin/sh
# ljwx-admin 运行时配置脚本

echo "启动ljwx-admin..."

# 设置默认的后端服务地址（如果环境变量未设置）
LJWX_BOOT_HOST=${LJWX_BOOT_HOST:-"ljwx-boot"}
LJWX_BOOT_PORT=${LJWX_BOOT_PORT:-"9998"}
LJWX_BIGSCREEN_HOST=${LJWX_BIGSCREEN_HOST:-"ljwx-bigscreen"}
LJWX_BIGSCREEN_PORT=${LJWX_BIGSCREEN_PORT:-"8001"}

# 缓存控制环境变量（默认为开发模式，禁用JS/CSS缓存）
ENABLE_STATIC_CACHE=${ENABLE_STATIC_CACHE:-"false"}

echo "后端服务配置："
echo "  Boot服务: ${LJWX_BOOT_HOST}:${LJWX_BOOT_PORT}"
echo "  Bigscreen服务: ${LJWX_BIGSCREEN_HOST}:${LJWX_BIGSCREEN_PORT}"
echo "  静态资源缓存: ${ENABLE_STATIC_CACHE}"

# 动态替换nginx配置中的upstream地址
sed -i "s/ljwx-boot:9998/${LJWX_BOOT_HOST}:${LJWX_BOOT_PORT}/g" /etc/nginx/nginx.conf
sed -i "s/ljwx-bigscreen:8001/${LJWX_BIGSCREEN_HOST}:${LJWX_BIGSCREEN_PORT}/g" /etc/nginx/nginx.conf

# 根据环境变量动态配置JS/CSS缓存策略
if [ "$ENABLE_STATIC_CACHE" = "true" ]; then
    echo "启用生产模式缓存..."
    # 生产环境：启用JS/CSS长期缓存
    sed -i '/# JS\/CSS文件禁用缓存/,/}$/{
        s/add_header Cache-Control "no-cache, no-store, must-revalidate";/expires 1y;\n            add_header Cache-Control "public, immutable";/
        /add_header Pragma "no-cache";/d
        /add_header Expires "0";/d
    }' /etc/nginx/nginx.conf
else 
    echo "使用开发模式缓存（禁用JS/CSS缓存）..."
    # 开发/测试环境：禁用JS/CSS缓存（默认配置）
fi

echo "nginx配置已更新"

# 启动nginx
exec nginx -g "daemon off;"
