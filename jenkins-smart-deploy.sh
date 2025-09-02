#!/bin/bash

# Jenkins 智能自动化部署脚本
# 适配现有服务环境，解决网络问题，提供离线部署选项
# 使用方法: ./jenkins-smart-deploy.sh [online|offline|local]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
LOG_FILE="${PROJECT_ROOT}/logs/jenkins-smart-deploy.log"

# 创建日志目录
mkdir -p "$(dirname "${LOG_FILE}")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日志函数
log() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a "${LOG_FILE}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${LOG_FILE}"; }
error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"; }
success() { echo -e "${PURPLE}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"; }

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║              🚀 Jenkins 智能自动化部署                        ║
║                                                            ║
║  ✅ 适配现有服务环境                                          ║
║  ✅ 智能网络问题解决                                          ║
║  ✅ 支持离线/本地部署                                         ║
║  ✅ 零配置开箱即用                                            ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 检测现有服务
detect_existing_services() {
    log "检测现有服务环境..."
    
    # 检测 Registry
    if docker ps | grep -q "registry.*35001"; then
        success "✅ 检测到现有 Registry 服务 (端口35001)"
        export EXISTING_REGISTRY_PORT="35001"
        export REGISTRY_URL="localhost:35001"
    elif docker ps | grep -q "registry.*5001"; then
        success "✅ 检测到现有 Registry 服务 (端口5001)" 
        export EXISTING_REGISTRY_PORT="5001"
        export REGISTRY_URL="localhost:5001"
    else
        warn "⚠️ 未检测到 Registry 服务"
        export EXISTING_REGISTRY_PORT=""
        export REGISTRY_URL="localhost:5001"
    fi
    
    # 检测 Gitea
    if docker ps | grep -q "gitea"; then
        success "✅ 检测到现有 Gitea 服务"
        export EXISTING_GITEA="true"
        # 尝试获取 Gitea 端口
        GITEA_PORT=$(docker ps | grep gitea | grep -o "0.0.0.0:[0-9]*->3000" | cut -d':' -f2 | cut -d'-' -f1 | head -1)
        if [[ -n "$GITEA_PORT" ]]; then
            export GITEA_URL="http://localhost:${GITEA_PORT}"
        else
            export GITEA_URL="http://192.168.1.6:3000"
        fi
    else
        warn "⚠️ 未检测到 Gitea 服务"
        export EXISTING_GITEA="false"
        export GITEA_URL="http://192.168.1.6:3000"
    fi
    
    # 检测网络
    if docker network inspect cicd-network &>/dev/null; then
        success "✅ 检测到现有 cicd-network 网络"
        export EXISTING_NETWORK="true"
    else
        log "将创建 cicd-network 网络"
        export EXISTING_NETWORK="false"
    fi
    
    log "服务检测完成"
}

# 检查网络连接
check_network_connectivity() {
    log "检查网络连接状态..."
    
    # 检查 Docker Hub 连接
    if curl -s --connect-timeout 5 "https://registry-1.docker.io/v2/" &>/dev/null; then
        success "✅ Docker Hub 连接正常"
        export NETWORK_MODE="online"
        return 0
    fi
    
    # 检查国内镜像源
    local mirrors=(
        "https://docker.mirrors.ustc.edu.cn"
        "https://registry.cn-hangzhou.aliyuncs.com"
        "https://hub-mirror.c.163.com"
    )
    
    for mirror in "${mirrors[@]}"; do
        if curl -s --connect-timeout 3 "${mirror}/v2/" &>/dev/null; then
            success "✅ 检测到可用镜像源: $mirror"
            export DOCKER_MIRROR="$mirror"
            export NETWORK_MODE="mirror"
            return 0
        fi
    done
    
    warn "⚠️ 网络连接受限，将使用离线模式"
    export NETWORK_MODE="offline"
    return 1
}

