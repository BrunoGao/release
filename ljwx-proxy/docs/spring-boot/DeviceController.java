package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.DeviceService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 设备管理API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/devices")
@RequiredArgsConstructor
@Tag(name = "Device API", description = "设备管理相关接口")
public class DeviceController {

    private final DeviceService deviceService;

    /**
     * 获取设备用户信息
     */
    @GetMapping("/user-info")
    @Operation(summary = "获取设备用户信息", description = "根据设备序列号获取绑定的用户信息")
    public ApiResponse<DeviceUserInfoDTO> getDeviceUserInfo(
            @Parameter(description = "设备序列号", required = true, example = "CRFTQ23409001890") 
            @RequestParam String deviceSn) {
        
        DeviceUserInfoDTO result = deviceService.getDeviceUserInfo(deviceSn);
        return ApiResponse.success(result);
    }

    /**
     * 获取设备状态信息
     */
    @GetMapping("/status")
    @Operation(summary = "获取设备状态信息", description = "获取设备的运行状态和基本信息")
    public ApiResponse<DeviceStatusDTO> getDeviceStatus(
            @Parameter(description = "设备序列号", required = true) 
            @RequestParam String deviceSn) {
        
        DeviceStatusDTO result = deviceService.getDeviceStatus(deviceSn);
        return ApiResponse.success(result);
    }

    /**
     * 获取设备用户组织信息
     */
    @GetMapping("/user-organization")
    @Operation(summary = "获取设备用户组织信息", description = "获取设备用户所属的组织信息")
    public ApiResponse<DeviceUserOrganizationDTO> getDeviceUserOrganization(
            @Parameter(description = "设备序列号", required = true) 
            @RequestParam String deviceSn) {
        
        DeviceUserOrganizationDTO result = deviceService.getDeviceUserOrganization(deviceSn);
        return ApiResponse.success(result);
    }
}