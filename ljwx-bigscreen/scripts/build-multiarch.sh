#!/bin/bash

# LJWX BigScreen 多架构镜像构建脚本
# 版本: 1.3.1
# 支持架构: AMD64, ARM64

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/bigscreen"

# 默认配置
DEFAULT_REGISTRY="registry.cn-hangzhou.aliyuncs.com"
DEFAULT_NAMESPACE="ljwx-bigscreen"
DEFAULT_IMAGE_NAME="ljwx-bigscreen"
DEFAULT_VERSION="1.3.1"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

log_debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
LJWX BigScreen 多架构镜像构建脚本

用法: $0 [选项]

选项:
  -r, --registry REGISTRY     容器镜像仓库地址 (默认: $DEFAULT_REGISTRY)
  -n, --namespace NAMESPACE   命名空间 (默认: $DEFAULT_NAMESPACE)
  -i, --image IMAGE_NAME      镜像名称 (默认: $DEFAULT_IMAGE_NAME)
  -t, --tag TAG              镜像标签 (默认: $DEFAULT_VERSION)
  -p, --platforms PLATFORMS  目标平台，逗号分隔 (默认: linux/amd64,linux/arm64)
  -f, --dockerfile FILE      Dockerfile 文件 (默认: Dockerfile.optimized)
  -b, --build-only           仅构建，不推送
  -c, --clean                构建前清理
  -d, --debug                启用调试模式
  -h, --help                 显示此帮助信息

示例:
  # 构建并推送到阿里云
  $0 -t 1.3.1

  # 仅构建本地镜像
  $0 -t 1.3.1 --build-only

  # 构建特定平台
  $0 -t 1.3.1 -p linux/amd64

  # 使用自定义 Dockerfile
  $0 -t 1.3.1 -f Dockerfile.custom

环境变量:
  DOCKER_USERNAME    Docker 用户名 (用于认证)
  DOCKER_PASSWORD    Docker 密码
  DEBUG              启用调试模式 (true/false)

EOF
}

# 解析命令行参数
parse_args() {
    REGISTRY="$DEFAULT_REGISTRY"
    NAMESPACE="$DEFAULT_NAMESPACE"
    IMAGE_NAME="$DEFAULT_IMAGE_NAME"
    VERSION="$DEFAULT_VERSION"
    PLATFORMS="linux/amd64,linux/arm64"
    DOCKERFILE="Dockerfile.optimized"
    BUILD_ONLY=false
    CLEAN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -r|--registry)
                REGISTRY="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -i|--image)
                IMAGE_NAME="$2"
                shift 2
                ;;
            -t|--tag)
                VERSION="$2"
                shift 2
                ;;
            -p|--platforms)
                PLATFORMS="$2"
                shift 2
                ;;
            -f|--dockerfile)
                DOCKERFILE="$2"
                shift 2
                ;;
            -b|--build-only)
                BUILD_ONLY=true
                shift
                ;;
            -c|--clean)
                CLEAN=true
                shift
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 构建完整镜像名称
    FULL_IMAGE_NAME="$REGISTRY/$NAMESPACE/$IMAGE_NAME"
    
    log_debug "解析的参数:"
    log_debug "  Registry: $REGISTRY"
    log_debug "  Namespace: $NAMESPACE"
    log_debug "  Image: $IMAGE_NAME"
    log_debug "  Version: $VERSION"
    log_debug "  Platforms: $PLATFORMS"
    log_debug "  Dockerfile: $DOCKERFILE"
    log_debug "  Full Image: $FULL_IMAGE_NAME:$VERSION"
}

# 检查前置条件
check_prerequisites() {
    log_info "检查前置条件..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 Docker 版本
    DOCKER_VERSION=$(docker version --format '{{.Client.Version}}' 2>/dev/null)
    log_info "Docker 版本: $DOCKER_VERSION"
    
    # 检查 Docker Buildx
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx 未安装或不可用"
        log_info "请安装 Docker Buildx 或升级到支持的 Docker 版本"
        exit 1
    fi
    
    # 检查构建上下文
    if [ ! -d "$BUILD_DIR" ]; then
        log_error "构建目录不存在: $BUILD_DIR"
        exit 1
    fi
    
    # 检查 Dockerfile
    if [ ! -f "$BUILD_DIR/$DOCKERFILE" ]; then
        log_error "Dockerfile 不存在: $BUILD_DIR/$DOCKERFILE"
        exit 1
    fi
    
    # 检查必要文件
    if [ ! -f "$BUILD_DIR/requirements-docker.txt" ]; then
        log_error "依赖文件不存在: $BUILD_DIR/requirements-docker.txt"
        exit 1
    fi
    
    if [ ! -f "$BUILD_DIR/run.py" ]; then
        log_error "应用入口文件不存在: $BUILD_DIR/run.py"
        exit 1
    fi
    
    log_info "前置条件检查通过 ✓"
}

# 设置 Docker Buildx
setup_buildx() {
    log_info "设置 Docker Buildx..."
    
    # 创建或使用现有的 builder
    BUILDER_NAME="ljwx-multiarch-builder"
    
    if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
        log_info "创建新的 builder: $BUILDER_NAME"
        docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
    else
        log_info "使用现有的 builder: $BUILDER_NAME"
        docker buildx use "$BUILDER_NAME"
    fi
    
    # 启动 builder
    docker buildx inspect --bootstrap
    
    log_info "Buildx 设置完成 ✓"
}

