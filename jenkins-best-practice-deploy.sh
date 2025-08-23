#!/bin/bash
# Jenkins最佳实践完全自动化部署脚本

set -e
BASE_DIR="/Users/brunogao/work/infra"
COMPOSE_FILE="$BASE_DIR/docker/compose/jenkins-auto-config.yml"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
C='\033[0;36m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }
cyan() { echo -e "${C}[STEP]${NC} $1"; }

# 显示欢迎信息
show_banner() {
    echo ""
    echo "============================================================"
    echo -e "${C}🚀 Jenkins CI/CD 最佳实践自动化部署${NC}"
    echo "============================================================"
    echo -e "${G}✅ 自动安装80+插件${NC}"
    echo -e "${G}✅ Configuration as Code (CasC)完全自动配置${NC}"
    echo -e "${G}✅ 工具自动配置: JDK/Maven/Gradle/NodeJS/Docker/Python${NC}"
    echo -e "${G}✅ 云配置: Docker Cloud + Kubernetes Cloud${NC}"
    echo -e "${G}✅ 凭据模板: Gitea/Registry/SSH/K8s等${NC}"
    echo -e "${G}✅ 预创建作业: 多平台构建/系统监控/镜像模板${NC}"
    echo -e "${G}✅ 完整持久化: 数据不丢失${NC}"
    echo "============================================================"
    echo ""
}

# 检查前置条件
check_prerequisites() {
    cyan "检查前置条件..."
    
    # 检查Docker
    if ! docker info &>/dev/null; then
        error "❌ Docker未运行，请先启动Docker"
        exit 1
    fi
    log "✅ Docker运行正常"
    
    # 检查Docker Compose
    if ! docker-compose --version &>/dev/null; then
        error "❌ Docker Compose未安装"
        exit 1
    fi
    log "✅ Docker Compose可用"
    
    # 检查磁盘空间(至少需要5GB)
    local available=$(df / | awk 'NR==2{print $4}')
    if [[ $available -lt 5000000 ]]; then
        warn "⚠️  磁盘空间不足，建议至少5GB可用空间"
    else
        log "✅ 磁盘空间充足"
    fi
}

# 清理现有环境
cleanup_existing() {
    cyan "清理现有Jenkins环境..."
    
    # 停止所有相关容器
    docker stop jenkins-simple jenkins-auto-config jenkins-persistent 2>/dev/null || true
    docker rm jenkins-simple jenkins-auto-config jenkins-persistent 2>/dev/null || true
    
    # 停止Registry容器
    docker stop jenkins-registry registry 2>/dev/null || true
    docker rm jenkins-registry registry 2>/dev/null || true
    
    log "✅ 现有环境已清理"
}

# 准备配置文件
prepare_configs() {
    cyan "准备配置文件..."
    
    # 创建必要目录
    mkdir -p "$BASE_DIR/docker/compose/jenkins"/{casc,init-scripts}
    mkdir -p "$BASE_DIR/data/jenkins"
    mkdir -p "$BASE_DIR/backup/jenkins"
    
    # 复制插件配置
    if [[ -f "$BASE_DIR/docker/compose/jenkins/plugins-best-practice.txt" ]]; then
        cp "$BASE_DIR/docker/compose/jenkins/plugins-best-practice.txt" \
           "$BASE_DIR/docker/compose/jenkins/plugins.txt"
        log "✅ 插件配置已准备 ($(wc -l < "$BASE_DIR/docker/compose/jenkins/plugins.txt") 个插件)"
    else
        error "❌ 插件配置文件不存在"
        exit 1
    fi
    
    # 复制CasC配置
    if [[ -f "$BASE_DIR/docker/compose/jenkins/casc/complete-config.yaml" ]]; then
        cp "$BASE_DIR/docker/compose/jenkins/casc/complete-config.yaml" \
           "$BASE_DIR/docker/compose/jenkins/casc/jenkins.yaml"
        log "✅ CasC配置已准备"
    else
        error "❌ CasC配置文件不存在"
        exit 1
    fi
    
    # 创建初始化脚本
    cat > "$BASE_DIR/docker/compose/jenkins/init-scripts/01-setup.groovy" << 'EOF'
#!/usr/bin/env groovy
// Jenkins自动化初始化脚本

import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// 设置系统消息
instance.setSystemMessage("""
🎉 Jenkins已完全自动配置！

📦 已安装插件: ${instance.pluginManager.plugins.size()} 个
🔧 工具配置: Git, JDK, Maven, Gradle, NodeJS, Docker, Python
☁️  云配置: Docker Cloud, Kubernetes Cloud  
🔐 凭据模板: Gitea, Registry, SSH, K8s等
📋 预创建作业: 多平台构建, 系统监控, 镜像模板
📚 管理文档: docs/jenkins-persistence-guide.md

🌐 访问地址: http://localhost:8081
👤 登录账号: admin / admin123
""")

// 保存配置
instance.save()

println "🎉 Jenkins自动化初始化完成!"
EOF
    
    log "✅ 初始化脚本已创建"
}

