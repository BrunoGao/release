package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.StatisticsService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 统计分析API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/statistics")
@RequiredArgsConstructor
@Tag(name = "Statistics API", description = "统计分析相关接口")
public class StatisticsController {

    private final StatisticsService statisticsService;

    /**
     * 获取统计概览
     */
    @GetMapping("/overview")
    @Operation(summary = "获取统计概览", description = "获取统计数据概览")
    public ApiResponse<StatisticsOverviewDTO> getStatisticsOverview(
            @Parameter(description = "组织ID", required = true) @RequestParam String orgId,
            @Parameter(description = "日期") @RequestParam(required = false) String date) {
        
        StatisticsOverviewQueryDTO query = StatisticsOverviewQueryDTO.builder()
                .orgId(orgId)
                .date(date)
                .build();
        
        StatisticsOverviewDTO result = statisticsService.getStatisticsOverview(query);
        return ApiResponse.success(result);
    }

    /**
     * 获取实时统计数据
     */
    @GetMapping("/realtime")
    @Operation(summary = "获取实时统计数据", description = "获取实时统计数据")
    public ApiResponse<RealtimeStatisticsDTO> getRealtimeStatistics(
            @Parameter(description = "客户ID", required = true) @RequestParam String customerId,
            @Parameter(description = "日期") @RequestParam(required = false) String date) {
        
        RealtimeStatisticsQueryDTO query = RealtimeStatisticsQueryDTO.builder()
                .customerId(customerId)
                .date(date)
                .build();
        
        RealtimeStatisticsDTO result = statisticsService.getRealtimeStatistics(query);
        return ApiResponse.success(result);
    }
}