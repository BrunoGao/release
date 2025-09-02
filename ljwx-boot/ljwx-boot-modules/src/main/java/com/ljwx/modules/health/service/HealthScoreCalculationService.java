package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.*;
import com.ljwx.modules.health.mapper.*;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.repository.mapper.TAlertInfoMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 健康评分计算服务
 * 实现多维度健康评分算法：生理指标、行为模式、风险因子综合评分
 */
@Slf4j
@Service
public class HealthScoreCalculationService {

    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private HealthDataConfigMapper healthDataConfigMapper;
    
    @Autowired
    private HealthScoreMapper healthScoreMapper;
    
    @Autowired
    private TAlertInfoMapper alertInfoMapper;
    
    @Autowired
    private ISysUserService sysUserService;

    /**
     * 计算用户综合健康评分
     * @param userId 用户ID
     * @param dateRange 统计天数（默认30天）
     * @return 健康评分详情
     */
    public HealthScoreDetail calculateComprehensiveHealthScore(Long userId, Integer dateRange) {
        if (dateRange == null) dateRange = 30;
        
        log.info("开始计算用户{}的综合健康评分，统计{}天数据", userId, dateRange);
        
        try {
            // 1. 获取用户信息
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                throw new BizException("用户不存在");
            }

            // 2. 获取时间范围内的健康数据
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(dateRange);
            List<UserHealthData> healthDataList = getUserHealthData(userId, startTime, endTime);
            
            if (healthDataList.isEmpty()) {
                log.warn("用户{}在{}天内无健康数据", userId, dateRange);
                return createDefaultScore(userId, user.getCustomerId());
            }

            // 3. 获取个人健康基线
            Map<String, HealthBaseline> baselineMap = getUserBaselines(userId);
            
            // 4. 获取健康配置权重
            Map<String, HealthDataConfig> configMap = getHealthDataConfigs(user.getCustomerId());
            
            // 5. 获取告警历史
            List<TAlertInfo> alertHistory = getUserAlerts(userId, startTime, endTime);
            
            // 6. 计算各维度评分
            double physiologicalScore = calculatePhysiologicalScore(healthDataList, baselineMap, configMap);
            double behavioralScore = calculateBehavioralScore(healthDataList, configMap);
            double riskFactorScore = calculateRiskFactorScore(userId, alertHistory);
            
            // 7. 计算综合评分
            double finalScore = physiologicalScore * 0.5 + behavioralScore * 0.3 + riskFactorScore * 0.2;
            
            // 8. 生成评分详情
            HealthScoreDetail scoreDetail = new HealthScoreDetail();
            scoreDetail.setUserId(userId);
            scoreDetail.setCustomerId(user.getCustomerId());
            scoreDetail.setScoreDate(LocalDate.now());
            scoreDetail.setTotalScore(BigDecimal.valueOf(finalScore).setScale(2, RoundingMode.HALF_UP));
            scoreDetail.setPhysiologicalScore(BigDecimal.valueOf(physiologicalScore).setScale(2, RoundingMode.HALF_UP));
            scoreDetail.setBehavioralScore(BigDecimal.valueOf(behavioralScore).setScale(2, RoundingMode.HALF_UP));
            scoreDetail.setRiskFactorScore(BigDecimal.valueOf(riskFactorScore).setScale(2, RoundingMode.HALF_UP));
            scoreDetail.setScoreLevel(determineScoreLevel(finalScore));
            
            // 9. 计算细分维度评分
            calculateDetailedScores(scoreDetail, healthDataList, baselineMap);
            
            log.info("用户{}健康评分计算完成: 总分={}, 生理={}, 行为={}, 风险={}", 
                userId, finalScore, physiologicalScore, behavioralScore, riskFactorScore);
            
            return scoreDetail;
            
        } catch (Exception e) {
            log.error("计算健康评分失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("计算健康评分失败: " + e.getMessage());
        }
    }

