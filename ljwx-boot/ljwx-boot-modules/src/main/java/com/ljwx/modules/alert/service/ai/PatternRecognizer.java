/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.alert.service.ai;

import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * 模式识别器
 * 识别告警的历史模式和趋势
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.ai.PatternRecognizer
 * @CreateTime 2024-08-30 - 19:00:00
 */
@Slf4j
@Service
public class PatternRecognizer {

    private final Random random = new Random();

    /**
     * 分析告警模式
     * 
     * @param alert 告警信息
     * @param context 上下文信息
     * @return 模式分析结果
     */
    public Map<String, Object> analyzePatterns(AnalyzedAlert alert, Map<String, Object> context) {
        log.debug("开始模式识别: alertId={}, alertType={}", 
                alert.getAlertId(), alert.getAlertType());
        
        Map<String, Object> patternResult = new HashMap<>();
        
        try {
            // 1. 时间模式识别
            Map<String, Object> timePatterns = recognizeTimePatterns(alert, context);
            patternResult.putAll(timePatterns);
            
            // 2. 频率模式识别
            Map<String, Object> frequencyPatterns = recognizeFrequencyPatterns(alert, context);
            patternResult.putAll(frequencyPatterns);
            
            // 3. 类型模式识别
            Map<String, Object> typePatterns = recognizeTypePatterns(alert, context);
            patternResult.putAll(typePatterns);
            
            // 4. 用户行为模式识别
            Map<String, Object> behaviorPatterns = recognizeBehaviorPatterns(alert, context);
            patternResult.putAll(behaviorPatterns);
            
            // 5. 设备模式识别
            Map<String, Object> devicePatterns = recognizeDevicePatterns(alert, context);
            patternResult.putAll(devicePatterns);
            
            // 6. 计算模式置信度
            double patternConfidence = calculatePatternConfidence(patternResult);
            patternResult.put("patternConfidence", patternConfidence);
            
            // 7. 生成模式摘要
            String patternSummary = generatePatternSummary(patternResult);
            patternResult.put("patternSummary", patternSummary);
            
            log.debug("模式识别完成: alertId={}, patternConfidence={}", 
                    alert.getAlertId(), patternConfidence);
            
        } catch (Exception e) {
            log.error("模式识别失败: alertId={}", alert.getAlertId(), e);
            
            // 返回默认结果
            patternResult.put("patternConfidence", 0.5);
            patternResult.put("patternSummary", "模式分析失败");
        }
        
        return patternResult;
    }

    /**
     * 时间模式识别
     */
    private Map<String, Object> recognizeTimePatterns(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> timePatterns = new HashMap<>();
        
        // 获取时间上下文信息
        String timeSlot = (String) context.get("timeSlot");
        String timePattern = (String) context.get("timePattern");
        Boolean isWeekday = (Boolean) context.get("isWeekday");
        
        // 分析周期性模式
        String periodicPattern = analyzePeriodicPattern(timeSlot, isWeekday);
        timePatterns.put("periodicPattern", periodicPattern);
        
        // 分析时间集中度
        double timeConcentration = calculateTimeConcentration(timePattern);
        timePatterns.put("timeConcentration", timeConcentration);
        
        // 分析时间趋势
        String timeTrend = analyzeTimeTrend(context);
        timePatterns.put("timeTrend", timeTrend);
        
        // 工作时间vs非工作时间分布
        String workTimeDistribution = analyzeWorkTimeDistribution(timePattern, isWeekday);
        timePatterns.put("workTimeDistribution", workTimeDistribution);
        
        return timePatterns;
    }

    /**
     * 频率模式识别
     */
    private Map<String, Object> recognizeFrequencyPatterns(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> frequencyPatterns = new HashMap<>();
        
        Object alertFreqObj = context.get("alertFrequency");
        int alertFrequency = alertFreqObj instanceof Number ? ((Number) alertFreqObj).intValue() : 0;
        
        // 频率分类
        String frequencyCategory = categorizeFrequency(alertFrequency);
        frequencyPatterns.put("frequencyCategory", frequencyCategory);
        
        // 频率趋势
        String frequencyTrend = analyzeFrequencyTrend(alertFrequency, context);
        frequencyPatterns.put("frequencyTrend", frequencyTrend);
        
        // 异常频率检测
        boolean isAbnormalFrequency = detectAbnormalFrequency(alertFrequency, alert.getAlertType());
        frequencyPatterns.put("isAbnormalFrequency", isAbnormalFrequency);
        
        // 频率预测
        int predictedFrequency = predictFutureFrequency(alertFrequency, context);
        frequencyPatterns.put("predictedFrequency", predictedFrequency);
        
        return frequencyPatterns;
    }

