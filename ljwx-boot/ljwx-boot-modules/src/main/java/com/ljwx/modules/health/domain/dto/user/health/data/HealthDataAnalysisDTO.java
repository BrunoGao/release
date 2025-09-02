package com.ljwx.modules.health.domain.dto.user.health.data;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Data
@Schema(name = "HealthDataAnalysisDTO", description = "健康数据分析参数")
public class HealthDataAnalysisDTO {
    
    @Schema(description = "部门ID列表")
    private List<String> departmentIds;
    
    @Schema(description = "用户ID列表")
    private List<String> userIds;
    
    @Schema(description = "开始时间戳")
    private Long startTime;
    
    @Schema(description = "结束时间戳")
    private Long endTime;
    
    @Schema(description = "数据类型列表 (如: heartRate, bloodOxygen, temperature等)")
    private List<String> dataTypes;
    
    @Schema(description = "时间粒度 (hour/day/week/month)")
    private String timeGranularity;
    
    @Schema(description = "是否包含异常数据")
    private Boolean includeAbnormal;
    
    @Schema(description = "自定义阈值")
    private List<ThresholdDTO> thresholds;
} 