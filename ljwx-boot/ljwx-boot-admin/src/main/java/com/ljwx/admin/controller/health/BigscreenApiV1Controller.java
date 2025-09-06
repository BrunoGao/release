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

package com.ljwx.admin.controller.health;

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.facade.IBigscreenHealthFacade;
import com.ljwx.modules.health.facade.IBigscreenDeviceFacade;
import com.ljwx.modules.health.facade.IBigscreenAlertFacade;
import com.ljwx.modules.health.facade.IBigscreenStatisticsFacade;
import com.ljwx.modules.health.domain.dto.v1.health.*;
import com.ljwx.modules.health.domain.dto.v1.device.*;
import com.ljwx.modules.health.domain.dto.v1.alert.*;
import com.ljwx.modules.health.domain.vo.v1.health.*;
import com.ljwx.modules.health.domain.vo.v1.device.*;
import com.ljwx.modules.health.domain.vo.v1.alert.*;
import com.ljwx.modules.health.domain.vo.v1.statistics.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Bigscreen V1 API Controller - 专门为大屏应用提供的规范化API接口
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.BigscreenApiV1Controller
 * @CreateTime 2025-01-01 - 10:00:00
 */

@RestController
@Tag(name = "Bigscreen V1 API", description = "大屏应用v1规范化API接口")
@RequiredArgsConstructor
@RequestMapping("/api/v1")
public class BigscreenApiV1Controller {

    @NonNull
    private IBigscreenHealthFacade bigscreenHealthFacade;
    
    @NonNull
    private IBigscreenDeviceFacade bigscreenDeviceFacade;
    
    @NonNull
    private IBigscreenAlertFacade bigscreenAlertFacade;
    
    @NonNull
    private IBigscreenStatisticsFacade bigscreenStatisticsFacade;

    // ==================== 健康数据相关API ====================

    @GetMapping("/health/scores/comprehensive")
    @Operation(operationId = "1", summary = "获取健康综合评分")
    public Result<HealthScoreVO> getComprehensiveHealthScore(
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId,
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId,
            @Parameter(description = "日期", required = false) @RequestParam(required = false) String date) {
        
        HealthScoreQueryDTO query = HealthScoreQueryDTO.builder()
                .userId(userId)
                .orgId(orgId)
                .date(date)
                .build();
        
        return Result.data(bigscreenHealthFacade.getComprehensiveHealthScore(query));
    }

    @GetMapping("/health/baseline/chart")
    @Operation(operationId = "2", summary = "获取基线数据图表")
    public Result<BaselineChartVO> getBaselineChart(
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId,
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId) {
        
        BaselineChartQueryDTO query = BaselineChartQueryDTO.builder()
                .userId(userId)
                .orgId(orgId)
                .build();
                
        return Result.data(bigscreenHealthFacade.getBaselineChart(query));
    }

    @PostMapping("/health/baseline/generate")
    @Operation(operationId = "3", summary = "生成基线数据")
    public Result<BaselineGenerateResultVO> generateBaseline(
            @Parameter(description = "基线生成请求") @RequestBody @Valid BaselineGenerateRequestDTO request) {
        
        return Result.data(bigscreenHealthFacade.generateBaseline(request));
    }

    @GetMapping("/health/data/{id}")
    @Operation(operationId = "4", summary = "根据ID获取健康数据")
    public Result<HealthDataDetailVO> getHealthDataById(
            @Parameter(description = "健康数据ID") @PathVariable("id") String id) {
        
        return Result.data(bigscreenHealthFacade.getHealthDataById(id));
    }

    @GetMapping("/health/realtime-data")
    @Operation(operationId = "5", summary = "获取实时健康数据")
    public Result<RealtimeHealthDataVO> getRealtimeHealthData(
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId,
            @Parameter(description = "设备序列号", required = false) @RequestParam(required = false) String deviceSn) {
        
        RealtimeHealthQueryDTO query = RealtimeHealthQueryDTO.builder()
                .userId(userId)
                .deviceSn(deviceSn)
                .build();
                
        return Result.data(bigscreenHealthFacade.getRealtimeHealthData(query));
    }

