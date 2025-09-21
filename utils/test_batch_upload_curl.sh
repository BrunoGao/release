#!/bin/bash

# ljwx-boot 批量上传接口 cURL 测试脚本
# 测试三个核心接口：upload_health_data, upload_device_info, upload_common_event

# 默认配置
BASE_URL="http://localhost:8080"
CONTENT_TYPE="Content-Type: application/json"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 工具函数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 测试健康数据上传接口
test_upload_health_data() {
    log_info "测试健康数据上传接口"
    
    # 生成测试数据
    local health_data='[
        {
            "device_id": "DEVICE_001",
            "user_id": "101",
            "org_id": "1",
            "customer_id": "8",
            "heart_rate": 75,
            "blood_oxygen": 98,
            "temperature": 36.5,
            "pressure_high": 120,
            "pressure_low": 80,
            "stress": 5,
            "step": 8500,
            "distance": 6.2,
            "calorie": 420.5,
            "latitude": 39.908823,
            "longitude": 116.397470,
            "altitude": 45.2,
            "create_time": "'$(date '+%Y-%m-%d %H:%M:%S')'"
        },
        {
            "device_id": "DEVICE_002",
            "user_id": "102",
            "org_id": "1",
            "customer_id": "8",
            "heart_rate": 82,
            "blood_oxygen": 97,
            "temperature": 36.8,
            "pressure_high": 125,
            "pressure_low": 82,
            "stress": 3,
            "step": 12000,
            "distance": 8.5,
            "calorie": 680.0,
            "create_time": "'$(date '+%Y-%m-%d %H:%M:%S')'"
        }
    ]'
    
    echo "📊 测试新格式接口: /batch/upload-health-data"
    local response1=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$health_data" \
        "$BASE_URL/batch/upload-health-data")
    
    local body1=$(echo $response1 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status1=$(echo $response1 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status1" -eq 200 ]; then
        log_success "新格式接口测试通过 (HTTP $status1)"
        echo "   响应: $(echo $body1 | jq -r '.message // .result.message // "处理成功"')"
        echo "   处理数据: $(echo $body1 | jq -r '.result.processed // "N/A"') 条"
    else
        log_error "新格式接口测试失败 (HTTP $status1)"
        echo "   错误: $body1"
    fi
    
    echo
    echo "📊 测试Python兼容接口: /batch/upload_health_data"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$health_data" \
        "$BASE_URL/batch/upload_health_data")
    
    local body2=$(echo $response2 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status2=$(echo $response2 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status2" -eq 200 ]; then
        log_success "Python兼容接口测试通过 (HTTP $status2)"
        echo "   响应: $(echo $body2 | jq -r '.message // .result.message // "处理成功"')"
    else
        log_error "Python兼容接口测试失败 (HTTP $status2)"
        echo "   错误: $body2"
    fi
}

# 测试设备信息上传接口
test_upload_device_info() {
    log_info "测试设备信息上传接口"
    
    # 生成测试数据
    local device_data='[
        {
            "device_id": "DEVICE_001",
            "device_name": "智能手环_001",
            "device_type": "wearable",
            "firmware_version": "v2.3.1",
            "battery_level": 85,
            "signal_strength": -45,
            "customer_id": "8",
            "status": "online",
            "last_sync": "'$(date '+%Y-%m-%d %H:%M:%S')'"
        },
        {
            "device_id": "DEVICE_002",
            "device_name": "智能手环_002",
            "device_type": "wearable",
            "firmware_version": "v2.3.2",
            "battery_level": 92,
            "signal_strength": -38,
            "customer_id": "8",
            "status": "charging",
            "last_sync": "'$(date '+%Y-%m-%d %H:%M:%S')'"
        }
    ]'
    
    echo "📱 测试新格式接口: /batch/upload-device-info"
    local response1=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$device_data" \
        "$BASE_URL/batch/upload-device-info")
    
    local body1=$(echo $response1 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status1=$(echo $response1 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status1" -eq 200 ]; then
        log_success "新格式接口测试通过 (HTTP $status1)"
        echo "   处理设备: $(echo $body1 | jq -r '.result.processed // "N/A"') 个"
    else
        log_error "新格式接口测试失败 (HTTP $status1)"
        echo "   错误: $body1"
    fi
    
    echo
    echo "📱 测试Python兼容接口: /batch/upload_device_info"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$device_data" \
        "$BASE_URL/batch/upload_device_info")
    
    local body2=$(echo $response2 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status2=$(echo $response2 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status2" -eq 200 ]; then
        log_success "Python兼容接口测试通过 (HTTP $status2)"
    else
        log_error "Python兼容接口测试失败 (HTTP $status2)"
        echo "   错误: $body2"
    fi
}

# 测试通用事件上传接口
test_upload_common_event() {
    log_info "测试通用事件上传接口"
    
    # 生成测试数据
    local event_data='{
        "health_data": [
            {
                "device_id": "DEVICE_001",
                "user_id": "101",
                "org_id": "1",
                "customer_id": "8",
                "heart_rate": 88,
                "blood_oxygen": 96,
                "temperature": 37.0,
                "create_time": "'$(date '+%Y-%m-%d %H:%M:%S')'"
            }
        ],
        "device_info": [
            {
                "device_id": "DEVICE_001",
                "device_name": "智能手环_001",
                "battery_level": 75,
                "customer_id": "8",
                "status": "online"
            }
        ],
        "alert_data": [
            {
                "alert_type": "heart_rate_abnormal",
                "device_id": "DEVICE_001",
                "user_id": "101",
                "severity": "high",
                "message": "心率异常：检测到心率持续过高",
                "timestamp": "'$(date '+%Y-%m-%d %H:%M:%S')'"
            }
        ]
    }'
    
    echo "🔄 测试新格式接口: /batch/upload-common-event"
    local response1=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$event_data" \
        "$BASE_URL/batch/upload-common-event")
    
    local body1=$(echo $response1 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status1=$(echo $response1 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status1" -eq 200 ]; then
        log_success "新格式接口测试通过 (HTTP $status1)"
        echo "   健康数据处理: $(echo $body1 | jq -r '.result.health_result.processed // "N/A"') 条"
        echo "   设备信息处理: $(echo $body1 | jq -r '.result.device_result.processed // "N/A"') 条"
    else
        log_error "新格式接口测试失败 (HTTP $status1)"
        echo "   错误: $body1"
    fi
    
    echo
    echo "🔄 测试Python兼容接口: /batch/upload_common_event"
    local response2=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        -H "$CONTENT_TYPE" \
        -d "$event_data" \
        "$BASE_URL/batch/upload_common_event")
    
    local body2=$(echo $response2 | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status2=$(echo $response2 | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status2" -eq 200 ]; then
        log_success "Python兼容接口测试通过 (HTTP $status2)"
    else
        log_error "Python兼容接口测试失败 (HTTP $status2)"
        echo "   错误: $body2"
    fi
}

# 测试统计信息接口
test_get_stats() {
    log_info "测试统计信息接口"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET \
        "$BASE_URL/batch/stats")
    
    local body=$(echo $response | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status=$(echo $response | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" -eq 200 ]; then
        log_success "统计信息接口测试通过 (HTTP $status)"
        echo "   已处理: $(echo $body | jq -r '.result.processed // "N/A"') 条"
        echo "   批次数: $(echo $body | jq -r '.result.batches // "N/A"')"
        echo "   错误数: $(echo $body | jq -r '.result.errors // "N/A"')"
        echo "   重复数: $(echo $body | jq -r '.result.duplicates // "N/A"')"
    else
        log_error "统计信息接口测试失败 (HTTP $status)"
        echo "   错误: $body"
    fi
}

# 测试健康检查接口
test_health_check() {
    log_info "测试健康检查接口"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X GET \
        "$BASE_URL/batch/health")
    
    local body=$(echo $response | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status=$(echo $response | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" -eq 200 ]; then
        log_success "健康检查接口测试通过 (HTTP $status)"
        echo "   服务状态: $(echo $body | jq -r '.result.status // "N/A"')"
        echo "   兼容性: $(echo $body | jq -r '.result.features.python_compatibility // "N/A"')"
    else
        log_error "健康检查接口测试失败 (HTTP $status)"
        echo "   错误: $body"
    fi
}

# 测试性能测试接口
test_performance() {
    local data_size=${1:-100}
    log_info "测试性能测试接口 (数据规模: $data_size)"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -X POST \
        "$BASE_URL/batch/performance-test?dataSize=$data_size")
    
    local body=$(echo $response | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status=$(echo $response | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" -eq 200 ]; then
        log_success "性能测试接口测试通过 (HTTP $status)"
        echo "   测试数据: $(echo $body | jq -r '.result.test_data_size // "N/A"') 条"
        echo "   总耗时: $(echo $body | jq -r '.result.total_time_ms // "N/A"') ms"
        echo "   QPS: $(echo $body | jq -r '.result.qps // "N/A"')"
        echo "   性能评级: $(echo $body | jq -r '.result.performance_rating // "N/A"')"
    else
        log_error "性能测试接口测试失败 (HTTP $status)"
        echo "   错误: $body"
    fi
}

# 主函数
main() {
    echo "🚀 ljwx-boot 批量上传接口 cURL 测试"
    echo "   目标服务: $BASE_URL"
    echo "   测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo
    
    # 检查 jq 是否安装
    if ! command -v jq &> /dev/null; then
        log_warning "jq 未安装，JSON 解析可能不完整"
        echo "   建议安装: brew install jq (macOS) 或 apt-get install jq (Ubuntu)"
        echo
    fi
    
    # 解析命令行参数
    case "${1:-all}" in
        "health")
            test_upload_health_data
            ;;
        "device")
            test_upload_device_info
            ;;
        "event")
            test_upload_common_event
            ;;
        "stats")
            test_get_stats
            ;;
        "check")
            test_health_check
            ;;
        "perf")
            test_performance "${2:-100}"
            ;;
        "all"|*)
            # 运行所有测试
            test_health_check
            echo
            test_upload_health_data
            echo
            test_upload_device_info
            echo
            test_upload_common_event
            echo
            test_get_stats
            echo
            test_performance 100
            ;;
    esac
    
    echo
    log_info "测试完成"
    echo
    echo "使用方法:"
    echo "  $0 [test_type] [params]"
    echo
    echo "测试类型:"
    echo "  all     - 运行所有测试 (默认)"
    echo "  health  - 仅测试健康数据接口"
    echo "  device  - 仅测试设备信息接口"
    echo "  event   - 仅测试通用事件接口"
    echo "  stats   - 仅测试统计信息接口"
    echo "  check   - 仅测试健康检查接口"
    echo "  perf    - 仅测试性能接口 (可指定数据规模)"
    echo
    echo "示例:"
    echo "  $0 health          # 测试健康数据接口"
    echo "  $0 perf 1000       # 测试性能接口 (1000条数据)"
}

# 设置BASE_URL（如果提供了参数）
if [[ $1 =~ ^https?:// ]]; then
    BASE_URL="$1"
    shift
fi

# 运行主函数
main "$@"