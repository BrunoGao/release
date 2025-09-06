#!/bin/bash
# Created Time:    2025-06-09 07:43:24
# Modified Time:   2025-06-26 20:39:46
#!/bin/bash
# 灵境万象系统 - 本地多架构构建脚本 v1.2.6

set -e

echo "🏗️ 灵境万象系统 - 本地多架构构建 v1.2.6"

# 加载版本配置
if [ -f "monitoring-versions.env" ]; then
    source monitoring-versions.env
    echo "📋 已加载版本配置文件"
else
    echo "⚠️ 未找到版本配置文件，使用默认配置"
    # 默认配置
    LJWX_VERSION="1.2.16"
    LJWX_GRAFANA_VERSION="1.2.6"
    LJWX_PROMETHEUS_VERSION="1.2.6"
    LJWX_LOKI_VERSION="1.2.6"
    LJWX_PROMTAIL_VERSION="1.2.6"
    LJWX_ALERTMANAGER_VERSION="1.2.6"
    REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"  # 阿里云镜像仓库
    PLATFORMS="linux/amd64,linux/arm64"  # 多架构构建
fi

# 构建器配置
BUILDER_NAME="multiarch-builder"

# 多架构构建模式配置  
LOCAL_BUILD=${LOCAL_BUILD:-false}  # 默认多架构构建
PUSH_TO_REGISTRY=${PUSH_TO_REGISTRY:-true}  # 默认推送到阿里云

# 设置阿里云Docker镜像加速
setup_aliyun_mirror() {
    echo "🚀 配置Docker镜像加速（包含xuanyuan.run镜像源）..."
    
    # 配置Docker daemon.json以使用阿里云镜像加速器
    local daemon_config='
    {
        "registry-mirrors": [
            "https://syxpn3chjq4bgj.xuanyuan.run",
            "https://mirror.baidubce.com",
            "https://dockerhub.azk8s.cn",
            "https://registry.cn-hangzhou.aliyuncs.com",
            "https://docker.mirrors.ustc.edu.cn"
        ],
        "insecure-registries": [
            "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com",
            "syxpn3chjq4bgj.xuanyuan.run"
        ]
    }'
    
    # 在Dockerfile中使用阿里云源镜像
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    
    echo "✅ Docker镜像加速配置完成，优先使用xuanyuan.run镜像源"
}

# 生成数据库升级脚本 - 已移除，请使用专门的数据库升级脚本

# 数据导出功能已移除 - 请使用专门的数据导出脚本 export-data.sh

# 自动登录阿里云镜像仓库
login_aliyun() {
    if [ "$PUSH_TO_REGISTRY" = "true" ] && [[ "$REGISTRY" == *"aliyuncs.com"* ]]; then
        echo "🔐 登录阿里云Docker镜像仓库..."
        echo "admin123" | docker login --username brunogao --password-stdin crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com
        if [ $? -eq 0 ]; then
            echo "✅ 阿里云登录成功"
        else
            echo "❌ 阿里云登录失败，请检查凭据"
            exit 1
        fi
    fi
}

