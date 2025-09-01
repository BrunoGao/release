package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.exception.BizException;
import com.ljwx.modules.health.entity.HealthBaseline;
import com.ljwx.modules.health.entity.UserHealthData;
import com.ljwx.modules.health.mapper.HealthBaselineMapper;
import com.ljwx.modules.health.mapper.HealthRecommendationTrackMapper;
import com.ljwx.modules.health.mapper.UserHealthDataMapper;
import com.ljwx.modules.health.service.HealthScoreCalculationService.HealthScoreDetail;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.repository.mapper.TAlertInfoMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 智能健康建议服务
 * 基于AI决策树和专家规则生成个性化健康建议
 */
@Slf4j
@Service
public class HealthRecommendationService {

    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private HealthBaselineMapper healthBaselineMapper;
    
    @Autowired
    private TAlertInfoMapper alertInfoMapper;
    
    @Autowired
    private HealthRecommendationTrackMapper recommendationTrackMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private HealthScoreCalculationService healthScoreCalculationService;

    /**
     * 生成用户个性化健康建议
     * @param userId 用户ID
     * @return 健康建议列表
     */
    public List<HealthRecommendation> generateHealthRecommendations(Long userId) {
        log.info("开始生成用户{}的个性化健康建议", userId);
        
        try {
            // 1. 获取用户信息
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                throw new BizException("用户不存在");
            }

            // 2. 构建用户健康画像
            UserHealthProfileDTO userProfile = buildUserHealthProfile(userId, user);
            
            // 3. 计算健康评分
            HealthScoreDetail healthScore = healthScoreCalculationService.calculateComprehensiveHealthScore(userId, 30);
            
            // 4. 生成建议
            List<HealthRecommendation> recommendations = new ArrayList<>();
            
            // 生理指标建议
            if (healthScore.getPhysiologicalScore().doubleValue() < 70) {
                recommendations.addAll(analyzePhysiologicalIssues(userProfile));
            }
            
            // 行为习惯建议
            if (healthScore.getBehavioralScore().doubleValue() < 75) {
                recommendations.addAll(analyzeBehavioralIssues(userProfile));
            }
            
            // 风险预警建议
            if (healthScore.getRiskFactorScore().doubleValue() < 80) {
                recommendations.addAll(analyzeRiskFactors(userProfile));
            }
            
            // 个性化优先级排序
            List<HealthRecommendation> prioritizedRecommendations = prioritizeRecommendations(recommendations, userProfile);
            
            log.info("用户{}健康建议生成完成，共生成{}条建议", userId, prioritizedRecommendations.size());
            
            return prioritizedRecommendations;
            
        } catch (Exception e) {
            log.error("生成健康建议失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new BizException("生成健康建议失败: " + e.getMessage());
        }
    }

    /**
     * 构建用户健康画像
     */
    private UserHealthProfileDTO buildUserHealthProfile(Long userId, SysUser user) {
        UserHealthProfileDTO profile = new UserHealthProfileDTO();
        profile.setUserId(userId);
        profile.setCustomerId(user.getCustomerId());
        profile.setUserName(user.getUserName());
        profile.setAge(30); // Default age since birthday field is not available
        profile.setGender(user.getGender());
        
        // 获取最近30天健康数据
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
            profile.setSleepHours(calculateAverageInt(healthDataList, data -> data.getSleep()) / 60.0); // 转换为小时
        }
        
        // 获取健康基线
        QueryWrapper<HealthBaseline> baselineQuery = new QueryWrapper<>();
        baselineQuery.eq("user_id", userId)
                    .eq("is_current", 1)
                    .eq("is_deleted", 0);
        List<HealthBaseline> baselines = healthBaselineMapper.selectList(baselineQuery);
        profile.setBaselines(baselines.stream().collect(
            Collectors.toMap(HealthBaseline::getFeatureName, baseline -> baseline)));
        
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
     * 分析生理指标问题
     */
    private List<HealthRecommendation> analyzePhysiologicalIssues(UserHealthProfileDTO profile) {
        List<HealthRecommendation> recommendations = new ArrayList<>();
        
        // 心率异常建议
        if (isHeartRateAbnormal(profile)) {
            recommendations.add(createHeartRateRecommendation(profile));
        }
        
        // 血氧异常建议
        if (isBloodOxygenAbnormal(profile)) {
            recommendations.add(createBloodOxygenRecommendation(profile));
        }
        
        // 血压异常建议
        if (isBloodPressureAbnormal(profile)) {
            recommendations.add(createBloodPressureRecommendation(profile));
        }
        
        // 体温异常建议
        if (isTemperatureAbnormal(profile)) {
            recommendations.add(createTemperatureRecommendation(profile));
        }
        
        return recommendations;
    }

