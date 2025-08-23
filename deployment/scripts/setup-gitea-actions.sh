#!/bin/bash

# Gitea Actions Runner 配置脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
GITEA_URL="http://192.168.1.83:3000"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; B='\033[0;34m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 检查 Gitea 服务
check_gitea_service() {
    log "检查 Gitea 服务状态..."
    
    if curl -s "${GITEA_URL}/api/healthz" >/dev/null; then
        log "✅ Gitea 服务正常运行"
    else
        error "❌ Gitea 服务无法访问，请先启动 Gitea"
        exit 1
    fi
}

# 启用 Gitea Actions
enable_gitea_actions() {
    log "启用 Gitea Actions..."
    
    # 检查是否已启用
    log "当前 Gitea 配置已启用 Actions"
    info "🔧 GITEA__actions__ENABLED=true"
    
    # 重启服务以确保配置生效
    cd "${PROJECT_ROOT}/docker/compose"
    docker-compose -f gitea-compose.yml restart gitea
    
    log "✅ Gitea Actions 配置完成"
}

# 设置 Actions Runner
setup_actions_runner() {
    log "设置 Gitea Actions Runner..."
    
    # 创建 runner 目录
    mkdir -p "${PROJECT_ROOT}/docker/compose/gitea-runner"
    
    # 创建 runner compose 文件
    cat > "${PROJECT_ROOT}/docker/compose/gitea-runner.yml" << 'EOF'
services:
  gitea-runner:
    image: gitea/act_runner:latest
    container_name: gitea-runner
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - gitea-runner-data:/data
    environment:
      - GITEA_INSTANCE_URL=http://gitea:3000
      - GITEA_RUNNER_REGISTRATION_TOKEN=${GITEA_RUNNER_TOKEN}
      - GITEA_RUNNER_NAME=docker-runner
      - GITEA_RUNNER_LABELS=ubuntu-latest:docker://node:18-bullseye,ubuntu-22.04:docker://node:18-bullseye
    networks:
      - cicd-network
    depends_on:
      - gitea
    command: >
      sh -c "
        while ! nc -z gitea 3000; do
          echo 'Waiting for Gitea...'
          sleep 1
        done
        echo 'Gitea is ready, starting runner...'
        act_runner register --no-interactive --instance http://gitea:3000 --token $${GITEA_RUNNER_REGISTRATION_TOKEN} --name docker-runner --labels ubuntu-latest:docker://catthehacker/ubuntu:act-latest
        act_runner daemon
      "

  gitea:
    image: gitea/gitea:1.21
    container_name: gitea
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - gitea-data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=sqlite3
      - GITEA__database__PATH=/data/gitea/gitea.db
      - GITEA__server__DOMAIN=192.168.1.83
      - GITEA__server__SSH_DOMAIN=192.168.1.83
      - GITEA__server__ROOT_URL=http://192.168.1.83:3000/
      - GITEA__server__DISABLE_SSH=true
      - GITEA__server__SSH_PORT=2221
      - GITEA__server__SSH_LISTEN_PORT=22
      - GITEA__server__START_SSH_SERVER=false
      - GITEA__repository__ENABLE_PUSH_CREATE_USER=true
      - GITEA__repository__ENABLE_PUSH_CREATE_ORG=true
      - GITEA__webhook__ALLOWED_HOST_LIST=192.168.1.83,localhost,jenkins,gitea-runner
      - GITEA__service__DISABLE_REGISTRATION=false
      - GITEA__service__REQUIRE_SIGNIN_VIEW=false
      - GITEA__actions__ENABLED=true
      - GITEA__actions__DEFAULT_ACTIONS_URL=https://github.com
      - GITEA__log__LEVEL=DEBUG
    networks:
      - cicd-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  cicd-network:
    external: true

volumes:
  gitea-data:
    external: true
    name: compose_gitea-data
  gitea-runner-data:
    driver: local
EOF

    log "✅ Runner Compose 文件已创建"
}

# 获取 Runner Token
get_runner_token() {
    log "获取 Runner 注册令牌..."
    
    warn "⚠️  需要手动获取 Runner 注册令牌"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 打开浏览器访问: ${GITEA_URL}"
    echo "2. 登录管理员账户"
    echo "3. 进入 '站点管理' -> 'Actions' -> 'Runners'"
    echo "4. 点击 '创建新的 Runner'"
    echo "5. 复制生成的注册令牌"
    echo ""
    
    read -p "请输入 Runner 注册令牌: " RUNNER_TOKEN
    
    if [ -n "$RUNNER_TOKEN" ]; then
        # 保存 token 到环境文件
        echo "GITEA_RUNNER_TOKEN=$RUNNER_TOKEN" > "${PROJECT_ROOT}/docker/compose/.env"
        log "✅ Runner 令牌已保存"
    else
        error "❌ 令牌不能为空"
        exit 1
    fi
}