# 检查参数
if [ $# -eq 0 ]; then
    echo "📋 使用方法:"
    echo "   $0 all                    # 构建所有镜像(应用+监控)"
    echo "   $0 apps                   # 构建应用镜像"
    echo "   $0 monitoring             # 构建监控镜像"
    echo ""
    echo "🔧 应用组件:"
    echo "   $0 mysql                  # 构建MySQL镜像"
    echo "   $0 redis                  # 构建Redis镜像"
    echo "   $0 boot                   # 构建Boot镜像"
    echo "   $0 bigscreen              # 构建Bigscreen镜像"
    echo "   $0 admin                  # 构建Admin镜像"
    echo ""
    echo "📊 监控组件:"
    echo "   $0 grafana                # 构建定制化Grafana"
    echo "   $0 prometheus             # 构建定制化Prometheus"
    echo "   $0 loki                   # 构建定制化Loki"
    echo "   $0 promtail               # 构建定制化Promtail"
    echo "   $0 alertmanager           # 构建定制化AlertManager"
    echo ""
    echo "🚀 缓存管理:"
    echo "   $0 cache-pull             # 预拉取所有基础镜像到本地缓存"
    echo "   $0 cache-clean            # 清理构建缓存"
    echo "   $0 cache-prune            # 清理未使用的镜像和缓存"
    echo ""
    echo "🎯 构建模式:"
    echo "   LOCAL_BUILD=false         # 多架构构建(默认)"
    echo "   PUSH_TO_REGISTRY=true     # 推送到阿里云(默认)"
    echo ""
    echo "📊 数据管理:"
    echo "   ./export-data.sh          # 导出MySQL数据到data.sql"
    echo "   database/version-workflow.sh # 数据库版本升级管理"
    echo ""
    echo "⚠️  注意事项:"
    echo "   - MySQL镜像构建需要data.sql文件，请先运行数据导出"
    echo "   - 数据库升级请使用专门的版本管理工具，不在构建中处理"
    echo ""
    echo "💡 当前架构: $PLATFORMS"
    echo "📊 当前版本: 应用 $LJWX_VERSION, 监控 $LJWX_GRAFANA_VERSION"
    echo "🏷️  镜像前缀: $REGISTRY"
    exit 1
fi

# 初始化多架构构建器(仅在需要时)
init_buildx() {
    if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
        echo "🔧 使用本地Docker构建..."
        return 0
    fi
    
    echo "🔧 初始化多架构构建器..."
    if ! docker buildx inspect $BUILDER_NAME >/dev/null 2>&1; then
        docker buildx create --name $BUILDER_NAME --use
    else
        docker buildx use $BUILDER_NAME
    fi
    docker buildx inspect --bootstrap
}

# 构建应用镜像函数
build_app_image() {
    local image=$1
    local image_name="ljwx-$image"
    local tag="$REGISTRY/$image_name:$LJWX_VERSION"
    local latest_tag="$REGISTRY/$image_name:latest"
    
    echo "🔨 构建应用镜像 $image_name (架构: $PLATFORMS)..."
    
    # 构建参数
    local build_args=""
    if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
        # 本地构建
        build_args="build"
    else
        # 多架构构建
        build_args="buildx build --platform $PLATFORMS"
        if [ "$PUSH_TO_REGISTRY" = "true" ]; then
            build_args="$build_args --push"
        else
            build_args="$build_args --load"
        fi
    fi
    
    case $image in
        "mysql")
            echo "🗄️ 构建MySQL镜像..."
            # 检查是否存在data.sql文件，如果没有则自动导出数据
            if [ ! -f "data.sql" ]; then
                echo "⚠️ 未找到data.sql文件，正在自动导出数据..."
                if [ -f "./export-data.sh" ]; then
                    echo "🚀 执行自动数据导出: ./export-data.sh"
                    ./export-data.sh
                    if [ $? -eq 0 ] && [ -f "data.sql" ]; then
                        echo "✅ 数据导出成功，将构建包含数据的MySQL镜像"
                    else
                        echo "❌ 数据导出失败，将构建不包含数据的MySQL镜像"
                        echo "💡 请检查数据库连接配置 (默认: 127.0.0.1:3306, test数据库, root/123456)"
                    fi
                else
                    echo "❌ 未找到export-data.sh脚本，将构建不包含数据的MySQL镜像"
                    echo "💡 请手动创建export-data.sh脚本或导出数据到data.sql"
                fi
            else
                echo "✅ 找到data.sql文件，将构建包含数据的MySQL镜像"
            fi
            if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
                docker build --no-cache -t $tag -t $latest_tag . -f docker/mysql/Dockerfile
            else
                docker $build_args --no-cache -t $tag -t $latest_tag . -f docker/mysql/Dockerfile
            fi
            ;;
        "redis")
            if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
                docker build -t $tag -t $latest_tag . -f docker/redis/Dockerfile
            else
                docker $build_args -t $tag -t $latest_tag . -f docker/redis/Dockerfile
            fi
            ;;
        "boot")
            echo "🔨 使用多阶段容器构建 Spring Boot JAR 包..."
            echo "💡 在容器内构建确保跨平台兼容性，使用阿里云Maven镜像加速"
            if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
                docker build --build-arg MAVEN_OPTS="-XX:+UseG1GC -Xmx1g" -t $tag -t $latest_tag . -f ljwx-boot/ljwx-boot-admin/Dockerfile.prod
            else
                docker $build_args --build-arg MAVEN_OPTS="-XX:+UseG1GC -Xmx1g" -t $tag -t $latest_tag . -f ljwx-boot/ljwx-boot-admin/Dockerfile.prod
            fi
            ;;
        "bigscreen")
            echo "🔨 使用多阶段容器构建 Python FastAPI 应用..."
            echo "💡 在容器内构建确保跨平台兼容性，使用阿里云Python镜像和pip源加速"
            if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
                docker build --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t $tag -t $latest_tag ljwx-bigscreen/bigscreen/ -f ljwx-bigscreen/bigscreen/Dockerfile.prod
            else
                docker $build_args --build-arg PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ -t $tag -t $latest_tag ljwx-bigscreen/bigscreen/ -f ljwx-bigscreen/bigscreen/Dockerfile.prod
            fi
            ;;
        "admin")
            echo "🔨 使用多阶段容器构建前端静态资源镜像..."
            echo "💡 在容器内构建确保跨平台兼容性，使用阿里云npm镜像加速"
            if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
                docker build -t $tag -t $latest_tag ljwx-admin/ -f ljwx-admin/Dockerfile.prod
            else
                docker $build_args -t $tag -t $latest_tag ljwx-admin/ -f ljwx-admin/Dockerfile.prod
            fi
            ;;
        *)
            echo "❌ 未知应用镜像: $image"
            return 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        echo "✅ $image_name 应用镜像构建成功"
        echo "🏷️  镜像标签: $tag, $latest_tag"
    else
        echo "❌ $image_name 应用镜像构建失败"
        return 1
    fi
}