# 创建网络
create_network() {
    cyan "创建Docker网络..."
    
    docker network create cicd-network 2>/dev/null || {
        log "网络 cicd-network 已存在"
    }
    
    log "✅ Docker网络已准备"
}

# 启动服务
start_services() {
    cyan "启动Jenkins最佳实践配置..."
    
    cd "$BASE_DIR/docker/compose"
    
    # 启动服务
    docker-compose -f jenkins-auto-config.yml up -d
    
    log "✅ 服务已启动，等待初始化..."
}

# 监控启动进度
monitor_startup() {
    cyan "监控Jenkins启动和配置进度..."
    
    local max_attempts=120  # 增加等待时间以便插件安装
    local attempt=0
    local last_message=""
    
    echo "启动进度监控 (最多等待10分钟):"
    
    while [[ $attempt -lt $max_attempts ]]; do
        # 检查容器状态
        if ! docker ps --format "{{.Names}}" | grep -q "jenkins-auto-config"; then
            error "❌ Jenkins容器已停止"
            echo "容器日志:"
            docker logs jenkins-auto-config --tail 20
            return 1
        fi
        
        # 获取最新日志
        local current_logs=$(docker logs jenkins-auto-config 2>&1 | tail -5)
        
        # 检查启动完成
        if echo "$current_logs" | grep -q "Jenkins is fully up and running"; then
            log "🎉 Jenkins启动完成！"
            break
        fi
        
        # 显示进度信息
        if [[ $((attempt % 10)) -eq 0 ]]; then
            local current_message=""
            
            if echo "$current_logs" | grep -q "Downloading plugins"; then
                current_message="📦 正在下载插件..."
            elif echo "$current_logs" | grep -q "Installing plugins"; then
                current_message="🔧 正在安装插件..."
            elif echo "$current_logs" | grep -q "Configuration as Code"; then
                current_message="⚙️  正在加载CasC配置..."
            elif echo "$current_logs" | grep -q "Initializing"; then
                current_message="🚀 正在初始化Jenkins..."
            elif echo "$current_logs" | grep -q "Started"; then
                current_message="✨ 正在完成启动..."
            else
                current_message="⏳ 启动中... (${attempt}/${max_attempts})"
            fi
            
            if [[ "$current_message" != "$last_message" ]]; then
                echo "$current_message"
                last_message="$current_message"
            fi
        fi
        
        sleep 5
        ((attempt++))
        
        # 显示进度点
        if [[ $((attempt % 2)) -eq 0 ]]; then
            echo -n "."
        fi
    done
    
    echo ""
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "❌ Jenkins启动超时"
        echo "最新日志:"
        docker logs jenkins-auto-config --tail 30
        return 1
    fi
    
    return 0
}

# 验证配置
verify_configuration() {
    cyan "验证Jenkins自动配置..."
    
    # 等待额外时间确保CasC配置完全加载
    sleep 15
    
    local checks_passed=0
    local total_checks=6
    
    # 检查Jenkins可访问性
    if curl -sf "http://localhost:8081/login" &>/dev/null; then
        log "✅ Jenkins Web界面可访问"
        ((checks_passed++))
    else
        warn "⚠️  Jenkins Web界面暂时不可访问"
    fi
    
    # 检查CasC配置加载
    local casc_logs=$(docker logs jenkins-auto-config 2>&1 | grep -i "configuration.*code\|casc")
    if [[ -n "$casc_logs" ]]; then
        log "✅ Configuration as Code已加载"
        ((checks_passed++))
    else
        warn "⚠️  未检测到CasC加载日志"
    fi
    
    # 检查插件安装
    local plugin_count=$(docker exec jenkins-auto-config find /var/jenkins_home/plugins -name "*.jpi" 2>/dev/null | wc -l)
    if [[ $plugin_count -gt 50 ]]; then
        log "✅ 插件安装成功 ($plugin_count 个)"
        ((checks_passed++))
    else
        warn "⚠️  插件安装可能不完整 ($plugin_count 个)"
    fi
    
    # 检查Registry服务
    if curl -sf "http://localhost:5001/v2/" &>/dev/null; then
        log "✅ Docker Registry服务正常"
        ((checks_passed++))
    else
        warn "⚠️  Docker Registry服务异常"
    fi
    
    # 检查数据持久化
    if [[ -f "$BASE_DIR/data/jenkins/config.xml" ]]; then
        log "✅ 数据持久化正常"
        ((checks_passed++))
    else
        warn "⚠️  数据持久化可能有问题"
    fi
    
    # 检查初始化脚本执行
    local init_logs=$(docker logs jenkins-auto-config 2>&1 | grep "自动化初始化完成")
    if [[ -n "$init_logs" ]]; then
        log "✅ 初始化脚本执行成功"
        ((checks_passed++))
    else
        warn "⚠️  初始化脚本执行状态未知"
    fi
    
    echo ""
    log "验证结果: $checks_passed/$total_checks 项检查通过"
    
    if [[ $checks_passed -ge 4 ]]; then
        log "🎉 Jenkins配置验证基本通过"
        return 0
    else
        warn "⚠️  部分配置可能需要手动检查"
        return 1
    fi
}

