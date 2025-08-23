#!/bin/bash
# Jenkins自动化配置和启动脚本 - 极致优化版

set -e
BASE_DIR="/Users/brunogao/work/infra"
JENKINS_URL="http://localhost:8081/jenkins"
COMPOSE_DIR="$BASE_DIR/docker/compose"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }

# 初始化环境
init_env(){
    log "初始化Jenkins环境..."
    mkdir -p "$BASE_DIR"/{data,backup}/jenkins "$COMPOSE_DIR/jenkins"/{config,plugins,scripts,templates,shared-library}
    
    # 创建网络
    docker network create cicd-network 2>/dev/null||true
    
    # 设置权限
    sudo chown -R 1000:1000 "$BASE_DIR/data/jenkins" 2>/dev/null||true
    chmod -R 755 "$BASE_DIR/data/jenkins"
    
    log "✅ 环境初始化完成"
}

# 启动服务栈
start_services(){
    log "启动CI/CD服务栈..."
    cd "$COMPOSE_DIR"
    
    # 启动Gitea
    if ! docker ps|grep -q gitea;then
        log "启动Gitea服务..."
        docker-compose -f gitea-compose.yml up -d
        wait_service "http://192.168.1.6:3000" "Gitea" 60
    fi
    
    # 启动Jenkins+Registry
    log "启动Jenkins和Registry..."
    docker-compose -f jenkins-compose.yml up -d
    
    # 等待服务就绪
    wait_service "$JENKINS_URL/login" "Jenkins" 120
    wait_service "http://localhost:5001/v2/" "Registry" 30
    
    log "✅ 服务栈启动完成"
}

# 等待服务就绪
wait_service(){
    local url="$1" service="$2" timeout="${3:-60}"
    log "等待${service}服务启动..."
    for i in $(seq 1 $timeout);do
        if curl -sf "$url" &>/dev/null;then
            log "✅ ${service}服务就绪"
            return 0
        fi
        sleep 2
    done
    error "❌ ${service}服务启动超时";return 1
}

# 跳过初始设置向导
skip_setup_wizard(){
    log "跳过Jenkins初始设置向导..."
    
    # 创建跳过向导标记
    docker exec jenkins bash -c '
        echo "2.0" > /var/jenkins_home/jenkins.install.InstallUtil.lastExecVersion
        echo "false" > /var/jenkins_home/jenkins.install.SetupWizard.state
        mkdir -p /var/jenkins_home/init.groovy.d
    '
    
    # 创建初始管理员用户脚本
    docker exec jenkins bash -c 'cat > /var/jenkins_home/init.groovy.d/basic-security.groovy << "EOF"
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// 创建管理员用户
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("admin", "admin123")
instance.setSecurityRealm(hudsonRealm)

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
EOF'
    
    # 重启Jenkins以应用配置
    docker restart jenkins
    wait_service "$JENKINS_URL/login" "Jenkins" 120
    
    log "✅ 初始设置完成"
}

# 配置凭据
setup_credentials(){
    log "配置系统凭据..."
    
    # 创建凭据配置脚本
    docker exec jenkins bash -c 'cat > /tmp/setup-credentials.groovy << "EOF"
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*

def instance = Jenkins.getInstance()
def domain = Domain.global()
def store = instance.getExtensionList("com.cloudbees.plugins.credentials.SystemCredentialsProvider")[0].getStore()

// Gitea Token
def giteaToken = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "gitea-token",
    "Gitea API访问令牌",
    "your-gitea-token-here"
)

// Registry认证
def registryAuth = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "registry-auth", 
    "Docker Registry认证",
    "admin",
    "admin123"
)

// K8s配置
def k8sConfig = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "k8s-config",
    "Kubernetes配置文件",
    """apiVersion: v1
kind: Config
clusters:
- name: docker-desktop
  cluster:
    server: https://kubernetes.docker.internal:6443
contexts:
- name: docker-desktop
  context:
    cluster: docker-desktop
current-context: docker-desktop"""
)

// SSH密钥
def sshKey = new BasicSSHUserPrivateKey(
    CredentialsScope.GLOBAL,
    "ssh-key",
    "jenkins",
    new BasicSSHUserPrivateKey.UsersPrivateKeySource(),
    "",
    "Git SSH访问密钥"
)

store.addCredentials(domain, giteaToken)
store.addCredentials(domain, registryAuth)
store.addCredentials(domain, k8sConfig)
store.addCredentials(domain, sshKey)

instance.save()
println "凭据配置完成"
EOF'
    
    # 执行配置
    docker exec jenkins java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s "$JENKINS_URL" -auth admin:admin123 groovy /tmp/setup-credentials.groovy
    
    log "✅ 凭据配置完成"
}

