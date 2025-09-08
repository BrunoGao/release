package com.ljwx.modules.health.service;

import com.ljwx.modules.health.entity.HealthPrediction;
import com.ljwx.modules.health.entity.HealthPredictionModelConfig;
import com.ljwx.modules.health.entity.UserHealthData;
import com.ljwx.modules.health.mapper.HealthPredictionMapper;
import com.ljwx.modules.health.mapper.HealthPredictionModelConfigMapper;
import com.ljwx.modules.health.mapper.UserHealthDataMapper;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.service.UnifiedHealthDataQueryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 健康预测服务 - 基于LSTM/ARIMA时间序列分析
 * 
 * @Author Bruno Gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.HealthPredictionService
 * @CreateTime 2025-01-26
 */
@Slf4j
@Service
public class HealthPredictionService {

    @Autowired
    private HealthPredictionMapper healthPredictionMapper;
    
    @Autowired
    private HealthPredictionModelConfigMapper modelConfigMapper;
    
    @Autowired
    private UserHealthDataMapper userHealthDataMapper;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;
    
    // 支持的健康特征
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", 
        "pressure_high", "pressure_low", "stress",
        "step", "calorie", "distance", "sleep"
    };
    
    // 预测类型
    private static final String[] PREDICTION_TYPES = {
        "health_trend", "risk_assessment", "intervention_effect",
        "deterioration_warning", "recovery_timeline"
    };

    /**
     * 生成用户健康趋势预测
     * @param userId 用户ID
     * @param customerId 租户ID
     * @param predictionHorizonDays 预测天数
     * @return 预测结果列表
     */
    @Transactional(rollbackFor = Exception.class)
    public List<HealthPrediction> generateHealthTrendPredictions(Long userId, Long customerId, Integer predictionHorizonDays) {
        log.info("🔮 开始生成用户健康趋势预测: userId={}, predictionDays={}", userId, predictionHorizonDays);
        
        try {
            List<HealthPrediction> predictions = new ArrayList<>();
            LocalDate predictionDate = LocalDate.now();
            
            // 为每个健康特征生成预测
            for (String feature : HEALTH_FEATURES) {
                try {
                    // 1. 使用统一查询服务获取历史数据
                    UnifiedHealthQueryDTO historyQuery = new UnifiedHealthQueryDTO();
                    historyQuery.setCustomerId(customerId);
                    historyQuery.setUserId(userId);
                    historyQuery.setMetric(feature); // 按特定指标查询
                    historyQuery.setStartDate(LocalDateTime.now().minusDays(90)); // 90天历史数据
                    historyQuery.setEndDate(LocalDateTime.now());
                    historyQuery.setPageSize(10000); // 预测需要大量历史数据
                    historyQuery.setEnableSharding(true);
                    historyQuery.setOrderBy("timestamp");
                    historyQuery.setOrderDirection("asc");
                    
                    Map<String, Object> historyResult = unifiedQueryService.queryHealthData(historyQuery);
                    List<UserHealthData> historicalData = (List<UserHealthData>) historyResult.get("data");
                    
                    if (historicalData.size() < 30) { // 至少需要30个数据点
                        log.warn("⚠️ 用户 {} 特征 {} 历史数据不足，跳过预测", userId, feature);
                        continue;
                    }
                    
                    // 2. 选择最适合的预测模型
                    HealthPredictionModelConfig modelConfig = selectOptimalModel(customerId, feature, historicalData);
                    
                    if (modelConfig == null) {
                        log.warn("⚠️ 特征 {} 未找到合适的预测模型", feature);
                        continue;
                    }
                    
                    // 3. 执行预测
                    PredictionResult predictionResult = executePrediction(historicalData, modelConfig, predictionHorizonDays);
                    
                    // 4. 创建预测记录
                    HealthPrediction prediction = createPredictionRecord(
                        userId, customerId, feature, "health_trend", 
                        modelConfig, predictionResult, predictionDate, predictionHorizonDays
                    );
                    
                    predictions.add(prediction);
                    
                    // 5. 保存到数据库
                    healthPredictionMapper.insert(prediction);
                    
                    log.info("✅ 特征 {} 预测完成，置信度: {}", feature, predictionResult.getConfidenceScore());
                    
                } catch (Exception e) {
                    log.error("❌ 特征 {} 预测失败: {}", feature, e.getMessage(), e);
                }
            }
            
            log.info("🎉 用户 {} 健康趋势预测完成，共生成 {} 个预测", userId, predictions.size());
            return predictions;
            
        } catch (Exception e) {
            log.error("❌ 生成健康趋势预测失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new RuntimeException("生成健康趋势预测失败: " + e.getMessage(), e);
        }
    }

    /**
     * 生成健康风险评估预测
     * @param userId 用户ID
     * @param customerId 租户ID
     * @return 风险预测结果
     */
    @Transactional(rollbackFor = Exception.class)
    public List<HealthPrediction> generateRiskAssessmentPredictions(Long userId, Long customerId) {
        log.info("⚠️ 开始生成用户健康风险评估: userId={}", userId);
        
        try {
            List<HealthPrediction> riskPredictions = new ArrayList<>();
            LocalDate predictionDate = LocalDate.now();
            
            // 1. 使用统一查询服务获取最近健康数据
            UnifiedHealthQueryDTO recentQuery = new UnifiedHealthQueryDTO();
            recentQuery.setCustomerId(customerId);
            recentQuery.setUserId(userId);
            recentQuery.setStartDate(LocalDateTime.now().minusDays(30));
            recentQuery.setEndDate(LocalDateTime.now());
            recentQuery.setQueryMode("all"); // 查询所有数据
            recentQuery.setEnableSharding(true);
            
            Map<String, Object> recentResult = unifiedQueryService.queryHealthData(recentQuery);
            List<UserHealthData> recentData = (List<UserHealthData>) recentResult.get("data");
            
            if (recentData.isEmpty()) {
                log.warn("⚠️ 用户 {} 缺少健康数据，无法进行风险评估", userId);
                return riskPredictions;
            }
            
            // 2. 计算各类健康风险
            Map<String, RiskAssessmentResult> riskAssessments = calculateHealthRisks(recentData);
            
            // 3. 为每个风险类别创建预测记录
            for (Map.Entry<String, RiskAssessmentResult> entry : riskAssessments.entrySet()) {
                String riskType = entry.getKey();
                RiskAssessmentResult riskResult = entry.getValue();
                
                // 创建风险预测记录
                HealthPrediction riskPrediction = new HealthPrediction();
                riskPrediction.setUserId(userId);
                riskPrediction.setCustomerId(customerId);
                riskPrediction.setPredictionType("risk_assessment");
                riskPrediction.setFeatureName(riskType);
                riskPrediction.setModelType("RISK_ASSESSMENT");
                riskPrediction.setModelVersion("v1.0");
                riskPrediction.setPredictionDate(predictionDate);
                riskPrediction.setPredictionStartDate(predictionDate);
                riskPrediction.setPredictionEndDate(predictionDate.plusDays(30));
                riskPrediction.setPredictionHorizonDays(30);
                riskPrediction.setPredictedValue(BigDecimal.valueOf(riskResult.getRiskScore()));
                riskPrediction.setConfidenceScore(BigDecimal.valueOf(riskResult.getConfidence()));
                riskPrediction.setPredictionStatus("completed");
                
                // 设置预测详情
                Map<String, Object> details = new HashMap<>();
                details.put("risk_level", riskResult.getRiskLevel());
                details.put("risk_factors", riskResult.getRiskFactors());
                details.put("warning_indicators", riskResult.getWarningIndicators());
                details.put("recommended_actions", riskResult.getRecommendedActions());
                riskPrediction.setPredictionDetails(convertMapToJson(details));
                
                riskPredictions.add(riskPrediction);
                healthPredictionMapper.insert(riskPrediction);
            }
            
            log.info("🎉 用户 {} 健康风险评估完成，识别 {} 个风险类别", userId, riskPredictions.size());
            return riskPredictions;
            
        } catch (Exception e) {
            log.error("❌ 生成健康风险评估失败: userId={}, error={}", userId, e.getMessage(), e);
            throw new RuntimeException("生成健康风险评估失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取历史健康数据 (已废弃，使用统一查询服务)
     */
    @Deprecated
    private List<UserHealthData> getHistoricalHealthData(Long userId, String feature, Integer days) {
        log.warn("使用了已废弃的getHistoricalHealthData方法，建议使用UnifiedHealthDataQueryService");
        try {
            LocalDateTime endTime = LocalDateTime.now();
            LocalDateTime startTime = endTime.minusDays(days);
            
            // 构建查询条件 - 这里简化实现，实际应该根据feature过滤特定字段
            Map<String, Object> queryParams = new HashMap<>();
            queryParams.put("userId", userId);
            queryParams.put("startTime", startTime);
            queryParams.put("endTime", endTime);
            
            // 使用MyBatis查询历史数据
            List<UserHealthData> data = userHealthDataMapper.selectHistoricalData(queryParams);
            
            // 按时间排序
            return data.stream()
                    .sorted(Comparator.comparing(UserHealthData::getTimestamp))
                    .collect(Collectors.toList());
                    
        } catch (Exception e) {
            log.error("获取历史健康数据失败: userId={}, feature={}, error={}", userId, feature, e.getMessage());
            return new ArrayList<>();
        }
    }

    /**
     * 选择最优预测模型
     */
    private HealthPredictionModelConfig selectOptimalModel(Long customerId, String feature, List<UserHealthData> historicalData) {
        try {
            // 查询可用的模型配置
            Map<String, Object> queryParams = new HashMap<>();
            queryParams.put("customerId", customerId);
            queryParams.put("featureName", feature);
            queryParams.put("isEnabled", true);
            
            List<HealthPredictionModelConfig> availableModels = modelConfigMapper.selectByCondition(queryParams);
            
            if (availableModels.isEmpty()) {
                log.warn("⚠️ 特征 {} 没有可用的预测模型", feature);
                return null;
            }
            
            // 简单策略：数据量大用LSTM，数据量小用ARIMA，非常小用线性回归
            if (historicalData.size() >= 100) {
                return availableModels.stream()
                        .filter(model -> "LSTM".equals(model.getModelType()))
                        .findFirst()
                        .orElse(availableModels.get(0));
            } else if (historicalData.size() >= 50) {
                return availableModels.stream()
                        .filter(model -> "ARIMA".equals(model.getModelType()))
                        .findFirst()
                        .orElse(availableModels.get(0));
            } else {
                return availableModels.stream()
                        .filter(model -> "LINEAR_REGRESSION".equals(model.getModelType()))
                        .findFirst()
                        .orElse(availableModels.get(0));
            }
            
        } catch (Exception e) {
            log.error("选择预测模型失败: feature={}, error={}", feature, e.getMessage());
            return null;
        }
    }

    /**
     * 执行预测算法
     */
    private PredictionResult executePrediction(List<UserHealthData> historicalData, 
                                             HealthPredictionModelConfig modelConfig, 
                                             Integer predictionHorizonDays) {
        try {
            String modelType = modelConfig.getModelType();
            
            switch (modelType) {
                case "LSTM":
                    return executeLSTMPrediction(historicalData, modelConfig, predictionHorizonDays);
                case "ARIMA":
                    return executeARIMAPrediction(historicalData, modelConfig, predictionHorizonDays);
                case "LINEAR_REGRESSION":
                    return executeLinearRegressionPrediction(historicalData, modelConfig, predictionHorizonDays);
                default:
                    throw new IllegalArgumentException("不支持的预测模型类型: " + modelType);
            }
            
        } catch (Exception e) {
            log.error("执行预测算法失败: modelType={}, error={}", modelConfig.getModelType(), e.getMessage());
            throw new RuntimeException("预测算法执行失败", e);
        }
    }

    /**
     * LSTM预测算法实现
     */
    private PredictionResult executeLSTMPrediction(List<UserHealthData> historicalData, 
                                                 HealthPredictionModelConfig modelConfig, 
                                                 Integer predictionHorizonDays) {
        try {
            log.info("🧠 执行LSTM预测算法，数据点数: {}, 预测天数: {}", historicalData.size(), predictionHorizonDays);
            
            // 提取数值序列（以心率为例，实际应根据feature_name动态选择）
            List<Double> values = historicalData.stream()
                    .map(data -> data.getHeartRate() != null ? data.getHeartRate().doubleValue() : 0.0)
                    .collect(Collectors.toList());
            
            // 数据预处理：归一化
            double[] normalizedData = normalizeData(values);
            
            // 简化的LSTM模拟实现（实际应调用Python ML服务或使用DL4J）
            List<Double> predictedValues = simulateLSTMPrediction(normalizedData, predictionHorizonDays);
            
            // 反归一化
            List<Double> denormalizedPredictions = denormalizeData(predictedValues, values);
            
            // 计算置信度（基于历史数据的稳定性）
            double confidence = calculateConfidenceScore(values, denormalizedPredictions);
            
            // 计算趋势方向
            String trendDirection = calculateTrendDirection(denormalizedPredictions);
            
            return PredictionResult.builder()
                    .predictedValues(denormalizedPredictions)
                    .confidenceScore(confidence)
                    .trendDirection(trendDirection)
                    .modelType("LSTM")
                    .build();
                    
        } catch (Exception e) {
            log.error("LSTM预测失败: {}", e.getMessage(), e);
            throw new RuntimeException("LSTM预测执行失败", e);
        }
    }

    /**
     * ARIMA预测算法实现
     */
    private PredictionResult executeARIMAPrediction(List<UserHealthData> historicalData, 
                                                  HealthPredictionModelConfig modelConfig, 
                                                  Integer predictionHorizonDays) {
        try {
            log.info("📈 执行ARIMA预测算法，数据点数: {}, 预测天数: {}", historicalData.size(), predictionHorizonDays);
            
            // 提取时间序列数据
            List<Double> timeSeries = historicalData.stream()
                    .map(data -> data.getHeartRate() != null ? data.getHeartRate().doubleValue() : 0.0)
                    .collect(Collectors.toList());
            
            // 简化的ARIMA模拟实现（实际应使用R或Python的统计库）
            List<Double> predictedValues = simulateARIMAPrediction(timeSeries, predictionHorizonDays);
            
            // 计算置信度
            double confidence = calculateARIMAConfidence(timeSeries, predictedValues);
            
            // 计算趋势
            String trendDirection = calculateTrendDirection(predictedValues);
            
            return PredictionResult.builder()
                    .predictedValues(predictedValues)
                    .confidenceScore(confidence)
                    .trendDirection(trendDirection)
                    .modelType("ARIMA")
                    .build();
                    
        } catch (Exception e) {
            log.error("ARIMA预测失败: {}", e.getMessage(), e);
            throw new RuntimeException("ARIMA预测执行失败", e);
        }
    }

    /**
     * 线性回归预测算法实现
     */
    private PredictionResult executeLinearRegressionPrediction(List<UserHealthData> historicalData, 
                                                             HealthPredictionModelConfig modelConfig, 
                                                             Integer predictionHorizonDays) {
        try {
            log.info("📊 执行线性回归预测算法，数据点数: {}, 预测天数: {}", historicalData.size(), predictionHorizonDays);
            
            // 简单线性回归实现
            List<Double> values = historicalData.stream()
                    .map(data -> data.getHeartRate() != null ? data.getHeartRate().doubleValue() : 0.0)
                    .collect(Collectors.toList());
            
            // 计算线性趋势
            double slope = calculateLinearSlope(values);
            double intercept = calculateLinearIntercept(values, slope);
            
            // 生成预测值
            List<Double> predictedValues = new ArrayList<>();
            int startIndex = values.size();
            
            for (int i = 0; i < predictionHorizonDays; i++) {
                double predictedValue = intercept + slope * (startIndex + i);
                predictedValues.add(Math.max(0, predictedValue)); // 确保非负值
            }
            
            // 基于R²计算置信度
            double confidence = calculateLinearRegressionConfidence(values, slope, intercept);
            
            String trendDirection = slope > 0.1 ? "improving" : (slope < -0.1 ? "declining" : "stable");
            
            return PredictionResult.builder()
                    .predictedValues(predictedValues)
                    .confidenceScore(confidence)
                    .trendDirection(trendDirection)
                    .modelType("LINEAR_REGRESSION")
                    .build();
                    
        } catch (Exception e) {
            log.error("线性回归预测失败: {}", e.getMessage(), e);
            throw new RuntimeException("线性回归预测执行失败", e);
        }
    }

    // ==================== 辅助方法 ====================

    /**
     * 数据归一化
     */
    private double[] normalizeData(List<Double> data) {
        if (data.isEmpty()) return new double[0];
        
        double min = data.stream().mapToDouble(Double::doubleValue).min().orElse(0);
        double max = data.stream().mapToDouble(Double::doubleValue).max().orElse(1);
        double range = max - min;
        
        return data.stream()
                .mapToDouble(value -> range > 0 ? (value - min) / range : 0)
                .toArray();
    }

    /**
     * 反归一化
     */
    private List<Double> denormalizeData(List<Double> normalizedData, List<Double> originalData) {
        if (originalData.isEmpty()) return normalizedData;
        
        double min = originalData.stream().mapToDouble(Double::doubleValue).min().orElse(0);
        double max = originalData.stream().mapToDouble(Double::doubleValue).max().orElse(1);
        double range = max - min;
        
        return normalizedData.stream()
                .map(value -> value * range + min)
                .collect(Collectors.toList());
    }

    /**
     * 简化的LSTM预测模拟（实际应调用深度学习框架）
     */
    private List<Double> simulateLSTMPrediction(double[] data, int predictionDays) {
        List<Double> predictions = new ArrayList<>();
        
        // 简化算法：基于最近趋势和季节性模式
        int windowSize = Math.min(14, data.length / 2); // 使用最近14天或数据的一半
        double recentAvg = 0;
        double trendSlope = 0;
        
        if (data.length >= windowSize) {
            // 计算最近平均值
            for (int i = data.length - windowSize; i < data.length; i++) {
                recentAvg += data[i];
            }
            recentAvg /= windowSize;
            
            // 计算趋势斜率
            for (int i = data.length - windowSize; i < data.length - 1; i++) {
                trendSlope += (data[i + 1] - data[i]);
            }
            trendSlope /= (windowSize - 1);
        }
        
        // 生成预测值（添加一些噪声模拟不确定性）
        Random random = new Random();
        for (int i = 0; i < predictionDays; i++) {
            double noise = random.nextGaussian() * 0.05; // 5%的噪声
            double cyclicComponent = 0.02 * Math.sin(2 * Math.PI * i / 7.0); // 周期性变化
            double predictedValue = recentAvg + trendSlope * i + cyclicComponent + noise;
            predictions.add(Math.max(0, Math.min(1, predictedValue))); // 限制在[0,1]范围内
        }
        
        return predictions;
    }

    /**
     * 简化的ARIMA预测模拟
     */
    private List<Double> simulateARIMAPrediction(List<Double> timeSeries, int predictionDays) {
        List<Double> predictions = new ArrayList<>();
        
        // 简单移动平均 + 趋势分析
        int maWindow = Math.min(7, timeSeries.size() / 3);
        List<Double> movingAverages = calculateMovingAverage(timeSeries, maWindow);
        
        // 计算趋势
        double trend = 0;
        if (movingAverages.size() >= 2) {
            trend = (movingAverages.get(movingAverages.size() - 1) - 
                    movingAverages.get(movingAverages.size() - 2));
        }
        
        // 生成预测
        double lastValue = timeSeries.get(timeSeries.size() - 1);
        for (int i = 0; i < predictionDays; i++) {
            double prediction = lastValue + trend * (i + 1);
            predictions.add(Math.max(0, prediction));
        }
        
        return predictions;
    }

    /**
     * 计算移动平均
     */
    private List<Double> calculateMovingAverage(List<Double> data, int windowSize) {
        List<Double> movingAverages = new ArrayList<>();
        
        for (int i = windowSize - 1; i < data.size(); i++) {
            double sum = 0;
            for (int j = i - windowSize + 1; j <= i; j++) {
                sum += data.get(j);
            }
            movingAverages.add(sum / windowSize);
        }
        
        return movingAverages;
    }

    /**
     * 计算线性斜率
     */
    private double calculateLinearSlope(List<Double> values) {
        int n = values.size();
        if (n < 2) return 0;
        
        double sumX = n * (n - 1) / 2.0; // 0+1+2+...+(n-1)
        double sumY = values.stream().mapToDouble(Double::doubleValue).sum();
        double sumXY = 0;
        double sumXX = 0;
        
        for (int i = 0; i < n; i++) {
            sumXY += i * values.get(i);
            sumXX += i * i;
        }
        
        return (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    }

    /**
     * 计算线性截距
     */
    private double calculateLinearIntercept(List<Double> values, double slope) {
        double meanY = values.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double meanX = (values.size() - 1) / 2.0;
        return meanY - slope * meanX;
    }

    /**
     * 计算置信度分数
     */
    private double calculateConfidenceScore(List<Double> historical, List<Double> predicted) {
        // 基于历史数据的变异系数计算置信度
        if (historical.isEmpty()) return 0.5;
        
        double mean = historical.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double variance = historical.stream()
                .mapToDouble(value -> Math.pow(value - mean, 2))
                .average().orElse(1);
        double standardDeviation = Math.sqrt(variance);
        
        // 变异系数越小，置信度越高
        double coefficientOfVariation = mean > 0 ? standardDeviation / mean : 1;
        double confidence = Math.max(0.3, Math.min(0.95, 1 - coefficientOfVariation));
        
        return confidence;
    }

    private double calculateARIMAConfidence(List<Double> timeSeries, List<Double> predicted) {
        // 基于时间序列的自相关性计算置信度
        return Math.max(0.4, Math.min(0.9, 0.8 - calculateVariability(timeSeries) * 0.3));
    }

    private double calculateLinearRegressionConfidence(List<Double> values, double slope, double intercept) {
        // 基于R²计算置信度
        double meanY = values.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double ssTotal = values.stream().mapToDouble(y -> Math.pow(y - meanY, 2)).sum();
        double ssResidual = 0;
        
        for (int i = 0; i < values.size(); i++) {
            double predicted = intercept + slope * i;
            ssResidual += Math.pow(values.get(i) - predicted, 2);
        }
        
        double rSquared = ssTotal > 0 ? 1 - (ssResidual / ssTotal) : 0;
        return Math.max(0.3, Math.min(0.9, rSquared));
    }

    private double calculateVariability(List<Double> data) {
        if (data.size() < 2) return 1.0;
        
        double mean = data.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double variance = data.stream().mapToDouble(x -> Math.pow(x - mean, 2)).average().orElse(1);
        return Math.sqrt(variance) / Math.max(1, Math.abs(mean));
    }

    /**
     * 计算趋势方向
     */
    private String calculateTrendDirection(List<Double> predictions) {
        if (predictions.size() < 2) return "stable";
        
        double firstHalf = predictions.subList(0, predictions.size() / 2).stream()
                .mapToDouble(Double::doubleValue).average().orElse(0);
        double secondHalf = predictions.subList(predictions.size() / 2, predictions.size()).stream()
                .mapToDouble(Double::doubleValue).average().orElse(0);
        
        double changeRatio = Math.abs(firstHalf) > 0 ? (secondHalf - firstHalf) / firstHalf : 0;
        
        if (changeRatio > 0.05) return "improving";
        else if (changeRatio < -0.05) return "declining";
        else return "stable";
    }

    /**
     * 计算健康风险
     */
    private Map<String, RiskAssessmentResult> calculateHealthRisks(List<UserHealthData> healthData) {
        Map<String, RiskAssessmentResult> riskAssessments = new HashMap<>();
        
        // 心血管风险评估
        RiskAssessmentResult cardiovascularRisk = assessCardiovascularRisk(healthData);
        riskAssessments.put("cardiovascular", cardiovascularRisk);
        
        // 代谢风险评估
        RiskAssessmentResult metabolicRisk = assessMetabolicRisk(healthData);
        riskAssessments.put("metabolic", metabolicRisk);
        
        // 呼吸系统风险评估
        RiskAssessmentResult respiratoryRisk = assessRespiratoryRisk(healthData);
        riskAssessments.put("respiratory", respiratoryRisk);
        
        return riskAssessments;
    }

    private RiskAssessmentResult assessCardiovascularRisk(List<UserHealthData> healthData) {
        // 简化的心血管风险评估逻辑
        List<Integer> heartRates = healthData.stream()
                .map(UserHealthData::getHeartRate)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
                
        if (heartRates.isEmpty()) {
            return RiskAssessmentResult.builder()
                    .riskScore(0.5)
                    .riskLevel("unknown")
                    .confidence(0.3)
                    .build();
        }
        
        double avgHeartRate = heartRates.stream().mapToInt(Integer::intValue).average().orElse(75);
        double riskScore = 0.0;
        String riskLevel;
        
        if (avgHeartRate > 100 || avgHeartRate < 50) {
            riskScore = 0.8;
            riskLevel = "high";
        } else if (avgHeartRate > 90 || avgHeartRate < 60) {
            riskScore = 0.4;
            riskLevel = "medium";
        } else {
            riskScore = 0.1;
            riskLevel = "low";
        }
        
        return RiskAssessmentResult.builder()
                .riskScore(riskScore)
                .riskLevel(riskLevel)
                .confidence(0.75)
                .riskFactors(Arrays.asList("heart_rate_abnormal"))
                .warningIndicators(Arrays.asList("持续心率异常"))
                .recommendedActions(Arrays.asList("定期监测心率", "适量运动", "咨询医生"))
                .build();
    }

    private RiskAssessmentResult assessMetabolicRisk(List<UserHealthData> healthData) {
        // 简化的代谢风险评估
        return RiskAssessmentResult.builder()
                .riskScore(0.2)
                .riskLevel("low")
                .confidence(0.6)
                .riskFactors(Arrays.asList())
                .warningIndicators(Arrays.asList())
                .recommendedActions(Arrays.asList("保持健康饮食", "规律运动"))
                .build();
    }

    private RiskAssessmentResult assessRespiratoryRisk(List<UserHealthData> healthData) {
        // 简化的呼吸系统风险评估
        List<Integer> oxygenLevels = healthData.stream()
                .map(UserHealthData::getBloodOxygen)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
                
        if (oxygenLevels.isEmpty()) {
            return RiskAssessmentResult.builder()
                    .riskScore(0.3)
                    .riskLevel("unknown")
                    .confidence(0.3)
                    .build();
        }
        
        double avgOxygen = oxygenLevels.stream().mapToInt(Integer::intValue).average().orElse(98);
        double riskScore = avgOxygen < 95 ? 0.7 : (avgOxygen < 97 ? 0.3 : 0.1);
        String riskLevel = avgOxygen < 95 ? "high" : (avgOxygen < 97 ? "medium" : "low");
        
        return RiskAssessmentResult.builder()
                .riskScore(riskScore)
                .riskLevel(riskLevel)
                .confidence(0.8)
                .riskFactors(avgOxygen < 95 ? Arrays.asList("low_oxygen_saturation") : Arrays.asList())
                .warningIndicators(avgOxygen < 95 ? Arrays.asList("血氧饱和度偏低") : Arrays.asList())
                .recommendedActions(Arrays.asList("监测血氧水平", "保持空气流通"))
                .build();
    }

    /**
     * 创建预测记录
     */
    private HealthPrediction createPredictionRecord(Long userId, Long customerId, String feature, 
                                                  String predictionType, HealthPredictionModelConfig modelConfig, 
                                                  PredictionResult predictionResult, LocalDate predictionDate, 
                                                  Integer predictionHorizonDays) {
        
        HealthPrediction prediction = new HealthPrediction();
        prediction.setUserId(userId);
        prediction.setCustomerId(customerId);
        prediction.setFeatureName(feature);
        prediction.setPredictionType(predictionType);
        prediction.setModelType(predictionResult.getModelType());
        prediction.setModelVersion(modelConfig.getModelVersion());
        prediction.setPredictionDate(predictionDate);
        prediction.setPredictionStartDate(predictionDate.plusDays(1));
        prediction.setPredictionEndDate(predictionDate.plusDays(predictionHorizonDays));
        prediction.setPredictionHorizonDays(predictionHorizonDays);
        prediction.setConfidenceScore(BigDecimal.valueOf(predictionResult.getConfidenceScore()));
        prediction.setPredictionStatus("completed");
        prediction.setCreatedBy("system");
        
        // 设置预测值序列
        Map<String, Object> predictedValues = new HashMap<>();
        predictedValues.put("values", predictionResult.getPredictedValues());
        predictedValues.put("dates", generatePredictionDates(predictionDate, predictionHorizonDays));
        prediction.setPredictedValues(convertMapToJson(predictedValues));
        
        // 设置预测详情
        Map<String, Object> details = new HashMap<>();
        details.put("trend_direction", predictionResult.getTrendDirection());
        details.put("model_type", predictionResult.getModelType());
        details.put("feature_analyzed", feature);
        details.put("confidence_level", getConfidenceLevel(predictionResult.getConfidenceScore()));
        prediction.setPredictionDetails(convertMapToJson(details));
        
        return prediction;
    }

    private List<String> generatePredictionDates(LocalDate startDate, int days) {
        List<String> dates = new ArrayList<>();
        for (int i = 1; i <= days; i++) {
            dates.add(startDate.plusDays(i).toString());
        }
        return dates;
    }

    private String getConfidenceLevel(double confidence) {
        if (confidence >= 0.8) return "high";
        else if (confidence >= 0.6) return "medium"; 
        else return "low";
    }

    // ==================== 内部数据类 ====================

    @lombok.Data
    @lombok.Builder
    private static class PredictionResult {
        private List<Double> predictedValues;
        private double confidenceScore;
        private String trendDirection;
        private String modelType;
    }

    @lombok.Data
    @lombok.Builder 
    private static class RiskAssessmentResult {
        private double riskScore;
        private String riskLevel;
        private double confidence;
        private List<String> riskFactors;
        private List<String> warningIndicators;
        private List<String> recommendedActions;
    }

    /**
     * 将 Map 对象转换为 JSON 字符串
     */
    private String convertMapToJson(Map<String, Object> map) {
        try {
            return objectMapper.writeValueAsString(map);
        } catch (Exception e) {
            log.warn("转换 Map 为 JSON 失败: {}", e.getMessage());
            return "{}";
        }
    }
}