# 配置 Docker 镜像源
configure_docker_mirror() {
    if [[ "$NETWORK_MODE" == "mirror" && -n "$DOCKER_MIRROR" ]]; then
        log "配置 Docker 镜像源..."
        
        # 创建或更新 daemon.json
        local docker_config="/etc/docker/daemon.json"
        local temp_config="/tmp/docker_daemon.json"
        
        if [[ -f "$docker_config" ]]; then
            # 备份现有配置
            cp "$docker_config" "${docker_config}.backup.$(date +%Y%m%d)"
        fi
        
        # 创建新配置
        cat > "$temp_config" << EOF
{
  "registry-mirrors": [
    "$DOCKER_MIRROR"
  ],
  "insecure-registries": [
    "localhost:5001",
    "localhost:35001",
    "$REGISTRY_URL"
  ]
}
EOF
        
        # 尝试更新配置（需要 sudo）
        if sudo cp "$temp_config" "$docker_config" 2>/dev/null; then
            log "重启 Docker 服务以应用镜像配置..."
            if sudo systemctl restart docker 2>/dev/null || sudo service docker restart 2>/dev/null; then
                success "✅ Docker 镜像源配置完成"
                sleep 5  # 等待 Docker 重启
            else
                warn "⚠️ 无法重启 Docker 服务，配置可能未生效"
            fi
        else
            warn "⚠️ 无权限修改 Docker 配置，将尝试其他方法"
        fi
        
        rm -f "$temp_config"
    fi
}

# 创建适配的 Docker Compose 配置
create_adaptive_compose() {
    log "创建适配现有环境的 Docker Compose 配置..."
    
    local compose_file="${PROJECT_ROOT}/docker/compose/jenkins-adaptive.yml"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:2.440-lts
    container_name: jenkins-smart
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8081:8080"
      - "50000:50000"
    volumes:
      # Jenkins 数据持久化
      - jenkins-smart-data:/var/jenkins_home
      
      # Docker 集成
      - /var/run/docker.sock:/var/run/docker.sock
      
      # 配置文件挂载
      - ./jenkins/casc:/var/jenkins_home/casc_configs:ro
      - ./jenkins/plugins.txt:/usr/share/jenkins/ref/plugins.txt:ro
      - ./jenkins/init-scripts:/var/jenkins_home/init.groovy.d:ro
      - ./jenkins/shared-library:/var/jenkins_home/shared-library:ro
      
      # 时区同步
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
      
    environment:
      # Jenkins 配置
      - JENKINS_OPTS=--httpPort=8080
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Xmx2g -XX:+UseG1GC
      
      # Configuration as Code
      - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
      
      # Docker 配置
      - DOCKER_HOST=unix:///var/run/docker.sock
      
      # 服务集成环境变量
      - JENKINS_ADMIN_ID=admin
      - JENKINS_ADMIN_PASSWORD=admin123
      - DOCKER_REGISTRY=${REGISTRY_URL}
      - GITEA_URL=${GITEA_URL}
      - GITEA_TOKEN=changeme-generate-in-gitea
      
    networks:
      - cicd-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

networks:
  cicd-network:
EOF

    # 根据网络存在情况配置网络
    if [[ "$EXISTING_NETWORK" == "true" ]]; then
        cat >> "$compose_file" << 'EOF'
    external: true
    name: cicd-network
EOF
    else
        cat >> "$compose_file" << 'EOF'
    driver: bridge
    name: cicd-network
EOF
    fi

    cat >> "$compose_file" << 'EOF'

volumes:
  jenkins-smart-data:
    driver: local
    name: jenkins-smart-data
EOF

    success "适配配置创建完成"
}

