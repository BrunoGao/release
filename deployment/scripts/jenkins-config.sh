#!/bin/bash
# Jenkins自动化配置脚本

set -e
JENKINS_URL="http://localhost:8081/jenkins"
JENKINS_CLI_JAR="/tmp/jenkins-cli.jar"
ADMIN_USER="admin"
ADMIN_PASS="admin123"  # 从jenkins.env读取

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 等待Jenkins启动
wait_jenkins() {
    log "等待Jenkins启动..."
    for i in {1..60}; do
        if curl -s "$JENKINS_URL/login" > /dev/null 2>&1; then
            log "Jenkins已启动"
            return 0
        fi
        sleep 5
    done
    error "Jenkins启动超时"
    return 1
}

# 下载Jenkins CLI
download_cli() {
    log "下载Jenkins CLI..."
    curl -s "$JENKINS_URL/jnlpJars/jenkins-cli.jar" -o "$JENKINS_CLI_JAR"
}

# 执行Jenkins CLI命令
jenkins_cli() {
    java -jar "$JENKINS_CLI_JAR" -s "$JENKINS_URL" -auth "$ADMIN_USER:$ADMIN_PASS" "$@"
}

# 安装必要插件
install_plugins() {
    log "安装必要插件..."
    local plugins=(
        "configuration-as-code"
        "job-dsl"
        "pipeline-stage-view"
        "blueocean"
        "gitea"
        "docker-plugin"
        "docker-workflow"
        "credentials-binding"
        "timestamper"
        "ws-cleanup"
        "build-timeout"
        "ant"
        "gradle"
        "maven-plugin"
        "nodejs"
        "python"
        "generic-webhook-trigger"
        "pipeline-utility-steps"
        "http_request"
        "email-ext"
        "slack"
    )
    
    for plugin in "${plugins[@]}"; do
        log "安装插件: $plugin"
        jenkins_cli install-plugin "$plugin" || warn "插件 $plugin 安装失败"
    done
    
    log "重启Jenkins以激活插件..."
    jenkins_cli restart
    wait_jenkins
}

# 创建管理员用户
create_admin_user() {
    log "配置管理员用户..."
    
    # 创建用户创建脚本
    cat > /tmp/create-admin.groovy << 'EOF'
import jenkins.model.*
import hudson.security.*
import hudson.security.csrf.DefaultCrumbIssuer
import jenkins.security.s2m.AdminWhitelistRule

def instance = Jenkins.getInstance()

// 启用CSRF保护
instance.setCrumbIssuer(new DefaultCrumbIssuer(true))

// 配置安全策略
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin123")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 禁用脚本安全
instance.getDescriptor("org.jenkinsci.plugins.scriptsecurity.scripts.ScriptApproval").setEnabled(false)

instance.save()
EOF
    
    jenkins_cli groovy /tmp/create-admin.groovy
    rm /tmp/create-admin.groovy
}

# 配置系统设置
configure_system() {
    log "配置系统设置..."
    
    cat > /tmp/system-config.groovy << 'EOF'
import jenkins.model.*
import hudson.model.*

def instance = Jenkins.getInstance()

// 设置系统消息
instance.setSystemMessage("Jenkins CI/CD服务器 - Mac Studio M2 环境")

// 配置执行器数量
instance.setNumExecutors(4)

// 配置安静期
instance.setQuietPeriod(5)

// 配置SCM检出重试次数
instance.setScmCheckoutRetryCount(3)

// 设置Jenkins URL
def jlc = JenkinsLocationConfiguration.get()
jlc.setUrl("http://localhost:8081/jenkins/")
jlc.setAdminAddress("admin@example.com")
jlc.save()

instance.save()
EOF
    
    jenkins_cli groovy /tmp/system-config.groovy
    rm /tmp/system-config.groovy
}

# 配置全局工具
configure_tools() {
    log "配置全局工具..."
    
    cat > /tmp/tools-config.groovy << 'EOF'
import jenkins.model.*
import hudson.model.*
import hudson.tools.*
import hudson.plugins.git.*
import hudson.plugins.gradle.*
import hudson.tasks.Maven.*
import org.jenkinsci.plugins.docker.commons.tools.*

def instance = Jenkins.getInstance()

// 配置Git
def gitInstallation = new GitTool("Default", "/usr/bin/git", [])
def gitDescriptor = instance.getDescriptor(GitTool.class)
gitDescriptor.setInstallations(gitInstallation)
gitDescriptor.save()

// 配置Docker
def dockerInstallation = new DockerTool("Docker", "/usr/local/bin/docker", [])
def dockerDescriptor = instance.getDescriptor(DockerTool.class)
dockerDescriptor.setInstallations(dockerInstallation)
dockerDescriptor.save()

instance.save()
EOF
    
    jenkins_cli groovy /tmp/tools-config.groovy
    rm /tmp/tools-config.groovy
}

