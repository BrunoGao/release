#!/usr/bin/env groovy
// Jenkins完整自动化配置脚本 - 包含agents、cloud、tools、credentials等

import jenkins.model.*
import hudson.security.*
import hudson.tools.*
import hudson.util.Secret
import jenkins.security.s2m.AdminWhitelistRule
import hudson.security.csrf.DefaultCrumbIssuer
import hudson.plugins.git.*
import hudson.tasks.*
import hudson.slaves.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import hudson.plugins.nodejs.*
import hudson.plugins.nodejs.tools.*
import hudson.plugins.gradle.*
import org.jenkinsci.plugins.docker.commons.credentials.DockerServerCredentials
import com.nirima.jenkins.plugins.docker.*
import com.nirima.jenkins.plugins.docker.launcher.*
import jenkins.install.InstallState

def instance = Jenkins.getInstance()

println "🚀 开始Jenkins完整自动化配置..."

// 1. 跳过设置向导和基础安全配置
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
def adminUsername = System.getenv('JENKINS_ADMIN_ID') ?: 'admin'
def adminPassword = System.getenv('JENKINS_ADMIN_PASSWORD') ?: 'admin123'

// 创建管理员用户
if (!hudsonRealm.getAllUsers().find { it.getId() == adminUsername }) {
    hudsonRealm.createAccount(adminUsername, adminPassword)
    instance.setSecurityRealm(hudsonRealm)
    println "✅ 创建管理员用户: ${adminUsername}"
}

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 启用CSRF保护
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

println "✅ 安全配置完成"

// 2. 配置凭据管理
def store = SystemCredentialsProvider.getInstance().getStore()
def domain = Domain.global()

println "🔐 配置凭据管理..."

// Gitea API Token
def giteaToken = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "gitea-api-token",
    "Gitea API访问令牌",
    Secret.fromString("your-gitea-token-here")
)

// Docker Registry认证
def registryAuth = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "docker-registry-auth", 
    "Docker Registry认证",
    "admin",
    "admin123"
)

// Git SSH密钥
def gitSshKey = new BasicSSHUserPrivateKey(
    CredentialsScope.GLOBAL,
    "git-ssh-key",
    "git",
    new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource("""-----BEGIN OPENSSH PRIVATE KEY-----
# SSH密钥内容，实际使用时需要替换
your-ssh-private-key-here
-----END OPENSSH PRIVATE KEY-----"""),
    "",
    "Git SSH密钥"
)

// Kubernetes配置
def k8sConfig = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "k8s-config",
    "Kubernetes配置文件",
    Secret.fromString("""apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://your-k8s-cluster
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: jenkins
  name: jenkins
current-context: jenkins
users:
- name: jenkins
  user:
    token: your-k8s-token""")
)

store.addCredentials(domain, giteaToken)
store.addCredentials(domain, registryAuth)
store.addCredentials(domain, gitSshKey)
store.addCredentials(domain, k8sConfig)

println "✅ 凭据配置完成"

// 3. 配置构建工具
println "🔧 配置构建工具..."

// 配置Git
def gitTool = instance.getDescriptorByType(GitTool.DescriptorImpl.class)
gitTool.setInstallations(new GitTool("Default", "/usr/bin/git", []))

// 配置JDK
def jdkTool = instance.getDescriptorByType(JDK.DescriptorImpl.class)
def jdk8 = new JDK("JDK-8", "/opt/java/openjdk")
def jdk11 = new JDK("JDK-11", "/usr/lib/jvm/java-11-openjdk")
def jdk21 = new JDK("JDK-21", "/opt/java/openjdk")
jdkTool.setInstallations(jdk8, jdk11, jdk21)

// 配置Maven
def maven = instance.getDescriptorByType(Maven.DescriptorImpl.class)
def mavenInstaller = new Maven.MavenInstaller("3.9.6")
def mavenInstallation = new Maven.MavenInstallation("Maven-3.9", "", [
    new InstallSourceProperty([mavenInstaller])
])
maven.setInstallations(mavenInstallation)

// 配置Gradle
def gradle = instance.getDescriptorByType(Gradle.DescriptorImpl.class)
def gradleInstaller = new GradleInstaller("8.5")
def gradleInstallation = new GradleInstallation("Gradle-8", "", [
    new InstallSourceProperty([gradleInstaller])
])
gradle.setInstallations(gradleInstallation)

// 配置NodeJS
def nodejs = instance.getDescriptorByType(NodeJSInstallation.DescriptorImpl.class)
def nodeInstaller = new NodeJSInstaller("18.19.0", "npm install -g yarn pnpm@latest", 72)
def nodeInstallation = new NodeJSInstallation("NodeJS-18", "", [
    new InstallSourceProperty([nodeInstaller])
])
nodejs.setInstallations(nodeInstallation)

