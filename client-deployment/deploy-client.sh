#!/bin/bash

# 客户现场部署脚本 - 使用预构建镜像 (Docker命名卷持久化)
# 使用方法：./deploy-client.sh [客户配置文件名] [offline]

set -e

# CentOS文件格式修复 #处理Windows换行符
if [ -f /etc/redhat-release ];then 
    echo "🔧 检测到CentOS系统，处理文件格式..."
    if ! command -v dos2unix > /dev/null 2>&1;then #安装dos2unix
        echo "📦 安装dos2unix工具..."
        if yum install -y dos2unix 2>/dev/null||echo "❌ 无法自动安装dos2unix，请手动执行: yum install dos2unix && dos2unix *";then 
            dos2unix * 2>/dev/null||true #转换所有文件格式
            echo "✅ 文件格式处理完成"
        fi
    else 
        dos2unix * 2>/dev/null||true #转换所有文件格式
        echo "✅ 文件格式处理完成"
    fi
fi

# 检查是否为离线模式
OFFLINE_MODE=false
if [[ "$1" == "offline" || "$2" == "offline" ]]; then
    OFFLINE_MODE=true
    echo "🔌 离线部署模式已启用"
    # 如果第一个参数是offline，使用默认配置文件
    if [[ "$1" == "offline" ]]; then
        CONFIG_FILE="custom-config.env"
    else
        CONFIG_FILE="$1"
    fi
else
    # 默认配置文件
    CONFIG_FILE=${1:-"custom-config.env"}
fi

echo "==================== 智能穿戴系统客户现场部署 ===================="
echo "使用配置文件: $CONFIG_FILE"
if [ "$OFFLINE_MODE" = true ]; then
    echo "部署模式: 离线部署 (使用本地镜像 + Docker命名卷持久化)"
else
    echo "部署模式: 在线部署 (预构建镜像部署 + Docker命名卷持久化)"
fi

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
echo "==================== 配置验证 ===================="
# 验证配置一致性
if [ -f "validate-config.sh" ]; then
    bash validate-config.sh $CONFIG_FILE
else
    echo "⚠️  警告: validate-config.sh 不存在，跳过配置验证"
fi

echo ""
echo "配置信息:"
echo "- 大屏标题: $BIGSCREEN_TITLE"
echo "- 管理端标题: $VITE_APP_TITLE"
echo "- 公司名称: $COMPANY_NAME"
echo "- 服务器IP: $SERVER_IP"
echo "- 大屏端口: $BIGSCREEN_PORT"
echo "- 大屏地址: $VITE_BIGSCREEN_URL"

# 检查必需的定制化文件
echo ""
echo "==================== 定制化文件检查 ===================="

# 文件挂载修复函数 #避免Docker创建目录
fix_file_mounts() {
    echo "🔧 修复文件挂载问题..."
    
    # 创建必需的目录结构
    mkdir -p logs/{mysql,redis,ljwx-boot,ljwx-bigscreen,ljwx-admin}
    mkdir -p backup/{mysql,redis,ljwx-boot,ljwx-bigscreen}
    
    # 检查client-data.sql
    if [ ! -f "client-data.sql" ]; then
        echo "⚠️  警告: client-data.sql 不存在，将影响首次部署数据初始化"
        echo "-- 客户数据占位符" > client-data.sql
    fi
    
    echo "✅ 文件挂载修复完成 (已创建logs和backup目录结构)"
}

# 执行文件挂载修复
fix_file_mounts

# 检查自定义配置文件
if [ -f "custom-config.py" ]; then
    echo "✅ 自定义Python配置: custom-config.py"
else
    echo "❌ 错误: 未找到 custom-config.py 文件"
    exit 1
fi

if [ -f "custom-admin-config.js" ]; then
    echo "✅ 自定义前端配置: custom-admin-config.js"
else
    echo "❌ 错误: 未找到 custom-admin-config.js 文件"
    exit 1
fi

