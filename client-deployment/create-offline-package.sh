#!/bin/bash
# LJWX离线部署包创建脚本 - 统一配置管理

set -e #出错即停

# 全局配置 - 统一管理所有变量
REGISTRY="crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com" #镜像仓库地址
VERSION="1.2.14" #系统版本
REDIS_VERSION="1.1.7" #Redis版本
OFFLINE_DIR="ljwx-offline-$(date +%Y%m%d)" #离线包目录
PACKAGE_NAME="ljwx-offline-deployment-$(date +%Y%m%d).tar.gz" #最终包名

# 颜色配置 - 终端输出美化
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m' #颜色代码

log() { echo -e "${GREEN}✅ $1${NC}"; } #成功日志
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; } #警告日志
error() { echo -e "${RED}❌ $1${NC}"; exit 1; } #错误日志
info() { echo -e "${BLUE}ℹ️  $1${NC}"; } #信息日志

# 环境检查
check_env() {
    info "检查环境依赖..."
    command -v docker >/dev/null || error "Docker未安装"
    command -v tar >/dev/null || error "tar命令不可用"
    command -v gzip >/dev/null || error "gzip命令不可用"
    log "环境检查通过"
}

# 创建工作目录
setup_workspace() {
    info "创建工作目录: $OFFLINE_DIR"
    [ -d "$OFFLINE_DIR" ] && rm -rf "$OFFLINE_DIR" #清理旧目录
    mkdir -p "$OFFLINE_DIR"/{images,deployment,scripts,docs}
    log "工作目录创建完成"
}

# 下载Docker镜像
download_images() {
    info "开始下载Docker镜像..."
    
    # 镜像列表 - 统一管理
    local images=(
        "$REGISTRY/ljwx/ljwx-mysql:$VERSION"
        "$REGISTRY/ljwx/ljwx-redis:$REDIS_VERSION"
        "$REGISTRY/ljwx/ljwx-boot:$VERSION"
        "$REGISTRY/ljwx/ljwx-bigscreen:$VERSION"
        "$REGISTRY/ljwx/ljwx-admin:$VERSION"
    )
    
    cd "$OFFLINE_DIR/images"
    for img in "${images[@]}"; do
        info "下载镜像: $img"
        docker pull "$img" || error "镜像下载失败: $img"
    done
    
    # 导出镜像
    info "导出镜像到tar文件..."
    docker save "${images[@]}" -o ljwx-images-${VERSION}.tar
    gzip ljwx-images-${VERSION}.tar
    
    log "镜像下载完成 ($(du -h ljwx-images-${VERSION}.tar.gz | cut -f1))"
}

# 复制部署文件
copy_deployment_files() {
    info "复制部署文件..."
    cd "../.."
    
    # 核心文件列表 - 统一管理
    local files=(
        "docker-compose.yml"
        "deploy-client.sh"
        "reset-database.sh"
        "backup-restore-manager.sh"
        "wait-for-it.sh"
        "custom-config.env"
        "customer-example.env"
        "custom-config.py"
        "custom-admin-config.js"
        "client-data.sql"
        "validate-centos-compatibility.sh"
        "CENTOS_COMPATIBILITY_FIXES.md"
    )
    
    for file in "${files[@]}"; do
        [ -f "$file" ] && cp "$file" "$OFFLINE_DIR/deployment/" || warn "文件不存在: $file"
    done
    
    # 复制目录
    [ -d "custom-assets" ] && cp -r custom-assets "$OFFLINE_DIR/deployment/"
    [ -d "backup" ] && cp -r backup "$OFFLINE_DIR/deployment/"
    
    log "部署文件复制完成"
}

# 创建辅助脚本
create_scripts() {
    info "创建辅助脚本..."
    
    # 离线导入脚本
    cat > "$OFFLINE_DIR/scripts/import-images.sh" << 'EOF'
#!/bin/bash
# 离线镜像导入脚本
set -e
[ ! -f "images/ljwx-images-*.tar.gz" ] && { echo "❌ 镜像文件不存在"; exit 1; }
echo "🐳 导入Docker镜像..."
gunzip images/ljwx-images-*.tar.gz
docker load -i images/ljwx-images-*.tar
echo "✅ 镜像导入完成"
docker images | grep ljwx #显示导入的镜像
EOF

    # 快速部署脚本
    cat > "$OFFLINE_DIR/scripts/quick-deploy.sh" << 'EOF'
#!/bin/bash
# 快速部署脚本
set -e
echo "🚀 LJWX系统快速部署"
cd deployment
chmod +x *.sh
./validate-centos-compatibility.sh #兼容性检查
bash deploy-client.sh #执行部署
echo "✅ 部署完成，请访问: http://$(hostname -I | awk '{print $1}'):8080"
EOF

    chmod +x "$OFFLINE_DIR/scripts"/*.sh
    log "辅助脚本创建完成"
}

# 创建文档
create_docs() {
    info "创建文档..."
    
    # README文件
    cat > "$OFFLINE_DIR/README.md" << EOF
# LJWX离线部署包 v${VERSION}

## 包含内容
- Docker镜像文件 (images/)
- 部署配置文件 (deployment/)  
- 辅助脚本 (scripts/)
- 技术文档 (docs/)

## 快速开始
1. 导入镜像: \`bash scripts/import-images.sh\`
2. 执行部署: \`bash scripts/quick-deploy.sh\`
3. 访问系统: http://服务器IP:8080

## 详细说明
参考: docs/离线部署完整指南.md

*生成时间: $(date)*
EOF

    # 复制详细文档
    cp "离线部署完整指南.md" "$OFFLINE_DIR/docs/" 2>/dev/null || warn "详细指南未找到"
    
    log "文档创建完成"
}

# 打包文件
create_package() {
    info "创建最终部署包..."
    
    # 生成清单文件
    find "$OFFLINE_DIR" -type f > "$OFFLINE_DIR/file-list.txt"
    
    # 计算文件大小
    echo "总文件数: $(wc -l < "$OFFLINE_DIR/file-list.txt")" > "$OFFLINE_DIR/package-info.txt"
    echo "总大小: $(du -sh "$OFFLINE_DIR" | cut -f1)" >> "$OFFLINE_DIR/package-info.txt"
    echo "创建时间: $(date)" >> "$OFFLINE_DIR/package-info.txt"
    echo "版本信息: LJWX v$VERSION" >> "$OFFLINE_DIR/package-info.txt"
    
    # 打包压缩
    tar -czf "$PACKAGE_NAME" "$OFFLINE_DIR"/
    
    log "离线部署包创建完成: $PACKAGE_NAME"
    log "包大小: $(du -h "$PACKAGE_NAME" | cut -f1)"
}

# 清理临时文件
cleanup() {
    info "清理临时文件..."
    rm -rf "$OFFLINE_DIR"
    log "清理完成"
}

# 主函数
main() {
    echo "🔧 LJWX离线部署包创建工具 v$VERSION"
    echo "================================================"
    
    check_env
    setup_workspace
    download_images  
    copy_deployment_files
    create_scripts
    create_docs
    create_package
    cleanup
    
    echo "================================================"
    log "🎉 离线部署包创建成功!"
    echo "📦 文件名: $PACKAGE_NAME"
    echo "📊 大小: $(du -h "$PACKAGE_NAME" | cut -f1)"
    echo "🚀 使用方法: tar -xzf $PACKAGE_NAME && cd ljwx-offline-*/scripts && ./quick-deploy.sh"
}

# 执行主函数
main "$@" 