# 配置凭据
configure_credentials() {
    log "配置凭据..."
    
    cat > /tmp/credentials-config.groovy << 'EOF'
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*

def instance = Jenkins.getInstance()
def domain = Domain.global()
def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// 创建Gitea Token凭据
def giteaToken = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "gitea-token",
    "Gitea API Token",
    "your-gitea-token-here"
)

// 创建Registry凭据
def registryCredentials = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "registry-auth",
    "Docker Registry Auth",
    "admin",
    "your-registry-password"
)

// 创建SSH密钥凭据
def sshKey = new BasicSSHUserPrivateKey(
    CredentialsScope.GLOBAL,
    "ssh-key",
    "jenkins",
    new BasicSSHUserPrivateKey.UsersPrivateKeySource(),
    "",
    "SSH Key for Git access"
)

store.addCredentials(domain, giteaToken)
store.addCredentials(domain, registryCredentials)
store.addCredentials(domain, sshKey)

instance.save()
EOF
    
    jenkins_cli groovy /tmp/credentials-config.groovy
    rm /tmp/credentials-config.groovy
}

# 创建示例Pipeline作业
create_sample_job() {
    log "创建示例Pipeline作业..."
    
    cat > /tmp/sample-pipeline.xml << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>示例CI/CD Pipeline</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH</name>
          <description>构建分支</description>
          <defaultValue>main</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps@2.92">
    <script>
pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'localhost:5001'
        GITEA_URL = 'http://gitea:3000'
    }
    
    stages {
        stage('检出代码') {
            steps {
                echo "检出代码从分支: ${params.BRANCH}"
                // git branch: "${params.BRANCH}", url: "${GITEA_URL}/your-repo.git"
            }
        }
        
        stage('构建测试') {
            steps {
                echo "执行构建和测试..."
                sh 'echo "模拟测试执行"'
            }
        }
        
        stage('构建镜像') {
            steps {
                echo "构建Docker镜像..."
                sh 'echo "模拟镜像构建"'
            }
        }
        
        stage('部署') {
            steps {
                echo "部署应用..."
                sh 'echo "模拟部署"'
            }
        }
    }
    
    post {
        always {
            echo "Pipeline执行完成"
        }
        success {
            echo "✅ 构建成功"
        }
        failure {
            echo "❌ 构建失败"
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF
    
    jenkins_cli create-job "sample-pipeline" < /tmp/sample-pipeline.xml
    rm /tmp/sample-pipeline.xml
}

# 配置Gitea Webhook
configure_gitea_webhook() {
    log "配置Gitea Webhook..."
    
    cat > /tmp/webhook-config.groovy << 'EOF'
import jenkins.model.*
import org.jenkinsci.plugins.gwt.*

def instance = Jenkins.getInstance()

// 配置Generic Webhook Trigger
def descriptor = instance.getDescriptor('org.jenkinsci.plugins.gwt.GenericWebhookTrigger')
if (descriptor) {
    log "Generic Webhook Trigger已配置"
}

instance.save()
EOF
    
    jenkins_cli groovy /tmp/webhook-config.groovy
    rm /tmp/webhook-config.groovy
}

# 主函数
main() {
    log "开始Jenkins自动化配置..."
    
    wait_jenkins
    download_cli
    
    # 跳过初始设置向导
    log "跳过初始设置向导..."
    echo '2.0' > /tmp/jenkins.install.InstallUtil.lastExecVersion
    docker cp /tmp/jenkins.install.InstallUtil.lastExecVersion jenkins:/var/jenkins_home/
    
    # 重启Jenkins
    docker restart jenkins
    wait_jenkins
    download_cli
    
    create_admin_user
    configure_system
    install_plugins
    configure_tools
    configure_credentials
    create_sample_job
    configure_gitea_webhook
    
    log "Jenkins配置完成！"
    log "访问地址: $JENKINS_URL"
    log "管理员账号: $ADMIN_USER"
    log "管理员密码: $ADMIN_PASS"
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 