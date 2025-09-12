package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.*;
import com.ljwx.modules.health.mapper.*;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
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
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 统一健康数据处理服务
 * 统一处理 baseline, score, prediction, recommendation, profile
 * 遵循：租户 → 部门 → 用户 → 汇总 的处理逻辑
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-09-12
 */
@Slf4j
@Service
public class UnifiedHealthProcessingService {

    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private HealthScoreMapper healthScoreMapper;
    
    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    
    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;
    
    @Autowired
    private WeightCalculationService weightCalculationService;
    
    @Autowired
    private HealthPredictionService healthPredictionService;
    
    @Autowired
    private HealthRecommendationService healthRecommendationService;
    
    @Autowired
    private HealthProfileService healthProfileService;
    
    private final ExecutorService executorService = Executors.newFixedThreadPool(10);
    
    // 健康特征配置
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
        "pressure_low", "stress", "step", "calorie", "distance", "sleep"
    };

    /**
     * 统一健康数据处理入口
     * 1. findTopLevelOrganizations → 获取租户
     * 2. findAllDescendants → 获取租户下的部门id  
     * 3. 根据org_id查询sys_user → 获取org下的user_id
     * 4. 对每个userId使用UnifiedHealthQueryDTO → 生成user的baseline
     * 5. 汇总到每个org → org级别的baseline
     * 6. 汇总到每个租户 → 租户级别的baseline
     * 
     * @param processType 处理类型: baseline, score, prediction, recommendation, profile
     * @param days 统计天数
     */
    @Transactional
    public void processUnifiedHealthData(String processType, Integer days) {
        log.info("🚀 开始统一健康数据处理: type={}, days={}", processType, days);
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. 获取所有租户（顶级组织）
            List<Long> customerIds = findTopLevelOrganizations();
            log.info("📊 找到{}个租户需要处理", customerIds.size());
            
            // 并行处理每个租户
            List<CompletableFuture<Void>> customerTasks = customerIds.stream()
                .map(customerId -> CompletableFuture.runAsync(() -> 
                    processCustomerHealthData(customerId, processType, days), executorService))
                .collect(Collectors.toList());
            
            // 等待所有租户处理完成
            CompletableFuture.allOf(customerTasks.toArray(new CompletableFuture[0])).join();
            
            long duration = System.currentTimeMillis() - startTime;
            log.info("✅ 统一健康数据处理完成: type={}, 用时{}ms, 处理租户数={}", 
                    processType, duration, customerIds.size());
            
        } catch (Exception e) {
            log.error("❌ 统一健康数据处理失败: type={}, error={}", processType, e.getMessage(), e);
            throw new BizException("统一健康数据处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理单个租户的健康数据
     */
    @Transactional
    public void processCustomerHealthData(Long customerId, String processType, Integer days) {
        log.info("🏢 开始处理租户{} - {}", customerId, processType);
        
        try {
            // 2. 获取租户下的所有部门
            List<Long> departmentIds = findAllDescendants(customerId);
            log.info("📂 租户{}下找到{}个部门", customerId, departmentIds.size());
            
            // 3. 处理每个部门
            Map<Long, Map<String, Object>> departmentResults = new HashMap<>();
            
            for (Long departmentId : departmentIds) {
                Map<String, Object> deptResult = processDepartmentHealthData(
                    customerId, departmentId, processType, days);
                departmentResults.put(departmentId, deptResult);
            }
            
            // 5. 汇总部门数据到组织级别
            aggregateDepartmentToOrg(customerId, departmentResults, processType);
            
            // 6. 汇总到租户级别
            aggregateToCustomer(customerId, departmentResults, processType);
            
            log.info("✅ 租户{}健康数据处理完成: {}", customerId, processType);
            
        } catch (Exception e) {
            log.error("❌ 租户{}健康数据处理失败: type={}, error={}", 
                    customerId, processType, e.getMessage(), e);
            throw new BizException("租户健康数据处理失败: " + e.getMessage());
        }
    }

    /**
     * 处理单个部门的健康数据
     */
    @Transactional
    public Map<String, Object> processDepartmentHealthData(Long customerId, Long departmentId, 
                                                         String processType, Integer days) {
        log.debug("👥 处理部门{} - {}", departmentId, processType);
        
        try {
            // 3. 根据org_id查询sys_user获取用户列表
            List<Long> userIds = getUserIdsByDepartment(departmentId);
            if (userIds.isEmpty()) {
                log.debug("⚠️ 部门{}下无用户数据", departmentId);
                return new HashMap<>();
            }
            
            // 4. 对每个userId处理健康数据
            List<CompletableFuture<Map<String, Object>>> userTasks = userIds.stream()
                .map(userId -> CompletableFuture.supplyAsync(() -> 
                    processUserHealthData(customerId, userId, processType, days), executorService))
                .collect(Collectors.toList());
            
            // 等待所有用户处理完成
            CompletableFuture<List<Map<String, Object>>> allUserResults = 
                CompletableFuture.allOf(userTasks.toArray(new CompletableFuture[0]))
                .thenApply(v -> userTasks.stream()
                    .map(CompletableFuture::join)
                    .collect(Collectors.toList()));
            
            List<Map<String, Object>> userResults = allUserResults.join();
            
            // 构建部门级汇总结果
            Map<String, Object> departmentResult = new HashMap<>();
            departmentResult.put("departmentId", departmentId);
            departmentResult.put("customerId", customerId);
            departmentResult.put("userCount", userIds.size());
            departmentResult.put("userResults", userResults);
            departmentResult.put("processType", processType);
            departmentResult.put("processTime", LocalDateTime.now());
            
            log.debug("✅ 部门{}处理完成: {}, 用户数={}", departmentId, processType, userIds.size());
            return departmentResult;
            
        } catch (Exception e) {
            log.error("❌ 部门{}处理失败: type={}, error={}", 
                    departmentId, processType, e.getMessage(), e);
            return new HashMap<>();
        }
    }

    /**
     * 处理单个用户的健康数据
     * 4. 对每个userId，根据UnifiedHealthQueryDTO查询健康数据并生成对应的处理结果
     */
    @Transactional
    public Map<String, Object> processUserHealthData(Long customerId, Long userId, 
                                                   String processType, Integer days) {
        log.debug("👤 处理用户{} - {}", userId, processType);
        
        try {
            // 获取用户健康数据
            List<UserHealthData> healthDataList = getUserHealthData(customerId, userId, days);
            if (healthDataList.isEmpty()) {
                log.debug("⚠️ 用户{}在{}天内无健康数据", userId, days);
                return createEmptyUserResult(userId, processType);
            }
            
            Map<String, Object> userResult = new HashMap<>();
            userResult.put("userId", userId);
            userResult.put("customerId", customerId);
            userResult.put("dataCount", healthDataList.size());
            userResult.put("processType", processType);
            
            // 根据处理类型调用不同的处理逻辑
            switch (processType.toLowerCase()) {
                case "baseline":
                    processUserBaseline(customerId, userId, healthDataList, userResult);
                    break;
                case "score":
                    processUserScore(customerId, userId, healthDataList, userResult);
                    break;
                case "prediction":
                    processUserPrediction(customerId, userId, healthDataList, userResult);
                    break;
                case "recommendation":
                    processUserRecommendation(customerId, userId, healthDataList, userResult);
                    break;
                case "profile":
                    processUserProfile(customerId, userId, healthDataList, userResult);
                    break;
                default:
                    throw new BizException("不支持的处理类型: " + processType);
            }
            
            userResult.put("processTime", LocalDateTime.now());
            userResult.put("success", true);
            
            return userResult;
            
        } catch (Exception e) {
            log.error("❌ 用户{}处理失败: type={}, error={}", userId, processType, e.getMessage(), e);
            return createErrorUserResult(userId, processType, e.getMessage());
        }
    }

    /**
     * 处理用户基线数据
     */
    private void processUserBaseline(Long customerId, Long userId, 
                                   List<UserHealthData> healthDataList, 
                                   Map<String, Object> userResult) {
        log.debug("📊 处理用户{}基线数据", userId);
        
        // 按指标分组计算基线
        Map<String, List<Double>> metricGroups = groupHealthMetrics(healthDataList);
        List<HealthBaseline> baselines = new ArrayList<>();
        
        SysUser user = sysUserService.getById(userId);
        UserProfile userProfile = buildUserProfile(user);
        
        for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
            String metric = entry.getKey();
            List<Double> values = entry.getValue();
            
            if (values.size() < 3) {
                continue; // 样本不足
            }
            
            BaselineStatistics stats = calculateStatistics(values);
            
            // 创建用户基线
            HealthBaseline baseline = buildUserBaseline(
                customerId, userId, metric, stats, userProfile, values.size());
            
            // 更新之前的基线为非当前
            updatePreviousBaselines("user", userId, null, metric);
            
            // 保存基线
            healthBaselineMapper.insert(baseline);
            baselines.add(baseline);
        }
        
        userResult.put("baselines", baselines);
        userResult.put("metricsProcessed", baselines.size());
    }

    /**
     * 处理用户健康评分
     */
    private void processUserScore(Long customerId, Long userId, 
                                List<UserHealthData> healthDataList, 
                                Map<String, Object> userResult) {
        log.debug("📈 处理用户{}健康评分", userId);
        
        // 获取用户基线
        List<HealthBaseline> userBaselines = getUserBaselines(customerId, userId);
        if (userBaselines.isEmpty()) {
            log.warn("⚠️ 用户{}无基线数据，跳过评分计算", userId);
            userResult.put("scores", new ArrayList<>());
            return;
        }
        
        // 计算评分
        List<HealthScore> scores = calculateUserHealthScores(
            customerId, userId, healthDataList, userBaselines);
        
        userResult.put("scores", scores);
        userResult.put("scoresProcessed", scores.size());
    }

    /**
     * 处理用户健康预测
     */
    private void processUserPrediction(Long customerId, Long userId, 
                                     List<UserHealthData> healthDataList, 
                                     Map<String, Object> userResult) {
        log.debug("🔮 处理用户{}健康预测", userId);
        
        try {
            // 调用预测服务 (暂时使用空实现)
            List<HealthPrediction> predictions = new ArrayList<>();
            // TODO: 实现预测服务方法
            log.debug("预测服务暂未实现，返回空列表");
            
            userResult.put("predictions", predictions);
            userResult.put("predictionsProcessed", predictions.size());
            
        } catch (Exception e) {
            log.error("❌ 用户{}预测处理失败: {}", userId, e.getMessage());
            userResult.put("predictions", new ArrayList<>());
            userResult.put("error", e.getMessage());
        }
    }

    /**
     * 处理用户健康建议
     */
    private void processUserRecommendation(Long customerId, Long userId, 
                                         List<UserHealthData> healthDataList, 
                                         Map<String, Object> userResult) {
        log.debug("💡 处理用户{}健康建议", userId);
        
        try {
            // 调用建议服务 (暂时使用空实现)
            // TODO: 实现建议服务方法
            log.debug("建议服务暂未实现");
            userResult.put("recommendationsProcessed", true);
            
        } catch (Exception e) {
            log.error("❌ 用户{}建议处理失败: {}", userId, e.getMessage());
            userResult.put("recommendationsProcessed", false);
            userResult.put("error", e.getMessage());
        }
    }

    /**
     * 处理用户健康档案
     */
    private void processUserProfile(Long customerId, Long userId, 
                                  List<UserHealthData> healthDataList, 
                                  Map<String, Object> userResult) {
        log.debug("📋 处理用户{}健康档案", userId);
        
        try {
            // 调用档案服务 (暂时使用空实现)
            // TODO: 实现档案服务方法
            log.debug("档案服务暂未实现");
            userResult.put("profileProcessed", true);
            
        } catch (Exception e) {
            log.error("❌ 用户{}档案处理失败: {}", userId, e.getMessage());
            userResult.put("profileProcessed", false);
            userResult.put("error", e.getMessage());
        }
    }

    /**
     * 5. 汇总部门数据到组织级别
     */
    @Transactional
    public void aggregateDepartmentToOrg(Long customerId, 
                                       Map<Long, Map<String, Object>> departmentResults,
                                       String processType) {
        log.info("🏢 汇总部门数据到组织级别: customerId={}, processType={}", customerId, processType);
        
        try {
            switch (processType.toLowerCase()) {
                case "baseline":
                    aggregateBaselineToOrg(customerId, departmentResults);
                    break;
                case "score":
                    aggregateScoreToOrg(customerId, departmentResults);
                    break;
                // 其他类型的汇总逻辑...
            }
            
        } catch (Exception e) {
            log.error("❌ 组织级汇总失败: customerId={}, error={}", customerId, e.getMessage(), e);
        }
    }

    /**
     * 6. 汇总到租户级别
     */
    @Transactional
    public void aggregateToCustomer(Long customerId, 
                                  Map<Long, Map<String, Object>> departmentResults,
                                  String processType) {
        log.info("🏪 汇总到租户级别: customerId={}, processType={}", customerId, processType);
        
        try {
            switch (processType.toLowerCase()) {
                case "baseline":
                    aggregateBaselineToCustomer(customerId, departmentResults);
                    break;
                case "score":
                    aggregateScoreToCustomer(customerId, departmentResults);
                    break;
                // 其他类型的汇总逻辑...
            }
            
        } catch (Exception e) {
            log.error("❌ 租户级汇总失败: customerId={}, error={}", customerId, e.getMessage(), e);
        }
    }

    // ========== 辅助方法 ==========

    /**
     * 1. 获取顶级组织（租户）
     */
    private List<Long> findTopLevelOrganizations() {
        try {
            // 获取所有customer_id
            QueryWrapper<SysUser> wrapper = new QueryWrapper<>();
            wrapper.select("DISTINCT customer_id");
            wrapper.isNotNull("customer_id");
            wrapper.ne("customer_id", 0);
            
            List<SysUser> users = sysUserService.list(wrapper);
            return users.stream()
                .map(SysUser::getCustomerId)
                .distinct()
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("❌ 获取顶级组织失败: {}", e.getMessage(), e);
            return new ArrayList<>();
        }
    }

    /**
     * 2. 获取租户下的所有部门
     */
    private List<Long> findAllDescendants(Long customerId) {
        try {
            // 获取租户下所有部门的org_id
            QueryWrapper<SysUser> wrapper = new QueryWrapper<>();
            wrapper.select("DISTINCT org_id");
            wrapper.eq("customer_id", customerId);
            wrapper.isNotNull("org_id");
            
            List<SysUser> users = sysUserService.list(wrapper);
            return users.stream()
                .map(SysUser::getOrgId)
                .distinct()
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("❌ 获取部门列表失败: customerId={}, error={}", customerId, e.getMessage(), e);
            return new ArrayList<>();
        }
    }

    /**
     * 3. 根据部门ID获取用户列表
     */
    private List<Long> getUserIdsByDepartment(Long departmentId) {
        try {
            QueryWrapper<SysUser> wrapper = new QueryWrapper<>();
            wrapper.select("user_id");
            wrapper.eq("org_id", departmentId);
            wrapper.eq("status", "1"); // 只获取正常用户
            
            List<SysUser> users = sysUserService.list(wrapper);
            return users.stream()
                .map(SysUser::getId)
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("❌ 获取部门用户失败: departmentId={}, error={}", departmentId, e.getMessage(), e);
            return new ArrayList<>();
        }
    }

    /**
     * 4. 获取用户健康数据
     */
    private List<UserHealthData> getUserHealthData(Long customerId, Long userId, Integer days) {
        try {
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(days);

            UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
            query.setCustomerId(customerId);
            query.setUserId(userId);
            query.setStartDate(startTime);
            query.setEndDate(endTime);
            query.setPageSize(50000);
            query.setEnableSharding(true);
            query.setOrderBy("timestamp");
            query.setOrderDirection("asc");
            
            Map<String, Object> queryResult = unifiedQueryService.queryHealthData(query);
            return (List<UserHealthData>) queryResult.getOrDefault("data", new ArrayList<>());
            
        } catch (Exception e) {
            log.error("❌ 获取用户健康数据失败: userId={}, error={}", userId, e.getMessage());
            return new ArrayList<>();
        }
    }

    // 其他辅助方法...
    
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

    private UserProfile buildUserProfile(SysUser user) {
        UserProfile profile = new UserProfile();
        profile.setAgeGroup(calculateAgeGroup(user.getBirthday()));
        profile.setGender(user.getGender());
        profile.setPositionRiskLevel("medium"); // 默认中等风险
        return profile;
    }

    private String calculateAgeGroup(LocalDate birthday) {
        if (birthday == null) return "unknown";
        
        int age = Period.between(birthday, LocalDate.now()).getYears();
        if (age < 30) return "young";
        else if (age < 50) return "middle";
        else return "senior";
    }

    private HealthBaseline buildUserBaseline(Long customerId, Long userId, String metric, 
                                           BaselineStatistics stats, UserProfile userProfile, int sampleCount) {
        HealthBaseline baseline = new HealthBaseline();
        baseline.setUserId(userId);
        baseline.setCustomerId(customerId);
        baseline.setFeatureName(metric);
        baseline.setBaselineDate(LocalDate.now());
        baseline.setBaselineType("user");
        baseline.setAgeGroup(userProfile.getAgeGroup());
        baseline.setGender(userProfile.getGender());
        baseline.setPositionRiskLevel(userProfile.getPositionRiskLevel());
        baseline.setMeanValue(BigDecimal.valueOf(stats.getMean()).setScale(2, RoundingMode.HALF_UP));
        baseline.setStdValue(BigDecimal.valueOf(stats.getStd()).setScale(2, RoundingMode.HALF_UP));
        baseline.setMinValue(BigDecimal.valueOf(stats.getMin()));
        baseline.setMaxValue(BigDecimal.valueOf(stats.getMax()));
        baseline.setSampleCount(sampleCount);
        baseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
        baseline.setBaselineTime(LocalDate.now());
        baseline.setIsCurrent(1);
        baseline.setIsDeleted(0);
        baseline.setCreateTime(LocalDateTime.now());
        baseline.setUpdateTime(LocalDateTime.now());
        
        return baseline;
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

    private List<HealthBaseline> getUserBaselines(Long customerId, Long userId) {
        QueryWrapper<HealthBaseline> wrapper = new QueryWrapper<>();
        wrapper.eq("customer_id", customerId)
               .eq("user_id", userId)
               .eq("baseline_type", "user")
               .eq("is_current", 1)
               .eq("is_deleted", 0);
        
        return healthBaselineMapper.selectList(wrapper);
    }

    private List<HealthScore> calculateUserHealthScores(Long customerId, Long userId, 
                                                      List<UserHealthData> healthDataList,
                                                      List<HealthBaseline> baselines) {
        List<HealthScore> scores = new ArrayList<>();
        
        // 基于基线计算健康评分的逻辑
        Map<String, HealthBaseline> baselineMap = baselines.stream()
            .collect(Collectors.toMap(HealthBaseline::getFeatureName, b -> b));
        
        Map<String, List<Double>> metricGroups = groupHealthMetrics(healthDataList);
        
        for (Map.Entry<String, List<Double>> entry : metricGroups.entrySet()) {
            String metric = entry.getKey();
            List<Double> values = entry.getValue();
            HealthBaseline baseline = baselineMap.get(metric);
            
            if (baseline != null && !values.isEmpty()) {
                double avgValue = values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
                double baselineMean = baseline.getMeanValue().doubleValue();
                double baselineStd = baseline.getStdValue().doubleValue();
                
                // 计算Z-Score
                double zScore = baselineStd > 0 ? (avgValue - baselineMean) / baselineStd : 0.0;
                
                // 转换为0-100的评分
                double scoreValue = Math.max(0, Math.min(100, 50 + zScore * 15));
                
                HealthScore score = new HealthScore();
                score.setUserId(userId);
                score.setCustomerId(customerId);
                score.setFeatureName(metric);
                score.setScoreDate(LocalDate.now());
                score.setScoreValue(BigDecimal.valueOf(scoreValue).setScale(2, RoundingMode.HALF_UP));
                score.setScoreLevel(getScoreLevel(scoreValue));
                score.setRawValue(BigDecimal.valueOf(avgValue));
                score.setBaselineValue(baseline.getMeanValue());
                score.setZScore(BigDecimal.valueOf(zScore).setScale(4, RoundingMode.HALF_UP));
                score.setCreateTime(LocalDateTime.now());
                score.setUpdateTime(LocalDateTime.now());
                score.setIsDeleted(0);
                
                healthScoreMapper.insert(score);
                scores.add(score);
            }
        }
        
        return scores;
    }

    private String getScoreLevel(double scoreValue) {
        if (scoreValue >= 80) return "excellent";
        else if (scoreValue >= 60) return "good";
        else if (scoreValue >= 40) return "fair";
        else return "poor";
    }

    private Map<String, Object> createEmptyUserResult(Long userId, String processType) {
        Map<String, Object> result = new HashMap<>();
        result.put("userId", userId);
        result.put("processType", processType);
        result.put("dataCount", 0);
        result.put("success", false);
        result.put("message", "无健康数据");
        return result;
    }

    private Map<String, Object> createErrorUserResult(Long userId, String processType, String error) {
        Map<String, Object> result = new HashMap<>();
        result.put("userId", userId);
        result.put("processType", processType);
        result.put("success", false);
        result.put("error", error);
        return result;
    }

    // 基线汇总到组织级别
    private void aggregateBaselineToOrg(Long customerId, Map<Long, Map<String, Object>> departmentResults) {
        log.info("📊 汇总基线到组织级别: customerId={}", customerId);
        
        // 收集所有用户的基线数据
        Map<String, List<HealthBaseline>> metricBaselines = new HashMap<>();
        
        departmentResults.values().forEach(deptResult -> {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> userResults = (List<Map<String, Object>>) deptResult.get("userResults");
            
            userResults.forEach(userResult -> {
                @SuppressWarnings("unchecked")
                List<HealthBaseline> baselines = (List<HealthBaseline>) userResult.get("baselines");
                if (baselines != null) {
                    baselines.forEach(baseline -> {
                        metricBaselines.computeIfAbsent(baseline.getFeatureName(), k -> new ArrayList<>())
                                     .add(baseline);
                    });
                }
            });
        });
        
        // 为每个指标生成组织级基线
        metricBaselines.forEach((metric, baselines) -> {
            if (baselines.size() >= 3) { // 需要足够的样本
                createOrgBaseline(customerId, metric, baselines);
            }
        });
    }

    private void createOrgBaseline(Long customerId, String metric, List<HealthBaseline> userBaselines) {
        // 计算组织级统计数据
        List<Double> means = userBaselines.stream()
            .map(b -> b.getMeanValue().doubleValue())
            .collect(Collectors.toList());
        
        BaselineStatistics orgStats = calculateStatistics(means);
        
        // 创建组织基线
        HealthBaseline orgBaseline = new HealthBaseline();
        orgBaseline.setUserId(0L); // 组织级基线用户ID为0
        orgBaseline.setCustomerId(customerId);
        orgBaseline.setFeatureName(metric);
        orgBaseline.setBaselineDate(LocalDate.now());
        orgBaseline.setBaselineType("org");
        orgBaseline.setMeanValue(BigDecimal.valueOf(orgStats.getMean()).setScale(2, RoundingMode.HALF_UP));
        orgBaseline.setStdValue(BigDecimal.valueOf(orgStats.getStd()).setScale(2, RoundingMode.HALF_UP));
        orgBaseline.setMinValue(BigDecimal.valueOf(orgStats.getMin()));
        orgBaseline.setMaxValue(BigDecimal.valueOf(orgStats.getMax()));
        orgBaseline.setSampleCount(userBaselines.size());
        orgBaseline.setConfidenceLevel(BigDecimal.valueOf(0.95));
        orgBaseline.setBaselineTime(LocalDate.now());
        orgBaseline.setIsCurrent(1);
        orgBaseline.setIsDeleted(0);
        orgBaseline.setCreateTime(LocalDateTime.now());
        orgBaseline.setUpdateTime(LocalDateTime.now());

        // 更新之前的组织基线
        updatePreviousBaselines("org", 0L, customerId, metric);
        
        healthBaselineMapper.insert(orgBaseline);
        
        log.debug("📊 创建组织基线: metric={}, mean={}, samples={}", 
                metric, orgStats.getMean(), userBaselines.size());
    }

    // 评分汇总方法（类似实现）
    private void aggregateScoreToOrg(Long customerId, Map<Long, Map<String, Object>> departmentResults) {
        log.info("📈 汇总评分到组织级别: customerId={}", customerId);
        // 类似的汇总逻辑...
    }

    private void aggregateBaselineToCustomer(Long customerId, Map<Long, Map<String, Object>> departmentResults) {
        log.info("🏪 汇总基线到租户级别: customerId={}", customerId);
        // 租户级别的汇总逻辑...
    }

    private void aggregateScoreToCustomer(Long customerId, Map<Long, Map<String, Object>> departmentResults) {
        log.info("🏪 汇总评分到租户级别: customerId={}", customerId);
        // 租户级别的汇总逻辑...
    }

    // 内部类定义
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

    private static class UserProfile {
        private String ageGroup;
        private String gender;
        private String positionRiskLevel;

        public String getAgeGroup() { return ageGroup; }
        public void setAgeGroup(String ageGroup) { this.ageGroup = ageGroup; }
        public String getGender() { return gender; }
        public void setGender(String gender) { this.gender = gender; }
        public String getPositionRiskLevel() { return positionRiskLevel; }
        public void setPositionRiskLevel(String positionRiskLevel) { this.positionRiskLevel = positionRiskLevel; }
    }
}