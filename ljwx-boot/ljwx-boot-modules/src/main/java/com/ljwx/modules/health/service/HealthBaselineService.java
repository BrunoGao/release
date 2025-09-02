package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.HealthBaseline;
import com.ljwx.modules.health.entity.UserHealthData;
import com.ljwx.modules.health.mapper.HealthBaselineMapper;
import com.ljwx.modules.health.mapper.UserHealthDataMapper;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.entity.SysPosition;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.service.ISysPositionService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 健康基线生成服务
 * 实现个人基线、群体基线、职位风险基线的智能计算
 */
@Slf4j
@Service
public class HealthBaselineService {

    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private ISysPositionService sysPositionService;

    /**
     * 生成个人健康基线
     * @param userId 用户ID
     * @param days 统计天数（默认30天）
     */
    @Transactional
    public void generatePersonalBaseline(Long userId, Integer days) {
        if (days == null) days = 30;
        
        log.info("开始生成用户{}的个人健康基线，统计{}天数据", userId, days);
        
        try {
            // 获取用户信息
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                throw new BizException("用户不存在");
            }

            // 计算时间范围
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(days);

            // 查询用户健康数据
            QueryWrapper<UserHealthData> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("user_id", userId)
                       .ge("timestamp", startTime)
                       .le("timestamp", endTime)
                       .eq("is_deleted", 0)
                       .orderByAsc("timestamp");

            List<UserHealthData> healthDataList = userHealthDataMapper.selectList(queryWrapper);
            
            if (healthDataList.isEmpty()) {
                log.warn("用户{}在{}天内无健康数据，跳过基线生成", userId, days);
                return;
            }

            // 按指标分组计算基线
            Map<String, List<Double>> metricGroups = groupHealthMetrics(healthDataList);
            
            // 获取用户年龄组和性别
            String ageGroup = calculateAgeGroup(LocalDate.now().minusYears(30)); // Default age
            String gender = user.getGender();
            
            // 获取职位风险等级
            String positionRiskLevel = getUserPositionRiskLevel(userId);

            // 为每个指标生成基线
            for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
                String metric = entry.getKey();
                List<Double> values = entry.getValue();
                
                if (values.size() < 3) {
                    log.warn("指标{}的样本数量不足，跳过基线生成", metric);
                    continue;
                }
                
                // 计算统计指标
                BaselineStatistics stats = calculateStatistics(values);
                
                // 季节性调整
                double seasonalFactor = getSeasonalFactor(metric, LocalDate.now().getMonthValue());
                
                // 创建基线记录
                HealthBaseline baseline = new HealthBaseline();
                baseline.setUserId(userId);
                baseline.setCustomerId(user.getCustomerId());
                baseline.setDeviceSn(healthDataList.get(0).getDeviceSn());
                baseline.setFeatureName(metric);
                baseline.setBaselineDate(LocalDate.now());
                baseline.setBaselineType("personal");
                baseline.setAgeGroup(ageGroup);
                baseline.setGender(gender);
                baseline.setPositionRiskLevel(positionRiskLevel);
                baseline.setMeanValue(BigDecimal.valueOf(stats.getMean() * seasonalFactor).setScale(2, RoundingMode.HALF_UP));
                baseline.setStdValue(BigDecimal.valueOf(stats.getStd()).setScale(2, RoundingMode.HALF_UP));
                baseline.setMinValue(BigDecimal.valueOf(stats.getMin()));
                baseline.setMaxValue(BigDecimal.valueOf(stats.getMax()));
                baseline.setSampleCount(values.size());
                baseline.setSeasonalFactor(BigDecimal.valueOf(seasonalFactor).setScale(4, RoundingMode.HALF_UP));
                baseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
                baseline.setBaselineTime(LocalDate.now());
                baseline.setIsCurrent(1);
                baseline.setIsDeleted(0);

                // 先将之前的基线设为非当前
                updatePreviousBaselines(userId, metric);
                
                // 插入新基线
                healthBaselineMapper.insert(baseline);
                
                log.debug("生成{}指标基线: mean={}, std={}, samples={}", 
                    metric, stats.getMean(), stats.getStd(), values.size());
            }
            
