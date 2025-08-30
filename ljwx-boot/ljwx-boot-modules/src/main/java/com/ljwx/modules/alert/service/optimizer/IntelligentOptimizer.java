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

package com.ljwx.modules.alert.service.optimizer;

import com.ljwx.modules.alert.service.monitor.AlertProcessingMonitor;
import com.ljwx.modules.alert.service.monitor.MetricsCollector;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 智能优化建议系统
 * 基于历史数据和实时监控提供系统优化建议
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.optimizer.IntelligentOptimizer
 * @CreateTime 2024-08-30 - 21:00:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class IntelligentOptimizer {

    private final AlertProcessingMonitor processingMonitor;
    private final MetricsCollector metricsCollector;
    private final AlertTrendPredictor trendPredictor;

    /**
     * 生成优化计划
     */
    public OptimizationPlan generateOptimizationPlan(int timeRangeDays) {
        log.info("开始生成优化计划: timeRange={}天", timeRangeDays);
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. 历史数据分析
            Map<String, Object> historicalAnalysis = analyzeHistoricalPerformance(timeRangeDays);
            log.debug("历史数据分析完成");
            
            // 2. 未来趋势预测
            Map<String, Object> futurePrediction = trendPredictor.predictAlertTrends(timeRangeDays);
            log.debug("趋势预测完成");
            
            // 3. 系统瓶颈识别
            List<SystemBottleneck> bottlenecks = identifySystemBottlenecks();
            log.debug("瓶颈识别完成: count={}", bottlenecks.size());
            
            // 4. 生成优化建议
            List<OptimizationRecommendation> recommendations = generateRecommendations(
                    historicalAnalysis, futurePrediction, bottlenecks);
            log.debug("优化建议生成完成: count={}", recommendations.size());
            
            // 5. 估算改进效果
            Map<String, Object> estimatedImprovements = estimateImprovements(recommendations);
            
            OptimizationPlan plan = OptimizationPlan.builder()
                    .analysisPeriod(timeRangeDays)
                    .generatedAt(LocalDateTime.now())
                    .historicalSummary(historicalAnalysis)
                    .futurePredictions(futurePrediction)
                    .identifiedBottlenecks(bottlenecks)
                    .optimizationPlan(recommendations)
                    .estimatedImprovements(estimatedImprovements)
                    .planValidityDays(7) // 计划有效期7天
                    .build();
            
            long planningTime = System.currentTimeMillis() - startTime;
            log.info("优化计划生成完成: recommendations={}, bottlenecks={}, time={}ms", 
                    recommendations.size(), bottlenecks.size(), planningTime);
            
            return plan;
            
        } catch (Exception e) {
            long planningTime = System.currentTimeMillis() - startTime;
            log.error("生成优化计划失败: timeRange={}, time={}ms", timeRangeDays, planningTime, e);
            
            return createFallbackPlan(e);
        }
    }

    /**
     * 分析历史性能数据
     */
    private Map<String, Object> analyzeHistoricalPerformance(int days) {
        Map<String, Object> analysis = new HashMap<>();
        
        try {
            // 获取性能快照
            MetricsCollector.AlertMetricsSnapshot snapshot = metricsCollector.getMetricsSnapshot();
            
            // 基础性能指标
            analysis.put("avgProcessingTime", snapshot.getAvgProcessingTime());
            analysis.put("errorRate", snapshot.getErrorRate());
            analysis.put("throughput", snapshot.getThroughput());
            analysis.put("totalProcessed", snapshot.getTotalProcessed());
            
            // 性能等级评估
            String performanceGrade = calculatePerformanceGrade(snapshot);
            analysis.put("performanceGrade", performanceGrade);
            
            // 关键问题识别
            List<String> criticalIssues = identifyCriticalIssues(snapshot);
            analysis.put("criticalIssues", criticalIssues);
            
            // 成功率分析
            double successRate = snapshot.getTotalProcessed() > 0 ? 
                    1.0 - snapshot.getErrorRate() : 1.0;
            analysis.put("successRate", successRate);
            
            // 稳定性评估
            String stabilityAssessment = assessSystemStability(snapshot);
            analysis.put("stabilityAssessment", stabilityAssessment);
            
        } catch (Exception e) {
            log.error("分析历史性能数据失败", e);
            analysis.put("error", e.getMessage());
        }
        
        return analysis;
    }

    /**
     * 识别系统瓶颈
     */
    private List<SystemBottleneck> identifySystemBottlenecks() {
        List<SystemBottleneck> bottlenecks = new ArrayList<>();
        
        try {
            // 获取当前监控数据
            Map<String, Object> monitoringData = processingMonitor.monitorProcessingPerformance();
            @SuppressWarnings("unchecked")
            Map<String, Object> currentMetrics = (Map<String, Object>) monitoringData.get("currentMetrics");
            
            if (currentMetrics != null) {
                // 处理时间瓶颈
                identifyProcessingTimeBottlenecks(currentMetrics, bottlenecks);
                
                // 队列瓶颈
                identifyQueueBottlenecks(currentMetrics, bottlenecks);
                
                // 资源瓶颈
                identifyResourceBottlenecks(currentMetrics, bottlenecks);
                
                // 错误率瓶颈
                identifyErrorRateBottlenecks(currentMetrics, bottlenecks);
            }
            
        } catch (Exception e) {
            log.error("识别系统瓶颈失败", e);
        }
        
        return bottlenecks;
    }

    /**
     * 生成优化建议
     */
    private List<OptimizationRecommendation> generateRecommendations(
            Map<String, Object> historical, 
            Map<String, Object> prediction, 
            List<SystemBottleneck> bottlenecks) {
        
        List<OptimizationRecommendation> recommendations = new ArrayList<>();
        
        try {
            // 基于历史数据的建议
            generateHistoricalBasedRecommendations(historical, recommendations);
            
            // 基于预测数据的建议
            generatePredictionBasedRecommendations(prediction, recommendations);
            
            // 基于瓶颈分析的建议
            generateBottleneckBasedRecommendations(bottlenecks, recommendations);
            
            // 系统架构建议
            generateArchitecturalRecommendations(historical, recommendations);
            
            // 按优先级排序
            recommendations.sort((r1, r2) -> r2.getPriority().compareTo(r1.getPriority()));
            
        } catch (Exception e) {
            log.error("生成优化建议失败", e);
        }
        
        return recommendations;
    }

    /**
     * 基于历史数据生成建议
     */
    private void generateHistoricalBasedRecommendations(
            Map<String, Object> historical, 
            List<OptimizationRecommendation> recommendations) {
        
        // 误报率优化
        Object errorRateObj = historical.get("errorRate");
        if (errorRateObj instanceof Number) {
            double errorRate = ((Number) errorRateObj).doubleValue();
            if (errorRate > 0.15) {
                recommendations.add(OptimizationRecommendation.builder()
                        .category("rule_optimization")
                        .priority(Priority.HIGH)
                        .title("优化告警规则降低误报率")
                        .description(String.format("当前误报率%.1f%%，建议调整规则阈值", errorRate * 100))
                        .implementationSteps(Arrays.asList(
                                "分析高误报的告警类型和设备",
                                "基于机器学习优化阈值设置",
                                "启用智能过滤算法",
                                "建立个人基线分析模型"
                        ))
                        .expectedImprovement("误报率降低至8%以下")
                        .implementationEffort(ImplementationEffort.MEDIUM)
                        .estimatedTimeDays(7)
                        .build());
            }
        }
        
        // 处理时间优化
        Object avgTimeObj = historical.get("avgProcessingTime");
        if (avgTimeObj instanceof Number) {
            double avgTime = ((Number) avgTimeObj).doubleValue();
            if (avgTime > 3000) { // 超过3秒
                recommendations.add(OptimizationRecommendation.builder()
                        .category("performance_optimization")
                        .priority(Priority.MEDIUM)
                        .title("优化处理性能")
                        .description(String.format("平均处理时间%.0fms偏高，建议优化", avgTime))
                        .implementationSteps(Arrays.asList(
                                "优化AI分析算法",
                                "增加处理线程池大小",
                                "优化数据库查询",
                                "启用结果缓存"
                        ))
                        .expectedImprovement("处理时间降低30-50%")
                        .implementationEffort(ImplementationEffort.HIGH)
                        .estimatedTimeDays(10)
                        .build());
            }
        }
    }

    /**
     * 基于预测数据生成建议
     */
    private void generatePredictionBasedRecommendations(
            Map<String, Object> prediction, 
            List<OptimizationRecommendation> recommendations) {
        
        // 容量规划建议
        Object peakLoadObj = prediction.get("peakLoadPrediction");
        Object currentCapacityObj = prediction.get("currentCapacity");
        
        if (peakLoadObj instanceof Number && currentCapacityObj instanceof Number) {
            double peakLoad = ((Number) peakLoadObj).doubleValue();
            double currentCapacity = ((Number) currentCapacityObj).doubleValue();
            
            if (peakLoad > currentCapacity * 0.8) {
                recommendations.add(OptimizationRecommendation.builder()
                        .category("capacity_planning")
                        .priority(Priority.HIGH)
                        .title("扩展系统处理容量")
                        .description("预测未来负载将接近系统容量上限")
                        .implementationSteps(Arrays.asList(
                                "增加告警处理线程池大小",
                                "优化数据库连接池配置",
                                "考虑水平扩展处理节点",
                                "实施负载均衡策略"
                        ))
                        .expectedImprovement("处理能力提升50%")
                        .implementationEffort(ImplementationEffort.HIGH)
                        .estimatedTimeDays(14)
                        .build());
            }
        }
    }

    /**
     * 基于瓶颈分析生成建议
     */
    private void generateBottleneckBasedRecommendations(
            List<SystemBottleneck> bottlenecks,
            List<OptimizationRecommendation> recommendations) {
        
        for (SystemBottleneck bottleneck : bottlenecks) {
            switch (bottleneck.getType()) {
                case "database_query":
                    recommendations.add(OptimizationRecommendation.builder()
                            .category("performance_optimization")
                            .priority(Priority.MEDIUM)
                            .title("优化数据库查询性能")
                            .description(String.format("查询响应时间%dms偏高", bottleneck.getResponseTime()))
                            .implementationSteps(Arrays.asList(
                                    "添加必要的数据库索引",
                                    "优化复杂查询的执行计划",
                                    "考虑查询结果缓存",
                                    "数据库分区优化"
                            ))
                            .expectedImprovement("查询性能提升60%")
                            .implementationEffort(ImplementationEffort.MEDIUM)
                            .estimatedTimeDays(5)
                            .build());
                    break;
                    
                case "memory_usage":
                    recommendations.add(OptimizationRecommendation.builder()
                            .category("resource_optimization")
                            .priority(Priority.HIGH)
                            .title("优化内存使用")
                            .description("内存使用率过高，可能影响系统性能")
                            .implementationSteps(Arrays.asList(
                                    "分析内存泄漏问题",
                                    "优化对象缓存策略",
                                    "调整JVM堆内存配置",
                                    "实施内存监控告警"
                            ))
                            .expectedImprovement("内存使用率降低至70%以下")
                            .implementationEffort(ImplementationEffort.MEDIUM)
                            .estimatedTimeDays(3)
                            .build());
                    break;
            }
        }
    }

    /**
     * 生成架构建议
     */
    private void generateArchitecturalRecommendations(
            Map<String, Object> historical,
            List<OptimizationRecommendation> recommendations) {
        
        // 微服务拆分建议
        Object throughputObj = historical.get("throughput");
        if (throughputObj instanceof Number) {
            double throughput = ((Number) throughputObj).doubleValue();
            if (throughput > 500) { // 高吞吐量场景
                recommendations.add(OptimizationRecommendation.builder()
                        .category("architecture_optimization")
                        .priority(Priority.LOW)
                        .title("考虑微服务架构拆分")
                        .description("系统负载较高，建议考虑拆分为独立的微服务")
                        .implementationSteps(Arrays.asList(
                                "分析业务边界和服务职责",
                                "设计服务间通信机制",
                                "实施数据分离策略",
                                "建立服务监控体系"
                        ))
                        .expectedImprovement("提升系统可扩展性和可维护性")
                        .implementationEffort(ImplementationEffort.VERY_HIGH)
                        .estimatedTimeDays(30)
                        .build());
            }
        }
    }

    /**
     * 估算改进效果
     */
    private Map<String, Object> estimateImprovements(List<OptimizationRecommendation> recommendations) {
        Map<String, Object> improvements = new HashMap<>();
        
        // 分类统计
        Map<String, Long> categoryCount = recommendations.stream()
                .collect(Collectors.groupingBy(
                        OptimizationRecommendation::getCategory, 
                        Collectors.counting()));
        
        improvements.put("recommendationsByCategory", categoryCount);
        
        // 优先级分布
        Map<String, Long> priorityDistribution = recommendations.stream()
                .collect(Collectors.groupingBy(
                        r -> r.getPriority().name(), 
                        Collectors.counting()));
        
        improvements.put("priorityDistribution", priorityDistribution);
        
        // 预期改进
        double expectedPerformanceImprovement = calculateExpectedPerformanceImprovement(recommendations);
        improvements.put("expectedPerformanceImprovement", expectedPerformanceImprovement);
        
        // 实施工作量
        int totalEstimatedDays = recommendations.stream()
                .mapToInt(OptimizationRecommendation::getEstimatedTimeDays)
                .sum();
        
        improvements.put("totalEstimatedImplementationDays", totalEstimatedDays);
        
        // ROI估算
        String roiEstimate = estimateROI(recommendations);
        improvements.put("roiEstimate", roiEstimate);
        
        return improvements;
    }

    // 辅助方法实现
    private String calculatePerformanceGrade(MetricsCollector.AlertMetricsSnapshot snapshot) {
        double score = 0;
        
        // 错误率评分 (0-30分)
        double errorRate = snapshot.getErrorRate();
        if (errorRate < 0.05) score += 30;
        else if (errorRate < 0.1) score += 20;
        else if (errorRate < 0.15) score += 10;
        
        // 处理时间评分 (0-35分)
        double avgTime = snapshot.getAvgProcessingTime();
        if (avgTime < 1000) score += 35;
        else if (avgTime < 3000) score += 25;
        else if (avgTime < 5000) score += 15;
        
        // 吞吐量评分 (0-35分)
        double throughput = snapshot.getThroughput();
        if (throughput > 100) score += 35;
        else if (throughput > 50) score += 25;
        else if (throughput > 20) score += 15;
        
        if (score >= 80) return "A";
        else if (score >= 60) return "B";
        else if (score >= 40) return "C";
        else return "D";
    }

    private List<String> identifyCriticalIssues(MetricsCollector.AlertMetricsSnapshot snapshot) {
        List<String> issues = new ArrayList<>();
        
        if (snapshot.getErrorRate() > 0.2) {
            issues.add("错误率过高 (>" + (snapshot.getErrorRate() * 100) + "%)");
        }
        
        if (snapshot.getAvgProcessingTime() > 5000) {
            issues.add("处理时间过长 (>" + snapshot.getAvgProcessingTime() + "ms)");
        }
        
        if (snapshot.getThroughput() < 10) {
            issues.add("吞吐量过低 (<" + snapshot.getThroughput() + " msg/min)");
        }
        
        return issues;
    }

    private String assessSystemStability(MetricsCollector.AlertMetricsSnapshot snapshot) {
        double errorRate = snapshot.getErrorRate();
        double avgTime = snapshot.getAvgProcessingTime();
        
        if (errorRate < 0.05 && avgTime < 3000) {
            return "stable";
        } else if (errorRate < 0.15 && avgTime < 5000) {
            return "moderate";
        } else {
            return "unstable";
        }
    }

    private void identifyProcessingTimeBottlenecks(Map<String, Object> metrics, List<SystemBottleneck> bottlenecks) {
        Object avgTimeObj = metrics.get("avgProcessingTime");
        if (avgTimeObj instanceof Number) {
            double avgTime = ((Number) avgTimeObj).doubleValue();
            if (avgTime > 3000) {
                bottlenecks.add(SystemBottleneck.builder()
                        .type("processing_time")
                        .component("alert_processing")
                        .responseTime((long) avgTime)
                        .severity(avgTime > 5000 ? "critical" : "warning")
                        .description("告警处理时间过长")
                        .build());
            }
        }
    }

    private void identifyQueueBottlenecks(Map<String, Object> metrics, List<SystemBottleneck> bottlenecks) {
        @SuppressWarnings("unchecked")
        Map<String, Object> queueStats = (Map<String, Object>) metrics.get("queueLength");
        
        if (queueStats != null) {
            Object totalLengthObj = queueStats.get("totalLength");
            if (totalLengthObj instanceof Number) {
                long totalLength = ((Number) totalLengthObj).longValue();
                if (totalLength > 500) {
                    bottlenecks.add(SystemBottleneck.builder()
                            .type("queue_length")
                            .component("message_queue")
                            .responseTime(0L)
                            .severity(totalLength > 1000 ? "critical" : "warning")
                            .description("消息队列积压过多")
                            .build());
                }
            }
        }
    }

    private void identifyResourceBottlenecks(Map<String, Object> metrics, List<SystemBottleneck> bottlenecks) {
        @SuppressWarnings("unchecked")
        Map<String, Object> resourceUsage = (Map<String, Object>) metrics.get("resourceUsage");
        
        if (resourceUsage != null) {
            Object memoryUsageObj = resourceUsage.get("memoryUsage");
            if (memoryUsageObj instanceof Number) {
                double memoryUsage = ((Number) memoryUsageObj).doubleValue();
                if (memoryUsage > 0.8) {
                    bottlenecks.add(SystemBottleneck.builder()
                            .type("memory_usage")
                            .component("jvm_heap")
                            .responseTime(0L)
                            .severity(memoryUsage > 0.9 ? "critical" : "warning")
                            .description("内存使用率过高")
                            .build());
                }
            }
        }
    }

    private void identifyErrorRateBottlenecks(Map<String, Object> metrics, List<SystemBottleneck> bottlenecks) {
        Object errorRateObj = metrics.get("errorRate");
        if (errorRateObj instanceof Number) {
            double errorRate = ((Number) errorRateObj).doubleValue();
            if (errorRate > 0.1) {
                bottlenecks.add(SystemBottleneck.builder()
                        .type("error_rate")
                        .component("alert_processing")
                        .responseTime(0L)
                        .severity(errorRate > 0.2 ? "critical" : "warning")
                        .description("系统错误率过高")
                        .build());
            }
        }
    }

    private double calculateExpectedPerformanceImprovement(List<OptimizationRecommendation> recommendations) {
        // 根据建议类型和优先级估算性能改进
        double improvement = 0.0;
        
        for (OptimizationRecommendation rec : recommendations) {
            switch (rec.getCategory()) {
                case "rule_optimization":
                    improvement += rec.getPriority() == Priority.HIGH ? 0.3 : 0.15;
                    break;
                case "performance_optimization":
                    improvement += rec.getPriority() == Priority.HIGH ? 0.4 : 0.2;
                    break;
                case "capacity_planning":
                    improvement += 0.5;
                    break;
                default:
                    improvement += 0.1;
            }
        }
        
        return Math.min(0.8, improvement); // 最大80%改进
    }

    private String estimateROI(List<OptimizationRecommendation> recommendations) {
        int totalDays = recommendations.stream()
                .mapToInt(OptimizationRecommendation::getEstimatedTimeDays)
                .sum();
        
        long highPriorityCount = recommendations.stream()
                .filter(r -> r.getPriority() == Priority.HIGH)
                .count();
        
        if (totalDays <= 7 && highPriorityCount > 0) {
            return "high";
        } else if (totalDays <= 14) {
            return "medium";
        } else {
            return "low";
        }
    }

    private OptimizationPlan createFallbackPlan(Exception e) {
        return OptimizationPlan.builder()
                .analysisPeriod(7)
                .generatedAt(LocalDateTime.now())
                .historicalSummary(Map.of("error", e.getMessage()))
                .futurePredictions(new HashMap<>())
                .identifiedBottlenecks(new ArrayList<>())
                .optimizationPlan(Arrays.asList(
                        OptimizationRecommendation.builder()
                                .category("system_health")
                                .priority(Priority.HIGH)
                                .title("检查系统状态")
                                .description("优化分析系统异常，建议检查系统状态")
                                .implementationSteps(Arrays.asList("检查系统日志", "验证监控数据"))
                                .expectedImprovement("恢复优化分析功能")
                                .implementationEffort(ImplementationEffort.LOW)
                                .estimatedTimeDays(1)
                                .build()
                ))
                .estimatedImprovements(new HashMap<>())
                .planValidityDays(1)
                .build();
    }

    // 枚举类型定义
    public enum Priority {
        VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW
    }

    public enum ImplementationEffort {
        VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    }

    // 数据类定义
    public static class OptimizationPlan {
        private int analysisPeriod;
        private LocalDateTime generatedAt;
        private Map<String, Object> historicalSummary;
        private Map<String, Object> futurePredictions;
        private List<SystemBottleneck> identifiedBottlenecks;
        private List<OptimizationRecommendation> optimizationPlan;
        private Map<String, Object> estimatedImprovements;
        private int planValidityDays;

        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private final OptimizationPlan plan = new OptimizationPlan();

            public Builder analysisPeriod(int analysisPeriod) {
                plan.analysisPeriod = analysisPeriod;
                return this;
            }

            public Builder generatedAt(LocalDateTime generatedAt) {
                plan.generatedAt = generatedAt;
                return this;
            }

            public Builder historicalSummary(Map<String, Object> historicalSummary) {
                plan.historicalSummary = historicalSummary;
                return this;
            }

            public Builder futurePredictions(Map<String, Object> futurePredictions) {
                plan.futurePredictions = futurePredictions;
                return this;
            }

            public Builder identifiedBottlenecks(List<SystemBottleneck> identifiedBottlenecks) {
                plan.identifiedBottlenecks = identifiedBottlenecks;
                return this;
            }

            public Builder optimizationPlan(List<OptimizationRecommendation> optimizationPlan) {
                plan.optimizationPlan = optimizationPlan;
                return this;
            }

            public Builder estimatedImprovements(Map<String, Object> estimatedImprovements) {
                plan.estimatedImprovements = estimatedImprovements;
                return this;
            }

            public Builder planValidityDays(int planValidityDays) {
                plan.planValidityDays = planValidityDays;
                return this;
            }

            public OptimizationPlan build() {
                return plan;
            }
        }

        // Getters
        public int getAnalysisPeriod() { return analysisPeriod; }
        public LocalDateTime getGeneratedAt() { return generatedAt; }
        public Map<String, Object> getHistoricalSummary() { return historicalSummary; }
        public Map<String, Object> getFuturePredictions() { return futurePredictions; }
        public List<SystemBottleneck> getIdentifiedBottlenecks() { return identifiedBottlenecks; }
        public List<OptimizationRecommendation> getOptimizationPlan() { return optimizationPlan; }
        public Map<String, Object> getEstimatedImprovements() { return estimatedImprovements; }
        public int getPlanValidityDays() { return planValidityDays; }
    }

    public static class OptimizationRecommendation {
        private String category;
        private Priority priority;
        private String title;
        private String description;
        private List<String> implementationSteps;
        private String expectedImprovement;
        private ImplementationEffort implementationEffort;
        private int estimatedTimeDays;

        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private final OptimizationRecommendation recommendation = new OptimizationRecommendation();

            public Builder category(String category) {
                recommendation.category = category;
                return this;
            }

            public Builder priority(Priority priority) {
                recommendation.priority = priority;
                return this;
            }

            public Builder title(String title) {
                recommendation.title = title;
                return this;
            }

            public Builder description(String description) {
                recommendation.description = description;
                return this;
            }

            public Builder implementationSteps(List<String> implementationSteps) {
                recommendation.implementationSteps = implementationSteps;
                return this;
            }

            public Builder expectedImprovement(String expectedImprovement) {
                recommendation.expectedImprovement = expectedImprovement;
                return this;
            }

            public Builder implementationEffort(ImplementationEffort implementationEffort) {
                recommendation.implementationEffort = implementationEffort;
                return this;
            }

            public Builder estimatedTimeDays(int estimatedTimeDays) {
                recommendation.estimatedTimeDays = estimatedTimeDays;
                return this;
            }

            public OptimizationRecommendation build() {
                return recommendation;
            }
        }

        // Getters
        public String getCategory() { return category; }
        public Priority getPriority() { return priority; }
        public String getTitle() { return title; }
        public String getDescription() { return description; }
        public List<String> getImplementationSteps() { return implementationSteps; }
        public String getExpectedImprovement() { return expectedImprovement; }
        public ImplementationEffort getImplementationEffort() { return implementationEffort; }
        public int getEstimatedTimeDays() { return estimatedTimeDays; }
    }

    public static class SystemBottleneck {
        private String type;
        private String component;
        private Long responseTime;
        private String severity;
        private String description;

        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private final SystemBottleneck bottleneck = new SystemBottleneck();

            public Builder type(String type) {
                bottleneck.type = type;
                return this;
            }

            public Builder component(String component) {
                bottleneck.component = component;
                return this;
            }

            public Builder responseTime(Long responseTime) {
                bottleneck.responseTime = responseTime;
                return this;
            }

            public Builder severity(String severity) {
                bottleneck.severity = severity;
                return this;
            }

            public Builder description(String description) {
                bottleneck.description = description;
                return this;
            }

            public SystemBottleneck build() {
                return bottleneck;
            }
        }

        // Getters
        public String getType() { return type; }
        public String getComponent() { return component; }
        public Long getResponseTime() { return responseTime; }
        public String getSeverity() { return severity; }
        public String getDescription() { return description; }
    }
}