# 清理操作
cleanup() {
    if [ "$CLEAN" = "true" ]; then
        log_info "执行清理操作..."
        
        # 清理 Docker 缓存
        docker buildx prune -f
        
        # 清理悬空镜像
        docker image prune -f
        
        log_info "清理完成 ✓"
    fi
}

# Docker 登录
docker_login() {
    if [ "$BUILD_ONLY" = "false" ]; then
        log_info "登录容器镜像仓库..."
        
        if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
            echo "$DOCKER_PASSWORD" | docker login "$REGISTRY" --username "$DOCKER_USERNAME" --password-stdin
            log_info "登录成功 ✓"
        else
            log_warn "未设置 DOCKER_USERNAME 或 DOCKER_PASSWORD 环境变量"
            log_warn "如果仓库需要认证，请手动登录"
        fi
    fi
}

# 构建镜像
build_image() {
    log_info "开始构建多架构镜像..."
    log_info "  镜像: $FULL_IMAGE_NAME:$VERSION"
    log_info "  平台: $PLATFORMS"
    log_info "  Dockerfile: $DOCKERFILE"
    
    cd "$BUILD_DIR"
    
    # 构建参数
    BUILD_ARGS=(
        "--file" "$DOCKERFILE"
        "--platform" "$PLATFORMS"
        "--tag" "$FULL_IMAGE_NAME:$VERSION"
        "--tag" "$FULL_IMAGE_NAME:latest"
        "--build-arg" "VERSION=$VERSION"
        "--build-arg" "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        "--build-arg" "VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
        "--cache-from" "type=gha"
        "--cache-to" "type=gha,mode=max"
        "--metadata-file" "/tmp/metadata.json"
    )
    
    # 如果不是仅构建模式，添加推送参数
    if [ "$BUILD_ONLY" = "false" ]; then
        BUILD_ARGS+=("--push")
        log_info "构建完成后将推送到仓库"
    else
        BUILD_ARGS+=("--load")
        log_info "仅构建本地镜像，不推送"
    fi
    
    # 执行构建
    log_info "执行 Docker Buildx 构建..."
    if ! docker buildx build "${BUILD_ARGS[@]}" .; then
        log_error "镜像构建失败"
        exit 1
    fi
    
    log_info "镜像构建成功 ✓"
    
    # 显示构建信息
    if [ -f "/tmp/metadata.json" ]; then
        log_info "构建元数据:"
        if command -v jq &> /dev/null; then
            jq . /tmp/metadata.json
        else
            cat /tmp/metadata.json
        fi
    fi
}

# 验证镜像
verify_image() {
    log_info "验证镜像..."
    
    if [ "$BUILD_ONLY" = "false" ]; then
        # 验证远程镜像
        log_info "检查远程镜像清单..."
        if docker buildx imagetools inspect "$FULL_IMAGE_NAME:$VERSION" > /dev/null 2>&1; then
            log_info "远程镜像验证成功 ✓"
            
            # 显示镜像信息
            log_info "镜像信息:"
            docker buildx imagetools inspect "$FULL_IMAGE_NAME:$VERSION"
        else
            log_error "远程镜像验证失败"
            exit 1
        fi
    else
        # 验证本地镜像
        log_info "检查本地镜像..."
        if docker images | grep -q "$IMAGE_NAME.*$VERSION"; then
            log_info "本地镜像验证成功 ✓"
            
            # 显示本地镜像信息
            docker images | grep "$IMAGE_NAME"
        else
            log_error "本地镜像验证失败"
            exit 1
        fi
    fi
}

# 显示构建摘要
show_summary() {
    log_info "构建摘要:"
    log_info "  镜像名称: $FULL_IMAGE_NAME:$VERSION"
    log_info "  支持平台: $PLATFORMS"
    log_info "  构建模式: $([ "$BUILD_ONLY" = "true" ] && echo "仅构建" || echo "构建并推送")"
    log_info "  Dockerfile: $DOCKERFILE"
    log_info "  构建时间: $(date)"
    
    if [ "$BUILD_ONLY" = "false" ]; then
        log_info ""
        log_info "镜像已推送到: $REGISTRY/$NAMESPACE/$IMAGE_NAME"
        log_info "拉取命令:"
        log_info "  docker pull $FULL_IMAGE_NAME:$VERSION"
        log_info "  docker pull $FULL_IMAGE_NAME:latest"
    else
        log_info ""
        log_info "本地镜像标签:"
        log_info "  $FULL_IMAGE_NAME:$VERSION"
        log_info "  $FULL_IMAGE_NAME:latest"
    fi
}

# 主函数
main() {
    log_info "LJWX BigScreen 多架构镜像构建工具 v1.3.1"
    log_info "=============================================="
    
    # 解析参数
    parse_args "$@"
    
    # 检查前置条件
    check_prerequisites
    
    # 清理操作
    cleanup
    
    # 设置 Buildx
    setup_buildx
    
    # Docker 登录
    docker_login
    
    # 构建镜像
    build_image
    
    # 验证镜像
    verify_image
    
    # 显示摘要
    show_summary
    
    log_info "🎉 多架构镜像构建完成！"
}

# 捕获中断信号
trap 'log_error "构建被中断"; exit 1' INT TERM

# 执行主函数
main "$@"