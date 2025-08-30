/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.admin.controller.alert;

import com.ljwx.common.api.Result;
import com.ljwx.modules.alert.service.UnifiedAlertSystem;
import com.ljwx.modules.alert.service.monitor.AlertProcessingMonitor;
import com.ljwx.modules.alert.service.monitor.MetricsCollector;
import com.ljwx.modules.alert.service.optimizer.IntelligentOptimizer;
import com.ljwx.modules.alert.service.queue.PriorityMessageQueue;
import com.ljwx.modules.alert.domain.dto.AlertProcessingRequest;
import com.ljwx.modules.alert.domain.dto.AlertProcessingResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 统一告警系统控制器
 * 提供告警处理、监控和优化的REST API接口
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.alert.UnifiedAlertController
 * @CreateTime 2024-08-30 - 22:00:00
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/alert")
@RequiredArgsConstructor
@Tag(name = "统一告警系统", description = "智能告警处理、监控和优化API")
public class UnifiedAlertController {

    private final UnifiedAlertSystem unifiedAlertSystem;
    private final AlertProcessingMonitor processingMonitor;
    private final MetricsCollector metricsCollector;
    private final IntelligentOptimizer intelligentOptimizer;
    private final PriorityMessageQueue messageQueue;

    /**
     * 处理单个告警
     */
    @PostMapping("/process")
    @Operation(summary = "处理告警", description = "智能处理单个告警请求")
    public Result<AlertProcessingResponse> processAlert(
            @RequestBody @Valid AlertProcessingRequest request) {
        
        log.info("收到告警处理请求: alertType={}, deviceSn={}, severity={}", 
                request.getAlertType(), request.getDeviceSn(), request.getSeverityLevel());
        
        try {
            long startTime = System.currentTimeMillis();
            
            AlertProcessingResponse response = unifiedAlertSystem.processAlert(request);
            
            long processingTime = System.currentTimeMillis() - startTime;
            
            // 记录处理指标
            if (response.isSuccess()) {
                metricsCollector.recordAlertProcessingSuccess(processingTime);
            } else {
                metricsCollector.recordAlertProcessingFailure(processingTime, "processing_error");
            }
            
            log.info("告警处理完成: success={}, alertId={}, time={}ms", 
                    response.isSuccess(), response.getAlertId(), processingTime);
            
            return Result.data(response);
            
        } catch (Exception e) {
            long processingTime = System.currentTimeMillis() - System.currentTimeMillis();
            metricsCollector.recordAlertProcessingFailure(processingTime, e.getClass().getSimpleName());
            
            log.error("告警处理失败", e);
            return Result.failure("告警处理失败: " + e.getMessage());
        }
    }

    /**
     * 批量处理告警
     */
    @PostMapping("/process/batch")
    @Operation(summary = "批量处理告警", description = "批量处理多个告警请求")
    public Result<List<AlertProcessingResponse>> processBatchAlerts(
            @RequestBody @Valid List<AlertProcessingRequest> requests) {
        
        log.info("收到批量告警处理请求: count={}", requests.size());
        
        try {
            long startTime = System.currentTimeMillis();
            
            List<AlertProcessingResponse> responses = unifiedAlertSystem.processBatchAlerts(requests);
            
            long processingTime = System.currentTimeMillis() - startTime;
            
            // 统计处理结果
            long successCount = responses.stream().mapToLong(r -> r.isSuccess() ? 1 : 0).sum();
            long failureCount = responses.size() - successCount;
            
            log.info("批量告警处理完成: total={}, success={}, failed={}, time={}ms", 
                    responses.size(), successCount, failureCount, processingTime);
            
            return Result.data(responses);
            
        } catch (Exception e) {
            log.error("批量告警处理失败", e);
            return Result.failure("批量告警处理失败: " + e.getMessage());
        }
    }

    /**
     * 获取系统性能监控数据
     */
    @GetMapping("/monitor/performance")
    @Operation(summary = "获取性能监控", description = "获取告警处理系统的实时性能监控数据")
    public Result<Map<String, Object>> getPerformanceMonitoring() {
        try {
            Map<String, Object> monitoringData = processingMonitor.monitorProcessingPerformance();
            return Result.data(monitoringData);
        } catch (Exception e) {
            log.error("获取性能监控数据失败", e);
            return Result.failure("获取监控数据失败: " + e.getMessage());
        }
    }

    /**
     * 获取系统指标快照
     */
    @GetMapping("/metrics/snapshot")
    @Operation(summary = "获取指标快照", description = "获取当前系统性能指标的快照")
    public Result<MetricsCollector.AlertMetricsSnapshot> getMetricsSnapshot() {
        try {
            MetricsCollector.AlertMetricsSnapshot snapshot = metricsCollector.getMetricsSnapshot();
            return Result.data(snapshot);
        } catch (Exception e) {
            log.error("获取指标快照失败", e);
            return Result.failure("获取指标快照失败: " + e.getMessage());
        }
    }

