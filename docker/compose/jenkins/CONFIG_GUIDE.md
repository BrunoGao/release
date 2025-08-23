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