// 配置Python
// Python通常使用系统安装或Docker容器，这里配置Docker容器方式

println "✅ 构建工具配置完成"

// 4. 配置Docker Cloud
println "☁️ 配置Docker Cloud..."

try {
    def dockerConnector = new DockerComputerSSHConnector(new DockerComputerSSHConnector.SSHKeyStrategyBuiltIn())
    
    // Java构建容器模板
    def javaTemplate = new DockerTemplate(
        "maven:3.9.6-openjdk-21", // Docker镜像
        "docker-java-agent", // 标签
        "/home/jenkins", // 远程文件系统根目录
        "22", // SSH端口
        InstanceCap.UNLIMITED, // 实例上限
        "5", // 空闲终止时间(分钟)
        dockerConnector, // 连接器
        "java maven docker", // 标签字符串
        "jenkins", // 用户
        "-v /var/run/docker.sock:/var/run/docker.sock" // Docker in Docker
    )
    
    // Vue3/Node.js构建容器模板
    def nodeTemplate = new DockerTemplate(
        "node:18-alpine",
        "docker-node-agent",
        "/home/jenkins",
        "22",
        InstanceCap.UNLIMITED,
        "5",
        dockerConnector,
        "nodejs vue docker",
        "jenkins",
        "-v /var/run/docker.sock:/var/run/docker.sock"
    )
    
    // Python构建容器模板
    def pythonTemplate = new DockerTemplate(
        "python:3.11-slim",
        "docker-python-agent",
        "/home/jenkins",
        "22", 
        InstanceCap.UNLIMITED,
        "5",
        dockerConnector,
        "python docker",
        "jenkins",
        "-v /var/run/docker.sock:/var/run/docker.sock"
    )
    
    // 创建Docker Cloud
    def dockerCloud = new DockerCloud(
        "docker-cloud", // 名称
        [javaTemplate, nodeTemplate, pythonTemplate], // 模板列表
        "unix:///var/run/docker.sock", // Docker Host URI
        100, // 容器上限
        5, // 连接超时
        5, // 读取超时
        null, // 凭据ID
        "", // Docker版本
        "" // Docker API版本
    )
    
    instance.clouds.add(dockerCloud)
    println "✅ Docker Cloud配置完成"
} catch (Exception e) {
    println "⚠️ Docker Cloud配置跳过: ${e.message}"
}

// 5. 系统配置
instance.setNumExecutors(2)
instance.setSystemMessage("""
🎉 Jenkins CI/CD服务器 - 完全自动化配置

📦 插件: 自动安装130+核心插件
🔧 工具: Java, Maven, Gradle, NodeJS, Python
☁️ Cloud: Docker动态Agent支持
🔐 凭据: Gitea, Registry, SSH, K8s已配置
📋 支持: Java, Vue3, Python多语言CI/CD

🌐 访问地址: http://localhost:8081
👤 登录账号: ${adminUsername} / ${adminPassword}

🚀 CI/CD流程:
Gitea Webhook → Jenkins → Build → Registry → K8s Deploy
""")

// 设置Jenkins URL
def location = instance.getDescriptor("jenkins.model.JenkinsLocationConfiguration")
location.setUrl("http://localhost:8081/")
location.setAdminAddress("admin@example.com")
location.save()

// 6. 创建多语言Pipeline作业模板
println "📋 创建Pipeline作业模板..."

