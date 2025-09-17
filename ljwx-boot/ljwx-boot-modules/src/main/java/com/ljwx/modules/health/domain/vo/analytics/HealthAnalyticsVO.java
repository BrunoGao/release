/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 健康数据分析结果VO
 * 包含睡眠、运动、心血管、活动量等各维度分析数据
 * 
 * @author Claude Code
 */
@Data
public class HealthAnalyticsVO {
    
    /**
     * 睡眠分析数据
     */
    private SleepAnalyticsData sleepData;
    
    /**
     * 运动分析数据
     */
    private ExerciseAnalyticsData exerciseData;
    
    /**
     * 心血管分析数据
     */
    private CardiovascularAnalyticsData cardiovascularData;
    
    /**
     * 活动量分析数据
     */
    private ActivityAnalyticsData activityData;
    
    /**
     * 统计摘要
     */
    private StatisticsSummary summary;
    
    /**
     * 分析生成时间
     */
    private LocalDateTime generatedAt;
    
    /**
     * 分析用户数量
     */
    private Integer userCount;
    
    /**
     * 数据时间范围
     */
    private String dateRange;
    
    /**
     * 数据质量评分 (0-100)
     */
    private Double dataQualityScore;
    
    /**
     * 分析版本
     */
    private String analyticsVersion = "1.0";
}