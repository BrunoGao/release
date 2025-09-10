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

package com.ljwx.admin.controller.monitor;

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.service.AlertRuleEngineService;
import com.ljwx.modules.health.service.AlertRulesCacheManager;
import com.ljwx.modules.health.service.UnifiedMessagePublisher;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 告警系统性能监控控制器
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertPerformanceController
 * @CreateTime 2025-09-10
 */
@Tag(name = "告警性能监控", description = "告警系统性能监控和统计接口")
@RestController
@RequestMapping("/api/monitor/alert")
@Slf4j
public class AlertPerformanceController {
    
    @Autowired
    private AlertRuleEngineService alertRuleEngineService;
    
    @Autowired
    private AlertRulesCacheManager cacheManager;
    
    @Autowired
    private UnifiedMessagePublisher messagePublisher;
    
    /**
     * 获取告警系统性能统计
     */
    @Operation(summary = "获取告警系统性能统计", description = "获取规则引擎、缓存管理器、消息发布器的性能统计信息")
    @GetMapping("/performance/stats")
    public Result<Map<String, Object>> getPerformanceStats() {
        try {
            Map<String, Object> stats = new HashMap<>();
            
            // 1. 规则引擎统计
            Map<String, Object> engineStats = alertRuleEngineService.getCacheStats();
            stats.put("engine", engineStats);
            
            // 2. 缓存管理器统计
            Map<String, Object> cacheStats = cacheManager.getCacheStats();
            stats.put("cache", cacheStats);
            
            // 3. 消息发布器统计
            Map<String, Object> messageStats = messagePublisher.getMessageStats();
            stats.put("message", messageStats);
            
            // 4. 系统概览
            Map<String, Object> overview = buildSystemOverview(engineStats, cacheStats, messageStats);
            stats.put("overview", overview);
            
            // 5. 时间戳
            stats.put("timestamp", LocalDateTime.now());
            stats.put("collectTime", System.currentTimeMillis());
            
            return Result.data(stats);
            
        } catch (Exception e) {
            log.error("获取性能统计失败", e);
            return Result.failure("获取性能统计失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取缓存健康状态
     */
    @Operation(summary = "缓存健康检查", description = "检查告警规则缓存管理器的健康状态")
    @GetMapping("/cache/health")
    public Result<Map<String, Object>> getCacheHealth() {
        try {
            boolean isHealthy = cacheManager.healthCheck();
            Map<String, Object> cacheStats = cacheManager.getCacheStats();
            
            Map<String, Object> health = new HashMap<>();
            health.put("healthy", isHealthy);
            health.put("status", isHealthy ? "UP" : "DOWN");
            health.put("stats", cacheStats);
            health.put("checkTime", LocalDateTime.now());
            
            return Result.data(health);
            
        } catch (Exception e) {
            log.error("缓存健康检查失败", e);
            Map<String, Object> health = new HashMap<>();
            health.put("healthy", false);
            health.put("status", "ERROR");
            health.put("error", e.getMessage());
            health.put("checkTime", LocalDateTime.now());
            
            return Result.data(health);
        }
    }
    
    /**
     * 清空指定客户的缓存
     */
    @Operation(summary = "清空客户缓存", description = "清空指定客户的告警规则缓存")
    @DeleteMapping("/cache/{customerId}")
    public Result<String> clearCustomerCache(@PathVariable Long customerId) {
        try {
            alertRuleEngineService.clearCustomerCache(String.valueOf(customerId));
            cacheManager.clearCustomerCache(customerId);
            
            log.info("清空客户缓存成功: customerId={}", customerId);
            return Result.success("缓存清空成功");
            
        } catch (Exception e) {
            log.error("清空客户缓存失败: customerId={}", customerId, e);
            return Result.failure("清空缓存失败: " + e.getMessage());
        }
    }
    
    /**
     * 清空所有本地缓存
     */
    @Operation(summary = "清空所有缓存", description = "清空告警规则引擎的所有本地缓存")
    @DeleteMapping("/cache/all")
    public Result<String> clearAllCache() {
        try {
            alertRuleEngineService.clearLocalCache();
            
            log.info("清空所有本地缓存成功");
            return Result.success("所有缓存清空成功");
            
        } catch (Exception e) {
            log.error("清空所有缓存失败", e);
            return Result.failure("清空缓存失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取线程池状态
     */
    @Operation(summary = "获取线程池状态", description = "获取告警系统相关线程池的运行状态")
    @GetMapping("/threadpool/status")
    public Result<Map<String, Object>> getThreadPoolStatus() {
        try {
            Map<String, Object> status = new HashMap<>();
            
            // 从各个服务获取线程池状态
            Map<String, Object> engineStats = alertRuleEngineService.getCacheStats();
            Map<String, Object> cacheStats = cacheManager.getCacheStats();
            
            // 规则引擎线程池
            if (engineStats.containsKey("threadPoolSize")) {
                Map<String, Object> engineThreadPool = new HashMap<>();
                engineThreadPool.put("poolSize", engineStats.get("threadPoolSize"));
                engineThreadPool.put("activeThreads", engineStats.get("activeThreads"));
                engineThreadPool.put("queueSize", engineStats.get("queueSize"));
                engineThreadPool.put("status", "RUNNING");
                status.put("ruleEngine", engineThreadPool);
            }
            
            // 缓存管理器线程池
            if (cacheStats.containsKey("threadPoolSize")) {
                Map<String, Object> cacheThreadPool = new HashMap<>();
                cacheThreadPool.put("poolSize", cacheStats.get("threadPoolSize"));
                cacheThreadPool.put("activeThreads", cacheStats.get("activeThreads"));
                cacheThreadPool.put("completedTasks", cacheStats.get("completedTasks"));
                cacheThreadPool.put("status", "RUNNING");
                status.put("cacheManager", cacheThreadPool);
            }
            
            status.put("checkTime", LocalDateTime.now());
            
            return Result.data(status);
            
        } catch (Exception e) {
            log.error("获取线程池状态失败", e);
            return Result.failure("获取线程池状态失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取告警生成统计
     */
    @Operation(summary = "获取告警生成统计", description = "获取告警生成相关的统计信息")
    @GetMapping("/alerts/stats")
    public Result<Map<String, Object>> getAlertStats(
            @RequestParam(required = false, defaultValue = "today") String period) {
        
        try {
            Map<String, Object> alertStats = getAlertGenerationStats(period);
            return Result.data(alertStats);
            
        } catch (Exception e) {
            log.error("获取告警统计失败", e);
            return Result.failure("获取告警统计失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取规则执行性能排行
     */
    @Operation(summary = "获取规则性能排行", description = "获取告警规则执行性能排行榜")
    @GetMapping("/rules/performance/ranking")
    public Result<Map<String, Object>> getRulePerformanceRanking(
            @RequestParam(required = false, defaultValue = "10") Integer limit) {
        
        try {
            Map<String, Object> ranking = getRuleExecutionRanking(limit);
            return Result.data(ranking);
            
        } catch (Exception e) {
            log.error("获取规则性能排行失败", e);
            return Result.failure("获取规则性能排行失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取系统负载指标
     */
    @Operation(summary = "获取系统负载", description = "获取告警系统的负载指标")
    @GetMapping("/system/load")
    public Result<Map<String, Object>> getSystemLoad() {
        try {
            Map<String, Object> load = new HashMap<>();
            
            // JVM内存使用情况
            Runtime runtime = Runtime.getRuntime();
            Map<String, Object> memory = new HashMap<>();
            memory.put("totalMemory", runtime.totalMemory());
            memory.put("freeMemory", runtime.freeMemory());
            memory.put("usedMemory", runtime.totalMemory() - runtime.freeMemory());
            memory.put("maxMemory", runtime.maxMemory());
            
            double memoryUsagePercent = (double) (runtime.totalMemory() - runtime.freeMemory()) / runtime.maxMemory() * 100;
            memory.put("usagePercent", Math.round(memoryUsagePercent * 100.0) / 100.0);
            
            load.put("memory", memory);
            
            // CPU核心数
            load.put("availableProcessors", runtime.availableProcessors());
            
            // 系统负载平均值 (仅Unix系统)
            try {
                java.lang.management.OperatingSystemMXBean osBean = 
                    java.lang.management.ManagementFactory.getOperatingSystemMXBean();
                if (osBean instanceof com.sun.management.OperatingSystemMXBean) {
                    com.sun.management.OperatingSystemMXBean sunOsBean = 
                        (com.sun.management.OperatingSystemMXBean) osBean;
                    
                    Map<String, Object> cpu = new HashMap<>();
                    cpu.put("processCpuLoad", Math.round(sunOsBean.getProcessCpuLoad() * 10000.0) / 100.0);
                    cpu.put("systemCpuLoad", Math.round(sunOsBean.getSystemCpuLoad() * 10000.0) / 100.0);
                    load.put("cpu", cpu);
                }
            } catch (Exception e) {
                log.debug("获取CPU负载信息失败", e);
            }
            
            load.put("collectTime", LocalDateTime.now());
            
            return Result.data(load);
            
        } catch (Exception e) {
            log.error("获取系统负载失败", e);
            return Result.failure("获取系统负载失败: " + e.getMessage());
        }
    }
    
    /**
     * 构建系统概览
     */
    private Map<String, Object> buildSystemOverview(
            Map<String, Object> engineStats, 
            Map<String, Object> cacheStats, 
            Map<String, Object> messageStats) {
        
        Map<String, Object> overview = new HashMap<>();
        
        // 总体状态评估
        boolean systemHealthy = true;
        StringBuilder healthIssues = new StringBuilder();
        
        // 检查缓存命中率
        Object hitRateObj = cacheStats.get("hit_rate");
        if (hitRateObj instanceof Number) {
            double hitRate = ((Number) hitRateObj).doubleValue();
            if (hitRate < 80) {
                systemHealthy = false;
                healthIssues.append("缓存命中率偏低(").append(hitRate).append("%); ");
            }
        }
        
        // 检查消息发送成功率
        Object successRateObj = messageStats.get("successRate");
        if (successRateObj instanceof Number) {
            double successRate = ((Number) successRateObj).doubleValue();
            if (successRate < 95) {
                systemHealthy = false;
                healthIssues.append("消息发送成功率偏低(").append(successRate).append("%); ");
            }
        }
        
        overview.put("systemHealthy", systemHealthy);
        overview.put("status", systemHealthy ? "HEALTHY" : "WARNING");
        if (!systemHealthy) {
            overview.put("issues", healthIssues.toString());
        }
        
        // 性能摘要
        overview.put("cacheHitRate", hitRateObj);
        overview.put("messageSuccessRate", successRateObj);
        overview.put("avgProcessingTime", messageStats.get("avgProcessingTime"));
        
        return overview;
    }
    
    /**
     * 获取告警生成统计 (模拟实现)
     */
    private Map<String, Object> getAlertGenerationStats(String period) {
        Map<String, Object> stats = new HashMap<>();
        
        // TODO: 实现真实的数据库查询
        // 这里使用模拟数据
        stats.put("totalAlerts", 1250);
        stats.put("todayAlerts", 89);
        stats.put("criticalAlerts", 12);
        stats.put("majorAlerts", 45);
        stats.put("minorAlerts", 156);
        stats.put("infoAlerts", 78);
        
        // 按小时分布
        int[] hourlyDistribution = new int[24];
        for (int i = 0; i < 24; i++) {
            hourlyDistribution[i] = (int) (Math.random() * 20);
        }
        stats.put("hourlyDistribution", hourlyDistribution);
        
        // 按规则类型分布
        Map<String, Object> typeDistribution = new HashMap<>();
        typeDistribution.put("SINGLE", 1050);
        typeDistribution.put("COMPOSITE", 180);
        typeDistribution.put("COMPLEX", 20);
        stats.put("typeDistribution", typeDistribution);
        
        return stats;
    }
    
    /**
     * 获取规则执行性能排行 (模拟实现)
     */
    private Map<String, Object> getRuleExecutionRanking(Integer limit) {
        Map<String, Object> ranking = new HashMap<>();
        
        // TODO: 实现真实的性能统计查询
        // 这里使用模拟数据
        java.util.List<Map<String, Object>> topRules = new java.util.ArrayList<>();
        
        for (int i = 1; i <= Math.min(limit, 10); i++) {
            Map<String, Object> rule = new HashMap<>();
            rule.put("ruleId", i);
            rule.put("ruleName", "规则" + i);
            rule.put("ruleType", i % 3 == 0 ? "COMPOSITE" : "SINGLE");
            rule.put("avgExecutionTime", 10 + Math.random() * 50);
            rule.put("totalExecutions", 1000 + (int) (Math.random() * 5000));
            rule.put("successRate", 95 + Math.random() * 5);
            rule.put("lastExecution", LocalDateTime.now().minusMinutes((int) (Math.random() * 60)));
            topRules.add(rule);
        }
        
        ranking.put("topPerformanceRules", topRules);
        ranking.put("totalRules", 125);
        ranking.put("avgExecutionTime", 28.5);
        ranking.put("overallSuccessRate", 98.2);
        
        return ranking;
    }
}