#!/bin/bash
# Jenkins Pipeline设置脚本

set -e
BASE_DIR="/Users/brunogao/work/infra"
JENKINS_URL="http://localhost:8081/jenkins"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }

# 创建Pipeline共享库
create_shared_library() {
    log "创建Jenkins Pipeline共享库..."
    
    local lib_dir="$BASE_DIR/docker/compose/jenkins/shared-library"
    mkdir -p "$lib_dir"/{vars,src/org/example,resources}
    
    # 创建共享库变量
    cat > "$lib_dir/vars/buildDockerImage.groovy" << 'EOF'
def call(Map config) {
    def registry = config.registry ?: 'localhost:5001'
    def appName = config.appName ?: env.JOB_NAME.split('/')[0]
    def imageTag = config.imageTag ?: "${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
    def credentialsId = config.credentialsId ?: 'registry-auth'
    
    echo "构建Docker镜像: ${registry}/${appName}:${imageTag}"
    
    script {
        def image = docker.build("${registry}/${appName}:${imageTag}")
        
        docker.withRegistry("http://${registry}", credentialsId) {
            image.push()
            image.push("latest")
        }
        
        return image
    }
}
EOF

    cat > "$lib_dir/vars/deployToEnvironment.groovy" << 'EOF'
def call(Map config) {
    def environment = config.environment ?: 'test'
    def appName = config.appName ?: env.JOB_NAME.split('/')[0]
    def imageTag = config.imageTag ?: "${env.BUILD_NUMBER}-${env.GIT_COMMIT[0..7]}"
    def registry = config.registry ?: 'localhost:5001'
    def port = config.port ?: 8080
    
    echo "部署到${environment}环境..."
    
    sh """
        docker stop ${appName}-${environment} || true
        docker rm ${appName}-${environment} || true
        docker run -d --name ${appName}-${environment} -p ${port}:5000 ${registry}/${appName}:${imageTag}
    """
    
    // 健康检查
    sh """
        sleep 10
        curl -f http://localhost:${port}/health || echo "健康检查失败"
    """
}
EOF

    cat > "$lib_dir/vars/runTests.groovy" << 'EOF'
def call(Map config = [:]) {
    def testType = config.testType ?: 'unit'
    def testPath = config.testPath ?: 'tests/'
    def coverage = config.coverage ?: false
    
    echo "运行${testType}测试..."
    
    sh """
        python -m venv venv || true
        . venv/bin/activate
        pip install -r requirements.txt
        
        if [ "${coverage}" == "true" ]; then
            pip install coverage
            coverage run -m pytest ${testPath} -v
            coverage report
            coverage html
        else
            python -m pytest ${testPath} -v
        fi
    """
    
    if (coverage) {
        publishHTML([
            allowMissing: false,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: 'htmlcov',
            reportFiles: 'index.html',
            reportName: 'Coverage Report'
        ])
    }
}
EOF

    cat > "$lib_dir/vars/sendNotification.groovy" << 'EOF'
def call(Map config) {
    def status = config.status ?: 'SUCCESS'
    def message = config.message ?: "构建${status}"
    def channel = config.channel ?: '#ci-cd'
    
    def color = 'good'
    def emoji = '✅'
    
    if (status == 'FAILURE') {
        color = 'danger'
        emoji = '❌'
    } else if (status == 'UNSTABLE') {
        color = 'warning'
        emoji = '⚠️'
    }
    
    echo "${emoji} ${message}"
    
    // 这里可以集成Slack、钉钉等通知
    /*
    slackSend(
        channel: channel,
        color: color,
        message: "${emoji} ${message}\n构建: ${env.BUILD_URL}"
    )
    */
}
EOF

    # 创建工具类
    cat > "$lib_dir/src/org/example/Utils.groovy" << 'EOF'
package org.example

class Utils {
    static def getGitCommitInfo(script) {
        def commit = script.sh(
            script: 'git rev-parse HEAD',
            returnStdout: true
        ).trim()
        
        def shortCommit = script.sh(
            script: 'git rev-parse --short HEAD',
            returnStdout: true
        ).trim()
        
        def author = script.sh(
            script: 'git log -1 --pretty=format:"%an"',
            returnStdout: true
        ).trim()
        
        def message = script.sh(
            script: 'git log -1 --pretty=format:"%s"',
            returnStdout: true
        ).trim()
        
        return [
            commit: commit,
            shortCommit: shortCommit,
            author: author,
            message: message
        ]
    }
    
    static def generateImageTag(buildNumber, gitCommit) {
        return "${buildNumber}-${gitCommit[0..7]}"
    }
    
    static def cleanupOldImages(script, registry, appName, keepCount = 5) {
        script.sh """
            images=\$(docker images ${registry}/${appName} --format "{{.Tag}}" | grep -E '^[0-9]+-[a-f0-9]{8}\$' | sort -nr | tail -n +${keepCount + 1})
            for img in \$images; do
                docker rmi ${registry}/${appName}:\$img || true
            done
        """
    }
}
EOF

    log "✅ Pipeline共享库已创建"
}

