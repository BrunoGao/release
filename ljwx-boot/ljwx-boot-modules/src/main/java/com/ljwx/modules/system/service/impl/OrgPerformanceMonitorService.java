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

package com.ljwx.modules.system.service.impl;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 组织架构性能监控服务
 * 
 * 功能特性:
 * - 实时性能指标收集
 * - 自动化性能告警
 * - 性能趋势分析  
 * - 缓存命中率监控
 * - 查询频次统计
 * - 慢查询检测
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.OrgPerformanceMonitorService
 * @CreateTime 2025-08-30 - 18:00:00
 */
@Slf4j
@Service
public class OrgPerformanceMonitorService {

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    // 性能指标缓存
    private final Map<String, AtomicLong> performanceCounters = new ConcurrentHashMap<>();
    private final Map<String, List<Long>> recentExecutionTimes = new ConcurrentHashMap<>();
    private final Map<String, AtomicLong> cacheCounters = new ConcurrentHashMap<>();

    // 配置参数
    private static final int SLOW_QUERY_THRESHOLD_MS = 100;
    private static final int PERFORMANCE_ALERT_THRESHOLD_MS = 200;
    private static final int RECENT_TIMES_MAX_SIZE = 100;
    private static final int CACHE_HIT_RATE_ALERT_THRESHOLD = 80;

    /**
     * 记录查询操作的性能指标
     */
    @Async
    public void recordQueryMetrics(String operationType, Long customerId, Long orgId, 
                                  long executionTimeMs, int resultCount, boolean success, String errorMessage) {
        try {
            // 1. 更新性能计数器
            String counterKey = String.format("%s:%s", operationType, customerId);
            performanceCounters.computeIfAbsent(counterKey, k -> new AtomicLong(0)).incrementAndGet();

            // 2. 记录最近的执行时间
            recentExecutionTimes.computeIfAbsent(counterKey, k -> Collections.synchronizedList(new ArrayList<>()))
                .add(executionTimeMs);
            
            // 保持列表大小
            List<Long> times = recentExecutionTimes.get(counterKey);
            if (times.size() > RECENT_TIMES_MAX_SIZE) {
                times.remove(0);
            }

            // 3. 慢查询检测
            if (executionTimeMs > SLOW_QUERY_THRESHOLD_MS) {
                recordSlowQuery(operationType, customerId, orgId, executionTimeMs, resultCount);
            }

            // 4. 性能告警检测
            if (executionTimeMs > PERFORMANCE_ALERT_THRESHOLD_MS) {
                triggerPerformanceAlert(operationType, customerId, executionTimeMs, errorMessage);
            }

        } catch (Exception e) {
            // 监控系统本身的错误不应影响业务逻辑
            log.debug("记录性能指标失败: operation={}, customerId={}", operationType, customerId, e);
        }
    }

    /**
     * 记录缓存操作指标
     */
    public void recordCacheMetrics(String cacheOperation, String cacheKey, Long customerId) {
        try {
            String counterKey = String.format("cache_%s:%s", cacheOperation.toLowerCase(), customerId);
            cacheCounters.computeIfAbsent(counterKey, k -> new AtomicLong(0)).incrementAndGet();

            // 记录缓存详情
            if (log.isDebugEnabled()) {
                log.debug("缓存操作: operation={}, key={}, customerId={}", cacheOperation, cacheKey, customerId);
            }

        } catch (Exception e) {
            log.debug("记录缓存指标失败: operation={}, key={}", cacheOperation, cacheKey, e);
        }
    }

    /**
     * 生成性能分析报告
     */
    public Map<String, Object> generatePerformanceReport(Long customerId, int hours) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        Map<String, Object> report = new HashMap<>();

