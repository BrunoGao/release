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

package com.ljwx.admin.controller.stream;

import cn.dev33.satoken.annotation.SaIgnore;
import com.ljwx.common.api.Result;
import com.ljwx.modules.stream.domain.dto.*;
import com.ljwx.modules.stream.service.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 健康数据流接入API控制器
 * 
 * 提供与ljwx-bigscreen兼容的数据接入接口，包括：
 * - upload_health_data: 健康数据上传
 * - upload_device_info: 设备信息上传
 * - upload_common_event: 通用事件上传
 * - fetch_health_data_config: 健康数据配置获取
 * - DeviceMessage相关接口: 设备消息管理
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataStreamController
 * @CreateTime 2024-12-16
 */
@Slf4j
@RestController
@Tag(name = "健康数据流接入API", description = "兼容ljwx-bigscreen的数据流处理接口")
@RequiredArgsConstructor
public class HealthDataStreamController {

    @NonNull
    private IHealthDataStreamService healthDataStreamService;
    
    @NonNull
    private IDeviceInfoStreamService deviceInfoStreamService;
    
    @NonNull
    private ICommonEventStreamService commonEventStreamService;
    
    @NonNull
    private IHealthDataConfigService healthDataConfigService;
    
    @NonNull
    private IDeviceMessageService deviceMessageService;

    /**
     * 健康数据上传接口 - 兼容ljwx-bigscreen
     * 
     * 支持单条和批量健康数据上传，完全兼容ljwx-bigscreen的数据格式
     */
    @SaIgnore
    @PostMapping("/upload_health_data")
    @Operation(summary = "健康数据上传", description = "兼容ljwx-bigscreen的健康数据上传接口，支持单条和批量上传")
    public Result<Map<String, Object>> uploadHealthData(
            @RequestBody HealthDataUploadRequest request,
            @RequestHeader(value = "X-Device-SN", required = false) String deviceSn,
            @RequestHeader(value = "X-Customer-ID", required = false) String customerId,
            HttpServletRequest httpRequest) {
        
        log.info("🏥 /upload_health_data 接口收到请求");
        log.info("🏥 请求头: {}", httpRequest.getHeaderNames());
        log.info("🏥 请求体大小: {} 字符", request != null ? request.toString().length() : 0);
        
        try {
            // 处理健康数据上传
            return healthDataStreamService.uploadHealthData(request, deviceSn, customerId);
            
        } catch (Exception e) {
            log.error("❌ 健康数据上传失败", e);
            return Result.failure("健康数据上传失败: " + e.getMessage());
        }
    }

    /**
     * 设备信息上传接口 - 兼容ljwx-bigscreen
     * 
     * 支持单个和批量设备信息上传
     */
    @SaIgnore
    @PostMapping("/upload_device_info")
    @Operation(summary = "设备信息上传", description = "兼容ljwx-bigscreen的设备信息上传接口，支持单个和批量上传")
    public Result<Map<String, Object>> uploadDeviceInfo(
            @RequestBody DeviceInfoUploadRequest request,
            HttpServletRequest httpRequest) {
        
        log.info("📱 /upload_device_info 接口收到请求");
        log.info("📱 请求体大小: {} 字符", request != null ? request.toString().length() : 0);
        
        try {
            return deviceInfoStreamService.uploadDeviceInfo(request);
            
        } catch (Exception e) {
            log.error("❌ 设备信息上传失败", e);
            return Result.failure("设备信息上传失败: " + e.getMessage());
        }
    }

