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
import com.ljwx.modules.health.service.HealthAnalyticsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Map;

/**
 * Health Analytics Controller 健康数据分析控制器
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.HealthAnalyticsController
 * @CreateTime 2025-01-15
 */
@Slf4j
@RestController
@Tag(name = "健康数据分析")
@RequiredArgsConstructor
@RequestMapping("health/analytics")
public class HealthAnalyticsController {

    @NonNull
    private HealthAnalyticsService healthAnalyticsService;

    @Operation(summary = "获取健康指标统计信息")
    @GetMapping(value = "/metrics")
    public Result<Map<String, Object>> getHealthMetrics(
            @Parameter(description = "客户ID") @RequestParam("customerId") Long customerId,
            @Parameter(description = "组织ID") @RequestParam(value = "orgId", required = false) String orgId,
            @Parameter(description = "用户ID") @RequestParam(value = "userId", required = false) String userId,
            @Parameter(description = "开始时间戳") @RequestParam("startDate") Long startDate,
            @Parameter(description = "结束时间戳") @RequestParam("endDate") Long endDate,
            @Parameter(description = "时间类型") @RequestParam(value = "timeType", defaultValue = "day") String timeType) {
        
        try {
            // 时间戳转换
            LocalDateTime startDateTime = Instant.ofEpochMilli(startDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            LocalDateTime endDateTime = Instant.ofEpochMilli(endDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();

            Map<String, Object> metrics = healthAnalyticsService.calculateHealthMetrics(
                    customerId, orgId, userId, startDateTime, endDateTime, timeType);

            return Result.data(metrics);
        } catch (Exception e) {
            log.error("❌ 获取健康指标统计失败: customerId={}, userId={}", customerId, userId, e);
            return Result.failure("获取健康指标统计失败: " + e.getMessage());
        }
    }

    @Operation(summary = "获取健康评分")
    @GetMapping(value = "/score")
    public Result<Map<String, Object>> getHealthScore(
            @Parameter(description = "客户ID") @RequestParam("customerId") Long customerId,
            @Parameter(description = "组织ID") @RequestParam(value = "orgId", required = false) String orgId,
            @Parameter(description = "用户ID") @RequestParam(value = "userId", required = false) String userId,
            @Parameter(description = "开始时间戳") @RequestParam("startDate") Long startDate,
            @Parameter(description = "结束时间戳") @RequestParam("endDate") Long endDate) {
        
        try {
            // 时间戳转换
            LocalDateTime startDateTime = Instant.ofEpochMilli(startDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            LocalDateTime endDateTime = Instant.ofEpochMilli(endDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();

            Map<String, Object> score = healthAnalyticsService.calculateHealthScore(
                    customerId, orgId, userId, startDateTime, endDateTime);

            return Result.data(score);
        } catch (Exception e) {
            log.error("❌ 获取健康评分失败: customerId={}, userId={}", customerId, userId, e);
            return Result.failure("获取健康评分失败: " + e.getMessage());
        }
    }

    @Operation(summary = "获取健康建议")
    @GetMapping(value = "/recommendations")
    public Result<Map<String, Object>> getHealthRecommendations(
            @Parameter(description = "客户ID") @RequestParam("customerId") Long customerId,
            @Parameter(description = "组织ID") @RequestParam(value = "orgId", required = false) String orgId,
            @Parameter(description = "用户ID") @RequestParam(value = "userId", required = false) String userId,
            @Parameter(description = "开始时间戳") @RequestParam("startDate") Long startDate,
            @Parameter(description = "结束时间戳") @RequestParam("endDate") Long endDate) {
        
        try {
            // 时间戳转换
            LocalDateTime startDateTime = Instant.ofEpochMilli(startDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            LocalDateTime endDateTime = Instant.ofEpochMilli(endDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();

            Map<String, Object> recommendations = healthAnalyticsService.generateHealthRecommendations(
                    customerId, orgId, userId, startDateTime, endDateTime);

            return Result.data(recommendations);
        } catch (Exception e) {
            log.error("❌ 获取健康建议失败: customerId={}, userId={}", customerId, userId, e);
            return Result.failure("获取健康建议失败: " + e.getMessage());
        }
    }

    @Operation(summary = "获取指标趋势分析")
    @GetMapping(value = "/trends")
    public Result<Map<String, Object>> getHealthTrends(
            @Parameter(description = "客户ID") @RequestParam("customerId") Long customerId,
            @Parameter(description = "组织ID") @RequestParam(value = "orgId", required = false) String orgId,
            @Parameter(description = "用户ID") @RequestParam(value = "userId", required = false) String userId,
            @Parameter(description = "开始时间戳") @RequestParam("startDate") Long startDate,
            @Parameter(description = "结束时间戳") @RequestParam("endDate") Long endDate,
            @Parameter(description = "指标类型") @RequestParam(value = "metricType", required = false) String metricType) {
        
        try {
            // 时间戳转换
            LocalDateTime startDateTime = Instant.ofEpochMilli(startDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            LocalDateTime endDateTime = Instant.ofEpochMilli(endDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();

            Map<String, Object> trends = healthAnalyticsService.analyzeHealthTrends(
                    customerId, orgId, userId, startDateTime, endDateTime, metricType);

            return Result.data(trends);
        } catch (Exception e) {
            log.error("❌ 获取指标趋势分析失败: customerId={}, userId={}", customerId, userId, e);
            return Result.failure("获取指标趋势分析失败: " + e.getMessage());
        }
    }

    @Operation(summary = "获取综合健康分析")
    @GetMapping(value = "/comprehensive")
    public Result<Map<String, Object>> getComprehensiveAnalysis(
            @Parameter(description = "客户ID") @RequestParam("customerId") Long customerId,
            @Parameter(description = "组织ID") @RequestParam(value = "orgId", required = false) String orgId,
            @Parameter(description = "用户ID") @RequestParam(value = "userId", required = false) String userId,
            @Parameter(description = "开始时间戳") @RequestParam("startDate") Long startDate,
            @Parameter(description = "结束时间戳") @RequestParam("endDate") Long endDate,
            @Parameter(description = "时间类型") @RequestParam(value = "timeType", defaultValue = "day") String timeType) {
        
        try {
            // 时间戳转换
            LocalDateTime startDateTime = Instant.ofEpochMilli(startDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            LocalDateTime endDateTime = Instant.ofEpochMilli(endDate)
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();

            Map<String, Object> analysis = healthAnalyticsService.getComprehensiveAnalysis(
                    customerId, orgId, userId, startDateTime, endDateTime, timeType);

            return Result.data(analysis);
        } catch (Exception e) {
            log.error("❌ 获取综合健康分析失败: customerId={}, userId={}", customerId, userId, e);
            return Result.failure("获取综合健康分析失败: " + e.getMessage());
        }
    }
}