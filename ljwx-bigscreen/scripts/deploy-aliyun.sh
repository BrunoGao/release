#!/bin/bash

# LJWX BigScreen 多架构镜像一键构建推送脚本
# 版本: 1.3.2
# 支持架构: AMD64, ARM64

set -e

# 配置变量
REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com"
NAMESPACE="ljwx"
IMAGE_NAME="ljwx-bigscreen"
VERSION="1.3.2"
FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}"

# 阿里云登录信息
ALIYUN_USERNAME="brunogao"
ALIYUN_PASSWORD="admin123"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker Buildx 是否可用
check_buildx() {
    echo_info "检查 Docker Buildx 支持..."
    if ! docker buildx version > /dev/null 2>&1; then
        echo_error "Docker Buildx 不可用，请升级 Docker 或启用 Buildx"
        exit 1
    fi
    echo_success "Docker Buildx 已就绪"
}

# 设置 Buildx builder
setup_builder() {
    echo_info "设置多架构构建器..."
    
    # 创建新的 builder 实例（如果不存在）
    if ! docker buildx inspect ljwx-multiarch-builder > /dev/null 2>&1; then
        docker buildx create --name ljwx-multiarch-builder --driver docker-container --use
        echo_success "创建多架构构建器成功"
    else
        docker buildx use ljwx-multiarch-builder
        echo_success "使用现有多架构构建器"
    fi
    
    # 启动构建器
    docker buildx inspect --bootstrap
}

# 登录阿里云容器镜像服务
login_registry() {
    echo_info "登录阿里云容器镜像服务..."
    echo_info "Registry: ${REGISTRY}"
    echo_info "Username: ${ALIYUN_USERNAME}"
    
    echo "${ALIYUN_PASSWORD}" | docker login ${REGISTRY} -u ${ALIYUN_USERNAME} --password-stdin
    echo_success "登录成功"
}

# 构建并推送多架构镜像
build_and_push() {
    echo_info "开始构建多架构镜像..."
    echo_info "镜像名称: ${FULL_IMAGE_NAME}"
    echo_info "版本: ${VERSION}"
    echo_info "支持架构: linux/amd64, linux/arm64"
    
    cd bigscreen
    
    # 检查必要文件
    if [ ! -f "Dockerfile.multiarch" ]; then
        echo_error "Dockerfile.multiarch 文件不存在"
        exit 1
    fi
    
    if [ ! -f "requirements-docker.txt" ]; then
        echo_error "requirements-docker.txt 文件不存在"
        exit 1
    fi
    
    # 构建并推送
    echo_info "执行构建命令..."
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file Dockerfile.multiarch \
        --tag ${FULL_IMAGE_NAME}:${VERSION} \
        --tag ${FULL_IMAGE_NAME}:latest \
        --build-arg VERSION=${VERSION} \
        --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
        --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
        --push \
        .
        
    cd ..
    echo_success "多架构镜像构建并推送成功！"
}

# 验证镜像
verify_images() {
    echo_info "验证多架构镜像..."
    
    # 检查镜像 manifest
    if docker buildx imagetools inspect ${FULL_IMAGE_NAME}:${VERSION}; then
        echo_success "镜像验证成功"
    else
        echo_error "镜像验证失败"
        exit 1
    fi
}

# 显示构建结果
show_results() {
    echo ""
    echo "=========================================="
    echo_success "🎉 构建完成！"
    echo "=========================================="
    echo_info "镜像详情："
    echo_info "  Registry: ${REGISTRY}"
    echo_info "  Namespace: ${NAMESPACE}"
    echo_info "  Image: ${IMAGE_NAME}"
    echo_info "  Version: ${VERSION}"
    echo_info "  Architecture: AMD64 + ARM64"
    echo ""
    echo_info "镜像地址："
    echo_info "  ${FULL_IMAGE_NAME}:${VERSION}"
    echo_info "  ${FULL_IMAGE_NAME}:latest"
    echo ""
    echo_info "拉取命令："
    echo_info "  docker pull ${FULL_IMAGE_NAME}:${VERSION}"
    echo_info "  docker pull ${FULL_IMAGE_NAME}:latest"
    echo ""
    echo_info "运行命令："
    echo_info "  docker run -d -p 5001:5001 ${FULL_IMAGE_NAME}:${VERSION}"
    echo ""
}

# 主函数
main() {
    echo_info "LJWX BigScreen v${VERSION} 多架构镜像构建"
    echo "=========================================="
    
    check_buildx
    setup_builder
    login_registry
    build_and_push
    verify_images
    show_results
}

# 错误处理
trap 'echo_error "构建过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"