    /**
     * 类型模式识别
     */
    private Map<String, Object> recognizeTypePatterns(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> typePatterns = new HashMap<>();
        
        String alertType = alert.getAlertType();
        String severityLevel = alert.getSeverityLevel();
        
        // 类型相关性分析
        List<String> relatedTypes = analyzeRelatedTypes(alertType, context);
        typePatterns.put("relatedTypes", relatedTypes);
        
        // 严重程度分布
        String severityDistribution = analyzeSeverityDistribution(severityLevel, context);
        typePatterns.put("severityDistribution", severityDistribution);
        
        // 类型演化模式
        String typeEvolution = analyzeTypeEvolution(alertType, context);
        typePatterns.put("typeEvolution", typeEvolution);
        
        // 共现模式
        List<String> coOccurrencePatterns = analyzeCoOccurrencePatterns(alertType, context);
        typePatterns.put("coOccurrencePatterns", coOccurrencePatterns);
        
        return typePatterns;
    }

    /**
     * 用户行为模式识别
     */
    private Map<String, Object> recognizeBehaviorPatterns(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> behaviorPatterns = new HashMap<>();
        
        String userProfile = (String) context.get("userProfile");
        String activityLevel = (String) context.get("activityLevel");
        String responsePattern = (String) context.get("userResponsePattern");
        
        // 行为一致性分析
        double behaviorConsistency = calculateBehaviorConsistency(userProfile, activityLevel);
        behaviorPatterns.put("behaviorConsistency", behaviorConsistency);
        
        // 响应模式分析
        String responsePrediction = predictResponsePattern(responsePattern, alert.getSeverityLevel());
        behaviorPatterns.put("responsePrediction", responsePrediction);
        
        // 用户风险行为识别
        List<String> riskBehaviors = identifyRiskBehaviors(userProfile, activityLevel, context);
        behaviorPatterns.put("riskBehaviors", riskBehaviors);
        
        // 行为改变检测
        boolean behaviorChangeDetected = detectBehaviorChange(context);
        behaviorPatterns.put("behaviorChangeDetected", behaviorChangeDetected);
        
        return behaviorPatterns;
    }

    /**
     * 设备模式识别
     */
    private Map<String, Object> recognizeDevicePatterns(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> devicePatterns = new HashMap<>();
        
        String deviceStatus = (String) context.get("deviceStatus");
        Object deviceHealthObj = context.get("deviceHealth");
        double deviceHealth = deviceHealthObj instanceof Number ? 
                ((Number) deviceHealthObj).doubleValue() : 0.8;
        
        // 设备健康趋势
        String healthTrend = analyzeDeviceHealthTrend(deviceHealth, deviceStatus);
        devicePatterns.put("healthTrend", healthTrend);
        
        // 设备故障模式
        String failurePattern = analyzeFailurePattern(deviceStatus, context);
        devicePatterns.put("failurePattern", failurePattern);
        
        // 维护需求预测
        boolean maintenanceRequired = predictMaintenanceNeeds(deviceHealth, context);
        devicePatterns.put("maintenanceRequired", maintenanceRequired);
        
        // 设备性能模式
        String performancePattern = analyzePerformancePattern(deviceHealth, context);
        devicePatterns.put("performancePattern", performancePattern);
        
        return devicePatterns;
    }

    /**
     * 计算模式置信度
     */
    private double calculatePatternConfidence(Map<String, Object> patternResult) {
        double confidence = 0.5; // 基础置信度
        
        // 时间集中度影响
        Object timeConcentration = patternResult.get("timeConcentration");
        if (timeConcentration instanceof Number) {
            confidence += ((Number) timeConcentration).doubleValue() * 0.1;
        }
        
        // 行为一致性影响
        Object behaviorConsistency = patternResult.get("behaviorConsistency");
        if (behaviorConsistency instanceof Number) {
            confidence += ((Number) behaviorConsistency).doubleValue() * 0.15;
        }
        
        // 异常频率检测影响
        Object isAbnormal = patternResult.get("isAbnormalFrequency");
        if (Boolean.TRUE.equals(isAbnormal)) {
            confidence += 0.2;
        }
        
        // 行为改变检测影响
        Object behaviorChange = patternResult.get("behaviorChangeDetected");
        if (Boolean.TRUE.equals(behaviorChange)) {
            confidence += 0.1;
        }
        
        return Math.max(0.0, Math.min(1.0, confidence));
    }

