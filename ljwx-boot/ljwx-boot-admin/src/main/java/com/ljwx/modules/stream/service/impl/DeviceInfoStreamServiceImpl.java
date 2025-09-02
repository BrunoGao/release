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
import com.ljwx.modules.stream.domain.dto.DeviceInfoUploadRequest;
import com.ljwx.modules.stream.service.IDeviceInfoStreamService;
// import com.ljwx.modules.device.service.IDeviceInfoService;

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
 * 设备信息流处理服务实现
 * 
 * 兼容ljwx-bigscreen的设备信息上传接口，支持设备注册、状态更新等功能
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DeviceInfoStreamServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeviceInfoStreamServiceImpl implements IDeviceInfoStreamService {

    // private final IDeviceInfoService deviceInfoService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> uploadDeviceInfo(DeviceInfoUploadRequest request) {
        
        log.info("📱 设备信息上传开始: {}", request.getDeviceSn());
        log.info("📱 请求数据: {}", request);
        
        try {
            // 处理单个和批量设备
            if (request.getBatchDevices() != null && !request.getBatchDevices().isEmpty()) {
                return processBatchDeviceInfo(request.getBatchDevices());
            } else {
                return processSingleDeviceInfo(request);
            }
            
        } catch (Exception e) {
            log.error("❌ 设备信息上传处理失败: {}", e.getMessage(), e);
            return Result.failure("设备信息上传处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理单个设备信息
     */
    private Result<Map<String, Object>> processSingleDeviceInfo(DeviceInfoUploadRequest request) {
        
        log.info("🔍 处理单个设备信息: deviceSn={}", request.getDeviceSn());
        
        try {
            if (!StringUtils.hasText(request.getDeviceSn())) {
                log.warn("⚠️ 设备SN为空，无法处理");
                return Result.failure("设备SN不能为空");
            }
            
            // 检查设备是否存在
            boolean deviceExists = checkDeviceExists(request.getDeviceSn());
            
            Map<String, Object> result = new HashMap<>();
            
            if (deviceExists) {
                // 更新设备信息
                boolean updated = updateDeviceInfo(request);
                if (updated) {
                    log.info("✅ 设备信息更新成功: {}", request.getDeviceSn());
                    result.put("success", true);
                    result.put("action", "updated");
                    result.put("message", "设备信息更新成功");
                } else {
                    log.error("❌ 设备信息更新失败: {}", request.getDeviceSn());
                    return Result.failure("设备信息更新失败");
                }
            } else {
                // 注册新设备
                boolean registered = registerNewDevice(request);
                if (registered) {
                    log.info("✅ 设备注册成功: {}", request.getDeviceSn());
                    result.put("success", true);
                    result.put("action", "registered");
                    result.put("message", "设备注册成功");
                } else {
                    log.error("❌ 设备注册失败: {}", request.getDeviceSn());
                    return Result.failure("设备注册失败");
                }
            }
            
            result.put("deviceSn", request.getDeviceSn());
            result.put("processedCount", 1);
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("❌ 单个设备信息处理异常: {}", e.getMessage(), e);
            return Result.failure("单个设备信息处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理批量设备信息
     */
    private Result<Map<String, Object>> processBatchDeviceInfo(List<DeviceInfoUploadRequest> batchDevices) {
        
        log.info("🔍 处理批量设备信息，数量: {}", batchDevices.size());
        
        int successCount = 0;
        int errorCount = 0;
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            for (int i = 0; i < batchDevices.size(); i++) {
                DeviceInfoUploadRequest device = batchDevices.get(i);
                log.info("🔍 处理第{}个设备: {}", i + 1, device.getDeviceSn());
                
                try {
                    Result<Map<String, Object>> deviceResult = processSingleDeviceInfo(device);
                    results.add(deviceResult.getData());
                    
                    if (deviceResult.getCode() == 200) {
                        successCount++;
                    } else {
                        errorCount++;
                    }
                    
                } catch (Exception e) {
                    log.error("❌ 第{}个设备处理异常: {}", i + 1, e.getMessage());
                    errorCount++;
                    
                    Map<String, Object> errorResult = new HashMap<>();
                    errorResult.put("success", false);
                    errorResult.put("deviceSn", device.getDeviceSn());
                    errorResult.put("error", e.getMessage());
                    results.add(errorResult);
                }
            }
            
            // 构建批量处理结果
            Map<String, Object> batchResult = new HashMap<>();
            batchResult.put("success", true);
            batchResult.put("totalCount", batchDevices.size());
            batchResult.put("successCount", successCount);
            batchResult.put("errorCount", errorCount);
            batchResult.put("message", String.format("批量设备处理完成: 成功%d, 失败%d", successCount, errorCount));
            batchResult.put("results", results);
            
            log.info("✅ 批量设备信息处理完成: 成功{}, 失败{}", successCount, errorCount);
            
            return Result.data(batchResult);
            
        } catch (Exception e) {
            log.error("❌ 批量设备信息处理异常: {}", e.getMessage(), e);
            return Result.failure("批量设备信息处理失败: " + e.getMessage());
        }
    }

    /**
     * 注册新设备
     */
    private boolean registerNewDevice(DeviceInfoUploadRequest request) {
        try {
            // TODO: 根据实际的设备实体模型实现
            Map<String, Object> deviceData = new HashMap<>();
            deviceData.put("deviceSn", request.getDeviceSn());
            deviceData.put("deviceName", request.getDeviceName());
            deviceData.put("deviceType", request.getDeviceType());
            deviceData.put("deviceModel", request.getDeviceModel());
            deviceData.put("manufacturer", request.getManufacturer());
            deviceData.put("firmwareVersion", request.getFirmwareVersion());
            deviceData.put("hardwareVersion", request.getHardwareVersion());
            deviceData.put("deviceStatus", request.getDeviceStatus() != null ? request.getDeviceStatus() : "online");
            deviceData.put("batteryLevel", request.getBatteryLevel());
            deviceData.put("signalStrength", request.getSignalStrength());
            
            if (request.getLastCommunicationTime() != null) {
                LocalDateTime commTime = Instant.ofEpochMilli(request.getLastCommunicationTime())
                        .atZone(ZoneId.systemDefault())
                        .toLocalDateTime();
                deviceData.put("lastCommunicationTime", commTime);
            }
            
            if (request.getRegistrationTime() != null) {
                LocalDateTime regTime = Instant.ofEpochMilli(request.getRegistrationTime())
                        .atZone(ZoneId.systemDefault())
                        .toLocalDateTime();
                deviceData.put("registrationTime", regTime);
            } else {
                deviceData.put("registrationTime", LocalDateTime.now());
            }
            
            deviceData.put("location", request.getLocation());
            deviceData.put("userId", request.getUserId());
            deviceData.put("customerId", request.getCustomerId());
            deviceData.put("orgId", request.getOrgId());
            
            // 扩展属性和配置
            if (request.getDeviceConfig() != null) {
                // TODO: 序列化为JSON存储
            }
            
            // TODO: 实现设备注册逻辑
            log.info("📱 模拟设备注册: {}", request.getDeviceSn());
            return true;
            
        } catch (Exception e) {
            log.error("❌ 设备注册异常: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 更新设备信息
     */
    private boolean updateDeviceInfo(DeviceInfoUploadRequest request) {
        try {
            Map<String, Object> updateData = new HashMap<>();
            
            // 只更新非空字段
            if (StringUtils.hasText(request.getDeviceName())) {
                updateData.put("deviceName", request.getDeviceName());
            }
            if (StringUtils.hasText(request.getDeviceStatus())) {
                updateData.put("deviceStatus", request.getDeviceStatus());
            }
            if (request.getBatteryLevel() != null) {
                updateData.put("batteryLevel", request.getBatteryLevel());
            }
            if (request.getSignalStrength() != null) {
                updateData.put("signalStrength", request.getSignalStrength());
            }
            if (request.getLastCommunicationTime() != null) {
                LocalDateTime commTime = Instant.ofEpochMilli(request.getLastCommunicationTime())
                        .atZone(ZoneId.systemDefault())
                        .toLocalDateTime();
                updateData.put("lastCommunicationTime", commTime);
            }
            if (StringUtils.hasText(request.getFirmwareVersion())) {
                updateData.put("firmwareVersion", request.getFirmwareVersion());
            }
            if (StringUtils.hasText(request.getLocation())) {
                updateData.put("location", request.getLocation());
            }
            
            updateData.put("updateTime", LocalDateTime.now());
            
            // TODO: 实现设备更新逻辑
            log.info("📱 模拟设备更新: {}", request.getDeviceSn());
            return true;
            
        } catch (Exception e) {
            log.error("❌ 设备更新异常: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 检查设备是否存在
     */
    private boolean checkDeviceExists(String deviceSn) {
        try {
            // TODO: 查询数据库检查设备是否存在
            log.info("🔍 检查设备是否存在: {}", deviceSn);
            return false; // 默认假设设备不存在，需要注册
        } catch (Exception e) {
            log.error("❌ 检查设备存在性异常: {}", e.getMessage());
            return false;
        }
    }

}