    @GetMapping("/health/trends")
    @Operation(operationId = "6", summary = "获取健康趋势数据")
    public Result<List<HealthTrendVO>> getHealthTrends(
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId,
            @Parameter(description = "开始日期", required = false) @RequestParam(required = false) String startDate,
            @Parameter(description = "结束日期", required = false) @RequestParam(required = false) String endDate) {
        
        HealthTrendQueryDTO query = HealthTrendQueryDTO.builder()
                .userId(userId)
                .startDate(startDate)
                .endDate(endDate)
                .build();
                
        return Result.data(bigscreenHealthFacade.getHealthTrends(query));
    }

    @GetMapping("/health/personal/scores")
    @Operation(operationId = "7", summary = "获取个人健康评分")
    public Result<PersonalHealthScoreVO> getPersonalHealthScores(
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId,
            @Parameter(description = "设备序列号", required = false) @RequestParam(required = false) String deviceSn) {
        
        PersonalHealthScoreQueryDTO query = PersonalHealthScoreQueryDTO.builder()
                .userId(userId)
                .deviceSn(deviceSn)
                .build();
                
        return Result.data(bigscreenHealthFacade.getPersonalHealthScores(query));
    }

    @GetMapping("/health/recommendations")
    @Operation(operationId = "8", summary = "获取健康建议")
    public Result<List<HealthRecommendationVO>> getHealthRecommendations(
            @Parameter(description = "用户ID") @RequestParam String userId) {
        
        return Result.data(bigscreenHealthFacade.getHealthRecommendations(userId));
    }

    @GetMapping("/health/predictions")
    @Operation(operationId = "9", summary = "获取健康预测")
    public Result<List<HealthPredictionVO>> getHealthPredictions(
            @Parameter(description = "用户ID") @RequestParam String userId) {
        
        return Result.data(bigscreenHealthFacade.getHealthPredictions(userId));
    }

    // ==================== 设备管理相关API ====================

    @GetMapping("/devices/user-info")
    @Operation(operationId = "10", summary = "获取设备用户信息")
    public Result<DeviceUserInfoVO> getDeviceUserInfo(
            @Parameter(description = "设备序列号") @RequestParam String deviceSn) {
        
        return Result.data(bigscreenDeviceFacade.getDeviceUserInfo(deviceSn));
    }

    @GetMapping("/devices/status")
    @Operation(operationId = "11", summary = "获取设备状态信息")
    public Result<DeviceStatusVO> getDeviceStatus(
            @Parameter(description = "设备序列号") @RequestParam String deviceSn) {
        
        return Result.data(bigscreenDeviceFacade.getDeviceStatus(deviceSn));
    }

    @GetMapping("/devices/user-organization")
    @Operation(operationId = "12", summary = "获取设备用户组织信息")
    public Result<DeviceUserOrganizationVO> getDeviceUserOrganization(
            @Parameter(description = "设备序列号") @RequestParam String deviceSn) {
        
        return Result.data(bigscreenDeviceFacade.getDeviceUserOrganization(deviceSn));
    }

    // ==================== 用户管理相关API ====================

    @GetMapping("/users/profile")
    @Operation(operationId = "13", summary = "获取用户资料")
    public Result<UserProfileVO> getUserProfile(
            @Parameter(description = "用户ID") @RequestParam String userId) {
        
        return Result.data(bigscreenDeviceFacade.getUserProfile(userId));
    }

    @GetMapping("/users")
    @Operation(operationId = "14", summary = "获取用户列表")
    public Result<List<UserVO>> getUsers(
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId,
            @Parameter(description = "页码", required = false) @RequestParam(required = false, defaultValue = "1") Integer page,
            @Parameter(description = "页大小", required = false) @RequestParam(required = false, defaultValue = "20") Integer size) {
        
        UserQueryDTO query = UserQueryDTO.builder()
                .orgId(orgId)
                .page(page)
                .size(size)
                .build();
                
        return Result.data(bigscreenDeviceFacade.getUsers(query));
    }

