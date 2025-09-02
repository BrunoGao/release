#!/bin/bash

# 客户现场离线部署脚本 #专为无网络环境设计，使用预加载镜像
# 使用方法：./deploy-client-offline.sh [客户配置文件名]

set -e

# 默认配置文件
CONFIG_FILE=${1:-"custom-config.env"}

echo "==================== 智能穿戴系统离线部署 ===================="
echo "使用配置文件: $CONFIG_FILE"
echo "部署模式: 离线部署 (使用预加载镜像)"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件 $CONFIG_FILE 不存在"
    echo "请复制 custom-config.env 并根据客户需求修改配置"
    exit 1
fi

# 检查Docker和docker-compose是否安装
if ! command -v docker > /dev/null 2>&1; then
    echo "错误: Docker 未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose > /dev/null 2>&1; then
    echo "错误: docker-compose 未安装，请先安装docker-compose"
    exit 1
fi

# 加载配置文件
. "$CONFIG_FILE"

echo ""
echo "==================== 离线镜像检查 ===================="
echo "�� 离线部署模式 - 检查预加载镜像"

# 从docker-compose.yml动态读取版本号 #确保使用正确的镜像标签
MYSQL_IMAGE=$(egrep '^ *image:.*ljwx-mysql:' docker-compose.yml | sed 's/.*ljwx-mysql:\([^ ]*\).*/\1/' | head -1)
REDIS_IMAGE=$(egrep '^ *image:.*ljwx-redis:' docker-compose.yml | sed 's/.*ljwx-redis:\([^ ]*\).*/\1/' | head -1)
BOOT_IMAGE=$(egrep '^ *image:.*ljwx-boot:' docker-compose.yml | sed 's/.*ljwx-boot:\([^ ]*\).*/\1/' | head -1)
BIGSCREEN_IMAGE=$(egrep '^ *image:.*ljwx-bigscreen:' docker-compose.yml | sed 's/.*ljwx-bigscreen:\([^ ]*\).*/\1/' | head -1)
ADMIN_IMAGE=$(egrep '^ *image:.*ljwx-admin:' docker-compose.yml | sed 's/.*ljwx-admin:\([^ ]*\).*/\1/' | head -1)

echo "�� 检查本地镜像:"
echo "- ljwx-mysql:$MYSQL_IMAGE"
echo "- ljwx-redis:$REDIS_IMAGE" 
echo "- ljwx-boot:$BOOT_IMAGE"
echo "- ljwx-bigscreen:$BIGSCREEN_IMAGE"
echo "- ljwx-admin:$ADMIN_IMAGE"

# 检查本地镜像是否存在 #确保所有必需镜像已预加载
MISSING_IMAGES=""
FOUND_IMAGES=0
for img in "ljwx-mysql:$MYSQL_IMAGE" "ljwx-redis:$REDIS_IMAGE" "ljwx-boot:$BOOT_IMAGE" "ljwx-bigscreen:$BIGSCREEN_IMAGE" "ljwx-admin:$ADMIN_IMAGE"; do
    if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^$img$"; then
        echo "✅ 找到镜像: $img"
        FOUND_IMAGES=$((FOUND_IMAGES + 1))
    else
        MISSING_IMAGES="$MISSING_IMAGES $img"
        echo "❌ 缺失镜像: $img"
    fi
done

if [ $FOUND_IMAGES -eq 0 ]; then
    echo ""
    echo "❌ 严重错误: 未找到任何必需镜像！"
    echo "请确保已通过以下方式之一加载镜像："
    echo "1. docker load -i ljwx-images.tar"
    echo "2. 或单独加载: docker load -i ljwx-mysql.tar"
    echo "3. 或使用镜像导入脚本"
    exit 1
elif [ -n "$MISSING_IMAGES" ]; then
    echo ""
    echo "⚠️  警告: 发现缺失镜像，但已找到 $FOUND_IMAGES/5 个镜像"
    echo "🔧 系统将尝试继续部署，如果失败请补充缺失镜像"
    echo "💡 缺失的镜像: $MISSING_IMAGES"
    sleep 3
else
    echo "✅ 所有必需镜像已就绪 ($FOUND_IMAGES/5)"
fi

echo ""
echo "==================== 开始部署 ===================="

# 停止现有服务但保留数据卷
echo "停止现有服务(保留数据卷)..."
docker-compose -f docker-compose.yml down

# 启动所有服务 #使用配置文件启动docker-compose服务
echo "🚀 正在启动所有服务..."
docker-compose -f docker-compose.yml --env-file $CONFIG_FILE up -d

# 等待服务初始化
echo "⏳ 等待服务初始化..."
sleep 15

echo ""
echo "==================== 服务状态检查 ===================="
docker-compose -f docker-compose.yml ps

# 替换前端应用中的大屏URL
echo ""
echo "🔄 更新前端大屏链接地址..."
if [ -f "replace-bigscreen-url.sh" ]; then
    ./replace-bigscreen-url.sh
    echo "✅ 大屏链接地址更新完成"
else
    echo "⚠️  警告: replace-bigscreen-url.sh 脚本不存在"
fi

echo ""
echo "🎉==================== 离线部署完成 ===================="
echo "✅ 所有服务已成功启动！"
echo ""
echo "📱 访问地址:"
echo "- 管理端: http://localhost:8080 或 http://$SERVER_IP:8080"
echo "- 大屏端: http://localhost:8001 或 http://$SERVER_IP:8001"
echo ""
echo "🔐 默认登录信息:"
echo "- 用户名: admin"
echo "- 密码: admin123"
echo ""
echo "🔌 离线部署特性:"
echo "- ✅ 无需网络连接"
echo "- ✅ 使用预加载镜像"
echo "- ✅ 自动配置客户定制设置"
