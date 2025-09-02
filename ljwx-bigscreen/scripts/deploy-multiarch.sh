#!/bin/bash

# LJWX BigScreen 多架构部署脚本
# 版本: 1.3.1
# 支持环境: dev, staging, prod

set -e

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"

# 默认配置
DEFAULT_REGISTRY="registry.cn-hangzhou.aliyuncs.com"
DEFAULT_NAMESPACE="ljwx-bigscreen"
DEFAULT_IMAGE_NAME="ljwx-bigscreen"
DEFAULT_VERSION="1.3.1"
DEFAULT_ENVIRONMENT="dev"
DEFAULT_K8S_NAMESPACE="ljwx-system"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $(date +'%Y-%m-%d %H:%M:%S') $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
LJWX BigScreen 多架构部署脚本

用法: $0 [选项]

选项:
  -e, --environment ENV      部署环境 (dev/staging/prod) (默认: $DEFAULT_ENVIRONMENT)
  -t, --tag TAG             镜像标签 (默认: $DEFAULT_VERSION)
  -r, --registry REGISTRY   容器镜像仓库地址 (默认: $DEFAULT_REGISTRY)
  -n, --namespace NAMESPACE  镜像命名空间 (默认: $DEFAULT_NAMESPACE)
  -i, --image IMAGE_NAME     镜像名称 (默认: $DEFAULT_IMAGE_NAME)
  -k, --kube-namespace NS    K8s 命名空间 (默认: $DEFAULT_K8S_NAMESPACE)
  -c, --canary               启用灰度部署 (仅限 prod 环境)
  -s, --scale REPLICAS       设置副本数
  -u, --upgrade              滚动升级现有部署
  -R, --rollback REVISION    回滚到指定版本
  -D, --dry-run              演练模式，不实际执行
  -w, --wait                 等待部署完成
  -f, --force                强制部署，跳过确认
  -d, --debug                启用调试模式
  -h, --help                 显示此帮助信息

操作:
  --status                   显示部署状态
  --logs                     显示应用日志
  --describe                 显示详细信息
  --cleanup                  清理资源

示例:
  # 部署到开发环境
  $0 -e dev -t 1.3.1

  # 生产环境灰度部署
  $0 -e prod -t 1.3.1 --canary

  # 扩容到 5 个副本
  $0 -e prod --scale 5

  # 回滚到上一版本
  $0 -e prod --rollback

  # 查看部署状态
  $0 --status -e prod

环境变量:
  KUBECONFIG             K8s 配置文件路径
  KUBECTL_CONTEXT        K8s 上下文
  DEBUG                  启用调试模式 (true/false)

EOF
}

# 解析命令行参数
parse_args() {
    ENVIRONMENT="$DEFAULT_ENVIRONMENT"
    VERSION="$DEFAULT_VERSION"
    REGISTRY="$DEFAULT_REGISTRY"
    NAMESPACE="$DEFAULT_NAMESPACE"
    IMAGE_NAME="$DEFAULT_IMAGE_NAME"
    KUBE_NAMESPACE="$DEFAULT_K8S_NAMESPACE"
    CANARY=false
    SCALE=""
    UPGRADE=false
    ROLLBACK=""
    DRY_RUN=false
    WAIT=false
    FORCE=false
    
    # 操作模式
    OPERATION=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                VERSION="$2"
                shift 2
                ;;
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
            -k|--kube-namespace)
                KUBE_NAMESPACE="$2"
                shift 2
                ;;
            -c|--canary)
                CANARY=true
                shift
                ;;
            -s|--scale)
                SCALE="$2"
                shift 2
                ;;
            -u|--upgrade)
                UPGRADE=true
                shift
                ;;
            -R|--rollback)
                ROLLBACK="${2:-previous}"
                shift 2
                ;;
            -D|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -w|--wait)
                WAIT=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            --status)
                OPERATION="status"
                shift
                ;;
            --logs)
                OPERATION="logs"
                shift
                ;;
            --describe)
                OPERATION="describe"
                shift
                ;;
            --cleanup)
                OPERATION="cleanup"
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
    
    # 验证环境
    case $ENVIRONMENT in
        dev|staging|prod)
            ;;
        *)
            log_error "无效的环境: $ENVIRONMENT (支持: dev, staging, prod)"
            exit 1
            ;;
    esac
    
    # 生产环境灰度部署检查
    if [ "$CANARY" = "true" ] && [ "$ENVIRONMENT" != "prod" ]; then
        log_error "灰度部署仅支持生产环境"
        exit 1
    fi
    
    # 构建完整镜像名称
    FULL_IMAGE_NAME="$REGISTRY/$NAMESPACE/$IMAGE_NAME:$VERSION"
    
    log_debug "解析的参数:"
    log_debug "  Environment: $ENVIRONMENT"
    log_debug "  Version: $VERSION"
    log_debug "  Registry: $REGISTRY"
    log_debug "  Namespace: $NAMESPACE"
    log_debug "  Image: $IMAGE_NAME"
    log_debug "  Full Image: $FULL_IMAGE_NAME"
    log_debug "  K8s Namespace: $KUBE_NAMESPACE"
    log_debug "  Canary: $CANARY"
    log_debug "  Scale: $SCALE"
    log_debug "  Operation: $OPERATION"
}

