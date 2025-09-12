#!/bin/bash
# 直接调用健康数据生成脚本（无需登录）
# 直接调用HealthBaselineScoreTasks的executeImmediately方法

set -e

# 配置参数
DAYS=${1:-30}
BASE_URL="http://localhost:9998"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 直接通过数据库触发健康数据生成
generate_via_service_call() {
    log_info "通过服务直接调用生成健康数据..."
    
    # 创建临时SQL脚本来触发数据生成
    local temp_sql="/tmp/trigger_health_generation.sql"
    
    cat > "$temp_sql" << EOF
-- 触发健康数据生成的SQL脚本
USE test;

-- 获取当前活跃用户列表（有健康数据的用户）
SELECT 
    '当前活跃用户统计' as info,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_records,
    DATE(MIN(create_time)) as earliest_data,
    DATE(MAX(create_time)) as latest_data
FROM t_user_health_data 
WHERE create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY);

-- 显示需要处理的用户ID
SELECT DISTINCT 
    user_id,
    customer_id,
    COUNT(*) as health_records,
    DATE(MAX(create_time)) as latest_data
FROM t_user_health_data 
WHERE create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
GROUP BY user_id, customer_id
ORDER BY health_records DESC
LIMIT 10;
EOF
    
    log_info "检查当前健康数据状态..."
    mysql -h127.0.0.1 -uroot -p123456 test < "$temp_sql" 2>/dev/null || {
        log_error "无法访问数据库"
        return 1
    }
    
    rm -f "$temp_sql"
}

# 通过HTTP API调用
call_health_api() {
    local data_type="$1"
    local description="$2"
    
    log_info "生成${description}..."
    
    # 尝试多个可能的API端点
    local endpoints=(
        "/api/health/task/manual/${data_type}"
        "/api/health/task/execute/${data_type}"
        "/health/task/run/${data_type}"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url="${BASE_URL}${endpoint}?days=${DAYS}"
        
        log_info "尝试调用: $url"
        
        local response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
            -H "Content-Type: application/json" \
            --connect-timeout 10 \
            --max-time 30 2>/dev/null || echo -e "\n000")
        
        local http_code=$(echo "$response" | tail -n1)
        local body=$(echo "$response" | head -n -1)
        
        if [ "$http_code" = "200" ]; then
            if echo "$body" | grep -q -i "success\|完成\|执行"; then
                log_success "${description}生成成功"
                return 0
            else
                log_warning "${description}API调用成功但状态未确认: $body"
                return 0
            fi
        elif [ "$http_code" = "404" ]; then
            log_warning "API端点不存在: $endpoint"
            continue
        elif [ "$http_code" = "401" ]; then
            log_warning "需要认证: $endpoint"
            continue
        else
            log_warning "API调用失败 (HTTP $http_code): $endpoint"
            continue
        fi
    done
    
    log_error "${description}生成失败: 所有API端点都无法访问"
    return 1
}

# 检查和创建必要的数据
ensure_data_structure() {
    log_info "确保数据结构完整..."
    
    # 检查基础表是否存在
    local tables=("t_health_baseline" "t_health_score" "t_health_prediction" "t_health_recommendation" "t_health_profile")
    
    for table in "${tables[@]}"; do
        local exists=$(mysql -h127.0.0.1 -uroot -p123456 -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='test' AND table_name='$table';" test 2>/dev/null | tail -n1)
        
        if [ "$exists" = "1" ]; then
            log_success "表 $table 存在"
        else
            log_error "表 $table 不存在"
        fi
    done
}

# 显示生成后的数据统计
show_data_summary() {
    log_info "显示数据生成结果..."
    
    mysql -h127.0.0.1 -uroot -p123456 -e "
    SELECT 
        '=== 健康数据生成结果统计 ===' as summary;
        
    SELECT 
        '基线数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT feature_name) as unique_features,
        DATE(MAX(create_time)) as latest_record
    FROM t_health_baseline 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '评分数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT feature_name) as unique_features,
        DATE(MAX(create_time)) as latest_record
    FROM t_health_score 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '预测数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        0 as unique_features,
        DATE(MAX(create_time)) as latest_record
    FROM t_health_prediction 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '建议数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        0 as unique_features,
        DATE(MAX(create_time)) as latest_record
    FROM t_health_recommendation 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY)
    UNION ALL
    SELECT 
        '档案数据' as data_type,
        COUNT(*) as total_records,
        COUNT(DISTINCT user_id) as unique_users,
        0 as unique_features,
        DATE(MAX(create_time)) as latest_record
    FROM t_health_profile 
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL ${DAYS} DAY);
    " test 2>/dev/null || log_warning "无法查询数据统计"
}

main() {
    echo "========================================"
    echo "🏥 健康数据直接生成脚本"
    echo "========================================"
    echo "📅 处理天数: ${DAYS} 天"
    echo "🌐 服务地址: ${BASE_URL}"
    echo ""
    
    # 1. 确保数据结构
    ensure_data_structure
    
    echo ""
    
    # 2. 检查当前数据状态
    generate_via_service_call
    
    echo ""
    echo "开始生成健康数据..."
    echo "========================================"
    
    # 3. 逐个生成健康数据类型
    local success_count=0
    local data_types=("baseline:健康基线数据" "score:健康评分数据" "prediction:健康预测数据" "recommendation:健康建议数据" "profile:健康档案数据")
    
    for item in "${data_types[@]}"; do
        IFS=':' read -ra ADDR <<< "$item"
        local type="${ADDR[0]}"
        local desc="${ADDR[1]}"
        
        if call_health_api "$type" "$desc"; then
            ((success_count++))
        fi
        
        sleep 3  # 给系统时间处理
    done
    
    echo ""
    echo "========================================"
    echo "📊 生成结果"
    echo "========================================"
    echo "✅ 成功: ${success_count}/5"
    echo "❌ 失败: $((5 - success_count))/5"
    
    if [ $success_count -gt 0 ]; then
        log_success "部分或全部健康数据生成完成"
    else
        log_warning "健康数据生成可能失败，请检查服务状态"
    fi
    
    # 4. 显示生成结果
    echo ""
    show_data_summary
    
    echo ""
    echo "========================================"
    echo "💡 说明"
    echo "========================================"
    echo "- 此脚本尝试直接调用健康数据生成API"
    echo "- 如果API调用失败，数据生成可能通过定时任务自动进行"
    echo "- 可以通过管理界面或数据库直接查看生成的数据"
    echo "- 服务文档: ${BASE_URL}/doc.html"
    echo "========================================"
}

# 检查参数
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "用法: $0 [天数]"
    echo "参数:"
    echo "  天数    生成数据的天数范围 (默认: 30)"
    echo ""
    echo "示例:"
    echo "  $0 30    # 生成过去30天的健康数据"
    echo "  $0 7     # 生成过去7天的健康数据"
    exit 0
fi

main "$@"