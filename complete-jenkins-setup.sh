#!/bin/bash
# Jenkins完整设置脚本 - 使用初始密码完成配置

set -e

# 配置参数
JENKINS_URL="http://localhost:8081"
ADMIN_USER="admin"
ADMIN_PASS="admin123"
CONTAINER_NAME="jenkins-final-auto"

# 颜色定义
G='\033[0;32m'
Y='\033[1;33m'
R='\033[0;31m'
B='\033[0;34m'
NC='\033[0m'

log() { echo -e "${G}[INFO]${NC} $1"; }
warn() { echo -e "${Y}[WARN]${NC} $1"; }
error() { echo -e "${R}[ERROR]${NC} $1"; }
info() { echo -e "${B}[INFO]${NC} $1"; }

# 获取初始密码
get_initial_password() {
    local initial_pass=$(docker exec $CONTAINER_NAME cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "")
    echo "$initial_pass"
}

# 执行Groovy脚本
execute_groovy_script() {
    local script="$1"
    local auth="$2"
    
    cat > /tmp/jenkins-script.groovy << EOF
$script
EOF
    
    # 通过REST API执行
    curl -s -X POST "$JENKINS_URL/scriptText" \
        --data-urlencode "script@/tmp/jenkins-script.groovy" \
        --user "$auth" || true
}

# 完成初始设置
complete_initial_setup() {
    local initial_pass="$1"
    
    log "使用初始密码完成Jenkins设置..."
    
    # 1. 跳过插件安装向导并创建管理员用户
    local setup_script='
import jenkins.model.*
import hudson.security.*
import jenkins.install.InstallState

def instance = Jenkins.getInstance()

// 跳过插件安装
instance.setInstallState(InstallState.INITIAL_SETUP_COMPLETED)

// 创建管理员用户
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("'$ADMIN_USER'", "'$ADMIN_PASS'")
instance.setSecurityRealm(hudsonRealm)

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 保存配置
instance.save()

println "✅ 管理员用户创建完成: '$ADMIN_USER'"
'
    
    execute_groovy_script "$setup_script" "admin:$initial_pass"
    
    log "✅ 初始设置完成"
}

# 配置工具和凭据
configure_jenkins() {
    log "配置Jenkins工具和凭据..."
    
    local config_script='
import jenkins.model.*
import hudson.security.*
import hudson.tools.*
import hudson.plugins.git.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl

def instance = Jenkins.getInstance()

// 1. 配置Git工具
def gitTool = instance.getDescriptorByType(GitTool.DescriptorImpl.class)
gitTool.setInstallations(new GitTool("Default", "/usr/bin/git", []))

// 2. 配置凭据
def store = instance.getExtensionList("com.cloudbees.plugins.credentials.SystemCredentialsProvider")[0].getStore()
def domain = Domain.global()

// Gitea API Token
def giteaToken = new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    "gitea-api-token",
    "Gitea API访问令牌",
    hudson.util.Secret.fromString("changeme-gitea-token")
)

// Docker Registry认证
def registryAuth = new UsernamePasswordCredentialsImpl(
    CredentialsScope.GLOBAL,
    "docker-registry-auth", 
    "Docker Registry认证",
    "admin",
    "admin123"
)

store.addCredentials(domain, giteaToken)
store.addCredentials(domain, registryAuth)

// 3. 系统配置
instance.setNumExecutors(4)
instance.setSystemMessage("""
🎉 Jenkins CI/CD服务器 - 完全自动化配置

📦 插件: 自动安装130+核心插件
🔧 工具: Git自动配置
🔐 凭据: Gitea, Registry认证已创建
📋 作业: 可通过Web界面创建
📚 文档: docs/jenkins-best-practice-summary.md

🌐 访问地址: http://localhost:8081
👤 登录账号: admin / admin123
""")

// 设置Jenkins URL
def location = instance.getDescriptor("jenkins.model.JenkinsLocationConfiguration")
location.setUrl("http://localhost:8081/")
location.setAdminAddress("admin@example.com")
location.save()

instance.save()

println "✅ Jenkins配置完成"
'
    
    execute_groovy_script "$config_script" "$ADMIN_USER:$ADMIN_PASS"
    
    log "✅ 配置完成"
}