# 构建监控镜像函数
build_monitoring_image() {
    local image=$1
    local image_name="ljwx-$image"
    
    # 根据组件设置版本
    case $image in
        "grafana")
            local version=$LJWX_GRAFANA_VERSION
            ;;
        "prometheus")
            local version=$LJWX_PROMETHEUS_VERSION
            ;;
        "loki")
            local version=$LJWX_LOKI_VERSION
            ;;
        "promtail")
            local version=$LJWX_PROMTAIL_VERSION
            ;;
        "alertmanager")
            local version=$LJWX_ALERTMANAGER_VERSION
            ;;
        *)
            echo "❌ 未知监控镜像: $image"
            return 1
            ;;
    esac
    
    local tag="$REGISTRY/$image_name:$version"
    local latest_tag="$REGISTRY/$image_name:latest"
    
    echo "🔨 构建监控镜像 $image_name:$version (架构: $PLATFORMS)..."
    
    # 构建镜像
    if [ "$LOCAL_BUILD" = "true" ] && [ "$PLATFORMS" = "linux/amd64" ]; then
        docker build \
            --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
            --build-arg VERSION="$version" \
            -t $tag -t $latest_tag \
            . -f docker/$image/Dockerfile
    else
        docker buildx build --platform $PLATFORMS \
            --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
            --build-arg VERSION="$version" \
            -t $tag -t $latest_tag \
            $([ "$PUSH_TO_REGISTRY" = "true" ] && echo "--push" || echo "--load") \
            . -f docker/$image/Dockerfile
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ $image_name:$version 监控镜像构建成功"
        echo "🏷️  镜像标签: $tag, $latest_tag"
    else
        echo "❌ $image_name:$version 监控镜像构建失败"
        return 1
    fi
}

# 构建所有应用镜像
build_all_apps() {
    echo "🚀 开始构建所有应用镜像..."
    
    local app_images=("mysql" "redis" "boot" "bigscreen" "admin")
    
    for image in "${app_images[@]}"; do
        build_app_image "$image"
        echo ""
    done
}

# 构建所有监控镜像
build_all_monitoring() {
    echo "📊 开始构建所有监控镜像..."
    
    local monitoring_images=("grafana" "prometheus" "loki" "promtail" "alertmanager")
    
    for image in "${monitoring_images[@]}"; do
        build_monitoring_image "$image"
        echo ""
    done
}

# 构建所有镜像
build_all() {
    echo "🏗️ 开始构建所有镜像(应用+监控)..."
    echo ""
    
    # 先构建应用镜像
    build_all_apps
    
    echo "🔄 应用镜像构建完成，开始构建监控镜像..."
    echo ""
    
    # 再构建监控镜像
    build_all_monitoring
}

# 缓存管理函数
cache_pull() {
    echo "🚀 预拉取所有基础镜像到本地缓存..."
    
    local base_images=(
        # Admin 前端镜像
        "node:18-alpine"
        "nginx:alpine"
        
        # Boot 后端镜像
        "eclipse-temurin:21-jdk-alpine"
        "eclipse-temurin:21-jre-alpine"
        
        # Bigscreen Python镜像
        "python:3.12-slim"
        
        # 数据库和缓存镜像
        "mysql:8.0"
        "redis:7-alpine"
        
        # 监控组件基础镜像
        "grafana/grafana:9.5.0"
        "prom/prometheus:v2.40.0"
        "grafana/loki:2.9.0" 
        "grafana/promtail:2.9.0"
        "prom/alertmanager:latest"
    )
    
    for image in "${base_images[@]}"; do
        echo "📥 拉取基础镜像: $image"
        if timeout 120 docker pull "$image"; then
            echo "✅ $image 拉取成功"
        else
            echo "⚠️  $image 拉取超时或失败，跳过"
        fi
        echo ""
    done
    
    echo "✅ 基础镜像缓存完成!"
}

