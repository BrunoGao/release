#!/bin/bash
# 多架构分别构建脚本 v1.0

set -e

echo "🏗️ 多架构分别构建解决方案"

# 加载版本配置
if [ -f "monitoring-versions.env" ]; then
    source monitoring-versions.env
    echo "📋 已加载版本配置文件"
else
    echo "⚠️ 未找到版本配置文件，使用默认配置"
    LJWX_VERSION="1.2.16"
    REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx"
fi

# 登录阿里云
echo "🔐 登录阿里云Docker镜像仓库..."
echo "admin123" | docker login --username brunogao --password-stdin crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com
if [ $? -eq 0 ]; then
    echo "✅ 阿里云登录成功"
else
    echo "❌ 阿里云登录失败，请检查凭据"
    exit 1
fi

# 构建函数
build_single_arch() {
    local arch=$1
    local tag_suffix=$2
    local image_name="ljwx-boot"
    local tag="$REGISTRY/$image_name:$LJWX_VERSION-$tag_suffix"
    
    echo "🔨 构建 $arch 架构镜像..."
    
    # 设置平台
    export DOCKER_DEFAULT_PLATFORM="linux/$arch"
    
    # 构建单架构镜像
    docker build \
        --platform linux/$arch \
        --progress=plain \
        -t $tag \
        . -f ljwx-boot/ljwx-boot-admin/Dockerfile.prod
    
    if [ $? -eq 0 ]; then
        echo "✅ $arch 架构构建成功: $tag"
        # 推送到镜像仓库
        docker push $tag
        echo "✅ $arch 架构推送成功"
        return 0
    else
        echo "❌ $arch 架构构建失败"
        return 1
    fi
}

# 创建多架构manifest
create_multiarch_manifest() {
    local image_name="ljwx-boot"
    local manifest_tag="$REGISTRY/$image_name:$LJWX_VERSION"
    local amd64_tag="$REGISTRY/$image_name:$LJWX_VERSION-amd64"
    local arm64_tag="$REGISTRY/$image_name:$LJWX_VERSION-arm64"
    
    echo "📦 创建多架构 manifest..."
    
    # 创建 manifest
    docker manifest create $manifest_tag $amd64_tag $arm64_tag
    
    # 设置架构信息
    docker manifest annotate $manifest_tag $amd64_tag --arch amd64
    docker manifest annotate $manifest_tag $arm64_tag --arch arm64
    
    # 推送 manifest
    docker manifest push $manifest_tag
    
    # 创建 latest 标签的 manifest
    local latest_tag="$REGISTRY/$image_name:latest"
    docker manifest create $latest_tag $amd64_tag $arm64_tag
    docker manifest annotate $latest_tag $amd64_tag --arch amd64
    docker manifest annotate $latest_tag $arm64_tag --arch arm64
    docker manifest push $latest_tag
    
    echo "✅ 多架构 manifest 创建完成"
    echo "🏷️ 镜像标签: $manifest_tag, $latest_tag"
}

# 主程序
main() {
    echo "🚀 开始分别构建多架构镜像..."
    
    # 构建 AMD64 架构
    echo ""
    echo "=== 构建 AMD64 架构 ==="
    if ! build_single_arch "amd64" "amd64"; then
        echo "❌ AMD64 架构构建失败"
        exit 1
    fi
    
    # 构建 ARM64 架构  
    echo ""
    echo "=== 构建 ARM64 架构 ==="
    if ! build_single_arch "arm64" "arm64"; then
        echo "❌ ARM64 架构构建失败"
        exit 1
    fi
    
    # 创建多架构 manifest
    echo ""
    echo "=== 创建多架构 Manifest ==="
    create_multiarch_manifest
    
    echo ""
    echo "🎉 多架构构建完成！"
    echo ""
    echo "📊 构建摘要:"
    echo "   AMD64: $REGISTRY/ljwx-boot:$LJWX_VERSION-amd64"
    echo "   ARM64: $REGISTRY/ljwx-boot:$LJWX_VERSION-arm64"  
    echo "   多架构: $REGISTRY/ljwx-boot:$LJWX_VERSION"
    echo "   多架构: $REGISTRY/ljwx-boot:latest"
    echo ""
    echo "💡 使用方式:"
    echo "   docker pull $REGISTRY/ljwx-boot:$LJWX_VERSION"
    echo "   Docker会自动选择适合当前架构的镜像"
}

# 执行主程序
main "$@"