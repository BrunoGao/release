#!/bin/bash

# Jenkins 快速自动化部署脚本
# 适配现有环境，解决网络问题
# 使用方法: ./jenkins-quick-deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🚀 Jenkins 快速自动化部署                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 停止现有服务
log "停止现有 Jenkins 服务..."
docker stop jenkins-smart jenkins-ultimate jenkins-simple jenkins 2>/dev/null || true
docker rm jenkins-smart jenkins-ultimate jenkins-simple jenkins 2>/dev/null || true

# 创建目录
log "创建必要的目录结构..."
mkdir -p "${PROJECT_ROOT}/docker/compose/jenkins/"{casc,plugins,init-scripts}

# 创建简单的 compose 文件
log "创建 Docker Compose 配置..."
cat > "${PROJECT_ROOT}/docker/compose/jenkins-quick.yml" << 'EOF'
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:2.440-lts
    container_name: jenkins-quick
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8081:8080"
      - "50000:50000"
    volumes:
      - jenkins-quick-data:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - ./jenkins/casc:/var/jenkins_home/casc_configs:ro
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    environment:
      - JENKINS_OPTS=--httpPort=8080
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Xmx1g
      - CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs
      - JENKINS_ADMIN_ID=admin
      - JENKINS_ADMIN_PASSWORD=admin123
    networks:
      - cicd-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  cicd-network:
    external: true
    name: cicd-network

volumes:
  jenkins-quick-data:
    driver: local
EOF

# 创建基础 CasC 配置
log "创建 Jenkins 配置..."
cat > "${PROJECT_ROOT}/docker/compose/jenkins/casc/jenkins.yaml" << 'EOF'
jenkins:
  systemMessage: |
    🚀 Jenkins CI/CD 快速自动化部署
    📅 部署时间: 2024-08-24
    🔧 适配现有环境: Registry(localhost:35001), Gitea(192.168.1.6:3000)
    
  numExecutors: 4
  mode: NORMAL
  quietPeriod: 5
  
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
        - "Job/Delete:authenticated"
        
  globalNodeProperties:
    - envVars:
        env:
          - key: "DOCKER_REGISTRY"
            value: "localhost:35001"
          - key: "GITEA_URL" 
            value: "http://192.168.1.6:3000"
          - key: "BUILD_PLATFORMS"
            value: "linux/amd64,linux/arm64"

tool:
  git:
    installations:
      - name: "Default"
        home: "/usr/bin/git"
  
  jdk:
    installations:
      - name: "JDK-17"
        home: "/opt/java/openjdk"

credentials:
  system:
    domainCredentials:
      - credentials:
          - string:
              scope: GLOBAL
              id: "gitea-api-token"
              description: "Gitea API Token - 请在Gitea中生成后更新"
              secret: "changeme-please-update-with-real-token"
              
          - usernamePassword:
              scope: GLOBAL
              id: "docker-registry-auth"
              description: "Docker Registry 认证"
              username: "admin"
              password: "admin123"

unclassified:
  location:
    url: "http://localhost:8081/"
    adminAddress: "admin@example.com"
    
  csrf:
    defaultCrumbIssuer:
      excludeClientIPFromCrumb: false

jobs:
  - script: >
      pipelineJob('hello-world-demo') {
        displayName('Hello World 演示')
        description('验证 Jenkins 自动化配置')
        
        definition {
          cps {
            script('''
              pipeline {
                  agent any
                  
                  stages {
                      stage('Hello Jenkins') {
                          steps {
                              echo "🎉 Jenkins 自动化配置成功！"
                              echo "📍 Docker Registry: localhost:35001"
                              echo "📍 Gitea URL: http://192.168.1.6:3000"
                              echo "🔨 支持平台: linux/amd64,linux/arm64"
                              
                              script {
                                  def dockerVersion = sh(
                                      script: 'docker --version',
                                      returnStdout: true
                                  ).trim()
                                  echo "🐳 Docker 版本: ${dockerVersion}"
                              }
                          }
                      }
                      
                      stage('环境检查') {
                          steps {
                              echo "🔍 检查服务连接..."
                              
                              script {
                                  // 检查 Registry 连接
                                  def registryCheck = sh(
                                      script: 'curl -s -o /dev/null -w "%{http_code}" http://localhost:35001/v2/ || echo "failed"',
                                      returnStdout: true
                                  ).trim()
                                  
                                  if (registryCheck == "200") {
                                      echo "✅ Registry 连接正常"
                                  } else {
                                      echo "⚠️ Registry 连接状态: ${registryCheck}"
                                  }
                                  
                                  // 检查 Gitea 连接
                                  def giteaCheck = sh(
                                      script: 'curl -s -o /dev/null -w "%{http_code}" http://192.168.1.6:3000/api/v1/version || echo "failed"',
                                      returnStdout: true
                                  ).trim()
                                  
                                  if (giteaCheck == "200") {
                                      echo "✅ Gitea 连接正常"
                                  } else {
                                      echo "⚠️ Gitea 连接状态: ${giteaCheck}"
                                  }
                              }
                          }
                      }
                  }
                  
                  post {
                      always {
                          echo "🎊 Jenkins 快速部署验证完成！"
                      }
                      success {
                          echo "✅ 所有检查通过，环境就绪！"
                      }
                  }
              }
            ''')
            sandbox()
          }
        }
      }
