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

package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.model.AlertResult;
import com.ljwx.modules.health.domain.model.HealthDataEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 批量告警处理器
 * 高性能批量健康数据告警检查和处理
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName BatchAlertProcessor
 * @CreateTime 2025-09-23
 */
@Slf4j
@Service
public class BatchAlertProcessor {
    
    @Autowired
    private AlertRuleEngineService alertRuleEngineService;
    
    @Autowired
    private ITAlertInfoService alertInfoService;
    
    @Autowired
    private Executor executor;
    
    // 统计信息
    private final AtomicLong processedCount = new AtomicLong(0);
    private final AtomicLong alertTriggeredCount = new AtomicLong(0);
    private final AtomicLong errorCount = new AtomicLong(0);
    
    /**
     * 批量处理健康数据告警检查
     * 采用分组并行处理，按客户ID分组提高缓存命中率
     */
    public Map<String, Object> processBatchAlerts(List<TUserHealthData> healthDataList) {
        if (healthDataList == null || healthDataList.isEmpty()) {
            return buildEmptyResult();
        }
        
        long startTime = System.currentTimeMillis();
        log.info("🚨 开始批量告警检查，数据量: {}", healthDataList.size());
        
        try {
            // 1. 按客户ID分组，提高缓存命中率
            Map<Long, List<TUserHealthData>> groupedByCustomer = healthDataList.stream()
                .filter(data -> data.getCustomerId() != null)
                .collect(Collectors.groupingBy(TUserHealthData::getCustomerId));
            
            // 2. 并行处理每个客户的数据
            List<CompletableFuture<List<AlertResult>>> futures = groupedByCustomer.entrySet().stream()
                .map(entry -> CompletableFuture.supplyAsync(() -> 
                    processCustomerHealthData(entry.getKey(), entry.getValue()), executor))
                .collect(Collectors.toList());
            
            // 3. 收集所有告警结果
            List<AlertResult> allAlerts = futures.stream()
                .map(future -> {
                    try {
                        return future.get();
                    } catch (Exception e) {
                        log.error("获取告警结果失败", e);
                        errorCount.incrementAndGet();
                        return Collections.<AlertResult>emptyList();
                    }
                })
                .flatMap(List::stream)
                .collect(Collectors.toList());
            
            // 4. 批量保存告警信息
            if (!allAlerts.isEmpty()) {
                saveAlertsInBatch(allAlerts);
            }
            
            long processingTime = System.currentTimeMillis() - startTime;
            
            // 5. 构建结果
            Map<String, Object> result = buildProcessResult(
                healthDataList.size(), allAlerts.size(), processingTime);
            
            log.info("✅ 批量告警检查完成: 处理{}条数据，触发{}个告警，耗时{}ms", 
                healthDataList.size(), allAlerts.size(), processingTime);
            
            return result;
            
        } catch (Exception e) {
            long errorTime = System.currentTimeMillis() - startTime;
            log.error("❌ 批量告警检查失败，耗时{}ms", errorTime, e);
            errorCount.addAndGet(healthDataList.size());
            
            return Map.of(
                "success", false,
                "processed", 0,
                "alerts_triggered", 0,
                "errors", healthDataList.size(),
                "processing_time_ms", errorTime,
                "error_message", e.getMessage()
            );
        }
    }
    
    /**
     * 处理单个客户的健康数据
     */
    private List<AlertResult> processCustomerHealthData(Long customerId, List<TUserHealthData> healthDataList) {
        List<AlertResult> customerAlerts = new ArrayList<>();
        
        try {
            log.debug("处理客户{}的健康数据，数量: {}", customerId, healthDataList.size());
            
            // 批量转换为HealthDataEvent
            List<HealthDataEvent> events = healthDataList.stream()
                .map(this::convertToHealthDataEvent)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
            
            // 并行告警评估
            for (HealthDataEvent event : events) {
                try {
                    List<AlertResult> alerts = alertRuleEngineService.evaluateRules(event);
                    if (alerts != null && !alerts.isEmpty()) {
                        customerAlerts.addAll(alerts);
                        alertTriggeredCount.addAndGet(alerts.size());
                    }
                    processedCount.incrementAndGet();
                } catch (Exception e) {
                    log.warn("单条健康数据告警评估失败: deviceSn={}", event.getDeviceSn(), e);
                    errorCount.incrementAndGet();
                }
            }
            
        } catch (Exception e) {
            log.error("处理客户{}健康数据失败", customerId, e);
            errorCount.addAndGet(healthDataList.size());
        }
        
        return customerAlerts;
    }
    
