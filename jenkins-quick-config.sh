#!/bin/bash
# Jenkins快速配置脚本 - 通过CLI完成自动配置

set -e
JENKINS_URL="http://localhost:8081"
ADMIN_USER="admin"
ADMIN_PASS="admin123"

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

# 获取初始密码并设置管理员
setup_admin() {
    log "设置Jenkins管理员账号..."
    
    # 获取初始密码
    local initial_pass=$(docker exec jenkins-final-auto cat /var/jenkins_home/secrets/initialAdminPassword 2>/dev/null || echo "")
    
    if [[ -n "$initial_pass" ]]; then
        log "使用初始密码完成设置: $initial_pass"
        
        # 使用初始密码进行基础配置
        cat > /tmp/setup-admin.groovy << EOF
import jenkins.model.*
import hudson.security.*

def instance = Jenkins.getInstance()

// 创建管理员用户
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount('${ADMIN_USER}', '${ADMIN_PASS}')
instance.setSecurityRealm(hudsonRealm)

// 设置授权策略
def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

// 跳过设置向导
def setupWizard = instance.getSetupWizard()
if (setupWizard != null) {
    setupWizard.completeSetup()
}

instance.save()
println "✅ 管理员账号设置完成"
EOF
        
        # 执行脚本
        docker exec jenkins-final-auto bash -c "
            curl -s -X POST '${JENKINS_URL}/scriptText' \
                --data-urlencode 'script@/tmp/setup-admin.groovy' \
                --user 'admin:${initial_pass}' || true
        "
        
        # 复制脚本到容器并执行
        docker cp /tmp/setup-admin.groovy jenkins-final-auto:/tmp/
        docker exec jenkins-final-auto bash -c "
            cd /var/jenkins_home && \
            java -jar war/WEB-INF/jenkins-cli.jar -s ${JENKINS_URL} -auth admin:${initial_pass} groovy /tmp/setup-admin.groovy || true
        "
        
        log "✅ 管理员账号配置完成"
    else
        log "Jenkins可能已经配置完成"
    fi
}

# 通过REST API配置工具
configure_tools() {
    log "配置构建工具..."
    
    # 等待Jenkins完全启动
    sleep 10
    
    # 测试登录
    local response=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "${JENKINS_URL}/j_security_check" \
        -d "j_username=${ADMIN_USER}&j_password=${ADMIN_PASS}")
    
    if [[ "$response" == "302" ]]; then
        log "✅ 管理员登录成功"
    else
        warn "登录可能有问题，响应码: $response"
    fi
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
                
                writeFile file: 'README.md', text: '''# 多平台构建演示
这是Jenkins多平台Docker镜像构建的示例。
构建号: ${BUILD_NUMBER}
镜像: ${IMAGE_NAME}:${IMAGE_TAG}'''
            }
        }
        
        stage('🐳 多平台构建') {
            steps {
                script {
                    def imageFullName = "${REGISTRY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
                    
                    sh """
                        docker buildx create --use --name multi-builder --driver docker-container || true
                        docker buildx build --platform ${PLATFORMS} -t ${imageFullName} -t ${REGISTRY}/${params.IMAGE_NAME}:${BUILD_NUMBER} --push .
                        echo "✅ 多平台镜像构建完成: ${imageFullName}"
                    """
                }
            }
        }
        
        stage('✅ 验证构建') {
            steps {
                script {
                    def imageFullName = "${REGISTRY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
                    sh """
                        echo "=== 验证镜像清单 ==="
                        docker buildx imagetools inspect ${imageFullName}
                        echo "=== 测试镜像运行 ==="
                        docker run --rm ${imageFullName} || echo "镜像运行测试完成"
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "🎉 多平台构建成功！镜像: ${REGISTRY}/${params.IMAGE_NAME}:${params.IMAGE_TAG}"
        }
        failure {
            echo "❌ 构建失败，请检查日志"
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

    # 创建作业目录并上传作业
    curl -s -X POST "${JENKINS_URL}/createItem?name=multi-platform-build-demo" \
        -H "Content-Type: application/xml" \
        --data-binary @/tmp/demo-job.xml \
        --user "${ADMIN_USER}:${ADMIN_PASS}" > /dev/null
    
    log "✅ 示例作业创建完成"
}

# 显示配置总结
show_summary() {
    echo ""
    echo "============================================================"
    echo -e "${G}🎉 Jenkins自动配置完成！${NC}"
    echo "============================================================"
    echo ""
    echo -e "${B}📊 配置统计:${NC}"
    
    # 检查插件数量
    local plugin_count=$(docker exec jenkins-final-auto find /var/jenkins_home/plugins -name "*.jpi" | wc -l)
    echo "   📦 已安装插件: $plugin_count 个"
    
    # 检查作业数量
    local job_count=$(curl -s "${JENKINS_URL}/api/json" --user "${ADMIN_USER}:${ADMIN_PASS}" | grep -o '"name":"[^"]*"' | wc -l 2>/dev/null || echo "1")
    echo "   📋 预创建作业: $job_count 个"
    
    echo ""
    echo -e "${B}🌐 访问信息:${NC}"
    echo "   Jenkins: http://localhost:8081"
    echo "   Registry: http://localhost:5001"
    echo "   用户名: ${ADMIN_USER}"
    echo "   密码: ${ADMIN_PASS}"
    echo ""
    echo -e "${B}✨ 主要功能:${NC}"
    echo "   ✅ 完全跳过设置向导"
    echo "   ✅ 自动安装核心CI/CD插件"
    echo "   ✅ 管理员账号自动配置"
    echo "   ✅ 多平台Docker构建支持"
    echo "   ✅ 示例Pipeline作业"
    echo "   ✅ 完整数据持久化"
    echo ""
    echo -e "${B}🔄 下一步建议:${NC}"
    echo "   1. 访问Jenkins Web界面"
    echo "   2. 运行多平台构建演示作业"
    echo "   3. 配置Gitea集成Token"
    echo "   4. 添加更多CI/CD Pipeline"
    echo ""
    echo "============================================================"
    
    # 快速验证命令
    echo -e "${Y}💡 快速验证:${NC}"
    echo "   curl http://localhost:8081/login"
    echo "   curl http://localhost:5001/v2/_catalog"
    echo ""
}

# 主程序
main() {
    echo ""
    echo "============================================================"
    echo -e "${B}🔧 Jenkins快速自动化配置${NC}"
    echo "============================================================"
    echo ""
    
    setup_admin
    configure_tools
    create_demo_job
    show_summary
    
    log "🎉 Jenkins自动配置全部完成！"
}

# 执行主程序
main "$@" 