    /**
     * 计算生理指标评分 (基于Z-Score标准化)
     */
    private double calculatePhysiologicalScore(List<UserHealthData> healthDataList, 
            Map<String, HealthBaseline> baselineMap, Map<String, HealthDataConfig> configMap) {
        
        double totalScore = 0.0;
        double totalWeight = 0.0;
        
        // 计算各生理指标的平均值
        Map<String, Double> avgMetrics = calculateAverageMetrics(healthDataList);
        
        for (Map.Entry<String, Double> entry : avgMetrics.entrySet()) {
            String metric = entry.getKey();
            double currentValue = entry.getValue();
            
            HealthBaseline baseline = baselineMap.get(metric);
            if (baseline == null) {
                log.warn("指标{}无基线数据，跳过评分", metric);
                continue;
            }
            
            // 计算Z-Score
            double baselineMean = baseline.getMeanValue().doubleValue();
            double baselineStd = baseline.getStdValue().doubleValue();
            
            if (baselineStd == 0) {
                log.warn("指标{}基线标准差为0，跳过评分", metric);
                continue;
            }
            
            double zScore = (currentValue - baselineMean) / baselineStd;
            
            // 转换为健康评分 (0-100)
            double metricScore = convertZScoreToHealthScore(metric, zScore);
            
            // 获取指标权重
            HealthDataConfig config = configMap.get(metric);
            double weight = config != null ? config.getWeight().doubleValue() : 0.15;
            
            totalScore += metricScore * weight;
            totalWeight += weight;
            
            log.debug("指标{}评分: 当前值={}, 基线均值={}, Z-Score={}, 得分={}", 
                metric, currentValue, baselineMean, zScore, metricScore);
        }
        
        return totalWeight > 0 ? totalScore / totalWeight : 0.0;
    }

    /**
     * 计算行为模式评分
     */
    private double calculateBehavioralScore(List<UserHealthData> healthDataList, 
            Map<String, HealthDataConfig> configMap) {
        
        // 计算运动评分
        double stepScore = calculateStepScore(healthDataList, configMap);
        
        // 计算睡眠评分
        double sleepScore = calculateSleepScore(healthDataList);
        
        // 计算活跃度评分
        double activityScore = calculateActivityScore(healthDataList);
        
        // 加权平均
        return stepScore * 0.4 + sleepScore * 0.4 + activityScore * 0.2;
    }

    /**
     * 计算风险因子评分
     */
    private double calculateRiskFactorScore(Long userId, List<TAlertInfo> alertHistory) {
        double baseScore = 100.0;
        
        // 获取职位权重（临时设置，实际需要查询职位表）
        double positionWeight = 0.8; // 假设中等风险职位
        double positionPenalty = (1 - positionWeight) * 10;
        
        // 计算告警惩罚
        double alertPenalty = 0.0;
        Map<Long, Double> alertPenalties = new HashMap<>();
        
        for (TAlertInfo alert : alertHistory) {
            double penalty = 0.0;
            String level = alert.getLevel();
            
            if ("critical".equals(level)) {
                penalty = 15.0;
            } else if ("major".equals(level)) {
                penalty = 10.0;
            } else if ("minor".equals(level)) {
                penalty = 5.0;
            }
            
            // 时间衰减：近期告警权重更大
            long daysAgo = ChronoUnit.DAYS.between(alert.getOccurAt().toLocalDate(), LocalDate.now());
            double decayFactor = Math.exp(-daysAgo / 30.0); // 30天衰减期
            
            alertPenalties.put(alert.getId(), penalty * decayFactor);
        }
        
        alertPenalty = alertPenalties.values().stream().mapToDouble(Double::doubleValue).sum();
        
        double totalPenalty = positionPenalty + alertPenalty;
        double finalScore = Math.max(baseScore - totalPenalty, 20.0);
        
        log.debug("风险因子评分: 基础分={}, 职位惩罚={}, 告警惩罚={}, 最终分={}", 
            baseScore, positionPenalty, alertPenalty, finalScore);
        
        return finalScore;
    }

    /**
     * Z-Score转换为健康评分
     */
    private double convertZScoreToHealthScore(String metric, double zScore) {
        double absZScore = Math.abs(zScore);
        
        // 不同指标使用不同的评分策略
        switch (metric) {
            case "heart_rate":
            case "blood_oxygen":
                // 正向指标：越接近正常范围越好
                return Math.max(100.0 - absZScore * 15.0, 50.0);
            
            case "pressure_high":
            case "pressure_low":
            case "stress":
                // 控制指标：偏离基线越多扣分越多
                return Math.max(100.0 - absZScore * 20.0, 40.0);
                
            case "temperature":
                // 体温指标：轻微偏离可接受
                return Math.max(100.0 - absZScore * 12.0, 60.0);
                
            default:
                return Math.max(100.0 - absZScore * 15.0, 50.0);
        }
    }