# 智能数据文件检查 #区分首次部署和升级
is_first_deployment() {
    # 检查是否存在任何命名卷数据
    for volume in mysql_data redis_data ljwx_boot_data ljwx_bigscreen_data; do
        if docker volume ls -q | grep -q "^client-deployment_${volume}$"; then
            return 1 #不是首次部署
        fi
    done
    return 0 #首次部署
}

if is_first_deployment; then
    echo "📦 检测到首次部署"
    if [ -f "client-data.sql" ] && [ -s "client-data.sql" ]; then
        echo "✅ 客户数据文件: client-data.sql (首次部署必需)"
    else
        echo "⚠️  警告: client-data.sql 文件为空或不存在，将使用默认数据"
    fi
else
    echo "🔄 检测到升级部署 (已有数据卷)"
    if [ -f "client-data.sql" ]; then
        echo "ℹ️  info: client-data.sql 存在但不会被使用 (数据已持久化)"
    fi
fi

# 检查自定义资源
if [ -d "custom-assets" ]; then
    echo "✅ 自定义资源目录: custom-assets/"
else
    echo "⚠️  警告: 未找到 custom-assets/ 目录，将使用默认资源"
    mkdir -p custom-assets
fi

echo ""
read -p "确认使用以上配置进行部署? (y/N): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "部署已取消"
    exit 0
fi

echo ""
echo "==================== Docker命名卷状态检查 ===================="

# 检查现有Docker命名卷
echo "检查现有Docker命名卷..."
EXISTING_VOLUMES=""

for volume in mysql_data redis_data ljwx_boot_data ljwx_bigscreen_data; do
    if docker volume ls -q | grep -q "^client-deployment_${volume}$"; then
        EXISTING_VOLUMES="$EXISTING_VOLUMES $volume"
    fi
done

if [ -n "$EXISTING_VOLUMES" ]; then
    echo "发现现有Docker命名卷:"
    for volume in $EXISTING_VOLUMES; do
        echo "  - client-deployment_$volume"
    done
    echo ""
    
    # 智能备份策略选择
    echo "🔄 升级部署检测到现有数据，请选择备份策略:"
    echo "1) 在线备份 (推荐) - 需要容器运行，完整SQL导出"
    echo "2) 离线卷备份 - 直接备份Docker卷，速度快"
    echo "3) 跳过备份 - 风险自担，直接升级"
    echo "4) 退出部署 - 手动处理后再运行"
    echo ""
    
    while true; do
        read -p "请选择备份策略 [1-4]: " backup_choice
        case $backup_choice in
            1)
                echo "📦 执行在线备份..."
                # 检查容器是否运行
                if docker ps | grep -q ljwx-mysql; then
                    if [ -f "auto-backup.sh" ]; then
                        ./auto-backup.sh
                        echo "✅ 在线备份完成"
                    else
                        echo "❌ auto-backup.sh 不存在，改用卷备份"
                        backup_choice=2
                        continue
                    fi
                else
                    echo "❌ MySQL容器未运行，无法在线备份，改用卷备份"
                    backup_choice=2
                    continue
                fi
                break
                ;;
            2)
                echo "📦 执行离线卷备份..."
                backup_dir="backup/volume_backup_$(date +%Y%m%d_%H%M%S)"
                mkdir -p "$backup_dir"
                for volume in $EXISTING_VOLUMES; do
                    echo "备份卷: client-deployment_$volume"
                    docker run --rm -v "client-deployment_$volume:/data" -v "$(pwd)/$backup_dir:/backup" alpine tar czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null || echo "警告: $volume 备份失败"
                done
                echo "✅ 离线卷备份完成: $backup_dir"
                break
                ;;
            3)
                echo "⚠️  跳过备份，直接升级 (风险自担)"
                break
                ;;
            4)
                echo "部署已取消"
                exit 0
                ;;
            *)
                echo "❌ 无效选择，请输入 1-4"
                ;;
        esac
    done
else
    echo "✅ 首次部署，将创建新的Docker命名卷"
fi

