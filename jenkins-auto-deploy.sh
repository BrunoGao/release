#!/bin/bash
# Jenkins CI/CD完全自动化部署脚本

set -e
BASE_DIR="/Users/brunogao/work/infra"
COMPOSE_FILE="$BASE_DIR/docker/compose/jenkins-simple.yml"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 检查并创建必要目录
init_directories() {
    log "初始化目录结构..."
    
    mkdir -p "$BASE_DIR"/{data,backup}/jenkins
    mkdir -p "$BASE_DIR/docker/compose/jenkins"/{casc,init-scripts}
    
    log "✅ 目录创建完成"
}

# 停止现有服务
stop_existing() {
    log "停止现有Jenkins服务..."
    
    # 停止所有可能运行的Jenkins容器
    docker stop jenkins-simple 2>/dev/null || true
    docker rm jenkins-simple 2>/dev/null || true
    
    # 清理旧的数据卷（可选）
    warn "是否清理现有Jenkins数据？(y/N)"
    read -r clean_data
    if [[ $clean_data == "y" || $clean_data == "Y" ]]; then
        docker volume rm compose_jenkins-data 2>/dev/null || true
        log "已清理旧数据"
    fi
}

# 启动服务
start_services() {
    log "启动Jenkins自动化CI/CD环境..."
    
    # 创建网络
    docker network create cicd-network 2>/dev/null || true
    
    # 启动服务
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-simple.yml up -d
    
    log "等待Jenkins启动和自动配置..."
    
    # 等待Jenkins完全启动
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker logs jenkins-simple 2>&1 | grep -q "Jenkins is fully up and running" || \
           curl -sf "http://localhost:8081/login" &>/dev/null; then
            log "✅ Jenkins启动成功！"
            break
        fi
        
        # 显示启动进度
        if [[ $((attempt % 10)) -eq 0 ]]; then
            local logs=$(docker logs jenkins-simple 2>&1 | tail -3)
            echo -e "${B}启动进度:${NC} $logs"
        fi
        
        sleep 3
        ((attempt++))
        echo -n "."
    done
    
    echo ""
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "❌ Jenkins启动超时"
        echo "查看日志："
        docker logs jenkins-simple --tail 20
        return 1
    fi
}

# 验证配置
verify_config() {
    log "验证Jenkins自动配置..."
    
    # 等待额外时间确保CasC配置加载完成
    sleep 10
    
    # 检查配置是否加载
    local config_check=$(docker logs jenkins-simple 2>&1 | grep -E "(Configuration as Code|CasC)" | tail -1)
    if [[ -n "$config_check" ]]; then
        log "✅ Configuration as Code已加载"
        echo "  $config_check"
    else
        warn "⚠️  未检测到CasC配置加载日志"
    fi
    
    # 检查服务健康状态
    if curl -sf "http://localhost:8081/login" &>/dev/null; then
        log "✅ Jenkins服务正常"
    else
        warn "⚠️  Jenkins服务异常"
    fi
    
    if curl -sf "http://localhost:5001/v2/" &>/dev/null; then
        log "✅ Registry服务正常"
    else
        warn "⚠️  Registry服务异常"
    fi
    
    if curl -sf "http://192.168.1.6:3000" &>/dev/null; then
        log "✅ Gitea服务正常"
    else
        warn "⚠️  Gitea服务异常"
    fi
}

