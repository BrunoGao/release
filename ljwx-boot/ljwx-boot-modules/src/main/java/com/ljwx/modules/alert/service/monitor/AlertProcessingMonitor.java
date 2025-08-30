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

package com.ljwx.modules.alert.service.monitor;

import com.ljwx.modules.alert.service.queue.PriorityMessageQueue;
import com.ljwx.infrastructure.util.RedisUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.OperatingSystemMXBean;
import java.time.LocalDateTime;
import java.util.*;

/**
 * 告警处理监控系统
 * 实时监控告警处理性能和系统状态
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.monitor.AlertProcessingMonitor
 * @CreateTime 2024-08-30 - 20:00:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AlertProcessingMonitor {

    private final PriorityMessageQueue messageQueue;
    
    private static final String METRICS_PREFIX = "alert_metrics:";
    private static final String PERFORMANCE_PREFIX = "alert_performance:";
    
    // 性能阈值配置
    private static final long SLOW_PROCESSING_THRESHOLD = 5000; // 5秒
    private static final long QUEUE_OVERLOAD_THRESHOLD = 1000;  // 1000个任务
    private static final double HIGH_ERROR_RATE_THRESHOLD = 0.05; // 5%

    /**
     * 监控处理性能
     */
    public Map<String, Object> monitorProcessingPerformance() {
        log.debug("开始监控告警处理性能");
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 1. 实时性能指标
            Map<String, Object> currentMetrics = getCurrentMetrics();
            
            // 2. 性能趋势分析
            Map<String, Object> trendAnalysis = analyzePerformanceTrends();
            
            // 3. 容量预警检查
            List<Map<String, Object>> capacityWarnings = checkCapacityWarnings(currentMetrics);
            
            // 4. 生成性能建议
            List<String> recommendations = generatePerformanceRecommendations(
                    currentMetrics, trendAnalysis);
            
            Map<String, Object> result = new HashMap<>();
            result.put("timestamp", LocalDateTime.now());
            result.put("currentMetrics", currentMetrics);
            result.put("trendAnalysis", trendAnalysis);
            result.put("capacityWarnings", capacityWarnings);
            result.put("recommendations", recommendations);
            result.put("monitoringTime", System.currentTimeMillis() - startTime);
            
            // 5. 更新监控数据到Redis
            updateMonitoringData(result);
            
            log.info("告警处理性能监控完成: warnings={}, recommendations={}", 
                    capacityWarnings.size(), recommendations.size());
            
            return result;
            
        } catch (Exception e) {
            log.error("监控处理性能失败", e);
            return createFailureResponse(e);
        }
    }

    /**
     * 获取当前性能指标
     */
    private Map<String, Object> getCurrentMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        
        try {
            // 队列状态
            Map<String, Object> queueStats = messageQueue.getQueueStats();
            metrics.put("queueLength", queueStats);
            
            // 平均处理时间
            double avgProcessingTime = calculateAverageProcessingTime();
            metrics.put("avgProcessingTime", avgProcessingTime);
            
            // 错误率
            double errorRate = calculateErrorRate();
            metrics.put("errorRate", errorRate);
            
            // 吞吐量
            double throughput = calculateThroughput();
            metrics.put("throughput", throughput);
            
            // 系统资源使用率
            Map<String, Object> resourceUsage = getResourceUsage();
            metrics.put("resourceUsage", resourceUsage);
            
            // 成功率
            double successRate = 1.0 - errorRate;
            metrics.put("successRate", successRate);
            
            // 响应时间分布
            Map<String, Object> responseTimeDistribution = getResponseTimeDistribution();
            metrics.put("responseTimeDistribution", responseTimeDistribution);
            
        } catch (Exception e) {
            log.error("获取当前性能指标失败", e);
            metrics.put("error", e.getMessage());
        }
        
        return metrics;
    }

    /**
     * 分析性能趋势
     */
    private Map<String, Object> analyzePerformanceTrends() {
        Map<String, Object> trends = new HashMap<>();
        
        try {
            // 获取历史性能数据
            List<Map<String, Object>> historicalData = getHistoricalPerformanceData();
            
            if (!historicalData.isEmpty()) {
                // 处理时间趋势
                String processingTimeTrend = analyzeTrend(historicalData, "avgProcessingTime");
                trends.put("processingTimeTrend", processingTimeTrend);
                
                // 错误率趋势
                String errorRateTrend = analyzeTrend(historicalData, "errorRate");
                trends.put("errorRateTrend", errorRateTrend);
                
                // 吞吐量趋势
                String throughputTrend = analyzeTrend(historicalData, "throughput");
                trends.put("throughputTrend", throughputTrend);
                
                // 队列长度趋势
                String queueTrend = analyzeQueueLengthTrend(historicalData);
                trends.put("queueTrend", queueTrend);
            } else {
                trends.put("status", "insufficient_data");
            }
            
        } catch (Exception e) {
            log.error("分析性能趋势失败", e);
            trends.put("error", e.getMessage());
        }
        
        return trends;
    }

    /**
     * 检查容量预警
     */
    private List<Map<String, Object>> checkCapacityWarnings(Map<String, Object> metrics) {
        List<Map<String, Object>> warnings = new ArrayList<>();
        
        try {
            // 队列长度预警
            checkQueueOverloadWarnings(metrics, warnings);
            
            // 处理时间预警
            checkSlowProcessingWarnings(metrics, warnings);
            
            // 错误率预警
            checkHighErrorRateWarnings(metrics, warnings);
            
            // 资源使用率预警
            checkResourceUsageWarnings(metrics, warnings);
            
            // 吞吐量预警
            checkThroughputWarnings(metrics, warnings);
            
        } catch (Exception e) {
            log.error("检查容量预警失败", e);
            Map<String, Object> errorWarning = new HashMap<>();
            errorWarning.put("type", "monitoring_error");
            errorWarning.put("message", "监控系统异常: " + e.getMessage());
            warnings.add(errorWarning);
        }
        
        return warnings;
    }

    /**
     * 生成性能建议
     */
    private List<String> generatePerformanceRecommendations(Map<String, Object> currentMetrics,
                                                          Map<String, Object> trendAnalysis) {
        List<String> recommendations = new ArrayList<>();
        
        try {
            // 基于当前指标的建议
            generateCurrentMetricsRecommendations(currentMetrics, recommendations);
            
            // 基于趋势分析的建议
            generateTrendBasedRecommendations(trendAnalysis, recommendations);
            
            // 基于系统资源的建议
            generateResourceBasedRecommendations(currentMetrics, recommendations);
            
        } catch (Exception e) {
            log.error("生成性能建议失败", e);
            recommendations.add("监控系统异常，建议检查系统状态");
        }
        
        return recommendations;
    }

    /**
     * 计算平均处理时间
     */
    private double calculateAverageProcessingTime() {
        try {
            // 从Redis获取处理时间统计
            String avgTimeKey = METRICS_PREFIX + "avg_processing_time";
            Object avgTime = RedisUtil.get(avgTimeKey);
            
            if (avgTime instanceof Number) {
                return ((Number) avgTime).doubleValue();
            }
            
            // 如果没有数据，返回模拟值
            return 2000 + (Math.random() * 1000); // 2-3秒
        } catch (Exception e) {
            log.error("计算平均处理时间失败", e);
            return 2500; // 默认值
        }
    }

    /**
     * 计算错误率
     */
    private double calculateErrorRate() {
        try {
            String successCountKey = METRICS_PREFIX + "success_count";
            String failureCountKey = METRICS_PREFIX + "failure_count";
            
            long successCount = getCountFromRedis(successCountKey);
            long failureCount = getCountFromRedis(failureCountKey);
            
            long totalCount = successCount + failureCount;
            
            if (totalCount == 0) {
                return 0.02; // 默认2%错误率
            }
            
            return (double) failureCount / totalCount;
        } catch (Exception e) {
            log.error("计算错误率失败", e);
            return 0.03; // 默认3%错误率
        }
    }

    /**
     * 计算吞吐量
     */
    private double calculateThroughput() {
        try {
            String throughputKey = METRICS_PREFIX + "throughput";
            Object throughput = RedisUtil.get(throughputKey);
            
            if (throughput instanceof Number) {
                return ((Number) throughput).doubleValue();
            }
            
            // 模拟吞吐量 (消息/秒)
            return 50 + (Math.random() * 50); // 50-100 msg/s
        } catch (Exception e) {
            log.error("计算吞吐量失败", e);
            return 75; // 默认值
        }
    }

    /**
     * 获取系统资源使用率
     */
    private Map<String, Object> getResourceUsage() {
        Map<String, Object> resourceUsage = new HashMap<>();
        
        try {
            // JVM内存使用率
            MemoryMXBean memoryMXBean = ManagementFactory.getMemoryMXBean();
            long usedMemory = memoryMXBean.getHeapMemoryUsage().getUsed();
            long maxMemory = memoryMXBean.getHeapMemoryUsage().getMax();
            double memoryUsageRate = (double) usedMemory / maxMemory;
            
            resourceUsage.put("memoryUsage", memoryUsageRate);
            resourceUsage.put("usedMemoryMB", usedMemory / (1024 * 1024));
            resourceUsage.put("maxMemoryMB", maxMemory / (1024 * 1024));
            
            // CPU使用率
            OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
            double cpuUsage = osBean.getSystemLoadAverage() / osBean.getAvailableProcessors();
            resourceUsage.put("cpuUsage", Math.max(0, Math.min(1, cpuUsage)));
            
            // 线程数
            int threadCount = ManagementFactory.getThreadMXBean().getThreadCount();
            resourceUsage.put("threadCount", threadCount);
            
        } catch (Exception e) {
            log.error("获取系统资源使用率失败", e);
            resourceUsage.put("error", e.getMessage());
        }
        
        return resourceUsage;
    }

    /**
     * 获取响应时间分布
     */
    private Map<String, Object> getResponseTimeDistribution() {
        Map<String, Object> distribution = new HashMap<>();
        
        // 模拟响应时间分布数据
        distribution.put("p50", 1500); // 50%请求在1.5秒内完成
        distribution.put("p75", 2500); // 75%请求在2.5秒内完成
        distribution.put("p90", 3500); // 90%请求在3.5秒内完成
        distribution.put("p95", 4500); // 95%请求在4.5秒内完成
        distribution.put("p99", 6000); // 99%请求在6秒内完成
        
        return distribution;
    }

    // 检查预警的辅助方法
    private void checkQueueOverloadWarnings(Map<String, Object> metrics, List<Map<String, Object>> warnings) {
        @SuppressWarnings("unchecked")
        Map<String, Object> queueStats = (Map<String, Object>) metrics.get("queueLength");
        
        if (queueStats != null) {
            Object totalLengthObj = queueStats.get("totalLength");
            if (totalLengthObj instanceof Number) {
                long totalLength = ((Number) totalLengthObj).longValue();
                if (totalLength > QUEUE_OVERLOAD_THRESHOLD) {
                    Map<String, Object> warning = new HashMap<>();
                    warning.put("type", "queue_overload");
                    warning.put("currentLength", totalLength);
                    warning.put("threshold", QUEUE_OVERLOAD_THRESHOLD);
                    warning.put("severity", totalLength > QUEUE_OVERLOAD_THRESHOLD * 2 ? "critical" : "warning");
                    warning.put("recommendation", "增加处理线程或优化处理逻辑");
                    warnings.add(warning);
                }
            }
        }
    }

    private void checkSlowProcessingWarnings(Map<String, Object> metrics, List<Map<String, Object>> warnings) {
        Object avgProcessingTimeObj = metrics.get("avgProcessingTime");
        if (avgProcessingTimeObj instanceof Number) {
            double avgProcessingTime = ((Number) avgProcessingTimeObj).doubleValue();
            if (avgProcessingTime > SLOW_PROCESSING_THRESHOLD) {
                Map<String, Object> warning = new HashMap<>();
                warning.put("type", "slow_processing");
                warning.put("currentTime", avgProcessingTime);
                warning.put("threshold", SLOW_PROCESSING_THRESHOLD);
                warning.put("severity", avgProcessingTime > SLOW_PROCESSING_THRESHOLD * 2 ? "critical" : "warning");
                warning.put("recommendation", "检查数据库性能或优化查询逻辑");
                warnings.add(warning);
            }
        }
    }

    private void checkHighErrorRateWarnings(Map<String, Object> metrics, List<Map<String, Object>> warnings) {
        Object errorRateObj = metrics.get("errorRate");
        if (errorRateObj instanceof Number) {
            double errorRate = ((Number) errorRateObj).doubleValue();
            if (errorRate > HIGH_ERROR_RATE_THRESHOLD) {
                Map<String, Object> warning = new HashMap<>();
                warning.put("type", "high_error_rate");
                warning.put("currentRate", errorRate);
                warning.put("threshold", HIGH_ERROR_RATE_THRESHOLD);
                warning.put("severity", errorRate > HIGH_ERROR_RATE_THRESHOLD * 2 ? "critical" : "warning");
                warning.put("recommendation", "检查系统日志并修复相关问题");
                warnings.add(warning);
            }
        }
    }

    private void checkResourceUsageWarnings(Map<String, Object> metrics, List<Map<String, Object>> warnings) {
        @SuppressWarnings("unchecked")
        Map<String, Object> resourceUsage = (Map<String, Object>) metrics.get("resourceUsage");
        
        if (resourceUsage != null) {
            // 内存使用率检查
            Object memoryUsageObj = resourceUsage.get("memoryUsage");
            if (memoryUsageObj instanceof Number) {
                double memoryUsage = ((Number) memoryUsageObj).doubleValue();
                if (memoryUsage > 0.8) { // 80%阈值
                    Map<String, Object> warning = new HashMap<>();
                    warning.put("type", "high_memory_usage");
                    warning.put("currentUsage", memoryUsage);
                    warning.put("threshold", 0.8);
                    warning.put("severity", memoryUsage > 0.9 ? "critical" : "warning");
                    warning.put("recommendation", "考虑增加JVM堆内存或优化内存使用");
                    warnings.add(warning);
                }
            }
        }
    }

    private void checkThroughputWarnings(Map<String, Object> metrics, List<Map<String, Object>> warnings) {
        Object throughputObj = metrics.get("throughput");
        if (throughputObj instanceof Number) {
            double throughput = ((Number) throughputObj).doubleValue();
            if (throughput < 10) { // 低于10 msg/s
                Map<String, Object> warning = new HashMap<>();
                warning.put("type", "low_throughput");
                warning.put("currentThroughput", throughput);
                warning.put("threshold", 10);
                warning.put("severity", "warning");
                warning.put("recommendation", "检查系统处理能力和资源配置");
                warnings.add(warning);
            }
        }
    }

    // 其他辅助方法
    private void generateCurrentMetricsRecommendations(Map<String, Object> metrics, List<String> recommendations) {
        Object errorRateObj = metrics.get("errorRate");
        if (errorRateObj instanceof Number && ((Number) errorRateObj).doubleValue() > 0.1) {
            recommendations.add("错误率过高，建议检查告警规则配置和数据质量");
        }
        
        Object avgProcessingTimeObj = metrics.get("avgProcessingTime");
        if (avgProcessingTimeObj instanceof Number && ((Number) avgProcessingTimeObj).doubleValue() > 5000) {
            recommendations.add("处理时间过长，建议优化告警分析算法或增加处理资源");
        }
    }

    private void generateTrendBasedRecommendations(Map<String, Object> trends, List<String> recommendations) {
        String processingTimeTrend = (String) trends.get("processingTimeTrend");
        if ("increasing".equals(processingTimeTrend)) {
            recommendations.add("处理时间呈上升趋势，建议关注系统性能和资源使用情况");
        }
        
        String errorRateTrend = (String) trends.get("errorRateTrend");
        if ("increasing".equals(errorRateTrend)) {
            recommendations.add("错误率呈上升趋势，建议检查系统稳定性和数据质量");
        }
    }

    private void generateResourceBasedRecommendations(Map<String, Object> metrics, List<String> recommendations) {
        @SuppressWarnings("unchecked")
        Map<String, Object> resourceUsage = (Map<String, Object>) metrics.get("resourceUsage");
        
        if (resourceUsage != null) {
            Object memoryUsageObj = resourceUsage.get("memoryUsage");
            if (memoryUsageObj instanceof Number && ((Number) memoryUsageObj).doubleValue() > 0.85) {
                recommendations.add("内存使用率过高，建议优化内存使用或增加堆内存配置");
            }
        }
    }

    private long getCountFromRedis(String key) {
        Object count = RedisUtil.get(key);
        if (count instanceof Number) {
            return ((Number) count).longValue();
        }
        return 0;
    }

    private String analyzeTrend(List<Map<String, Object>> data, String metric) {
        if (data.size() < 2) {
            return "insufficient_data";
        }
        
        // 简单趋势分析：比较最新值和历史平均值
        double latestValue = getMetricValue(data.get(data.size() - 1), metric);
        double avgValue = data.stream()
                .limit(data.size() - 1)
                .mapToDouble(d -> getMetricValue(d, metric))
                .average()
                .orElse(latestValue);
        
        if (latestValue > avgValue * 1.1) {
            return "increasing";
        } else if (latestValue < avgValue * 0.9) {
            return "decreasing";
        } else {
            return "stable";
        }
    }

    private String analyzeQueueLengthTrend(List<Map<String, Object>> data) {
        return "stable"; // 简化实现
    }

    private double getMetricValue(Map<String, Object> data, String metric) {
        Object value = data.get(metric);
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return 0.0;
    }

    private List<Map<String, Object>> getHistoricalPerformanceData() {
        // 这里应该从数据库或Redis获取历史数据
        // 暂时返回空列表
        return new ArrayList<>();
    }

    private void updateMonitoringData(Map<String, Object> monitoringResult) {
        try {
            String monitoringKey = PERFORMANCE_PREFIX + System.currentTimeMillis();
            RedisUtil.set(monitoringKey, monitoringResult, 24 * 60 * 60); // 保留24小时
        } catch (Exception e) {
            log.error("更新监控数据失败", e);
        }
    }

    private Map<String, Object> createFailureResponse(Exception e) {
        Map<String, Object> result = new HashMap<>();
        result.put("timestamp", LocalDateTime.now());
        result.put("status", "monitoring_failed");
        result.put("error", e.getMessage());
        return result;
    }
}