    // ==================== 组织管理相关API ====================

    @GetMapping("/organizations/statistics")
    @Operation(operationId = "15", summary = "获取组织统计信息")
    public Result<OrganizationStatisticsVO> getOrganizationStatistics(
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId) {
        
        return Result.data(bigscreenStatisticsFacade.getOrganizationStatistics(orgId));
    }

    @GetMapping("/departments")
    @Operation(operationId = "16", summary = "获取部门列表")
    public Result<List<DepartmentVO>> getDepartments(
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId) {
        
        return Result.data(bigscreenStatisticsFacade.getDepartments(orgId));
    }

    // ==================== 统计分析相关API ====================

    @GetMapping("/statistics/overview")
    @Operation(operationId = "17", summary = "获取统计概览")
    public Result<StatisticsOverviewVO> getStatisticsOverview(
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId) {
        
        return Result.data(bigscreenStatisticsFacade.getStatisticsOverview(orgId));
    }

    @GetMapping("/statistics/realtime")
    @Operation(operationId = "18", summary = "获取实时统计数据")
    public Result<RealtimeStatisticsVO> getRealtimeStatistics(
            @Parameter(description = "组织ID", required = false) @RequestParam(required = false) String orgId) {
        
        return Result.data(bigscreenStatisticsFacade.getRealtimeStatistics(orgId));
    }

    // ==================== 告警管理相关API ====================

    @GetMapping("/alerts/user")
    @Operation(operationId = "19", summary = "获取用户告警")
    public Result<List<UserAlertVO>> getUserAlerts(
            @Parameter(description = "用户ID") @RequestParam String userId,
            @Parameter(description = "状态", required = false) @RequestParam(required = false) String status) {
        
        UserAlertQueryDTO query = UserAlertQueryDTO.builder()
                .userId(userId)
                .status(status)
                .build();
                
        return Result.data(bigscreenAlertFacade.getUserAlerts(query));
    }

    @GetMapping("/alerts/personal")
    @Operation(operationId = "20", summary = "获取个人告警")
    public Result<List<PersonalAlertVO>> getPersonalAlerts(
            @Parameter(description = "设备序列号", required = false) @RequestParam(required = false) String deviceSn,
            @Parameter(description = "用户ID", required = false) @RequestParam(required = false) String userId) {
        
        PersonalAlertQueryDTO query = PersonalAlertQueryDTO.builder()
                .deviceSn(deviceSn)
                .userId(userId)
                .build();
                
        return Result.data(bigscreenAlertFacade.getPersonalAlerts(query));
    }

    @PostMapping("/alerts/acknowledge")
    @Operation(operationId = "21", summary = "确认告警")
    public Result<Boolean> acknowledgeAlert(
            @Parameter(description = "告警确认请求") @RequestBody @Valid AlertAcknowledgeRequestDTO request) {
        
        return Result.status(bigscreenAlertFacade.acknowledgeAlert(request));
    }

    @PostMapping("/alerts/deal")
    @Operation(operationId = "22", summary = "处理告警")
    public Result<Boolean> dealAlert(
            @Parameter(description = "告警ID") @RequestParam Long alertId) {
        
        return Result.status(bigscreenAlertFacade.dealAlert(alertId));
    }

    // ==================== 消息管理相关API ====================

    @GetMapping("/messages/user")
    @Operation(operationId = "23", summary = "获取用户消息")
    public Result<List<UserMessageVO>> getUserMessages(
            @Parameter(description = "用户ID") @RequestParam String userId,
            @Parameter(description = "消息类型", required = false) @RequestParam(required = false) String messageType) {
        
        UserMessageQueryDTO query = UserMessageQueryDTO.builder()
                .userId(userId)
                .messageType(messageType)
                .build();
                
        return Result.data(bigscreenAlertFacade.getUserMessages(query));
    }
}