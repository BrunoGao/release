#!/bin/bash

# Jenkins 终极自动化配置测试脚本
# 验证所有自动化功能是否正常工作

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_LOG="${SCRIPT_DIR}/logs/jenkins-ultimate-test.log"

# 创建测试日志目录
mkdir -p "$(dirname "${TEST_LOG}")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试结果统计
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# 日志函数
log() { echo -e "${GREEN}[TEST]${NC} $1" | tee -a "${TEST_LOG}"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "${TEST_LOG}"; }
error() { echo -e "${RED}[FAIL]${NC} $1" | tee -a "${TEST_LOG}"; }
success() { echo -e "${GREEN}[PASS]${NC} $1" | tee -a "${TEST_LOG}"; }

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "🧪 测试: $test_name ... "
    
    if eval "$test_command" &>/dev/null; then
        success "✅ PASS"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        error "❌ FAIL"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    local service_name="$1"
    local service_url="$2"
    local max_attempts=30
    local attempt=0
    
    log "等待 $service_name 服务启动..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf "$service_url" &>/dev/null; then
            success "$service_name 服务已启动"
            return 0
        fi
        
        sleep 2
        ((attempt++))
        echo -n "."
    done
    
    error "$service_name 服务启动超时"
    return 1
}

# 显示测试横幅
show_test_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║              🧪 Jenkins 终极自动化配置测试                      ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# 基础服务测试
test_basic_services() {
    log "开始基础服务测试..."
    
    run_test "Jenkins 服务响应" "curl -sf http://localhost:8081/login"
    run_test "Docker Registry 服务" "curl -sf http://localhost:5001/v2/"
    run_test "Registry UI 服务" "curl -sf http://localhost:5002"
    
    # Jenkins 健康检查
    run_test "Jenkins 健康检查" "curl -sf http://localhost:8081/manage/systemInfo"
}

# 认证测试
test_authentication() {
    log "开始认证测试..."
    
    # 测试管理员登录
    local login_response=$(curl -s -c /tmp/jenkins_cookies.txt -d "j_username=admin&j_password=admin123" \
        -X POST "http://localhost:8081/j_spring_security_check" -w "%{http_code}")
    
    if [[ "$login_response" == *"302"* ]] || [[ "$login_response" == *"200"* ]]; then
        success "✅ 管理员登录测试通过"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        error "❌ 管理员登录测试失败"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    # 测试 API 访问
    run_test "Jenkins API 访问" "curl -sf -b /tmp/jenkins_cookies.txt http://localhost:8081/api/json"
    
    # 清理 cookies
    rm -f /tmp/jenkins_cookies.txt
}