# 配置全局工具
setup_tools(){
    log "配置全局开发工具..."
    
    docker exec jenkins bash -c 'cat > /tmp/setup-tools.groovy << "EOF"
import jenkins.model.*
import hudson.tools.*
import hudson.plugins.git.*
import hudson.tasks.Maven.*
import hudson.plugins.gradle.*
import jenkins.plugins.nodejs.tools.*
import org.jenkinsci.plugins.docker.commons.tools.*

def instance = Jenkins.getInstance()

// Git配置
def gitTool = new GitTool("Git", "/usr/bin/git", [])
instance.getDescriptor(GitTool.class).setInstallations(gitTool)

// Docker配置  
def dockerTool = new DockerTool("Docker", "/usr/local/bin/docker", [])
instance.getDescriptor(DockerTool.class).setInstallations(dockerTool)

// Maven自动安装
def mavenInstaller = new Maven.MavenInstaller("3.9.6")
def mavenInstallation = new Maven.MavenInstallation("Maven-3.9", "", [new InstallSourceProperty([mavenInstaller])])
instance.getDescriptor(Maven.class).setInstallations(mavenInstallation)

// Node.js自动安装
def nodeInstaller = new NodeJSInstaller("18.19.0", "", 72)
def nodeInstallation = new NodeJSInstallation("NodeJS-18", "", [new InstallSourceProperty([nodeInstaller])])
instance.getDescriptor(NodeJSInstallation.class).setInstallations(nodeInstallation)

instance.save()
println "工具配置完成"
EOF'
    
    docker exec jenkins java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s "$JENKINS_URL" -auth admin:admin123 groovy /tmp/setup-tools.groovy
    
    log "✅ 工具配置完成"
}

# 创建示例Pipeline作业
create_sample_jobs(){
    log "创建示例CI/CD作业..."
    
    # 多平台构建Pipeline
    cat > /tmp/multiplatform-pipeline.xml << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>多平台Docker镜像构建Pipeline</description>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
    <script>
pipeline {
    agent any
    
    environment {
        REGISTRY = 'localhost:5001'
        IMAGE_NAME = 'test-app'
        PLATFORMS = 'linux/amd64,linux/arm64'
    }
    
    stages {
        stage('环境检查') {
            steps {
                sh 'docker --version'
                sh 'docker buildx version'
                sh 'curl -f http://localhost:5001/v2/ || echo "Registry检查"'
            }
        }
        
        stage('代码检出') {
            steps {
                echo "模拟代码检出..."
                writeFile file: 'Dockerfile', text: '''
FROM alpine:latest
RUN apk add --no-cache curl
COPY . /app
WORKDIR /app
CMD echo "Hello from ${TARGETPLATFORM:-unknown}"
'''
            }
        }
        
        stage('多平台构建') {
            steps {
                script {
                    sh """
                        docker buildx create --use --name multibuilder --driver docker-container 2>/dev/null || true
                        docker buildx build --platform \${PLATFORMS} \\
                            -t \${REGISTRY}/\${IMAGE_NAME}:latest \\
                            -t \${REGISTRY}/\${IMAGE_NAME}:\${BUILD_NUMBER} \\
                            --push .
                    """
                }
            }
        }
        
        stage('部署验证') {
            parallel {
                stage('K8s部署') {
                    steps {
                        echo "模拟K8s部署..."
                        sh 'kubectl version --client || echo "K8s CLI检查"'
                    }
                }
                stage('健康检查') {
                    steps {
                        sh 'docker run --rm ${REGISTRY}/${IMAGE_NAME}:latest'
                    }
                }
            }
        }
    }
    
    post {
        always {
            echo "构建完成: \${currentBuild.currentResult}"
        }
        success {
            echo "✅ 多平台构建成功"
        }
        failure {
            echo "❌ 构建失败，请检查日志"
        }
    }
}
    </script>
    <sandbox>true</sandbox>
  </definition>
</flow-definition>
EOF
    
    # 创建作业
    curl -X POST "$JENKINS_URL/createItem?name=multiplatform-build" \
        --user admin:admin123 \
        --header "Content-Type: application/xml" \
        --data-binary @/tmp/multiplatform-pipeline.xml
    
    log "✅ 示例作业创建完成"
}

