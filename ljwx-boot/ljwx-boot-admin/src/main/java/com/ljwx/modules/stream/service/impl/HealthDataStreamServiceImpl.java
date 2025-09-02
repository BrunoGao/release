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
import com.ljwx.modules.stream.domain.dto.HealthDataUploadRequest;
import com.ljwx.modules.stream.service.IHealthDataStreamService;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.system.service.ISysUserService;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.time.Instant;
import java.time.ZoneId;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 健康数据流处理服务实现
 * 
 * 兼容ljwx-bigscreen的健康数据上传接口，提供高性能的批量健康数据处理能力
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataStreamServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class HealthDataStreamServiceImpl implements IHealthDataStreamService {

    private final ITUserHealthDataService userHealthDataService;
    private final ISysUserService sysUserService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> uploadHealthData(HealthDataUploadRequest request, String deviceSn, String customerId) {
        
        log.info("🏥 健康数据上传开始 - 设备SN: {}, 客户ID: {}", deviceSn, customerId);
        log.info("🏥 请求数据: {}", request);
        
        try {
            // 处理单条和批量数据
            if (request.getBatchData() != null && !request.getBatchData().isEmpty()) {
                return processBatchHealthData(request.getBatchData(), deviceSn, customerId);
            } else {
                return processSingleHealthData(request, deviceSn, customerId);
            }
            
        } catch (Exception e) {
            log.error("❌ 健康数据上传处理失败: {}", e.getMessage(), e);
            return Result.failure("健康数据上传处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理单条健康数据
     */
    private Result<Map<String, Object>> processSingleHealthData(HealthDataUploadRequest request, String deviceSn, String customerId) {
        
        log.info("🔍 处理单条健康数据: deviceSn={}", deviceSn);
        
        try {
            // 从请求中提取或使用请求头中的设备SN
            String finalDeviceSn = StringUtils.hasText(request.getDeviceSn()) ? request.getDeviceSn() : deviceSn;
            
            if (!StringUtils.hasText(finalDeviceSn)) {
                log.warn("⚠️ 设备SN为空，无法处理数据");
                return Result.failure("设备SN不能为空");
            }
            
            // 获取用户组织信息
            Map<String, Object> userOrgInfo = getUserOrgInfo(finalDeviceSn);
            if (userOrgInfo == null) {
                log.warn("❌ 未找到设备对应的用户: {}", finalDeviceSn);
                return Result.failure("设备对应用户未找到");
            }
            
            Long userId = (Long) userOrgInfo.get("userId");
            Long orgId = (Long) userOrgInfo.get("orgId");
            Long customerIdFromDb = (Long) userOrgInfo.get("customerId");
            
            log.info("✅ 用户组织信息: userId={}, orgId={}, customerId={}", userId, orgId, customerIdFromDb);
            
            // 检查重复数据
            if (isDuplicateData(finalDeviceSn, request.getTimestamp())) {
                log.info("⚠️ 跳过重复数据: deviceSn={}, timestamp={}", finalDeviceSn, request.getTimestamp());
                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("reason", "duplicate");
                result.put("message", "数据库中已存在相同时间戳数据");
                return Result.data(result);
            }
            
            // 构建健康数据实体
            TUserHealthData healthData = buildHealthDataEntity(request, finalDeviceSn, userId, orgId, customerIdFromDb);
            
            // 保存到数据库
            boolean saved = userHealthDataService.save(healthData);
            
            if (saved) {
                log.info("✅ 健康数据保存成功: id={}", healthData.getId());
                
                // 异步处理告警检测
                processHealthAlerts(healthData);
                
                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("message", "健康数据保存成功");
                result.put("dataId", healthData.getId());
                result.put("processedCount", 1);
                
                return Result.data(result);
            } else {
                log.error("❌ 健康数据保存失败");
                return Result.failure("健康数据保存失败");
            }
            
        } catch (Exception e) {
            log.error("❌ 单条健康数据处理异常: {}", e.getMessage(), e);
            return Result.failure("单条健康数据处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理批量健康数据
     */
    private Result<Map<String, Object>> processBatchHealthData(List<HealthDataUploadRequest> batchData, String deviceSn, String customerId) {
        
        log.info("🔍 处理批量健康数据，数量: {}", batchData.size());
        
        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger duplicateCount = new AtomicInteger(0);
        AtomicInteger errorCount = new AtomicInteger(0);
        
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            // 批量处理
            for (int i = 0; i < batchData.size(); i++) {
                HealthDataUploadRequest item = batchData.get(i);
                log.info("🔍 处理第{}条数据: {}", i + 1, item.getDeviceSn());
                
                try {
                    Result<Map<String, Object>> itemResult = processSingleHealthData(item, deviceSn, customerId);
                    Map<String, Object> resultData = itemResult.getData();
                    
                    results.add(resultData);
                    
                    if (itemResult.getCode() == 200 && resultData != null) {
                        if ("duplicate".equals(resultData.get("reason"))) {
                            duplicateCount.incrementAndGet();
                        } else {
                            successCount.incrementAndGet();
                        }
                    } else {
                        errorCount.incrementAndGet();
                    }
                    
                } catch (Exception e) {
                    log.error("❌ 第{}条数据处理异常: {}", i + 1, e.getMessage());
                    errorCount.incrementAndGet();
                    
                    Map<String, Object> errorResult = new HashMap<>();
                    errorResult.put("success", false);
                    errorResult.put("error", e.getMessage());
                    results.add(errorResult);
                }
            }
            
            // 构建批量处理结果
            Map<String, Object> batchResult = new HashMap<>();
            batchResult.put("success", true);
            batchResult.put("totalCount", batchData.size());
            batchResult.put("successCount", successCount.get());
            batchResult.put("duplicateCount", duplicateCount.get());
            batchResult.put("errorCount", errorCount.get());
            batchResult.put("message", String.format("批量处理完成: 成功%d, 重复%d, 失败%d", 
                    successCount.get(), duplicateCount.get(), errorCount.get()));
            batchResult.put("results", results);
            
            log.info("✅ 批量健康数据处理完成: 成功{}, 重复{}, 失败{}", 
                    successCount.get(), duplicateCount.get(), errorCount.get());
            
            return Result.data(batchResult);
            
        } catch (Exception e) {
            log.error("❌ 批量健康数据处理异常: {}", e.getMessage(), e);
            return Result.failure("批量健康数据处理失败: " + e.getMessage());
        }
    }

    /**
     * 获取用户组织信息
     */
    private Map<String, Object> getUserOrgInfo(String deviceSn) {
        // TODO: 调用用户服务获取设备关联的用户信息
        // 这里需要根据实际的数据模型实现查询逻辑
        log.info("🔍 查找设备对应用户信息: {}", deviceSn);
        
        try {
            // 示例实现，需要根据实际业务调整
            // TODO: 实现根据设备SN获取用户信息的逻辑
            Map<String, Object> userInfo = mockGetUserByDeviceSn(deviceSn);
            if (userInfo != null) {
                Map<String, Object> result = new HashMap<>();
                result.put("userId", userInfo.get("id"));
                result.put("orgId", userInfo.get("orgId"));
                result.put("customerId", userInfo.get("customerId"));
                return result;
            }
        } catch (Exception e) {
            log.error("❌ 获取用户组织信息异常: {}", e.getMessage());
        }
        
        return null;
    }

    /**
     * 检查重复数据
     */
    private boolean isDuplicateData(String deviceSn, Long timestamp) {
        if (timestamp == null) {
            return false;
        }
        
        try {
            LocalDateTime dateTime = Instant.ofEpochMilli(timestamp)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
                    
            // TODO: 查询数据库检查是否存在相同的设备SN和时间戳
            // TODO: 实现重复数据检查逻辑
            return mockCheckDuplicateData(deviceSn, dateTime);
            
        } catch (Exception e) {
            log.warn("⚠️ 重复检查失败，继续处理: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 构建健康数据实体
     */
    private TUserHealthData buildHealthDataEntity(HealthDataUploadRequest request, String deviceSn, Long userId, Long orgId, Long customerId) {
        TUserHealthData healthData = new TUserHealthData();
        
        // 基础信息
        healthData.setDeviceSn(deviceSn);
        healthData.setUserId(userId);
        healthData.setOrgId(orgId);
        healthData.setCustomerId(customerId);
        
        // 健康指标
        healthData.setHeartRate(request.getHeartRate());
        healthData.setBloodOxygen(request.getBloodOxygen());
        healthData.setTemperature(request.getBodyTemperature());
        healthData.setPressureHigh(request.getBloodPressureSystolic());
        healthData.setPressureLow(request.getBloodPressureDiastolic());
        healthData.setStep(request.getStep());
        healthData.setDistance(request.getDistance() != null ? request.getDistance().doubleValue() : null);
        healthData.setCalorie(request.getCalorie() != null ? request.getCalorie().doubleValue() : null);
        healthData.setLatitude(request.getLatitude());
        healthData.setLongitude(request.getLongitude());
        healthData.setStress(request.getStress());
        // 睡眠质量数据已迁移到分表，这里暂时不设置
        // 运动强度数据已迁移到分表，这里暂时不设置
        
        // 时间处理
        if (request.getTimestamp() != null) {
            LocalDateTime dateTime = Instant.ofEpochMilli(request.getTimestamp())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            healthData.setTimestamp(dateTime);
        } else {
            healthData.setTimestamp(LocalDateTime.now());
        }
        
        // 数据来源和版本 - 使用数据库表中支持的枚举值
        String sourceType = request.getSourceType();
        if ("device".equals(sourceType)) {
            healthData.setUploadMethod("common_event"); // 设备上传使用 common_event
        } else if ("wifi".equals(sourceType) || "bluetooth".equals(sourceType)) {
            healthData.setUploadMethod(sourceType);
        } else {
            healthData.setUploadMethod("wifi"); // 默认使用 wifi
        }
        
        // 扩展数据
        if (request.getExtraData() != null && !request.getExtraData().isEmpty()) {
            // TODO: 根据需要处理扩展数据，可以存储为JSON字符串
            // healthData.setExtraData(JSON.toJSONString(request.getExtraData()));
        }
        
        // 审计字段
        healthData.setCreateTime(LocalDateTime.now());
        // isDeleted字段由BaseEntity管理，这里不需要手动设置
        
        return healthData;
    }

    /**
     * 异步处理健康告警检测
     */
    private void processHealthAlerts(TUserHealthData healthData) {
        try {
            // TODO: 异步调用告警服务进行健康指标告警检测
            // 这里可以集成到现有的告警系统或通过消息队列处理
            log.info("🚨 健康告警检测处理: deviceSn={}", healthData.getDeviceSn());
        } catch (Exception e) {
            log.error("❌ 健康告警检测异常: {}", e.getMessage());
            // 告警检测失败不影响主流程
        }
    }

    /**
     * 模拟根据设备SN获取用户信息
     */
    private Map<String, Object> mockGetUserByDeviceSn(String deviceSn) {
        // TODO: 实现真实的用户查询逻辑
        log.info("🔍 模拟查询用户信息: deviceSn={}", deviceSn);
        
        Map<String, Object> userInfo = new HashMap<>();
        userInfo.put("id", 1001L);
        userInfo.put("orgId", 2001L);
        userInfo.put("customerId", 3001L);
        
        return userInfo;
    }

    /**
     * 模拟重复数据检查
     */
    private boolean mockCheckDuplicateData(String deviceSn, LocalDateTime dateTime) {
        // TODO: 实现真实的重复数据检查逻辑
        log.info("🔍 模拟重复数据检查: deviceSn={}, dateTime={}", deviceSn, dateTime);
        return false; // 默认不重复
    }

}