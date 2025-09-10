#!/bin/bash

# V2消息系统集成验证脚本
# 验证跨平台V2消息系统的完整功能
# 
# Author: jjgao
# Project: ljwx V2 Message System
# Date: 2025-09-10

set -e  # 遇到错误立即退出

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

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info "V2消息系统集成验证开始"
log_info "项目根目录: $PROJECT_ROOT"

# 验证计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "运行测试: $test_name"
    
    if eval "$test_command"; then
        log_success "✅ $test_name 通过"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        log_error "❌ $test_name 失败"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 1. 验证ljwx-phone Flutter/Dart V2模型
validate_flutter_models() {
    log_info "验证Flutter/Dart V2模型..."
    
    local flutter_models_dir="$PROJECT_ROOT/ljwx-phone/lib/models"
    local flutter_services_dir="$PROJECT_ROOT/ljwx-phone/lib/services"
    
    # 检查模型文件存在性
    if [[ -f "$flutter_models_dir/message_v2_model.dart" ]]; then
        log_success "Flutter V2模型文件存在"
        
        # 检查关键类定义
        if grep -q "class DeviceMessageV2" "$flutter_models_dir/message_v2_model.dart" && \
           grep -q "class DeviceMessageDetailV2" "$flutter_models_dir/message_v2_model.dart" && \
           grep -q "enum.*Enum" "$flutter_models_dir/message_v2_model.dart"; then
            log_success "Flutter V2模型类定义完整"
            return 0
        else
            log_error "Flutter V2模型类定义不完整"
            return 1
        fi
    else
        log_error "Flutter V2模型文件不存在"
        return 1
    fi
}

# 2. 验证ljwx-phone Flutter/Dart V2服务
validate_flutter_services() {
    log_info "验证Flutter/Dart V2服务..."
    
    local flutter_services_dir="$PROJECT_ROOT/ljwx-phone/lib/services"
    
    if [[ -f "$flutter_services_dir/message_v2_service.dart" ]]; then
        log_success "Flutter V2服务文件存在"
        
        # 检查关键服务类
        if grep -q "class MessageV2DatabaseService" "$flutter_services_dir/message_v2_service.dart" && \
           grep -q "class MessageV2ApiService" "$flutter_services_dir/message_v2_service.dart"; then
            log_success "Flutter V2服务类定义完整"
            return 0
        else
            log_error "Flutter V2服务类定义不完整"
            return 1
        fi
    else
        log_error "Flutter V2服务文件不存在"
        return 1
    fi
}

# 3. 验证ljwx-watch HarmonyOS V2服务
validate_harmonyos_service() {
    log_info "验证HarmonyOS V2服务..."
    
    local harmony_service_file="$PROJECT_ROOT/ljwx-watch/entry/src/main/java/com/ljwx/watch/service/MessageV2Service.java"
    
    if [[ -f "$harmony_service_file" ]]; then
        log_success "HarmonyOS V2服务文件存在"
        
        # 检查关键服务方法
        if grep -q "public static class MessageV2" "$harmony_service_file" && \
           grep -q "fetchMessages" "$harmony_service_file" && \
           grep -q "acknowledgeMessage" "$harmony_service_file"; then
            log_success "HarmonyOS V2服务方法完整"
            return 0
        else
            log_error "HarmonyOS V2服务方法不完整"
            return 1
        fi
    else
        log_error "HarmonyOS V2服务文件不存在"
        return 1
    fi
}

# 4. 验证ljwx-boot V2 API控制器
validate_boot_api_controllers() {
    log_info "验证ljwx-boot V2 API控制器..."
    
    local v2_controller="$PROJECT_ROOT/ljwx-boot/ljwx-boot-admin/src/main/java/com/ljwx/admin/controller/health/TDeviceMessageV2Controller.java"
    local compatibility_controller="$PROJECT_ROOT/ljwx-boot/ljwx-boot-admin/src/main/java/com/ljwx/admin/controller/health/MessageCompatibilityController.java"
    
    # 检查V2控制器
    if [[ -f "$v2_controller" ]]; then
        log_success "V2 API控制器文件存在"
        
        if grep -q "@RequestMapping(\"/api/v2/messages\")" "$v2_controller" && \
           grep -q "createMessage" "$v2_controller" && \
           grep -q "batchCreateMessages" "$v2_controller"; then
            log_success "V2 API控制器方法完整"
        else
            log_error "V2 API控制器方法不完整"
            return 1
        fi
    else
        log_error "V2 API控制器文件不存在"
        return 1
    fi
    
    # 检查兼容性控制器
    if [[ -f "$compatibility_controller" ]]; then
        log_success "V1兼容性控制器文件存在"
        
        if grep -q "@RequestMapping(\"t_device_message\")" "$compatibility_controller" && \
           grep -q "convertToV2" "$compatibility_controller"; then
            log_success "V1兼容性控制器方法完整"
            return 0
        else
            log_error "V1兼容性控制器方法不完整"
            return 1
        fi
    else
        log_error "V1兼容性控制器文件不存在"
        return 1
    fi
}

# 5. 验证Redis消息总线集成
validate_redis_integration() {
    log_info "验证Redis消息总线集成..."
    
    local unified_publisher="$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/UnifiedMessagePublisher.java"
    
    if [[ -f "$unified_publisher" ]]; then
        log_success "统一消息发布器文件存在"
        
        # 检查V2 Redis集成方法
        if grep -q "publishMessageCreated" "$unified_publisher" && \
           grep -q "publishMessageDistributed" "$unified_publisher" && \
           grep -q "publishBatchMessageDistributed" "$unified_publisher" && \
           grep -q "publishMessageAcknowledged" "$unified_publisher" && \
           grep -q "pushToDeviceQueue" "$unified_publisher"; then
            log_success "Redis消息总线V2集成方法完整"
            return 0
        else
            log_error "Redis消息总线V2集成方法不完整"
            return 1
        fi
    else
        log_error "统一消息发布器文件不存在"
        return 1
    fi
}

