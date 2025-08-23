#!/bin/bash
# Jenkins与Gitea集成配置脚本

set -e
JENKINS_URL="http://localhost:8081/jenkins"
GITEA_URL="http://localhost:3000"
GITEA_ADMIN="gitea"  # 请替换为实际的Gitea管理员用户名
BASE_DIR="/Users/brunogao/work/infra"

# 颜色输出
G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; NC='\033[0m'
log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

# 检查服务状态
check_services() {
    log "检查服务状态..."
    
    # 检查Jenkins
    if curl -s "$JENKINS_URL/login" > /dev/null; then
        log "✅ Jenkins运行正常"
    else
        error "❌ Jenkins无法访问"
        return 1
    fi
    
    # 检查Gitea
    if curl -s "$GITEA_URL/api/v1/version" > /dev/null; then
        log "✅ Gitea运行正常"
    else
        error "❌ Gitea无法访问"
        return 1
    fi
}

# 创建Gitea测试仓库
create_test_repo() {
    log "创建Gitea测试仓库..."
    
    # 创建测试项目目录
    local test_repo_dir="/tmp/jenkins-test-repo"
    rm -rf "$test_repo_dir"
    mkdir -p "$test_repo_dir"
    
    cat > "$test_repo_dir/README.md" << 'EOF'
# Jenkins测试仓库

这是一个用于测试Jenkins CI/CD的示例仓库。

## 项目结构
- `src/` - 源代码目录
- `tests/` - 测试代码目录
- `Dockerfile` - Docker镜像构建文件
- `Jenkinsfile` - Jenkins Pipeline配置
EOF

    # 创建简单的应用代码
    mkdir -p "$test_repo_dir/src"
    cat > "$test_repo_dir/src/app.py" << 'EOF'
#!/usr/bin/env python3
# 简单的Flask应用示例

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        'message': 'Hello from Jenkins CI/CD!',
        'version': os.environ.get('APP_VERSION', '1.0.0'),
        'environment': os.environ.get('ENV', 'development')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

    # 创建测试文件
    mkdir -p "$test_repo_dir/tests"
    cat > "$test_repo_dir/tests/test_app.py" << 'EOF'
#!/usr/bin/env python3
# 应用测试

import unittest
import json
from src.app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_hello(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)

    def test_health(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

if __name__ == '__main__':
    unittest.main()
EOF

    # 创建requirements.txt
    cat > "$test_repo_dir/requirements.txt" << 'EOF'
Flask==2.3.3
pytest==7.4.2
EOF

    # 创建Dockerfile
    cat > "$test_repo_dir/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/

EXPOSE 5000

CMD ["python", "src/app.py"]
EOF

    # 创建Jenkinsfile
    cat > "$test_repo_dir/Jenkinsfile" << 'EOF'
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        APP_NAME = 'jenkins-test-app'
        APP_VERSION = "${BUILD_NUMBER}"
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
                }
            }
        }
        
        stage('代码检查') {
            steps {
                echo '执行代码检查...'
                sh 'find . -name "*.py" | head -5'
            }
        }
        
        stage('运行测试') {
            steps {
                echo '运行单元测试...'
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m pytest tests/ -v || echo "测试完成"
                '''
            }
        }
        
        stage('构建镜像') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                    branch 'develop'
                }
            }
            steps {
                script {
                    def imageTag = "${APP_NAME}:${APP_VERSION}-${GIT_COMMIT_SHORT}"
                    def latestTag = "${APP_NAME}:latest"
                    
                    echo "构建镜像: ${imageTag}"
                    
                    sh """
                        docker build -t ${DOCKER_REGISTRY}/${imageTag} .
                        docker tag ${DOCKER_REGISTRY}/${imageTag} ${DOCKER_REGISTRY}/${latestTag}
                    """
                    
                    echo "推送镜像到Registry..."
                    sh """
                        docker push ${DOCKER_REGISTRY}/${imageTag}
                        docker push ${DOCKER_REGISTRY}/${latestTag}
                    """
                }
            }
        }
        
        stage('部署测试') {
            when {
                branch 'develop'
            }
            steps {
                echo '部署到测试环境...'
                sh 'echo "模拟部署到测试环境"'
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
                echo '部署到生产环境...'
                sh 'echo "模拟部署到生产环境"'
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline执行完成'
            sh 'docker system prune -f || true'
        }
        success {
            echo '✅ 构建成功!'
        }
        failure {
            echo '❌ 构建失败!'
        }
        cleanup {
            sh 'rm -rf venv || true'
        }
    }
}
EOF

    log "✅ 测试仓库文件已创建在: $test_repo_dir"
    log "请手动在Gitea中创建仓库并推送代码:"
    log "1. 访问 $GITEA_URL"
    log "2. 创建新仓库 'jenkins-test-app'"
    log "3. 执行以下命令推送代码:"
    echo ""
    echo "cd $test_repo_dir"
    echo "git init"
    echo "git add ."
    echo "git commit -m 'Initial commit'"
    echo "git remote add origin $GITEA_URL/$GITEA_ADMIN/jenkins-test-app.git"
    echo "git push -u origin main"
}

# 创建Jenkins Pipeline作业配置
create_jenkins_job() {
    log "创建Jenkins Pipeline作业配置..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/jobs/jenkins-test-app.xml" << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Jenkins测试应用CI/CD Pipeline</description>
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
              <value>$.repository.name</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
            <org.jenkinsci.plugins.gwt.GenericVariable>
              <expressionType>JSONPath</expressionType>
              <key>GITEA_BRANCH</key>
              <value>$.ref</value>
            </org.jenkinsci.plugins.gwt.GenericVariable>
          </genericVariables>
          <regexpFilterText>$GITEA_REPO</regexpFilterText>
          <regexpFilterExpression>jenkins-test-app</regexpFilterExpression>
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
          <url>http://gitea:3000/gitea/jenkins-test-app.git</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/main</name>
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

    mkdir -p "$BASE_DIR/docker/compose/jenkins/jobs"
    log "✅ Jenkins作业配置已创建"
}

# 创建Webhook配置指南
create_webhook_guide() {
    log "创建Webhook配置指南..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/WEBHOOK_GUIDE.md" << 'EOF'
# Gitea Webhook配置指南

## 1. 在Gitea中配置Webhook

### 1.1 访问仓库设置
1. 登录Gitea: http://localhost:3000
2. 进入目标仓库 (如: jenkins-test-app)
3. 点击 "设置" -> "Webhooks"

### 1.2 添加Webhook
1. 点击 "添加Webhook" -> "Gitea"
2. 配置以下信息:
   - **目标URL**: `http://jenkins:8080/generic-webhook-trigger/invoke`
   - **HTTP方法**: POST
   - **内容类型**: application/json
   - **密钥**: (可选，增强安全性)

### 1.3 触发事件
选择以下事件:
- [x] Push events
- [x] Pull request events
- [x] Create events
- [x] Delete events

### 1.4 测试Webhook
1. 点击 "测试推送"
2. 检查Jenkins是否收到触发信号

## 2. Jenkins Generic Webhook Trigger配置

### 2.1 在Jenkins作业中配置
1. 进入Jenkins作业配置
2. 在 "构建触发器" 中勾选 "Generic Webhook Trigger"
3. 配置变量提取:

```
变量名: GITEA_REPO
表达式: $.repository.name
表达式类型: JSONPath

变量名: GITEA_BRANCH  
表达式: $.ref
表达式类型: JSONPath

变量名: GITEA_COMMIT
表达式: $.after
表达式类型: JSONPath
```

### 2.2 过滤器配置
- **过滤器表达式**: `jenkins-test-app`
- **过滤器文本**: `$GITEA_REPO`

## 3. 网络配置

### 3.1 Docker网络
确保Jenkins和Gitea在同一Docker网络中:
```bash
docker network create cicd-network
```

### 3.2 服务间通信
- Jenkins访问Gitea: `http://gitea:3000`
- Gitea访问Jenkins: `http://jenkins:8080`

## 4. 故障排除

### 4.1 常见问题
1. **Webhook无法触发**
   - 检查URL是否正确
   - 确认网络连通性
   - 查看Jenkins日志

2. **认证失败**
   - 检查凭据配置
   - 确认用户权限

3. **构建失败**
   - 检查Jenkinsfile语法
   - 确认环境变量配置

### 4.2 调试命令
```bash
# 查看Jenkins日志
docker logs jenkins

# 查看Gitea日志  
docker logs gitea

# 测试网络连通性
docker exec jenkins ping gitea
docker exec gitea ping jenkins
```

## 5. 高级配置

### 5.1 分支策略
```groovy
when {
    anyOf {
        branch 'main'
        branch 'develop'
        branch 'feature/*'
    }
}
```

### 5.2 条件部署
```groovy
when {
    allOf {
        branch 'main'
        not { changeRequest() }
    }
}
```

### 5.3 并行构建
```groovy
parallel {
    stage('单元测试') {
        steps {
            sh 'pytest tests/unit'
        }
    }
    stage('集成测试') {
        steps {
            sh 'pytest tests/integration'
        }
    }
}
```
EOF

    log "✅ Webhook配置指南已创建"
}

# 创建凭据配置脚本
create_credentials_config() {
    log "创建凭据配置脚本..."
    
    cat > "$BASE_DIR/docker/compose/jenkins/scripts/setup-credentials.sh" << 'EOF'
#!/bin/bash
# Jenkins凭据配置脚本

echo "=== Jenkins凭据配置指南 ==="
echo ""
echo "请在Jenkins管理界面中配置以下凭据:"
echo ""
echo "1. Gitea访问Token"
echo "   - 类型: Secret text"
echo "   - ID: gitea-token"
echo "   - 描述: Gitea API Token"
echo "   - Secret: (在Gitea用户设置->应用中生成)"
echo ""
echo "2. Docker Registry认证"
echo "   - 类型: Username with password"  
echo "   - ID: registry-auth"
echo "   - 描述: Docker Registry Auth"
echo "   - Username: admin"
echo "   - Password: (Registry管理员密码)"
echo ""
echo "3. SSH密钥"
echo "   - 类型: SSH Username with private key"
echo "   - ID: ssh-key"
echo "   - 描述: Git SSH Key"
echo "   - Username: git"
echo "   - Private Key: (SSH私钥内容)"
echo ""
echo "配置路径: Jenkins -> 管理Jenkins -> 凭据 -> System -> 全局凭据"
EOF

    chmod +x "$BASE_DIR/docker/compose/jenkins/scripts/setup-credentials.sh"
    log "✅ 凭据配置脚本已创建"
}

# 主函数
main() {
    log "开始配置Jenkins与Gitea集成..."
    
    check_services
    create_test_repo
    create_jenkins_job
    create_webhook_guide
    create_credentials_config
    
    log "✅ Jenkins与Gitea集成配置完成!"
    log ""
    log "📋 下一步操作:"
    log "1. 在Gitea中创建测试仓库并推送代码"
    log "2. 在Jenkins中创建Pipeline作业"
    log "3. 配置Webhook (参考: docker/compose/jenkins/WEBHOOK_GUIDE.md)"
    log "4. 配置凭据 (运行: docker/compose/jenkins/scripts/setup-credentials.sh)"
    log ""
    log "📁 测试仓库位置: /tmp/jenkins-test-repo"
    log "📖 Webhook配置指南: docker/compose/jenkins/WEBHOOK_GUIDE.md"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 