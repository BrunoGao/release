package com.ljwx.modules.health.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.Builder;

import java.util.List;
import java.util.Map;

@Data
@Builder
@Schema(name = "HealthDataAnalysisVO", description = "健康数据分析结果")
public class HealthDataAnalysisVO {
    
    @Schema(description = "时间维度统计数据")
    private Map<String, List<TimeSeriesDataPoint>> timeSeriesData;
    
    @Schema(description = "部门维度统计数据")
    private Map<String, DepartmentStats> departmentStats;
    
    @Schema(description = "个人维度统计数据")
    private Map<String, UserStats> userStats;
    
    @Schema(description = "异常数据统计")
    private AbnormalStats abnormalStats;
    
    @Data
    @Builder
    public static class TimeSeriesDataPoint {
        private String timestamp;
        private String dataType;
        private Double avgValue;
        private Double maxValue;
        private Double minValue;
        private Integer sampleCount;
    }
    
    @Data
    @Builder
    public static class DepartmentStats {
        private String departmentId;
        private String departmentName;
        private Map<String, AggregateStats> dataTypeStats;
        private Integer totalEmployees;
        private Integer activeEmployees;
    }
    
    @Data
    @Builder
    public static class UserStats {
        private String userId;
        private String userName;
        private String departmentId;
        private Map<String, AggregateStats> dataTypeStats;
        private Integer dataPoints;
        private Double complianceRate;
    }
    
    @Data
    @Builder
    public static class AggregateStats {
        private Double avgValue;
        private Double maxValue;
        private Double minValue;
        private Double stdDev;
        private Integer sampleCount;
        private Integer abnormalCount;
    }
    
    @Data
    @Builder
    public static class AbnormalStats {
        private Integer totalAbnormalCount;
        private Map<String, Integer> abnormalByDataType;
        private Map<String, Integer> abnormalByDepartment;
        private List<AbnormalRecord> topAbnormalRecords;
    }
    
    @Data
    @Builder
    public static class AbnormalRecord {
        private String userId;
        private String userName;
        private String departmentId;
        private String dataType;
        private Double value;
        private String timestamp;
    }
} 