    /**
     * 分析行为习惯问题
     */
    private List<HealthRecommendation> analyzeBehavioralIssues(UserHealthProfileDTO profile) {
        List<HealthRecommendation> recommendations = new ArrayList<>();
        
        // 运动不足建议
        if (profile.getDailySteps() < 6000) {
            recommendations.add(createExerciseRecommendation(profile));
        }
        
        // 睡眠问题建议
        if (profile.getSleepHours() < 6 || profile.getSleepHours() > 10) {
            recommendations.add(createSleepRecommendation(profile));
        }
        
        // 压力管理建议
        if (profile.getAvgStress() > 70) {
            recommendations.add(createStressManagementRecommendation(profile));
        }
        
        return recommendations;
    }

    /**
     * 分析风险因子
     */
    private List<HealthRecommendation> analyzeRiskFactors(UserHealthProfileDTO profile) {
        List<HealthRecommendation> recommendations = new ArrayList<>();
        
        // 高频告警建议
        if (profile.getRecentAlerts().size() > 5) {
            recommendations.add(createAlertFrequencyRecommendation(profile));
        }
        
        // 年龄相关建议
        if (profile.getAge() > 60) {
            recommendations.add(createSeniorHealthRecommendation(profile));
        }
        
        return recommendations;
    }

    /**
     * 建议优先级排序
     */
    private List<HealthRecommendation> prioritizeRecommendations(
            List<HealthRecommendation> recommendations, UserHealthProfileDTO profile) {
        
        // 根据紧急程度和用户特征排序
        return recommendations.stream()
            .sorted((r1, r2) -> {
                // 首先按紧急程度排序
                int priorityCompare = r1.getPriority().compareTo(r2.getPriority());
                if (priorityCompare != 0) return priorityCompare;
                
                // 然后按可行性排序
                return Double.compare(r2.getFeasibility(), r1.getFeasibility());
            })
            .limit(8) // 限制建议数量
            .collect(Collectors.toList());
    }

    // 具体建议创建方法

    private HealthRecommendation createHeartRateRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("physiological");
        recommendation.setType("heart_rate");
        
        if (profile.getAvgHeartRate() > getHeartRateUpperBound(profile)) {
            recommendation.setPriority(Priority.HIGH);
            recommendation.setTitle("心率偏高警示");
            recommendation.setDescription("您的平均心率超出正常范围，建议减少剧烈运动，保持充足休息。");
            recommendation.setActions(Arrays.asList(
                "避免过度劳累和精神紧张",
                "保持规律作息，充足睡眠",
                "如持续异常，建议及时就医检查"
            ));
            recommendation.setTimeline("立即执行");
            recommendation.setFeasibility(0.8);
        } else if (profile.getAvgHeartRate() < getHeartRateLowerBound(profile)) {
            recommendation.setPriority(Priority.MEDIUM);
            recommendation.setTitle("心率偏低提醒");
            recommendation.setDescription("您的平均心率较低，建议适当增加有氧运动。");
            recommendation.setActions(Arrays.asList(
                "每日进行30分钟有氧运动",
                "监测运动时心率变化",
                "如伴有其他症状，建议咨询医生"
            ));
            recommendation.setTimeline("2-4周改善计划");
            recommendation.setFeasibility(0.9);
        }
        
