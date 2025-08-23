#!/bin/bash
# CI/CD统一管理脚本 - 解决gitea多实例问题，配置完整流水线

set -e
BASE_DIR="/Users/brunogao/work/infra"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
NC='\033[0m'

# 日志函数
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

log "=== CI/CD统一管理系统 ==="

# 创建数据目录
init_dirs(){
    log "初始化目录结构..."
    mkdir -p "$BASE_DIR"/{data/{gitea,jenkins},backup/{gitea,jenkins},docker/registry/auth}
    log "✅ 目录创建完成"
}

# 检查服务状态
check_services(){
    log "检查服务状态..."
    
    # Gitea
    if curl -s http://192.168.1.6:3000/api/healthz>/dev/null;then
        log "✅ Gitea运行正常 (192.168.1.6:3000)"
    else
        warn "⚠️  Gitea未运行或不可访问"
    fi
    
    # Jenkins
    if curl -s http://localhost:8081/jenkins/login>/dev/null;then
        log "✅ Jenkins运行正常 (localhost:8081)"
    else
        warn "⚠️  Jenkins未运行"
    fi
    
    # Registry
    if curl -s http://localhost:5001/v2/_catalog>/dev/null;then
        log "✅ Registry运行正常 (localhost:5001)"
    else
        warn "⚠️  Registry未运行"
    fi
}

# 停止所有旧的gitea实例
stop_old_gitea(){
    log "停止旧的Gitea实例..."
    docker ps -a|grep gitea|awk '{print $1}'|xargs -r docker stop||true
    docker ps -a|grep gitea|awk '{print $1}'|xargs -r docker rm||true
    log "✅ 旧实例已清理"
}

# 启动统一gitea
start_gitea(){
    log "启动统一Gitea服务..."
    cd "$BASE_DIR/docker/compose"
    
    # 创建网络
    docker network create cicd-network 2>/dev/null||true
    
    # 启动gitea
    docker-compose -f gitea-compose.yml up -d
    
    # 等待启动
    log "等待Gitea启动..."
    for i in {1..30};do
        if curl -s http://192.168.1.6:3000/api/healthz>/dev/null;then
            log "✅ Gitea启动成功"
            return 0
        fi
        sleep 5
    done
    error "❌ Gitea启动超时"
}

# 启动Jenkins
start_jenkins(){
    log "启动Jenkins服务..."
    cd "$BASE_DIR/docker/compose"
    docker-compose -f jenkins-compose.yml up -d
    
    log "等待Jenkins启动..."
    for i in {1..60};do
        if curl -s http://localhost:8081/jenkins/login>/dev/null;then
            log "✅ Jenkins启动成功"
            return 0
        fi
        sleep 5
    done
    error "❌ Jenkins启动超时"
}

# 配置多平台构建环境
setup_multiplatform(){
    log "配置多平台构建环境..."
    
    # 启用buildx
    docker buildx create --use --name multiplatform --driver docker-container 2>/dev/null||true
    docker buildx inspect --bootstrap multiplatform
    
    log "✅ 多平台构建环境已配置"
}

# 创建项目Pipeline
create_project_pipelines(){
    log "创建项目Pipeline模板..."
    
    local projects=("ljwx-admin" "ljwx-boot" "ljwx-boot-starter" "ljwx-bigscreen")
    
    for project in "${projects[@]}";do
        log "创建 $project Pipeline..."
        
        # 根据项目类型选择模板
        local template=""
        case $project in
            ljwx-admin)template="Jenkinsfile.multiplatform";;
            ljwx-boot*)template="Jenkinsfile.multiplatform";;
            ljwx-bigscreen)template="Jenkinsfile.multiplatform";;
        esac
        
        # 创建项目特定配置
        cat > "$BASE_DIR/projects/$project/Jenkinsfile" << EOF
@Library('jenkins-shared-library') _

// 项目: $project
// 自动生成时间: $(date)

pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        GITEA_URL = 'http://192.168.1.6:3000'
        APP_NAME = '$project'
        PLATFORMS = 'linux/amd64,linux/arm64'
    }
    
    stages {
        stage('检出代码'){
            steps{
                git branch:'main',url:"\${GITEA_URL}/cicd/$project.git"
            }
        }
        
        stage('多平台构建'){
            steps{
                script{
                    buildMultiPlatformImage([
                        appName:env.APP_NAME,
                        platforms:env.PLATFORMS,
                        registry:env.DOCKER_REGISTRY
                    ])
                }
            }
        }
        
        stage('部署'){
            when{branch 'main'}
            steps{
                deployToEnvironment([
                    environment:'prod',
                    appName:env.APP_NAME
                ])
            }
        }
    }
}
EOF
    done
    
    log "✅ Pipeline模板已创建"
}

# 测试完整流程
test_pipeline(){
    log "测试CI/CD流程..."
    
    # 测试Gitea webhook
    curl -X POST http://192.168.1.6:3000/api/v1/repos/cicd/ljwx-admin/hooks \
        -H "Content-Type:application/json" \
        -d '{"type":"gitea","config":{"url":"http://jenkins:8080/generic-webhook-trigger/invoke","content_type":"json"}}'||warn "Webhook配置需要手动设置"
    
    # 测试Registry推送
    docker tag alpine:latest localhost:5001/test:latest 2>/dev/null||true
    docker push localhost:5001/test:latest||warn "Registry推送测试失败"
    docker rmi localhost:5001/test:latest 2>/dev/null||true
    
    log "✅ 流程测试完成"
}

# 显示配置信息
show_info(){
    log "=== CI/CD配置信息 ==="
    echo "
🔧 服务配置:
- Gitea:    http://192.168.1.6:3000 (统一实例)
- Jenkins:  http://localhost:8081/jenkins
- Registry: http://localhost:5001

📦 支持项目:
- ljwx-admin (Vue3)
- ljwx-boot (Java21)
- ljwx-boot-starter (Java21) 
- ljwx-bigscreen (Python)

🏗️  多平台支持:
- linux/amd64 (Intel/AMD)
- linux/arm64 (Apple Silicon)

📋 使用步骤:
1. 在Gitea创建项目: http://192.168.1.6:3000
2. 推送代码到仓库
3. Jenkins自动触发构建
4. 多平台镜像推送到Registry
"
}

# 备份配置
backup_configs(){
    local timestamp=$(date +%Y%m%d_%H%M%S)
    log "备份配置 ($timestamp)..."
    
    tar -czf "$BASE_DIR/backup/cicd-config-$timestamp.tar.gz" \
        -C "$BASE_DIR" docker/ deployment/ --exclude='*.log' --exclude='data/'
    
    log "✅ 备份完成: cicd-config-$timestamp.tar.gz"
}

# 主菜单
show_menu(){
    echo "
=== CI/CD管理菜单 ===
1. 🔄 重置Gitea (解决多实例问题)
2. 🚀 启动所有服务
3. 🛠️  配置多平台构建
4. 📝 创建项目Pipeline
5. 🧪 测试CI/CD流程
6. 📊 查看服务状态
7. ℹ️  显示配置信息
8. 💾 备份配置
9. 🧹 清理环境
0. 退出

请选择操作 (0-9): "
}

# 清理环境
cleanup_env(){
    log "清理CI/CD环境..."
    
    # 停止所有服务
    docker-compose -f "$BASE_DIR/docker/compose/gitea-compose.yml" down 2>/dev/null||true
    docker-compose -f "$BASE_DIR/docker/compose/jenkins-compose.yml" down 2>/dev/null||true
    
    # 清理buildx
    docker buildx rm multiplatform 2>/dev/null||true
    
    # 清理镜像
    docker system prune -f
    
    log "✅ 环境清理完成"
}

# 主程序
main(){
    init_dirs
    
    while true;do
        show_menu
        read -r choice
        case $choice in
            1)stop_old_gitea;start_gitea;;
            2)start_gitea;start_jenkins;setup_multiplatform;;
            3)setup_multiplatform;;
            4)create_project_pipelines;;
            5)test_pipeline;;
            6)check_services;;
            7)show_info;;
            8)backup_configs;;
            9)cleanup_env;;
            0)log "👋 再见!";exit 0;;
            *)warn "无效选择，请重试";;
        esac
        echo;read -p "按回车继续...";echo
    done
}

main "$@" 