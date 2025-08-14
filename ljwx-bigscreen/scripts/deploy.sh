#!/bin/bash
# LJWX BigScreen 部署脚本

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REGISTRY="${REGISTRY:-192.168.1.83:5000}"
IMAGE_NAME="${IMAGE_NAME:-ljwx-bigscreen}"
NAMESPACE="${NAMESPACE:-ljwx-system}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

usage() {
    cat << EOF
用法: $0 [选项]

选项:
    -e, --env ENV           部署环境 (dev|prod) [默认: dev]
    -t, --tag TAG           镜像标签 [默认: latest]
    -n, --namespace NS      K8s命名空间 [默认: ljwx-system]
    -r, --registry REG      Docker镜像仓库 [默认: 192.168.1.83:5000]
    --canary               执行灰度部署
    --rollback             回滚到上一版本
    --scale REPLICAS       扩缩容到指定副本数
    -h, --help             显示帮助信息

示例:
    $0 -e dev -t v1.0.0                    # 部署到开发环境
    $0 -e prod -t v1.0.0                   # 部署到生产环境
    $0 -e prod -t v1.0.0 --canary          # 灰度部署
    $0 --rollback                          # 回滚
    $0 --scale 5                           # 扩容到5个副本
EOF
}

# 解析命令行参数
ENV="dev"
TAG="latest"
CANARY=false
ROLLBACK=false
SCALE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        --canary)
            CANARY=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --scale)
            SCALE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "未知参数: $1"
            ;;
    esac
done

# 验证环境参数
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    error "环境参数必须是 dev 或 prod"
fi

# 检查kubectl
if ! command -v kubectl &> /dev/null; then
    error "kubectl 未安装或不在PATH中"
fi

# 检查命名空间
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log "创建命名空间: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# 回滚功能
if [[ "$ROLLBACK" == "true" ]]; then
    log "执行回滚操作..."
    if [[ "$ENV" == "prod" ]]; then
        kubectl rollout undo deployment/ljwx-bigscreen -n "$NAMESPACE"
        kubectl rollout status deployment/ljwx-bigscreen -n "$NAMESPACE"
        # 清理可能存在的canary部署
        kubectl delete deployment ljwx-bigscreen-canary -n "$NAMESPACE" --ignore-not-found
    else
        kubectl rollout undo deployment/ljwx-bigscreen-dev -n "$NAMESPACE"
        kubectl rollout status deployment/ljwx-bigscreen-dev -n "$NAMESPACE"
    fi
    log "回滚完成"
    exit 0
fi

# 扩缩容功能
if [[ -n "$SCALE" ]]; then
    log "扩缩容到 $SCALE 个副本..."
    if [[ "$ENV" == "prod" ]]; then
        kubectl scale deployment ljwx-bigscreen --replicas="$SCALE" -n "$NAMESPACE"
    else
        kubectl scale deployment ljwx-bigscreen-dev --replicas="$SCALE" -n "$NAMESPACE"
    fi
    log "扩缩容完成"
    exit 0
fi

# 设置镜像变量
export REGISTRY="$REGISTRY"
export IMAGE_NAME="$IMAGE_NAME"
export IMAGE_TAG="$TAG"

log "开始部署 LJWX BigScreen"
log "环境: $ENV"
log "镜像: $REGISTRY/$IMAGE_NAME:$TAG"
log "命名空间: $NAMESPACE"

# 应用基础配置
log "应用基础配置..."
kubectl apply -f "$PROJECT_DIR/k8s/base/"

# 根据环境部署
if [[ "$ENV" == "dev" ]]; then
    log "部署到开发环境..."
    envsubst < "$PROJECT_DIR/k8s/dev/deployment.yaml" | kubectl apply -f -
    kubectl rollout status deployment/ljwx-bigscreen-dev -n "$NAMESPACE"
    
elif [[ "$ENV" == "prod" ]]; then
    if [[ "$CANARY" == "true" ]]; then
        log "执行灰度部署..."
        
        # 部署canary版本
        envsubst < "$PROJECT_DIR/k8s/prod/canary-deployment.yaml" | kubectl apply -f -
        kubectl rollout status deployment/ljwx-bigscreen-canary -n "$NAMESPACE"
        
        # 应用canary服务配置
        kubectl apply -f "$PROJECT_DIR/k8s/prod/canary-service.yaml"
        
        log "灰度部署完成，10%流量已切换到新版本"
        log "请验证新版本功能正常后，运行以下命令完成全量部署:"
        log "$0 -e prod -t $TAG"
        
    else
        log "部署到生产环境..."
        
        # 检查是否存在canary部署
        if kubectl get deployment ljwx-bigscreen-canary -n "$NAMESPACE" &> /dev/null; then
            log "检测到灰度部署，执行全量部署..."
        fi
        
        # 部署主版本
        envsubst < "$PROJECT_DIR/k8s/prod/deployment.yaml" | kubectl apply -f -
        kubectl apply -f "$PROJECT_DIR/k8s/prod/service.yaml"
        kubectl apply -f "$PROJECT_DIR/k8s/prod/ingress.yaml"
        
        kubectl rollout status deployment/ljwx-bigscreen -n "$NAMESPACE"
        
        # 清理canary部署
        kubectl delete deployment ljwx-bigscreen-canary -n "$NAMESPACE" --ignore-not-found
        kubectl delete service ljwx-bigscreen-canary-service -n "$NAMESPACE" --ignore-not-found
        kubectl delete ingress ljwx-bigscreen-canary-ingress -n "$NAMESPACE" --ignore-not-found
        
        log "生产环境部署完成"
    fi
fi

# 应用监控配置
if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
    log "应用监控配置..."
    kubectl apply -f "$PROJECT_DIR/k8s/monitoring/"
fi

# 显示部署状态
log "部署状态:"
kubectl get pods -n "$NAMESPACE" -l app=ljwx-bigscreen
kubectl get svc -n "$NAMESPACE" -l app=ljwx-bigscreen

if [[ "$ENV" == "prod" ]]; then
    kubectl get ingress -n "$NAMESPACE" -l app=ljwx-bigscreen
fi

log "部署完成! 🎉" 