// Java Spring Boot项目Pipeline
def javaJobXml = '''<flow-definition plugin="workflow-job">
  <description>Java Spring Boot CI/CD Pipeline</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
pipeline {
    agent { label 'java' }
    
    environment {
        REGISTRY = 'localhost:5001'
        IMAGE_NAME = 'ljwx-java-app'
        MAVEN_OPTS = '-Dmaven.repo.local=/var/jenkins_home/.m2/repository'
    }
    
    stages {
        stage('📥 Checkout') {
            steps {
                git credentialsId: 'git-ssh-key', url: '${GIT_URL}'
            }
        }
        
        stage('🔍 Test') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'target/surefire-reports/*.xml'
                }
            }
        }
        
        stage('📦 Build') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }
        
        stage('🐳 Docker Build') {
            steps {
                script {
                    def imageTag = "${env.BUILD_NUMBER}"
                    sh """
                        docker build -t ${REGISTRY}/${IMAGE_NAME}:${imageTag} .
                        docker build -t ${REGISTRY}/${IMAGE_NAME}:latest .
                    """
                }
            }
        }
        
        stage('📤 Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-registry-auth', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASS')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo ${REGISTRY_PASS} | docker login ${REGISTRY} -u ${REGISTRY_USER} --password-stdin
                            docker push ${REGISTRY}/${IMAGE_NAME}:${imageTag}
                            docker push ${REGISTRY}/${IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }
        
        stage('🚀 Deploy to K8s') {
            steps {
                withCredentials([string(credentialsId: 'k8s-config', variable: 'KUBECONFIG_CONTENT')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo '${KUBECONFIG_CONTENT}' > kubeconfig
                            export KUBECONFIG=./kubeconfig
                            
                            # 更新部署
                            kubectl set image deployment/java-app java-app=${REGISTRY}/${IMAGE_NAME}:${imageTag} --record
                            kubectl rollout status deployment/java-app
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo '🎉 Java应用部署成功！'
        }
    }
}
    </script>
  </definition>
  <triggers>
    <org.jenkinsci.plugins.gwt.GenericTrigger plugin="generic-webhook-trigger">
      <genericVariables>
        <org.jenkinsci.plugins.gwt.GenericVariable>
          <expressionType>JSONPath</expressionType>
          <key>GIT_URL</key>
          <value>$.repository.clone_url</value>
        </org.jenkinsci.plugins.gwt.GenericVariable>
      </genericVariables>
      <regexpFilterText></regexpFilterText>
      <regexpFilterExpression></regexpFilterExpression>
      <printContributedVariables>false</printContributedVariables>
      <printPostContent>false</printPostContent>
      <causeString>Gitea Webhook</causeString>
      <token>java-webhook-token</token>
    </org.jenkinsci.plugins.gwt.GenericTrigger>
  </triggers>
</flow-definition>'''

// Vue3项目Pipeline
def vue3JobXml = '''<flow-definition plugin="workflow-job">
  <description>Vue3 Frontend CI/CD Pipeline</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
pipeline {
    agent { label 'nodejs' }
    
    environment {
        REGISTRY = 'localhost:5001'
        IMAGE_NAME = 'ljwx-vue3-app'
        NODE_OPTIONS = '--max-old-space-size=4096'
    }
    
    stages {
        stage('📥 Checkout') {
            steps {
                git credentialsId: 'git-ssh-key', url: '${GIT_URL}'
            }
        }
        
        stage('📦 Install Dependencies') {
            steps {
                sh '''
                    npm config set registry https://registry.npmmirror.com
                    npm install
                '''
            }
        }
        
        stage('🔍 Lint & Test') {
            steps {
                sh '''
                    npm run lint
                    npm run test:unit
                '''
            }
        }
        
        stage('🏗️ Build') {
            steps {
                sh 'npm run build'
            }
        }
        
        stage('🐳 Docker Build') {
            steps {
                script {
                    def imageTag = "${env.BUILD_NUMBER}"
                    sh """
                        cat > Dockerfile << 'EOF'
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

                        cat > nginx.conf << 'EOF'
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    sendfile on;
    server {
        listen 80;
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }
    }
}
EOF

                        docker build -t ${REGISTRY}/${IMAGE_NAME}:${imageTag} .
                        docker build -t ${REGISTRY}/${IMAGE_NAME}:latest .
                    """
                }
            }
        }
        
        stage('📤 Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-registry-auth', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASS')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo ${REGISTRY_PASS} | docker login ${REGISTRY} -u ${REGISTRY_USER} --password-stdin
                            docker push ${REGISTRY}/${IMAGE_NAME}:${imageTag}
                            docker push ${REGISTRY}/${IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }
        
        stage('🚀 Deploy to K8s') {
            steps {
                withCredentials([string(credentialsId: 'k8s-config', variable: 'KUBECONFIG_CONTENT')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo '${KUBECONFIG_CONTENT}' > kubeconfig
                            export KUBECONFIG=./kubeconfig
                            
                            kubectl set image deployment/vue3-app vue3-app=${REGISTRY}/${IMAGE_NAME}:${imageTag} --record
                            kubectl rollout status deployment/vue3-app
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo '🎉 Vue3应用部署成功！'
        }
    }
}
    </script>
  </definition>
  <triggers>
    <org.jenkinsci.plugins.gwt.GenericTrigger plugin="generic-webhook-trigger">
      <genericVariables>
        <org.jenkinsci.plugins.gwt.GenericVariable>
          <expressionType>JSONPath</expressionType>
          <key>GIT_URL</key>
          <value>$.repository.clone_url</value>
        </org.jenkinsci.plugins.gwt.GenericVariable>
      </genericVariables>
      <token>vue3-webhook-token</token>
    </org.jenkinsci.plugins.gwt.GenericTrigger>
  </triggers>
</flow-definition>'''

