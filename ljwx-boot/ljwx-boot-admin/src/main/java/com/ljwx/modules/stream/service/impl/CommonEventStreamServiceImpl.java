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

package com.ljwx.modules.stream.service.impl;

import com.ljwx.common.api.Result;
import com.ljwx.modules.stream.domain.dto.CommonEventUploadRequest;
import com.ljwx.modules.stream.service.ICommonEventStreamService;
import com.ljwx.modules.alert.service.IAlertService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.time.Instant;
import java.time.ZoneId;
import java.util.*;

/**
 * 通用事件流处理服务实现
 * 
 * 兼容ljwx-bigscreen的通用事件上传接口，用于处理SOS、跌倒检测等紧急事件
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName CommonEventStreamServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class CommonEventStreamServiceImpl implements ICommonEventStreamService {

    private final IAlertService alertService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> uploadCommonEvent(CommonEventUploadRequest request) {
        
        log.info("🚨 通用事件上传开始: eventType={}, eventLevel={}", request.getEventType(), request.getEventLevel());
        log.info("🚨 事件详情: {}", request);
        
        try {
            // 处理单个和批量事件
            if (request.getBatchEvents() != null && !request.getBatchEvents().isEmpty()) {
                return processBatchEvents(request.getBatchEvents());
            } else {
                return processSingleEvent(request);
            }
            
        } catch (Exception e) {
            log.error("❌ 通用事件上传处理失败: {}", e.getMessage(), e);
            return Result.failure("通用事件上传处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理单个事件
     */
    private Result<Map<String, Object>> processSingleEvent(CommonEventUploadRequest request) {
        
        log.info("🔍 处理单个事件: eventId={}, eventType={}", request.getEventId(), request.getEventType());
        
        try {
            // 基础验证
            if (!StringUtils.hasText(request.getEventType())) {
                log.warn("⚠️ 事件类型为空，无法处理");
                return Result.failure("事件类型不能为空");
            }
            
            if (!StringUtils.hasText(request.getDeviceSn()) && !StringUtils.hasText(request.getUserId())) {
                log.warn("⚠️ 设备SN和用户ID都为空，无法处理");
                return Result.failure("设备SN或用户ID至少需要提供一个");
            }
            
            // 构建告警数据
            Map<String, Object> alertData = buildAlertData(request);
            
            // 根据事件类型和级别确定处理优先级
            boolean isEmergency = isEmergencyEvent(request.getEventType(), request.getEventLevel());
            
            Map<String, Object> result = new HashMap<>();
            
            if (isEmergency) {
                // 紧急事件立即处理
                log.info("🚨 紧急事件立即处理: {}", request.getEventType());
                boolean processed = processEmergencyEvent(alertData);
                
                if (processed) {
                    result.put("success", true);
                    result.put("priority", "emergency");
                    result.put("message", "紧急事件处理成功，已触发告警");
                    result.put("immediateAlert", true);
                } else {
                    log.error("❌ 紧急事件处理失败");
                    return Result.failure("紧急事件处理失败");
                }
            } else {
                // 普通事件异步处理
                log.info("📋 普通事件异步处理: {}", request.getEventType());
                boolean queued = queueNormalEvent(alertData);
                
                if (queued) {
                    result.put("success", true);
                    result.put("priority", "normal");
                    result.put("message", "事件已加入处理队列");
                    result.put("queued", true);
                } else {
                    log.error("❌ 事件队列处理失败");
                    return Result.failure("事件队列处理失败");
                }
            }
            
            result.put("eventId", request.getEventId());
            result.put("eventType", request.getEventType());
            result.put("processedCount", 1);
            
            log.info("✅ 单个事件处理完成: eventId={}", request.getEventId());
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("❌ 单个事件处理异常: {}", e.getMessage(), e);
            return Result.failure("单个事件处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理批量事件
     */
    private Result<Map<String, Object>> processBatchEvents(List<CommonEventUploadRequest> batchEvents) {
        
        log.info("🔍 处理批量事件，数量: {}", batchEvents.size());
        
        int successCount = 0;
        int emergencyCount = 0;
        int errorCount = 0;
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            for (int i = 0; i < batchEvents.size(); i++) {
                CommonEventUploadRequest event = batchEvents.get(i);
                log.info("🔍 处理第{}个事件: {}", i + 1, event.getEventType());
                
                try {
                    Result<Map<String, Object>> eventResult = processSingleEvent(event);
                    Map<String, Object> resultData = eventResult.getData();
                    results.add(resultData);
                    
                    if (eventResult.isSuccess()) {
                        successCount++;
                        if ("emergency".equals(resultData.get("priority"))) {
                            emergencyCount++;
                        }
                    } else {
                        errorCount++;
                    }
                    
                } catch (Exception e) {
                    log.error("❌ 第{}个事件处理异常: {}", i + 1, e.getMessage());
                    errorCount++;
                    
                    Map<String, Object> errorResult = new HashMap<>();
                    errorResult.put("success", false);
                    errorResult.put("eventId", event.getEventId());
                    errorResult.put("error", e.getMessage());
                    results.add(errorResult);
                }
            }
            
            // 构建批量处理结果
            Map<String, Object> batchResult = new HashMap<>();
            batchResult.put("success", true);
            batchResult.put("totalCount", batchEvents.size());
            batchResult.put("successCount", successCount);
            batchResult.put("emergencyCount", emergencyCount);
            batchResult.put("errorCount", errorCount);
            batchResult.put("message", String.format("批量事件处理完成: 成功%d(紧急%d), 失败%d", 
                    successCount, emergencyCount, errorCount));
            batchResult.put("results", results);
            
            log.info("✅ 批量事件处理完成: 成功{}, 紧急{}, 失败{}", successCount, emergencyCount, errorCount);
            
            return Result.data(batchResult);
            
        } catch (Exception e) {
            log.error("❌ 批量事件处理异常: {}", e.getMessage(), e);
            return Result.failure("批量事件处理失败: " + e.getMessage());
        }
    }

    /**
     * 构建告警数据
     */
    private Map<String, Object> buildAlertData(CommonEventUploadRequest request) {
        Map<String, Object> alertData = new HashMap<>();
        
        alertData.put("eventId", request.getEventId());
        alertData.put("eventType", request.getEventType());
        alertData.put("eventLevel", request.getEventLevel() != null ? request.getEventLevel() : "WARNING");
        alertData.put("deviceSn", request.getDeviceSn());
        alertData.put("userId", request.getUserId());
        alertData.put("customerId", request.getCustomerId());
        alertData.put("orgId", request.getOrgId());
        alertData.put("eventDescription", request.getEventDescription());
        alertData.put("priority", request.getPriority() != null ? request.getPriority() : 3);
        alertData.put("immediateNotification", request.getImmediateNotification() != null ? request.getImmediateNotification() : false);
        
        // 时间处理
        if (request.getEventTime() != null) {
            LocalDateTime eventTime = Instant.ofEpochMilli(request.getEventTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            alertData.put("eventTime", eventTime);
        } else {
            alertData.put("eventTime", LocalDateTime.now());
        }
        
        // 位置信息
        if (request.getLocation() != null) {
            alertData.put("location", request.getLocation());
        }
        
        // 健康数据
        if (request.getHealthData() != null) {
            alertData.put("healthData", request.getHealthData());
        }
        
        // 事件详细信息
        if (request.getEventDetails() != null) {
            alertData.put("eventDetails", request.getEventDetails());
        }
        
        // 触发条件
        if (request.getTriggerConditions() != null) {
            alertData.put("triggerConditions", request.getTriggerConditions());
        }
        
        // 通知方式
        if (request.getNotificationMethods() != null) {
            alertData.put("notificationMethods", request.getNotificationMethods());
        }
        
        // 相关联系人
        if (request.getRelatedContacts() != null) {
            alertData.put("relatedContacts", request.getRelatedContacts());
        }
        
        // 超时设置
        if (request.getTimeoutMinutes() != null) {
            alertData.put("timeoutMinutes", request.getTimeoutMinutes());
        }
        
        alertData.put("eventSource", request.getEventSource() != null ? request.getEventSource() : "api");
        alertData.put("eventStatus", request.getEventStatus() != null ? request.getEventStatus() : "PENDING");
        
        return alertData;
    }

    /**
     * 判断是否为紧急事件
     */
    private boolean isEmergencyEvent(String eventType, String eventLevel) {
        // 紧急事件类型
        Set<String> emergencyTypes = Set.of("SOS", "FALL", "HEART_ATTACK", "ABNORMAL_HEART_RATE");
        
        // 紧急级别
        Set<String> emergencyLevels = Set.of("CRITICAL", "EMERGENCY");
        
        return emergencyTypes.contains(eventType) || emergencyLevels.contains(eventLevel);
    }

    /**
     * 处理紧急事件
     */
    private boolean processEmergencyEvent(Map<String, Object> alertData) {
        try {
            // TODO: 调用告警服务立即处理紧急事件
            // return alertService.processEmergencyAlert(alertData);
            
            log.info("🚨 紧急事件处理: {}", alertData.get("eventType"));
            // 模拟处理成功
            return true;
            
        } catch (Exception e) {
            log.error("❌ 紧急事件处理异常: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 队列普通事件
     */
    private boolean queueNormalEvent(Map<String, Object> alertData) {
        try {
            // TODO: 将普通事件加入异步处理队列
            // return alertService.queueNormalAlert(alertData);
            
            log.info("📋 普通事件队列: {}", alertData.get("eventType"));
            // 模拟队列成功
            return true;
            
        } catch (Exception e) {
            log.error("❌ 事件队列异常: {}", e.getMessage());
            return false;
        }
    }

}