# 检查前置条件
check_prerequisites() {
    log_step "检查前置条件..."
    
    # 检查 kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安装或不在 PATH 中"
        exit 1
    fi
    
    # 检查 kubectl 版本
    KUBECTL_VERSION=$(kubectl version --client -o yaml | grep gitVersion | cut -d'"' -f4)
    log_info "kubectl 版本: $KUBECTL_VERSION"
    
    # 检查 K8s 连接
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到 Kubernetes 集群"
        log_info "请检查 KUBECONFIG 环境变量或 ~/.kube/config 文件"
        exit 1
    fi
    
    # 检查命名空间
    if ! kubectl get namespace "$KUBE_NAMESPACE" &> /dev/null; then
        log_warn "命名空间 $KUBE_NAMESPACE 不存在，将自动创建"
        if [ "$DRY_RUN" = "false" ]; then
            kubectl create namespace "$KUBE_NAMESPACE"
            log_info "已创建命名空间: $KUBE_NAMESPACE"
        fi
    fi
    
    # 检查 K8s 配置文件
    ENV_CONFIG_DIR="$K8S_DIR/$ENVIRONMENT"
    if [ ! -d "$ENV_CONFIG_DIR" ]; then
        log_error "环境配置目录不存在: $ENV_CONFIG_DIR"
        exit 1
    fi
    
    log_info "前置条件检查通过 ✓"
}

# 设置 K8s 上下文
setup_context() {
    if [ -n "$KUBECTL_CONTEXT" ]; then
        log_info "切换 K8s 上下文: $KUBECTL_CONTEXT"
        kubectl config use-context "$KUBECTL_CONTEXT"
    fi
    
    # 显示当前上下文
    CURRENT_CONTEXT=$(kubectl config current-context)
    CURRENT_CLUSTER=$(kubectl config view -o jsonpath='{.contexts[?(@.name == "'$CURRENT_CONTEXT'")].context.cluster}')
    log_info "当前 K8s 上下文: $CURRENT_CONTEXT"
    log_info "当前集群: $CURRENT_CLUSTER"
}

# 准备部署配置
prepare_deployment_config() {
    log_step "准备部署配置..."
    
    # 设置环境变量用于模板替换
    export REGISTRY="$REGISTRY"
    export NAMESPACE="$NAMESPACE"
    export IMAGE_NAME="$IMAGE_NAME"
    export IMAGE_TAG="$VERSION"
    export ENVIRONMENT="$ENVIRONMENT"
    export KUBE_NAMESPACE="$KUBE_NAMESPACE"
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export DEPLOYMENT_ID=$(date +%s)
    
    # 扩容配置
    if [ -n "$SCALE" ]; then
        export REPLICAS="$SCALE"
    fi
    
    log_info "部署配置已准备 ✓"
}

# 执行部署操作
execute_deployment() {
    case $OPERATION in
        "status")
            show_deployment_status
            ;;
        "logs")
            show_application_logs
            ;;
        "describe")
            describe_deployment
            ;;
        "cleanup")
            cleanup_resources
            ;;
        *)
            perform_deployment
            ;;
    esac
}

# 执行实际部署
perform_deployment() {
    if [ -n "$ROLLBACK" ]; then
        perform_rollback
        return
    fi
    
    if [ "$CANARY" = "true" ]; then
        perform_canary_deployment
    else
        perform_standard_deployment
    fi
}

