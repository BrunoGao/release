package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.*;
import com.ljwx.modules.health.mapper.*;
import com.ljwx.modules.health.service.HealthScoreCalculationService.HealthScoreDetail;
import com.ljwx.modules.health.service.HealthRecommendationService.HealthRecommendation;
import com.ljwx.modules.health.service.HealthRecommendationService.UserHealthProfileDTO;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.repository.mapper.TAlertInfoMapper;
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
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 综合健康画像服务
 * 整合基线、评分、建议，生成完整的用户健康画像
 */
@Slf4j
@Service
public class HealthProfileService {

    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private TAlertInfoMapper alertInfoMapper;
    
    @Autowired
    private UserHealthProfileMapper userHealthProfileMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private HealthScoreCalculationService healthScoreService;
    
    @Autowired
    private HealthRecommendationService healthRecommendationService;
    
    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;

    /**
     * 生成用户综合健康画像
     * @param userId 用户ID
     * @return 综合健康画像
     */
    @Transactional
    public ComprehensiveHealthProfile generateComprehensiveHealthProfile(Long userId) {
        log.info("开始生成用户{}的综合健康画像", userId);
        
        try {
            // 1. 获取用户基本信息
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                throw new BizException("用户不存在");
            }

            // 2. 构建基础用户画像
            UserHealthProfileDTO userProfile = buildUserProfile(userId, user);
            
            // 3. 计算健康评分
            HealthScoreDetail healthScore = healthScoreService.calculateComprehensiveHealthScore(userId, 30);
            
            // 4. 生成个性化建议
            List<HealthRecommendation> recommendations = healthRecommendationService.generateHealthRecommendations(userId);
            
            // 5. 分析健康趋势
            HealthTrendAnalysis trendAnalysis = analyzeHealthTrends(userId);
            
            // 6. 风险评估
            RiskAssessment riskAssessment = assessHealthRisks(userProfile, healthScore);
            
            // 7. 生成可视化数据
            VisualizationData visualizationData = createVisualizationData(userProfile, healthScore, trendAnalysis);
            
            // 8. 构建综合健康画像
            ComprehensiveHealthProfile profile = new ComprehensiveHealthProfile();
            profile.setProfileId(generateProfileId(userId));
            profile.setGenerationDate(LocalDateTime.now());
            profile.setUserId(userId);
            profile.setCustomerId(user.getCustomerId());
            profile.setUserBasicInfo(createBasicInfo(user));
            profile.setCurrentHealthStatus(createCurrentHealthStatus(healthScore));
            profile.setHealthMetricsAnalysis(createHealthMetricsAnalysis(userProfile, healthScore));
            profile.setBehavioralAnalysis(createBehavioralAnalysis(userProfile));
            profile.setRiskAssessment(riskAssessment);
            profile.setHealthTrends(trendAnalysis);
            profile.setPersonalizedRecommendations(recommendations);
            profile.setHealthGoals(generatePersonalizedGoals(userProfile, healthScore));
            profile.setMonitoringPlan(createMonitoringPlan(userProfile, riskAssessment));
            profile.setVisualizationData(visualizationData);
            
            // 9. 保存健康画像到数据库
            saveHealthProfileToDB(profile);
            
            log.info("用户{}的综合健康画像生成完成", userId);
            
            return profile;
            
        } catch (Exception e) {
            log.error("生成综合健康画像失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("生成综合健康画像失败: " + e.getMessage());
        }
    }

    /**
     * 构建用户基础画像
     */
    private UserHealthProfileDTO buildUserProfile(Long userId, SysUser user) {
        UserHealthProfileDTO profile = new UserHealthProfileDTO();
        profile.setUserId(userId);
        profile.setCustomerId(user.getCustomerId());
        profile.setUserName(user.getUserName());
        profile.setAge(30); // Default age since birthday field is not available
        profile.setGender(user.getGender());
        
        // 获取健康数据
        LocalDateTime endTime = LocalDateTime.now();
        LocalDateTime startTime = endTime.minusDays(30);
        
        QueryWrapper<UserHealthData> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId)
                   .ge("timestamp", startTime)
                   .le("timestamp", endTime)
                   .eq("is_deleted", 0)
                   .orderByDesc("timestamp");
        
        List<UserHealthData> healthDataList = userHealthDataMapper.selectList(queryWrapper);
        profile.setRecentHealthData(healthDataList);
        
        // 计算平均指标
        if (!healthDataList.isEmpty()) {
            profile.setAvgHeartRate(calculateAverage(healthDataList, data -> data.getHeartRate()));
            profile.setAvgBloodOxygen(calculateAverage(healthDataList, data -> data.getBloodOxygen()));
            profile.setAvgPressureHigh(calculateAverage(healthDataList, data -> data.getPressureHigh()));
            profile.setAvgPressureLow(calculateAverage(healthDataList, data -> data.getPressureLow()));
            profile.setAvgTemperature(calculateAverageDecimal(healthDataList, data -> data.getTemperature()));
            profile.setAvgStress(calculateAverage(healthDataList, data -> data.getStress()));
            profile.setDailySteps(calculateAverageInt(healthDataList, data -> data.getStep()));
            profile.setSleepHours(calculateAverageInt(healthDataList, data -> data.getSleep()) / 60.0);
        }
        