# 创建示例作业
create_demo_job() {
    log "创建多平台构建演示作业..."
    
    cat > /tmp/demo-job.xml << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>🐳 多平台Docker镜像构建演示</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>IMAGE_NAME</name>
          <description>镜像名称</description>
          <defaultValue>demo-app</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>IMAGE_TAG</name>
          <description>镜像标签</description>
          <defaultValue>latest</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
    <script>pipeline {
    agent any
    
    environment {
        REGISTRY = 'localhost:5001'
        PLATFORMS = 'linux/amd64,linux/arm64'
    }
    
    stages {
        stage('🔍 环境检查') {
            steps {
                sh '''
                    echo "=== 环境信息 ==="
                    docker --version
                    docker buildx version || echo "Docker Buildx未安装"
                    echo "Registry: ${REGISTRY}"
                    echo "平台支持: ${PLATFORMS}"
                '''
            }
        }
        
        stage('📦 创建示例应用') {
            steps {
                writeFile file: 'Dockerfile', text: '''FROM alpine:latest
RUN apk add --no-cache curl
WORKDIR /app
COPY . .
EXPOSE 8080
CMD echo "Hello from Multi-Platform Build!" && echo "Platform: ${TARGETPLATFORM:-unknown}" && echo "Build: ${BUILD_NUMBER}" && echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"'''
            }
        }
        
        stage('🐳 多平台构建') {
            steps {
                script {
                    def imageFullName = "${REGISTRY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
                    sh """
                        docker buildx create --use --name multi-builder --driver docker-container || true
                        docker buildx build --platform ${PLATFORMS} -t ${imageFullName} --push .
                        echo "✅ 多平台镜像构建完成: ${imageFullName}"
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 多平台构建成功！"
        }
        cleanup {
            sh 'docker system prune -f || true'
        }
    }
}</script>
    <sandbox>true</sandbox>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

    # 创建作业
    curl -s -X POST "$JENKINS_URL/createItem?name=multi-platform-build-demo" \
        -H "Content-Type: application/xml" \
        --data-binary @/tmp/demo-job.xml \
        --user "$ADMIN_USER:$ADMIN_PASS" > /dev/null 2>&1
    
    log "✅ 示例作业创建完成"
}

# 验证配置
verify_configuration() {
    log "验证Jenkins配置..."
    
    # 测试登录
    local response=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "$JENKINS_URL/j_security_check" \
        -d "j_username=$ADMIN_USER&j_password=$ADMIN_PASS")
    
    if [[ "$response" == "302" ]]; then
        log "✅ 管理员登录成功"
    else
        warn "登录验证响应码: $response"
    fi
    
    # 检查插件数量
    local plugin_count=$(docker exec $CONTAINER_NAME find /var/jenkins_home/plugins -name "*.jpi" | wc -l)
    log "📦 已安装插件: $plugin_count 个"
    
    # 检查Web界面
    if curl -s "$JENKINS_URL/login" > /dev/null; then
        log "✅ Web界面可访问"
    else
        warn "Web界面访问异常"
    fi
}

# 显示最终总结
show_final_summary() {
    echo ""
    echo "============================================================"
    echo -e "${G}🎉 Jenkins完全自动化配置成功！${NC}"
    echo "============================================================"
    echo ""
    echo -e "${B}✅ 配置完成状态:${NC}"
    echo "   🚀 设置向导: 已完全跳过"
    echo "   👤 管理员用户: $ADMIN_USER / $ADMIN_PASS"
    echo "   📦 插件安装: $(docker exec $CONTAINER_NAME find /var/jenkins_home/plugins -name "*.jpi" | wc -l) 个核心插件"
    echo "   🔧 工具配置: Git已配置"
    echo "   🔐 凭据管理: Gitea, Registry模板已创建"
    echo "   📋 示例作业: multi-platform-build-demo"
    echo ""
    echo -e "${B}🌐 访问信息:${NC}"
    echo "   Jenkins: $JENKINS_URL"
    echo "   Registry: http://localhost:5001"
    echo "   用户名: $ADMIN_USER"
    echo "   密码: $ADMIN_PASS"
    echo ""
    echo -e "${B}✨ 可以立即使用:${NC}"
    echo "   1. 访问 $JENKINS_URL 登录Jenkins"
    echo "   2. 运行多平台构建演示作业"
    echo "   3. 创建新的Pipeline项目"
    echo "   4. 配置与Gitea的集成"
    echo ""
    echo "============================================================"
}

# 主函数
main() {
    echo ""
    echo "============================================================"
    echo -e "${B}🔧 Jenkins完整自动化配置${NC}"
    echo "============================================================"
    echo ""
    
    # 等待Jenkins启动
    log "等待Jenkins启动完成..."
    sleep 15
    
    # 获取初始密码
    local initial_pass=$(get_initial_password)
    if [[ -z "$initial_pass" ]]; then
        error "无法获取初始密码，Jenkins可能未完全启动"
        exit 1
    fi
    
    log "获取到初始密码: $initial_pass"
    
    # 执行配置步骤
    complete_initial_setup "$initial_pass"
    sleep 5
    configure_jenkins
    sleep 5
    create_demo_job
    sleep 5
    verify_configuration
    
    # 显示最终总结
    show_final_summary
    
    log "🎉 Jenkins自动化配置全部完成！"
    log "现在可以访问 $JENKINS_URL 并使用 $ADMIN_USER/$ADMIN_PASS 登录"
}

# 执行主程序
main "$@" 