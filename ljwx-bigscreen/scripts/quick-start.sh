#!/bin/bash
# LJWX BigScreen CI/CD 快速启动脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

# 配置变量
GITEA_HOST="${GITEA_HOST:-192.168.1.83:3000}"
REGISTRY_HOST="${REGISTRY_HOST:-192.168.1.83:5000}"
K8S_NAMESPACE="${K8S_NAMESPACE:-ljwx-system}"

log "🚀 LJWX BigScreen CI/CD 快速启动"
log "Gitea: http://$GITEA_HOST"
log "Registry: $REGISTRY_HOST"
log "Namespace: $K8S_NAMESPACE"

# 检查依赖
check_dependencies() {
    log "检查依赖工具..."
    
    local missing_tools=()
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "缺少必需工具: ${missing_tools[*]}"
    fi
    
    log "✅ 依赖检查通过"
}

# 配置K8s环境
setup_k8s() {
    log "配置Kubernetes环境..."
    
    # 创建命名空间
    if ! kubectl get namespace "$K8S_NAMESPACE" &> /dev/null; then
        log "创建命名空间: $K8S_NAMESPACE"
        kubectl create namespace "$K8S_NAMESPACE"
    else
        log "命名空间已存在: $K8S_NAMESPACE"
    fi
    
    # 应用基础配置
    log "应用基础配置..."
    kubectl apply -f ../k8s/base/ || warn "基础配置应用失败，请检查文件"
    
    # 检查Metrics Server
    if ! kubectl get deployment metrics-server -n kube-system &> /dev/null; then
        warn "Metrics Server未安装，HPA功能将不可用"
        echo "安装命令: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
    fi
    
    log "✅ Kubernetes环境配置完成"
}

# 配置Docker Registry
setup_registry() {
    log "配置Docker Registry..."
    
    # 测试Registry连接
    if ! curl -s "http://$REGISTRY_HOST/v2/" &> /dev/null; then
        warn "无法连接到Registry: $REGISTRY_HOST"
        echo "请确保Registry服务正在运行:"
        echo "docker run -d -p 5000:5000 --name registry -v /opt/registry:/var/lib/registry registry:2"
        return 1
    fi
    
    # 配置Docker daemon
    local daemon_config="/etc/docker/daemon.json"
    if [ -f "$daemon_config" ]; then
        if ! grep -q "$REGISTRY_HOST" "$daemon_config"; then
            warn "请将 $REGISTRY_HOST 添加到Docker daemon.json的insecure-registries中"
        fi
    else
        warn "Docker daemon.json不存在，请创建并添加insecure-registries配置"
    fi
    
    log "✅ Registry配置检查完成"
}

# 初始化Git仓库
setup_git() {
    log "配置Git仓库..."
    
    # 检查是否在Git仓库中
    if ! git rev-parse --git-dir &> /dev/null; then
        log "初始化Git仓库..."
        git init
        git add .
        git commit -m "Initial commit: CI/CD配置"
    fi
    
    # 检查远程仓库
    if ! git remote get-url origin &> /dev/null; then
        warn "未配置远程仓库，请手动添加:"
        echo "git remote add origin http://admin:admin123@$GITEA_HOST/admin/ljwx-bigscreen.git"
    fi
    
    log "✅ Git配置检查完成"
}

# 生成配置文件
generate_configs() {
    log "生成配置文件..."
    
    # 生成环境配置
    cat > .env << EOF
# LJWX BigScreen 环境配置
REGISTRY=$REGISTRY_HOST
IMAGE_NAME=ljwx-bigscreen
NAMESPACE=$K8S_NAMESPACE
GITEA_HOST=$GITEA_HOST

# 数据库配置
MYSQL_HOST=mysql-service.ljwx-system.svc.cluster.local
MYSQL_PORT=3306
MYSQL_USER=ljwx
MYSQL_PASSWORD=ljwx123
MYSQL_DATABASE=ljwx

# Redis配置
REDIS_HOST=redis-service.ljwx-system.svc.cluster.local
REDIS_PORT=6379
EOF
    
    # 生成部署配置
    cat > deploy-config.yaml << EOF
# 部署配置
environments:
  dev:
    replicas: 1
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi
  
  prod:
    replicas: 3
    resources:
      requests:
        cpu: 200m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    
    hpa:
      minReplicas: 3
      maxReplicas: 10
      targetCPU: 70
      targetMemory: 80
EOF
    
    log "✅ 配置文件生成完成"
}

# 测试部署
test_deployment() {
    log "测试部署功能..."
    
    # 构建测试镜像
    if [ -f "../bigscreen/Dockerfile.multiarch" ]; then
        log "构建测试镜像..."
        docker build -f ../bigscreen/Dockerfile.multiarch -t "$REGISTRY_HOST/ljwx-bigscreen:test" ../bigscreen/ || {
            warn "镜像构建失败，请检查Dockerfile"
            return 1
        }
        
        # 推送测试镜像
        docker push "$REGISTRY_HOST/ljwx-bigscreen:test" || {
            warn "镜像推送失败，请检查Registry配置"
            return 1
        }
        
        log "✅ 镜像构建和推送成功"
    else
        warn "Dockerfile不存在，跳过镜像构建测试"
    fi
    
    # 测试部署脚本
    if [ -f "deploy.sh" ]; then
        log "测试部署脚本..."
        chmod +x deploy.sh
        ./deploy.sh -h > /dev/null || warn "部署脚本执行失败"
        log "✅ 部署脚本测试通过"
    fi
}

# 显示后续步骤
show_next_steps() {
    log "🎉 快速启动完成！"
    echo
    echo -e "${BLUE}后续步骤:${NC}"
    echo "1. 配置Gitea Secrets:"
    echo "   - DOCKER_USERNAME: admin"
    echo "   - DOCKER_PASSWORD: your_password"
    echo "   - KUBECONFIG: \$(cat ~/.kube/config | base64 -w 0)"
    echo
    echo "2. 推送代码触发CI/CD:"
    echo "   git add ."
    echo "   git commit -m 'feat: 启用CI/CD'"
    echo "   git push origin main"
    echo
    echo "3. 手动部署测试:"
    echo "   ./scripts/deploy.sh -e dev -t test"
    echo
    echo "4. 查看部署状态:"
    echo "   kubectl get pods -n $K8S_NAMESPACE"
    echo
    echo "5. 访问应用:"
    echo "   kubectl port-forward svc/ljwx-bigscreen-service 8080:80 -n $K8S_NAMESPACE"
    echo "   http://localhost:8080"
    echo
    echo -e "${GREEN}文档地址: CI_CD_README.md${NC}"
}

# 主函数
main() {
    check_dependencies
    setup_k8s
    setup_registry
    setup_git
    generate_configs
    test_deployment
    show_next_steps
}

# 执行主函数
main "$@" 