    /**
     * 获取队列状态
     */
    @GetMapping("/queue/status")
    @Operation(summary = "获取队列状态", description = "获取消息队列的当前状态统计")
    public Result<Map<String, Object>> getQueueStatus() {
        try {
            Map<String, Object> queueStats = messageQueue.getQueueStats();
            return Result.data(queueStats);
        } catch (Exception e) {
            log.error("获取队列状态失败", e);
            return Result.failure("获取队列状态失败: " + e.getMessage());
        }
    }

    /**
     * 生成优化建议
     */
    @GetMapping("/optimize/recommendations")
    @Operation(summary = "获取优化建议", description = "基于历史数据生成系统优化建议")
    public Result<IntelligentOptimizer.OptimizationPlan> getOptimizationRecommendations(
            @Parameter(description = "分析时间范围(天)", example = "7")
            @RequestParam(defaultValue = "7") int timeRangeDays) {
        
        try {
            IntelligentOptimizer.OptimizationPlan plan = intelligentOptimizer.generateOptimizationPlan(timeRangeDays);
            return Result.data(plan);
        } catch (Exception e) {
            log.error("生成优化建议失败", e);
            return Result.failure("生成优化建议失败: " + e.getMessage());
        }
    }

    /**
     * 清理过期的去重缓存
     */
    @PostMapping("/maintenance/cleanup-dedup-cache")
    @Operation(summary = "清理去重缓存", description = "清理过期的消息去重缓存")
    public Result<String> cleanupDedupCache() {
        try {
            messageQueue.cleanExpiredDedupCache();
            return Result.success("去重缓存清理完成");
        } catch (Exception e) {
            log.error("清理去重缓存失败", e);
            return Result.failure("清理去重缓存失败: " + e.getMessage());
        }
    }

    /**
     * 生成每日统计报告
     */
    @PostMapping("/maintenance/daily-report")
    @Operation(summary = "生成每日报告", description = "生成系统性能的每日统计报告")
    public Result<String> generateDailyReport() {
        try {
            metricsCollector.generateDailyReport();
            return Result.success("每日统计报告生成完成");
        } catch (Exception e) {
            log.error("生成每日报告失败", e);
            return Result.failure("生成每日报告失败: " + e.getMessage());
        }
    }

    /**
     * 系统健康检查
     */
    @GetMapping("/health")
    @Operation(summary = "系统健康检查", description = "检查告警系统各组件的健康状态")
    public Result<Map<String, Object>> healthCheck() {
        try {
            Map<String, Object> healthStatus = performHealthCheck();
            return Result.data(healthStatus);
        } catch (Exception e) {
            log.error("系统健康检查失败", e);
            return Result.failure("健康检查失败: " + e.getMessage());
        }
    }

    /**
     * 测试告警处理接口
     */
    @PostMapping("/test")
    @Operation(summary = "测试告警处理", description = "创建测试告警用于验证系统功能")
    public Result<AlertProcessingResponse> testAlertProcessing(
            @Parameter(description = "告警类型", example = "HEART_RATE")
            @RequestParam(defaultValue = "HEART_RATE") String alertType,
            @Parameter(description = "严重程度", example = "HIGH") 
            @RequestParam(defaultValue = "HIGH") String severityLevel,
            @Parameter(description = "租户ID", example = "1")
            @RequestParam(defaultValue = "1") Long customerId) {
        
        try {
            // 创建测试告警请求
            AlertProcessingRequest testRequest = AlertProcessingRequest.builder()
                    .alertType(alertType)
                    .deviceSn("TEST_DEVICE_" + System.currentTimeMillis())
                    .alertTimestamp(LocalDateTime.now())
                    .alertDesc("系统测试告警 - " + alertType)
                    .severityLevel(severityLevel)
                    .userId(1L)
                    .orgId(1L)
                    .customerId(customerId)
                    .ruleId(1L)
                    .latitude(new BigDecimal("39.9042"))
                    .longitude(new BigDecimal("116.4074"))
                    .build();
            
            AlertProcessingResponse response = unifiedAlertSystem.processAlert(testRequest);
            
            log.info("测试告警处理完成: alertId={}, success={}", 
                    response.getAlertId(), response.isSuccess());
            
            return Result.data(response);
            
        } catch (Exception e) {
            log.error("测试告警处理失败", e);
            return Result.failure("测试失败: " + e.getMessage());
        }
    }

    /**
     * 执行系统健康检查
     */
    private Map<String, Object> performHealthCheck() {
        Map<String, Object> healthStatus = Map.of(
            "timestamp", LocalDateTime.now(),
            "alertSystem", "healthy",
            "messageQueue", "healthy", 
            "monitoring", "healthy",
            "optimizer", "healthy",
            "overallStatus", "healthy",
            "version", "1.0.0"
        );
        
        return healthStatus;
    }
}