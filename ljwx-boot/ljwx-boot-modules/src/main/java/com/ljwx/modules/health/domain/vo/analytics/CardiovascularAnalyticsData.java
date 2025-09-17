/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 心血管分析数据
 * 包含心率变异性、血压趋势、血氧饱和度等心血管健康指标
 * 
 * @author Claude Code
 */
@Data
public class CardiovascularAnalyticsData {
    
    /**
     * 心率变异性数据
     */
    private List<HeartRateVariabilityData> hrvData;
    
    /**
     * 血压趋势数据
     */
    private List<BloodPressureTrendData> bloodPressureData;
    
    /**
     * 血氧饱和度数据
     */
    private List<OxygenSaturationData> oxygenData;
    
    /**
     * 心率变异性数据
     */
    @Data
    public static class HeartRateVariabilityData {
        private LocalDateTime timestamp;
        private Integer heartRate; // 心率 (bpm)
        private Double variability; // 心率变异性 (ms)
        private String zone; // 心率区间 ("resting", "fat_burn", "cardio", "peak")
        private String zoneName; // 心率区间中文名
        private Double stressLevel; // 压力水平 (0-100)
        private Integer recoveryTime; // 恢复时间（分钟）
    }
    
    /**
     * 血压趋势数据
     */
    @Data
    public static class BloodPressureTrendData {
        private LocalDateTime timestamp;
        private Integer systolic; // 收缩压 (mmHg)
        private Integer diastolic; // 舒张压 (mmHg)
        private Double meanPressure; // 平均动脉压
        private String level; // 血压等级 ("normal", "elevated", "high1", "high2", "crisis")
        private String levelName; // 血压等级中文名
        private String riskLevel; // 风险等级 ("低", "中", "高")
    }
    
    /**
     * 血氧饱和度数据
     */
    @Data
    public static class OxygenSaturationData {
        private LocalDateTime timestamp;
        private Integer saturation; // 血氧饱和度 (%)
        private String level; // 血氧水平 ("normal", "low", "critical")
        private String levelName; // 血氧水平中文名
        private Double altitude; // 海拔高度（米）
        private String activity; // 活动状态 ("rest", "light", "moderate", "vigorous")
        private String activityName; // 活动状态中文名
    }
}