    /**
     * 计算运动评分
     */
    private double calculateStepScore(List<UserHealthData> healthDataList, 
            Map<String, HealthDataConfig> configMap) {
        
        // 计算日均步数
        double totalSteps = healthDataList.stream()
            .filter(data -> data.getStep() != null && data.getStep() > 0)
            .mapToInt(data -> data.getStep())
            .average()
            .orElse(0.0);
        
        // 获取步数目标（默认8000步）
        HealthDataConfig stepConfig = configMap.get("step");
        double stepTarget = stepConfig != null && stepConfig.getTargetValue() != null ? 
            stepConfig.getTargetValue().doubleValue() : 8000.0;
        
        // 计算步数评分
        return Math.min(totalSteps / stepTarget * 100.0, 100.0);
    }

    /**
     * 计算睡眠评分
     */
    private double calculateSleepScore(List<UserHealthData> healthDataList) {
        // 计算平均睡眠时长（小时）
        double avgSleep = healthDataList.stream()
            .filter(data -> data.getSleep() != null && data.getSleep() > 0)
            .mapToDouble(data -> data.getSleep().doubleValue() / 60.0) // 转换为小时
            .average()
            .orElse(0.0);
        
        if (avgSleep >= 7 && avgSleep <= 9) {
            return 100.0;
        } else if ((avgSleep >= 6 && avgSleep < 7) || (avgSleep > 9 && avgSleep <= 10)) {
            return 85.0;
        } else {
            return Math.max(70.0 - Math.abs(avgSleep - 8.0) * 10.0, 40.0);
        }
    }

    /**
     * 计算活跃度评分
     */
    private double calculateActivityScore(List<UserHealthData> healthDataList) {
        // 计算日均距离和卡路里
        double avgDistance = healthDataList.stream()
            .filter(data -> data.getDistance() != null && data.getDistance().doubleValue() > 0)
            .mapToDouble(data -> data.getDistance().doubleValue())
            .average()
            .orElse(0.0);
            
        double avgCalories = healthDataList.stream()
            .filter(data -> data.getCalorie() != null && data.getCalorie().doubleValue() > 0)
            .mapToDouble(data -> data.getCalorie().doubleValue())
            .average()
            .orElse(0.0);
        
        // 综合活跃度评分
        return Math.min((avgDistance * 0.3 + avgCalories * 0.01) * 2.0, 100.0);
    }

    /**
     * 计算详细评分维度
     */
    private void calculateDetailedScores(HealthScoreDetail scoreDetail, 
            List<UserHealthData> healthDataList, Map<String, HealthBaseline> baselineMap) {
        
        Map<String, Double> avgMetrics = calculateAverageMetrics(healthDataList);
        
        // 心血管评分
        double cardiovascularScore = calculateCardiovascularScore(avgMetrics, baselineMap);
        scoreDetail.setCardiovascularScore(BigDecimal.valueOf(cardiovascularScore).setScale(2, RoundingMode.HALF_UP));
        
        // 呼吸系统评分
        double respiratoryScore = calculateRespiratoryScore(avgMetrics, baselineMap);
        scoreDetail.setRespiratoryScore(BigDecimal.valueOf(respiratoryScore).setScale(2, RoundingMode.HALF_UP));
        
        // 代谢功能评分
        double metabolicScore = calculateMetabolicScore(avgMetrics, baselineMap);
        scoreDetail.setMetabolicScore(BigDecimal.valueOf(metabolicScore).setScale(2, RoundingMode.HALF_UP));
        
        // 心理健康评分
        double psychologicalScore = calculatePsychologicalScore(avgMetrics, baselineMap);
        scoreDetail.setPsychologicalScore(BigDecimal.valueOf(psychologicalScore).setScale(2, RoundingMode.HALF_UP));
    }

    // 辅助方法实现

