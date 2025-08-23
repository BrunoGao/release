# Jenkins CI/CD完整配置指南

## 🚀 快速启动

Jenkins已成功启动！初始管理员密码：`5d3e7c4031c04137b9e6d77c0a15ddbd`

### 访问地址
- **Jenkins**: http://localhost:8081
- **Docker Registry**: http://localhost:5001
- **Registry UI**: http://localhost:5002
- **Gitea**: http://192.168.1.6:3000

## 📋 初始化配置步骤

### 1. 访问Jenkins并完成设置向导
1. 打开 http://localhost:8081
2. 输入初始密码：`5d3e7c4031c04137b9e6d77c0a15ddbd`
3. 选择"安装推荐的插件"
4. 创建管理员用户
5. 保持Jenkins URL为默认设置

### 2. 安装必要插件
进入"管理Jenkins" -> "插件管理" -> "可选插件"，搜索并安装：

#### 核心插件
- Build Timeout
- Credentials Binding
- Timestamper
- Workspace Cleanup
- AnsiColor

#### Git和版本控制
- Git plugin
- Gitea plugin
- SSH Credentials plugin

#### Pipeline和构建
- Pipeline: Stage View
- Pipeline Utility Steps
- Workflow Aggregator
- Blue Ocean

#### Docker集成
- Docker plugin
- Docker Pipeline
- Docker Commons
- Kubernetes plugin

#### 构建工具
- Maven Integration plugin
- Gradle plugin
- NodeJS plugin
- Python plugin

#### 自动化和通知
- Generic Webhook Trigger
- Email Extension
- Slack Notification

### 3. 全局工具配置
进入"管理Jenkins" -> "全局工具配置"：

#### Git
- 名称：Default
- 路径：/usr/bin/git

#### Maven
- 名称：Maven-3.9
- 选择"自动安装"，版本：3.9.6

#### Gradle
- 名称：Gradle-8
- 选择"自动安装"，版本：8.5

#### Node.js
- 名称：NodeJS-18
- 选择"自动安装"，版本：18.19.0

#### Docker
- 名称：Docker
- 路径：/usr/local/bin/docker

### 4. 凭据配置
进入"管理Jenkins" -> "凭据" -> "系统" -> "全局凭据"：

#### Gitea Token (Secret text)
- ID：gitea-token
- Description：Gitea API访问令牌
- Secret：[在Gitea中生成的Personal Access Token]

#### Docker Registry (Username with password)
- ID：registry-auth
- Description：Docker Registry认证
- Username：admin
- Password：admin123

#### SSH密钥 (SSH Username with private key)
- ID：ssh-key
- Description：Git SSH访问密钥
- Username：jenkins
- Private Key：[粘贴SSH私钥内容]

#### Kubernetes配置 (Secret file)
- ID：k8s-config
- Description：Kubernetes配置文件
- File：[上传kubeconfig文件]

### 5. 系统配置
进入"管理Jenkins" -> "系统配置"：

#### 执行器数量
设置为：4

#### 环境变量
添加全局环境变量：
- DOCKER_REGISTRY=localhost:5001
- GITEA_URL=http://192.168.1.6:3000
- TZ=Asia/Shanghai

#### Gitea服务器配置
- 显示名称：Local Gitea
- 服务器URL：http://192.168.1.6:3000
- 凭据：选择gitea-token

### 6. 创建Pipeline作业

#### 多平台构建Pipeline
```groovy
pipeline {
    agent any
    
    environment {
        REGISTRY = 'localhost:5001'
        APP_NAME = 'my-app'
        PLATFORMS = 'linux/amd64,linux/arm64'
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
            }
        }
        
        stage('多平台构建') {
            steps {
                script {
                    sh '''
                        docker buildx create --use --name builder || true
                        docker buildx build --platform ${PLATFORMS} \\
                            -t ${REGISTRY}/${APP_NAME}:${BUILD_NUMBER} \\
                            -t ${REGISTRY}/${APP_NAME}:latest \\
                            --push .
                    '''
                }
            }
        }
        
        stage('部署验证') {
            steps {
                sh 'docker run --rm ${REGISTRY}/${APP_NAME}:latest echo "部署验证成功"'
            }
        }
    }
}
```

