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

package com.ljwx.modules.health.service;

import com.alibaba.fastjson.JSON;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.repository.mapper.TAlertRulesMapper;
import lombok.Data;
import lombok.Builder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.*;

/**
 * 告警规则缓存管理器 - 增强版本
 * 实现三层缓存架构和跨DB发布订阅
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertRulesCacheManager
 * @CreateTime 2025-09-10
 */
@Component
@Slf4j
public class AlertRulesCacheManager {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private TAlertRulesMapper alertRulesMapper;
    
    // 缓存通道名称
    private static final String CACHE_CHANNEL = "alert_rules_channel";
    
    // Redis缓存TTL (24小时)
    private static final Duration REDIS_CACHE_TTL = Duration.ofHours(24);
    
    // 异步任务执行器
    private ExecutorService asyncExecutor;
    
    // 批量更新队列
    private BlockingQueue<Long> updateQueue = new LinkedBlockingQueue<>(10000);
    
    // 统计信息
    private final CacheStats stats = new CacheStats();
    
    @PostConstruct
    public void init() {
        // 初始化异步执行器
        asyncExecutor = new ThreadPoolExecutor(
            2, 8, 60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),
            r -> {
                Thread t = new Thread(r, "alert-cache-manager-" + r.hashCode());
                t.setDaemon(true);
                return t;
            }
        );
        
        // 启动批量更新处理器
        startBatchUpdateProcessor();
        