        return recommendation;
    }

    private HealthRecommendation createBloodOxygenRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("physiological");
        recommendation.setType("blood_oxygen");
        recommendation.setPriority(Priority.HIGH);
        recommendation.setTitle("血氧饱和度偏低");
        recommendation.setDescription("血氧饱和度低于正常值，建议增加有氧运动，改善呼吸系统功能。");
        recommendation.setActions(Arrays.asList(
            "每日进行30分钟有氧运动",
            "保持室内空气流通",
            "戒烟限酒，避免呼吸道刺激",
            "深呼吸练习，增强肺功能"
        ));
        recommendation.setTimeline("2-4周改善计划");
        recommendation.setFeasibility(0.7);
        return recommendation;
    }

    private HealthRecommendation createBloodPressureRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("physiological");
        recommendation.setType("blood_pressure");
        recommendation.setPriority(Priority.HIGH);
        recommendation.setTitle("血压异常管理");
        recommendation.setDescription("血压指标异常，建议调整生活方式并密切监测。");
        recommendation.setActions(Arrays.asList(
            "低盐低脂饮食，控制钠摄入",
            "适量运动，避免过度激烈运动",
            "保持心情愉悦，减少压力",
            "定期监测血压变化",
            "必要时咨询心血管专科医生"
        ));
        recommendation.setTimeline("持续执行");
        recommendation.setFeasibility(0.6);
        return recommendation;
    }

    private HealthRecommendation createTemperatureRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("physiological");
        recommendation.setType("temperature");
        recommendation.setPriority(Priority.MEDIUM);
        recommendation.setTitle("体温调节建议");
        recommendation.setDescription("体温略有异常，建议注意环境温度和身体状态。");
        recommendation.setActions(Arrays.asList(
            "注意保暖或降温",
            "多喝温水，保持身体水分",
            "观察是否有其他症状",
            "体温持续异常请及时就医"
        ));
        recommendation.setTimeline("即时关注");
        recommendation.setFeasibility(0.9);
        return recommendation;
    }

    private HealthRecommendation createExerciseRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("behavioral");
        recommendation.setType("exercise");
        recommendation.setPriority(Priority.MEDIUM);
        recommendation.setTitle("增加运动量");
        recommendation.setDescription("您的日常活动量偏低，建议增加体育锻炼。");
        
        // 根据年龄调整运动建议
        if (profile.getAge() > 60) {
            recommendation.setActions(Arrays.asList(
                "每日快走30分钟",
                "进行适量的柔韧性练习",
                "太极拳或瑜伽等温和运动",
                "避免过于激烈的运动"
            ));
        } else {
            recommendation.setActions(Arrays.asList(
                "每日步行8000步以上",
                "每周3-4次有氧运动",
                "适量力量训练",
                "选择喜欢的运动项目持之以恒"
            ));
        }
        
        recommendation.setTimeline("逐步增加，4-6周见效");
        recommendation.setFeasibility(0.8);
        return recommendation;
    }

    private HealthRecommendation createSleepRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("behavioral");
        recommendation.setType("sleep");
        recommendation.setPriority(Priority.HIGH);
        recommendation.setTitle("改善睡眠质量");
        recommendation.setDescription("您的睡眠时间不在理想范围内，建议调整睡眠习惯。");
        recommendation.setActions(Arrays.asList(
            "保持规律的作息时间",
            "睡前1小时避免电子设备",
            "创造舒适的睡眠环境",
            "避免睡前饮用咖啡和酒精",
            "适当放松练习如冥想"
        ));
        recommendation.setTimeline("1-2周调整适应");
        recommendation.setFeasibility(0.7);
        return recommendation;
    }

    private HealthRecommendation createStressManagementRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("behavioral");
        recommendation.setType("stress");
        recommendation.setPriority(Priority.MEDIUM);
        recommendation.setTitle("压力管理");
        recommendation.setDescription("您的压力水平较高，建议学习压力管理技巧。");
        recommendation.setActions(Arrays.asList(
            "学习深呼吸和冥想技巧",
            "培养兴趣爱好，转移注意力",
            "适当社交，寻求支持",
            "合理安排工作和休息时间",
            "必要时寻求专业心理帮助"
        ));
        recommendation.setTimeline("持续改善");
        recommendation.setFeasibility(0.6);
        return recommendation;
    }

    private HealthRecommendation createAlertFrequencyRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("risk_factor");
        recommendation.setType("alert_frequency");
        recommendation.setPriority(Priority.HIGH);
        recommendation.setTitle("频繁健康告警处理");
        recommendation.setDescription("您近期健康告警频繁，建议全面健康检查。");
        recommendation.setActions(Arrays.asList(
            "预约全面健康体检",
            "详细记录症状和触发条件",
            "咨询专业医生意见",
            "加强日常健康监测",
            "调整生活方式和工作强度"
        ));
        recommendation.setTimeline("1周内安排检查");
        recommendation.setFeasibility(0.5);
        return recommendation;
    }

    private HealthRecommendation createSeniorHealthRecommendation(UserHealthProfileDTO profile) {
        HealthRecommendation recommendation = new HealthRecommendation();
        recommendation.setCategory("risk_factor");
        recommendation.setType("senior_care");
        recommendation.setPriority(Priority.MEDIUM);
        recommendation.setTitle("老年健康管理");
        recommendation.setDescription("考虑到您的年龄，建议加强健康管理和定期检查。");
        recommendation.setActions(Arrays.asList(
            "每半年进行一次体检",
            "关注心血管和骨骼健康",
            "保持社交活动和脑力锻炼",
            "合理营养搭配，注意钙质补充",
            "建立紧急联系机制"
        ));
        recommendation.setTimeline("长期执行");
        recommendation.setFeasibility(0.7);
        return recommendation;
    }

    // 辅助方法

    private boolean isHeartRateAbnormal(UserHealthProfileDTO profile) {
        if (profile.getAvgHeartRate() == 0) return false;
        double lower = getHeartRateLowerBound(profile);
        double upper = getHeartRateUpperBound(profile);
        return profile.getAvgHeartRate() < lower || profile.getAvgHeartRate() > upper;
    }

    private boolean isBloodOxygenAbnormal(UserHealthProfileDTO profile) {
        return profile.getAvgBloodOxygen() > 0 && profile.getAvgBloodOxygen() < 95;
    }

    private boolean isBloodPressureAbnormal(UserHealthProfileDTO profile) {
        return profile.getAvgPressureHigh() > 140 || profile.getAvgPressureHigh() < 90 ||
               profile.getAvgPressureLow() > 90 || profile.getAvgPressureLow() < 60;
    }

    private boolean isTemperatureAbnormal(UserHealthProfileDTO profile) {
        return profile.getAvgTemperature() < 36.0 || profile.getAvgTemperature() > 37.5;
    }

    private double getHeartRateUpperBound(UserHealthProfileDTO profile) {
        // 根据年龄计算心率上限
        return 220 - profile.getAge();
    }

    private double getHeartRateLowerBound(UserHealthProfileDTO profile) {
        // 一般成年人静息心率下限
        return profile.getAge() > 60 ? 50 : 60;
    }

    private int calculateAge(LocalDate birthday) {
        if (birthday == null) return 30; // 默认年龄
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

    // 内部类定义

    public static class UserHealthProfileDTO {
        private Long userId;
        private Long customerId;
        private String userName;
        private int age;
        private String gender;
        private double avgHeartRate;
        private double avgBloodOxygen;
        private double avgPressureHigh;
        private double avgPressureLow;
        private double avgTemperature;
        private double avgStress;
        private int dailySteps;
        private double sleepHours;
        private List<UserHealthData> recentHealthData;
        private Map<String, HealthBaseline> baselines;
        private List<TAlertInfo> recentAlerts;

        // Getters and Setters
        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        
        public Long getCustomerId() { return customerId; }
        public void setCustomerId(Long customerId) { this.customerId = customerId; }
        
        public String getUserName() { return userName; }
        public void setUserName(String userName) { this.userName = userName; }
        
        public int getAge() { return age; }
        public void setAge(int age) { this.age = age; }
        
        public String getGender() { return gender; }
        public void setGender(String gender) { this.gender = gender; }
        
        public double getAvgHeartRate() { return avgHeartRate; }
        public void setAvgHeartRate(double avgHeartRate) { this.avgHeartRate = avgHeartRate; }
        
        public double getAvgBloodOxygen() { return avgBloodOxygen; }
        public void setAvgBloodOxygen(double avgBloodOxygen) { this.avgBloodOxygen = avgBloodOxygen; }
        
        public double getAvgPressureHigh() { return avgPressureHigh; }
        public void setAvgPressureHigh(double avgPressureHigh) { this.avgPressureHigh = avgPressureHigh; }
        
        public double getAvgPressureLow() { return avgPressureLow; }
        public void setAvgPressureLow(double avgPressureLow) { this.avgPressureLow = avgPressureLow; }
        
        public double getAvgTemperature() { return avgTemperature; }
        public void setAvgTemperature(double avgTemperature) { this.avgTemperature = avgTemperature; }
        
        public double getAvgStress() { return avgStress; }
        public void setAvgStress(double avgStress) { this.avgStress = avgStress; }
        
        public int getDailySteps() { return dailySteps; }
        public void setDailySteps(int dailySteps) { this.dailySteps = dailySteps; }
        
        public double getSleepHours() { return sleepHours; }
        public void setSleepHours(double sleepHours) { this.sleepHours = sleepHours; }
        
        public List<UserHealthData> getRecentHealthData() { return recentHealthData; }
        public void setRecentHealthData(List<UserHealthData> recentHealthData) { this.recentHealthData = recentHealthData; }
        
        public Map<String, HealthBaseline> getBaselines() { return baselines; }
        public void setBaselines(Map<String, HealthBaseline> baselines) { this.baselines = baselines; }
        
        public List<TAlertInfo> getRecentAlerts() { return recentAlerts; }
        public void setRecentAlerts(List<TAlertInfo> recentAlerts) { this.recentAlerts = recentAlerts; }
    }

    public static class HealthRecommendation {
        private String category;
        private String type;
        private Priority priority;
        private String title;
        private String description;
        private List<String> actions;
        private String timeline;
        private double feasibility;

        // Getters and Setters
        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        
        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        
        public Priority getPriority() { return priority; }
        public void setPriority(Priority priority) { this.priority = priority; }
        
        public String getTitle() { return title; }
        public void setTitle(String title) { this.title = title; }
        
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        
        public List<String> getActions() { return actions; }
        public void setActions(List<String> actions) { this.actions = actions; }
        
        public String getTimeline() { return timeline; }
        public void setTimeline(String timeline) { this.timeline = timeline; }
        
        public double getFeasibility() { return feasibility; }
        public void setFeasibility(double feasibility) { this.feasibility = feasibility; }
    }

    public enum Priority {
        LOW(3), MEDIUM(2), HIGH(1), CRITICAL(0);
        
        private final int value;
        
        Priority(int value) {
            this.value = value;
        }
        
        public int getValue() { return value; }
    }
}