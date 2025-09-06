package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.AlertService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 告警管理API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/alerts")
@RequiredArgsConstructor
@Tag(name = "Alert API", description = "告警管理相关接口")
public class AlertController {

    private final AlertService alertService;

    /**
     * 获取用户告警
     */
    @GetMapping("/user")
    @Operation(summary = "获取用户告警", description = "获取指定用户的告警信息")
    public ApiResponse<List<UserAlertDTO>> getUserAlerts(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId) {
        
        List<UserAlertDTO> result = alertService.getUserAlerts(userId);
        return ApiResponse.success(result);
    }

    /**
     * 获取个人告警
     */
    @GetMapping("/personal")
    @Operation(summary = "获取个人告警", description = "获取基于设备的个人告警信息")
    public ApiResponse<List<PersonalAlertDTO>> getPersonalAlerts(
            @Parameter(description = "设备序列号", required = true) @RequestParam String deviceSn) {
        
        List<PersonalAlertDTO> result = alertService.getPersonalAlerts(deviceSn);
        return ApiResponse.success(result);
    }

    /**
     * 确认告警
     */
    @PostMapping("/acknowledge")
    @Operation(summary = "确认告警", description = "确认指定的告警信息")
    public ApiResponse<AlertAcknowledgeResultDTO> acknowledgeAlert(
            @RequestBody AlertAcknowledgeRequestDTO request) {
        
        AlertAcknowledgeResultDTO result = alertService.acknowledgeAlert(request);
        return ApiResponse.success(result);
    }

    /**
     * 处理告警
     */
    @PostMapping("/deal")
    @Operation(summary = "处理告警", description = "处理指定的告警")
    public ApiResponse<AlertDealResultDTO> dealAlert(
            @Parameter(description = "告警ID", required = true) @RequestParam String alertId) {
        
        AlertDealResultDTO result = alertService.dealAlert(alertId);
        return ApiResponse.success(result);
    }
}