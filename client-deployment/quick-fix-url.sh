#!/bin/bash
echo "🔧 快速修复大屏URL为192.168.1.6:8001..."

CONTAINER_ID=$(docker ps -q -f name=ljwx-admin)
if [ -z "$CONTAINER_ID" ]; then
    echo "❌ ljwx-admin容器未运行"
    exit 1
fi

echo "📦 容器ID: $CONTAINER_ID"

# 直接替换为192.168.1.6:8001
docker exec "$CONTAINER_ID" sh -c "
    find /usr/share/nginx/html -name '*.js' -o -name '*.html' | while read file; do
        sed -i 's|192\.168\.1\.7:8001|192.168.1.6:8001|g' \"\$file\"
        sed -i 's|localhost:8001|192.168.1.6:8001|g' \"\$file\"
    done
"

# 重新加载nginx
docker exec "$CONTAINER_ID" nginx -s reload

echo "✅ URL已修复为192.168.1.6:8001"
echo "💡 请清除浏览器缓存并刷新页面"
