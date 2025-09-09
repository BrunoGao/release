package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.HealthBaseline;
import com.ljwx.modules.health.entity.UserHealthData;
import com.ljwx.modules.health.mapper.HealthBaselineMapper;
import com.ljwx.modules.health.mapper.UserHealthDataMapper;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.service.UnifiedHealthDataQueryService;
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
 * 统一健康基线服务
 * 融合个人基线、用户基线、组织基线的智能计算
 * 通过baseline_type字段区分不同类型的基线：personal, user, org, population
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-01-26
 */
@Slf4j
@Service
public class UnifiedHealthBaselineService {

    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;

    /**
     * 统一基线生成入口 - 根据类型生成不同维度的基线
     * @param baselineType 基线类型: personal, user, org, population
     * @param entityId 实体ID(用户ID或组织ID)
     * @param customerId 租户ID
     * @param days 统计天数
     * @param additionalParams 附加参数(如年龄组、性别等)
     */
    @Transactional
    public void generateUnifiedBaseline(String baselineType, Long entityId, Long customerId, 
                                      Integer days, Map<String, Object> additionalParams) {
        log.info("🔄 开始生成统一健康基线: type={}, entityId={}, customerId={}, days={}", 
                baselineType, entityId, customerId, days);
        
        switch (baselineType.toLowerCase()) {
            case "personal":
            case "user":
                generatePersonalBaseline(entityId, customerId, days);
                break;
            case "org":
            case "organization":
                generateOrganizationBaseline(entityId, customerId, days);
                break;
            case "population":
                generatePopulationBaseline(customerId, additionalParams, days);
                break;
            default:
                throw new BizException("不支持的基线类型: " + baselineType);
        }
    }

    /**
     * 生成个人健康基线 (替代原personal基线)
     * @param userId 用户ID
     * @param customerId 租户ID
     * @param days 统计天数
     */
    @Transactional
    public void generatePersonalBaseline(Long userId, Long customerId, Integer days) {
        if (days == null) days = 30;
        
        log.info("📊 开始生成用户{}的个人健康基线，统计{}天数据", userId, days);
        
        try {
            // 获取用户信息
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                throw new BizException("用户不存在: " + userId);
            }

            // 使用统一查询服务获取健康数据
            List<UserHealthData> healthDataList = getHealthDataForBaseline(
                customerId, userId, null, days);
            
            if (healthDataList.isEmpty()) {
                log.warn("⚠️ 用户{}在{}天内无健康数据，跳过基线生成", userId, days);
                return;
            }

            // 按指标分组计算基线
            Map<String, List<Double>> metricGroups = groupHealthMetrics(healthDataList);
            
            // 获取用户附加信息
            UserProfile userProfile = buildUserProfile(user);
            
            // 为每个指标生成基线
            int processedMetrics = 0;
            for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
                String metric = entry.getKey();
                List<Double> values = entry.getValue();
                
                if (values.size() < 3) {
                    log.debug("⏭️ 指标{}的样本数量不足({}个)，跳过基线生成", metric, values.size());
                    continue;
                }
                
                // 计算统计指标
                BaselineStatistics stats = calculateStatistics(values);
                
                // 季节性和职位风险调整
                double seasonalFactor = getSeasonalFactor(metric, LocalDate.now().getMonthValue());
                double riskFactor = getPositionRiskAdjustmentFactor(userProfile.getPositionRiskLevel());
                
                // 创建基线记录 - 使用统一表结构
                HealthBaseline baseline = buildBaselineRecord(
                    "user", userId, customerId, 
                    healthDataList.get(0).getDeviceSn(), 
                    metric, stats, userProfile,
                    seasonalFactor, riskFactor, values.size()
                );
                
                // 设置组织ID用于组织级聚合
                if (user.getOrgId() != null) {
                    baseline.setOrgId(String.valueOf(user.getOrgId()));
                }

                // 更新之前的基线为非当前
                updatePreviousBaselines("user", userId, null, metric);
                
                // 插入新基线
                healthBaselineMapper.insert(baseline);
                processedMetrics++;
                
                log.debug("📈 生成{}指标基线: mean={}, std={}, samples={}", 
                    metric, stats.getMean(), stats.getStd(), values.size());
            }
            