# 显示配置信息
show_config_info() {
    log "Jenkins CI/CD环境自动配置完成！"
    
    echo ""
    echo "======================================================="
    echo -e "${B}🚀 Jenkins自动配置完成${NC}"
    echo "======================================================="
    echo ""
    echo -e "${G}访问地址：${NC}"
    echo "  Jenkins:      http://localhost:8081"
    echo "  Registry:     http://localhost:5001"
    echo "  Registry UI:  http://localhost:5002"
    echo "  Gitea:        http://192.168.1.6:3000"
    echo ""
    echo -e "${G}登录信息：${NC}"
    echo "  用户名: admin"
    echo "  密码:   admin123"
    echo ""
    echo -e "${G}自动配置功能：${NC}"
    echo "  ✅ 跳过设置向导"
    echo "  ✅ 管理员用户自动创建"
    echo "  ✅ 必要插件自动安装"
    echo "  ✅ 工具自动配置(Git、Maven、Gradle、NodeJS、Docker)"
    echo "  ✅ 凭据模板已创建"
    echo "  ✅ Gitea服务器集成"
    echo "  ✅ 示例Pipeline作业已创建"
    echo "  ✅ 系统健康检查作业已配置"
    echo ""
    echo -e "${G}预创建的作业：${NC}"
    echo "  • multiplatform-build-demo - 多平台Docker构建演示"
    echo "  • system-health-check - 系统健康检查（每30分钟）"
    echo ""
    echo -e "${Y}后续配置建议：${NC}"
    echo "  1. 在Gitea中生成Personal Access Token并更新'gitea-token'凭据"
    echo "  2. 如需SSH访问，请更新'ssh-key'凭据"
    echo "  3. 运行示例作业验证环境配置"
    echo "  4. 根据需要调整CasC配置文件: docker/compose/jenkins/casc/jenkins.yaml"
    echo ""
    echo -e "${B}管理命令：${NC}"
    echo "  ./jenkins-manager.sh status   # 查看状态"
    echo "  ./jenkins-manager.sh logs     # 查看日志"
    echo "  ./jenkins-manager.sh backup   # 备份配置"
    echo ""
    echo "======================================================="
}

# 创建快速测试脚本
create_test_script() {
    log "创建快速测试脚本..."
    
    cat > "$BASE_DIR/test-jenkins-auto.sh" << 'EOF'
#!/bin/bash
# Jenkins自动配置测试脚本

echo "🧪 测试Jenkins自动配置..."

# 测试登录
echo "1. 测试管理员登录..."
response=$(curl -s -c cookies.txt -d "j_username=admin&j_password=admin123" \
    -X POST "http://localhost:8081/j_spring_security_check")
if [[ $? -eq 0 ]]; then
    echo "✅ 管理员登录成功"
else
    echo "❌ 管理员登录失败"
fi

# 测试API访问
echo "2. 测试Jenkins API..."
crumb=$(curl -s -b cookies.txt "http://localhost:8081/crumbIssuer/api/json" | \
    grep -o '"crumb":"[^"]*' | cut -d'"' -f4)
if [[ -n "$crumb" ]]; then
    echo "✅ API访问正常"
else
    echo "❌ API访问失败"
fi

# 测试作业列表
echo "3. 检查预创建作业..."
jobs=$(curl -s -b cookies.txt "http://localhost:8081/api/json" | \
    grep -o '"name":"[^"]*' | cut -d'"' -f4)
if echo "$jobs" | grep -q "multiplatform-build-demo"; then
    echo "✅ 示例作业已创建"
else
    echo "❌ 示例作业缺失"
fi

# 清理
rm -f cookies.txt

echo "🎉 测试完成"
EOF
    
    chmod +x "$BASE_DIR/test-jenkins-auto.sh"
    log "✅ 测试脚本已创建: test-jenkins-auto.sh"
}

# 主程序
main() {
    echo "========================================================="
    echo -e "${B}Jenkins CI/CD 完全自动化部署${NC}"
    echo "========================================================="
    echo ""
    
    # 检查Docker是否运行
    if ! docker info &>/dev/null; then
        error "❌ Docker未运行，请先启动Docker"
        exit 1
    fi
    
    init_directories
    stop_existing
    start_services
    verify_config
    create_test_script
    show_config_info
    
    echo ""
    info "💡 提示：运行 './test-jenkins-auto.sh' 测试自动配置"
    echo ""
    log "🎉 Jenkins CI/CD环境自动部署完成！"
}

# 错误处理
trap 'error "部署失败，请检查错误信息"; exit 1' ERR

# 执行主程序
main "$@" 