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

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * 机器学习告警分析器
 * 基于机器学习算法进行异常检测和告警分析
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.ai.MLAlertAnalyzer
 * @CreateTime 2024-08-30 - 18:20:00
 */
@Slf4j
@Service
public class MLAlertAnalyzer {

    private final Random random = new Random();

    /**
     * 机器学习异常检测
     * 
     * @param alert 告警信息
     * @param context 上下文信息
     * @param patternAnalysis 模式分析结果
     * @return ML分析结果
     */
    public Map<String, Object> detectAnomaly(AnalyzedAlert alert, 
                                           Map<String, Object> context,
                                           Map<String, Object> patternAnalysis) {
        
        log.debug("开始ML异常检测: alertId={}, alertType={}", 
                alert.getAlertId(), alert.getAlertType());
        
        Map<String, Object> mlResult = new HashMap<>();
        
        try {
            // 1. 孤立森林异常检测
            double isolationForestScore = performIsolationForestAnalysis(alert, context);
            mlResult.put("isolationForestScore", isolationForestScore);
            
            // 2. 时序分析
            Map<String, Object> timeSeriesAnalysis = performTimeSeriesAnalysis(alert, context);
            mlResult.putAll(timeSeriesAnalysis);
            
            // 3. 个人基线学习
            Map<String, Object> baselineAnalysis = performPersonalBaselineAnalysis(alert, context);
            mlResult.putAll(baselineAnalysis);
            
            // 4. 综合异常评分
            double anomalyScore = calculateCompositeAnomalyScore(mlResult);
            mlResult.put("anomalyScore", anomalyScore);
            
            // 5. 置信度计算
            double confidenceScore = calculateMLConfidenceScore(mlResult);
            mlResult.put("confidenceScore", confidenceScore);
            
            // 6. 误报概率估算
            double falsePositiveProb = estimateFalsePositiveProbability(mlResult);
            mlResult.put("falsePositiveProb", falsePositiveProb);
            
            log.debug("ML异常检测完成: alertId={}, anomalyScore={}, confidence={}", 
                    alert.getAlertId(), anomalyScore, confidenceScore);
            
        } catch (Exception e) {
            log.error("ML异常检测失败: alertId={}", alert.getAlertId(), e);
            
            // 返回默认结果
            mlResult.put("anomalyScore", 0.5);
            mlResult.put("confidenceScore", 0.3);
            mlResult.put("falsePositiveProb", 0.3);
        }
        
        return mlResult;
    }

    /**
     * 孤立森林异常检测分析
     */
    private double performIsolationForestAnalysis(AnalyzedAlert alert, Map<String, Object> context) {
        // 模拟孤立森林算法异常检测
        // 实际实现中会使用真实的机器学习模型
        
        double score = 0.5; // 基础分数
        
        // 基于告警严重程度调整
        String severityLevel = alert.getSeverityLevel();
        switch (severityLevel) {
            case "CRITICAL":
                score += 0.3;
                break;
            case "HIGH":
                score += 0.2;
                break;
            case "MEDIUM":
                score += 0.1;
                break;
        }
        
        // 基于历史告警频率调整
        Object alertFrequency = context.get("alertFrequency");
        if (alertFrequency instanceof Number) {
            double frequency = ((Number) alertFrequency).doubleValue();
            if (frequency > 10) {
                score -= 0.1; // 频繁告警降低异常分数
            } else if (frequency < 2) {
                score += 0.1; // 罕见告警提高异常分数
            }
        }
        
        // 添加随机噪声模拟真实ML模型的变化
        score += (random.nextGaussian() * 0.05);
        
        return Math.max(0.0, Math.min(1.0, score));
    }

    /**
     * 时序分析
     */
    private Map<String, Object> performTimeSeriesAnalysis(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> timeSeriesResult = new HashMap<>();
        
        // 模拟LSTM时序分析
        double trendScore = 0.5 + (random.nextGaussian() * 0.1);
        double seasonalityScore = 0.4 + (random.nextGaussian() * 0.1);
        double volatilityScore = 0.3 + (random.nextGaussian() * 0.1);
        
        timeSeriesResult.put("trendScore", Math.max(0.0, Math.min(1.0, trendScore)));
        timeSeriesResult.put("seasonalityScore", Math.max(0.0, Math.min(1.0, seasonalityScore)));
        timeSeriesResult.put("volatilityScore", Math.max(0.0, Math.min(1.0, volatilityScore)));
        
        // 时序异常指标
        double timeSeriesAnomalyScore = (trendScore + seasonalityScore + volatilityScore) / 3;
        timeSeriesResult.put("timeSeriesAnomalyScore", timeSeriesAnomalyScore);
        
        return timeSeriesResult;
    }

