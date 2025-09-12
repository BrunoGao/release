#!/bin/bash
# 健康数据生成脚本
# 先登录获取token，然后生成过去一个月的baseline, score, prediction, recommendation, profile

set -e

# 配置参数
BASE_URL="http://localhost:9998"
USERNAME="admin"
PASSWORD="admin123"
DAYS=30

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务是否可用
check_service() {
    log_info "检查ljwx-boot服务状态..."
    
    if curl -s "${BASE_URL}/actuator/health" > /dev/null; then
        log_success "服务正常运行"
    else
        log_error "服务不可访问，请确保ljwx-boot已启动"
        exit 1
    fi
}

# 登录获取token
login() {
    log_info "开始登录获取token..."
    
    local login_data=$(cat <<EOF
{
    "username": "${USERNAME}",
    "password": "${PASSWORD}"
}
EOF
)
    
    local response=$(curl -s -X POST \
        "${BASE_URL}/auth/login" \
        -H "Content-Type: application/json" \
        -d "$login_data")
    
    # 提取token (根据实际API响应格式调整)
    local token=$(echo "$response" | jq -r '.data.token // .token // .access_token // empty')
    
    if [ -z "$token" ] || [ "$token" = "null" ]; then
        log_warning "使用标准登录方式失败，尝试其他登录接口..."
        
        # 尝试其他可能的登录接口
        response=$(curl -s -X POST \
            "${BASE_URL}/api/auth/login" \
            -H "Content-Type: application/json" \
            -d "$login_data")
        
        token=$(echo "$response" | jq -r '.data.token // .token // .access_token // empty')
        
        if [ -z "$token" ] || [ "$token" = "null" ]; then
            # 尝试直接访问健康任务接口（可能不需要登录）
            log_warning "无法获取token，尝试直接访问API..."
            TOKEN=""
            return 0
        fi
    fi
    
    TOKEN="$token"
    log_success "登录成功，token已获取"
    return 0
}

# 执行API请求
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    local headers="-H 'Content-Type: application/json'"
    if [ -n "$TOKEN" ]; then
        headers="$headers -H 'Authorization: Bearer $TOKEN'"
    fi
    
    local url="${BASE_URL}${endpoint}"
    
    if [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            eval curl -s -X POST "$url" $headers -d "'$data'"
        else
            eval curl -s -X POST "$url" $headers
        fi
    else
        eval curl -s -X GET "$url" $headers
    fi
}

# 生成健康数据
generate_health_data() {
    local data_type="$1"
    local description="$2"
    
    log_info "开始生成${description}..."
    
    local endpoint="/api/health/task/execute/${data_type}?days=${DAYS}"
    local response=$(api_request "POST" "$endpoint")
    
    # 检查响应
    local code=$(echo "$response" | jq -r '.code // .status // 200')
    local message=$(echo "$response" | jq -r '.message // .msg // "success"')
    
    if [ "$code" = "200" ] || [ "$code" = "0" ] || echo "$response" | grep -q "success\|完成\|执行"; then
        log_success "${description}生成完成"
        return 0
    else
        log_error "${description}生成失败: $message"
        echo "Response: $response"
        return 1
    fi
}

# 检查任务状态
check_task_status() {
    log_info "检查任务执行状态..."
    
    local response=$(api_request "GET" "/api/health/task/status")
    echo "任务状态: $response"
}

# 验证生成的数据
verify_data() {
    log_info "验证生成的数据..."
    
    # 检查数据库中的记录数量
    mysql -h127.0.0.1 -uroot -p123456 -e "
    SELECT 
        '基线数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as users,
        DATE(MAX(create_time)) as latest_date
    FROM t_health_baseline 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '评分数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as users,
        DATE(MAX(create_time)) as latest_date
    FROM t_health_score 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '预测数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as users,
        DATE(MAX(create_time)) as latest_date
    FROM t_health_prediction 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '建议数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as users,
        DATE(MAX(create_time)) as latest_date
    FROM t_health_recommendation 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '档案数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as users,
        DATE(MAX(create_time)) as latest_date
    FROM t_health_profile 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY);
    " test 2>/dev/null || log_warning "无法验证数据库数据"
}

# 主函数
main() {
    echo "========================================"
    echo "🏥 健康数据生成脚本"
    echo "========================================"
    echo "📅 生成时间范围: 过去 ${DAYS} 天"
    echo "🌐 服务地址: ${BASE_URL}"
    echo "👤 用户名: ${USERNAME}"
    echo ""
    
    # 1. 检查服务状态
    check_service
    
    # 2. 登录获取token
    login
    
    echo ""
    echo "开始生成健康数据..."
    echo "========================================"
    
    # 3. 按顺序生成各类健康数据
    local success_count=0
    local total_count=5
    
    # 3.1 生成基线数据
    if generate_health_data "baseline" "健康基线数据"; then
        ((success_count++))
    fi
    sleep 2
    
    # 3.2 生成评分数据
    if generate_health_data "score" "健康评分数据"; then
        ((success_count++))
    fi
    sleep 2
    
    # 3.3 生成预测数据  
    if generate_health_data "prediction" "健康预测数据"; then
        ((success_count++))
    fi
    sleep 2
    
    # 3.4 生成建议数据
    if generate_health_data "recommendation" "健康建议数据"; then
        ((success_count++))
    fi
    sleep 2
    
    # 3.5 生成档案数据
    if generate_health_data "profile" "健康档案数据"; then
        ((success_count++))
    fi
    
    echo ""
    echo "========================================"
    echo "📊 生成结果统计"
    echo "========================================"
    echo "✅ 成功: ${success_count}/${total_count}"
    echo "❌ 失败: $((total_count - success_count))/${total_count}"
    
    if [ $success_count -eq $total_count ]; then
        log_success "所有健康数据生成完成！"
    else
        log_warning "部分健康数据生成失败，请检查日志"
    fi
    
    # 4. 验证生成的数据
    echo ""
    verify_data
    
    # 5. 输出访问信息
    echo ""
    echo "========================================"
    echo "🔗 访问地址"
    echo "========================================"
    echo "📖 API文档: ${BASE_URL}/doc.html"
    echo "📊 健康监控: ${BASE_URL}/actuator/health"
    echo "🎯 任务管理: ${BASE_URL}/api/health/task/"
    echo ""
    echo "💡 提示："
    echo "  - 可以通过管理界面查看生成的数据"
    echo "  - 数据生成可能需要一些时间处理"
    echo "  - 如有失败，可以重新运行此脚本"
    echo "========================================"
}

# 运行主函数
main "$@"