package com.ljwx.admin.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.StopWatch;
import org.springframework.boot.actuate.metrics.MetricsEndpoint;

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
 * @author Claude Code Assistant
 * @since 2025-08-30
 */
@Slf4j
@Service
public class OrgPerformanceMonitorService {

    @Autowired
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

    // ================== 性能指标收集 ==================

    /**
     * 记录查询操作的性能指标
     * 
     * @param operationType 操作类型
     * @param customerId 租户ID
     * @param orgId 组织ID
     * @param executionTimeMs 执行时间(毫秒)
     * @param resultCount 结果数量
     * @param success 是否成功
     * @param errorMessage 错误信息
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

            // 5. 异步写入数据库
            persistPerformanceLog(operationType, customerId, orgId, executionTimeMs, resultCount, success, errorMessage);

        } catch (Exception e) {
            // 监控系统本身的错误不应影响业务逻辑
            log.debug("记录性能指标失败: operation={}, customerId={}", operationType, customerId, e);
        }
    }

    /**
     * 记录缓存操作指标
     * 
     * @param cacheOperation 缓存操作类型 (HIT/MISS/EVICT)
     * @param cacheKey 缓存键
     * @param customerId 租户ID
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

    // ================== 性能分析报告 ==================

    /**
     * 生成性能分析报告
     * 
     * @param customerId 租户ID (null表示全局报告)
     * @param hours 统计时间范围(小时)
     * @return 性能分析报告
     */
    public Map<String, Object> generatePerformanceReport(Long customerId, int hours) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        Map<String, Object> report = new HashMap<>();

        try {
            // 1. 基础性能统计
            Map<String, Object> basicStats = getBasicPerformanceStats(customerId, hours);
            report.put("basicStatistics", basicStats);

            // 2. 操作类型分析
            List<Map<String, Object>> operationAnalysis = getOperationTypeAnalysis(customerId, hours);
            report.put("operationAnalysis", operationAnalysis);

            // 3. 性能趋势分析
            Map<String, Object> trendAnalysis = getPerformanceTrends(customerId, hours);
            report.put("trendAnalysis", trendAnalysis);

            // 4. 缓存性能分析
            Map<String, Object> cacheAnalysis = getCachePerformanceAnalysis(customerId);
            report.put("cacheAnalysis", cacheAnalysis);

            // 5. 慢查询分析
            List<Map<String, Object>> slowQueries = getSlowQueriesAnalysis(customerId, hours);
            report.put("slowQueries", slowQueries);

            // 6. 租户性能排名
            if (customerId == null) {
                List<Map<String, Object>> tenantRanking = getTenantPerformanceRanking(hours);
                report.put("tenantRanking", tenantRanking);
            }

            // 7. 性能建议
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
     * 
     * @param customerId 租户ID
     * @return 实时性能指标
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

            // 4. 当前活跃连接（从数据库获取）
            Integer activeConnections = getCurrentActiveConnections();
            metrics.put("activeConnections", activeConnections);

            // 5. 系统健康状态
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

    // ================== 定时任务监控 ==================

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

            // 3. 检查数据库连接状态
            checkDatabaseConnectionHealth();

            // 4. 清理过期的性能数据
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
                log.info("🎯 每小时性能摘要: 总查询={}, 平均耗时={}ms, 成功率={}%", 
                    basicStats.get("totalQueries"), 
                    basicStats.get("averageExecutionTime"),
                    basicStats.get("successRate"));
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

    /**
     * 每天清理历史性能数据
     */
    @Scheduled(cron = "0 2 * * * ?") // 每天凌晨2点
    public void cleanHistoricalPerformanceData() {
        try {
            log.info("🧹 开始清理历史性能数据...");

            // 清理30天前的性能日志
            String cleanSql = """
                DELETE FROM sys_org_performance_log 
                WHERE create_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
                """;
            int deletedRows = jdbcTemplate.update(cleanSql);

            log.info("✅ 历史性能数据清理完成: 删除{}条记录", deletedRows);

        } catch (Exception e) {
            log.error("❌ 清理历史性能数据失败", e);
        }
    }

    // ================== 私有辅助方法 ==================

    private void recordSlowQuery(String operationType, Long customerId, Long orgId, 
                                long executionTimeMs, int resultCount) {
        log.warn("🐌 慢查询检测: operation={}, customerId={}, orgId={}, time={}ms, count={}", 
            operationType, customerId, orgId, executionTimeMs, resultCount);

        // 记录慢查询详情
        try {
            String sql = """
                INSERT INTO sys_org_performance_log 
                (operation_type, customer_id, org_id, execution_time_ms, result_count, success, error_message)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """;
            
            String slowQueryNote = String.format("SLOW_QUERY: %dms (threshold: %dms)", 
                executionTimeMs, SLOW_QUERY_THRESHOLD_MS);
                
            jdbcTemplate.update(sql, "SLOW_" + operationType, customerId, orgId, 
                executionTimeMs, resultCount, slowQueryNote);

        } catch (Exception e) {
            log.debug("记录慢查询失败", e);
        }
    }

    private void triggerPerformanceAlert(String operationType, Long customerId, 
                                       long executionTimeMs, String errorMessage) {
        log.error("🚨 性能告警: operation={}, customerId={}, time={}ms, error={}", 
            operationType, customerId, executionTimeMs, errorMessage);

        // 这里可以集成告警系统，发送邮件、短信等通知
        // alertNotificationService.sendPerformanceAlert(...)
    }

    private void persistPerformanceLog(String operationType, Long customerId, Long orgId, 
                                     long executionTimeMs, int resultCount, boolean success, String errorMessage) {
        try {
            String sql = """
                INSERT INTO sys_org_performance_log 
                (operation_type, customer_id, org_id, execution_time_ms, result_count, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """;
            
            jdbcTemplate.update(sql, operationType, customerId, orgId, 
                executionTimeMs, resultCount, success ? 1 : 0, errorMessage);

        } catch (Exception e) {
            log.debug("持久化性能日志失败", e);
        }
    }

    private Map<String, Object> getBasicPerformanceStats(Long customerId, int hours) {
        String customerFilter = customerId != null ? " AND customer_id = ?" : "";
        String sql = String.format("""
            SELECT 
                COUNT(*) as total_queries,
                AVG(execution_time_ms) as avg_execution_time,
                MAX(execution_time_ms) as max_execution_time,
                MIN(execution_time_ms) as min_execution_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
                COUNT(DISTINCT customer_id) as unique_customers,
                COUNT(DISTINCT operation_type) as unique_operations
            FROM sys_org_performance_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)%s
            """, customerFilter);

        List<Object> params = new ArrayList<>();
        params.add(hours);
        if (customerId != null) {
            params.add(customerId);
        }

        List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, params.toArray());
        
        if (!results.isEmpty()) {
            Map<String, Object> stats = new HashMap<>(results.get(0));
            
            // 计算成功率
            Integer totalQueries = (Integer) stats.get("total_queries");
            Integer successCount = (Integer) stats.get("success_count");
            if (totalQueries != null && totalQueries > 0) {
                double successRate = (double) successCount / totalQueries * 100;
                stats.put("successRate", Math.round(successRate * 10.0) / 10.0);
            }
            
            return stats;
        }
        
        return Collections.emptyMap();
    }