        log.info("告警规则缓存管理器已初始化");
    }
    
    @PreDestroy
    public void destroy() {
        if (asyncExecutor != null && !asyncExecutor.isShutdown()) {
            asyncExecutor.shutdown();
            try {
                if (!asyncExecutor.awaitTermination(10, TimeUnit.SECONDS)) {
                    asyncExecutor.shutdownNow();
                }
            } catch (InterruptedException e) {
                asyncExecutor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
        log.info("告警规则缓存管理器已关闭");
    }
    
    /**
     * 更新告警规则缓存 - 增强版本
     */
    @Transactional
    public void updateAlertRulesCache(Long customerId) {
        String lockKey = "alert_rules_lock_" + customerId;
        
        try {
            // 分布式锁
            Boolean lockAcquired = redisTemplate.opsForValue()
                .setIfAbsent(lockKey, "locked", Duration.ofMinutes(5));
            
            if (!lockAcquired) {
                log.warn("获取分布式锁失败，添加到队列稍后处理: customerId={}", customerId);
                // 添加到队列稍后处理
                updateQueue.offer(customerId);
                return;
            }
            
            long startTime = System.currentTimeMillis();
            
            // 1. 查询最新规则
            List<TAlertRules> rules = loadRulesFromDatabase(customerId);
            
            // 2. 增加版本号
            Long version = redisTemplate.opsForValue().increment("alert_rules_version_" + customerId);
            
            // 3. 构建缓存数据
            CacheData cacheData = CacheData.builder()
                .version(version)
                .rules(rules)
                .updateTime(System.currentTimeMillis())
                .customerId(customerId)
                .ruleCount(rules.size())
                .build();
            
            // 4. 更新Redis缓存
            String cacheKey = "alert_rules:" + customerId;
            redisTemplate.opsForValue().set(cacheKey, rules, REDIS_CACHE_TTL);
            
            // 5. 发布更新通知
            String message = String.format("update:%s:%s", customerId, version);
            redisTemplate.convertAndSend(CACHE_CHANNEL, message);
            
            // 6. 记录同步状态
            updateSyncStatus(customerId, cacheKey, version, "synced", null);
            
            // 7. 更新统计
            long processingTime = System.currentTimeMillis() - startTime;
            stats.recordUpdate(processingTime);
            
            log.info("告警规则缓存更新成功: customerId={}, version={}, rules={}, time={}ms", 
                customerId, version, rules.size(), processingTime);
            
        } catch (Exception e) {
            log.error("告警规则缓存更新失败: customerId={}", customerId, e);
            updateSyncStatus(customerId, "alert_rules:" + customerId, 0L, "failed", e.getMessage());
            stats.recordFailure();
            throw e;
        } finally {
            redisTemplate.delete(lockKey);
        }
    }
    
    /**
     * 异步更新缓存
     */
    public void updateAlertRulesCacheAsync(Long customerId) {
        if (customerId == null) {
            return;
        }
        
        asyncExecutor.submit(() -> {
            try {
                updateAlertRulesCache(customerId);
            } catch (Exception e) {
                log.error("异步更新缓存失败: customerId={}", customerId, e);
            }
        });
    }
    
    /**
     * 批量更新缓存 - 性能优化
     */
    public void batchUpdateCache(List<Long> customerIds) {
        if (customerIds == null || customerIds.isEmpty()) {
            return;
        }
        
        log.info("开始批量更新缓存: {} 个客户", customerIds.size());
        
        // 分批处理，避免阻塞
        int batchSize = 10;
        List<CompletableFuture<Void>> futures = new ArrayList<>();
        
        for (int i = 0; i < customerIds.size(); i += batchSize) {
            List<Long> batch = customerIds.subList(i, Math.min(i + batchSize, customerIds.size()));
            
            CompletableFuture<Void> future = CompletableFuture.runAsync(() -> {
                batch.parallelStream().forEach(this::updateAlertRulesCache);
            }, asyncExecutor);
            
            futures.add(future);
        }
        
        // 等待所有批次完成
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
            futures.toArray(new CompletableFuture[0])
        );
        
        try {
            allFutures.get(5, TimeUnit.MINUTES); // 5分钟超时
            log.info("批量缓存更新完成: {} 个客户", customerIds.size());
        } catch (Exception e) {
            log.error("批量缓存更新部分失败", e);
        }
    }
    
    /**
     * 启动批量更新处理器
     */
    private void startBatchUpdateProcessor() {
        asyncExecutor.submit(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    // 批量从队列中取出待更新的客户ID
                    List<Long> batch = new ArrayList<>();
                    Long customerId = updateQueue.poll(5, TimeUnit.SECONDS);
                    
                    if (customerId != null) {
                        batch.add(customerId);
                        
                        // 继续取出更多元素，最多处理20个
                        updateQueue.drainTo(batch, 19);
                        
                        // 去重
                        List<Long> uniqueBatch = batch.stream().distinct().collect(java.util.stream.Collectors.toList());
                        
                        log.debug("批量处理队列中的缓存更新: {} 个客户", uniqueBatch.size());
                        
                        // 并行处理
                        uniqueBatch.parallelStream().forEach(id -> {
                            try {
                                updateAlertRulesCache(id);
                            } catch (Exception e) {
                                log.error("队列处理缓存更新失败: customerId={}", id, e);
                            }
                        });
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    log.error("批量更新处理器异常", e);
                }
            }
        });
    }
    
    /**
     * 从数据库加载规则
     */
    private List<TAlertRules> loadRulesFromDatabase(Long customerId) {
        try {
            LambdaQueryWrapper<TAlertRules> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(TAlertRules::getCustomerId, customerId)
                   .eq(TAlertRules::getIsEnabled, true)
                   .eq(TAlertRules::getDeleted, 0)  // 0表示未删除
                   .orderBy(true, true, TAlertRules::getPriorityLevel);
            
            List<TAlertRules> rules = alertRulesMapper.selectList(wrapper);
            return rules != null ? rules : java.util.Collections.emptyList();
            
        } catch (Exception e) {
            log.error("从数据库加载规则失败: customerId={}", customerId, e);
            return java.util.Collections.emptyList();
        }
    }
    
    /**
     * 更新同步状态
     */
    private void updateSyncStatus(Long customerId, String cacheKey, Long version, String status, String errorMessage) {
        try {
            // 这里可以插入到 t_alert_cache_sync 表中
            // 由于没有对应的 mapper，暂时记录日志
            log.debug("缓存同步状态: customerId={}, cacheKey={}, version={}, status={}, error={}", 
                customerId, cacheKey, version, status, errorMessage);
                
        } catch (Exception e) {
            log.warn("记录同步状态失败", e);
        }
    }
    
    /**
     * 发布规则变更事件
     */
    public void publishRuleChangeEvent(Long customerId, String changeType) {
        try {
            String message = String.format("%s:%s:%s", changeType, customerId, System.currentTimeMillis());
            redisTemplate.convertAndSend(CACHE_CHANNEL, message);
            log.debug("发布规则变更事件: {}", message);
        } catch (Exception e) {
            log.error("发布规则变更事件失败: customerId={}, changeType={}", customerId, changeType, e);
        }
    }
    
    /**
     * 预热缓存
     */
    public void warmUpCache(List<Long> customerIds) {
        if (customerIds == null || customerIds.isEmpty()) {
            return;
        }
        
        log.info("开始预热告警规则缓存: {} 个客户", customerIds.size());
        long startTime = System.currentTimeMillis();
        
        CompletableFuture<Void> warmUpTask = CompletableFuture.runAsync(() -> {
            customerIds.parallelStream().forEach(customerId -> {
                try {
                    List<TAlertRules> rules = loadRulesFromDatabase(customerId);
                    if (!rules.isEmpty()) {
                        String cacheKey = "alert_rules:" + customerId;
                        redisTemplate.opsForValue().set(cacheKey, rules, REDIS_CACHE_TTL);
                    }
                } catch (Exception e) {
                    log.warn("预热缓存失败: customerId={}", customerId, e);
                }
            });
        }, asyncExecutor);
        
        try {
            warmUpTask.get(2, TimeUnit.MINUTES);
            long duration = System.currentTimeMillis() - startTime;
            log.info("告警规则缓存预热完成: {} 个客户, 耗时: {}ms", customerIds.size(), duration);
        } catch (Exception e) {
            log.error("缓存预热超时或失败", e);
        }
    }
    
    /**
     * 清空指定客户的缓存
     */
    public void clearCustomerCache(Long customerId) {
        try {
            String cacheKey = "alert_rules:" + customerId;
            redisTemplate.delete(cacheKey);
            redisTemplate.delete("alert_rules_version_" + customerId);
            
            // 发布清除事件
            publishRuleChangeEvent(customerId, "clear");
            
            log.info("清空客户缓存: customerId={}", customerId);
            
        } catch (Exception e) {
            log.error("清空客户缓存失败: customerId={}", customerId, e);
        }
    }
    
    /**
     * 获取缓存统计信息
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> result = new java.util.HashMap<>();
        result.put("updateCount", stats.getUpdateCount());
        result.put("failureCount", stats.getFailureCount());
        result.put("avgUpdateTime", stats.getAvgUpdateTime());
        result.put("queueSize", updateQueue.size());
        result.put("threadPoolSize", ((ThreadPoolExecutor) asyncExecutor).getPoolSize());
        result.put("activeThreads", ((ThreadPoolExecutor) asyncExecutor).getActiveCount());
        result.put("completedTasks", ((ThreadPoolExecutor) asyncExecutor).getCompletedTaskCount());
        return result;
    }
    
    /**
     * 健康检查
     */
    public boolean healthCheck() {
        try {
            // 检查Redis连接
            String testKey = "alert_rules_health_check";
            redisTemplate.opsForValue().set(testKey, "ok", Duration.ofSeconds(10));
            Object value = redisTemplate.opsForValue().get(testKey);
            
            if (!"ok".equals(value)) {
                log.warn("Redis健康检查失败: value={}", value);
                return false;
            }
            
            // 检查线程池状态
            if (asyncExecutor.isShutdown() || asyncExecutor.isTerminated()) {
                log.warn("线程池已关闭");
                return false;
            }
            
            return true;
            
        } catch (Exception e) {
            log.error("缓存管理器健康检查失败", e);
            return false;
        }
    }
    
    /**
     * 缓存数据
     */
    @Data
    @Builder
    private static class CacheData {
        private Long version;
        private List<TAlertRules> rules;
        private Long updateTime;
        private Long customerId;
        private Integer ruleCount;
    }
    
    /**
     * 缓存统计信息
     */
    private static class CacheStats {
        private volatile long updateCount = 0;
        private volatile long failureCount = 0;
        private volatile long totalUpdateTime = 0;
        
        public void recordUpdate(long processingTime) {
            updateCount++;
            totalUpdateTime += processingTime;
        }
        
        public void recordFailure() {
            failureCount++;
        }
        
        public long getUpdateCount() {
            return updateCount;
        }
        
        public long getFailureCount() {
            return failureCount;
        }
        
        public double getAvgUpdateTime() {
            return updateCount > 0 ? (double) totalUpdateTime / updateCount : 0;
        }
    }
}