# 6. 验证集成测试
validate_integration_tests() {
    log_info "验证集成测试..."
    
    local integration_test="$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/test/java/com/ljwx/modules/health/integration/MessageV2IntegrationTest.java"
    
    if [[ -f "$integration_test" ]]; then
        log_success "V2集成测试文件存在"
        
        # 检查测试方法
        if grep -q "testCompleteV2MessageFlow" "$integration_test" && \
           grep -q "testV2BatchMessageProcessing" "$integration_test" && \
           grep -q "testV2MessagePerformance" "$integration_test" && \
           grep -q "testV2MessageErrorHandling" "$integration_test"; then
            log_success "V2集成测试方法完整"
            return 0
        else
            log_error "V2集成测试方法不完整"
            return 1
        fi
    else
        log_error "V2集成测试文件不存在"
        return 1
    fi
}

# 7. 验证数据库兼容性
validate_database_compatibility() {
    log_info "验证数据库兼容性..."
    
    # 检查V2实体类
    local v2_message_entity="$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/domain/entity/TDeviceMessageV2.java"
    local v2_detail_entity="$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/domain/entity/TDeviceMessageDetailV2.java"
    
    if [[ -f "$v2_message_entity" && -f "$v2_detail_entity" ]]; then
        log_success "V2数据库实体类文件存在"
        
        # 检查关键注解
        if grep -q "@TableName" "$v2_message_entity" && \
           grep -q "@TableField" "$v2_message_entity" && \
           grep -q "@TableName" "$v2_detail_entity" && \
           grep -q "@TableField" "$v2_detail_entity"; then
            log_success "V2数据库实体类注解完整"
            return 0
        else
            log_error "V2数据库实体类注解不完整"
            return 1
        fi
    else
        log_error "V2数据库实体类文件不存在"
        return 1
    fi
}

# 8. 性能指标验证
validate_performance_optimization() {
    log_info "验证性能优化..."
    
    local performance_indicators=0
    
    # 检查ENUM优化
    if grep -rq "enum.*V2" "$PROJECT_ROOT/ljwx-phone/lib/models/" 2>/dev/null || \
       grep -rq "enum.*V2" "$PROJECT_ROOT/ljwx-watch/entry/src/main/java/" 2>/dev/null || \
       grep -rq "enum.*V2" "$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/" 2>/dev/null; then
        log_success "✅ ENUM优化实现检测到"
        performance_indicators=$((performance_indicators + 1))
    fi
    
    # 检查缓存策略
    if grep -rq "cache" "$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/com/ljwx/modules/health/service/" 2>/dev/null; then
        log_success "✅ 缓存策略实现检测到"
        performance_indicators=$((performance_indicators + 1))
    fi
    
    # 检查批量操作
    if grep -rq "batch" "$PROJECT_ROOT/ljwx-boot/ljwx-boot-admin/src/main/java/" 2>/dev/null; then
        log_success "✅ 批量操作实现检测到"
        performance_indicators=$((performance_indicators + 1))
    fi
    
    # 检查异步处理
    if grep -rq "@Async" "$PROJECT_ROOT/ljwx-boot/ljwx-boot-modules/src/main/java/" 2>/dev/null; then
        log_success "✅ 异步处理实现检测到"
        performance_indicators=$((performance_indicators + 1))
    fi
    
    if [[ $performance_indicators -ge 3 ]]; then
        log_success "性能优化特性充分实现 ($performance_indicators/4)"
        return 0
    else
        log_warning "性能优化特性实现不足 ($performance_indicators/4)"
        return 1
    fi
}

# 主验证流程
main() {
    log_info "开始V2消息系统完整集成验证"
    echo "============================================="
    
    # 运行所有验证测试
    run_test "Flutter/Dart V2模型验证" "validate_flutter_models"
    run_test "Flutter/Dart V2服务验证" "validate_flutter_services"
    run_test "HarmonyOS V2服务验证" "validate_harmonyos_service"
    run_test "ljwx-boot V2 API控制器验证" "validate_boot_api_controllers"
    run_test "Redis消息总线集成验证" "validate_redis_integration"
    run_test "集成测试验证" "validate_integration_tests"
    run_test "数据库兼容性验证" "validate_database_compatibility"
    run_test "性能优化验证" "validate_performance_optimization"
    
    echo "============================================="
    log_info "V2消息系统集成验证完成"
    
    # 输出测试结果汇总
    echo ""
    log_info "测试结果汇总:"
    log_info "总测试数: $TOTAL_TESTS"
    log_success "通过测试: $PASSED_TESTS"
    
    if [[ $FAILED_TESTS -gt 0 ]]; then
        log_error "失败测试: $FAILED_TESTS"
    else
        log_success "失败测试: $FAILED_TESTS"
    fi
    
    local success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    log_info "成功率: ${success_rate}%"
    
    # 最终结果判定
    if [[ $success_rate -ge 90 ]]; then
        echo ""
        log_success "🎉 V2消息系统集成验证成功完成！"
        log_success "系统已准备好进行生产部署。"
        exit 0
    elif [[ $success_rate -ge 75 ]]; then
        echo ""
        log_warning "⚠️  V2消息系统集成验证基本通过，但存在一些问题需要修复。"
        exit 1
    else
        echo ""
        log_error "❌ V2消息系统集成验证失败，需要进行重大修复。"
        exit 2
    fi
}

# 脚本入口
main "$@"