### 7. Webhook配置

#### 在Gitea中配置Webhook
1. 进入项目设置 -> Webhooks
2. 添加新的Webhook：
   - URL：`http://jenkins-simple:8080/generic-webhook-trigger/invoke`
   - 内容类型：`application/json`
   - 密钥：设置一个随机字符串
   - 触发事件：Push events

#### 在Jenkins中配置触发器
在Pipeline配置中添加：
```groovy
triggers {
    GenericTrigger(
        genericVariables: [
            [key: 'ref', value: '$.ref']
        ],
        causeString: 'Triggered by Gitea',
        token: 'your-webhook-token',
        tokenCredentialId: '',
        printContributedVariables: true,
        printPostContent: true
    )
}
```

## 🔧 高级配置

### 性能优化
1. JVM参数已优化：`-Xmx1g -Xms512m`
2. 构建历史保留：最多50个构建，30天
3. 工作空间自动清理：使用Workspace Cleanup插件

### 多环境部署
创建参数化构建：
```groovy
parameters {
    choice(
        name: 'DEPLOY_ENV',
        choices: ['dev', 'staging', 'prod'],
        description: '部署环境'
    )
}
```

### 共享库配置
1. 在Gitea中创建jenkins-shared-library仓库
2. 在Jenkins中配置全局Pipeline库：
   - 名称：jenkins-shared-library
   - 默认版本：main
   - SCM：Git，URL：http://192.168.1.6:3000/your-org/jenkins-shared-library.git

## 🛠️ 管理命令

### 服务管理
```bash
# 启动Jenkins
docker-compose -f docker/compose/jenkins-simple.yml up -d

# 停止Jenkins
docker-compose -f docker/compose/jenkins-simple.yml down

# 查看日志
docker logs jenkins-simple -f

# 重启Jenkins
docker restart jenkins-simple
```

### 备份和恢复
```bash
# 备份Jenkins配置
docker exec jenkins-simple tar czf /tmp/jenkins-backup.tar.gz -C /var/jenkins_home .
docker cp jenkins-simple:/tmp/jenkins-backup.tar.gz ./backup/

# 恢复Jenkins配置
docker cp ./backup/jenkins-backup.tar.gz jenkins-simple:/tmp/
docker exec jenkins-simple tar xzf /tmp/jenkins-backup.tar.gz -C /var/jenkins_home
docker restart jenkins-simple
```

### 插件管理
```bash
# 列出已安装插件
docker exec jenkins-simple cat /var/jenkins_home/plugins.txt

# 安装新插件
docker exec jenkins-simple jenkins-plugin-cli --plugins plugin-name:version
```

## 🚀 项目集成示例

### Vue3项目
```groovy
pipeline {
    agent any
    stages {
        stage('构建') {
            steps {
                sh 'npm ci'
                sh 'npm run build'
                sh 'docker build -t localhost:5001/vue-app:${BUILD_NUMBER} .'
                sh 'docker push localhost:5001/vue-app:${BUILD_NUMBER}'
            }
        }
    }
}
```

### Spring Boot项目
```groovy
pipeline {
    agent any
    stages {
        stage('构建') {
            steps {
                sh 'mvn clean package -DskipTests'
                sh 'docker build -t localhost:5001/spring-app:${BUILD_NUMBER} .'
                sh 'docker push localhost:5001/spring-app:${BUILD_NUMBER}'
            }
        }
    }
}
```

## 📞 故障排查

### 常见问题
1. **Jenkins无法访问Docker**：确保用户有Docker权限
2. **插件安装失败**：检查网络连接，尝试使用清华镜像源
3. **构建失败**：查看控制台输出，检查环境变量和工具配置
4. **Webhook不触发**：确认网络连通性和认证配置

### 日志查看
```bash
# Jenkins主日志
docker logs jenkins-simple

# 构建日志
# 在Jenkins Web界面中查看

# 系统信息
# 管理Jenkins -> 系统信息
```

## 🎯 下一步

1. 配置具体项目的Pipeline
2. 设置代码质量检查（SonarQube）
3. 配置通知机制（邮件/Slack）
4. 设置定时备份
5. 配置监控和告警

---

🎉 **恭喜！你的Jenkins CI/CD环境已完全配置就绪！** 