if [ "$OFFLINE_MODE" = false ]; then
    echo ""
    echo "==================== 登录镜像仓库 ===================="
    echo "正在登录阿里云容器镜像服务..."

    # 登录Docker镜像仓库
    echo "admin123" | docker login --username=brunogao --password-stdin crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com
    if [ $? -ne 0 ]; then
        echo "❌ Docker登录失败，请检查用户名和密码"
        exit 1
    fi
    echo "✅ Docker登录成功"

    echo ""
    echo "==================== 拉取最新镜像 ===================="
    echo "正在拉取预构建镜像..."

    # 从docker-compose.yml动态读取版本号
    MYSQL_IMAGE=$(egrep '^ *image:.*ljwx-mysql:' docker-compose.yml | sed 's/.*ljwx-mysql:\([^ ]*\).*/\1/' | head -1)
    REDIS_IMAGE=$(egrep '^ *image:.*ljwx-redis:' docker-compose.yml | sed 's/.*ljwx-redis:\([^ ]*\).*/\1/' | head -1)
    BOOT_IMAGE=$(egrep '^ *image:.*ljwx-boot:' docker-compose.yml | sed 's/.*ljwx-boot:\([^ ]*\).*/\1/' | head -1)
    BIGSCREEN_IMAGE=$(egrep '^ *image:.*ljwx-bigscreen:' docker-compose.yml | sed 's/.*ljwx-bigscreen:\([^ ]*\).*/\1/' | head -1)
    ADMIN_IMAGE=$(egrep '^ *image:.*ljwx-admin:' docker-compose.yml | sed 's/.*ljwx-admin:\([^ ]*\).*/\1/' | head -1)

    # 显示检测到的版本号
    echo "检测到的镜像版本:"
    echo "- ljwx-mysql: $MYSQL_IMAGE"
    echo "- ljwx-redis: $REDIS_IMAGE"
    echo "- ljwx-boot: $BOOT_IMAGE"
    echo "- ljwx-bigscreen: $BIGSCREEN_IMAGE"
    echo "- ljwx-admin: $ADMIN_IMAGE"

    # 拉取最新镜像
    docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-mysql:$MYSQL_IMAGE || echo "警告: 无法拉取 ljwx-mysql 镜像，将使用本地镜像"
    docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-redis:$REDIS_IMAGE || echo "警告: 无法拉取 ljwx-redis 镜像，将使用本地镜像"
    docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-boot:$BOOT_IMAGE || echo "警告: 无法拉取 ljwx-boot 镜像，将使用本地镜像"
    docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-bigscreen:$BIGSCREEN_IMAGE || echo "警告: 无法拉取 ljwx-bigscreen 镜像，将使用本地镜像"
    docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/ljwx-admin:$ADMIN_IMAGE || echo "警告: 无法拉取 ljwx-admin 镜像，将使用本地镜像"