# 标准部署
perform_standard_deployment() {
    log_step "执行标准部署到 $ENVIRONMENT 环境..."
    
    ENV_CONFIG_DIR="$K8S_DIR/$ENVIRONMENT"
    
    # 确认部署
    if [ "$FORCE" = "false" ] && [ "$DRY_RUN" = "false" ]; then
        echo -e "${YELLOW}即将部署:${NC}"
        echo "  环境: $ENVIRONMENT"
        echo "  镜像: $FULL_IMAGE_NAME"
        echo "  命名空间: $KUBE_NAMESPACE"
        if [ -n "$SCALE" ]; then
            echo "  副本数: $SCALE"
        fi
        
        read -p "确认部署? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi
    
    # 应用配置
    for config_file in "$ENV_CONFIG_DIR"/*.yaml; do
        if [ -f "$config_file" ]; then
            log_info "应用配置: $(basename "$config_file")"
            if [ "$DRY_RUN" = "true" ]; then
                envsubst < "$config_file" | kubectl apply --dry-run=client -f -
            else
                envsubst < "$config_file" | kubectl apply -f -
            fi
        fi
    done
    
    # 等待部署完成
    if [ "$WAIT" = "true" ] && [ "$DRY_RUN" = "false" ]; then
        wait_for_deployment
    fi
    
    # 验证部署
    if [ "$DRY_RUN" = "false" ]; then
        verify_deployment
    fi
    
    log_info "标准部署完成 ✓"
}

# 灰度部署
perform_canary_deployment() {
    log_step "执行灰度部署到生产环境..."
    
    PROD_CONFIG_DIR="$K8S_DIR/prod"
    
    # 确认灰度部署
    if [ "$FORCE" = "false" ] && [ "$DRY_RUN" = "false" ]; then
        echo -e "${YELLOW}即将执行灰度部署:${NC}"
        echo "  环境: $ENVIRONMENT (灰度)"
        echo "  镜像: $FULL_IMAGE_NAME"
        echo "  流量分配: 10% → 新版本"
        
        read -p "确认灰度部署? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "灰度部署已取消"
            exit 0
        fi
    fi
    
    # 部署 Canary 版本
    log_info "部署 Canary 版本..."
    if [ "$DRY_RUN" = "true" ]; then
        envsubst < "$PROD_CONFIG_DIR/canary-deployment.yaml" | kubectl apply --dry-run=client -f -
        envsubst < "$PROD_CONFIG_DIR/canary-service.yaml" | kubectl apply --dry-run=client -f -
    else
        envsubst < "$PROD_CONFIG_DIR/canary-deployment.yaml" | kubectl apply -f -
        envsubst < "$PROD_CONFIG_DIR/canary-service.yaml" | kubectl apply -f -
    fi
    
    # 等待 Canary 部署完成
    if [ "$WAIT" = "true" ] && [ "$DRY_RUN" = "false" ]; then
        log_info "等待 Canary 部署完成..."
        kubectl rollout status deployment/ljwx-bigscreen-canary -n "$KUBE_NAMESPACE" --timeout=300s
    fi
    
    # 验证 Canary 部署
    if [ "$DRY_RUN" = "false" ]; then
        verify_canary_deployment
    fi
    
    log_info "灰度部署完成 ✓"
    log_warn "请验证 Canary 版本运行正常后，手动执行全量部署"
}

# 回滚操作
perform_rollback() {
    log_step "执行回滚操作..."
    
    DEPLOYMENT_NAME="ljwx-bigscreen"
    if [ "$CANARY" = "true" ]; then
        DEPLOYMENT_NAME="ljwx-bigscreen-canary"
    fi
    
    # 确认回滚
    if [ "$FORCE" = "false" ] && [ "$DRY_RUN" = "false" ]; then
        echo -e "${YELLOW}即将回滚部署:${NC}"
        echo "  环境: $ENVIRONMENT"
        echo "  部署: $DEPLOYMENT_NAME"
        if [ "$ROLLBACK" != "previous" ]; then
            echo "  目标版本: $ROLLBACK"
        else
            echo "  目标版本: 上一版本"
        fi
        
        read -p "确认回滚? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "回滚已取消"
            exit 0
        fi
    fi
    
    # 执行回滚
    if [ "$DRY_RUN" = "true" ]; then
        log_info "[DRY RUN] 将回滚部署: $DEPLOYMENT_NAME"
    else
        if [ "$ROLLBACK" = "previous" ]; then
            kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE"
        else
            kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE" --to-revision="$ROLLBACK"
        fi
        
        # 等待回滚完成
        kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE" --timeout=300s
    fi
    
    log_info "回滚完成 ✓"
}

# 等待部署完成
wait_for_deployment() {
    log_info "等待部署完成..."
    
    DEPLOYMENT_NAME="ljwx-bigscreen"
    if [ "$ENVIRONMENT" == "dev" ]; then
        DEPLOYMENT_NAME="ljwx-bigscreen-dev"
    elif [ "$CANARY" = "true" ]; then
        DEPLOYMENT_NAME="ljwx-bigscreen-canary"
    fi
    
    if ! kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE" --timeout=600s; then
        log_error "部署超时或失败"
        show_deployment_troubleshooting
        exit 1
    fi
    
    log_info "部署完成 ✓"
}

# 验证部署
verify_deployment() {
    log_step "验证部署..."
    
    # 检查 Pod 状态
    log_info "检查 Pod 状态..."
    kubectl get pods -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,env="$ENVIRONMENT"
    
    # 检查服务状态
    log_info "检查服务状态..."
    kubectl get services -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen
    
    # 健康检查
    log_info "执行健康检查..."
    sleep 10
    
    # 获取服务 URL (这里需要根据实际的 Ingress 配置调整)
    if [ "$ENVIRONMENT" = "prod" ]; then
        SERVICE_URL="http://bigscreen.ljwx.local"
    else
        SERVICE_URL="http://bigscreen-$ENVIRONMENT.ljwx.local"
    fi
    
    # 简单的健康检查
    if command -v curl &> /dev/null; then
        for i in {1..3}; do
            if curl -f -s "$SERVICE_URL/api/health" > /dev/null; then
                log_info "健康检查通过 ✓"
                break
            elif [ $i -eq 3 ]; then
                log_warn "健康检查失败，但服务可能仍在启动中"
            else
                log_info "健康检查重试 ($i/3)..."
                sleep 10
            fi
        done
    fi
    
    log_info "部署验证完成 ✓"
}

# 验证灰度部署
verify_canary_deployment() {
    log_step "验证灰度部署..."
    
    # 检查 Canary Pod 状态
    kubectl get pods -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,version=canary
    
    # 检查 Canary 服务
    kubectl get services -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,version=canary
    
    # Canary 健康检查
    sleep 15
    
    SERVICE_URL="http://bigscreen.ljwx.local"
    if command -v curl &> /dev/null; then
        for i in {1..5}; do
            # 通过 canary header 访问灰度版本
            if curl -H "canary: true" -f -s "$SERVICE_URL/api/health" > /dev/null; then
                log_info "Canary 健康检查通过 ✓"
                break
            elif [ $i -eq 5 ]; then
                log_warn "Canary 健康检查失败"
                show_canary_troubleshooting
            else
                log_info "Canary 健康检查重试 ($i/5)..."
                sleep 10
            fi
        done
    fi
    
    log_info "灰度部署验证完成 ✓"
}

# 显示部署状态
show_deployment_status() {
    log_step "显示 $ENVIRONMENT 环境部署状态..."
    
    echo -e "\n${BLUE}=== Deployments ===${NC}"
    kubectl get deployments -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen
    
    echo -e "\n${BLUE}=== Pods ===${NC}"
    kubectl get pods -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen -o wide
    
    echo -e "\n${BLUE}=== Services ===${NC}"
    kubectl get services -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen
    
    echo -e "\n${BLUE}=== Ingress ===${NC}"
    kubectl get ingress -n "$KUBE_NAMESPACE" 2>/dev/null || echo "No ingress found"
    
    echo -e "\n${BLUE}=== HPA ===${NC}"
    kubectl get hpa -n "$KUBE_NAMESPACE" 2>/dev/null || echo "No HPA found"
}

# 显示应用日志
show_application_logs() {
    log_step "显示应用日志..."
    
    DEPLOYMENT_NAME="ljwx-bigscreen"
    if [ "$ENVIRONMENT" == "dev" ]; then
        DEPLOYMENT_NAME="ljwx-bigscreen-dev"
    fi
    
    kubectl logs -f deployment/"$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE" --tail=100
}

# 描述部署
describe_deployment() {
    log_step "显示部署详细信息..."
    
    DEPLOYMENT_NAME="ljwx-bigscreen"
    if [ "$ENVIRONMENT" == "dev" ]; then
        DEPLOYMENT_NAME="ljwx-bigscreen-dev"
    fi
    
    echo -e "\n${BLUE}=== Deployment Description ===${NC}"
    kubectl describe deployment "$DEPLOYMENT_NAME" -n "$KUBE_NAMESPACE"
    
    echo -e "\n${BLUE}=== Pod Events ===${NC}"
    kubectl get events -n "$KUBE_NAMESPACE" --sort-by='.lastTimestamp' | tail -20
}

# 清理资源
cleanup_resources() {
    log_step "清理资源..."
    
    if [ "$FORCE" = "false" ]; then
        echo -e "${YELLOW}即将清理以下资源:${NC}"
        echo "  环境: $ENVIRONMENT"
        echo "  命名空间: $KUBE_NAMESPACE"
        
        read -p "确认清理? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "清理已取消"
            exit 0
        fi
    fi
    
    # 删除部署
    kubectl delete deployment -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,env="$ENVIRONMENT" --ignore-not-found=true
    
    # 删除服务
    kubectl delete service -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,env="$ENVIRONMENT" --ignore-not-found=true
    
    # 删除 ConfigMap 和 Secret (可选)
    # kubectl delete configmap -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen --ignore-not-found=true
    
    log_info "资源清理完成 ✓"
}

# 显示故障排查信息
show_deployment_troubleshooting() {
    log_error "部署可能遇到问题，以下是故障排查信息:"
    
    echo -e "\n${BLUE}=== Recent Events ===${NC}"
    kubectl get events -n "$KUBE_NAMESPACE" --sort-by='.lastTimestamp' | tail -10
    
    echo -e "\n${BLUE}=== Pod Status ===${NC}"
    kubectl get pods -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen
    
    echo -e "\n${BLUE}=== Pod Logs ===${NC}"
    kubectl logs -l app=ljwx-bigscreen -n "$KUBE_NAMESPACE" --tail=50
}

# 显示灰度故障排查信息
show_canary_troubleshooting() {
    log_error "Canary 部署可能遇到问题，以下是故障排查信息:"
    
    echo -e "\n${BLUE}=== Canary Pods ===${NC}"
    kubectl get pods -n "$KUBE_NAMESPACE" -l app=ljwx-bigscreen,version=canary
    
    echo -e "\n${BLUE}=== Canary Logs ===${NC}"
    kubectl logs -l app=ljwx-bigscreen,version=canary -n "$KUBE_NAMESPACE" --tail=50
}

# 显示部署摘要
show_deployment_summary() {
    log_info "部署摘要:"
    log_info "  环境: $ENVIRONMENT"
    log_info "  镜像: $FULL_IMAGE_NAME"
    log_info "  命名空间: $KUBE_NAMESPACE"
    
    if [ -n "$SCALE" ]; then
        log_info "  副本数: $SCALE"
    fi
    
    if [ "$CANARY" = "true" ]; then
        log_info "  部署类型: 灰度部署"
    else
        log_info "  部署类型: 标准部署"
    fi
    
    log_info "  部署时间: $(date)"
    
    # 显示访问地址
    if [ "$ENVIRONMENT" = "prod" ]; then
        log_info "  访问地址: http://bigscreen.ljwx.local"
    else
        log_info "  访问地址: http://bigscreen-$ENVIRONMENT.ljwx.local"
    fi
}

# 主函数
main() {
    log_info "LJWX BigScreen 多架构部署工具 v1.3.1"
    log_info "=============================================="
    
    # 解析参数
    parse_args "$@"
    
    # 检查前置条件
    check_prerequisites
    
    # 设置上下文
    setup_context
    
    # 准备配置
    prepare_deployment_config
    
    # 执行部署
    execute_deployment
    
    # 显示摘要 (仅在标准部署时显示)
    if [ -z "$OPERATION" ] && [ -z "$ROLLBACK" ]; then
        show_deployment_summary
    fi
    
    log_info "🎉 部署操作完成！"
}

# 捕获中断信号
trap 'log_error "部署被中断"; exit 1' INT TERM

# 执行主函数
main "$@"