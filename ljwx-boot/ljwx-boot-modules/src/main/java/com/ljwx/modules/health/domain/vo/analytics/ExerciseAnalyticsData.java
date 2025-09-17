/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 运动分析数据
 * 包含运动类型分布、强度分析、卡路里消耗等专业运动数据
 * 
 * @author Claude Code
 */
@Data
public class ExerciseAnalyticsData {
    
    /**
     * 运动类型分布统计
     */
    private Map<String, ExerciseTypeStats> exerciseTypeDistribution;
    
    /**
     * 运动强度热力图数据
     */
    private List<ExerciseIntensityData> intensityHeatmap;
    
    /**
     * 卡路里燃烧趋势数据
     */
    private List<CalorieBurnData> calorieTrend;
    
    /**
     * 运动类型统计数据
     */
    @Data
    public static class ExerciseTypeStats {
        private String exerciseType; // 运动类型
        private String exerciseTypeName; // 运动类型中文名
        private Integer totalDuration; // 总时长（分钟）
        private Integer totalCalories; // 总卡路里消耗
        private Integer frequency; // 频次
        private Double averageIntensity; // 平均强度 (1-10)
        private Double averageHeartRate; // 平均心率
        private Double totalDistance; // 总距离（公里）
        private Double percentage; // 占总运动时间百分比
    }
    
    /**
     * 运动强度热力图数据
     */
    @Data
    public static class ExerciseIntensityData {
        private Integer hourOfDay; // 小时 (0-23)
        private Integer dayOfWeek; // 星期 (1-7)
        private String dayName; // 星期名称
        private Double intensity; // 强度值 (0-10)
        private String intensityLevel; // 强度等级 ("低", "中", "高", "很高")
        private Integer duration; // 该时段运动时长（分钟）
    }
    
    /**
     * 卡路里燃烧数据
     */
    @Data
    public static class CalorieBurnData {
        private LocalDateTime timestamp;
        private String exerciseType; // 运动类型
        private Integer activeCalories; // 主动卡路里
        private Integer restingCalories; // 静息卡路里
        private Integer totalCalories; // 总卡路里
        private Integer duration; // 运动时长（分钟）
        private Double averageHeartRate; // 平均心率
        private Double distance; // 距离（公里）
    }
}