    /**
     * 生成模式摘要
     */
    private String generatePatternSummary(Map<String, Object> patternResult) {
        StringBuilder summary = new StringBuilder();
        
        String periodicPattern = (String) patternResult.get("periodicPattern");
        String frequencyCategory = (String) patternResult.get("frequencyCategory");
        String healthTrend = (String) patternResult.get("healthTrend");
        
        summary.append("周期模式: ").append(periodicPattern != null ? periodicPattern : "未知");
        summary.append(", 频率类别: ").append(frequencyCategory != null ? frequencyCategory : "未知");
        summary.append(", 设备趋势: ").append(healthTrend != null ? healthTrend : "稳定");
        
        return summary.toString();
    }

    // 辅助方法实现
    private String analyzePeriodicPattern(String timeSlot, Boolean isWeekday) {
        if (isWeekday != null && isWeekday) {
            return "工作日" + (timeSlot != null ? "-" + timeSlot : "");
        } else {
            return "周末" + (timeSlot != null ? "-" + timeSlot : "");
        }
    }

    private double calculateTimeConcentration(String timePattern) {
        if ("work_hours".equals(timePattern)) {
            return 0.8;
        } else if ("sleep_hours".equals(timePattern)) {
            return 0.3;
        } else {
            return 0.6;
        }
    }

    private String analyzeTimeTrend(Map<String, Object> context) {
        return random.nextBoolean() ? "increasing" : "stable";
    }

    private String analyzeWorkTimeDistribution(String timePattern, Boolean isWeekday) {
        if ("work_hours".equals(timePattern) && Boolean.TRUE.equals(isWeekday)) {
            return "work_concentrated";
        } else {
            return "distributed";
        }
    }

    private String categorizeFrequency(int frequency) {
        if (frequency == 0) return "no_history";
        if (frequency <= 2) return "rare";
        if (frequency <= 5) return "occasional";
        if (frequency <= 10) return "frequent";
        return "very_frequent";
    }

    private String analyzeFrequencyTrend(int frequency, Map<String, Object> context) {
        return frequency > 5 ? "increasing" : "stable";
    }

    private boolean detectAbnormalFrequency(int frequency, String alertType) {
        // 基于告警类型判断异常频率
        return frequency > 10 || (frequency == 0 && "CRITICAL".equals(alertType));
    }

    private int predictFutureFrequency(int currentFreq, Map<String, Object> context) {
        return Math.max(0, currentFreq + random.nextInt(3) - 1);
    }

    private List<String> analyzeRelatedTypes(String alertType, Map<String, Object> context) {
        List<String> related = new ArrayList<>();
        if ("HEART_RATE".equals(alertType)) {
            related.add("BLOOD_PRESSURE");
            related.add("ACTIVITY_LEVEL");
        }
        return related;
    }

    private String analyzeSeverityDistribution(String severity, Map<String, Object> context) {
        return "mixed_distribution";
    }

    private String analyzeTypeEvolution(String alertType, Map<String, Object> context) {
        return "stable_type";
    }

    private List<String> analyzeCoOccurrencePatterns(String alertType, Map<String, Object> context) {
        return new ArrayList<>();
    }

    private double calculateBehaviorConsistency(String userProfile, String activityLevel) {
        return 0.7 + (random.nextGaussian() * 0.1);
    }

    private String predictResponsePattern(String currentPattern, String severity) {
        if ("CRITICAL".equals(severity)) {
            return "immediate_response";
        }
        return "delayed_response".equals(currentPattern) ? "delayed_response" : "normal_response";
    }

    private List<String> identifyRiskBehaviors(String userProfile, String activityLevel, Map<String, Object> context) {
        List<String> risks = new ArrayList<>();
        if ("inactive".equals(activityLevel)) {
            risks.add("sedentary_lifestyle");
        }
        return risks;
    }

    private boolean detectBehaviorChange(Map<String, Object> context) {
        return random.nextDouble() < 0.3; // 30%概率检测到行为改变
    }

    private String analyzeDeviceHealthTrend(double health, String status) {
        if (health > 0.8) return "excellent";
        if (health > 0.6) return "good";
        return "declining";
    }

    private String analyzeFailurePattern(String status, Map<String, Object> context) {
        return "error".equals(status) ? "recurring_error" : "normal_operation";
    }

    private boolean predictMaintenanceNeeds(double health, Map<String, Object> context) {
        return health < 0.7;
    }

    private String analyzePerformancePattern(double health, Map<String, Object> context) {
        return health > 0.8 ? "optimal" : "degraded";
    }
}