    /**
     * 转换TUserHealthData为HealthDataEvent
     */
    private HealthDataEvent convertToHealthDataEvent(TUserHealthData healthData) {
        if (healthData == null) {
            return null;
        }
        
        try {
            HealthDataEvent event = HealthDataEvent.builder()
                .deviceSn(healthData.getDeviceSn())
                .userId(healthData.getUserId())
                .orgId(healthData.getOrgId())
                .customerId(healthData.getCustomerId())
                .timestamp(healthData.getCreateTime() != null ? healthData.getCreateTime() : LocalDateTime.now())
                .build();
            
            // 构建健康数据映射
            Map<String, Object> healthDataMap = new HashMap<>();
            addIfNotNull(healthDataMap, "heart_rate", healthData.getHeartRate());
            addIfNotNull(healthDataMap, "blood_oxygen", healthData.getBloodOxygen());
            addIfNotNull(healthDataMap, "body_temperature", healthData.getTemperature());
            addIfNotNull(healthDataMap, "blood_pressure_systolic", healthData.getPressureHigh());
            addIfNotNull(healthDataMap, "blood_pressure_diastolic", healthData.getPressureLow());
            addIfNotNull(healthDataMap, "step", healthData.getStep());
            addIfNotNull(healthDataMap, "distance", healthData.getDistance());
            addIfNotNull(healthDataMap, "calorie", healthData.getCalorie());
            addIfNotNull(healthDataMap, "stress", healthData.getStress());
            addIfNotNull(healthDataMap, "latitude", healthData.getLatitude());
            addIfNotNull(healthDataMap, "longitude", healthData.getLongitude());
            addIfNotNull(healthDataMap, "altitude", healthData.getAltitude());
            
            event.setHealthData(healthDataMap);
            return event;
            
        } catch (Exception e) {
            log.warn("转换健康数据事件失败: deviceSn={}", healthData.getDeviceSn(), e);
            return null;
        }
    }
    
    /**
     * 批量保存告警信息
     */
    private void saveAlertsInBatch(List<AlertResult> alerts) {
        try {
            List<TAlertInfo> alertInfoList = alerts.stream()
                .map(this::convertToAlertInfo)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
            
            if (!alertInfoList.isEmpty()) {
                boolean success = alertInfoService.saveBatch(alertInfoList);
                if (success) {
                    log.debug("批量保存{}个告警信息成功", alertInfoList.size());
                } else {
                    log.warn("批量保存告警信息失败");
                }
            }
            
        } catch (Exception e) {
            log.error("批量保存告警信息异常", e);
        }
    }
    
    /**
     * 转换AlertResult为TAlertInfo
     */
    private TAlertInfo convertToAlertInfo(AlertResult alertResult) {
        if (alertResult == null) {
            return null;
        }
        
        try {
            TAlertInfo alertInfo = new TAlertInfo();
            alertInfo.setRuleId(alertResult.getRuleId());
            alertInfo.setDeviceSn(alertResult.getDeviceSn());
            alertInfo.setCustomerId(alertResult.getCustomerId());
            alertInfo.setAlertType(alertResult.getRuleType());
            alertInfo.setSeverityLevel(alertResult.getSeverityLevel());
            alertInfo.setAlertTimestamp(LocalDateTime.now());
            alertInfo.setOccurAt(LocalDateTime.now());
            alertInfo.setAlertStatus("TRIGGERED");
            alertInfo.setUserId(alertResult.getUserId());
            alertInfo.setOrgId(alertResult.getOrgId());
            alertInfo.setCreateTime(LocalDateTime.now());
            alertInfo.setUpdateTime(LocalDateTime.now());
            
            // 构建告警描述，包含物理指标和当前值信息
            String alertDesc = String.format("告警规则 %d 触发: %s 当前值异常", 
                alertResult.getRuleId(), 
                alertResult.getPhysicalSign() != null ? alertResult.getPhysicalSign() : "健康指标");
            if (alertResult.getAlertMessage() != null) {
                alertDesc = alertResult.getAlertMessage();
            }
            alertInfo.setAlertDesc(alertDesc);
            
            return alertInfo;
            
        } catch (Exception e) {
            log.warn("转换告警信息失败: ruleId={}", alertResult.getRuleId(), e);
            return null;
        }
    }
    
    /**
     * 构建处理结果
     */
    private Map<String, Object> buildProcessResult(int totalProcessed, int alertsTriggered, long processingTime) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("processed", totalProcessed);
        result.put("alerts_triggered", alertsTriggered);
        result.put("errors", 0);
        result.put("processing_time_ms", processingTime);
        
        // 性能指标
        if (processingTime > 0) {
            result.put("throughput_per_second", totalProcessed * 1000.0 / processingTime);
        }
        
        // 告警率
        if (totalProcessed > 0) {
            result.put("alert_rate_percent", alertsTriggered * 100.0 / totalProcessed);
        }
        
        return result;
    }
    
    /**
     * 构建空结果
     */
    private Map<String, Object> buildEmptyResult() {
        return Map.of(
            "success", true,
            "processed", 0,
            "alerts_triggered", 0,
            "errors", 0,
            "processing_time_ms", 0L
        );
    }
    
    /**
     * 添加非空值到Map
     */
    private void addIfNotNull(Map<String, Object> map, String key, Object value) {
        if (value != null) {
            map.put(key, value);
        }
    }
    
    /**
     * 获取统计信息
     */
    public Map<String, Object> getStatistics() {
        return Map.of(
            "total_processed", processedCount.get(),
            "total_alerts_triggered", alertTriggeredCount.get(),
            "total_errors", errorCount.get(),
            "success_rate", calculateSuccessRate()
        );
    }
    
    /**
     * 计算成功率
     */
    private double calculateSuccessRate() {
        long total = processedCount.get() + errorCount.get();
        if (total == 0) {
            return 100.0;
        }
        return (processedCount.get() * 100.0) / total;
    }
    
    /**
     * 重置统计信息
     */
    public void resetStatistics() {
        processedCount.set(0);
        alertTriggeredCount.set(0);
        errorCount.set(0);
        log.info("批量告警处理统计信息已重置");
    }
}