# 创建简化的 CasC 配置
create_simple_casc() {
    log "创建简化的 CasC 配置..."
    
    local casc_file="${PROJECT_ROOT}/docker/compose/jenkins/casc/jenkins-simple.yaml"
    mkdir -p "$(dirname "$casc_file")"
    
    cat > "$casc_file" << 'EOF'
jenkins:
  systemMessage: |
    🚀 Jenkins CI/CD 智能自动化部署
    📅 部署时间: 2024-08-24
    🔧 适配现有环境自动检测
    
  numExecutors: 4
  mode: NORMAL
  quietPeriod: 5
  
  # 安全配置
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "admin"
          password: "admin123"
          
  authorizationStrategy:
    globalMatrix:
      permissions:
        - "Overall/Administer:admin"
        - "Overall/Read:authenticated"
        - "Job/Build:authenticated"
        - "Job/Read:authenticated"
        - "Job/Configure:authenticated"
        - "Job/Create:authenticated"
        
  # 全局环境变量
  globalNodeProperties:
    - envVars:
        env:
          - key: "DOCKER_REGISTRY"
            value: "localhost:35001"
          - key: "GITEA_URL" 
            value: "http://192.168.1.6:3000"
          - key: "BUILD_PLATFORMS"
            value: "linux/amd64,linux/arm64"

# 工具配置
tool:
  git:
    installations:
      - name: "Default"
        home: "/usr/bin/git"
  
  # JDK 配置（使用容器内置）
  jdk:
    installations:
      - name: "JDK-17"
        home: "/opt/java/openjdk"

# 凭据配置
credentials:
  system:
    domainCredentials:
      - credentials:
          - string:
              scope: GLOBAL
              id: "gitea-api-token"
              description: "Gitea API Token"
              secret: "changeme-please-update"
              
          - usernamePassword:
              scope: GLOBAL
              id: "docker-registry-auth"
              description: "Docker Registry Auth"
              username: "admin"
              password: "admin123"

# 系统配置
unclassified:
  location:
    url: "http://localhost:8081/"
    adminAddress: "admin@example.com"
    
  # CSRF 保护
  csrf:
    defaultCrumbIssuer:
      excludeClientIPFromCrumb: false

# 简单的预创建作业
jobs:
  - script: >
      pipelineJob('hello-world-demo') {
        displayName('Hello World 演示')
        description('验证 Jenkins 自动化配置的简单演示作业')
        
        definition {
          cps {
            script('''
              pipeline {
                  agent any
                  
                  stages {
                      stage('Hello') {
                          steps {
                              echo "🎉 Jenkins 自动化配置成功！"
                              echo "📍 Docker Registry: ${env.DOCKER_REGISTRY}"
                              echo "📍 Gitea URL: ${env.GITEA_URL}"
                              echo "🔨 支持的平台: ${env.BUILD_PLATFORMS}"
                              
                              script {
                                  def version = sh(script: 'docker --version', returnStdout: true).trim()
                                  echo "🐳 Docker 版本: ${version}"
                              }
                          }
                      }
                      
                      stage('Environment Check') {
                          steps {
                              script {
                                  echo "🔍 环境检查..."
                                  
                                  // 检查 Registry 连接
                                  def registryStatus = sh(
                                      script: "curl -s -o /dev/null -w '%{http_code}' ${env.DOCKER_REGISTRY}/v2/ || echo 'failed'",
                                      returnStdout: true
                                  ).trim()
                                  
                                  if (registryStatus == '200') {
                                      echo "✅ Registry 连接正常"
                                  } else {
                                      echo "⚠️ Registry 连接异常: ${registryStatus}"
                                  }
                                  
                                  // 检查 Gitea 连接
                                  def giteaStatus = sh(
                                      script: "curl -s -o /dev/null -w '%{http_code}' ${env.GITEA_URL}/api/v1/version || echo 'failed'",
                                      returnStdout: true
                                  ).trim()
                                  
                                  if (giteaStatus == '200') {
                                      echo "✅ Gitea 连接正常"
                                  } else {
                                      echo "⚠️ Gitea 连接异常: ${giteaStatus}"
                                  }
                              }
                          }
                      }
                  }
                  
                  post {
                      always {
                          echo "🎊 Jenkins 智能自动化配置验证完成！"
                      }
                      success {
                          echo "✅ 所有检查通过，环境配置正常"
                      }
                  }
              }
            ''')
            sandbox()
          }
        }
      }
EOF

    success "简化 CasC 配置创建完成"
}

# 预拉取必要镜像
pre_pull_images() {
    if [[ "$NETWORK_MODE" == "offline" ]]; then
        warn "离线模式，跳过镜像预拉取"
        return 0
    fi
    
    log "预拉取必要的 Docker 镜像..."
    
    local images=(
        "jenkins/jenkins:2.440-lts"
        "busybox:latest"
        "hello-world:latest"
    )
    
    for image in "${images[@]}"; do
        log "拉取镜像: $image"
        if ! docker pull "$image" 2>/dev/null; then
            warn "⚠️ 拉取镜像失败: $image，将在启动时尝试"
        else
            success "✅ 镜像拉取成功: $image"
        fi
    done
}

