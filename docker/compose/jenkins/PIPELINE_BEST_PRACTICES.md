# Jenkins Pipeline最佳实践指南

## 1. Pipeline结构设计

### 1.1 基本结构
```groovy
pipeline {
    agent any
    
    environment {
        // 环境变量
    }
    
    options {
        // Pipeline选项
    }
    
    stages {
        // 构建阶段
    }
    
    post {
        // 后置处理
    }
}
```

### 1.2 阶段设计原则
- **单一职责**: 每个阶段只做一件事
- **快速失败**: 耗时短的阶段放在前面
- **并行执行**: 无依赖的阶段并行执行
- **条件执行**: 使用when条件控制执行

## 2. 共享库使用

### 2.1 共享库结构
```
shared-library/
├── vars/                    # 全局变量
│   ├── buildDockerImage.groovy
│   ├── deployToEnvironment.groovy
│   └── runTests.groovy
├── src/                     # 源代码
│   └── org/example/
│       └── Utils.groovy
└── resources/               # 资源文件
    └── scripts/
        └── deploy.sh
```

### 2.2 使用示例
```groovy
@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    stages {
        stage('构建') {
            steps {
                buildDockerImage([
                    registry: 'localhost:5001',
                    appName: 'my-app'
                ])
            }
        }
    }
}
```

## 3. 错误处理和重试

### 3.1 重试机制
```groovy
stage('不稳定测试') {
    steps {
        retry(3) {
            sh 'npm test'
        }
    }
}
```

### 3.2 超时控制
```groovy
stage('长时间任务') {
    steps {
        timeout(time: 10, unit: 'MINUTES') {
            sh 'long-running-task.sh'
        }
    }
}
```

### 3.3 错误捕获
```groovy
stage('可能失败的任务') {
    steps {
        script {
            try {
                sh 'risky-command'
            } catch (Exception e) {
                echo "任务失败: ${e.getMessage()}"
                currentBuild.result = 'UNSTABLE'
            }
        }
    }
}
```

## 4. 并行执行

### 4.1 并行阶段
```groovy
stage('并行测试') {
    parallel {
        stage('单元测试') {
            steps {
                sh 'npm run test:unit'
            }
        }
        stage('集成测试') {
            steps {
                sh 'npm run test:integration'
            }
        }
        stage('E2E测试') {
            steps {
                sh 'npm run test:e2e'
            }
        }
    }
}
```

### 4.2 并行构建
```groovy
stage('多平台构建') {
    parallel {
        stage('Linux AMD64') {
            steps {
                sh 'docker buildx build --platform linux/amd64 .'
            }
        }
        stage('Linux ARM64') {
            steps {
                sh 'docker buildx build --platform linux/arm64 .'
            }
        }
    }
}
```

## 5. 条件执行

### 5.1 分支条件
```groovy
stage('部署生产') {
    when {
        anyOf {
            branch 'main'
            branch 'master'
        }
    }
    steps {
        sh 'deploy-to-production.sh'
    }
}
```

### 5.2 环境条件
```groovy
stage('夜间构建') {
    when {
        allOf {
            branch 'develop'
            environment name: 'BUILD_TYPE', value: 'nightly'
        }
    }
    steps {
        sh 'run-full-test-suite.sh'
    }
}
```

### 5.3 自定义条件
```groovy
stage('变更检测') {
    when {
        changeset "src/**"
    }
    steps {
        sh 'build-source-code.sh'
    }
}
```

## 6. 凭据管理

### 6.1 用户名密码
```groovy
stage('部署') {
    steps {
        withCredentials([usernamePassword(
            credentialsId: 'deploy-credentials',
            usernameVariable: 'DEPLOY_USER',
            passwordVariable: 'DEPLOY_PASS'
        )]) {
            sh 'deploy.sh $DEPLOY_USER $DEPLOY_PASS'
        }
    }
}
```

### 6.2 SSH密钥
```groovy
stage('部署') {
    steps {
        withCredentials([sshUserPrivateKey(
            credentialsId: 'ssh-key',
            keyFileVariable: 'SSH_KEY'
        )]) {
            sh 'ssh -i $SSH_KEY user@server deploy.sh'
        }
    }
}
```

### 6.3 Secret文本
```groovy
stage('API调用') {
    steps {
        withCredentials([string(
            credentialsId: 'api-token',
            variable: 'API_TOKEN'
        )]) {
            sh 'curl -H "Authorization: Bearer $API_TOKEN" api.example.com'
        }
    }
}
```

## 7. 制品管理

### 7.1 制品归档
```groovy
post {
    always {
        archiveArtifacts artifacts: 'dist/**', fingerprint: true
    }
}
```

### 7.2 测试结果
```groovy
post {
    always {
        publishTestResults testResultsPattern: 'test-results.xml'
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'coverage',
            reportFiles: 'index.html',
            reportName: 'Coverage Report'
        ])
    }
}
```

## 8. 通知和报告

### 8.1 邮件通知
```groovy
post {
    failure {
        emailext(
            subject: "构建失败: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
            body: "构建失败，请查看: ${env.BUILD_URL}",
            to: "${env.CHANGE_AUTHOR_EMAIL}"
        )
    }
}
```

### 8.2 Slack通知
```groovy
post {
    success {
        slackSend(
            channel: '#ci-cd',
            color: 'good',
            message: "✅ 构建成功: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
        )
    }
}
```

## 9. 性能优化

### 9.1 构建缓存
```groovy
stage('构建') {
    steps {
        // 使用Docker构建缓存
        sh 'docker build --cache-from my-app:latest -t my-app:${BUILD_NUMBER} .'
    }
}
```

### 9.2 工作空间清理
```groovy
options {
    skipDefaultCheckout()
}

stages {
    stage('检出') {
        steps {
            checkout scm
        }
    }
}

post {
    always {
        cleanWs()
    }
}
```

## 10. 调试和监控

### 10.1 调试信息
```groovy
stage('调试') {
    steps {
        script {
            echo "构建号: ${env.BUILD_NUMBER}"
            echo "Git提交: ${env.GIT_COMMIT}"
            echo "分支: ${env.BRANCH_NAME}"
            sh 'env | sort'
        }
    }
}
```

### 10.2 构建监控
```groovy
post {
    always {
        script {
            def duration = currentBuild.duration
            def result = currentBuild.result ?: 'SUCCESS'
            
            echo "构建耗时: ${duration}ms"
            echo "构建结果: ${result}"
        }
    }
}
```
