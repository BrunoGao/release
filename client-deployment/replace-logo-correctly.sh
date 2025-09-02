#!/bin/bash
source custom-config.env # 加载配置
echo "🔄 正确替换前端应用Logo..."

if [ "$VITE_CUSTOM_LOGO" = "true" ] && [ -f "custom-logo.svg" ]; then
    # 查找所有logo相关的SVG文件
    echo "📋 查找前端应用中的logo文件..."
    LOGO_FILES=$(docker exec ljwx-admin find /usr/share/nginx/html/assets -name "logo*.svg" 2>/dev/null)
    
    if [ -n "$LOGO_FILES" ]; then
        echo "找到以下logo文件:"
        echo "$LOGO_FILES"
        
        # 备份原始logo文件
        for file in $LOGO_FILES; do
            docker exec ljwx-admin cp "$file" "$file.backup" 2>/dev/null || true
            echo "✅ 已备份: $file"
        done
        
        # 用定制logo替换所有logo文件
        for file in $LOGO_FILES; do
            docker exec ljwx-admin cp /tmp/custom-logo.svg "$file"
            echo "✅ 已替换: $file"
        done
        
        # 设置权限
        for file in $LOGO_FILES; do
            docker exec ljwx-admin chmod 644 "$file"
        done
        
        echo "🎉 Logo替换完成！"
        echo "💡 请强制刷新浏览器页面 (Ctrl+F5) 查看效果"
    else
        echo "❌ 未找到logo文件"
    fi
else
    echo "❌ Logo配置未启用或custom-logo.svg文件不存在"
fi 