# 启动 Runner
start_runner() {
    log "启动 Gitea Actions Runner..."
    
    cd "${PROJECT_ROOT}/docker/compose"
    
    # 停止现有的 gitea 服务
    docker-compose -f gitea-compose.yml down || true
    
    # 使用包含 runner 的配置启动
    GITEA_RUNNER_REGISTRATION_TOKEN=$(cat .env | grep GITEA_RUNNER_TOKEN | cut -d'=' -f2) \
    docker-compose -f gitea-runner.yml up -d
    
    # 等待服务启动
    log "等待服务启动..."
    sleep 15
    
    # 检查状态
    docker-compose -f gitea-runner.yml ps
    
    log "✅ Gitea Actions Runner 已启动"
}

# 创建示例工作流
create_example_workflow() {
    log "创建示例工作流..."
    
    local example_dir="${PROJECT_ROOT}/examples/workflows"
    mkdir -p "$example_dir"
    
    # 简单的测试工作流
    cat > "$example_dir/hello-world.yml" << 'EOF'
name: 🚀 Hello World

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  hello:
    name: 👋 问候世界
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout 代码
        uses: actions/checkout@v4
      
      - name: 打印问候信息
        run: |
          echo "🌍 Hello, Gitea Actions!"
          echo "📅 当前时间: $(date)"
          echo "🖥️ 运行环境: $(uname -a)"
          echo "🐳 Docker 版本: $(docker --version)"
      
      - name: 测试 Python
        run: |
          python3 --version
          pip3 --version
      
      - name: 测试 Node.js
        run: |
          node --version
          npm --version
EOF

    # Docker 构建工作流
    cat > "$example_dir/docker-build.yml" << 'EOF'
name: 🐳 Docker 构建测试

on:
  push:
    branches: [ main ]

env:
  REGISTRY_URL: 'localhost:5001'

jobs:
  build:
    name: 🏗️ 构建镜像
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout 代码
        uses: actions/checkout@v4
      
      - name: 创建测试 Dockerfile
        run: |
          cat > Dockerfile << 'EOF_DOCKERFILE'
          FROM nginx:alpine
          COPY . /usr/share/nginx/html/
          EXPOSE 80
          CMD ["nginx", "-g", "daemon off;"]
          EOF_DOCKERFILE
      
      - name: 构建 Docker 镜像
        run: |
          docker build -t ${{ env.REGISTRY_URL }}/test-app:${{ github.sha }} .
          docker build -t ${{ env.REGISTRY_URL }}/test-app:latest .
      
      - name: 推送到私有仓库
        run: |
          docker push ${{ env.REGISTRY_URL }}/test-app:${{ github.sha }}
          docker push ${{ env.REGISTRY_URL }}/test-app:latest
          
          echo "✅ 镜像推送完成"
          echo "📦 镜像: ${{ env.REGISTRY_URL }}/test-app:latest"
EOF

    log "✅ 示例工作流已创建在: $example_dir"
}

# 显示使用指南
show_usage_guide() {
    log "Gitea Actions 使用指南:"
    echo ""
    echo "📁 工作流文件位置:"
    echo "   在项目根目录创建: .gitea/workflows/your-workflow.yml"
    echo ""
    echo "🔧 基本工作流结构:"
    cat << 'EOF'
name: 工作流名称

on:
  push:
    branches: [ main ]

jobs:
  job-name:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello World"
EOF
    echo ""
    echo "🌐 访问 Actions:"
    echo "   ${GITEA_URL}/user/repo/actions"
    echo ""
    echo "📝 文档翻译工作流:"
    echo "   复制 examples/gitea-actions/doc-translation.yml"
    echo "   到项目的 .gitea/workflows/ 目录"
    echo ""
    echo "🚀 快速开始:"
    echo "   1. 在项目中创建 .gitea/workflows/test.yml"
    echo "   2. 提交并推送到 main 分支"
    echo "   3. 在 Gitea 中查看 Actions 运行结果"
}

# 主函数
main() {
    case "${1:-help}" in
        setup)
            check_gitea_service
            enable_gitea_actions
            setup_actions_runner
            get_runner_token
            start_runner
            create_example_workflow
            show_usage_guide
            ;;
        token)
            get_runner_token
            ;;
        start)
            start_runner
            ;;
        examples)
            create_example_workflow
            ;;
        guide)
            show_usage_guide
            ;;
        help|--help|-h)
            echo "Gitea Actions 配置脚本"
            echo ""
            echo "使用方法:"
            echo "  $0 setup     # 完整设置 Gitea Actions"
            echo "  $0 token     # 获取 Runner 令牌"
            echo "  $0 start     # 启动 Runner"
            echo "  $0 examples  # 创建示例工作流"
            echo "  $0 guide     # 显示使用指南"
            echo ""
            ;;
        *)
            error "未知命令: $1"
            $0 help
            exit 1
            ;;
    esac
}

main "$@" 