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

package com.ljwx.modules.alert.service.engine;

import com.ljwx.modules.alert.domain.dto.AlertProcessingRequest;
import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import com.ljwx.modules.alert.service.ai.MLAlertAnalyzer;
import com.ljwx.modules.alert.service.ai.ContextAnalyzer;
import com.ljwx.modules.alert.service.ai.PatternRecognizer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 智能告警处理引擎
 * 提供多维度告警分析和处理能力
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.engine.SmartAlertEngine
 * @CreateTime 2024-08-30 - 18:00:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SmartAlertEngine {

    private final MLAlertAnalyzer mlAnalyzer;
    private final ContextAnalyzer contextAnalyzer;
    private final PatternRecognizer patternRecognizer;

    /**
     * 多维度告警分析
     */
    public AnalyzedAlert analyzeAlert(AlertProcessingRequest request) {
        log.info("开始智能告警分析: alertType={}, deviceSn={}, severityLevel={}", 
                request.getAlertType(), request.getDeviceSn(), request.getSeverityLevel());
        
        long startTime = System.currentTimeMillis();
        Long alertId = generateAlertId();
        
        try {
            // 1. 基础告警信息增强
            AnalyzedAlert enhancedAlert = enhanceBasicInfo(request, alertId);
            log.debug("基础信息增强完成: alertId={}", alertId);
            
            // 2. 上下文分析
            Map<String, Object> context = contextAnalyzer.analyzeContext(
                    enhancedAlert.getDeviceSn(),
                    enhancedAlert.getUserId(),
                    enhancedAlert.getAlertTimestamp()
            );
            log.debug("上下文分析完成: alertId={}, contextKeys={}", alertId, context.keySet());
            
            // 3. 历史模式分析
            Map<String, Object> patternAnalysis = patternRecognizer.analyzePatterns(
                    enhancedAlert, context
            );
            log.debug("模式分析完成: alertId={}, patterns={}", alertId, patternAnalysis.keySet());
            
            // 4. 机器学习异常检测
            Map<String, Object> mlAnalysis = mlAnalyzer.detectAnomaly(
                    enhancedAlert, context, patternAnalysis
            );
            log.debug("ML异常检测完成: alertId={}, anomalyScore={}", 
                    alertId, mlAnalysis.get("anomalyScore"));
            
            // 5. 综合评估
            AnalyzedAlert finalAssessment = comprehensiveAssessment(
                    enhancedAlert, context, patternAnalysis, mlAnalysis
            );
            
            long analysisTime = System.currentTimeMillis() - startTime;
            log.info("告警分析完成: alertId={}, confidence={}, time={}ms", 
                    alertId, finalAssessment.getConfidenceScore(), analysisTime);
            
            return finalAssessment;
            
        } catch (Exception e) {
            long analysisTime = System.currentTimeMillis() - startTime;
            log.error("告警分析失败: alertType={}, deviceSn={}, time={}ms", 
                    request.getAlertType(), request.getDeviceSn(), analysisTime, e);
            
            // 分析失败时返回基础增强信息
            return enhanceBasicInfo(request, alertId);
        }
    }

    /**
     * 基础告警信息增强
     */
    private AnalyzedAlert enhanceBasicInfo(AlertProcessingRequest request, Long alertId) {
        return AnalyzedAlert.builder()
                .alertId(alertId)
                .alertType(request.getAlertType())
                .deviceSn(request.getDeviceSn())
                .alertTimestamp(request.getAlertTimestamp())
                .healthId(request.getHealthId())
                .alertDesc(request.getAlertDesc())
                .severityLevel(request.getSeverityLevel())
                .userId(request.getUserId())
                .orgId(request.getOrgId())
                .customerId(request.getCustomerId())
                .ruleId(request.getRuleId())
                .latitude(request.getLatitude())
                .longitude(request.getLongitude())
                .confidenceScore(0.5) // 默认置信度
                .urgencyLevel("MEDIUM") // 默认紧急级别
                .falsePositiveProbability(0.2) // 默认误报概率
                .autoProcessable(false) // 默认需要人工处理
                .recommendedActions(getDefaultRecommendedActions(request))
                .contextData(new HashMap<>())
                .calculationBreakdown(new HashMap<>())
                .build();
    }

    /**
     * 综合评估告警
     */
    private AnalyzedAlert comprehensiveAssessment(AnalyzedAlert alert, 
                                                Map<String, Object> context,
                                                Map<String, Object> patternAnalysis, 
                                                Map<String, Object> mlResult) {
        
        // 计算综合置信度
        Double confidenceScore = calculateConfidence(patternAnalysis, mlResult);
        
        // 计算紧急级别
        String urgencyLevel = calculateUrgency(alert, context);
        
        // 计算误报概率
        Double falsePositiveProbability = calculateFalsePositiveProbability(mlResult);
        
        // 评估是否可自动处理
        boolean autoProcessable = assessAutoProcessability(alert, mlResult);
        
        // 生成推荐操作
        List<String> recommendedActions = generateRecommendations(alert, context, mlResult);
        
        // 创建计算明细
        Map<String, Double> calculationBreakdown = createCalculationBreakdown(
                context, patternAnalysis, mlResult);
        
        return alert.toBuilder()
                .confidenceScore(confidenceScore)
                .urgencyLevel(urgencyLevel)
                .falsePositiveProbability(falsePositiveProbability)
                .autoProcessable(autoProcessable)
                .recommendedActions(recommendedActions)
                .contextData(context)
                .calculationBreakdown(calculationBreakdown)
                .build();
    }

    private Double calculateConfidence(Map<String, Object> patternAnalysis, Map<String, Object> mlResult) {
        double baseConfidence = 0.5;
        
        // 基于模式分析的置信度调整
        Object patternScore = patternAnalysis.get("patternConfidence");
        if (patternScore instanceof Number) {
            baseConfidence += ((Number) patternScore).doubleValue() * 0.2;
        }
        
        // 基于ML分析的置信度调整
        Object mlScore = mlResult.get("confidenceScore");
        if (mlScore instanceof Number) {
            baseConfidence = (baseConfidence + ((Number) mlScore).doubleValue()) / 2;
        }
        
        return Math.max(0.0, Math.min(1.0, baseConfidence));
    }

    private String calculateUrgency(AnalyzedAlert alert, Map<String, Object> context) {
        // 基于严重级别和上下文计算紧急程度
        String severityLevel = alert.getSeverityLevel();
        
        if ("CRITICAL".equals(severityLevel)) {
            return "HIGH";
        } else if ("HIGH".equals(severityLevel)) {
            // 检查是否有历史类似告警
            Object hasHistoricalAlerts = context.get("hasHistoricalAlerts");
            return Boolean.TRUE.equals(hasHistoricalAlerts) ? "HIGH" : "MEDIUM";
        } else {
            return "LOW";
        }
    }

    private Double calculateFalsePositiveProbability(Map<String, Object> mlResult) {
        Object falsePositiveProb = mlResult.get("falsePositiveProb");
        if (falsePositiveProb instanceof Number) {
            return ((Number) falsePositiveProb).doubleValue();
        }
        return 0.15; // 默认误报率15%
    }

    private boolean assessAutoProcessability(AnalyzedAlert alert, Map<String, Object> mlResult) {
        // 基于置信度和误报概率判断是否可自动处理
        Object confidence = mlResult.get("confidenceScore");
        Object falsePositiveProb = mlResult.get("falsePositiveProb");
        
        if (confidence instanceof Number && falsePositiveProb instanceof Number) {
            double conf = ((Number) confidence).doubleValue();
            double fpp = ((Number) falsePositiveProb).doubleValue();
            
            // 高置信度且低误报率才可自动处理
            return conf > 0.8 && fpp < 0.1;
        }
        
        return false;
    }

    private List<String> generateRecommendations(AnalyzedAlert alert, 
                                               Map<String, Object> context, 
                                               Map<String, Object> mlResult) {
        List<String> recommendations = new ArrayList<>();
        
        String alertType = alert.getAlertType();
        String severityLevel = alert.getSeverityLevel();
        
        // 基于告警类型的推荐
        switch (alertType) {
            case "HEART_RATE":
                if ("CRITICAL".equals(severityLevel)) {
                    recommendations.add("立即联系医护人员");
                    recommendations.add("建议用户停止当前活动");
                } else {
                    recommendations.add("建议用户注意休息");
                    recommendations.add("持续监控心率变化");
                }
                break;
                
            case "DEVICE_OFFLINE":
                recommendations.add("检查设备连接状态");
                recommendations.add("联系用户确认设备状态");
                break;
                
            default:
                recommendations.add("人工评估告警情况");
                recommendations.add("根据具体情况采取相应措施");
        }
        
        return recommendations;
    }

    private List<String> getDefaultRecommendedActions(AlertProcessingRequest request) {
        List<String> actions = new ArrayList<>();
        actions.add("人工确认告警");
        actions.add("联系相关人员");
        return actions;
    }

    private Map<String, Double> createCalculationBreakdown(Map<String, Object> context,
                                                         Map<String, Object> patternAnalysis, 
                                                         Map<String, Object> mlResult) {
        Map<String, Double> breakdown = new HashMap<>();
        
        // 提取数值型计算结果
        extractNumericValue(context, "contextScore", breakdown);
        extractNumericValue(patternAnalysis, "patternConfidence", breakdown);
        extractNumericValue(mlResult, "anomalyScore", breakdown);
        extractNumericValue(mlResult, "confidenceScore", breakdown);
        
        return breakdown;
    }

    private void extractNumericValue(Map<String, Object> source, String key, Map<String, Double> target) {
        Object value = source.get(key);
        if (value instanceof Number) {
            target.put(key, ((Number) value).doubleValue());
        }
    }

    private Long generateAlertId() {
        return System.currentTimeMillis() + (long) (Math.random() * 1000);
    }
}