else
    echo ""
    echo "==================== 离线模式 ===================="
    echo "🔌 使用本地镜像部署，跳过镜像下载步骤"
    
    # 从docker-compose.yml动态读取版本号
    MYSQL_IMAGE=$(egrep '^ *image:.*ljwx-mysql:' docker-compose.yml | sed 's/.*ljwx-mysql:\([^ ]*\).*/\1/' | head -1)
    REDIS_IMAGE=$(egrep '^ *image:.*ljwx-redis:' docker-compose.yml | sed 's/.*ljwx-redis:\([^ ]*\).*/\1/' | head -1)
    BOOT_IMAGE=$(egrep '^ *image:.*ljwx-boot:' docker-compose.yml | sed 's/.*ljwx-boot:\([^ ]*\).*/\1/' | head -1)
    BIGSCREEN_IMAGE=$(egrep '^ *image:.*ljwx-bigscreen:' docker-compose.yml | sed 's/.*ljwx-bigscreen:\([^ ]*\).*/\1/' | head -1)
    ADMIN_IMAGE=$(egrep '^ *image:.*ljwx-admin:' docker-compose.yml | sed 's/.*ljwx-admin:\([^ ]*\).*/\1/' | head -1)

    echo "将使用本地镜像版本:"
    echo "- ljwx-mysql: $MYSQL_IMAGE"
    echo "- ljwx-redis: $REDIS_IMAGE"
    echo "- ljwx-boot: $BOOT_IMAGE"
    echo "- ljwx-bigscreen: $BIGSCREEN_IMAGE"
    echo "- ljwx-admin: $ADMIN_IMAGE"
    
    # 检查本地镜像是否存在
    echo ""
    echo "检查本地镜像可用性..."
    MISSING_IMAGES=""
    for image in "ljwx-mysql:$MYSQL_IMAGE" "ljwx-redis:$REDIS_IMAGE" "ljwx-boot:$BOOT_IMAGE" "ljwx-bigscreen:$BIGSCREEN_IMAGE" "ljwx-admin:$ADMIN_IMAGE"; do
        if docker images -q "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx/$image" | grep -q "."; then
            echo "✅ $image - 本地镜像可用"
        else
            echo "⚠️  $image - 本地镜像不存在"
            MISSING_IMAGES="$MISSING_IMAGES $image"
        fi
    done
    
    if [ -n "$MISSING_IMAGES" ]; then
        echo ""
        echo "❌ 警告: 以下镜像在本地不存在:"
        for img in $MISSING_IMAGES; do
            echo "   - $img"
        done
        echo ""
        read -p "是否继续离线部署? 缺失的镜像将导致服务启动失败 (y/N): " continue_offline
        if [ "$continue_offline" != "y" ] && [ "$continue_offline" != "Y" ]; then
            echo "部署已取消。请先拉取所需镜像或使用在线模式"
            exit 1
        fi
    fi
fi

echo ""
echo "==================== 开始部署 ===================="

# 生成动态docker-compose配置
echo "🔧 生成动态配置..."
if [ -f "generate-docker-compose.sh" ]; then
    chmod +x generate-docker-compose.sh
    ./generate-docker-compose.sh
    COMPOSE_FILE="docker-compose-generated.yml"
else
    echo "⚠️  警告: generate-docker-compose.sh 不存在，使用静态配置"
    COMPOSE_FILE="docker-compose.yml"
fi

# 停止现有服务但保留数据卷
echo "停止现有服务(保留命名卷)..."
docker-compose -f $COMPOSE_FILE down

# 清理可能存在的容器冲突
echo "清理容器冲突..."
docker rm -f ljwx-mysql ljwx-redis ljwx-boot ljwx-bigscreen ljwx-admin 2>/dev/null || true

# 确保目录权限正确
echo "🔧 设置目录权限..."
chmod -R 755 logs/ backup/ 2>/dev/null || true
echo "✅ 目录权限设置完成"

# 启动服务 - 根据模式选择不同的启动方式
if [ "$OFFLINE_MODE" = true ]; then
    echo "启动服务(离线模式-禁用镜像拉取)..."
    # 离线模式：强制使用本地镜像，禁止拉取
    docker-compose -f $COMPOSE_FILE --env-file $CONFIG_FILE up -d --pull never
else
    echo "启动服务(在线模式-允许镜像拉取)..."
    # 在线模式：允许拉取缺失的镜像
    docker-compose -f $COMPOSE_FILE --env-file $CONFIG_FILE up -d --pull missing
fi

# 等待服务启动
echo "等待服务启动..."
sleep 20

# 检查服务状态
echo ""
echo "==================== 服务状态检查 ===================="
docker-compose -f $COMPOSE_FILE ps

# 检查Docker命名卷状态
echo ""
echo "Docker命名卷状态:"
for volume in mysql_data redis_data ljwx_boot_data ljwx_bigscreen_data; do
    if docker volume ls -q | grep -q "client-deployment_${volume}"; then
        echo "  - client-deployment_$volume: ✅ 已创建"
    else
        echo "  - client-deployment_$volume: ❌ 未创建"
    fi
done

# 检查服务健康状态
echo ""
echo "检查服务健康状态..."

# 后端服务健康检查
echo "等待后端服务启动..."
i=1
while [ $i -le 60 ]; do
    if curl -s http://localhost:9998/actuator/health > /dev/null 2>&1; then
        echo "✅ 后端服务启动成功"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  后端服务启动超时，请检查日志: docker-compose logs ljwx-boot"
    fi
    sleep 2
    i=$((i + 1))