    /**
     * 通用事件上传接口 - 兼容ljwx-bigscreen
     * 
     * 用于上传SOS、跌倒检测等通用事件
     */
    @SaIgnore
    @PostMapping("/upload_common_event")
    @Operation(summary = "通用事件上传", description = "兼容ljwx-bigscreen的通用事件上传接口，用于SOS、跌倒检测等事件")
    public Result<Map<String, Object>> uploadCommonEvent(
            @RequestBody CommonEventUploadRequest request,
            HttpServletRequest httpRequest) {
        
        log.info("🚨 /upload_common_event 接口收到请求");
        log.info("🚨 请求体大小: {} 字符", request != null ? request.toString().length() : 0);
        
        try {
            return commonEventStreamService.uploadCommonEvent(request);
            
        } catch (Exception e) {
            log.error("❌ 通用事件上传失败", e);
            return Result.failure("通用事件上传失败: " + e.getMessage());
        }
    }

    /**
     * 健康数据配置获取接口 - 兼容ljwx-bigscreen
     * 
     * 根据customer_id和deviceSn获取健康数据配置
     */
    @SaIgnore
    @GetMapping("/fetch_health_data_config")
    @Operation(summary = "获取健康数据配置", description = "兼容ljwx-bigscreen的健康数据配置获取接口")
    public Result<Map<String, Object>> fetchHealthDataConfig(
            @Parameter(description = "客户ID") @RequestParam(value = "customer_id", required = false) String customerId,
            @Parameter(description = "设备序列号") @RequestParam(value = "deviceSn", required = false) String deviceSn) {
        
        log.info("⚙️  /fetch_health_data_config 接口收到请求");
        log.info("⚙️  参数 - customerId: {}, deviceSn: {}", customerId, deviceSn);
        
        try {
            return healthDataConfigService.fetchHealthDataConfig(customerId, deviceSn);
            
        } catch (Exception e) {
            log.error("❌ 获取健康数据配置失败", e);
            return Result.failure("获取健康数据配置失败: " + e.getMessage());
        }
    }

    /**
     * 设备消息保存接口 - 兼容ljwx-bigscreen DeviceMessage/save_message
     */
    @SaIgnore
    @PostMapping("/DeviceMessage/save_message")
    @Operation(summary = "设备消息保存", description = "保存设备消息到数据库")
    public Result<Map<String, Object>> saveDeviceMessage(
            @RequestBody DeviceMessageSaveRequest request) {
        
        log.info("💬 /DeviceMessage/save_message 接口收到请求");
        
        try {
            return deviceMessageService.saveMessage(request);
            
        } catch (Exception e) {
            log.error("❌ 设备消息保存失败", e);
            return Result.failure("设备消息保存失败: " + e.getMessage());
        }
    }

    /**
     * 设备消息发送接口 - 兼容ljwx-bigscreen DeviceMessage/send
     */
    @SaIgnore
    @PostMapping("/DeviceMessage/send")
    @Operation(summary = "设备消息发送", description = "发送消息到指定设备或用户")
    public Result<Map<String, Object>> sendDeviceMessage(
            @RequestBody DeviceMessageSendRequest request) {
        
        log.info("📤 /DeviceMessage/send 接口收到请求");
        
        try {
            return deviceMessageService.sendMessage(request);
            
        } catch (Exception e) {
            log.error("❌ 设备消息发送失败", e);
            return Result.failure("设备消息发送失败: " + e.getMessage());
        }
    }

    /**
     * 设备消息接收接口 - 兼容ljwx-bigscreen DeviceMessage/receive
     */
    @SaIgnore
    @GetMapping("/DeviceMessage/receive")
    @Operation(summary = "设备消息接收", description = "获取指定设备的消息列表")
    public Result<Map<String, Object>> receiveDeviceMessages(
            @Parameter(description = "设备序列号") @RequestParam("deviceSn") String deviceSn) {
        
        log.info("📥 /DeviceMessage/receive 接口收到请求");
        log.info("📥 参数 - deviceSn: {}", deviceSn);
        
        try {
            return deviceMessageService.receiveMessages(deviceSn);
            
        } catch (Exception e) {
            log.error("❌ 设备消息接收失败", e);
            return Result.failure("设备消息接收失败: " + e.getMessage());
        }
    }
}