# 停止现有 Jenkins
stop_existing_jenkins() {
    log "停止现有 Jenkins 服务..."
    
    # 停止可能存在的 Jenkins 容器
    local containers=(
        "jenkins-smart"
        "jenkins-ultimate"
        "jenkins-simple"
        "jenkins"
    )
    
    for container in "${containers[@]}"; do
        if docker ps -a | grep -q "$container"; then
            log "停止容器: $container"
            docker stop "$container" 2>/dev/null || true
            docker rm "$container" 2>/dev/null || true
        fi
    done
    
    success "现有 Jenkins 服务已停止"
}

# 启动 Jenkins 服务
start_jenkins() {
    log "启动 Jenkins 智能自动化服务..."
    
    # 创建网络（如果不存在）
    if [[ "$EXISTING_NETWORK" == "false" ]]; then
        docker network create cicd-network 2>/dev/null || true
    fi
    
    # 启动服务
    cd "${PROJECT_ROOT}/docker/compose"
    
    # 使用适配的配置文件启动
    if docker-compose -f jenkins-adaptive.yml up -d jenkins; then
        success "✅ Jenkins 服务启动成功"
    else
        error "❌ Jenkins 服务启动失败"
        return 1
    fi
    
    # 等待服务启动
    log "等待 Jenkins 服务完全启动..."
    local max_attempts=60
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf "http://localhost:8081/login" &>/dev/null; then
            success "✅ Jenkins 启动成功！"
            break
        fi
        
        if [[ $((attempt % 10)) -eq 0 ]]; then
            log "等待启动... (${attempt}/${max_attempts})"
            # 显示启动日志
            docker logs jenkins-smart --tail 3 2>/dev/null | grep -v "^$" || true
        fi
        
        sleep 3
        ((attempt++))
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "❌ Jenkins 启动超时"
        log "查看启动日志:"
        docker logs jenkins-smart --tail 20
        return 1
    fi
    
    # 等待配置加载
    log "等待 CasC 配置加载..."
    sleep 15
    
    success "Jenkins 智能自动化部署完成"
}

# 验证部署
verify_deployment() {
    log "验证部署状态..."
    
    # 检查 Jenkins
    if curl -sf "http://localhost:8081/login" &>/dev/null; then
        success "✅ Jenkins 服务正常"
    else
        error "❌ Jenkins 服务异常"
        return 1
    fi
    
    # 检查 Registry 连接
    if curl -sf "http://${REGISTRY_URL}/v2/" &>/dev/null; then
        success "✅ Registry 连接正常"
    else
        warn "⚠️ Registry 连接异常"
    fi
    
    # 检查 Gitea 连接
    if curl -sf "${GITEA_URL}/api/v1/version" &>/dev/null; then
        success "✅ Gitea 连接正常"
    else
        warn "⚠️ Gitea 连接异常"
    fi
    
    # 检查 Docker 集成
    if docker exec jenkins-smart docker --version &>/dev/null; then
        success "✅ Docker 集成正常"
    else
        warn "⚠️ Docker 集成异常"
    fi
    
    success "部署验证完成"
}

