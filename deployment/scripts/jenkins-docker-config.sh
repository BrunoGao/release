#!/bin/bash
# Jenkins Docker集成配置脚本

set -e
JENKINS_URL="http://localhost:8081/jenkins"
REGISTRY_URL="localhost:5001"
BASE_DIR="/Users/brunogao/work/infra"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

# 检查Docker和Registry服务
check_docker_services() {
    log "检查Docker和Registry服务..."
    
    # 检查Docker
    if docker info > /dev/null 2>&1; then
        log "✅ Docker运行正常"
    else
        error "❌ Docker无法访问"
        return 1
    fi
    
    # 检查Registry
    if curl -s "$REGISTRY_URL/v2/_catalog" > /dev/null; then
        log "✅ Registry运行正常"
    else
        error "❌ Registry无法访问"
        return 1
    fi
}

# 配置Docker Registry认证
configure_registry_auth() {
    log "配置Docker Registry认证..."
    
    # 创建Registry认证配置
    cat > "$BASE_DIR/docker/compose/jenkins/scripts/registry-auth.sh" << 'EOF'
#!/bin/bash
# Docker Registry认证配置

REGISTRY_URL="localhost:5001"
REGISTRY_USER="admin"
REGISTRY_PASS="registry123"

echo "=== Docker Registry认证配置 ==="
echo ""
echo "Registry URL: $REGISTRY_URL"
echo "用户名: $REGISTRY_USER"
echo "密码: $REGISTRY_PASS"
echo ""
echo "在Jenkins中配置Registry认证:"
echo "1. 进入 Jenkins -> 管理Jenkins -> 凭据"
echo "2. 点击 'System' -> '全局凭据'"
echo "3. 点击 '添加凭据'"
echo "4. 选择类型: 'Username with password'"
echo "5. 填写信息:"
echo "   - ID: registry-auth"
echo "   - 描述: Docker Registry Auth"
echo "   - 用户名: $REGISTRY_USER"
echo "   - 密码: $REGISTRY_PASS"
echo ""
echo "测试Registry连接:"
echo "docker login $REGISTRY_URL -u $REGISTRY_USER -p $REGISTRY_PASS"
EOF

    chmod +x "$BASE_DIR/docker/compose/jenkins/scripts/registry-auth.sh"
    log "✅ Registry认证配置已创建"
}