            log.info("用户{}的个人健康基线生成完成，共处理{}个指标", userId, metricGroups.size());
            
        } catch (Exception e) {
            log.error("生成个人健康基线失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("生成个人健康基线失败: " + e.getMessage());
        }
    }

    /**
     * 生成群体健康基线
     * @param customerId 租户ID
     * @param ageGroup 年龄组
     * @param gender 性别
     */
    @Transactional
    public void generatePopulationBaseline(Long customerId, String ageGroup, String gender) {
        log.info("开始生成群体健康基线: customerId={}, ageGroup={}, gender={}", customerId, ageGroup, gender);
        
        try {
            // 计算时间范围（90天）
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(90);

            // 查询符合条件的用户健康数据
            List<UserHealthData> populationData = getUserHealthDataByDemographics(
                customerId, ageGroup, gender, startTime, endTime);
            
            if (populationData.isEmpty()) {
                log.warn("群体{}{}在90天内无健康数据", ageGroup, gender);
                return;
            }

            // 按指标分组计算群体基线
            Map<String, List<Double>> metricGroups = groupHealthMetrics(populationData);
            
            for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
                String metric = entry.getKey();
                List<Double> values = entry.getValue();
                
                if (values.size() < 10) { // 群体基线需要更多样本
                    log.warn("群体指标{}的样本数量不足，跳过基线生成", metric);
                    continue;
                }
                
                BaselineStatistics stats = calculateStatistics(values);
                
                // 创建群体基线记录
                HealthBaseline baseline = new HealthBaseline();
                baseline.setUserId(0L); // 群体基线用户ID为0
                baseline.setCustomerId(customerId);
                baseline.setFeatureName(metric);
                baseline.setBaselineDate(LocalDate.now());
                baseline.setBaselineType("population");
                baseline.setAgeGroup(ageGroup);
                baseline.setGender(gender);
                baseline.setMeanValue(BigDecimal.valueOf(stats.getMean()).setScale(2, RoundingMode.HALF_UP));
                baseline.setStdValue(BigDecimal.valueOf(stats.getStd()).setScale(2, RoundingMode.HALF_UP));
                baseline.setMinValue(BigDecimal.valueOf(stats.getMin()));
                baseline.setMaxValue(BigDecimal.valueOf(stats.getMax()));
                baseline.setSampleCount(values.size());
                baseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
                baseline.setBaselineTime(LocalDate.now());
                baseline.setIsCurrent(1);
                baseline.setIsDeleted(0);

                // 更新之前的群体基线
                updatePreviousPopulationBaselines(customerId, ageGroup, gender, metric);
                
                healthBaselineMapper.insert(baseline);
                
                log.debug("生成群体{}指标基线: mean={}, std={}, samples={}", 
                    metric, stats.getMean(), stats.getStd(), values.size());
            }
            
            log.info("群体健康基线生成完成: customerId={}, ageGroup={}, gender={}", customerId, ageGroup, gender);
            
        } catch (Exception e) {
            log.error("生成群体健康基线失败: customerId={}, ageGroup={}, gender={}, error={}", 
                customerId, ageGroup, gender, e.getMessage(), e);
            throw new BizException("生成群体健康基线失败: " + e.getMessage());
        }
    }

    /**
     * 生成职位风险调整基线
     * @param userId 用户ID
     */
    public void generatePositionAdjustedBaseline(Long userId) {
        log.info("开始生成用户{}的职位风险调整基线", userId);
        
        try {
            // 获取用户个人基线
            QueryWrapper<HealthBaseline> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("user_id", userId)
                       .eq("baseline_type", "personal")
                       .eq("is_current", 1)
                       .eq("is_deleted", 0);
            
            List<HealthBaseline> personalBaselines = healthBaselineMapper.selectList(queryWrapper);
            
            if (personalBaselines.isEmpty()) {
                log.warn("用户{}无个人基线数据，无法生成职位调整基线", userId);
                return;
            }
            
            // 获取职位风险系数
            String positionRiskLevel = getUserPositionRiskLevel(userId);
            double riskAdjustmentFactor = getPositionRiskAdjustmentFactor(positionRiskLevel);
            
            for (HealthBaseline personalBaseline : personalBaselines) {
                // 计算调整后的基线值
                BigDecimal adjustedMeanValue = personalBaseline.getMeanValue()
                    .multiply(BigDecimal.valueOf(riskAdjustmentFactor))
                    .setScale(2, RoundingMode.HALF_UP);
                
                // 创建职位调整基线
                HealthBaseline adjustedBaseline = new HealthBaseline();
                adjustedBaseline.setUserId(userId);
                adjustedBaseline.setCustomerId(personalBaseline.getCustomerId());
                adjustedBaseline.setDeviceSn(personalBaseline.getDeviceSn());
                adjustedBaseline.setFeatureName(personalBaseline.getFeatureName());
                adjustedBaseline.setBaselineDate(LocalDate.now());
                adjustedBaseline.setBaselineType("position");
                adjustedBaseline.setAgeGroup(personalBaseline.getAgeGroup());
                adjustedBaseline.setGender(personalBaseline.getGender());
                adjustedBaseline.setPositionRiskLevel(positionRiskLevel);
                adjustedBaseline.setMeanValue(adjustedMeanValue);
                adjustedBaseline.setStdValue(personalBaseline.getStdValue());
                adjustedBaseline.setMinValue(personalBaseline.getMinValue());
                adjustedBaseline.setMaxValue(personalBaseline.getMaxValue());
                adjustedBaseline.setSampleCount(personalBaseline.getSampleCount());
                adjustedBaseline.setSeasonalFactor(personalBaseline.getSeasonalFactor());
                adjustedBaseline.setConfidenceLevel(personalBaseline.getConfidenceLevel());
                adjustedBaseline.setBaselineTime(LocalDate.now());
                adjustedBaseline.setIsCurrent(1);
                adjustedBaseline.setIsDeleted(0);
                
                // 更新之前的职位基线
                updatePreviousPositionBaselines(userId, personalBaseline.getFeatureName());
                
                healthBaselineMapper.insert(adjustedBaseline);
            }
            
            log.info("用户{}的职位风险调整基线生成完成", userId);
            
        } catch (Exception e) {
            log.error("生成职位风险调整基线失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("生成职位风险调整基线失败: " + e.getMessage());
        }
    }

    // 辅助方法实现

    /**
     * 将健康数据按指标分组
     */
    private Map<String, List<Double>> groupHealthMetrics(List<UserHealthData> healthDataList) {
        Map<String, List<Double>> metricGroups = new HashMap<>();
        
        for (UserHealthData data : healthDataList) {
            if (data.getHeartRate() != null && data.getHeartRate() > 0) {
                metricGroups.computeIfAbsent("heart_rate", k -> new ArrayList<>()).add(data.getHeartRate().doubleValue());
            }
            if (data.getBloodOxygen() != null && data.getBloodOxygen() > 0) {
                metricGroups.computeIfAbsent("blood_oxygen", k -> new ArrayList<>()).add(data.getBloodOxygen().doubleValue());
            }
            if (data.getPressureHigh() != null && data.getPressureHigh() > 0) {
                metricGroups.computeIfAbsent("pressure_high", k -> new ArrayList<>()).add(data.getPressureHigh().doubleValue());
            }
            if (data.getPressureLow() != null && data.getPressureLow() > 0) {
                metricGroups.computeIfAbsent("pressure_low", k -> new ArrayList<>()).add(data.getPressureLow().doubleValue());
            }
            if (data.getTemperature() != null && data.getTemperature().doubleValue() > 0) {
                metricGroups.computeIfAbsent("temperature", k -> new ArrayList<>()).add(data.getTemperature().doubleValue());
            }
            if (data.getStress() != null && data.getStress() > 0) {
                metricGroups.computeIfAbsent("stress", k -> new ArrayList<>()).add(data.getStress().doubleValue());
            }
        }
        
        return metricGroups;
    }

    /**
     * 计算统计指标
     */
    private BaselineStatistics calculateStatistics(List<Double> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException("统计值列表不能为空");
        }
        
        // 计算均值
        double mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        
        // 计算标准差
        double variance = values.stream()
            .mapToDouble(v -> Math.pow(v - mean, 2))
            .average()
            .orElse(0.0);
        double std = Math.sqrt(variance);
        
        // 最小值和最大值
        double min = values.stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
        double max = values.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);
        
        return new BaselineStatistics(mean, std, min, max);
    }

    /**
     * 计算年龄组
     */
    private String calculateAgeGroup(LocalDate birthday) {
        if (birthday == null) {
            return "unknown";
        }
        
        int age = Period.between(birthday, LocalDate.now()).getYears();
        
        if (age < 30) {
            return "young";
        } else if (age < 50) {
            return "middle";
        } else {
            return "senior";
        }
    }

    /**
     * 获取用户职位风险等级
     */
    private String getUserPositionRiskLevel(Long userId) {
        try {
            // 通过用户服务获取用户职位信息
            // 这里需要根据实际的用户-职位关联表查询
            // 临时返回默认值
            return "medium";
        } catch (Exception e) {
            log.warn("获取用户{}职位风险等级失败，使用默认值", userId);
            return "medium";
        }
    }

    /**
     * 获取季节性调整因子
     */
    private double getSeasonalFactor(String metric, int month) {
        Map<String, Map<String, Double>> seasonalFactors = new HashMap<>();
        
        // 心率季节性调整
        Map<String, Double> heartRateFactors = new HashMap<>();
        heartRateFactors.put("winter", 1.02);  // 冬季心率略高
        heartRateFactors.put("spring", 1.00);
        heartRateFactors.put("summer", 0.98);  // 夏季心率略低
        heartRateFactors.put("autumn", 1.01);
        seasonalFactors.put("heart_rate", heartRateFactors);
        
        // 血压季节性调整
        Map<String, Double> pressureFactors = new HashMap<>();
        pressureFactors.put("winter", 1.05);  // 冬季血压偏高
        pressureFactors.put("spring", 1.00);
        pressureFactors.put("summer", 0.96);
        pressureFactors.put("autumn", 1.02);
        seasonalFactors.put("pressure_high", pressureFactors);
        seasonalFactors.put("pressure_low", pressureFactors);
        
        String season = getSeason(month);
        return seasonalFactors.getOrDefault(metric, Map.of(season, 1.0)).getOrDefault(season, 1.0);
    }

    private String getSeason(int month) {
        if (month >= 12 || month <= 2) return "winter";
        if (month >= 3 && month <= 5) return "spring";
        if (month >= 6 && month <= 8) return "summer";
        return "autumn";
    }

    /**
     * 获取职位风险调整因子
     */
    private double getPositionRiskAdjustmentFactor(String riskLevel) {
        switch (riskLevel) {
            case "high": return 0.85;
            case "medium": return 0.90;
            case "low":
            default: return 1.0;
        }
    }

    // 数据库更新方法

    private void updatePreviousBaselines(Long userId, String metric) {
        QueryWrapper<HealthBaseline> updateWrapper = new QueryWrapper<>();
        updateWrapper.eq("user_id", userId)
                    .eq("feature_name", metric)
                    .eq("baseline_type", "personal")
                    .eq("is_current", 1)
                    .eq("is_deleted", 0);
        
        HealthBaseline updateBaseline = new HealthBaseline();
        updateBaseline.setIsCurrent(0);
        healthBaselineMapper.update(updateBaseline, updateWrapper);
    }

    private void updatePreviousPopulationBaselines(Long customerId, String ageGroup, String gender, String metric) {
        QueryWrapper<HealthBaseline> updateWrapper = new QueryWrapper<>();
        updateWrapper.eq("customer_id", customerId)
                    .eq("age_group", ageGroup)
                    .eq("gender", gender)
                    .eq("feature_name", metric)
                    .eq("baseline_type", "population")
                    .eq("is_current", 1)
                    .eq("is_deleted", 0);
        
        HealthBaseline updateBaseline = new HealthBaseline();
        updateBaseline.setIsCurrent(0);
        healthBaselineMapper.update(updateBaseline, updateWrapper);
    }

    private void updatePreviousPositionBaselines(Long userId, String metric) {
        QueryWrapper<HealthBaseline> updateWrapper = new QueryWrapper<>();
        updateWrapper.eq("user_id", userId)
                    .eq("feature_name", metric)
                    .eq("baseline_type", "position")
                    .eq("is_current", 1)
                    .eq("is_deleted", 0);
        
        HealthBaseline updateBaseline = new HealthBaseline();
        updateBaseline.setIsCurrent(0);
        healthBaselineMapper.update(updateBaseline, updateWrapper);
    }

    private List<UserHealthData> getUserHealthDataByDemographics(Long customerId, String ageGroup, 
            String gender, LocalDateTime startTime, LocalDateTime endTime) {
        // 这里需要实现复杂的查询逻辑，关联用户表和健康数据表
        // 临时返回空列表，实际实现需要编写相应的SQL
        return new ArrayList<>();
    }

    /**
     * 统计数据内部类
     */
    private static class BaselineStatistics {
        private final double mean;
        private final double std;
        private final double min;
        private final double max;

        public BaselineStatistics(double mean, double std, double min, double max) {
            this.mean = mean;
            this.std = std;
            this.min = min;
            this.max = max;
        }

        public double getMean() { return mean; }
        public double getStd() { return std; }
        public double getMin() { return min; }
        public double getMax() { return max; }
    }
}