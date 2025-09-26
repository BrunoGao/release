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

package com.ljwx.admin.controller.geofence;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.geofence.domain.dto.alert.GeofenceAlertProcessDTO;
import com.ljwx.modules.geofence.domain.dto.alert.GeofenceAlertQueryDTO;
import com.ljwx.modules.geofence.domain.vo.GeofenceAlertVO;
import com.ljwx.modules.geofence.service.GeofenceAlertService;
import com.ljwx.modules.geofence.service.GeofenceCalculatorService;
import com.ljwx.modules.health.domain.vo.track.TrackPointVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 围栏告警 Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.geofence.GeofenceAlertController
 * @CreateTime 2025-01-27 - 14:30:00
 */

@Slf4j
@RestController
@Tag(name = "围栏告警管理", description = "围栏告警查询、处理和统计功能")
@RequiredArgsConstructor
@RequestMapping("/geofence/alert")
public class GeofenceAlertController {

    @NonNull
    private GeofenceAlertService geofenceAlertService;
    
    @NonNull
    private GeofenceCalculatorService geofenceCalculatorService;

    @GetMapping("/page")
    @SaCheckPermission("geofence:alert:page")
    @Operation(operationId = "1", summary = "分页查询围栏告警")
    public Result<RPage<GeofenceAlertVO>> queryAlertsPage(
            @Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
            @Parameter(description = "查询条件") GeofenceAlertQueryDTO queryDTO) {
        try {
            RPage<GeofenceAlertVO> result = geofenceAlertService.queryAlertsPage(pageQuery, queryDTO);
            log.info("📋 围栏告警分页查询成功: 页数{}, 总数{}", pageQuery.getPage(), result.getTotal());
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ 围栏告警分页查询失败: {}", e.getMessage(), e);
            return Result.failure("告警查询失败: " + e.getMessage());
        }
    }