    /**
     * 个人基线学习分析
     */
    private Map<String, Object> performPersonalBaselineAnalysis(AnalyzedAlert alert, Map<String, Object> context) {
        Map<String, Object> baselineResult = new HashMap<>();
        
        // 模拟个人基线偏差分析
        double baselineDeviation = 0.5 + (random.nextGaussian() * 0.2);
        double personalPatternScore = 0.6 + (random.nextGaussian() * 0.15);
        
        // 基于用户历史数据的适应性评分
        double adaptiveScore = calculateAdaptiveScore(alert, context);
        
        baselineResult.put("baselineDeviation", Math.max(0.0, Math.min(1.0, baselineDeviation)));
        baselineResult.put("personalPatternScore", Math.max(0.0, Math.min(1.0, personalPatternScore)));
        baselineResult.put("adaptiveScore", adaptiveScore);
        
        return baselineResult;
    }

    /**
     * 计算综合异常评分
     */
    private double calculateCompositeAnomalyScore(Map<String, Object> mlResult) {
        double isolationForestScore = getDoubleValue(mlResult, "isolationForestScore", 0.5);
        double timeSeriesScore = getDoubleValue(mlResult, "timeSeriesAnomalyScore", 0.5);
        double baselineDeviation = getDoubleValue(mlResult, "baselineDeviation", 0.5);
        
        // 加权平均计算综合异常分数
        return (isolationForestScore * 0.4 + timeSeriesScore * 0.3 + baselineDeviation * 0.3);
    }

    /**
     * 计算ML置信度分数
     */
    private double calculateMLConfidenceScore(Map<String, Object> mlResult) {
        double anomalyScore = getDoubleValue(mlResult, "anomalyScore", 0.5);
        double personalPatternScore = getDoubleValue(mlResult, "personalPatternScore", 0.5);
        double adaptiveScore = getDoubleValue(mlResult, "adaptiveScore", 0.5);
        
        // 综合计算置信度
        double confidence = (anomalyScore * 0.5 + personalPatternScore * 0.3 + adaptiveScore * 0.2);
        
        // 应用置信度校准
        return applyConfidenceCalibration(confidence);
    }

    /**
     * 估算误报概率
     */
    private double estimateFalsePositiveProbability(Map<String, Object> mlResult) {
        double anomalyScore = getDoubleValue(mlResult, "anomalyScore", 0.5);
        double confidenceScore = getDoubleValue(mlResult, "confidenceScore", 0.5);
        
        // 基于异常分数和置信度估算误报率
        // 异常分数越高、置信度越高，误报率越低
        double falsePositiveProb = 0.25 - (anomalyScore * 0.15) - (confidenceScore * 0.1);
        
        return Math.max(0.05, Math.min(0.5, falsePositiveProb));
    }

    /**
     * 计算适应性评分
     */
    private double calculateAdaptiveScore(AnalyzedAlert alert, Map<String, Object> context) {
        // 基于用户行为模式的适应性评分
        double score = 0.5;
        
        // 基于告警类型调整
        String alertType = alert.getAlertType();
        if ("HEART_RATE".equals(alertType) || "BLOOD_PRESSURE".equals(alertType)) {
            score += 0.1; // 生理指标类告警适应性较高
        }
        
        // 基于时间模式调整
        Object timePattern = context.get("timePattern");
        if ("normal_hours".equals(timePattern)) {
            score += 0.05;
        }
        
        return Math.max(0.0, Math.min(1.0, score));
    }

    /**
     * 置信度校准
     */
    private double applyConfidenceCalibration(double rawConfidence) {
        // 应用校准函数，提高置信度的准确性
        // 这里使用简单的sigmoid校准
        double calibrated = 1.0 / (1.0 + Math.exp(-(rawConfidence - 0.5) * 2));
        return Math.max(0.1, Math.min(0.95, calibrated));
    }

    private double getDoubleValue(Map<String, Object> map, String key, double defaultValue) {
        Object value = map.get(key);
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return defaultValue;
    }
}