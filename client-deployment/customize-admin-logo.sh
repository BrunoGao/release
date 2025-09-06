#!/bin/bash
# ljwx-admin自定义Logo实现脚本
# 支持png、jpg、svg格式的logo文件

set -e

# 加载配置文件
CONFIG_FILE=${1:-"custom-config.env"}
if [ -f "$CONFIG_FILE" ]; then
    source $CONFIG_FILE
    echo "📋 已加载配置文件: $CONFIG_FILE"
else
    echo "❌ 错误: 配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

echo ""
echo "==================== ljwx-admin自定义Logo ===================="

# 检查是否启用自定义logo
if [ "$VITE_CUSTOM_LOGO" != "true" ]; then
    echo "⚠️  自定义Logo功能未启用，请在配置文件中设置 VITE_CUSTOM_LOGO=true"
    exit 0
fi

# 检查ljwx-admin容器是否运行
CONTAINER_ID=$(docker ps -q -f name=ljwx-admin)
if [ -z "$CONTAINER_ID" ]; then
    echo "❌ 错误: ljwx-admin 容器未运行"
    exit 1
fi

# 支持的logo文件格式
LOGO_EXTENSIONS=("png" "jpg" "jpeg" "svg")
FOUND_LOGO=""

echo "🔍 检查custom-assets/目录中的logo文件..."

# 查找logo文件
for ext in "${LOGO_EXTENSIONS[@]}"; do
    if [ -f "custom-assets/logo.$ext" ]; then
        FOUND_LOGO="custom-assets/logo.$ext"
        echo "✅ 找到自定义logo文件: $FOUND_LOGO"
        break
    fi
done

# 如果没找到logo.xxx，尝试查找包含logo的文件
if [ -z "$FOUND_LOGO" ]; then
    for ext in "${LOGO_EXTENSIONS[@]}"; do
        LOGO_FILES=$(find custom-assets/ -name "*logo*.$ext" 2>/dev/null | head -1)
        if [ -n "$LOGO_FILES" ]; then
            FOUND_LOGO="$LOGO_FILES"
            echo "✅ 找到自定义logo文件: $FOUND_LOGO"
            break
        fi
    done
fi

if [ -z "$FOUND_LOGO" ]; then
    echo "❌ 错误: 未在custom-assets/目录中找到logo文件"
    echo "支持的文件名格式:"
    echo "  - logo.png, logo.jpg, logo.jpeg, logo.svg"
    echo "  - 或任何包含'logo'的图片文件"
    exit 1
fi

echo ""
echo "🔄 开始替换ljwx-admin中的logo..."

# 获取文件扩展名
FILE_EXT="${FOUND_LOGO##*.}"
CONTAINER_LOGO_PATH="/usr/share/nginx/html/logo-custom.$FILE_EXT"

# 1. 将logo文件复制到容器中
echo "📋 步骤1: 复制logo文件到容器..."
docker cp "$FOUND_LOGO" "$CONTAINER_ID:$CONTAINER_LOGO_PATH"
echo "✅ logo文件已复制到容器: $CONTAINER_LOGO_PATH"

# 2. 更新system-logo组件以使用自定义logo
echo "📋 步骤2: 更新前端logo引用..."

# 创建临时的JavaScript代码来注入logo配置
LOGO_CONFIG_JS="/tmp/logo-config-$(date +%s).js"
cat > "$LOGO_CONFIG_JS" << EOF
// 自定义Logo配置注入脚本
(function() {
    // 设置全局logo配置
    window.CUSTOM_LOGO_CONFIG = {
        enabled: true,
        logoUrl: '/logo-custom.$FILE_EXT',
        timestamp: Date.now()
    };
    
    // 如果页面已加载，触发logo更新事件
    if (document.readyState === 'complete') {
        window.dispatchEvent(new CustomEvent('customLogoConfigUpdated'));
    } else {
        window.addEventListener('load', function() {
            window.dispatchEvent(new CustomEvent('customLogoConfigUpdated'));
        });
    }
})();
EOF

# 将配置文件复制到容器的html根目录
docker cp "$LOGO_CONFIG_JS" "$CONTAINER_ID:/usr/share/nginx/html/logo-config.js"
rm -f "$LOGO_CONFIG_JS"

# 3. 在index.html中注入logo配置脚本
echo "📋 步骤3: 注入logo配置到index.html..."
docker exec "$CONTAINER_ID" sh -c "
    # 检查是否已经注入过
    if ! grep -q 'logo-config.js' /usr/share/nginx/html/index.html; then
        # 在</head>前插入script标签
        sed -i 's|</head>|<script src=\"/logo-config.js\"></script></head>|' /usr/share/nginx/html/index.html
        echo '✅ 已注入logo配置脚本到index.html'
    else
        echo '⚠️  logo配置脚本已存在，跳过注入'
    fi
"

# 4. 设置文件权限
echo "📋 步骤4: 设置文件权限..."
docker exec "$CONTAINER_ID" sh -c "
    chmod 644 $CONTAINER_LOGO_PATH
    chmod 644 /usr/share/nginx/html/logo-config.js
    echo '✅ 文件权限设置完成'
"

# 5. 重新加载nginx配置
echo "📋 步骤5: 重新加载nginx配置..."
docker exec "$CONTAINER_ID" nginx -s reload
echo "✅ nginx配置已重新加载"

# 6. 清理浏览器缓存提示
echo ""
echo "==================== 完成 ===================="
echo "🎉 ljwx-admin自定义logo配置完成！"
echo ""
echo "📋 配置信息:"
echo "  - 源文件: $FOUND_LOGO"
echo "  - 容器路径: $CONTAINER_LOGO_PATH"
echo "  - 文件格式: $FILE_EXT"
echo ""
echo "💡 重要提示:"
echo "  1. 请强制刷新浏览器页面 (Ctrl+F5 或 Cmd+Shift+R)"
echo "  2. 如果logo未生效，请清理浏览器缓存"
echo "  3. logo文件建议尺寸: 32x32 或 64x64 像素"
echo ""
echo "🌐 访问地址: http://$SERVER_IP:$LJWX_ADMIN_EXTERNAL_PORT"
echo ""