cache_clean() {
    echo "🧹 清理构建缓存..."
    docker builder prune -f
    echo "✅ 构建缓存清理完成!"
}

cache_prune() {
    echo "🗑️  清理未使用的镜像和缓存..."
    docker system prune -f
    docker image prune -f
    docker builder prune -f
    echo "✅ 系统清理完成!"
}

# 显示构建总结
show_summary() {
    echo ""
    echo "🎉 本地构建完成！"
    echo ""
    echo "📊 构建摘要:"
    echo "   应用版本: $LJWX_VERSION"
    echo "   监控版本: $LJWX_GRAFANA_VERSION"
    echo "   构建架构: $PLATFORMS"
    echo "   镜像前缀: $REGISTRY"
    echo "   构建模式: $([ "$LOCAL_BUILD" = "true" ] && echo "本地构建" || echo "多架构构建")"
    echo ""
    echo "🔍 查看本地镜像:"
    echo "   docker images | grep $REGISTRY"
    echo ""
    
    if [[ " $@ " =~ " all " ]] || [[ " $@ " =~ " apps " ]]; then
        echo "   # 应用镜像"
        echo "   docker images $REGISTRY/ljwx-mysql"
        echo "   docker images $REGISTRY/ljwx-redis"
        echo "   docker images $REGISTRY/ljwx-boot"
        echo "   docker images $REGISTRY/ljwx-bigscreen"
        echo "   docker images $REGISTRY/ljwx-admin"
    fi
    
    if [[ " $@ " =~ " all " ]] || [[ " $@ " =~ " monitoring " ]]; then
        echo "   # 监控镜像"
        echo "   docker images $REGISTRY/ljwx-grafana"
        echo "   docker images $REGISTRY/ljwx-prometheus"
        echo "   docker images $REGISTRY/ljwx-loki"
        echo "   docker images $REGISTRY/ljwx-promtail"
        echo "   docker images $REGISTRY/ljwx-alertmanager"
    fi
    
    echo ""
    echo "🚀 推送到阿里云的镜像:"
    if [[ " $@ " =~ " all " ]] || [[ " $@ " =~ " apps " ]]; then
        echo "   $REGISTRY/ljwx-mysql:$LJWX_VERSION"
        echo "   $REGISTRY/ljwx-redis:$LJWX_VERSION"
        echo "   $REGISTRY/ljwx-boot:$LJWX_VERSION"
        echo "   $REGISTRY/ljwx-bigscreen:$LJWX_VERSION"
        echo "   $REGISTRY/ljwx-admin:$LJWX_VERSION"
    fi
    echo ""
    echo "   客户可使用命令拉取: docker pull $REGISTRY/ljwx-xxx:$LJWX_VERSION"
}

# 主程序
main() {
    # 设置阿里云镜像加速
    setup_aliyun_mirror
    
    # 登录阿里云(如果需要推送)
    login_aliyun
    
    # 初始化构建器
    init_buildx
    
    case "$1" in
        "all")
            build_all
            ;;
        "apps")
            build_all_apps
            ;;
        "monitoring")
            build_all_monitoring
            ;;
        "cache-pull")
            cache_pull
            return 0
            ;;
        "cache-clean")
            cache_clean
            return 0
            ;;
        "cache-prune")
            cache_prune
            return 0
            ;;
        "mysql"|"redis"|"boot"|"bigscreen"|"admin")
            for image in "$@"; do
                build_app_image "$image"
                echo ""
            done
            ;;
        "grafana"|"prometheus"|"loki"|"promtail"|"alertmanager")
            for image in "$@"; do
                build_monitoring_image "$image"
                echo ""
            done
            ;;
        *)
            # 混合构建：检查每个参数类型
            for image in "$@"; do
                case $image in
                    "mysql"|"redis"|"boot"|"bigscreen"|"admin")
                        build_app_image "$image"
                        ;;
                    "grafana"|"prometheus"|"loki"|"promtail"|"alertmanager")
                        build_monitoring_image "$image"
                        ;;
                    *)
                        echo "❌ 未知镜像类型: $image"
                        ;;
                esac
                echo ""
            done
            ;;
    esac
    
    # 显示构建总结
    show_summary "$@"
}

# 执行主程序
main "$@"
