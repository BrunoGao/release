/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.util.List;

/**
 * 活动量分析数据
 * 包含步数目标、距离卡路里关系、活动时间分布等活动量指标
 * 
 * @author Claude Code
 */
@Data
public class ActivityAnalyticsData {
    
    /**
     * 步数目标进度数据
     */
    private StepGoalData stepData;
    
    /**
     * 距离-卡路里散点数据
     */
    private List<DistanceCaloriePoint> distanceCalorieData;
    
    /**
     * 活动时间分布数据
     */
    private List<ActivityTimeDistribution> timeDistribution;
    
    /**
     * 步数目标数据
     */
    @Data
    public static class StepGoalData {
        private Integer target; // 目标步数
        private Integer current; // 当前步数
        private Integer weeklyAverage; // 周平均步数
        private String monthlyTrend; // 月度趋势 ("increasing", "decreasing", "stable")
        private String monthlyTrendName; // 月度趋势中文名
        private Double completionRate; // 完成率 (%)
        private Integer daysAboveTarget; // 达标天数
        private Integer totalDays; // 总天数
        
        // 计算完成率
        public Double getCompletionRate() {
            if (target == null || target == 0) return 0.0;
            return (double) current / target * 100;
        }
    }
    
    /**
     * 距离-卡路里散点数据点
     */
    @Data
    public static class DistanceCaloriePoint {
        private Double distance; // 距离（公里）
        private Double calories; // 卡路里
        private Integer duration; // 时长（分钟）
        private String exerciseType; // 运动类型
        private String exerciseTypeName; // 运动类型中文名
        private Double intensity; // 强度 (1-10)
        private Double efficiency; // 效率（卡路里/公里）
        
        // 计算效率
        public Double getEfficiency() {
            if (distance == null || distance == 0) return 0.0;
            return calories / distance;
        }
    }
    
    /**
     * 活动时间分布
     */
    @Data
    public static class ActivityTimeDistribution {
        private String category; // 活动类别 ("sedentary", "light", "moderate", "vigorous")
        private String categoryName; // 活动类别中文名
        private Integer minutes; // 时长（分钟）
        private Double percentage; // 占比 (%)
        private String colorCode; // 图表颜色代码
        private Integer recommendedMin; // 推荐最小时长（分钟）
        private Integer recommendedMax; // 推荐最大时长（分钟）
        private String healthImpact; // 健康影响描述
    }
}