# 显示配置完成信息
show_completion_info() {
    echo ""
    echo "============================================================"
    echo -e "${G}🎉 Jenkins最佳实践配置部署完成！${NC}"
    echo "============================================================"
    echo ""
    echo -e "${C}📡 访问信息:${NC}"
    echo "   🌐 Jenkins Web界面: http://localhost:8081"
    echo "   📦 Docker Registry: http://localhost:5001"
    echo "   👤 管理员账号: admin"
    echo "   🔑 管理员密码: admin123"
    echo ""
    echo -e "${C}✨ 自动配置完成:${NC}"
    echo "   📦 已安装 80+ CI/CD插件"
    echo "   🔧 工具: JDK21/17/11, Maven3.9/3.8, Gradle8/7, NodeJS20/18, Docker, Python"
    echo "   ☁️  云平台: Docker Cloud + Kubernetes Cloud"
    echo "   🔐 凭据模板: Gitea/Registry/SSH/K8s/AWS/Azure"
    echo "   📋 预创建作业: 多平台构建演示/系统监控/镜像构建模板"
    echo ""
    echo -e "${C}📚 管理工具:${NC}"
    echo "   ./jenkins-persistence-manager.sh    # 持久化管理"
    echo "   ./jenkins-manager.sh               # 日常管理"
    echo "   docker logs jenkins-auto-config    # 查看日志"
    echo ""
    echo -e "${C}📖 文档和配置:${NC}"
    echo "   docs/jenkins-persistence-guide.md  # 持久化指南"
    echo "   docker/compose/jenkins/casc/       # CasC配置目录"
    echo "   docker/compose/jenkins/plugins.txt # 插件列表"
    echo ""
    echo -e "${C}🔄 下一步建议:${NC}"
    echo "   1. 访问Jenkins Web界面验证配置"
    echo "   2. 在Gitea中生成Personal Access Token"
    echo "   3. 更新凭据中的实际Token和密钥"
    echo "   4. 运行示例作业测试功能"
    echo "   5. 根据需要调整CasC配置"
    echo ""
    echo "============================================================"
    
    # 显示快速验证命令
    echo -e "${Y}💡 快速验证:${NC}"
    echo "   curl http://localhost:8081/login"
    echo "   docker exec jenkins-auto-config ls -la /var/jenkins_home/plugins | wc -l"
    echo ""
}

# 故障排除信息
show_troubleshooting() {
    echo ""
    echo -e "${Y}🔧 故障排除:${NC}"
    echo ""
    echo "如果遇到问题，请检查:"
    echo "  1. Docker日志: docker logs jenkins-auto-config"
    echo "  2. 插件安装: docker exec jenkins-auto-config ls /var/jenkins_home/plugins"
    echo "  3. CasC配置: docker exec jenkins-auto-config cat /var/jenkins_home/casc_configs/jenkins.yaml"
    echo "  4. 网络连通: docker network ls | grep cicd"
    echo "  5. 磁盘空间: df -h"
    echo ""
    echo "常见解决方案:"
    echo "  • 重新部署: $0"
    echo "  • 查看完整日志: docker logs jenkins-auto-config --tail 100"
    echo "  • 手动重启: docker restart jenkins-auto-config"
    echo "  • 进入容器调试: docker exec -it jenkins-auto-config bash"
    echo ""
    echo "获取帮助:"
    echo "  📖 查看文档: docs/jenkins-persistence-guide.md"
    echo "  📧 报告问题: 包含具体错误日志"
}

# 主程序
main() {
    show_banner
    
    # 执行部署步骤
    check_prerequisites
    cleanup_existing
    prepare_configs
    create_network
    start_services
    
    # 监控和验证
    if monitor_startup; then
        if verify_configuration; then
            show_completion_info
        else
            warn "配置验证发现问题，但Jenkins已启动"
            show_completion_info
            show_troubleshooting
        fi
    else
        error "Jenkins启动失败"
        show_troubleshooting
        exit 1
    fi
}

# 错误处理
trap 'error "部署过程中发生错误，请检查日志"; show_troubleshooting; exit 1' ERR

# 执行主程序
main "$@" 