    @GetMapping("/{alertId}")
    @SaCheckPermission("geofence:alert:detail")
    @Operation(operationId = "2", summary = "获取告警详情")
    public Result<GeofenceAlertVO> getAlertDetail(
            @Parameter(description = "告警ID", required = true) @PathVariable String alertId) {
        try {
            GeofenceAlertVO alert = geofenceAlertService.getAlertDetail(alertId);
            log.info("📋 围栏告警详情查询成功: 告警ID{}", alertId);
            return Result.data(alert);
        } catch (Exception e) {
            log.error("❌ 围栏告警详情查询失败: {}", e.getMessage(), e);
            return Result.failure("告警详情查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/process")
    @SaCheckPermission("geofence:alert:process")
    @Operation(operationId = "3", summary = "处理围栏告警")
    public Result<Boolean> processAlert(
            @Parameter(description = "告警处理对象", required = true) 
            @Valid @RequestBody GeofenceAlertProcessDTO processDTO) {
        try {
            Boolean result = geofenceAlertService.processAlert(processDTO);
            log.info("✅ 围栏告警处理成功: 告警ID{}, 处理状态{}", 
                    processDTO.getAlertId(), processDTO.getNewStatus());
            return Result.status(result);
        } catch (Exception e) {
            log.error("❌ 围栏告警处理失败: {}", e.getMessage(), e);
            return Result.failure("告警处理失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch-process")
    @SaCheckPermission("geofence:alert:batch-process")
    @Operation(operationId = "4", summary = "批量处理围栏告警")
    public Result<Map<String, Boolean>> batchProcessAlerts(
            @Parameter(description = "批量告警处理对象", required = true) 
            @Valid @RequestBody List<GeofenceAlertProcessDTO> processList) {
        try {
            Map<String, Boolean> result = geofenceAlertService.batchProcessAlerts(processList);
            log.info("✅ 围栏告警批量处理完成: 总数{}, 成功{}", 
                    processList.size(), result.values().stream().mapToLong(v -> v ? 1 : 0).sum());
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ 围栏告警批量处理失败: {}", e.getMessage(), e);
            return Result.failure("批量处理失败: " + e.getMessage());
        }
    }

    @GetMapping("/stats")
    @SaCheckPermission("geofence:alert:stats")
    @Operation(operationId = "5", summary = "获取告警统计")
    public Result<Map<String, Object>> getAlertStats(
            @Parameter(description = "查询条件") GeofenceAlertQueryDTO queryDTO) {
        try {
            Map<String, Object> stats = geofenceAlertService.getAlertStats(queryDTO);
            log.info("📊 围栏告警统计查询成功");
            return Result.data(stats);
        } catch (Exception e) {
            log.error("❌ 围栏告警统计查询失败: {}", e.getMessage(), e);
            return Result.failure("告警统计查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/check-events")
    @SaCheckPermission("geofence:alert:check")
    @Operation(operationId = "6", summary = "检测轨迹点的围栏事件")
    public Result<List<GeofenceCalculatorService.GeofenceEvent>> checkGeofenceEvents(
            @Parameter(description = "轨迹点", required = true) 
            @Valid @RequestBody TrackPointVO trackPoint) {
        try {
            List<GeofenceCalculatorService.GeofenceEvent> events = 
                    geofenceCalculatorService.calculateGeofenceEvents(trackPoint);
            log.info("🔍 围栏事件检测完成: 用户{}, 事件数{}", trackPoint.getUserId(), events.size());
            return Result.data(events);
        } catch (Exception e) {
            log.error("❌ 围栏事件检测失败: {}", e.getMessage(), e);
            return Result.failure("围栏事件检测失败: " + e.getMessage());
        }
    }

    @PostMapping("/batch-check-events")
    @SaCheckPermission("geofence:alert:batch-check")
    @Operation(operationId = "7", summary = "批量检测多用户轨迹点的围栏事件")
    public Result<Map<Long, List<GeofenceCalculatorService.GeofenceEvent>>> batchCheckGeofenceEvents(
            @Parameter(description = "多用户轨迹点列表", required = true) 
            @Valid @RequestBody List<TrackPointVO> trackPoints) {
        try {
            Map<Long, List<GeofenceCalculatorService.GeofenceEvent>> result = 
                    geofenceCalculatorService.batchCalculateGeofenceEvents(trackPoints);
            log.info("🔍 批量围栏事件检测完成: 轨迹点{}, 用户事件{}", 
                    trackPoints.size(), result.size());
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ 批量围栏事件检测失败: {}", e.getMessage(), e);
            return Result.failure("批量围栏事件检测失败: " + e.getMessage());
        }
    }

    @GetMapping("/recent")
    @SaCheckPermission("geofence:alert:recent")
    @Operation(operationId = "8", summary = "获取最近告警")
    public Result<List<GeofenceAlertVO>> getRecentAlerts(
            @Parameter(description = "最大数量") @RequestParam(defaultValue = "10") Integer limit,
            @Parameter(description = "用户ID") @RequestParam(required = false) Long userId) {
        try {
            GeofenceAlertQueryDTO queryDTO = new GeofenceAlertQueryDTO();
            queryDTO.setUserId(userId);
            queryDTO.setLimit(limit);
            
            List<GeofenceAlertVO> alerts = geofenceAlertService.getRecentAlerts(queryDTO);
            log.info("📋 最近告警查询成功: 数量{}", alerts.size());
            return Result.data(alerts);
        } catch (Exception e) {
            log.error("❌ 最近告警查询失败: {}", e.getMessage(), e);
            return Result.failure("最近告警查询失败: " + e.getMessage());
        }
    }

    @PostMapping("/initialize-geo-index")
    @SaCheckPermission("geofence:admin:index")
    @Operation(operationId = "9", summary = "初始化围栏地理索引")
    public Result<String> initializeGeoIndex() {
        try {
            geofenceCalculatorService.initializeGeofenceGeoIndex();
            log.info("🚀 围栏地理索引初始化成功");
            return Result.success("围栏地理索引初始化成功");
        } catch (Exception e) {
            log.error("❌ 围栏地理索引初始化失败: {}", e.getMessage(), e);
            return Result.failure("索引初始化失败: " + e.getMessage());
        }
    }
}