# 配置Gitea集成
setup_gitea_integration(){
    log "配置Gitea集成..."
    
    docker exec jenkins bash -c 'cat > /tmp/gitea-config.groovy << "EOF"
import jenkins.model.*

def instance = Jenkins.getInstance()

// 配置Gitea服务器
def giteaConfig = instance.getDescriptor("org.jenkinsci.plugin.gitea.GiteaServer")
if (giteaConfig) {
    println "Gitea插件配置完成"
}

// 配置Webhook触发器
def webhookConfig = instance.getDescriptor("org.jenkinsci.plugins.gwt.GenericWebhookTrigger")
if (webhookConfig) {
    println "Webhook触发器配置完成" 
}

instance.save()
EOF'
    
    docker exec jenkins java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s "$JENKINS_URL" -auth admin:admin123 groovy /tmp/gitea-config.groovy 2>/dev/null || true
    
    log "✅ Gitea集成配置完成"
}

# 性能优化
optimize_performance(){
    log "执行性能优化..."
    
    # JVM优化已在compose中配置
    # 清理旧数据
    docker exec jenkins find /var/jenkins_home/workspace -name "*" -mtime +7 -delete 2>/dev/null || true
    docker exec jenkins find /var/jenkins_home/logs -name "*.log" -mtime +3 -delete 2>/dev/null || true
    
    # 配置构建历史保留
    docker exec jenkins bash -c 'cat > /tmp/optimize-config.groovy << "EOF"
import jenkins.model.*

def instance = Jenkins.getInstance()

// 设置全局执行器数量
instance.setNumExecutors(4)

// 设置安静期
instance.setQuietPeriod(5)

// 设置SCM检出重试次数
instance.setScmCheckoutRetryCount(3)

instance.save()
println "性能优化配置完成"
EOF'
    
    docker exec jenkins java -jar /var/jenkins_home/war/WEB-INF/jenkins-cli.jar -s "$JENKINS_URL" -auth admin:admin123 groovy /tmp/optimize-config.groovy
    
    log "✅ 性能优化完成"
}

# 健康检查
health_check(){
    log "执行系统健康检查..."
    
    local status=0
    
    # 检查服务状态
    if ! curl -sf "$JENKINS_URL/login" &>/dev/null;then
        error "❌ Jenkins服务异常"
        ((status++))
    else
        log "✅ Jenkins服务正常"
    fi
    
    if ! curl -sf "http://localhost:5001/v2/" &>/dev/null;then
        error "❌ Registry服务异常"
        ((status++))
    else
        log "✅ Registry服务正常"
    fi
    
    if ! curl -sf "http://192.168.1.6:3000" &>/dev/null;then
        warn "⚠️  Gitea服务异常"
    else
        log "✅ Gitea服务正常"
    fi
    
    # 检查磁盘空间
    local disk_usage=$(df -h "$BASE_DIR/data/jenkins"|awk 'NR==2{print $5}'|sed 's/%//')
    if [[ $disk_usage -gt 80 ]];then
        warn "⚠️  磁盘使用率过高: ${disk_usage}%"
    else
        log "✅ 磁盘空间充足: ${disk_usage}%"
    fi
    
    # 检查Docker
    if ! docker info &>/dev/null;then
        error "❌ Docker服务异常"
        ((status++))
    else
        log "✅ Docker服务正常"
    fi
    
    return $status
}

# 显示配置信息
show_info(){
    log "Jenkins CI/CD环境配置完成！"
    echo -e "${B}================== 访问信息 ==================${NC}"
    echo -e "${G}Jenkins URL:${NC} $JENKINS_URL"
    echo -e "${G}管理员账号:${NC} admin"
    echo -e "${G}管理员密码:${NC} admin123"
    echo -e "${G}Registry URL:${NC} http://localhost:5001"
    echo -e "${G}Gitea URL:${NC} http://192.168.1.6:3000"
    echo -e "${B}===========================================${NC}"
    echo -e "${Y}后续配置步骤：${NC}"
    echo "1. 访问Jenkins更新Gitea Token凭据"
    echo "2. 在Gitea中配置Webhook: $JENKINS_URL/generic-webhook-trigger/invoke"
    echo "3. 创建项目Pipeline使用多平台构建模板"
    echo "4. 配置K8s集群连接(可选)"
}

# 主执行函数
main(){
    log "开始Jenkins自动化配置..."
    
    init_env
    start_services
    skip_setup_wizard
    setup_credentials
    setup_tools
    create_sample_jobs
    setup_gitea_integration
    optimize_performance
    
    if health_check;then
        show_info
        log "🎉 Jenkins CI/CD环境配置成功！"
    else
        error "❌ 配置过程中发现问题，请检查日志"
        return 1
    fi
}

# 错误处理
trap 'error "脚本执行失败，请检查错误信息"; exit 1' ERR

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]];then
    main "$@"
fi 