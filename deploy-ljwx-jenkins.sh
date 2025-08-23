#!/bin/bash
# LJWX Jenkins完整自动化部署脚本

set -e

# 配置参数
COMPOSE_FILE="docker/compose/ljwx-jenkins-complete.yml"
IMAGE_NAME="ljwx-jenkins"
REGISTRY_URL="localhost:5001"
PROJECT_NAME="ljwx"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
P='\033[0;35m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }
success() { echo -e "${P}[SUCCESS]${NC} $1"; }

# 检查环境
check_environment() {
    log "检查环境依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查Docker服务
    if ! docker info &> /dev/null; then
        error "Docker服务未运行"
        exit 1
    fi
    
    success "环境检查通过"
}

# 清理旧部署
cleanup_old_deployment() {
    log "清理旧部署..."
    
    # 停止并删除旧容器
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    
    # 删除旧镜像
    docker rmi $IMAGE_NAME:latest 2>/dev/null || true
    
    # 清理未使用的资源
    docker system prune -f 2>/dev/null || true
    
    success "清理完成"
}

# 构建镜像
build_image() {
    log "构建LJWX Jenkins镜像..."
    
    # 确保目录存在
    mkdir -p docker/compose/jenkins/setup
    
    # 构建镜像
    docker-compose -f $COMPOSE_FILE build --no-cache ljwx-jenkins
    
    # 标记镜像
    docker tag ljwx-jenkins:latest $IMAGE_NAME:$(date +%Y%m%d-%H%M%S)
    
    success "镜像构建完成: $IMAGE_NAME:latest"
}

# 启动服务
start_services() {
    log "启动LJWX Jenkins服务..."
    
    # 启动服务
    docker-compose -f $COMPOSE_FILE up -d
    
    success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log "等待服务就绪..."
    
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8081/login > /dev/null 2>&1; then
            success "Jenkins服务就绪"
            break
        fi
        
        echo -n "."
        sleep 5
        ((attempt++))
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "Jenkins服务启动超时"
        exit 1
    fi
    
    # 检查Registry
    if curl -s http://localhost:5001/v2/ > /dev/null 2>&1; then
        success "Registry服务就绪"
    else
        warn "Registry服务可能未就绪"
    fi
}

# 推送镜像到Registry
push_to_registry() {
    log "推送镜像到Registry..."
    
    # 等待Registry就绪
    sleep 10
    
    # 标记镜像
    docker tag $IMAGE_NAME:latest $REGISTRY_URL/$IMAGE_NAME:latest
    docker tag $IMAGE_NAME:latest $REGISTRY_URL/$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)
    
    # 推送镜像
    docker push $REGISTRY_URL/$IMAGE_NAME:latest
    docker push $REGISTRY_URL/$IMAGE_NAME:$(date +%Y%m%d-%H%M%S)
    
    success "镜像推送完成"
}

# 验证部署
verify_deployment() {
    log "验证部署状态..."
    
    echo ""
    echo "============================================================"
    echo -e "${B}📊 部署状态检查${NC}"
    echo "============================================================"
    
    # 检查容器状态
    echo -e "${B}🐳 容器状态:${NC}"
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    echo -e "${B}🔌 插件统计:${NC}"
    local plugin_count=$(docker exec ljwx-jenkins find /var/jenkins_home/plugins -name "*.jpi" 2>/dev/null | wc -l || echo "检查中...")
    echo "   已安装插件: $plugin_count 个"
    
    echo ""
    echo -e "${B}📦 镜像信息:${NC}"
    echo "   本地镜像: $(docker images $IMAGE_NAME:latest --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}")"
    
    echo ""
    echo -e "${B}🌐 服务地址:${NC}"
    echo "   Jenkins Web: http://localhost:8081"
    echo "   Registry API: http://localhost:5001"
    echo "   Registry UI: http://localhost:5002"
    
    echo ""
    echo -e "${B}🔑 登录信息:${NC}"
    echo "   用户名: admin"
    echo "   密码: admin123"
    
    # 检查Registry中的镜像
    echo ""
    echo -e "${B}📋 Registry镜像:${NC}"
    curl -s http://localhost:5001/v2/_catalog 2>/dev/null | grep -o '"repositories":\[[^]]*\]' || echo "   检查Registry镜像列表中..."
}

