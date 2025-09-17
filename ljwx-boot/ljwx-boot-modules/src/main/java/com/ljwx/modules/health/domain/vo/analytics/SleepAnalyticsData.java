/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 睡眠分析数据
 * 包含睡眠阶段、质量指标、趋势分析等专业睡眠数据
 * 
 * @author Claude Code
 */
@Data
public class SleepAnalyticsData {
    
    /**
     * 睡眠阶段数据列表
     */
    private List<SleepStageData> sleepStages;
    
    /**
     * 睡眠质量指标
     */
    private SleepQualityMetrics qualityMetrics;
    
    /**
     * 睡眠趋势数据
     */
    private List<SleepTrendData> trendData;
    
    /**
     * 睡眠阶段数据
     */
    @Data
    public static class SleepStageData {
        private LocalDateTime startTime;
        private LocalDateTime endTime;
        private String stage; // "light", "deep", "rem", "awake"
        private String stageName; // "浅睡", "深睡", "REM", "清醒"
        private Integer duration; // 持续时间（分钟）
        private Double percentage; // 占总睡眠时间百分比
    }
    
    /**
     * 睡眠质量指标
     */
    @Data
    public static class SleepQualityMetrics {
        private Double efficiency; // 睡眠效率 (%)
        private Double stability; // 睡眠稳定性评分 (0-100)
        private Double depthScore; // 深度睡眠评分 (0-100)
        private Double continuityScore; // 连续性评分 (0-100)
        private Integer totalDuration; // 总睡眠时长（分钟）
        private Integer deepSleepDuration; // 深度睡眠时长（分钟）
        private Integer lightSleepDuration; // 浅度睡眠时长（分钟）
        private Integer remSleepDuration; // REM睡眠时长（分钟）
        private Integer awakeDuration; // 清醒时长（分钟）
    }
    
    /**
     * 睡眠趋势数据
     */
    @Data
    public static class SleepTrendData {
        private LocalDate date;
        private Double totalSleep; // 总睡眠时长（小时）
        private Double deepSleep; // 深度睡眠时长（小时）
        private Double lightSleep; // 浅度睡眠时长（小时）
        private Double remSleep; // REM睡眠时长（小时）
        private Double efficiency; // 睡眠效率
        private Integer sleepLatency; // 入睡延迟（分钟）
        private Integer awakeCount; // 夜间觉醒次数
    }
}