        // 获取告警历史
        QueryWrapper<TAlertInfo> alertQuery = new QueryWrapper<>();
        alertQuery.eq("user_id", userId)
                 .ge("occur_at", startTime)
                 .eq("is_deleted", 0)
                 .orderByDesc("occur_at");
        List<TAlertInfo> alerts = alertInfoMapper.selectList(alertQuery);
        profile.setRecentAlerts(alerts);
        
        return profile;
    }

    /**
     * 分析健康趋势
     */
    private HealthTrendAnalysis analyzeHealthTrends(Long userId) {
        LocalDateTime endTime = LocalDateTime.now();
        LocalDateTime startTime = endTime.minusDays(180); // 6个月数据
        
        // 使用统一查询服务获取趋势分析数据
        UnifiedHealthQueryDTO trendQuery = new UnifiedHealthQueryDTO();
        // 从用户服务获取customerId
        SysUser userForTrend = sysUserService.getById(userId);
        Long customerId = userForTrend != null ? userForTrend.getCustomerId() : 0L;
        trendQuery.setCustomerId(customerId);
        trendQuery.setUserId(userId);
        trendQuery.setStartDate(startTime);
        trendQuery.setEndDate(endTime);
        trendQuery.setPageSize(10000); // 趋势分析需要大量数据
        trendQuery.setEnableSharding(true); // 跨月查询需要分表支持
        trendQuery.setOrderBy("timestamp");
        trendQuery.setOrderDirection("asc");
        
        Map<String, Object> trendResult = unifiedQueryService.queryHealthData(trendQuery);
        List<UserHealthData> historicalData = (List<UserHealthData>) trendResult.get("data");
        
        HealthTrendAnalysis analysis = new HealthTrendAnalysis();
        
        // 分析各指标趋势
        Map<String, TrendInfo> trends = new HashMap<>();
        
        trends.put("heart_rate", analyzeTrend(historicalData, "heart_rate"));
        trends.put("blood_oxygen", analyzeTrend(historicalData, "blood_oxygen"));
        trends.put("pressure_high", analyzeTrend(historicalData, "pressure_high"));
        trends.put("pressure_low", analyzeTrend(historicalData, "pressure_low"));
        trends.put("temperature", analyzeTrend(historicalData, "temperature"));
        trends.put("stress", analyzeTrend(historicalData, "stress"));
        trends.put("steps", analyzeTrend(historicalData, "steps"));
        trends.put("sleep", analyzeTrend(historicalData, "sleep"));
        
        analysis.setTrends(trends);
        analysis.setAnalysisPeriod(180);
        analysis.setDataPoints(historicalData.size());
        
        return analysis;
    }

    /**
     * 健康风险评估
     */
    private RiskAssessment assessHealthRisks(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        RiskAssessment assessment = new RiskAssessment();
        
        // 当前风险等级评估
        String currentRiskLevel = determineCurrentRiskLevel(healthScore);
        assessment.setCurrentRiskLevel(currentRiskLevel);
        
        // 未来风险预测
        double predictedRiskScore = predictFutureRisk(profile, healthScore);
        assessment.setPredictedRiskScore(BigDecimal.valueOf(predictedRiskScore).setScale(2, RoundingMode.HALF_UP));
        
        // 风险因子识别
        List<RiskFactor> riskFactors = identifyRiskFactors(profile, healthScore);
        assessment.setRiskFactors(riskFactors);
        
        // 保护因子识别
        List<ProtectiveFactor> protectiveFactors = identifyProtectiveFactors(profile, healthScore);
        assessment.setProtectiveFactors(protectiveFactors);
        
        // 重点关注事项
        List<String> immediateConcerns = identifyImmediateConcerns(profile, healthScore);
        assessment.setImmediateConcerns(immediateConcerns);
        
        return assessment;
    }

    /**
     * 创建可视化数据
     */
    private VisualizationData createVisualizationData(UserHealthProfileDTO profile, 
            HealthScoreDetail healthScore, HealthTrendAnalysis trendAnalysis) {
        
        VisualizationData data = new VisualizationData();
        
        // 雷达图数据：多维度健康指标
        RadarChartData radarData = new RadarChartData();
        radarData.setDimensions(Arrays.asList("心血管", "呼吸系统", "代谢功能", "心理健康", "运动能力", "睡眠质量"));
        
        List<Double> values = Arrays.asList(
            healthScore.getCardiovascularScore().doubleValue(),
            healthScore.getRespiratoryScore().doubleValue(),
            healthScore.getMetabolicScore().doubleValue(),
            healthScore.getPsychologicalScore().doubleValue(),
            calculateActivityScore(profile),
            calculateSleepScore(profile)
        );
        radarData.setValues(values);
        data.setRadarChart(radarData);
        
        // 趋势图数据
        Map<String, TrendChartData> trendCharts = new HashMap<>();
        for (Map.Entry<String, TrendInfo> entry : trendAnalysis.getTrends().entrySet()) {
            TrendChartData trendChart = new TrendChartData();
            trendChart.setDirection(entry.getValue().getDirection());
            trendChart.setStrength(entry.getValue().getStrength());
            trendChart.setStability(entry.getValue().getStability());
            trendCharts.put(entry.getKey(), trendChart);
        }
        data.setTrendCharts(trendCharts);
        
        // 风险热力图数据
        RiskHeatmapData heatmapData = new RiskHeatmapData();
        // 这里可以添加具体的热力图数据实现
        data.setRiskHeatmap(heatmapData);
        
        // 摘要指标
        SummaryMetrics summaryMetrics = createSummaryMetrics(healthScore, profile);
        data.setSummaryMetrics(summaryMetrics);
        
        return data;
    }

    /**
     * 分析指标趋势
     */
    private TrendInfo analyzeTrend(List<UserHealthData> data, String metric) {
        if (data.size() < 3) {
            return new TrendInfo("stable", 0.0, 1.0, 0);
        }
        
        // 提取指标值
        List<Double> values = new ArrayList<>();
        for (UserHealthData item : data) {
            Double value = extractMetricValue(item, metric);
            if (value != null && value > 0) {
                values.add(value);
            }
        }
        
        if (values.size() < 3) {
            return new TrendInfo("stable", 0.0, 1.0, 0);
        }
        
        // 计算线性趋势斜率
        double slope = calculateTrendSlope(values);
        
        // 计算稳定性（标准差的倒数）
        double mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        double variance = values.stream().mapToDouble(v -> Math.pow(v - mean, 2)).average().orElse(0.0);
        double stability = variance > 0 ? 1.0 / Math.sqrt(variance) : 1.0;
        
        // 检测异常点
        int anomalies = detectAnomalies(values);
        
        // 确定趋势方向
        String direction;
        if (Math.abs(slope) < 0.01) {
            direction = "stable";
        } else if (slope > 0) {
            direction = "improving";
        } else {
            direction = "deteriorating";
        }
        
        return new TrendInfo(direction, Math.abs(slope), stability, anomalies);
    }

    /**
     * 生成个性化目标
     */
    private List<HealthGoal> generatePersonalizedGoals(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        List<HealthGoal> goals = new ArrayList<>();
        
        // 基于当前评分设定改进目标
        if (healthScore.getPhysiologicalScore().doubleValue() < 80) {
            goals.add(new HealthGoal("physiological", "提升生理指标", 
                "在2个月内将生理指标评分提升到80分以上", 
                LocalDate.now().plusMonths(2), "pending"));
        }
        
        if (healthScore.getBehavioralScore().doubleValue() < 75) {
            goals.add(new HealthGoal("behavioral", "改善行为习惯", 
                "建立规律的运动和睡眠习惯，评分达到75分以上", 
                LocalDate.now().plusMonths(3), "pending"));
        }
        
        // 基于年龄设定预防性目标
        if (profile.getAge() > 50) {
            goals.add(new HealthGoal("preventive", "预防慢性疾病", 
                "定期体检，维持心血管和代谢指标在正常范围", 
                LocalDate.now().plusMonths(6), "pending"));
        }
        
        // 基于日常活动设定目标
        if (profile.getDailySteps() < 8000) {
            goals.add(new HealthGoal("activity", "增加日常活动", 
                "日均步数达到8000步以上", 
                LocalDate.now().plusMonths(1), "pending"));
        }
        
        return goals;
    }

    /**
     * 创建监测计划
     */
    private MonitoringPlan createMonitoringPlan(UserHealthProfileDTO profile, RiskAssessment riskAssessment) {
        MonitoringPlan plan = new MonitoringPlan();
        
        // 基于风险等级制定监测频率
        String riskLevel = riskAssessment.getCurrentRiskLevel();
        
        Map<String, Integer> monitoringFrequency = new HashMap<>();
        if ("high".equals(riskLevel) || "critical".equals(riskLevel)) {
            monitoringFrequency.put("vital_signs", 2); // 每天2次
            monitoringFrequency.put("activity", 1); // 每天1次
            monitoringFrequency.put("sleep", 1); // 每天1次
            plan.setCheckupInterval(30); // 30天体检一次
        } else if ("medium".equals(riskLevel)) {
            monitoringFrequency.put("vital_signs", 1); // 每天1次
            monitoringFrequency.put("activity", 1); // 每天1次
            monitoringFrequency.put("sleep", 1); // 每天1次
            plan.setCheckupInterval(90); // 90天体检一次
        } else {
            monitoringFrequency.put("vital_signs", 1); // 每2天1次
            monitoringFrequency.put("activity", 1); // 每天1次
            monitoringFrequency.put("sleep", 1); // 每天1次
            plan.setCheckupInterval(180); // 180天体检一次
        }
        
        plan.setMonitoringFrequency(monitoringFrequency);
        plan.setKeyMetrics(Arrays.asList("heart_rate", "blood_pressure", "blood_oxygen", "steps", "sleep"));
        plan.setAlertThresholds(createAlertThresholds(profile));
        
        return plan;
    }

    // 保存健康画像到数据库
    @Transactional
    private void saveHealthProfileToDB(ComprehensiveHealthProfile profile) {
        // 先查询是否存在当日的画像记录
        QueryWrapper<UserHealthProfile> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", profile.getUserId())
                   .eq("profile_date", LocalDate.now())
                   .eq("is_deleted", 0);
        
        UserHealthProfile existingProfile = userHealthProfileMapper.selectOne(queryWrapper);
        
        UserHealthProfile dbProfile;
        if (existingProfile != null) {
            dbProfile = existingProfile;
        } else {
            dbProfile = new UserHealthProfile();
            dbProfile.setUserId(profile.getUserId());
            dbProfile.setCustomerId(profile.getCustomerId());
            dbProfile.setProfileDate(LocalDate.now());
        }
        
        // 设置评分数据
        HealthScoreDetail score = (HealthScoreDetail) profile.getCurrentHealthStatus().get("health_score");
        if (score != null) {
            dbProfile.setOverallHealthScore(score.getTotalScore());
            dbProfile.setPhysiologicalScore(score.getPhysiologicalScore());
            dbProfile.setBehavioralScore(score.getBehavioralScore());
            dbProfile.setRiskFactorScore(score.getRiskFactorScore());
            dbProfile.setCardiovascularScore(score.getCardiovascularScore());
            dbProfile.setRespiratoryScore(score.getRespiratoryScore());
            dbProfile.setMetabolicScore(score.getMetabolicScore());
            dbProfile.setPsychologicalScore(score.getPsychologicalScore());
            dbProfile.setHealthLevel(score.getScoreLevel());
        }
        
        // 设置风险评估
        RiskAssessment risk = profile.getRiskAssessment();
        if (risk != null) {
            dbProfile.setCurrentRiskLevel(risk.getCurrentRiskLevel());
            dbProfile.setPredictedRiskScore(risk.getPredictedRiskScore());
        }
        
        // 设置JSON扩展字段
        Map<String, Object> detailedAnalysis = new HashMap<>();
        detailedAnalysis.put("health_metrics", profile.getHealthMetricsAnalysis());
        detailedAnalysis.put("behavioral_analysis", profile.getBehavioralAnalysis());
        
        Map<String, Object> trendAnalysisMap = new HashMap<>();
        trendAnalysisMap.put("trends", profile.getHealthTrends());
        
        Map<String, Object> recommendationsMap = new HashMap<>();
        recommendationsMap.put("recommendations", profile.getPersonalizedRecommendations());
        recommendationsMap.put("goals", profile.getHealthGoals());
        recommendationsMap.put("monitoring_plan", profile.getMonitoringPlan());
        
        // 保存或更新记录
        if (existingProfile != null) {
            userHealthProfileMapper.updateById(dbProfile);
            log.info("更新用户{}的健康画像记录", profile.getUserId());
        } else {
            userHealthProfileMapper.insert(dbProfile);
            log.info("创建用户{}的健康画像记录", profile.getUserId());
        }
    }

    // 辅助方法实现

    private String generateProfileId(Long userId) {
        return "HP_" + userId + "_" + LocalDate.now().toString().replace("-", "");
    }

    private int calculateAge(LocalDate birthday) {
        if (birthday == null) return 30;
        return Period.between(birthday, LocalDate.now()).getYears();
    }

    private double calculateAverage(List<UserHealthData> dataList, java.util.function.Function<UserHealthData, Integer> extractor) {
        return dataList.stream()
            .filter(data -> extractor.apply(data) != null && extractor.apply(data) > 0)
            .mapToInt(data -> extractor.apply(data))
            .average()
            .orElse(0.0);
    }

    private double calculateAverageDecimal(List<UserHealthData> dataList, java.util.function.Function<UserHealthData, java.math.BigDecimal> extractor) {
        return dataList.stream()
            .filter(data -> extractor.apply(data) != null && extractor.apply(data).doubleValue() > 0)
            .mapToDouble(data -> extractor.apply(data).doubleValue())
            .average()
            .orElse(0.0);
    }

    private int calculateAverageInt(List<UserHealthData> dataList, java.util.function.Function<UserHealthData, Integer> extractor) {
        return (int) dataList.stream()
            .filter(data -> extractor.apply(data) != null && extractor.apply(data) > 0)
            .mapToInt(data -> extractor.apply(data))
            .average()
            .orElse(0.0);
    }

    private Double extractMetricValue(UserHealthData data, String metric) {
        switch (metric) {
            case "heart_rate":
                return data.getHeartRate() != null ? data.getHeartRate().doubleValue() : null;
            case "blood_oxygen":
                return data.getBloodOxygen() != null ? data.getBloodOxygen().doubleValue() : null;
            case "pressure_high":
                return data.getPressureHigh() != null ? data.getPressureHigh().doubleValue() : null;
            case "pressure_low":
                return data.getPressureLow() != null ? data.getPressureLow().doubleValue() : null;
            case "temperature":
                return data.getTemperature() != null ? data.getTemperature().doubleValue() : null;
            case "stress":
                return data.getStress() != null ? data.getStress().doubleValue() : null;
            case "steps":
                return data.getStep() != null ? data.getStep().doubleValue() : null;
            case "sleep":
                return data.getSleep() != null ? data.getSleep().doubleValue() : null;
            default:
                return null;
        }
    }

    private double calculateTrendSlope(List<Double> values) {
        if (values.size() < 2) return 0.0;
        
        int n = values.size();
        double sumX = n * (n - 1) / 2.0; // 0 + 1 + 2 + ... + (n-1)
        double sumY = values.stream().mapToDouble(Double::doubleValue).sum();
        double sumXY = 0.0;
        double sumXX = n * (n - 1) * (2 * n - 1) / 6.0; // 0² + 1² + 2² + ... + (n-1)²
        
        for (int i = 0; i < n; i++) {
            sumXY += i * values.get(i);
        }
        
        double denominator = n * sumXX - sumX * sumX;
        if (denominator == 0) return 0.0;
        
        return (n * sumXY - sumX * sumY) / denominator;
    }

    private int detectAnomalies(List<Double> values) {
        if (values.size() < 3) return 0;
        
        double mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0);
        double std = Math.sqrt(values.stream().mapToDouble(v -> Math.pow(v - mean, 2)).average().orElse(0.0));
        
        if (std == 0) return 0;
        
        int anomalies = 0;
        for (double value : values) {
            if (Math.abs(value - mean) > 2 * std) { // 2σ准则
                anomalies++;
            }
        }
        
        return anomalies;
    }

    private String determineCurrentRiskLevel(HealthScoreDetail healthScore) {
        double totalScore = healthScore.getTotalScore().doubleValue();
        
        if (totalScore >= 85) return "low";
        if (totalScore >= 70) return "medium";
        if (totalScore >= 55) return "high";
        return "critical";
    }

    private double predictFutureRisk(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        // 简化的风险预测模型
        double baseRisk = 100 - healthScore.getTotalScore().doubleValue();
        
        // 年龄因子
        double ageFactor = Math.max(0, (profile.getAge() - 30) * 0.5);
        
        // 告警频率因子
        double alertFactor = Math.min(profile.getRecentAlerts().size() * 2, 20);
        
        return Math.min(baseRisk + ageFactor + alertFactor, 100.0);
    }

    private List<RiskFactor> identifyRiskFactors(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        List<RiskFactor> factors = new ArrayList<>();
        
        if (profile.getAge() > 60) {
            factors.add(new RiskFactor("age", "高龄", "moderate", "年龄超过60岁，需要加强健康监测"));
        }
        
        if (profile.getRecentAlerts().size() > 3) {
            factors.add(new RiskFactor("alert_frequency", "告警频繁", "high", "近期健康告警频繁，需要重点关注"));
        }
        
        if (profile.getAvgPressureHigh() > 140) {
            factors.add(new RiskFactor("hypertension", "高血压风险", "high", "血压偏高，需要控制饮食和运动"));
        }
        
        return factors;
    }

    private List<ProtectiveFactor> identifyProtectiveFactors(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        List<ProtectiveFactor> factors = new ArrayList<>();
        
        if (profile.getDailySteps() >= 8000) {
            factors.add(new ProtectiveFactor("regular_exercise", "规律运动", "每日步数达标，有助于心血管健康"));
        }
        
        if (profile.getSleepHours() >= 7 && profile.getSleepHours() <= 8) {
            factors.add(new ProtectiveFactor("adequate_sleep", "充足睡眠", "睡眠时间理想，有利于身体恢复"));
        }
        
        return factors;
    }

    private List<String> identifyImmediateConcerns(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        List<String> concerns = new ArrayList<>();
        
        if (healthScore.getTotalScore().doubleValue() < 60) {
            concerns.add("综合健康评分较低，建议全面健康检查");
        }
        
        if (profile.getRecentAlerts().stream().anyMatch(alert -> "critical".equals(alert.getLevel()))) {
            concerns.add("近期存在严重健康告警，需要立即关注");
        }
        
        return concerns;
    }

    private double calculateActivityScore(UserHealthProfileDTO profile) {
        return Math.min(profile.getDailySteps() / 8000.0 * 100, 100);
    }

    private double calculateSleepScore(UserHealthProfileDTO profile) {
        double sleepHours = profile.getSleepHours();
        if (sleepHours >= 7 && sleepHours <= 8) {
            return 100.0;
        } else if ((sleepHours >= 6 && sleepHours < 7) || (sleepHours > 8 && sleepHours <= 9)) {
            return 85.0;
        } else {
            return Math.max(70.0 - Math.abs(sleepHours - 7.5) * 10.0, 40.0);
        }
    }

    // 创建各种数据结构的方法
    private Map<String, Object> createBasicInfo(SysUser user) {
        Map<String, Object> basicInfo = new HashMap<>();
        basicInfo.put("user_name", user.getUserName());
        basicInfo.put("age", 30); // Default age since birthday field is not available
        basicInfo.put("gender", user.getGender());
        basicInfo.put("customer_id", user.getCustomerId());
        return basicInfo;
    }

    private Map<String, Object> createCurrentHealthStatus(HealthScoreDetail healthScore) {
        Map<String, Object> status = new HashMap<>();
        status.put("overall_score", healthScore.getTotalScore());
        status.put("health_level", healthScore.getScoreLevel());
        status.put("health_score", healthScore);
        return status;
    }

    private Map<String, Object> createHealthMetricsAnalysis(UserHealthProfileDTO profile, HealthScoreDetail healthScore) {
        Map<String, Object> analysis = new HashMap<>();
        
        Map<String, Object> cardiovascular = new HashMap<>();
        cardiovascular.put("score", healthScore.getCardiovascularScore());
        cardiovascular.put("avg_heart_rate", profile.getAvgHeartRate());
        cardiovascular.put("avg_pressure", Arrays.asList(profile.getAvgPressureHigh(), profile.getAvgPressureLow()));
        
        Map<String, Object> respiratory = new HashMap<>();
        respiratory.put("score", healthScore.getRespiratoryScore());
        respiratory.put("avg_blood_oxygen", profile.getAvgBloodOxygen());
        
        analysis.put("cardiovascular", cardiovascular);
        analysis.put("respiratory", respiratory);
        
        return analysis;
    }

    private Map<String, Object> createBehavioralAnalysis(UserHealthProfileDTO profile) {
        Map<String, Object> behavioral = new HashMap<>();
        behavioral.put("daily_steps", profile.getDailySteps());
        behavioral.put("sleep_hours", profile.getSleepHours());
        behavioral.put("activity_consistency", calculateActivityConsistency(profile));
        return behavioral;
    }

    private SummaryMetrics createSummaryMetrics(HealthScoreDetail healthScore, UserHealthProfileDTO profile) {
        SummaryMetrics metrics = new SummaryMetrics();
        metrics.setOverallScore(healthScore.getTotalScore().doubleValue());
        metrics.setHealthLevel(healthScore.getScoreLevel());
        metrics.setRiskLevel(determineCurrentRiskLevel(healthScore));
        metrics.setDailySteps(profile.getDailySteps());
        metrics.setSleepHours(profile.getSleepHours());
        metrics.setAlertCount(profile.getRecentAlerts().size());
        return metrics;
    }

    private double calculateActivityConsistency(UserHealthProfileDTO profile) {
        // 简化计算，实际可以更复杂
        return profile.getDailySteps() > 5000 ? 0.8 : 0.5;
    }

    private Map<String, Object> createAlertThresholds(UserHealthProfileDTO profile) {
        Map<String, Object> thresholds = new HashMap<>();
        thresholds.put("heart_rate_high", 100 + profile.getAge() * 0.5);
        thresholds.put("heart_rate_low", Math.max(50, 80 - profile.getAge() * 0.2));
        thresholds.put("blood_oxygen_low", 95);
        thresholds.put("pressure_high", 140);
        thresholds.put("pressure_low", 60);
        return thresholds;
    }

    // 内部数据类定义（简化版，实际应该在独立文件中）

    public static class ComprehensiveHealthProfile {
        private String profileId;
        private LocalDateTime generationDate;
        private Long userId;
        private Long customerId;
        private Map<String, Object> userBasicInfo;
        private Map<String, Object> currentHealthStatus;
        private Map<String, Object> healthMetricsAnalysis;
        private Map<String, Object> behavioralAnalysis;
        private RiskAssessment riskAssessment;
        private HealthTrendAnalysis healthTrends;
        private List<HealthRecommendation> personalizedRecommendations;
        private List<HealthGoal> healthGoals;
        private MonitoringPlan monitoringPlan;
        private VisualizationData visualizationData;

        // Getters and Setters
        public String getProfileId() { return profileId; }
        public void setProfileId(String profileId) { this.profileId = profileId; }
        
        public LocalDateTime getGenerationDate() { return generationDate; }
        public void setGenerationDate(LocalDateTime generationDate) { this.generationDate = generationDate; }
        
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public Long getCustomerId() { return customerId; }
        public void setCustomerId(Long customerId) { this.customerId = customerId; }
        
        public Map<String, Object> getUserBasicInfo() { return userBasicInfo; }
        public void setUserBasicInfo(Map<String, Object> userBasicInfo) { this.userBasicInfo = userBasicInfo; }
        
        public Map<String, Object> getCurrentHealthStatus() { return currentHealthStatus; }
        public void setCurrentHealthStatus(Map<String, Object> currentHealthStatus) { this.currentHealthStatus = currentHealthStatus; }
        
        public Map<String, Object> getHealthMetricsAnalysis() { return healthMetricsAnalysis; }
        public void setHealthMetricsAnalysis(Map<String, Object> healthMetricsAnalysis) { this.healthMetricsAnalysis = healthMetricsAnalysis; }
        
        public Map<String, Object> getBehavioralAnalysis() { return behavioralAnalysis; }
        public void setBehavioralAnalysis(Map<String, Object> behavioralAnalysis) { this.behavioralAnalysis = behavioralAnalysis; }
        
        public RiskAssessment getRiskAssessment() { return riskAssessment; }
        public void setRiskAssessment(RiskAssessment riskAssessment) { this.riskAssessment = riskAssessment; }
        
        public HealthTrendAnalysis getHealthTrends() { return healthTrends; }
        public void setHealthTrends(HealthTrendAnalysis healthTrends) { this.healthTrends = healthTrends; }
        
        public List<HealthRecommendation> getPersonalizedRecommendations() { return personalizedRecommendations; }
        public void setPersonalizedRecommendations(List<HealthRecommendation> personalizedRecommendations) { this.personalizedRecommendations = personalizedRecommendations; }
        
        public List<HealthGoal> getHealthGoals() { return healthGoals; }
        public void setHealthGoals(List<HealthGoal> healthGoals) { this.healthGoals = healthGoals; }
        
        public MonitoringPlan getMonitoringPlan() { return monitoringPlan; }
        public void setMonitoringPlan(MonitoringPlan monitoringPlan) { this.monitoringPlan = monitoringPlan; }
        
        public VisualizationData getVisualizationData() { return visualizationData; }
        public void setVisualizationData(VisualizationData visualizationData) { this.visualizationData = visualizationData; }
    }

    // 其他内部类定义...
    public static class HealthTrendAnalysis {
        private Map<String, TrendInfo> trends;
        private int analysisPeriod;
        private int dataPoints;

        public Map<String, TrendInfo> getTrends() { return trends; }
        public void setTrends(Map<String, TrendInfo> trends) { this.trends = trends; }
        
        public int getAnalysisPeriod() { return analysisPeriod; }
        public void setAnalysisPeriod(int analysisPeriod) { this.analysisPeriod = analysisPeriod; }
        
        public int getDataPoints() { return dataPoints; }
        public void setDataPoints(int dataPoints) { this.dataPoints = dataPoints; }
    }

    public static class TrendInfo {
        private String direction;
        private double strength;
        private double stability;
        private int anomalies;

        public TrendInfo(String direction, double strength, double stability, int anomalies) {
            this.direction = direction;
            this.strength = strength;
            this.stability = stability;
            this.anomalies = anomalies;
        }

        public String getDirection() { return direction; }
        public double getStrength() { return strength; }
        public double getStability() { return stability; }
        public int getAnomalies() { return anomalies; }
    }

    public static class RiskAssessment {
        private String currentRiskLevel;
        private BigDecimal predictedRiskScore;
        private List<RiskFactor> riskFactors;
        private List<ProtectiveFactor> protectiveFactors;
        private List<String> immediateConcerns;

        public String getCurrentRiskLevel() { return currentRiskLevel; }
        public void setCurrentRiskLevel(String currentRiskLevel) { this.currentRiskLevel = currentRiskLevel; }
        
        public BigDecimal getPredictedRiskScore() { return predictedRiskScore; }
        public void setPredictedRiskScore(BigDecimal predictedRiskScore) { this.predictedRiskScore = predictedRiskScore; }
        
        public List<RiskFactor> getRiskFactors() { return riskFactors; }
        public void setRiskFactors(List<RiskFactor> riskFactors) { this.riskFactors = riskFactors; }
        
        public List<ProtectiveFactor> getProtectiveFactors() { return protectiveFactors; }
        public void setProtectiveFactors(List<ProtectiveFactor> protectiveFactors) { this.protectiveFactors = protectiveFactors; }
        
        public List<String> getImmediateConcerns() { return immediateConcerns; }
        public void setImmediateConcerns(List<String> immediateConcerns) { this.immediateConcerns = immediateConcerns; }
    }

    public static class RiskFactor {
        private String type;
        private String name;
        private String severity;
        private String description;

        public RiskFactor(String type, String name, String severity, String description) {
            this.type = type;
            this.name = name;
            this.severity = severity;
            this.description = description;
        }

        public String getType() { return type; }
        public String getName() { return name; }
        public String getSeverity() { return severity; }
        public String getDescription() { return description; }
    }

    public static class ProtectiveFactor {
        private String type;
        private String name;
        private String description;

        public ProtectiveFactor(String type, String name, String description) {
            this.type = type;
            this.name = name;
            this.description = description;
        }

        public String getType() { return type; }
        public String getName() { return name; }
        public String getDescription() { return description; }
    }

    public static class HealthGoal {
        private String category;
        private String title;
        private String description;
        private LocalDate targetDate;
        private String status;

        public HealthGoal(String category, String title, String description, LocalDate targetDate, String status) {
            this.category = category;
            this.title = title;
            this.description = description;
            this.targetDate = targetDate;
            this.status = status;
        }

        public String getCategory() { return category; }
        public String getTitle() { return title; }
        public String getDescription() { return description; }
        public LocalDate getTargetDate() { return targetDate; }
        public String getStatus() { return status; }
    }

    public static class MonitoringPlan {
        private Map<String, Integer> monitoringFrequency;
        private List<String> keyMetrics;
        private Map<String, Object> alertThresholds;
        private int checkupInterval;

        public Map<String, Integer> getMonitoringFrequency() { return monitoringFrequency; }
        public void setMonitoringFrequency(Map<String, Integer> monitoringFrequency) { this.monitoringFrequency = monitoringFrequency; }
        
        public List<String> getKeyMetrics() { return keyMetrics; }
        public void setKeyMetrics(List<String> keyMetrics) { this.keyMetrics = keyMetrics; }
        
        public Map<String, Object> getAlertThresholds() { return alertThresholds; }
        public void setAlertThresholds(Map<String, Object> alertThresholds) { this.alertThresholds = alertThresholds; }
        
        public int getCheckupInterval() { return checkupInterval; }
        public void setCheckupInterval(int checkupInterval) { this.checkupInterval = checkupInterval; }
    }

    public static class VisualizationData {
        private RadarChartData radarChart;
        private Map<String, TrendChartData> trendCharts;
        private RiskHeatmapData riskHeatmap;
        private SummaryMetrics summaryMetrics;

        public RadarChartData getRadarChart() { return radarChart; }
        public void setRadarChart(RadarChartData radarChart) { this.radarChart = radarChart; }
        
        public Map<String, TrendChartData> getTrendCharts() { return trendCharts; }
        public void setTrendCharts(Map<String, TrendChartData> trendCharts) { this.trendCharts = trendCharts; }
        
        public RiskHeatmapData getRiskHeatmap() { return riskHeatmap; }
        public void setRiskHeatmap(RiskHeatmapData riskHeatmap) { this.riskHeatmap = riskHeatmap; }
        
        public SummaryMetrics getSummaryMetrics() { return summaryMetrics; }
        public void setSummaryMetrics(SummaryMetrics summaryMetrics) { this.summaryMetrics = summaryMetrics; }
    }

    public static class RadarChartData {
        private List<String> dimensions;
        private List<Double> values;

        public List<String> getDimensions() { return dimensions; }
        public void setDimensions(List<String> dimensions) { this.dimensions = dimensions; }
        
        public List<Double> getValues() { return values; }
        public void setValues(List<Double> values) { this.values = values; }
    }

    public static class TrendChartData {
        private String direction;
        private double strength;
        private double stability;

        public String getDirection() { return direction; }
        public void setDirection(String direction) { this.direction = direction; }
        
        public double getStrength() { return strength; }
        public void setStrength(double strength) { this.strength = strength; }
        
        public double getStability() { return stability; }
        public void setStability(double stability) { this.stability = stability; }
    }

    public static class RiskHeatmapData {
        // 热力图数据结构，可以根据具体需求实现
    }

    public static class SummaryMetrics {
        private double overallScore;
        private String healthLevel;
        private String riskLevel;
        private int dailySteps;
        private double sleepHours;
        private int alertCount;

        public double getOverallScore() { return overallScore; }
        public void setOverallScore(double overallScore) { this.overallScore = overallScore; }
        
        public String getHealthLevel() { return healthLevel; }
        public void setHealthLevel(String healthLevel) { this.healthLevel = healthLevel; }
        
        public String getRiskLevel() { return riskLevel; }
        public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
        
        public int getDailySteps() { return dailySteps; }
        public void setDailySteps(int dailySteps) { this.dailySteps = dailySteps; }
        
        public double getSleepHours() { return sleepHours; }
        public void setSleepHours(double sleepHours) { this.sleepHours = sleepHours; }
        
        public int getAlertCount() { return alertCount; }
        public void setAlertCount(int alertCount) { this.alertCount = alertCount; }
    }
}