# 显示Webhook配置信息
show_webhook_info() {
    echo ""
    echo "============================================================"
    echo -e "${P}🚀 CI/CD配置指南${NC}"
    echo "============================================================"
    
    echo -e "${B}📝 Gitea Webhook配置:${NC}"
    echo "   Java项目: http://localhost:8081/generic-webhook-trigger/invoke?token=java-webhook-token"
    echo "   Vue3项目: http://localhost:8081/generic-webhook-trigger/invoke?token=vue3-webhook-token"
    echo "   Python项目: http://localhost:8081/generic-webhook-trigger/invoke?token=python-webhook-token"
    
    echo ""
    echo -e "${B}📋 Pipeline作业:${NC}"
    echo "   ✅ java-spring-boot-pipeline (Java SpringBoot CI/CD)"
    echo "   ✅ vue3-frontend-pipeline (Vue3前端CI/CD)"
    echo "   ✅ python-fastapi-pipeline (Python FastAPI CI/CD)"
    
    echo ""
    echo -e "${B}🔧 配置步骤:${NC}"
    echo "   1. 访问 http://localhost:8081 登录Jenkins (admin/admin123)"
    echo "   2. 更新凭据管理中的实际Token和密钥"
    echo "   3. 在Gitea中配置上述Webhook URL"
    echo "   4. 推送代码触发自动CI/CD流程"
    
    echo ""
    echo -e "${B}📚 CI/CD流程:${NC}"
    echo "   Git Push → Gitea Webhook → Jenkins Pipeline → Docker Build → Registry Push → K8s Deploy"
}

# 显示管理命令
show_management_commands() {
    echo ""
    echo "============================================================"
    echo -e "${Y}🔧 管理命令${NC}"
    echo "============================================================"
    
    echo -e "${B}日常管理:${NC}"
    echo "   查看日志: docker-compose -f $COMPOSE_FILE logs -f ljwx-jenkins"
    echo "   重启服务: docker-compose -f $COMPOSE_FILE restart ljwx-jenkins"
    echo "   停止服务: docker-compose -f $COMPOSE_FILE down"
    echo "   更新镜像: ./deploy-ljwx-jenkins.sh"
    
    echo ""
    echo -e "${B}备份恢复:${NC}"
    echo "   备份数据: docker run --rm -v ljwx-jenkins-data:/data -v \$(pwd):/backup alpine tar czf /backup/jenkins-backup-\$(date +%Y%m%d).tar.gz -C /data ."
    echo "   恢复数据: docker run --rm -v ljwx-jenkins-data:/data -v \$(pwd):/backup alpine tar xzf /backup/jenkins-backup-YYYYMMDD.tar.gz -C /data"
    
    echo ""
    echo -e "${B}镜像管理:${NC}"
    echo "   查看镜像: curl -s http://localhost:5001/v2/_catalog | jq"
    echo "   删除镜像: curl -X DELETE http://localhost:5001/v2/$IMAGE_NAME/manifests/\$(docker manifest inspect $REGISTRY_URL/$IMAGE_NAME:latest | jq -r '.mediaType')"
}

# 主函数
main() {
    echo ""
    echo "============================================================"
    echo -e "${P}🚀 LJWX Jenkins 完整自动化部署${NC}"
    echo "============================================================"
    echo ""
    
    check_environment
    cleanup_old_deployment
    build_image
    start_services
    wait_for_services
    
    # 推送到Registry
    push_to_registry || warn "Registry推送失败，请检查服务状态"
    
    verify_deployment
    show_webhook_info
    show_management_commands
    
    echo ""
    echo "============================================================"
    success "🎉 LJWX Jenkins部署完成！"
    echo -e "${P}现在可以访问 http://localhost:8081 开始使用完整的CI/CD环境！${NC}"
    echo "============================================================"
}

# 检查参数
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "cleanup")
        cleanup_old_deployment
        ;;
    "build")
        build_image
        ;;
    "push")
        push_to_registry
        ;;
    "verify")
        verify_deployment
        ;;
    *)
        echo "用法: $0 [deploy|cleanup|build|push|verify]"
        echo "  deploy  - 完整部署 (默认)"
        echo "  cleanup - 清理旧部署"
        echo "  build   - 仅构建镜像"
        echo "  push    - 仅推送镜像"
        echo "  verify  - 仅验证部署"
        exit 1
        ;;
esac 