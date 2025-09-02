#!/bin/bash
# LJWX BigScreen 回滚脚本

set -e

NAMESPACE="${NAMESPACE:-ljwx-system}"
ENV="${ENV:-prod}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

usage() {
    cat << EOF
用法: $0 [选项]

选项:
    -e, --env ENV           环境 (dev|prod) [默认: prod]
    -n, --namespace NS      K8s命名空间 [默认: ljwx-system]
    -r, --revision REV      回滚到指定版本号
    --list                  列出历史版本
    --emergency             紧急回滚(回滚到上一版本)
    -h, --help              显示帮助信息

示例:
    $0 --list                           # 查看历史版本
    $0 --emergency                      # 紧急回滚
    $0 -r 3                            # 回滚到版本3
    $0 -e dev --emergency              # 开发环境紧急回滚
EOF
}

# 解析参数
REVISION=""
LIST=false
EMERGENCY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--revision)
            REVISION="$2"
            shift 2
            ;;
        --list)
            LIST=true
            shift
            ;;
        --emergency)
            EMERGENCY=true
            shift
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

# 设置部署名称
if [[ "$ENV" == "dev" ]]; then
    DEPLOYMENT="ljwx-bigscreen-dev"
else
    DEPLOYMENT="ljwx-bigscreen"
fi

# 检查kubectl
if ! command -v kubectl &> /dev/null; then
    error "kubectl 未安装或不在PATH中"
fi

# 检查部署是否存在
if ! kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" &> /dev/null; then
    error "部署 $DEPLOYMENT 在命名空间 $NAMESPACE 中不存在"
fi

# 列出历史版本
if [[ "$LIST" == "true" ]]; then
    log "查看 $DEPLOYMENT 的历史版本:"
    kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    exit 0
fi

# 紧急回滚
if [[ "$EMERGENCY" == "true" ]]; then
    log "执行紧急回滚..."
    
    # 获取当前版本
    CURRENT_REVISION=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    log "当前版本: $CURRENT_REVISION"
    
    # 执行回滚
    kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE"
    
    # 等待回滚完成
    log "等待回滚完成..."
    kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s
    
    # 清理可能的canary部署
    if [[ "$ENV" == "prod" ]]; then
        kubectl delete deployment ljwx-bigscreen-canary -n "$NAMESPACE" --ignore-not-found
        kubectl delete service ljwx-bigscreen-canary-service -n "$NAMESPACE" --ignore-not-found
        kubectl delete ingress ljwx-bigscreen-canary-ingress -n "$NAMESPACE" --ignore-not-found
    fi
    
    # 获取回滚后版本
    NEW_REVISION=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    log "回滚完成! 当前版本: $NEW_REVISION"
    
    # 显示Pod状态
    kubectl get pods -n "$NAMESPACE" -l app=ljwx-bigscreen
    
    exit 0
fi

# 回滚到指定版本
if [[ -n "$REVISION" ]]; then
    log "回滚到版本 $REVISION..."
    
    # 检查版本是否存在
    if ! kubectl rollout history deployment/"$DEPLOYMENT" -n "$NAMESPACE" --revision="$REVISION" &> /dev/null; then
        error "版本 $REVISION 不存在"
    fi
    
    # 执行回滚
    kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE" --to-revision="$REVISION"
    
    # 等待回滚完成
    log "等待回滚完成..."
    kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s
    
    # 清理可能的canary部署
    if [[ "$ENV" == "prod" ]]; then
        kubectl delete deployment ljwx-bigscreen-canary -n "$NAMESPACE" --ignore-not-found
        kubectl delete service ljwx-bigscreen-canary-service -n "$NAMESPACE" --ignore-not-found
        kubectl delete ingress ljwx-bigscreen-canary-ingress -n "$NAMESPACE" --ignore-not-found
    fi
    
    log "回滚到版本 $REVISION 完成!"
    
    # 显示Pod状态
    kubectl get pods -n "$NAMESPACE" -l app=ljwx-bigscreen
    
    exit 0
fi

# 如果没有指定任何操作，显示帮助
usage 