    private List<Map<String, Object>> getOperationTypeAnalysis(Long customerId, int hours) {
        String customerFilter = customerId != null ? " AND customer_id = ?" : "";
        String sql = String.format("""
            SELECT 
                operation_type,
                COUNT(*) as call_count,
                AVG(execution_time_ms) as avg_time,
                MAX(execution_time_ms) as max_time,
                MIN(execution_time_ms) as min_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN execution_time_ms > %d THEN 1 ELSE 0 END) as slow_query_count
            FROM sys_org_performance_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)%s
            GROUP BY operation_type
            ORDER BY call_count DESC
            """, SLOW_QUERY_THRESHOLD_MS, customerFilter);

        List<Object> params = new ArrayList<>();
        params.add(hours);
        if (customerId != null) {
            params.add(customerId);
        }

        return jdbcTemplate.queryForList(sql, params.toArray());
    }

    private Map<String, Object> getPerformanceTrends(Long customerId, int hours) {
        String customerFilter = customerId != null ? " AND customer_id = ?" : "";
        String sql = String.format("""
            SELECT 
                DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:00:00') as hour_slot,
                COUNT(*) as query_count,
                AVG(execution_time_ms) as avg_response_time,
                MAX(execution_time_ms) as max_response_time
            FROM sys_org_performance_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)%s
            GROUP BY DATE_FORMAT(create_time, '%%Y-%%m-%%d %%H:00:00')
            ORDER BY hour_slot DESC
            LIMIT 24
            """, customerFilter);

        List<Object> params = new ArrayList<>();
        params.add(hours);
        if (customerId != null) {
            params.add(customerId);
        }

        List<Map<String, Object>> trends = jdbcTemplate.queryForList(sql, params.toArray());
        
        Map<String, Object> result = new HashMap<>();
        result.put("hourlyTrends", trends);
        
        // 计算趋势指标
        if (trends.size() >= 2) {
            Map<String, Object> latest = trends.get(0);
            Map<String, Object> previous = trends.get(1);
            
            Number latestAvg = (Number) latest.get("avg_response_time");
            Number previousAvg = (Number) previous.get("avg_response_time");
            
            if (latestAvg != null && previousAvg != null) {
                double trend = (latestAvg.doubleValue() - previousAvg.doubleValue()) / previousAvg.doubleValue() * 100;
                result.put("responseTimeTrend", String.format("%.1f%%", trend));
                result.put("trendDirection", trend > 0 ? "INCREASING" : "DECREASING");
            }
        }
        
        return result;
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

        long totalEvicts = cacheCounters.entrySet().stream()
            .filter(entry -> entry.getKey().startsWith("cache_evict") && 
                           (customerId == null || entry.getKey().endsWith(customerFilter)))
            .mapToLong(entry -> entry.getValue().get())
            .sum();

        analysis.put("cacheHits", totalHits);
        analysis.put("cacheMisses", totalMisses);
        analysis.put("cacheEvictions", totalEvicts);

        if (totalHits + totalMisses > 0) {
            double hitRate = (double) totalHits / (totalHits + totalMisses) * 100;
            analysis.put("hitRate", String.format("%.1f%%", hitRate));
            
            if (hitRate < CACHE_HIT_RATE_ALERT_THRESHOLD) {
                analysis.put("alert", "缓存命中率较低，建议优化缓存策略");
            }
        }

        return analysis;
    }

