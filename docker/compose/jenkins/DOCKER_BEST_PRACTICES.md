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
