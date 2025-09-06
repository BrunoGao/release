package com.ljwx.api.v1.controller;

import com.ljwx.api.v1.dto.*;
import com.ljwx.api.v1.service.HealthService;
import com.ljwx.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 健康数据API控制器 v1
 * 
 * @author LJWX Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/health")
@RequiredArgsConstructor
@Tag(name = "Health API", description = "健康数据相关接口")
public class HealthController {

    private final HealthService healthService;

    /**
     * 获取健康综合评分
     */
    @GetMapping("/scores/comprehensive")
    @Operation(summary = "获取健康综合评分", description = "获取指定用户或组织的健康综合评分")
    public ApiResponse<HealthScoreDTO> getComprehensiveHealthScore(
            @Parameter(description = "用户ID", example = "123") @RequestParam(required = false) String userId,
            @Parameter(description = "组织ID", example = "456") @RequestParam(required = false) String orgId,
            @Parameter(description = "日期", example = "2024-01-01") @RequestParam(required = false) String date) {
        
        HealthScoreQueryDTO query = HealthScoreQueryDTO.builder()
                .userId(userId)
                .orgId(orgId)
                .date(date)
                .build();
        
        HealthScoreDTO result = healthService.getComprehensiveHealthScore(query);
        return ApiResponse.success(result);
    }

    /**
     * 获取实时健康数据
     */
    @GetMapping("/realtime-data")
    @Operation(summary = "获取实时健康数据", description = "获取用户的实时健康监测数据")
    public ApiResponse<RealtimeHealthDataDTO> getRealtimeHealthData(
            @Parameter(description = "用户ID") @RequestParam(required = false) String userId,
            @Parameter(description = "设备序列号") @RequestParam(required = false) String deviceSn) {
        
        RealtimeHealthQueryDTO query = RealtimeHealthQueryDTO.builder()
                .userId(userId)
                .deviceSn(deviceSn)
                .build();
        
        RealtimeHealthDataDTO result = healthService.getRealtimeHealthData(query);
        return ApiResponse.success(result);
    }

    /**
     * 获取健康趋势数据
     */
    @GetMapping("/trends")
    @Operation(summary = "获取健康趋势数据", description = "获取用户健康数据的历史趋势")
    public ApiResponse<List<HealthTrendDTO>> getHealthTrends(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId,
            @Parameter(description = "开始日期") @RequestParam(required = false) String startDate,
            @Parameter(description = "结束日期") @RequestParam(required = false) String endDate) {
        
        HealthTrendQueryDTO query = HealthTrendQueryDTO.builder()
                .userId(userId)
                .startDate(startDate)
                .endDate(endDate)
                .build();
        
        List<HealthTrendDTO> result = healthService.getHealthTrends(query);
        return ApiResponse.success(result);
    }

    /**
     * 获取基线数据图表
     */
    @GetMapping("/baseline/chart")
    @Operation(summary = "获取基线数据图表", description = "获取基线健康数据的图表数据")
    public ApiResponse<BaselineChartDTO> getBaselineChart(
            @Parameter(description = "组织ID", required = true) @RequestParam String orgId,
            @Parameter(description = "开始日期", required = true) @RequestParam String startDate,
            @Parameter(description = "结束日期", required = true) @RequestParam String endDate) {
        
        BaselineChartQueryDTO query = BaselineChartQueryDTO.builder()
                .orgId(orgId)
                .startDate(startDate)
                .endDate(endDate)
                .build();
        
        BaselineChartDTO result = healthService.getBaselineChart(query);
        return ApiResponse.success(result);
    }

    /**
     * 生成基线数据
     */
    @PostMapping("/baseline/generate")
    @Operation(summary = "生成基线数据", description = "生成健康基线数据")
    public ApiResponse<BaselineGenerateResultDTO> generateBaseline(
            @RequestBody BaselineGenerateRequestDTO request) {
        
        BaselineGenerateResultDTO result = healthService.generateBaseline(request);
        return ApiResponse.success(result);
    }

    /**
     * 根据ID获取健康数据
     */
    @GetMapping("/data/{id}")
    @Operation(summary = "根据ID获取健康数据", description = "根据ID获取具体的健康数据详情")
    public ApiResponse<HealthDataDetailDTO> getHealthDataById(
            @Parameter(description = "健康数据ID", required = true) @PathVariable String id) {
        
        HealthDataDetailDTO result = healthService.getHealthDataById(id);
        return ApiResponse.success(result);
    }

    /**
     * 获取个人健康评分
     */
    @GetMapping("/personal/scores")
    @Operation(summary = "获取个人健康评分", description = "获取个人的健康评分详情")
    public ApiResponse<PersonalHealthScoreDTO> getPersonalHealthScores(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId,
            @Parameter(description = "日期") @RequestParam(required = false) String date) {
        
        PersonalHealthScoreQueryDTO query = PersonalHealthScoreQueryDTO.builder()
                .userId(userId)
                .date(date)
                .build();
        
        PersonalHealthScoreDTO result = healthService.getPersonalHealthScores(query);
        return ApiResponse.success(result);
    }

    /**
     * 获取健康建议
     */
    @GetMapping("/recommendations")
    @Operation(summary = "获取健康建议", description = "基于健康数据获取个性化健康建议")
    public ApiResponse<List<HealthRecommendationDTO>> getHealthRecommendations(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId) {
        
        List<HealthRecommendationDTO> result = healthService.getHealthRecommendations(userId);
        return ApiResponse.success(result);
    }

    /**
     * 获取健康预测
     */
    @GetMapping("/predictions")
    @Operation(summary = "获取健康预测", description = "基于历史数据预测健康趋势")
    public ApiResponse<List<HealthPredictionDTO>> getHealthPredictions(
            @Parameter(description = "用户ID", required = true) @RequestParam String userId) {
        
        List<HealthPredictionDTO> result = healthService.getHealthPredictions(userId);
        return ApiResponse.success(result);
    }
}