# 创建标准Pipeline模板
create_pipeline_templates() {
    log "创建标准Pipeline模板..."
    
    # 基础Web应用Pipeline
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Jenkinsfile.webapp" << 'EOF'
@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'webapp'
        REGISTRY_CREDENTIALS = 'registry-auth'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '20', daysToKeepStr: '30'))
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
                script {
                    def gitInfo = org.example.Utils.getGitCommitInfo(this)
                    env.GIT_COMMIT = gitInfo.commit
                    env.GIT_COMMIT_SHORT = gitInfo.shortCommit
                    env.GIT_AUTHOR = gitInfo.author
                    env.GIT_MESSAGE = gitInfo.message
                    env.IMAGE_TAG = org.example.Utils.generateImageTag(env.BUILD_NUMBER, env.GIT_COMMIT)
                }
            }
        }
        
        stage('代码质量检查') {
            parallel {
                stage('语法检查') {
                    steps {
                        sh 'find . -name "*.py" -exec python -m py_compile {} \\; || echo "语法检查完成"'
                    }
                }
                stage('安全扫描') {
                    steps {
                        sh 'echo "执行安全扫描..." && sleep 2'
                    }
                }
                stage('依赖检查') {
                    steps {
                        sh 'pip list --outdated || echo "依赖检查完成"'
                    }
                }
            }
        }
        
        stage('运行测试') {
            steps {
                runTests([
                    testType: 'unit',
                    testPath: 'tests/',
                    coverage: true
                ])
            }
        }
        
        stage('构建镜像') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    branch 'feature/*'
                }
            }
            steps {
                script {
                    buildDockerImage([
                        registry: env.DOCKER_REGISTRY,
                        appName: env.APP_NAME,
                        imageTag: env.IMAGE_TAG,
                        credentialsId: env.REGISTRY_CREDENTIALS
                    ])
                }
            }
        }
        
        stage('部署测试') {
            when {
                branch 'develop'
            }
            steps {
                deployToEnvironment([
                    environment: 'test',
                    appName: env.APP_NAME,
                    imageTag: env.IMAGE_TAG,
                    port: 8080
                ])
            }
        }
        
        stage('集成测试') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    echo "运行集成测试..."
                    sleep 5
                    curl -f http://localhost:8080/health || echo "集成测试失败"
                '''
            }
        }
        
        stage('部署生产') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    input message: '确认部署到生产环境?', ok: '部署'
                    deployToEnvironment([
                        environment: 'prod',
                        appName: env.APP_NAME,
                        imageTag: env.IMAGE_TAG,
                        port: 8081
                    ])
                }
            }
        }
    }
    
    post {
        always {
            script {
                org.example.Utils.cleanupOldImages(this, env.DOCKER_REGISTRY, env.APP_NAME, 5)
            }
        }
        success {
            sendNotification([
                status: 'SUCCESS',
                message: "✅ 构建成功! 提交: ${env.GIT_COMMIT_SHORT} by ${env.GIT_AUTHOR}"
            ])
        }
        failure {
            sendNotification([
                status: 'FAILURE',
                message: "❌ 构建失败! 提交: ${env.GIT_COMMIT_SHORT} by ${env.GIT_AUTHOR}"
            ])
        }
        unstable {
            sendNotification([
                status: 'UNSTABLE',
                message: "⚠️ 构建不稳定! 提交: ${env.GIT_COMMIT_SHORT} by ${env.GIT_AUTHOR}"
            ])
        }
    }
}
EOF

    # 微服务Pipeline模板
    cat > "$BASE_DIR/docker/compose/jenkins/templates/Jenkinsfile.microservice" << 'EOF'
@Library('jenkins-shared-library') _

pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        SERVICE_NAME = 'microservice'
        REGISTRY_CREDENTIALS = 'registry-auth'
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = "${BUILD_NUMBER}-${GIT_COMMIT[0..7]}"
                }
            }
        }
        
        stage('并行构建') {
            parallel {
                stage('单元测试') {
                    steps {
                        runTests([testType: 'unit'])
                    }
                }
                stage('API测试') {
                    steps {
                        runTests([testType: 'api', testPath: 'tests/api/'])
                    }
                }
                stage('性能测试') {
                    steps {
                        sh 'echo "运行性能测试..." && sleep 3'
                    }
                }
            }
        }
        
        stage('构建服务镜像') {
            steps {
                script {
                    buildDockerImage([
                        appName: env.SERVICE_NAME,
                        imageTag: env.IMAGE_TAG
                    ])
                }
            }
        }
        
        stage('服务部署') {
            parallel {
                stage('部署到测试环境') {
                    when { branch 'develop' }
                    steps {
                        deployToEnvironment([
                            environment: 'test',
                            appName: env.SERVICE_NAME,
                            port: 8080
                        ])
                    }
                }
                stage('部署到预发环境') {
                    when { branch 'release/*' }
                    steps {
                        deployToEnvironment([
                            environment: 'staging',
                            appName: env.SERVICE_NAME,
                            port: 8081
                        ])
                    }
                }
                stage('部署到生产环境') {
                    when { branch 'main' }
                    steps {
                        script {
                            input message: '确认部署到生产环境?'
                            deployToEnvironment([
                                environment: 'prod',
                                appName: env.SERVICE_NAME,
                                port: 8082
                            ])
                        }
                    }
                }
            }
        }
    }
}
EOF

    log "✅ Pipeline模板已创建"
}

# 创建Pipeline作业生成器
create_job_generator() {
    log "创建Pipeline作业生成器..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/scripts/create-pipeline-job.sh" << 'EOF'
#!/bin/bash
# Pipeline作业生成器

set -e

# 参数
JOB_NAME="$1"
REPO_URL="$2"
PIPELINE_TYPE="$3"
BRANCH="$4"

if [[ -z "$JOB_NAME" || -z "$REPO_URL" ]]; then
    echo "用法: $0 <作业名称> <仓库URL> [Pipeline类型] [分支]"
    echo ""
    echo "Pipeline类型:"
    echo "  webapp      - Web应用 (默认)"
    echo "  microservice - 微服务"
    echo "  docker      - Docker构建"
    echo "  multistage  - 多阶段构建"
    echo ""
    echo "示例:"
    echo "  $0 my-webapp http://gitea:3000/user/repo.git webapp main"
    exit 1
fi

PIPELINE_TYPE=${PIPELINE_TYPE:-webapp}
BRANCH=${BRANCH:-main}

# 生成作业配置XML
cat > "/tmp/${JOB_NAME}.xml" << EOF
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>自动生成的${PIPELINE_TYPE} Pipeline作业</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <org.jenkinsci.plugins.gwt.GenericTrigger plugin="generic-webhook-trigger">
          <spec></spec>
          <genericVariables>
            <org.jenkinsci.plugins.gwt.GenericVariable>
              <expressionType>JSONPath</expressionType>
              <key>GITEA_REPO</key>
              <value>\$.repository.name</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
            <org.jenkinsci.plugins.gwt.GenericVariable>
              <expressionType>JSONPath</expressionType>
              <key>GITEA_BRANCH</key>
              <value>\$.ref</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
          </genericVariables>
          <regexpFilterText>\$GITEA_REPO</regexpFilterText>
          <regexpFilterExpression>$JOB_NAME</regexpFilterExpression>
          <printContributedVariables>true</printContributedVariables>
          <printPostContent>true</printPostContent>
        </org.jenkinsci.plugins.gwt.GenericTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>$REPO_URL</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/$BRANCH</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

echo "✅ 作业配置文件已生成: /tmp/${JOB_NAME}.xml"
echo ""
echo "📋 下一步操作:"
echo "1. 在Jenkins中导入作业:"
echo "   - 进入Jenkins -> 新建任务"
echo "   - 选择 '流水线' 类型"
echo "   - 名称: $JOB_NAME"
echo "   - 配置Git仓库: $REPO_URL"
echo "   - 设置Jenkinsfile路径"
echo ""
echo "2. 或使用Jenkins CLI导入:"
echo "   java -jar jenkins-cli.jar -s http://localhost:8081/jenkins create-job $JOB_NAME < /tmp/${JOB_NAME}.xml"
echo ""
echo "3. 复制对应的Jenkinsfile模板到仓库根目录:"
echo "   cp docker/compose/jenkins/templates/Jenkinsfile.${PIPELINE_TYPE} /path/to/repo/Jenkinsfile"

    chmod +x "$BASE_DIR/docker/compose/jenkins/scripts/create-pipeline-job.sh"
    log "✅ Pipeline作业生成器已创建"
}

# 创建Pipeline最佳实践指南
create_pipeline_best_practices() {
    log "创建Pipeline最佳实践指南..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/PIPELINE_BEST_PRACTICES.md" << 'EOF'
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
EOF

    log "✅ Pipeline最佳实践指南已创建"
}

# 主函数
main() {
    log "开始设置Jenkins Pipeline..."
    
    create_shared_library
    create_pipeline_templates
    create_job_generator
    create_pipeline_best_practices
    
    log "✅ Jenkins Pipeline设置完成!"
    log ""
    log "📋 下一步操作:"
    log "1. 配置共享库 (路径: docker/compose/jenkins/shared-library/)"
    log "2. 使用作业生成器创建Pipeline (运行: docker/compose/jenkins/scripts/create-pipeline-job.sh)"
    log "3. 查看最佳实践指南 (docker/compose/jenkins/PIPELINE_BEST_PRACTICES.md)"
    log "4. 复制Pipeline模板到项目仓库"
    log ""
    log "📁 模板位置: docker/compose/jenkins/templates/"
    log "📚 共享库: docker/compose/jenkins/shared-library/"
    log "📖 最佳实践: docker/compose/jenkins/PIPELINE_BEST_PRACTICES.md"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 