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

package com.ljwx.modules.health.service.impl;

import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.service.HealthAnalyticsService;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Health Analytics Service Implementation 健康数据分析服务实现
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.HealthAnalyticsServiceImpl
 * @CreateTime 2025-01-15
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class HealthAnalyticsServiceImpl implements HealthAnalyticsService {

    private final ITUserHealthDataService userHealthDataService;
    private final ITHealthDataConfigService healthDataConfigService;

    // 健康指标正常范围配置
    private static final Map<String, Map<String, Double>> HEALTH_STANDARDS = Map.of(
        "heart_rate", Map.of("min", 60.0, "max", 100.0),
        "blood_oxygen", Map.of("min", 95.0, "max", 100.0),
        "temperature", Map.of("min", 36.1, "max", 37.2),
        "pressure_high", Map.of("min", 90.0, "max", 140.0),
        "pressure_low", Map.of("min", 60.0, "max", 90.0),
        "step", Map.of("min", 6000.0, "max", 15000.0),
        "sleep", Map.of("min", 7.0, "max", 9.0),
        "stress", Map.of("min", 0.0, "max", 30.0),
        "calorie", Map.of("min", 1200.0, "max", 2500.0),
        "distance", Map.of("min", 3.0, "max", 10.0)
    );

    @Override
    public Map<String, Object> calculateHealthMetrics(Long customerId, String orgId, String userId, 
                                                       LocalDateTime startDate, LocalDateTime endDate, String timeType) {
        try {
            log.info("🔍 计算健康指标统计: customerId={}, userId={}, timeType={}", customerId, userId, timeType);

            // 查询健康数据
            List<TUserHealthData> healthDataList = queryHealthData(customerId, orgId, userId, startDate, endDate);
            
            if (healthDataList.isEmpty()) {
                return createEmptyMetrics();
            }

            Map<String, Object> metrics = new HashMap<>();
            
            // 计算当前值（最新值）
            Map<String, Object> current = calculateCurrentValues(healthDataList);
            metrics.put("current", current);
            
            // 计算平均值
            Map<String, Object> average = calculateAverageValues(healthDataList);
            metrics.put("average", average);
            
            // 计算趋势
            Map<String, String> trend = calculateTrends(healthDataList);
            metrics.put("trend", trend);
            
            // 计算状态
            Map<String, String> status = calculateStatus(current);
            metrics.put("status", status);
            
            // 生成建议
            List<String> recommendations = generateSimpleRecommendations(current, status);
            metrics.put("recommendations", recommendations);

            log.info("✅ 健康指标统计计算完成: 指标数={}", current.size());
            return metrics;
            
        } catch (Exception e) {
            log.error("❌ 计算健康指标统计失败", e);
            return createEmptyMetrics();
        }
    }

    @Override
    public Map<String, Object> calculateHealthScore(Long customerId, String orgId, String userId, 
                                                     LocalDateTime startDate, LocalDateTime endDate) {
        try {
            log.info("📊 计算健康评分: customerId={}, userId={}", customerId, userId);

            List<TUserHealthData> healthDataList = queryHealthData(customerId, orgId, userId, startDate, endDate);
            
            if (healthDataList.isEmpty()) {
                return Map.of("score", 0, "level", "unknown", "description", "暂无数据");
            }

            // 计算当前值
            Map<String, Object> current = calculateCurrentValues(healthDataList);
            
            // 计算各指标评分
            Map<String, Integer> metricScores = new HashMap<>();
            int totalScore = 0;
            int metricCount = 0;

            for (Map.Entry<String, Object> entry : current.entrySet()) {
                String metric = entry.getKey();
                Object value = entry.getValue();
                
                if (value instanceof Number && HEALTH_STANDARDS.containsKey(metric)) {
                    int score = calculateMetricScore(metric, ((Number) value).doubleValue());
                    metricScores.put(metric, score);
                    totalScore += score;
                    metricCount++;
                }
            }

            int healthScore = metricCount > 0 ? totalScore / metricCount : 0;
            
            Map<String, Object> result = new HashMap<>();
            result.put("score", healthScore);
            result.put("level", getHealthLevel(healthScore));
            result.put("description", getHealthDescription(healthScore));
            result.put("metricScores", metricScores);
            result.put("metricCount", metricCount);

            log.info("✅ 健康评分计算完成: score={}, level={}", healthScore, result.get("level"));
            return result;
            
        } catch (Exception e) {
            log.error("❌ 计算健康评分失败", e);
            return Map.of("score", 0, "level", "error", "description", "计算失败");
        }
    }

    @Override
    public Map<String, Object> generateHealthRecommendations(Long customerId, String orgId, String userId, 
                                                               LocalDateTime startDate, LocalDateTime endDate) {
        try {
            log.info("💡 生成健康建议: customerId={}, userId={}", customerId, userId);

            List<TUserHealthData> healthDataList = queryHealthData(customerId, orgId, userId, startDate, endDate);
            
            if (healthDataList.isEmpty()) {
                return Map.of("recommendations", Collections.singletonList("暂无健康数据，无法提供建议"));
            }

            Map<String, Object> current = calculateCurrentValues(healthDataList);
            Map<String, String> status = calculateStatus(current);
            
            List<String> recommendations = new ArrayList<>();
            
            // 基于状态生成建议
            for (Map.Entry<String, String> entry : status.entrySet()) {
                String metric = entry.getKey();
                String metricStatus = entry.getValue();
                Object value = current.get(metric);
                
                if ("danger".equals(metricStatus) && value instanceof Number) {
                    recommendations.addAll(generateMetricRecommendations(metric, ((Number) value).doubleValue(), metricStatus));
                } else if ("warning".equals(metricStatus)) {
                    recommendations.add(getMetricName(metric) + "需要关注，建议保持健康生活方式");
                }
            }
            
            // 如果没有异常，给出一般性建议
            if (recommendations.isEmpty()) {
                recommendations.add("各项健康指标正常，继续保持良好的生活习惯！");
                recommendations.add("建议定期监测健康数据，保持适量运动");
                recommendations.add("注意饮食均衡，保证充足睡眠");
            }

            Map<String, Object> result = new HashMap<>();
            result.put("recommendations", recommendations);
            result.put("priority", determinePriority(status));
            result.put("urgency", determineUrgency(status));

            log.info("✅ 健康建议生成完成: 建议数={}", recommendations.size());
            return result;
            
        } catch (Exception e) {
            log.error("❌ 生成健康建议失败", e);
            return Map.of("recommendations", Collections.singletonList("生成建议失败"));
        }
    }

    @Override
    public Map<String, Object> analyzeHealthTrends(Long customerId, String orgId, String userId, 
                                                     LocalDateTime startDate, LocalDateTime endDate, String metricType) {
        try {
            log.info("📈 分析健康趋势: customerId={}, userId={}, metricType={}", customerId, userId, metricType);

            List<TUserHealthData> healthDataList = queryHealthData(customerId, orgId, userId, startDate, endDate);
            
            if (healthDataList.isEmpty()) {
                return Map.of("trends", Collections.emptyMap(), "analysis", "暂无数据");
            }

            Map<String, Object> trends = new HashMap<>();
            
            if (StringUtils.hasText(metricType)) {
                // 分析特定指标趋势
                Map<String, Object> metricTrend = analyzeMetricTrend(healthDataList, metricType);
                trends.put(metricType, metricTrend);
            } else {
                // 分析所有指标趋势
                for (String metric : HEALTH_STANDARDS.keySet()) {
                    Map<String, Object> metricTrend = analyzeMetricTrend(healthDataList, metric);
                    if (!metricTrend.isEmpty()) {
                        trends.put(metric, metricTrend);
                    }
                }
            }

            Map<String, Object> result = new HashMap<>();
            result.put("trends", trends);
            result.put("analysis", generateTrendAnalysis(trends));
            result.put("period", Map.of("start", startDate, "end", endDate));

            log.info("✅ 健康趋势分析完成: 指标数={}", trends.size());
            return result;
            
        } catch (Exception e) {
            log.error("❌ 分析健康趋势失败", e);
            return Map.of("trends", Collections.emptyMap(), "analysis", "分析失败");
        }
    }

    @Override
    public Map<String, Object> getComprehensiveAnalysis(Long customerId, String orgId, String userId, 
                                                          LocalDateTime startDate, LocalDateTime endDate, String timeType) {
        try {
            log.info("🏥 获取综合健康分析: customerId={}, userId={}", customerId, userId);

            Map<String, Object> comprehensive = new HashMap<>();
            
            // 获取健康指标
            Map<String, Object> metrics = calculateHealthMetrics(customerId, orgId, userId, startDate, endDate, timeType);
            comprehensive.put("metrics", metrics);
            
            // 获取健康评分
            Map<String, Object> score = calculateHealthScore(customerId, orgId, userId, startDate, endDate);
            comprehensive.put("score", score);
            
            // 获取健康建议
            Map<String, Object> recommendations = generateHealthRecommendations(customerId, orgId, userId, startDate, endDate);
            comprehensive.put("recommendations", recommendations);
            
            // 获取趋势分析
            Map<String, Object> trends = analyzeHealthTrends(customerId, orgId, userId, startDate, endDate, null);
            comprehensive.put("trends", trends);
            
            // 生成综合评估
            String assessment = generateComprehensiveAssessment(score, metrics, trends);
            comprehensive.put("assessment", assessment);
            
            comprehensive.put("timestamp", LocalDateTime.now());
            comprehensive.put("period", Map.of("start", startDate, "end", endDate, "type", timeType));

            log.info("✅ 综合健康分析完成");
            return comprehensive;
            
        } catch (Exception e) {
            log.error("❌ 获取综合健康分析失败", e);
            return Map.of("error", "综合分析失败: " + e.getMessage());
        }
    }

    // 私有辅助方法

    private List<TUserHealthData> queryHealthData(Long customerId, String orgId, String userId, 
                                                   LocalDateTime startDate, LocalDateTime endDate) {
        try {
            log.debug("查询健康数据: customerId={}, orgId={}, userId={}", customerId, orgId, userId);
            
            // 如果没有指定用户ID，返回空列表
            if (StringUtils.isEmpty(userId) || "all".equals(userId) || "0".equals(userId)) {
                log.debug("未指定用户ID或查询所有用户，返回空列表");
                return Collections.emptyList();
            }
            
            Long userIdLong;
            try {
                userIdLong = Long.valueOf(userId);
            } catch (NumberFormatException e) {
                log.warn("用户ID格式错误: userId={}", userId);
                return Collections.emptyList();
            }
            
            // 限制查询范围，避免大数据量查询
            long daysDiff = java.time.Duration.between(startDate, endDate).toDays();
            if (daysDiff > 31) {
                log.warn("查询时间范围过大：{}天，限制为最近31天", daysDiff);
                startDate = endDate.minusDays(31);
            }
            
            // 使用 userHealthDataService 查询数据
            // 注意：这里需要通过MyBatis-Plus直接查询，因为原getUserHealthData返回的是复杂的聚合数据
            return userHealthDataService.lambdaQuery()
                    .eq(TUserHealthData::getUserId, userIdLong)
                    .ge(TUserHealthData::getTimestamp, startDate)
                    .le(TUserHealthData::getTimestamp, endDate)
                    .ne(TUserHealthData::getUploadMethod, "common_event") // 过滤掉common_event数据
                    .orderByDesc(TUserHealthData::getTimestamp) // 按时间倒序，获取最新数据
                    .last("LIMIT 1000") // 限制查询数量，避免性能问题
                    .list();
                    
        } catch (Exception e) {
            log.error("查询健康数据失败: customerId={}, userId={}", customerId, userId, e);
            return Collections.emptyList();
        }
    }

    private Map<String, Object> createEmptyMetrics() {
        return Map.of(
            "current", Collections.emptyMap(),
            "average", Collections.emptyMap(),
            "trend", Collections.emptyMap(),
            "status", Collections.emptyMap(),
            "recommendations", Collections.singletonList("暂无健康数据")
        );
    }

    private Map<String, Object> calculateCurrentValues(List<TUserHealthData> dataList) {
        if (dataList.isEmpty()) return Collections.emptyMap();
        
        // 获取最新的数据记录
        TUserHealthData latest = dataList.stream()
                .max(Comparator.comparing(TUserHealthData::getTimestamp))
                .orElse(null);
                
        if (latest == null) return Collections.emptyMap();
        
        Map<String, Object> current = new HashMap<>();
        addIfNotNull(current, "heart_rate", latest.getHeartRate());
        addIfNotNull(current, "blood_oxygen", latest.getBloodOxygen());
        addIfNotNull(current, "temperature", latest.getTemperature());
        addIfNotNull(current, "pressure_high", latest.getPressureHigh());
        addIfNotNull(current, "pressure_low", latest.getPressureLow());
        addIfNotNull(current, "step", latest.getStep());
        addIfNotNull(current, "stress", latest.getStress());
        addIfNotNull(current, "calorie", latest.getCalorie());
        addIfNotNull(current, "distance", latest.getDistance());
        
        // 注意：睡眠数据已迁移到分表，这里暂不添加睡眠数据
        // 如需睡眠数据，需要单独查询 THealthDataSlowDaily 表
        
        return current;
    }

    private Map<String, Object> calculateAverageValues(List<TUserHealthData> dataList) {
        if (dataList.isEmpty()) return Collections.emptyMap();
        
        Map<String, Object> averages = new HashMap<>();
        
        // 计算心率平均值
        OptionalDouble heartRateAvg = dataList.stream()
                .filter(d -> d.getHeartRate() != null && d.getHeartRate() > 0)
                .mapToDouble(d -> d.getHeartRate().doubleValue())
                .average();
        if (heartRateAvg.isPresent()) {
            averages.put("heart_rate", BigDecimal.valueOf(heartRateAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算血氧平均值
        OptionalDouble bloodOxygenAvg = dataList.stream()
                .filter(d -> d.getBloodOxygen() != null && d.getBloodOxygen() > 0)
                .mapToDouble(d -> d.getBloodOxygen().doubleValue())
                .average();
        if (bloodOxygenAvg.isPresent()) {
            averages.put("blood_oxygen", BigDecimal.valueOf(bloodOxygenAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算体温平均值
        OptionalDouble temperatureAvg = dataList.stream()
                .filter(d -> d.getTemperature() != null && d.getTemperature() > 0)
                .mapToDouble(TUserHealthData::getTemperature)
                .average();
        if (temperatureAvg.isPresent()) {
            averages.put("temperature", BigDecimal.valueOf(temperatureAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算收缩压平均值
        OptionalDouble pressureHighAvg = dataList.stream()
                .filter(d -> d.getPressureHigh() != null && d.getPressureHigh() > 0)
                .mapToDouble(d -> d.getPressureHigh().doubleValue())
                .average();
        if (pressureHighAvg.isPresent()) {
            averages.put("pressure_high", BigDecimal.valueOf(pressureHighAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算舒张压平均值
        OptionalDouble pressureLowAvg = dataList.stream()
                .filter(d -> d.getPressureLow() != null && d.getPressureLow() > 0)
                .mapToDouble(d -> d.getPressureLow().doubleValue())
                .average();
        if (pressureLowAvg.isPresent()) {
            averages.put("pressure_low", BigDecimal.valueOf(pressureLowAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算步数平均值
        OptionalDouble stepAvg = dataList.stream()
                .filter(d -> d.getStep() != null && d.getStep() > 0)
                .mapToDouble(d -> d.getStep().doubleValue())
                .average();
        if (stepAvg.isPresent()) {
            averages.put("step", BigDecimal.valueOf(stepAvg.getAsDouble()).setScale(0, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算压力指数平均值
        OptionalDouble stressAvg = dataList.stream()
                .filter(d -> d.getStress() != null && d.getStress() >= 0)
                .mapToDouble(d -> d.getStress().doubleValue())
                .average();
        if (stressAvg.isPresent()) {
            averages.put("stress", BigDecimal.valueOf(stressAvg.getAsDouble()).setScale(1, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算卡路里平均值
        OptionalDouble calorieAvg = dataList.stream()
                .filter(d -> d.getCalorie() != null && d.getCalorie() > 0)
                .mapToDouble(TUserHealthData::getCalorie)
                .average();
        if (calorieAvg.isPresent()) {
            averages.put("calorie", BigDecimal.valueOf(calorieAvg.getAsDouble()).setScale(0, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 计算距离平均值
        OptionalDouble distanceAvg = dataList.stream()
                .filter(d -> d.getDistance() != null && d.getDistance() > 0)
                .mapToDouble(TUserHealthData::getDistance)
                .average();
        if (distanceAvg.isPresent()) {
            averages.put("distance", BigDecimal.valueOf(distanceAvg.getAsDouble()).setScale(2, RoundingMode.HALF_UP).doubleValue());
        }
        
        // 注意：睡眠数据已迁移到分表，这里暂不计算睡眠平均值
        // 如需睡眠数据，需要单独查询 THealthDataSlowDaily 表
        
        return averages;
    }

    private Map<String, String> calculateTrends(List<TUserHealthData> dataList) {
        Map<String, String> trends = new HashMap<>();
        
        if (dataList.size() < 3) {
            // 数据不足，无法计算趋势
            return trends;
        }
        
        // 按时间排序
        List<TUserHealthData> sortedData = dataList.stream()
                .sorted(Comparator.comparing(TUserHealthData::getTimestamp))
                .collect(Collectors.toList());
        
        trends.put("heart_rate", calculateMetricTrend(sortedData, d -> d.getHeartRate() != null ? d.getHeartRate().doubleValue() : null));
        trends.put("blood_oxygen", calculateMetricTrend(sortedData, d -> d.getBloodOxygen() != null ? d.getBloodOxygen().doubleValue() : null));
        trends.put("temperature", calculateMetricTrend(sortedData, d -> d.getTemperature()));
        trends.put("pressure_high", calculateMetricTrend(sortedData, d -> d.getPressureHigh() != null ? d.getPressureHigh().doubleValue() : null));
        trends.put("pressure_low", calculateMetricTrend(sortedData, d -> d.getPressureLow() != null ? d.getPressureLow().doubleValue() : null));
        trends.put("step", calculateMetricTrend(sortedData, d -> d.getStep() != null ? d.getStep().doubleValue() : null));
        trends.put("stress", calculateMetricTrend(sortedData, d -> d.getStress() != null ? d.getStress().doubleValue() : null));
        trends.put("calorie", calculateMetricTrend(sortedData, d -> d.getCalorie()));
        trends.put("distance", calculateMetricTrend(sortedData, d -> d.getDistance()));
        
        return trends;
    }

    private String calculateMetricTrend(List<TUserHealthData> sortedData, 
                                         java.util.function.Function<TUserHealthData, Double> valueExtractor) {
        List<Double> values = sortedData.stream()
                .map(valueExtractor)
                .filter(Objects::nonNull)
                .filter(v -> v > 0)
                .collect(Collectors.toList());
        
        if (values.size() < 3) return "stable";
        
        // 取最近的数据和之前的数据进行对比
        int recentCount = Math.min(3, values.size() / 3);
        double recentAvg = values.subList(values.size() - recentCount, values.size())
                .stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double earlierAvg = values.subList(0, values.size() - recentCount)
                .stream().mapToDouble(Double::doubleValue).average().orElse(0);
        
        double changePercent = earlierAvg > 0 ? ((recentAvg - earlierAvg) / earlierAvg) * 100 : 0;
        
        if (changePercent > 5) return "up";
        else if (changePercent < -5) return "down";
        else return "stable";
    }

    private Map<String, String> calculateStatus(Map<String, Object> current) {
        Map<String, String> status = new HashMap<>();
        
        for (Map.Entry<String, Object> entry : current.entrySet()) {
            String metric = entry.getKey();
            Object value = entry.getValue();
            
            if (value instanceof Number && HEALTH_STANDARDS.containsKey(metric)) {
                double numValue = ((Number) value).doubleValue();
                Map<String, Double> standard = HEALTH_STANDARDS.get(metric);
                double min = standard.get("min");
                double max = standard.get("max");
                
                if (numValue >= min && numValue <= max) {
                    status.put(metric, "normal");
                } else if (numValue < min * 0.8 || numValue > max * 1.2) {
                    status.put(metric, "danger");
                } else {
                    status.put(metric, "warning");
                }
            }
        }
        
        return status;
    }

    private List<String> generateSimpleRecommendations(Map<String, Object> current, Map<String, String> status) {
        List<String> recommendations = new ArrayList<>();
        
        for (Map.Entry<String, String> entry : status.entrySet()) {
            String metric = entry.getKey();
            String metricStatus = entry.getValue();
            
            if ("danger".equals(metricStatus)) {
                recommendations.addAll(generateMetricRecommendations(metric, 
                    current.get(metric) instanceof Number ? ((Number) current.get(metric)).doubleValue() : 0, 
                    metricStatus));
            }
        }
        
        if (recommendations.isEmpty()) {
            recommendations.add("各项健康指标正常，继续保持良好的生活习惯！");
        }
        
        return recommendations;
    }

    private List<String> generateMetricRecommendations(String metric, double value, String status) {
        List<String> recommendations = new ArrayList<>();
        
        switch (metric) {
            case "heart_rate":
                if ("danger".equals(status)) {
                    if (value > 100) {
                        recommendations.add("心率偏高，建议减少剧烈运动，保持情绪稳定");
                    } else {
                        recommendations.add("心率偏低，建议适当增加有氧运动");
                    }
                }
                break;
            case "blood_oxygen":
                if ("danger".equals(status) && value < 95) {
                    recommendations.add("血氧偏低，建议进行深呼吸练习，如有持续请就医");
                }
                break;
            case "step":
                if ("danger".equals(status) && value < 6000) {
                    recommendations.add("运动量不足，建议每天至少6000步，增加日常活动");
                }
                break;
            case "sleep":
                if ("danger".equals(status) && value < 7) {
                    recommendations.add("睡眠不足，建议保持规律作息，每晚7-9小时睡眠");
                }
                break;
            default:
                recommendations.add(getMetricName(metric) + "需要关注，建议咨询医生");
        }
        
        return recommendations;
    }

    private int calculateMetricScore(String metric, double value) {
        Map<String, Double> standard = HEALTH_STANDARDS.get(metric);
        if (standard == null) return 50;
        
        double min = standard.get("min");
        double max = standard.get("max");
        
        if (value >= min && value <= max) {
            return 100; // 正常范围
        } else if (value < min * 0.8 || value > max * 1.2) {
            return 30; // 危险范围
        } else {
            return 70; // 警告范围
        }
    }

    private String getHealthLevel(int score) {
        if (score >= 90) return "excellent";
        if (score >= 75) return "good";
        if (score >= 60) return "fair";
        return "poor";
    }

    private String getHealthDescription(int score) {
        if (score >= 90) return "健康状况优秀";
        if (score >= 75) return "健康状况良好";
        if (score >= 60) return "健康状况一般";
        return "健康状况需要改善";
    }

    private String getMetricName(String metric) {
        return switch (metric) {
            case "heart_rate" -> "心率";
            case "blood_oxygen" -> "血氧";
            case "temperature" -> "体温";
            case "pressure_high" -> "收缩压";
            case "pressure_low" -> "舒张压";
            case "step" -> "步数";
            case "sleep" -> "睡眠";
            case "stress" -> "压力";
            case "calorie" -> "卡路里";
            case "distance" -> "距离";
            default -> metric;
        };
    }

    private String determinePriority(Map<String, String> status) {
        long dangerCount = status.values().stream().filter("danger"::equals).count();
        long warningCount = status.values().stream().filter("warning"::equals).count();
        
        if (dangerCount > 0) return "high";
        if (warningCount > 0) return "medium";
        return "low";
    }

    private String determineUrgency(Map<String, String> status) {
        long dangerCount = status.values().stream().filter("danger"::equals).count();
        return dangerCount > 2 ? "urgent" : "normal";
    }

    private Map<String, Object> analyzeMetricTrend(List<TUserHealthData> dataList, String metric) {
        Map<String, Object> trend = new HashMap<>();
        
        if (dataList.isEmpty()) {
            trend.put("trend", "stable");
            trend.put("direction", 0);
            trend.put("changePercent", 0.0);
            trend.put("dataPoints", 0);
            return trend;
        }
        
        // 根据指标类型提取数值
        List<Double> values = new ArrayList<>();
        List<LocalDateTime> timestamps = new ArrayList<>();
        
        for (TUserHealthData data : dataList) {
            Double value = extractMetricValue(data, metric);
            if (value != null && value > 0) {
                values.add(value);
                timestamps.add(data.getTimestamp());
            }
        }
        
        if (values.size() < 2) {
            trend.put("trend", "stable");
            trend.put("direction", 0);
            trend.put("changePercent", 0.0);
            trend.put("dataPoints", values.size());
            return trend;
        }
        
        // 计算趋势（简单的线性回归或者首末值对比）
        double firstValue = values.get(0);
        double lastValue = values.get(values.size() - 1);
        double changePercent = firstValue > 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;
        
        // 计算平均变化率
        double totalChange = 0;
        for (int i = 1; i < values.size(); i++) {
            if (values.get(i - 1) > 0) {
                totalChange += ((values.get(i) - values.get(i - 1)) / values.get(i - 1)) * 100;
            }
        }
        double avgChangePercent = totalChange / (values.size() - 1);
        
        // 确定趋势方向
        String trendDirection;
        int direction;
        if (Math.abs(avgChangePercent) < 2) {
            trendDirection = "stable";
            direction = 0;
        } else if (avgChangePercent > 0) {
            trendDirection = "up";
            direction = 1;
        } else {
            trendDirection = "down";
            direction = -1;
        }
        
        trend.put("trend", trendDirection);
        trend.put("direction", direction);
        trend.put("changePercent", BigDecimal.valueOf(changePercent).setScale(2, RoundingMode.HALF_UP).doubleValue());
        trend.put("avgChangePercent", BigDecimal.valueOf(avgChangePercent).setScale(2, RoundingMode.HALF_UP).doubleValue());
        trend.put("dataPoints", values.size());
        trend.put("firstValue", firstValue);
        trend.put("lastValue", lastValue);
        trend.put("maxValue", values.stream().max(Double::compareTo).orElse(0.0));
        trend.put("minValue", values.stream().min(Double::compareTo).orElse(0.0));
        trend.put("avgValue", values.stream().mapToDouble(Double::doubleValue).average().orElse(0.0));
        
        return trend;
    }
    
    private Double extractMetricValue(TUserHealthData data, String metric) {
        return switch (metric) {
            case "heart_rate" -> data.getHeartRate() != null ? data.getHeartRate().doubleValue() : null;
            case "blood_oxygen" -> data.getBloodOxygen() != null ? data.getBloodOxygen().doubleValue() : null;
            case "temperature" -> data.getTemperature();
            case "pressure_high" -> data.getPressureHigh() != null ? data.getPressureHigh().doubleValue() : null;
            case "pressure_low" -> data.getPressureLow() != null ? data.getPressureLow().doubleValue() : null;
            case "step" -> data.getStep() != null ? data.getStep().doubleValue() : null;
            case "stress" -> data.getStress() != null ? data.getStress().doubleValue() : null;
            case "calorie" -> data.getCalorie();
            case "distance" -> data.getDistance();
            default -> null;
        };
    }

    private String generateTrendAnalysis(Map<String, Object> trends) {
        if (trends.isEmpty()) {
            return "暂无趋势数据";
        }
        
        return "健康指标趋势分析显示总体" + (trends.size() > 5 ? "稳定" : "波动") + "状态";
    }

    private String generateComprehensiveAssessment(Map<String, Object> score, 
                                                   Map<String, Object> metrics, 
                                                   Map<String, Object> trends) {
        Object scoreObj = score.get("score");
        int healthScore = scoreObj instanceof Number ? ((Number) scoreObj).intValue() : 0;
        
        if (healthScore >= 80) {
            return "综合健康状况良好，建议继续保持当前的健康管理方式";
        } else if (healthScore >= 60) {
            return "综合健康状况一般，建议加强健康监测和生活方式调整";
        } else {
            return "综合健康状况需要关注，建议咨询医生并制定健康改善计划";
        }
    }

    private void addIfNotNull(Map<String, Object> map, String key, Object value) {
        if (value != null && (!(value instanceof Number) || ((Number) value).doubleValue() > 0)) {
            map.put(key, value);
        }
    }
}