done

# 大屏服务健康检查
echo "等待大屏服务启动..."
i=1
while [ $i -le 60 ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ 大屏服务启动成功"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  大屏服务启动超时，请检查日志: docker-compose logs ljwx-bigscreen"
    fi
    sleep 2
    i=$((i + 1))
done

# 管理端服务健康检查
echo "等待管理端服务启动..."
i=1
while [ $i -le 60 ]; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "✅ 管理端服务启动成功"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  管理端服务启动超时，请检查日志: docker-compose logs ljwx-admin"
    fi
    sleep 2
    i=$((i + 1))
done

echo ""
echo "==================== 定制化配置后处理 ===================="

# 等待服务完全启动后再进行定制化配置
sleep 5

# 替换前端应用中的大屏URL
echo "🔄 更新前端大屏链接地址..."
if [ -f "replace-bigscreen-url.sh" ]; then
    ./replace-bigscreen-url.sh
    echo "✅ 大屏链接地址更新完成"
    
    # 清除浏览器缓存
    echo ""
    echo "🗑️  清除浏览器缓存..."
    if [ -f "clear-browser-cache.sh" ]; then
        ./clear-browser-cache.sh
        echo "✅ 浏览器缓存清除完成"
    else
        echo "⚠️  警告: clear-browser-cache.sh 脚本不存在"
    fi
else
    echo "⚠️  警告: replace-bigscreen-url.sh 脚本不存在"
fi

# 验证挂载配置
echo ""
echo "🔍 验证容器挂载配置..."
if [ -f "verify-mounts.sh" ]; then
    ./verify-mounts.sh
    echo "✅ 挂载配置验证完成"
else
    echo "⚠️  警告: verify-mounts.sh 脚本不存在，跳过挂载验证"
fi

# 显示访问地址
echo ""
echo "==================== 部署完成 ===================="
echo "🎉 客户定制化系统部署成功！"
echo ""
echo "服务访问地址:"
echo "- 管理端: http://localhost:8080"
echo "- 大屏端: http://localhost:8001"
echo "- 后端API: http://localhost:9998"
echo ""
echo "数据持久化:"
echo "- MySQL数据: client-deployment_mysql_data (命名卷)"
echo "- Redis数据: client-deployment_redis_data (命名卷)"
echo "- 后端数据: client-deployment_ljwx_boot_data (命名卷)"
echo "- 大屏数据: client-deployment_ljwx_bigscreen_data (命名卷)"
echo ""
echo "日志挂载 (宿主机目录):"
echo "- MySQL日志: ./logs/mysql/"
echo "- Redis日志: ./logs/redis/"
echo "- 后端日志: ./logs/ljwx-boot/"
echo "- 大屏日志: ./logs/ljwx-bigscreen/"
echo "- 管理端日志: ./logs/ljwx-admin/"
echo ""
echo "默认登录账号: admin / 123456"
echo ""
echo "管理命令:"
echo "- 日志查看工具: ./logs-viewer.sh (推荐)"
echo "- 查看容器日志: docker-compose logs -f [服务名]"
echo "- 查看文件日志: tail -f logs/[服务名]/*.log"
echo "- 停止服务: docker-compose down"
echo "- 重启服务: docker-compose restart [服务名]"
echo "- 数据备份: ./auto-backup.sh"
echo "- 数据恢复: ./restore-backup.sh"
echo "- 查看命名卷: docker volume ls"
echo ""
echo "备份恢复:"
echo "- 在线备份: ./auto-backup.sh (需要容器运行)"
echo "- 离线卷备份: 直接备份Docker卷到tar.gz"
echo "- 数据恢复: 通过备份恢复脚本或手动恢复"
echo ""
echo "部署模式说明:"
echo "- 在线模式: ./deploy-client.sh [配置文件]"
echo "- 离线模式: ./deploy-client.sh offline 或 ./deploy-client.sh [配置文件] offline"
echo ""
echo "如有问题，请联系技术支持" 