        try {
            // 1. 基础性能统计
            Map<String, Object> basicStats = getBasicPerformanceStats(customerId);
            report.put("basicStatistics", basicStats);

            // 2. 缓存性能分析
            Map<String, Object> cacheAnalysis = getCachePerformanceAnalysis(customerId);
            report.put("cacheAnalysis", cacheAnalysis);

            // 3. 性能建议
            List<String> recommendations = generatePerformanceRecommendations(report);
            report.put("recommendations", recommendations);

            stopWatch.stop();
            report.put("reportGenerationTime", stopWatch.getTotalTimeMillis());
            report.put("reportTimestamp", LocalDateTime.now());
            report.put("statisticsPeriod", hours + " hours");

            log.info("📊 性能分析报告生成完成: customerId={}, 范围={}小时, 耗时={}ms", 
                customerId, hours, stopWatch.getTotalTimeMillis());

            return report;

        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 生成性能报告失败: customerId={}, hours={}", customerId, hours, e);

            report.put("error", e.getMessage());
            report.put("reportTimestamp", LocalDateTime.now());
            return report;
        }
    }

    /**
     * 获取实时性能指标
     */
    public Map<String, Object> getRealTimeMetrics(Long customerId) {
        Map<String, Object> metrics = new HashMap<>();

        try {
            String customerFilter = customerId != null ? ":" + customerId : "";

            // 1. 当前查询频次
            Map<String, Long> queryFrequency = performanceCounters.entrySet().stream()
                .filter(entry -> customerId == null || entry.getKey().endsWith(customerFilter))
                .collect(Collectors.toMap(
                    entry -> entry.getKey().split(":")[0], 
                    entry -> entry.getValue().get(),
                    Long::sum
                ));
            metrics.put("queryFrequency", queryFrequency);

            // 2. 平均响应时间
            Map<String, Double> avgResponseTimes = new HashMap<>();
            for (Map.Entry<String, List<Long>> entry : recentExecutionTimes.entrySet()) {
                if (customerId == null || entry.getKey().endsWith(customerFilter)) {
                    List<Long> times = entry.getValue();
                    double avgTime = times.stream().mapToLong(Long::longValue).average().orElse(0.0);
                    avgResponseTimes.put(entry.getKey().split(":")[0], avgTime);
                }
            }
            metrics.put("averageResponseTimes", avgResponseTimes);

            // 3. 缓存命中率
            long cacheHits = cacheCounters.getOrDefault("cache_hit" + customerFilter, new AtomicLong(0)).get();
            long cacheMisses = cacheCounters.getOrDefault("cache_miss" + customerFilter, new AtomicLong(0)).get();
            double hitRate = (cacheHits + cacheMisses) > 0 ? 
                (double) cacheHits / (cacheHits + cacheMisses) * 100 : 0.0;
            metrics.put("cacheHitRate", String.format("%.1f%%", hitRate));

            // 4. 系统健康状态
            String healthStatus = determineSystemHealthStatus(avgResponseTimes, hitRate);
            metrics.put("healthStatus", healthStatus);

            metrics.put("timestamp", LocalDateTime.now());

            return metrics;

        } catch (Exception e) {
            log.error("❌ 获取实时指标失败: customerId={}", customerId, e);
            
            metrics.put("error", e.getMessage());
            metrics.put("timestamp", LocalDateTime.now());
            return metrics;
        }
    }

    /**
     * 每5分钟执行一次性能检查
     */
    @Scheduled(fixedRate = 300000) // 5分钟
    public void performanceHealthCheck() {
        try {
            log.debug("🔍 执行性能健康检查...");

            // 1. 检查平均响应时间
            checkAverageResponseTimes();

            // 2. 检查缓存命中率
            checkCacheHitRates();

            // 3. 清理过期的性能数据
            cleanExpiredPerformanceData();

            log.debug("✅ 性能健康检查完成");

        } catch (Exception e) {
            log.error("❌ 性能健康检查失败", e);
        }
    }

    /**
     * 每小时生成性能摘要报告
     */
    @Scheduled(fixedRate = 3600000) // 1小时
    public void generateHourlyPerformanceSummary() {
        try {
            log.info("📈 生成每小时性能摘要...");

            Map<String, Object> summary = generatePerformanceReport(null, 1);
            
            // 记录关键指标到日志
            Map<String, Object> basicStats = (Map<String, Object>) summary.get("basicStatistics");
            if (basicStats != null) {
                log.info("🎯 每小时性能摘要: 总操作={}, 平均耗时={}ms", 
                    basicStats.get("totalOperations"), 
                    basicStats.get("averageExecutionTime"));
            }

            // 如果性能有问题，发送告警
            List<String> recommendations = (List<String>) summary.get("recommendations");
            if (recommendations != null && !recommendations.isEmpty()) {
                log.warn("⚠️ 性能优化建议: {}", String.join("; ", recommendations));
            }

        } catch (Exception e) {
            log.error("❌ 生成每小时性能摘要失败", e);
        }
    }

    // ================== 私有辅助方法 ==================

    private void recordSlowQuery(String operationType, Long customerId, Long orgId, 
                                long executionTimeMs, int resultCount) {
        log.warn("🐌 慢查询检测: operation={}, customerId={}, orgId={}, time={}ms, count={}", 
            operationType, customerId, orgId, executionTimeMs, resultCount);
    }

    private void triggerPerformanceAlert(String operationType, Long customerId, 
                                       long executionTimeMs, String errorMessage) {
        log.error("🚨 性能告警: operation={}, customerId={}, time={}ms, error={}", 
            operationType, customerId, executionTimeMs, errorMessage);
    }

    private Map<String, Object> getBasicPerformanceStats(Long customerId) {
        Map<String, Object> stats = new HashMap<>();
        
        String customerFilter = customerId != null ? ":" + customerId : "";
        
        // 总操作次数
        long totalOperations = performanceCounters.entrySet().stream()
            .filter(entry -> customerId == null || entry.getKey().endsWith(customerFilter))
            .mapToLong(entry -> entry.getValue().get())
            .sum();
        stats.put("totalOperations", totalOperations);
        
        // 平均执行时间
        double avgTime = recentExecutionTimes.entrySet().stream()
            .filter(entry -> customerId == null || entry.getKey().endsWith(customerFilter))
            .flatMap(entry -> entry.getValue().stream())
            .mapToLong(Long::longValue)
            .average()
            .orElse(0.0);
        stats.put("averageExecutionTime", Math.round(avgTime * 10.0) / 10.0);
        
        return stats;
    }

    private Map<String, Object> getCachePerformanceAnalysis(Long customerId) {
        Map<String, Object> analysis = new HashMap<>();

        String customerFilter = customerId != null ? ":" + customerId : "";
        
        long totalHits = cacheCounters.entrySet().stream()
            .filter(entry -> entry.getKey().startsWith("cache_hit") && 
                           (customerId == null || entry.getKey().endsWith(customerFilter)))
            .mapToLong(entry -> entry.getValue().get())
            .sum();

        long totalMisses = cacheCounters.entrySet().stream()
            .filter(entry -> entry.getKey().startsWith("cache_miss") && 
                           (customerId == null || entry.getKey().endsWith(customerFilter)))
            .mapToLong(entry -> entry.getValue().get())
            .sum();

        analysis.put("cacheHits", totalHits);
        analysis.put("cacheMisses", totalMisses);

        if (totalHits + totalMisses > 0) {
            double hitRate = (double) totalHits / (totalHits + totalMisses) * 100;
            analysis.put("hitRate", String.format("%.1f%%", hitRate));
            
            if (hitRate < CACHE_HIT_RATE_ALERT_THRESHOLD) {
                analysis.put("alert", "缓存命中率较低，建议优化缓存策略");
            }
        }

        return analysis;
    }

    private List<String> generatePerformanceRecommendations(Map<String, Object> report) {
        List<String> recommendations = new ArrayList<>();

        // 分析基础统计数据
        Map<String, Object> basicStats = (Map<String, Object>) report.get("basicStatistics");
        if (basicStats != null) {
            Number avgTime = (Number) basicStats.get("averageExecutionTime");

            if (avgTime != null && avgTime.doubleValue() > PERFORMANCE_ALERT_THRESHOLD_MS) {
                recommendations.add("平均响应时间过长，建议优化数据库索引或增加缓存");
            }
        }

        // 分析缓存性能
        Map<String, Object> cacheAnalysis = (Map<String, Object>) report.get("cacheAnalysis");
        if (cacheAnalysis != null) {
            String hitRateStr = (String) cacheAnalysis.get("hitRate");
            if (hitRateStr != null) {
                double hitRate = Double.parseDouble(hitRateStr.replace("%", ""));
                if (hitRate < CACHE_HIT_RATE_ALERT_THRESHOLD) {
                    recommendations.add("缓存命中率偏低，建议调整缓存策略或增加缓存容量");
                }
            }
        }

        if (recommendations.isEmpty()) {
            recommendations.add("系统性能表现良好，继续保持当前优化策略");
        }

        return recommendations;
    }

    private void checkAverageResponseTimes() {
        recentExecutionTimes.forEach((key, times) -> {
            if (!times.isEmpty()) {
                double avgTime = times.stream().mapToLong(Long::longValue).average().orElse(0.0);
                if (avgTime > PERFORMANCE_ALERT_THRESHOLD_MS) {
                    log.warn("⚠️ 平均响应时间告警: operation={}, avgTime={}ms", key, avgTime);
                }
            }
        });
    }

    private void checkCacheHitRates() {
        Set<String> customerIds = cacheCounters.keySet().stream()
            .filter(key -> key.contains(":"))
            .map(key -> key.split(":")[1])
            .collect(Collectors.toSet());

        for (String customerId : customerIds) {
            long hits = cacheCounters.getOrDefault("cache_hit:" + customerId, new AtomicLong(0)).get();
            long misses = cacheCounters.getOrDefault("cache_miss:" + customerId, new AtomicLong(0)).get();

            if (hits + misses > 0) {
                double hitRate = (double) hits / (hits + misses) * 100;
                if (hitRate < CACHE_HIT_RATE_ALERT_THRESHOLD) {
                    log.warn("⚠️ 缓存命中率告警: customerId={}, hitRate={}%", customerId, String.format("%.1f", hitRate));
                }
            }
        }
    }

    private String determineSystemHealthStatus(Map<String, Double> avgResponseTimes, double cacheHitRate) {
        boolean hasSlowOperations = avgResponseTimes.values().stream()
            .anyMatch(time -> time > PERFORMANCE_ALERT_THRESHOLD_MS);
        
        boolean lowCacheHit = cacheHitRate < CACHE_HIT_RATE_ALERT_THRESHOLD;

        if (hasSlowOperations && lowCacheHit) {
            return "CRITICAL";
        } else if (hasSlowOperations || lowCacheHit) {
            return "WARNING";
        } else {
            return "HEALTHY";
        }
    }

    private void cleanExpiredPerformanceData() {
        // 清理内存中超过1小时的执行时间记录
        recentExecutionTimes.entrySet().removeIf(entry -> {
            List<Long> times = entry.getValue();
            return times.isEmpty();
        });

        // 重置过大的计数器
        performanceCounters.entrySet().forEach(entry -> {
            if (entry.getValue().get() > 1000000) {
                entry.getValue().set(0);
            }
        });

        cacheCounters.entrySet().forEach(entry -> {
            if (entry.getValue().get() > 1000000) {
                entry.getValue().set(0);
            }
        });
    }
}