    private List<UserHealthData> getUserHealthData(Long userId, LocalDateTime startTime, LocalDateTime endTime) {
        QueryWrapper<UserHealthData> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId)
                   .ge("timestamp", startTime)
                   .le("timestamp", endTime)
                   .eq("is_deleted", 0)
                   .orderByDesc("timestamp");
        return userHealthDataMapper.selectList(queryWrapper);
    }

    private Map<String, HealthBaseline> getUserBaselines(Long userId) {
        QueryWrapper<HealthBaseline> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId)
                   .eq("is_current", 1)
                   .eq("is_deleted", 0);
        
        List<HealthBaseline> baselines = healthBaselineMapper.selectList(queryWrapper);
        return baselines.stream()
            .collect(Collectors.toMap(HealthBaseline::getFeatureName, baseline -> baseline));
    }

    private Map<String, HealthDataConfig> getHealthDataConfigs(Long customerId) {
        QueryWrapper<HealthDataConfig> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("customer_id", customerId)
                   .eq("is_deleted", 0);
        
        List<HealthDataConfig> configs = healthDataConfigMapper.selectList(queryWrapper);
        return configs.stream()
            .collect(Collectors.toMap(HealthDataConfig::getMetricName, config -> config));
    }

    private List<TAlertInfo> getUserAlerts(Long userId, LocalDateTime startTime, LocalDateTime endTime) {
        QueryWrapper<TAlertInfo> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId)
                   .ge("occur_at", startTime)
                   .le("occur_at", endTime)
                   .eq("is_deleted", 0)
                   .orderByDesc("occur_at");
        return alertInfoMapper.selectList(queryWrapper);
    }

    private Map<String, Double> calculateAverageMetrics(List<UserHealthData> healthDataList) {
        Map<String, Double> avgMetrics = new HashMap<>();
        
        avgMetrics.put("heart_rate", healthDataList.stream()
            .filter(data -> data.getHeartRate() != null && data.getHeartRate() > 0)
            .mapToDouble(data -> data.getHeartRate().doubleValue())
            .average().orElse(0.0));
            
        avgMetrics.put("blood_oxygen", healthDataList.stream()
            .filter(data -> data.getBloodOxygen() != null && data.getBloodOxygen() > 0)
            .mapToDouble(data -> data.getBloodOxygen().doubleValue())
            .average().orElse(0.0));
            
        avgMetrics.put("pressure_high", healthDataList.stream()
            .filter(data -> data.getPressureHigh() != null && data.getPressureHigh() > 0)
            .mapToDouble(data -> data.getPressureHigh().doubleValue())
            .average().orElse(0.0));
            
        avgMetrics.put("pressure_low", healthDataList.stream()
            .filter(data -> data.getPressureLow() != null && data.getPressureLow() > 0)
            .mapToDouble(data -> data.getPressureLow().doubleValue())
            .average().orElse(0.0));
            
        avgMetrics.put("temperature", healthDataList.stream()
            .filter(data -> data.getTemperature() != null && data.getTemperature().doubleValue() > 0)
            .mapToDouble(data -> data.getTemperature().doubleValue())
            .average().orElse(0.0));
            
        avgMetrics.put("stress", healthDataList.stream()
            .filter(data -> data.getStress() != null && data.getStress() > 0)
            .mapToDouble(data -> data.getStress().doubleValue())
            .average().orElse(0.0));
        
        return avgMetrics;
    }

    private double calculateCardiovascularScore(Map<String, Double> avgMetrics, Map<String, HealthBaseline> baselineMap) {
        double heartRateScore = 100.0;
        double pressureScore = 100.0;
        
        // 心率评分
        if (avgMetrics.containsKey("heart_rate") && baselineMap.containsKey("heart_rate")) {
            double currentHR = avgMetrics.get("heart_rate");
            HealthBaseline hrBaseline = baselineMap.get("heart_rate");
            double zScore = (currentHR - hrBaseline.getMeanValue().doubleValue()) / hrBaseline.getStdValue().doubleValue();
            heartRateScore = convertZScoreToHealthScore("heart_rate", zScore);
        }
        
        // 血压评分
        if (avgMetrics.containsKey("pressure_high") && baselineMap.containsKey("pressure_high")) {
            double currentBP = avgMetrics.get("pressure_high");
            HealthBaseline bpBaseline = baselineMap.get("pressure_high");
            double zScore = (currentBP - bpBaseline.getMeanValue().doubleValue()) / bpBaseline.getStdValue().doubleValue();
            pressureScore = convertZScoreToHealthScore("pressure_high", zScore);
        }
        
        return (heartRateScore + pressureScore) / 2.0;
    }

    private double calculateRespiratoryScore(Map<String, Double> avgMetrics, Map<String, HealthBaseline> baselineMap) {
        if (avgMetrics.containsKey("blood_oxygen") && baselineMap.containsKey("blood_oxygen")) {
            double currentSPO2 = avgMetrics.get("blood_oxygen");
            HealthBaseline spo2Baseline = baselineMap.get("blood_oxygen");
            double zScore = (currentSPO2 - spo2Baseline.getMeanValue().doubleValue()) / spo2Baseline.getStdValue().doubleValue();
            return convertZScoreToHealthScore("blood_oxygen", zScore);
        }
        return 75.0; // 默认评分
    }

    private double calculateMetabolicScore(Map<String, Double> avgMetrics, Map<String, HealthBaseline> baselineMap) {
        if (avgMetrics.containsKey("temperature") && baselineMap.containsKey("temperature")) {
            double currentTemp = avgMetrics.get("temperature");
            HealthBaseline tempBaseline = baselineMap.get("temperature");
            double zScore = (currentTemp - tempBaseline.getMeanValue().doubleValue()) / tempBaseline.getStdValue().doubleValue();
            return convertZScoreToHealthScore("temperature", zScore);
        }
        return 75.0; // 默认评分
    }

    private double calculatePsychologicalScore(Map<String, Double> avgMetrics, Map<String, HealthBaseline> baselineMap) {
        if (avgMetrics.containsKey("stress") && baselineMap.containsKey("stress")) {
            double currentStress = avgMetrics.get("stress");
            HealthBaseline stressBaseline = baselineMap.get("stress");
            double zScore = (currentStress - stressBaseline.getMeanValue().doubleValue()) / stressBaseline.getStdValue().doubleValue();
            return convertZScoreToHealthScore("stress", zScore);
        }
        return 75.0; // 默认评分
    }

    private String determineScoreLevel(double score) {
        if (score >= 90) return "excellent";
        if (score >= 80) return "good";
        if (score >= 70) return "fair";
        if (score >= 60) return "poor";
        return "critical";
    }

    private HealthScoreDetail createDefaultScore(Long userId, Long customerId) {
        HealthScoreDetail scoreDetail = new HealthScoreDetail();
        scoreDetail.setUserId(userId);
        scoreDetail.setCustomerId(customerId);
        scoreDetail.setScoreDate(LocalDate.now());
        scoreDetail.setTotalScore(BigDecimal.valueOf(60.0));
        scoreDetail.setPhysiologicalScore(BigDecimal.valueOf(60.0));
        scoreDetail.setBehavioralScore(BigDecimal.valueOf(60.0));
        scoreDetail.setRiskFactorScore(BigDecimal.valueOf(80.0));
        scoreDetail.setScoreLevel("fair");
        return scoreDetail;
    }

    /**
     * 健康评分详情内部类
     */
    public static class HealthScoreDetail {
        private Long userId;
        private Long customerId;
        private LocalDate scoreDate;
        private BigDecimal totalScore;
        private BigDecimal physiologicalScore;
        private BigDecimal behavioralScore;
        private BigDecimal riskFactorScore;
        private BigDecimal cardiovascularScore;
        private BigDecimal respiratoryScore;
        private BigDecimal metabolicScore;
        private BigDecimal psychologicalScore;
        private String scoreLevel;

        // Getters and Setters
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public Long getCustomerId() { return customerId; }
        public void setCustomerId(Long customerId) { this.customerId = customerId; }
        
        public LocalDate getScoreDate() { return scoreDate; }
        public void setScoreDate(LocalDate scoreDate) { this.scoreDate = scoreDate; }
        
        public BigDecimal getTotalScore() { return totalScore; }
        public void setTotalScore(BigDecimal totalScore) { this.totalScore = totalScore; }
        
        public BigDecimal getPhysiologicalScore() { return physiologicalScore; }
        public void setPhysiologicalScore(BigDecimal physiologicalScore) { this.physiologicalScore = physiologicalScore; }
        
        public BigDecimal getBehavioralScore() { return behavioralScore; }
        public void setBehavioralScore(BigDecimal behavioralScore) { this.behavioralScore = behavioralScore; }
        
        public BigDecimal getRiskFactorScore() { return riskFactorScore; }
        public void setRiskFactorScore(BigDecimal riskFactorScore) { this.riskFactorScore = riskFactorScore; }
        
        public BigDecimal getCardiovascularScore() { return cardiovascularScore; }
        public void setCardiovascularScore(BigDecimal cardiovascularScore) { this.cardiovascularScore = cardiovascularScore; }
        
        public BigDecimal getRespiratoryScore() { return respiratoryScore; }
        public void setRespiratoryScore(BigDecimal respiratoryScore) { this.respiratoryScore = respiratoryScore; }
        
        public BigDecimal getMetabolicScore() { return metabolicScore; }
        public void setMetabolicScore(BigDecimal metabolicScore) { this.metabolicScore = metabolicScore; }
        
        public BigDecimal getPsychologicalScore() { return psychologicalScore; }
        public void setPsychologicalScore(BigDecimal psychologicalScore) { this.psychologicalScore = psychologicalScore; }
        
        public String getScoreLevel() { return scoreLevel; }
        public void setScoreLevel(String scoreLevel) { this.scoreLevel = scoreLevel; }
    }
}