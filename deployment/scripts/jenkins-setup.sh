#!/bin/bash
# Jenkins简化配置脚本

set -e
JENKINS_URL="http://localhost:8081/jenkins"
BASE_DIR="/Users/brunogao/work/infra"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

# 获取初始管理员密码
get_admin_password() {
    log "获取Jenkins初始管理员密码..."
    local password=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "")
    if [[ -n "$password" ]]; then
        log "初始管理员密码: $password"
        echo "$password" > /tmp/jenkins-admin-password.txt
        log "密码已保存到: /tmp/jenkins-admin-password.txt"
    else
        warn "无法获取初始密码，Jenkins可能已经初始化"
    fi
}

# 检查Jenkins状态
check_jenkins_status() {
    log "检查Jenkins状态..."
    if curl -s "$JENKINS_URL/login" > /dev/null; then
        log "✅ Jenkins运行正常"
        log "🌐 访问地址: $JENKINS_URL"
        return 0
    else
        warn "❌ Jenkins无法访问"
        return 1
    fi
}

# 创建Jenkins配置目录
setup_directories() {
    log "创建Jenkins配置目录..."
    mkdir -p "$BASE_DIR/data/jenkins"
    mkdir -p "$BASE_DIR/backup/jenkins"
    mkdir -p "$BASE_DIR/docker/compose/jenkins"/{config,plugins,scripts}
    log "✅ 目录创建完成"
}

# 创建插件安装脚本
create_plugin_installer() {
    log "创建插件安装脚本..."
    cat > "$BASE_DIR/docker/compose/jenkins/scripts/install-plugins.sh" << 'EOF'
#!/bin/bash
# Jenkins插件安装脚本

PLUGINS=(
    "configuration-as-code:latest"
    "job-dsl:latest"
    "pipeline-stage-view:latest"
    "blueocean:latest"
    "gitea:latest"
    "docker-plugin:latest"
    "docker-workflow:latest"
    "credentials-binding:latest"
    "timestamper:latest"
    "ws-cleanup:latest"
    "build-timeout:latest"
    "generic-webhook-trigger:latest"
    "pipeline-utility-steps:latest"
    "http_request:latest"
    "email-ext:latest"
    "maven-plugin:latest"
    "gradle:latest"
    "nodejs:latest"
    "python:latest"
)

echo "推荐安装的插件列表："
for plugin in "${PLUGINS[@]}"; do
    echo "- $plugin"
done

echo ""
echo "在Jenkins管理界面中，进入 '管理Jenkins' -> '插件管理' -> '可选插件'"
echo "搜索并安装上述插件"
EOF
    chmod +x "$BASE_DIR/docker/compose/jenkins/scripts/install-plugins.sh"
    log "✅ 插件安装脚本已创建"
}

# 创建配置指南
create_config_guide() {
    log "创建配置指南..."
    cat > "$BASE_DIR/docker/compose/jenkins/CONFIG_GUIDE.md" << 'EOF'
# Jenkins配置指南

## 1. 初始化设置

1. 访问 http://localhost:8081/jenkins
2. 使用初始管理员密码登录（见 /tmp/jenkins-admin-password.txt）
3. 选择 "安装推荐的插件"
4. 创建管理员用户
5. 配置Jenkins URL: http://localhost:8081/jenkins/

## 2. 必要插件安装

运行插件安装脚本查看推荐插件：
```bash
./docker/compose/jenkins/scripts/install-plugins.sh
```

## 3. 系统配置

### 3.1 全局工具配置
- Git: /usr/bin/git
- Docker: /usr/local/bin/docker
- Maven: 自动安装最新版本
- Node.js: 自动安装最新LTS版本

### 3.2 凭据配置
在 "管理Jenkins" -> "凭据" 中添加：
- Gitea Token (Secret text)
- Docker Registry 认证 (Username/Password)
- SSH密钥 (SSH Username with private key)

### 3.3 系统设置
- 执行器数量: 4
- 安静期: 5秒
- SCM检出重试次数: 3
- Jenkins URL: http://localhost:8081/jenkins/

## 4. 创建Pipeline作业

### 4.1 基础Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        GITEA_URL = 'http://gitea:3000'
    }
    
    stages {
        stage('检出代码') {
            steps {
                git branch: 'main', url: "${GITEA_URL}/your-repo.git"
            }
        }
        
        stage('构建测试') {
            steps {
                sh 'echo "执行测试..."'
            }
        }
        
        stage('构建镜像') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/app:${BUILD_NUMBER}")
                    docker.withRegistry("http://${DOCKER_REGISTRY}") {
                        image.push()
                    }
                }
            }
        }
    }
}
```

### 4.2 Gitea Webhook配置
1. 在Gitea项目设置中添加Webhook
2. URL: http://localhost:8081/jenkins/generic-webhook-trigger/invoke
3. 内容类型: application/json
4. 触发事件: Push events

## 5. 性能优化

### 5.1 JVM参数优化
在docker-compose.yml中已配置：
- -Xmx2g -Xms1g
- -XX:+UseG1GC
- -XX:MaxGCPauseMillis=200

### 5.2 构建历史清理
- 保留构建数: 50
- 保留天数: 30

### 5.3 工作空间清理
使用 "Workspace Cleanup" 插件自动清理

## 6. 备份策略

### 6.1 自动备份
使用 jenkins-manager.sh 脚本：
```bash
./deployment/scripts/jenkins-manager.sh
# 选择选项 4 进行备份
```

### 6.2 手动备份
```bash
tar -czf jenkins-backup-$(date +%Y%m%d).tar.gz -C /Users/brunogao/work/infra/data/jenkins .
```

## 7. 故障排除

### 7.1 常见问题
- Jenkins无法启动: 检查端口占用和权限
- 插件安装失败: 检查网络连接和代理设置
- 构建失败: 检查工具配置和环境变量

### 7.2 日志查看
```bash
docker logs jenkins
docker exec jenkins tail -f /var/jenkins_home/logs/jenkins.log
```
EOF
    log "✅ 配置指南已创建"
}

# 创建快速启动脚本
create_quick_start() {
    log "创建快速启动脚本..."
    cat > "$BASE_DIR/quick-start-jenkins.sh" << 'EOF'
#!/bin/bash
# Jenkins快速启动脚本

echo "🚀 启动Jenkins服务..."
cd /Users/brunogao/work/infra/docker/compose
docker-compose -f jenkins-compose.yml up -d

echo "⏳ 等待Jenkins启动..."
sleep 10

echo "🔑 获取管理员密码..."
password=$(docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "已初始化")
echo "管理员密码: $password"

echo "🌐 打开Jenkins..."
open http://localhost:8081/jenkins

echo "📖 查看配置指南..."
echo "配置指南位置: docker/compose/jenkins/CONFIG_GUIDE.md"
EOF
    chmod +x "$BASE_DIR/quick-start-jenkins.sh"
    log "✅ 快速启动脚本已创建"
}

# 主函数
main() {
    log "开始Jenkins初始化配置..."
    
    setup_directories
    check_jenkins_status
    get_admin_password
    create_plugin_installer
    create_config_guide
    create_quick_start
    
    log "✅ Jenkins初始化配置完成！"
    log ""
    log "📋 下一步操作："
    log "1. 访问 $JENKINS_URL"
    log "2. 使用初始密码登录（见 /tmp/jenkins-admin-password.txt）"
    log "3. 按照配置指南完成设置（见 docker/compose/jenkins/CONFIG_GUIDE.md）"
    log "4. 运行插件安装脚本查看推荐插件"
    log ""
    log "🚀 快速启动命令: ./quick-start-jenkins.sh"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 