            log.info("✅ 用户{}的个人健康基线生成完成，共处理{}个指标", userId, processedMetrics);
            
        } catch (Exception e) {
            log.error("❌ 生成个人健康基线失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("生成个人健康基线失败: " + e.getMessage());
        }
    }

    /**
     * 生成组织健康基线 (解决t_org_health_baseline缺失问题)
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param days 统计天数
     */
    @Transactional
    public void generateOrganizationBaseline(Long orgId, Long customerId, Integer days) {
        if (days == null) days = 90;
        
        log.info("🏢 开始生成组织{}的健康基线，统计{}天数据", orgId, days);
        
        try {
            // 获取组织下所有用户的健康数据
            List<UserHealthData> orgHealthDataList = getOrgHealthData(orgId, customerId, days);
            
            if (orgHealthDataList.isEmpty()) {
                log.warn("⚠️ 组织{}在{}天内无健康数据，跳过基线生成", orgId, days);
                return;
            }

            // 按指标分组计算组织基线
            Map<String, List<Double>> metricGroups = groupHealthMetrics(orgHealthDataList);
            
            // 计算组织用户数量
            long userCount = orgHealthDataList.stream()
                .map(UserHealthData::getUserId)
                .distinct()
                .count();
            
            int processedMetrics = 0;
            for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
                String metric = entry.getKey();
                List<Double> values = entry.getValue();
                
                if (values.size() < 10) { // 组织基线需要更多样本
                    log.debug("⏭️ 组织指标{}的样本数量不足({}个)，跳过基线生成", metric, values.size());
                    continue;
                }
                
                BaselineStatistics stats = calculateStatistics(values);
                
                // 创建组织基线记录
                HealthBaseline baseline = new HealthBaseline();
                baseline.setUserId(0L); // 组织基线用户ID为0
                baseline.setCustomerId(customerId);
                baseline.setOrgId(String.valueOf(orgId));
                baseline.setFeatureName(metric);
                baseline.setBaselineDate(LocalDate.now());
                baseline.setBaselineType("org"); // 统一使用org类型
                baseline.setMeanValue(BigDecimal.valueOf(stats.getMean()).setScale(2, RoundingMode.HALF_UP));
                baseline.setStdValue(BigDecimal.valueOf(stats.getStd()).setScale(2, RoundingMode.HALF_UP));
                baseline.setMinValue(BigDecimal.valueOf(stats.getMin()));
                baseline.setMaxValue(BigDecimal.valueOf(stats.getMax()));
                baseline.setSampleCount(values.size());
                baseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
                baseline.setBaselineTime(LocalDate.now());
                baseline.setIsCurrent(1);
                baseline.setIsDeleted(0);
                baseline.setCreateTime(LocalDateTime.now());
                baseline.setUpdateTime(LocalDateTime.now());

                // 更新之前的组织基线
                updatePreviousBaselines("org", 0L, orgId, metric);
                
                healthBaselineMapper.insert(baseline);
                processedMetrics++;
                
                log.debug("📊 生成组织{}指标基线: mean={}, std={}, samples={}, users={}", 
                    metric, stats.getMean(), stats.getStd(), values.size(), userCount);
            }
            
            log.info("✅ 组织{}健康基线生成完成，共处理{}个指标，覆盖{}个用户", 
                    orgId, processedMetrics, userCount);
            
        } catch (Exception e) {
            log.error("❌ 生成组织健康基线失败: orgId={}, error={}", orgId, e.getMessage(), e);
            throw new BizException("生成组织健康基线失败: " + e.getMessage());
        }
    }

    /**
     * 生成人口统计学基线
     * @param customerId 租户ID
     * @param params 参数(年龄组、性别等)
     * @param days 统计天数
     */
    @Transactional
    public void generatePopulationBaseline(Long customerId, Map<String, Object> params, Integer days) {
        if (days == null) days = 180;
        
        String ageGroup = (String) params.getOrDefault("ageGroup", "all");
        String gender = (String) params.getOrDefault("gender", "all");
        
        log.info("👥 开始生成人口基线: customerId={}, ageGroup={}, gender={}, days={}", 
                customerId, ageGroup, gender, days);
        
        try {
            // 获取符合人口统计学特征的健康数据
            List<UserHealthData> populationData = getPopulationHealthData(
                customerId, ageGroup, gender, days);
            
            if (populationData.isEmpty()) {
                log.warn("⚠️ 群体{}{}在{}天内无健康数据", ageGroup, gender, days);
                return;
            }

            // 按指标分组计算群体基线
            Map<String, List<Double>> metricGroups = groupHealthMetrics(populationData);
            
            long userCount = populationData.stream()
                .map(UserHealthData::getUserId)
                .distinct()
                .count();
            
            int processedMetrics = 0;
            for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
                String metric = entry.getKey();
                List<Double> values = entry.getValue();
                
                if (values.size() < 20) { // 人口基线需要大量样本
                    log.debug("⏭️ 群体指标{}的样本数量不足({}个)，跳过基线生成", metric, values.size());
                    continue;
                }
                
                BaselineStatistics stats = calculateStatistics(values);
                
                // 创建人口基线记录
                HealthBaseline baseline = new HealthBaseline();
                baseline.setUserId(0L);
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
                baseline.setCreateTime(LocalDateTime.now());
                baseline.setUpdateTime(LocalDateTime.now());

                // 更新之前的群体基线
                updatePreviousPopulationBaselines(customerId, ageGroup, gender, metric);
                
                healthBaselineMapper.insert(baseline);
                processedMetrics++;
            }
            
            log.info("✅ 群体健康基线生成完成: ageGroup={}, gender={}, metrics={}, users={}", 
                    ageGroup, gender, processedMetrics, userCount);
            
        } catch (Exception e) {
            log.error("❌ 生成群体健康基线失败: ageGroup={}, gender={}, error={}", 
                    ageGroup, gender, e.getMessage(), e);
            throw new BizException("生成群体健康基线失败: " + e.getMessage());
        }
    }

    /**
     * 查询基线数据 - 支持统一查询接口
     * @param queryType 查询类型
     * @param entityId 实体ID
     * @param customerId 租户ID
     * @param featureName 指标名称
     * @return 基线列表
     */
    public List<HealthBaseline> queryBaselines(String queryType, Long entityId, Long customerId, String featureName) {
        QueryWrapper<HealthBaseline> wrapper = new QueryWrapper<>();
        wrapper.eq("customer_id", customerId)
               .eq("baseline_type", queryType)
               .eq("is_current", 1)
               .eq("is_deleted", 0);
        
        if ("user".equals(queryType) && entityId != null && entityId > 0) {
            wrapper.eq("user_id", entityId);
        } else if ("org".equals(queryType) && entityId != null) {
            wrapper.eq("org_id", String.valueOf(entityId));
        }
        
        if (featureName != null && !featureName.trim().isEmpty()) {
            wrapper.eq("feature_name", featureName);
        }
        
        wrapper.orderByDesc("baseline_date");
        
        return healthBaselineMapper.selectList(wrapper);
    }

    // ========== 私有辅助方法 ==========

    /**
     * 获取健康数据用于基线计算
     */
    private List<UserHealthData> getHealthDataForBaseline(Long customerId, Long userId, 
                                                        String deviceSn, Integer days) {
        try {
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(days);

            UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
            query.setCustomerId(customerId);
            query.setUserId(userId);
            if (deviceSn != null) query.setDeviceSn(deviceSn);
            query.setStartDate(startTime);
            query.setEndDate(endTime);
            query.setPageSize(50000); // 基线需要大量数据
            query.setEnableSharding(true);
            query.setOrderBy("timestamp");
            query.setOrderDirection("asc");
            
            Map<String, Object> queryResult = unifiedQueryService.queryHealthData(query);
            return (List<UserHealthData>) queryResult.getOrDefault("data", new ArrayList<>());
            
        } catch (Exception e) {
            log.error("查询健康数据失败: customerId={}, userId={}, error={}", 
                    customerId, userId, e.getMessage(), e);
            return new ArrayList<>();
        }
    }

    /**
     * 获取组织健康数据
     */
    private List<UserHealthData> getOrgHealthData(Long orgId, Long customerId, Integer days) {
        // 这里需要实现组织用户查询逻辑
        // 暂时使用简化实现
        try {
            QueryWrapper<UserHealthData> wrapper = new QueryWrapper<>();
            wrapper.eq("customer_id", customerId);
            if (orgId != null) {
                wrapper.eq("org_id", orgId);
            }
            wrapper.ge("create_time", LocalDateTime.now().minusDays(days));
            wrapper.orderByAsc("timestamp");
            
            return userHealthDataMapper.selectList(wrapper);
        } catch (Exception e) {
            log.error("查询组织健康数据失败: orgId={}, error={}", orgId, e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 获取人口统计学健康数据
     */
    private List<UserHealthData> getPopulationHealthData(Long customerId, String ageGroup, 
                                                       String gender, Integer days) {
        // 需要关联用户表进行人口统计学过滤
        // 这里提供简化实现框架
        try {
            QueryWrapper<UserHealthData> wrapper = new QueryWrapper<>();
            wrapper.eq("customer_id", customerId);
            wrapper.ge("create_time", LocalDateTime.now().minusDays(days));
            
            // TODO: 添加年龄组和性别过滤逻辑
            // 需要JOIN sys_user表进行过滤
            
            return userHealthDataMapper.selectList(wrapper);
        } catch (Exception e) {
            log.error("查询人口统计学数据失败: ageGroup={}, gender={}, error={}", 
                    ageGroup, gender, e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 将健康数据按指标分组
     */
    private Map<String, List<Double>> groupHealthMetrics(List<UserHealthData> healthDataList) {
        Map<String, List<Double>> metricGroups = new HashMap<>();
        
        for (UserHealthData data : healthDataList) {
            addMetricValue(metricGroups, "heart_rate", data.getHeartRate());
            addMetricValue(metricGroups, "blood_oxygen", data.getBloodOxygen());
            addMetricValue(metricGroups, "pressure_high", data.getPressureHigh());
            addMetricValue(metricGroups, "pressure_low", data.getPressureLow());
            addMetricValue(metricGroups, "temperature", data.getTemperature());
            addMetricValue(metricGroups, "stress", data.getStress());
            addMetricValue(metricGroups, "step", data.getStep());
            addMetricValue(metricGroups, "calorie", data.getCalorie());
            addMetricValue(metricGroups, "distance", data.getDistance());
            addMetricValue(metricGroups, "sleep", data.getSleep());
        }
        
        return metricGroups;
    }

    private void addMetricValue(Map<String, List<Double>> metricGroups, String metricName, Number value) {
        if (value != null && value.doubleValue() > 0) {
            metricGroups.computeIfAbsent(metricName, k -> new ArrayList<>())
                       .add(value.doubleValue());
        }
    }

    /**
     * 构建用户画像
     */
    private UserProfile buildUserProfile(SysUser user) {
        UserProfile profile = new UserProfile();
        profile.setAgeGroup(calculateAgeGroup(user.getBirthday()));
        profile.setGender(user.getGender());
        profile.setPositionRiskLevel(getUserPositionRiskLevel(user.getId()));
        return profile;
    }

    /**
     * 构建基线记录
     */
    private HealthBaseline buildBaselineRecord(String baselineType, Long userId, Long customerId,
                                             String deviceSn, String metric, 
                                             BaselineStatistics stats, UserProfile userProfile,
                                             double seasonalFactor, double riskFactor, int sampleCount) {
        HealthBaseline baseline = new HealthBaseline();
        baseline.setUserId(userId);
        baseline.setCustomerId(customerId);
        baseline.setDeviceSn(deviceSn);
        baseline.setFeatureName(metric);
        baseline.setBaselineDate(LocalDate.now());
        baseline.setBaselineType(baselineType);
        baseline.setAgeGroup(userProfile.getAgeGroup());
        baseline.setGender(userProfile.getGender());
        baseline.setPositionRiskLevel(userProfile.getPositionRiskLevel());
        
        double adjustedMean = stats.getMean() * seasonalFactor * riskFactor;
        baseline.setMeanValue(BigDecimal.valueOf(adjustedMean).setScale(2, RoundingMode.HALF_UP));
        baseline.setStdValue(BigDecimal.valueOf(stats.getStd()).setScale(2, RoundingMode.HALF_UP));
        baseline.setMinValue(BigDecimal.valueOf(stats.getMin()));
        baseline.setMaxValue(BigDecimal.valueOf(stats.getMax()));
        baseline.setSampleCount(sampleCount);
        baseline.setSeasonalFactor(BigDecimal.valueOf(seasonalFactor).setScale(4, RoundingMode.HALF_UP));
        baseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
        baseline.setBaselineTime(LocalDate.now());
        baseline.setIsCurrent(1);
        baseline.setIsDeleted(0);
        baseline.setCreateTime(LocalDateTime.now());
        baseline.setUpdateTime(LocalDateTime.now());
        
        return baseline;
    }

    // 其他辅助方法保持不变...
    
    private BaselineStatistics calculateStatistics(List<Double> values) {
        if (values.isEmpty()) {
            throw new IllegalArgumentException("统计值列表不能为空");
        }
        
        double mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        double variance = values.stream()
            .mapToDouble(v -> Math.pow(v - mean, 2))
            .average()
            .orElse(0.0);
        double std = Math.sqrt(variance);
        double min = values.stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
        double max = values.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);
        
        return new BaselineStatistics(mean, std, min, max);
    }

    private String calculateAgeGroup(LocalDate birthday) {
        if (birthday == null) return "unknown";
        
        int age = Period.between(birthday, LocalDate.now()).getYears();
        if (age < 30) return "young";
        else if (age < 50) return "middle";
        else return "senior";
    }

    private String getUserPositionRiskLevel(Long userId) {
        // TODO: 实现职位风险等级查询
        return "medium";
    }

    private double getSeasonalFactor(String metric, int month) {
        // 季节性调整逻辑
        return 1.0;
    }

    private double getPositionRiskAdjustmentFactor(String riskLevel) {
        switch (riskLevel) {
            case "high": return 0.85;
            case "medium": return 0.90;
            case "low":
            default: return 1.0;
        }
    }

    private void updatePreviousBaselines(String baselineType, Long userId, Long orgId, String metric) {
        QueryWrapper<HealthBaseline> updateWrapper = new QueryWrapper<>();
        updateWrapper.eq("baseline_type", baselineType)
                   .eq("feature_name", metric)
                   .eq("is_current", 1)
                   .eq("is_deleted", 0);
        
        if ("user".equals(baselineType)) {
            updateWrapper.eq("user_id", userId);
        } else if ("org".equals(baselineType)) {
            updateWrapper.eq("org_id", String.valueOf(orgId));
        }
        
        HealthBaseline updateBaseline = new HealthBaseline();
        updateBaseline.setIsCurrent(0);
        updateBaseline.setUpdateTime(LocalDateTime.now());
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
        updateBaseline.setUpdateTime(LocalDateTime.now());
        healthBaselineMapper.update(updateBaseline, updateWrapper);
    }

    // 内部类
    private static class BaselineStatistics {
        private final double mean;
        private final double std;
        private final double min;
        private final double max;

        public BaselineStatistics(double mean, double std, double min, double max) {
            this.mean = mean; this.std = std; this.min = min; this.max = max;
        }

        public double getMean() { return mean; }
        public double getStd() { return std; }
        public double getMin() { return min; }
        public double getMax() { return max; }
    }

    private static class UserProfile {
        private String ageGroup;
        private String gender;
        private String positionRiskLevel;

        // Getters and Setters
        public String getAgeGroup() { return ageGroup; }
        public void setAgeGroup(String ageGroup) { this.ageGroup = ageGroup; }
        public String getGender() { return gender; }
        public void setGender(String gender) { this.gender = gender; }
        public String getPositionRiskLevel() { return positionRiskLevel; }
        public void setPositionRiskLevel(String positionRiskLevel) { this.positionRiskLevel = positionRiskLevel; }
    }
}