# Configuration as Code 测试
test_casc_config() {
    log "开始 CasC 配置测试..."
    
    # 检查 CasC 端点
    run_test "CasC 配置端点" "curl -sf http://localhost:8081/manage/configuration-as-code/"
    
    # 检查配置是否加载
    local casc_logs=$(docker logs jenkins-ultimate 2>&1 | grep -i "configuration as code" | wc -l)
    if [[ $casc_logs -gt 0 ]]; then
        success "✅ CasC 配置日志检查通过"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        error "❌ CasC 配置日志检查失败"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# 插件测试
test_plugins() {
    log "开始插件测试..."
    
    # 检查关键插件是否安装
    local plugins=(
        "git"
        "workflow-aggregator"
        "docker-plugin"
        "kubernetes"
        "configuration-as-code"
        "blueocean"
        "pipeline-stage-view"
    )
    
    for plugin in "${plugins[@]}"; do
        run_test "插件 $plugin" "curl -sf http://localhost:8081/pluginManager/api/json | grep -q '\"shortName\":\"$plugin\"'"
    done
}

# 工具配置测试
test_tools_config() {
    log "开始工具配置测试..."
    
    # 检查 Docker 集成
    run_test "Jenkins Docker 集成" "docker exec jenkins-ultimate docker --version"
    
    # 检查 Docker Buildx
    run_test "Jenkins Docker Buildx" "docker exec jenkins-ultimate docker buildx version"
    
    # 检查 Git
    run_test "Jenkins Git 工具" "docker exec jenkins-ultimate git --version"
    
    # 检查 Java
    run_test "Jenkins Java 环境" "docker exec jenkins-ultimate java --version"
}

# 共享库测试
test_shared_library() {
    log "开始共享库测试..."
    
    # 检查共享库文件是否存在
    run_test "多平台构建函数" "test -f ${SCRIPT_DIR}/docker/compose/jenkins/shared-library/vars/buildMultiPlatformImage.groovy"
    run_test "通知函数" "test -f ${SCRIPT_DIR}/docker/compose/jenkins/shared-library/vars/sendNotification.groovy"
    
    # 检查共享库挂载
    run_test "共享库挂载" "docker exec jenkins-ultimate test -d /var/jenkins_home/shared-library"
}

# 模板测试
test_pipeline_templates() {
    log "开始流水线模板测试..."
    
    run_test "Java 应用模板" "test -f ${SCRIPT_DIR}/docker/compose/jenkins/templates/Jenkinsfile-java-app"
    run_test "Node.js 应用模板" "test -f ${SCRIPT_DIR}/docker/compose/jenkins/templates/Jenkinsfile-nodejs-app"
}

# Docker Registry 测试
test_docker_registry() {
    log "开始 Docker Registry 测试..."
    
    run_test "Registry Catalog API" "curl -sf http://localhost:5001/v2/_catalog"
    run_test "Registry 健康检查" "curl -sf http://localhost:5001/v2/"
    
    # 测试简单镜像推送（使用 hello-world）
    local test_image="localhost:5001/test/hello-world:test"
    
    if docker pull hello-world:latest &>/dev/null && \
       docker tag hello-world:latest "$test_image" &>/dev/null && \
       docker push "$test_image" &>/dev/null; then
        success "✅ Registry 推送测试通过"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        # 清理测试镜像
        docker rmi "$test_image" hello-world:latest &>/dev/null || true
    else
        error "❌ Registry 推送测试失败"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# 性能测试
test_performance() {
    log "开始性能测试..."
    
    # 检查内存使用
    local memory_usage=$(docker exec jenkins-ultimate free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    if (( $(echo "$memory_usage < 80" | bc -l) )); then
        success "✅ 内存使用率正常 (${memory_usage}%)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warn "⚠️ 内存使用率较高 (${memory_usage}%)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    # 检查磁盘使用
    local disk_usage=$(docker exec jenkins-ultimate df -h /var/jenkins_home | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 85 ]]; then
        success "✅ 磁盘使用率正常 (${disk_usage}%)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warn "⚠️ 磁盘使用率较高 (${disk_usage}%)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# 管理脚本测试
test_management_script() {
    log "开始管理脚本测试..."
    
    run_test "管理脚本存在" "test -x ${SCRIPT_DIR}/jenkins-ultimate-manager.sh"
    run_test "管理脚本状态功能" "${SCRIPT_DIR}/jenkins-ultimate-manager.sh status"
    run_test "管理脚本健康检查" "${SCRIPT_DIR}/jenkins-ultimate-manager.sh health"
}

# 安全性测试
test_security() {
    log "开始安全性测试..."
    
    # 检查 CSRF 保护
    run_test "CSRF 保护" "curl -sf http://localhost:8081/crumbIssuer/api/json"
    
    # 检查匿名访问限制
    local anonymous_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/manage/systemInfo)
    if [[ "$anonymous_response" == "403" ]] || [[ "$anonymous_response" == "302" ]]; then
        success "✅ 匿名访问正确限制"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warn "⚠️ 匿名访问配置可能有问题"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

# 显示测试报告
show_test_report() {
    echo ""
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                      📊 测试结果报告                          ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${GREEN}📈 测试统计：${NC}"
    echo "  总测试数: $TESTS_TOTAL"
    echo "  通过: $TESTS_PASSED"
    echo "  失败: $TESTS_FAILED"
    echo "  成功率: $(( TESTS_PASSED * 100 / TESTS_TOTAL ))%"
    
    echo ""
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 所有测试通过！Jenkins 自动化配置完全正常！${NC}"
        echo ""
        echo -e "${GREEN}✅ 你的 Jenkins 环境已完全自动化配置并验证正常：${NC}"
        echo "  • 服务运行正常"
        echo "  • 认证配置正确"
        echo "  • 插件安装完整"
        echo "  • 工具集成成功"
        echo "  • 共享库可用"
        echo "  • 安全配置正确"
        echo "  • 性能状态良好"
    else
        echo -e "${YELLOW}⚠️ 部分测试失败，请检查相关配置${NC}"
        echo ""
        echo -e "${YELLOW}建议操作：${NC}"
        echo "  1. 检查失败的测试项目"
        echo "  2. 查看详细日志: ${TEST_LOG}"
        echo "  3. 重新运行自动化配置脚本"
        echo "  4. 检查 Docker 和网络配置"
    fi
    
    echo ""
    echo -e "${BLUE}📋 详细测试日志: ${TEST_LOG}${NC}"
}

# 主函数
main() {
    show_test_banner
    
    log "开始 Jenkins 终极自动化配置验证测试..."
    
    # 等待服务启动
    wait_for_service "Jenkins" "http://localhost:8081/login" || exit 1
    wait_for_service "Registry" "http://localhost:5001/v2/" || exit 1
    
    # 运行所有测试
    test_basic_services
    test_authentication
    test_casc_config
    test_plugins
    test_tools_config
    test_shared_library
    test_pipeline_templates
    test_docker_registry
    test_performance
    test_management_script
    test_security
    
    # 显示测试报告
    show_test_report
    
    # 退出码
    if [[ $TESTS_FAILED -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
}

# 错误处理
trap 'error "测试过程中发生错误"; exit 1' ERR

# 执行主函数
main "$@"