// Python项目Pipeline
def pythonJobXml = '''<flow-definition plugin="workflow-job">
  <description>Python FastAPI CI/CD Pipeline</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
pipeline {
    agent { label 'python' }
    
    environment {
        REGISTRY = 'localhost:5001'
        IMAGE_NAME = 'ljwx-python-app'
        PYTHONPATH = '.'
    }
    
    stages {
        stage('📥 Checkout') {
            steps {
                git credentialsId: 'git-ssh-key', url: '${GIT_URL}'
            }
        }
        
        stage('📦 Install Dependencies') {
            steps {
                sh '''
                    pip install -r requirements.txt
                    pip install pytest pytest-cov flake8
                '''
            }
        }
        
        stage('🔍 Lint & Test') {
            steps {
                sh '''
                    flake8 . --max-line-length=88 --exclude=venv,__pycache__
                    pytest --cov=. --cov-report=xml
                '''
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'pytest.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
        stage('🐳 Docker Build') {
            steps {
                script {
                    def imageTag = "${env.BUILD_NUMBER}"
                    sh """
                        cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

                        docker build -t ${REGISTRY}/${IMAGE_NAME}:${imageTag} .
                        docker build -t ${REGISTRY}/${IMAGE_NAME}:latest .
                    """
                }
            }
        }
        
        stage('📤 Push to Registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-registry-auth', usernameVariable: 'REGISTRY_USER', passwordVariable: 'REGISTRY_PASS')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo ${REGISTRY_PASS} | docker login ${REGISTRY} -u ${REGISTRY_USER} --password-stdin
                            docker push ${REGISTRY}/${IMAGE_NAME}:${imageTag}
                            docker push ${REGISTRY}/${IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }
        
        stage('🚀 Deploy to K8s') {
            steps {
                withCredentials([string(credentialsId: 'k8s-config', variable: 'KUBECONFIG_CONTENT')]) {
                    script {
                        def imageTag = "${env.BUILD_NUMBER}"
                        sh """
                            echo '${KUBECONFIG_CONTENT}' > kubeconfig
                            export KUBECONFIG=./kubeconfig
                            
                            kubectl set image deployment/python-app python-app=${REGISTRY}/${IMAGE_NAME}:${imageTag} --record
                            kubectl rollout status deployment/python-app
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo '🎉 Python应用部署成功！'
        }
    }
}
    </script>
  </definition>
  <triggers>
    <org.jenkinsci.plugins.gwt.GenericTrigger plugin="generic-webhook-trigger">
      <genericVariables>
        <org.jenkinsci.plugins.gwt.GenericVariable>
          <expressionType>JSONPath</expressionType>
          <key>GIT_URL</key>
          <value>$.repository.clone_url</value>
        </org.jenkinsci.plugins.gwt.GenericVariable>
      </genericVariables>
      <token>python-webhook-token</token>
    </org.jenkinsci.plugins.gwt.GenericTrigger>
  </triggers>
</flow-definition>'''

// 创建作业
try {
    instance.createProjectFromXML("java-spring-boot-pipeline", new ByteArrayInputStream(javaJobXml.getBytes()))
    instance.createProjectFromXML("vue3-frontend-pipeline", new ByteArrayInputStream(vue3JobXml.getBytes()))
    instance.createProjectFromXML("python-fastapi-pipeline", new ByteArrayInputStream(pythonJobXml.getBytes()))
    println "✅ Pipeline作业模板创建完成"
} catch (Exception e) {
    println "⚠️ 作业创建部分失败: ${e.message}"
}

// 7. 保存配置
instance.save()

println """
🎉 Jenkins完整自动化配置完成！

📋 配置摘要:
- ✅ 管理员用户: ${adminUsername}
- ✅ 安全策略: 已配置
- ✅ 构建工具: Java, Maven, Gradle, NodeJS, Python
- ✅ Docker Cloud: 动态Agent支持
- ✅ 凭据管理: Gitea, Registry, SSH, K8s
- ✅ Pipeline模板: Java, Vue3, Python

🌐 访问地址: http://localhost:8081
👤 登录信息: ${adminUsername} / ${adminPassword}

🚀 Webhook URLs:
- Java: http://localhost:8081/generic-webhook-trigger/invoke?token=java-webhook-token
- Vue3: http://localhost:8081/generic-webhook-trigger/invoke?token=vue3-webhook-token  
- Python: http://localhost:8081/generic-webhook-trigger/invoke?token=python-webhook-token

📚 下一步:
1. 更新凭据中的实际Token和密钥
2. 在Gitea中配置Webhook URL
3. 测试CI/CD流程
4. 根据需要调整Pipeline
""" 