# 创建Docker构建脚本模板
create_docker_build_templates() {
    log "创建Docker构建脚本模板..."
    
    # 创建基础Dockerfile模板
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Dockerfile.python" << 'EOF'
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 运行应用
CMD ["python", "app.py"]
EOF

    # 创建Node.js Dockerfile模板
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Dockerfile.nodejs" << 'EOF'
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# 运行应用
CMD ["npm", "start"]
EOF

    # 创建Java Dockerfile模板
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Dockerfile.java" << 'EOF'
FROM openjdk:11-jre-slim

# 设置工作目录
WORKDIR /app

# 复制JAR文件
COPY target/*.jar app.jar

# 暴露端口
EXPOSE 8080

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

# 运行应用
CMD ["java", "-jar", "app.jar"]
EOF

    mkdir -p "$BASE_DIR/docker/compose/jenkins/templates"
    log "✅ Docker构建模板已创建"
}

# 创建Docker构建Pipeline模板
create_docker_pipeline_templates() {
    log "创建Docker构建Pipeline模板..."
    
    # 基础Docker构建Pipeline
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Jenkinsfile.docker" << 'EOF'
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'my-app'
        APP_VERSION = "${BUILD_NUMBER}"
        REGISTRY_CREDENTIALS = 'registry-auth'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${APP_VERSION}-${GIT_COMMIT_SHORT}"
                }
            }
        }
        
        stage('构建Docker镜像') {
            steps {
                script {
                    def imageName = "${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
                    def latestName = "${DOCKER_REGISTRY}/${APP_NAME}:latest"
                    
                    echo "构建镜像: ${imageName}"
                    
                    // 构建镜像
                    sh """
                        docker build -t ${imageName} .
                        docker tag ${imageName} ${latestName}
                    """
                    
                    // 推送镜像
                    withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDENTIALS,
                        usernameVariable: 'REGISTRY_USER',
                        passwordVariable: 'REGISTRY_PASS'
                    )]) {
                        sh """
                            echo \$REGISTRY_PASS | docker login ${DOCKER_REGISTRY} -u \$REGISTRY_USER --password-stdin
                            docker push ${imageName}
                            docker push ${latestName}
                        """
                    }
                }
            }
        }
        
        stage('镜像安全扫描') {
            steps {
                echo '执行镜像安全扫描...'
                sh """
                    echo "扫描镜像: ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
                    # 这里可以集成Trivy等安全扫描工具
                """
            }
        }
        
        stage('部署到测试环境') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    echo '部署到测试环境...'
                    sh """
                        docker stop ${APP_NAME}-test || true
                        docker rm ${APP_NAME}-test || true
                        docker run -d --name ${APP_NAME}-test -p 8080:5000 ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }
        
        stage('部署到生产环境') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    echo '部署到生产环境...'
                    sh """
                        docker stop ${APP_NAME}-prod || true
                        docker rm ${APP_NAME}-prod || true
                        docker run -d --name ${APP_NAME}-prod -p 8081:5000 ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                    """
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline执行完成'
            sh """
                docker logout ${DOCKER_REGISTRY} || true
                docker system prune -f || true
            """
        }
        success {
            echo '✅ 构建成功!'
        }
        failure {
            echo '❌ 构建失败!'
        }
    }
}
EOF

    # 多阶段构建Pipeline
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Jenkinsfile.multistage" << 'EOF'
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'my-app'
        REGISTRY_CREDENTIALS = 'registry-auth'
    }
    
    stages {
        stage('并行构建') {
            parallel {
                stage('单元测试') {
                    steps {
                        sh 'echo "执行单元测试..."'
                    }
                }
                stage('代码检查') {
                    steps {
                        sh 'echo "执行代码检查..."'
                    }
                }
                stage('安全扫描') {
                    steps {
                        sh 'echo "执行安全扫描..."'
                    }
                }
            }
        }
        
        stage('构建多架构镜像') {
            steps {
                script {
                    def platforms = ['linux/amd64', 'linux/arm64']
                    def imageName = "${DOCKER_REGISTRY}/${APP_NAME}:${BUILD_NUMBER}"
                    
                    echo "构建多架构镜像: ${imageName}"
                    
                    withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDENTIALS,
                        usernameVariable: 'REGISTRY_USER',
                        passwordVariable: 'REGISTRY_PASS'
                    )]) {
                        sh """
                            echo \$REGISTRY_PASS | docker login ${DOCKER_REGISTRY} -u \$REGISTRY_USER --password-stdin
                            docker buildx create --use --name multiarch-builder || true
                            docker buildx build --platform ${platforms.join(',')} -t ${imageName} --push .
                        """
                    }
                }
            }
        }
    }
}
EOF

    log "✅ Docker Pipeline模板已创建"
}

# 创建Docker工具配置脚本
create_docker_tools_config() {
    log "创建Docker工具配置脚本..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/scripts/docker-tools.sh" << 'EOF'
#!/bin/bash
# Docker工具配置脚本

echo "=== Docker工具配置指南 ==="
echo ""
echo "1. 配置Docker工具"
echo "   路径: Jenkins -> 管理Jenkins -> 全局工具配置"
echo "   添加Docker安装:"
echo "   - 名称: Docker"
echo "   - 安装目录: /usr/local/bin/docker"
echo "   - 或选择自动安装最新版本"
echo ""
echo "2. 配置Docker Cloud (可选)"
echo "   路径: Jenkins -> 管理Jenkins -> 节点和云 -> 配置云"
echo "   添加Docker Cloud:"
echo "   - Docker Host URI: unix:///var/run/docker.sock"
echo "   - 启用: 是"
echo ""
echo "3. 安装Docker相关插件"
echo "   推荐插件:"
echo "   - Docker Plugin"
echo "   - Docker Pipeline"
echo "   - Docker Commons"
echo "   - Docker Build Step"
echo ""
echo "4. 验证Docker配置"
echo "   在Jenkins Pipeline中测试:"
echo "   sh 'docker --version'"
echo "   sh 'docker info'"
echo ""
echo "5. 配置Docker Registry"
echo "   在Pipeline中使用:"
echo "   docker.withRegistry('http://localhost:5001', 'registry-auth') {"
echo "       def image = docker.build('my-app:latest')"
echo "       image.push()"
echo "   }"
EOF

    chmod +x "$BASE_DIR/docker/compose/jenkins/scripts/docker-tools.sh"
    log "✅ Docker工具配置脚本已创建"
}

# 创建Docker最佳实践指南
create_docker_best_practices() {
    log "创建Docker最佳实践指南..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/DOCKER_BEST_PRACTICES.md" << 'EOF'
# Docker CI/CD最佳实践指南

## 1. Dockerfile最佳实践

### 1.1 基础镜像选择
```dockerfile
# 使用官方基础镜像
FROM python:3.11-slim

# 避免使用latest标签
FROM python:3.11-slim  # 好
FROM python:latest     # 不好
```

### 1.2 层优化
```dockerfile
# 合并RUN指令减少层数
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget && \
    rm -rf /var/lib/apt/lists/*

# 利用缓存，先复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 1.3 安全实践
```dockerfile
# 创建非root用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
USER nextjs

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
```

## 2. Jenkins Pipeline最佳实践

### 2.1 镜像构建
```groovy
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'my-app'
        IMAGE_TAG = "${BUILD_NUMBER}-${GIT_COMMIT[0..7]}"
    }
    
    stages {
        stage('构建镜像') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}")
                    
                    // 推送镜像
                    docker.withRegistry("http://${DOCKER_REGISTRY}", 'registry-auth') {
                        image.push()
                        image.push("latest")
                    }
                }
            }
        }
    }
}
```

### 2.2 并行构建
```groovy
stage('并行任务') {
    parallel {
        stage('单元测试') {
            steps {
                sh 'pytest tests/unit'
            }
        }
        stage('构建镜像') {
            steps {
                script {
                    docker.build("${APP_NAME}:${BUILD_NUMBER}")
                }
            }
        }
    }
}
```

### 2.3 条件部署
```groovy
stage('部署') {
    when {
        allOf {
            branch 'main'
            not { changeRequest() }
        }
    }
    steps {
        script {
            sh """
                docker stop ${APP_NAME} || true
                docker rm ${APP_NAME} || true
                docker run -d --name ${APP_NAME} -p 8080:5000 ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
            """
        }
    }
}
```

## 3. Registry管理

### 3.1 镜像标签策略
```bash
# 语义化版本
my-app:1.0.0
my-app:1.0.0-rc1

# 构建信息
my-app:build-123
my-app:build-123-abc1234

# 环境标签
my-app:dev
my-app:staging
my-app:prod
```

### 3.2 镜像清理
```groovy
post {
    always {
        sh """
            # 清理本地镜像
            docker rmi ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG} || true
            
            # 清理悬空镜像
            docker system prune -f
        """
    }
}
```

## 4. 安全实践

### 4.1 镜像扫描
```groovy
stage('安全扫描') {
    steps {
        script {
            // 使用Trivy扫描
            sh """
                trivy image --exit-code 1 --severity HIGH,CRITICAL ${DOCKER_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
            """
        }
    }
}
```

### 4.2 凭据管理
```groovy
withCredentials([usernamePassword(
    credentialsId: 'registry-auth',
    usernameVariable: 'REGISTRY_USER',
    passwordVariable: 'REGISTRY_PASS'
)]) {
    sh """
        echo \$REGISTRY_PASS | docker login ${DOCKER_REGISTRY} -u \$REGISTRY_USER --password-stdin
    """
}
```

## 5. 性能优化

### 5.1 构建缓存
```dockerfile
# 使用构建缓存
FROM python:3.11-slim as builder

# 多阶段构建
FROM builder as dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.11-slim as runtime
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

### 5.2 并行构建
```groovy
stage('并行构建') {
    parallel {
        stage('AMD64') {
            steps {
                sh 'docker buildx build --platform linux/amd64 -t ${APP_NAME}:amd64 .'
            }
        }
        stage('ARM64') {
            steps {
                sh 'docker buildx build --platform linux/arm64 -t ${APP_NAME}:arm64 .'
            }
        }
    }
}
```

## 6. 监控和日志

### 6.1 构建监控
```groovy
post {
    always {
        // 发布构建报告
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'reports',
            reportFiles: 'index.html',
            reportName: 'Build Report'
        ])
    }
}
```

### 6.2 日志管理
```dockerfile
# 配置日志驱动
LABEL logging.driver="json-file"
LABEL logging.options.max-size="10m"
LABEL logging.options.max-file="3"
```

## 7. 故障排除

### 7.1 常见问题
1. **构建失败**
   - 检查Dockerfile语法
   - 确认基础镜像可用
   - 检查网络连接

2. **推送失败**
   - 检查Registry认证
   - 确认网络连通性
   - 检查存储空间

3. **部署失败**
   - 检查端口占用
   - 确认镜像存在
   - 检查环境变量

### 7.2 调试命令
```bash
# 查看构建日志
docker logs jenkins

# 检查镜像
docker images | grep my-app

# 测试Registry连接
curl -u admin:password http://localhost:5001/v2/_catalog

# 检查容器状态
docker ps -a
```
EOF

    log "✅ Docker最佳实践指南已创建"
}

# 主函数
main() {
    log "开始配置Jenkins Docker集成..."
    
    check_docker_services
    configure_registry_auth
    create_docker_build_templates
    create_docker_pipeline_templates
    create_docker_tools_config
    create_docker_best_practices
    
    log "✅ Jenkins Docker集成配置完成!"
    log ""
    log "📋 下一步操作:"
    log "1. 配置Docker Registry认证 (运行: docker/compose/jenkins/scripts/registry-auth.sh)"
    log "2. 配置Docker工具 (运行: docker/compose/jenkins/scripts/docker-tools.sh)"
    log "3. 查看最佳实践指南 (docker/compose/jenkins/DOCKER_BEST_PRACTICES.md)"
    log "4. 使用Pipeline模板创建Docker构建作业"
    log ""
    log "📁 模板位置: docker/compose/jenkins/templates/"
    log "📖 最佳实践: docker/compose/jenkins/DOCKER_BEST_PRACTICES.md"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 