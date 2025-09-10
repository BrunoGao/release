/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.modules.customer.service;

import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 健康数据配置缓存服务
 * 负责租户级别的体征指标缓存管理
 * 
 * @author brunoGao
 */
@Slf4j
@Service
public class HealthDataConfigCacheService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    @Lazy
    private ITHealthDataConfigService healthDataConfigService;

    private static final String HEALTH_CONFIG_CACHE_PREFIX = "health:config:";
    private static final String ENABLED_METRICS_KEY = "enabled_metrics";
    private static final long CACHE_EXPIRE_HOURS = 24; // 24小时缓存
    
    /**
     * 获取租户启用的体征指标（带缓存）
     * @param customerId 租户ID
     * @return 启用的指标列表
     */
    public List<String> getEnabledMetrics(Long customerId) {
        String cacheKey = buildCacheKey(customerId, ENABLED_METRICS_KEY);
        
        try {
            // 尝试从缓存获取
            @SuppressWarnings("unchecked")
            List<String> cachedMetrics = (List<String>) redisTemplate.opsForValue().get(cacheKey);
            
            if (cachedMetrics != null) {
                log.debug("🎯 健康配置缓存命中: customer_id={}, metrics={}", customerId, cachedMetrics.size());
                return cachedMetrics;
            }
            
            // 缓存未命中，从数据库查询
            log.warn("⚠️ 健康配置缓存miss: customer_id={}", customerId);
            List<String> metrics = loadEnabledMetricsFromDB(customerId);
            
            // 存入缓存
            if (!metrics.isEmpty()) {
                cacheEnabledMetrics(customerId, metrics);
                log.info("✅ 健康配置已缓存: customer_id={}, metrics={}", customerId, metrics);
            }
            
            return metrics;
            
        } catch (Exception e) {
            log.error("❌ 健康配置缓存异常: customer_id={}, error={}", customerId, e.getMessage());
            // 降级到直接数据库查询
            return loadEnabledMetricsFromDB(customerId);
        }
    }
    
    /**
     * 缓存租户启用的体征指标
     * @param customerId 租户ID
     * @param metrics 指标列表
     */
    public void cacheEnabledMetrics(Long customerId, List<String> metrics) {
        String cacheKey = buildCacheKey(customerId, ENABLED_METRICS_KEY);
        
        try {
            redisTemplate.opsForValue().set(cacheKey, metrics, CACHE_EXPIRE_HOURS, TimeUnit.HOURS);
            log.info("✅ 健康配置缓存更新: customer_id={}, metrics_count={}", customerId, metrics.size());
        } catch (Exception e) {
            log.error("❌ 健康配置缓存失败: customer_id={}, error={}", customerId, e.getMessage());
        }
    }
    
    /**
     * 失效租户的健康配置缓存
     * @param customerId 租户ID
     */
    public void invalidateCache(Long customerId) {
        try {
            String pattern = buildCacheKey(customerId, "*");
            redisTemplate.delete(redisTemplate.keys(pattern));
            
            // 发布缓存失效事件到ljwx-bigscreen
            publishCacheInvalidationEvent(customerId);
            
            log.info("🗑️ 健康配置缓存已失效: customer_id={}", customerId);
        } catch (Exception e) {
            log.error("❌ 健康配置缓存失效异常: customer_id={}, error={}", customerId, e.getMessage());
        }
    }
    
    /**
     * 发布缓存失效事件
     * @param customerId 租户ID
     */
    private void publishCacheInvalidationEvent(Long customerId) {
        try {
            String channel = "health_config_changed";
            String message = String.format("{\"customer_id\":%d,\"event\":\"config_updated\",\"timestamp\":%d}", 
                customerId, System.currentTimeMillis());
            
            redisTemplate.convertAndSend(channel, message);
            log.info("📢 健康配置变更事件已发布: customer_id={}", customerId);
        } catch (Exception e) {
            log.error("❌ 健康配置事件发布失败: customer_id={}, error={}", customerId, e.getMessage());
        }
    }
    
    /**
     * 从数据库加载启用的指标
     * @param customerId 租户ID
     * @return 启用的指标列表
     */
    private List<String> loadEnabledMetricsFromDB(Long customerId) {
        try {
            List<THealthDataConfig> configs = healthDataConfigService.getEnabledConfigsByCustomerId(customerId);
            
            return configs.stream()
                .map(THealthDataConfig::getDataType)
                .filter(dataType -> dataType != null && !dataType.trim().isEmpty())
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("❌ 查询健康配置失败: customer_id={}, error={}", customerId, e.getMessage());
            return List.of(); // 返回空列表而非null
        }
    }
    
    /**
     * 预热指定租户的缓存
     * @param customerId 租户ID
     */
    public void warmupCache(Long customerId) {
        log.info("🔥 开始预热健康配置缓存: customer_id={}", customerId);
        getEnabledMetrics(customerId); // 触发缓存加载
    }
    
    /**
     * 构建缓存键
     * @param customerId 租户ID
     * @param suffix 后缀
     * @return 缓存键
     */
    private String buildCacheKey(Long customerId, String suffix) {
        return HEALTH_CONFIG_CACHE_PREFIX + customerId + ":" + suffix;
    }
    
    /**
     * 获取缓存统计信息
     * @param customerId 租户ID
     * @return 缓存状态信息
     */
    public String getCacheStatus(Long customerId) {
        String cacheKey = buildCacheKey(customerId, ENABLED_METRICS_KEY);
        boolean exists = Boolean.TRUE.equals(redisTemplate.hasKey(cacheKey));
        Long ttl = redisTemplate.getExpire(cacheKey, TimeUnit.SECONDS);
        
        return String.format("customer_id=%d, cached=%s, ttl=%ds", customerId, exists, ttl != null ? ttl : -1);
    }
}