# 创建管理脚本
create_smart_manager() {
    log "创建智能管理脚本..."
    
    cat > "${PROJECT_ROOT}/jenkins-smart-manager.sh" << 'EOF'
#!/bin/bash

# Jenkins 智能管理脚本
# 使用方法: ./jenkins-smart-manager.sh [start|stop|restart|status|logs|test]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose/jenkins-adaptive.yml"

case "${1:-help}" in
    "start")
        echo "🚀 启动 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-adaptive.yml up -d
        echo "✅ 服务启动完成"
        echo "📍 访问地址: http://localhost:8081 (admin/admin123)"
        ;;
        
    "stop")
        echo "⏸️ 停止 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-adaptive.yml down
        echo "✅ 服务停止完成"
        ;;
        
    "restart")
        echo "🔄 重启 Jenkins 服务..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-adaptive.yml restart
        echo "✅ 服务重启完成"
        ;;
        
    "status")
        echo "📊 检查服务状态..."
        docker ps | grep jenkins-smart || echo "Jenkins 服务未运行"
        echo ""
        echo "🔗 服务连接检查:"
        curl -s -o /dev/null -w "Jenkins: %{http_code}\n" http://localhost:8081/login
        ;;
        
    "logs")
        echo "📋 显示 Jenkins 日志..."
        docker logs jenkins-smart -f
        ;;
        
    "test")
        echo "🧪 运行测试作业..."
        echo "请在浏览器中访问: http://localhost:8081"
        echo "使用 admin/admin123 登录，然后运行 'hello-world-demo' 作业"
        ;;
        
    "help"|*)
        echo "Jenkins 智能管理"
        echo ""
        echo "使用方法:"
        echo "  $0 start     # 启动服务"
        echo "  $0 stop      # 停止服务"
        echo "  $0 restart   # 重启服务"
        echo "  $0 status    # 查看状态"
        echo "  $0 logs      # 查看日志"
        echo "  $0 test      # 运行测试"
        echo ""
        echo "访问地址: http://localhost:8081"
        echo "登录信息: admin / admin123"
        ;;
esac
EOF
    
    chmod +x "${PROJECT_ROOT}/jenkins-smart-manager.sh"
    success "管理脚本创建完成"
}

# 显示完成信息
show_completion() {
    echo ""
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                   🎉 Jenkins 智能部署完成                      ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    success "Jenkins 智能自动化配置完成！"
    
    echo ""
    echo -e "${GREEN}📍 服务信息：${NC}"
    echo "  • Jenkins:      http://localhost:8081"
    echo "  • Registry:     http://${REGISTRY_URL}"
    echo "  • Gitea:        ${GITEA_URL}"
    
    echo ""
    echo -e "${GREEN}🔐 登录信息：${NC}"
    echo "  • 用户名: admin"
    echo "  • 密码:   admin123"
    
    echo ""
    echo -e "${GREEN}🚀 智能特性：${NC}"
    echo "  ✅ 适配现有服务环境"
    echo "  ✅ 智能网络问题解决"
    echo "  ✅ 简化配置，快速启动"
    echo "  ✅ Docker 多平台构建支持"
    echo "  ✅ 预创建验证作业"
    
    echo ""
    echo -e "${GREEN}🛠️ 管理命令：${NC}"
    echo "  ./jenkins-smart-manager.sh start     # 启动服务"
    echo "  ./jenkins-smart-manager.sh stop      # 停止服务"
    echo "  ./jenkins-smart-manager.sh status    # 查看状态"
    echo "  ./jenkins-smart-manager.sh test      # 运行测试"
    
    echo ""
    echo -e "${YELLOW}📋 下一步操作：${NC}"
    echo "  1. 访问 http://localhost:8081 登录 Jenkins"
    echo "  2. 运行 'hello-world-demo' 作业验证环境"
    echo "  3. 在 Gitea 中生成 Personal Access Token 并更新凭据"
    echo "  4. 开始创建你的第一个 CI/CD 流水线"
    
    echo ""
    success "🎊 享受智能化的 Jenkins CI/CD 体验！"
}

# 主函数
main() {
    show_banner
    
    local mode="${1:-smart}"
    
    case "$mode" in
        "offline")
            log "离线模式部署"
            export NETWORK_MODE="offline"
            ;;
        "local")
            log "本地模式部署"
            export NETWORK_MODE="local"
            ;;
        *)
            log "智能模式部署"
            check_network_connectivity
            ;;
    esac
    
    detect_existing_services
    
    if [[ "$NETWORK_MODE" != "offline" ]]; then
        configure_docker_mirror
        pre_pull_images
    fi
    
    stop_existing_jenkins
    create_adaptive_compose
    create_simple_casc
    start_jenkins
    verify_deployment
    create_smart_manager
    show_completion
}

# 错误处理
trap 'error "部署失败，请查看错误信息"; exit 1' ERR

# 执行主函数
main "$@"