    private List<Map<String, Object>> getSlowQueriesAnalysis(Long customerId, int hours) {
        String customerFilter = customerId != null ? " AND customer_id = ?" : "";
        String sql = String.format("""
            SELECT 
                operation_type,
                customer_id,
                org_id,
                execution_time_ms,
                result_count,
                create_time,
                error_message
            FROM sys_org_performance_log 
            WHERE execution_time_ms > ? 
              AND create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)%s
            ORDER BY execution_time_ms DESC
            LIMIT 50
            """, customerFilter);

        List<Object> params = new ArrayList<>();
        params.add(SLOW_QUERY_THRESHOLD_MS);
        params.add(hours);
        if (customerId != null) {
            params.add(customerId);
        }

        return jdbcTemplate.queryForList(sql, params.toArray());
    }

    private List<Map<String, Object>> getTenantPerformanceRanking(int hours) {
        String sql = """
            SELECT 
                customer_id,
                COUNT(*) as total_queries,
                AVG(execution_time_ms) as avg_response_time,
                MAX(execution_time_ms) as max_response_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN execution_time_ms > ? THEN 1 ELSE 0 END) as slow_query_count
            FROM sys_org_performance_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)
            GROUP BY customer_id
            ORDER BY total_queries DESC
            LIMIT 20
            """;

        return jdbcTemplate.queryForList(sql, SLOW_QUERY_THRESHOLD_MS, hours);
    }

    private List<String> generatePerformanceRecommendations(Map<String, Object> report) {
        List<String> recommendations = new ArrayList<>();

        // 分析基础统计数据
        Map<String, Object> basicStats = (Map<String, Object>) report.get("basicStatistics");
        if (basicStats != null) {
            Number avgTime = (Number) basicStats.get("avg_execution_time");
            Number successRate = (Number) basicStats.get("successRate");

            if (avgTime != null && avgTime.doubleValue() > PERFORMANCE_ALERT_THRESHOLD_MS) {
                recommendations.add("平均响应时间过长，建议优化数据库索引或增加缓存");
            }

            if (successRate != null && successRate.doubleValue() < 95.0) {
                recommendations.add("查询成功率较低，建议检查错误日志并优化异常处理");
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

        // 分析慢查询
        List<Map<String, Object>> slowQueries = (List<Map<String, Object>>) report.get("slowQueries");
        if (slowQueries != null && !slowQueries.isEmpty()) {
            recommendations.add(String.format("发现%d个慢查询，建议针对性优化相关操作", slowQueries.size()));
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

    private void checkDatabaseConnectionHealth() {
        try {
            Integer connectionCount = getCurrentActiveConnections();
            if (connectionCount != null && connectionCount > 80) {
                log.warn("⚠️ 数据库连接数告警: activeConnections={}", connectionCount);
            }
        } catch (Exception e) {
            log.error("❌ 数据库连接健康检查失败", e);
        }
    }

    private Integer getCurrentActiveConnections() {
        try {
            String sql = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND != 'Sleep'";
            return jdbcTemplate.queryForObject(sql, Integer.class);
        } catch (Exception e) {
            log.debug("获取数据库连接数失败", e);
            return null;
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