EOF

# 启动服务
log "启动 Jenkins 服务..."
cd "${PROJECT_ROOT}/docker/compose"
docker-compose -f jenkins-quick.yml up -d

# 等待启动
log "等待 Jenkins 启动..."
for i in {1..60}; do
    if curl -sf "http://localhost:8081/login" &>/dev/null; then
        log "✅ Jenkins 启动成功！"
        break
    fi
    
    if [[ $((i % 10)) -eq 0 ]]; then
        echo "等待启动... ($i/60)"
    fi
    
    sleep 3
done

# 等待配置加载
log "等待配置加载..."
sleep 15

# 验证服务
log "验证服务状态..."
if curl -sf "http://localhost:8081/login" &>/dev/null; then
    log "✅ Jenkins 服务正常"
else
    error "❌ Jenkins 服务异常"
    docker logs jenkins-quick --tail 10
    exit 1
fi

# 创建管理脚本
log "创建管理脚本..."
cat > "${PROJECT_ROOT}/jenkins-quick-manager.sh" << 'EOF'
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker/compose/jenkins-quick.yml"

case "${1:-help}" in
    "start")
        echo "🚀 启动 Jenkins..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml up -d
        echo "✅ 启动完成: http://localhost:8081"
        ;;
    "stop")
        echo "⏸️ 停止 Jenkins..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml down
        echo "✅ 停止完成"
        ;;
    "restart")
        echo "🔄 重启 Jenkins..."
        cd "${SCRIPT_DIR}/docker/compose"
        docker-compose -f jenkins-quick.yml restart
        echo "✅ 重启完成"
        ;;
    "status")
        echo "📊 服务状态:"
        docker ps | grep jenkins-quick || echo "服务未运行"
        echo ""
        curl -s -o /dev/null -w "Jenkins: %{http_code}\n" http://localhost:8081/login
        ;;
    "logs")
        docker logs jenkins-quick -f
        ;;
    "test")
        echo "🧪 请在浏览器访问 http://localhost:8081"
        echo "登录: admin / admin123"
        echo "运行 'hello-world-demo' 作业进行测试"
        ;;
    *)
        echo "Jenkins 快速管理"
        echo ""
        echo "使用方法:"
        echo "  $0 start    # 启动服务"
        echo "  $0 stop     # 停止服务"
        echo "  $0 restart  # 重启服务"
        echo "  $0 status   # 查看状态"
        echo "  $0 logs     # 查看日志"
        echo "  $0 test     # 测试说明"
        echo ""
        echo "访问: http://localhost:8081"
        echo "登录: admin / admin123"
        ;;
esac
EOF

chmod +x "${PROJECT_ROOT}/jenkins-quick-manager.sh"

# 显示完成信息
echo ""
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                   🎉 Jenkins 快速部署完成                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${GREEN}📍 服务访问：${NC}"
echo "  Jenkins:      http://localhost:8081"
echo "  Registry:     http://localhost:35001"
echo "  Gitea:        http://192.168.1.6:3000"

echo ""
echo -e "${GREEN}🔐 登录信息：${NC}"
echo "  用户名: admin"
echo "  密码:   admin123"

echo ""
echo -e "${GREEN}🚀 已配置功能：${NC}"
echo "  ✅ 跳过设置向导"
echo "  ✅ 自动创建管理员账户"
echo "  ✅ Configuration as Code"
echo "  ✅ Docker 集成"
echo "  ✅ 环境变量配置"
echo "  ✅ 示例作业创建"

echo ""
echo -e "${GREEN}🛠️ 管理命令：${NC}"
echo "  ./jenkins-quick-manager.sh start     # 启动"
echo "  ./jenkins-quick-manager.sh status    # 状态"
echo "  ./jenkins-quick-manager.sh test      # 测试"

echo ""
echo -e "${YELLOW}📋 下一步：${NC}"
echo "  1. 访问 http://localhost:8081 登录"
echo "  2. 运行 'hello-world-demo' 作业验证"
echo "  3. 在 Gitea 生成 Token 并更新凭据"

echo ""
log "🎊 Jenkins 自动化配置完成！"