package com.ljwx.modules.health.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ljwx.modules.health.entity.HealthBaseline;
import com.ljwx.modules.health.service.HealthProfileService.ComprehensiveHealthProfile;
import com.ljwx.modules.health.service.HealthScoreCalculationService.HealthScoreDetail;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDate;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * 健康数据缓存服务
 * 实现Redis缓存优化，提升系统性能
 */
@Slf4j
@Service
public class HealthDataCacheService {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    // 缓存TTL配置
    private static final int HEALTH_SUMMARY_TTL = 3600; // 1小时
    private static final int BASELINE_DATA_TTL = 7200; // 2小时
    private static final int SCORE_DATA_TTL = 1800; // 30分钟
    private static final int PROFILE_DATA_TTL = 3600; // 1小时
    private static final int TREND_DATA_TTL = 14400; // 4小时

    /**
     * 获取用户健康摘要缓存
     */
    public String getUserHealthSummary(Long userId) {
        String cacheKey = buildCacheKey("health_summary", userId);
        try {
            return redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.warn("获取健康摘要缓存失败: userId={}, error={}", userId, e.getMessage());
            return null;
        }
    }

    /**
     * 设置用户健康摘要缓存
     */
    public void setUserHealthSummary(Long userId, Object healthSummary) {
        String cacheKey = buildCacheKey("health_summary", userId);
        try {
            String jsonValue = objectMapper.writeValueAsString(healthSummary);
            redisTemplate.opsForValue().set(cacheKey, jsonValue, HEALTH_SUMMARY_TTL, TimeUnit.SECONDS);
            log.debug("设置健康摘要缓存成功: userId={}", userId);
        } catch (Exception e) {
            log.error("设置健康摘要缓存失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    /**
     * 获取用户基线数据缓存
     */
    public String getUserBaseline(Long userId, String metric) {
        String cacheKey = buildCacheKey("health_baseline", userId, metric);
        try {
            return redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.warn("获取基线数据缓存失败: userId={}, metric={}, error={}", userId, metric, e.getMessage());
            return null;
        }
    }

    /**
     * 设置用户基线数据缓存
     */
    public void setUserBaseline(Long userId, String metric, HealthBaseline baseline) {
        String cacheKey = buildCacheKey("health_baseline", userId, metric);
        try {
            String jsonValue = objectMapper.writeValueAsString(baseline);
            redisTemplate.opsForValue().set(cacheKey, jsonValue, BASELINE_DATA_TTL, TimeUnit.SECONDS);
            log.debug("设置基线数据缓存成功: userId={}, metric={}", userId, metric);
        } catch (Exception e) {
            log.error("设置基线数据缓存失败: userId={}, metric={}, error={}", userId, metric, e.getMessage());
        }
    }

    /**
     * 获取用户健康评分缓存
     */
    public String getUserHealthScore(Long userId) {
        String cacheKey = buildCacheKey("health_score", userId, LocalDate.now().toString());
        try {
            return redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.warn("获取健康评分缓存失败: userId={}, error={}", userId, e.getMessage());
            return null;
        }
    }

    /**
     * 设置用户健康评分缓存
     */
    public void setUserHealthScore(Long userId, HealthScoreDetail scoreDetail) {
        String cacheKey = buildCacheKey("health_score", userId, LocalDate.now().toString());
        try {
            String jsonValue = objectMapper.writeValueAsString(scoreDetail);
            redisTemplate.opsForValue().set(cacheKey, jsonValue, SCORE_DATA_TTL, TimeUnit.SECONDS);
            log.debug("设置健康评分缓存成功: userId={}", userId);
        } catch (Exception e) {
            log.error("设置健康评分缓存失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    /**
     * 获取用户健康画像缓存
     */
    public String getUserHealthProfile(Long userId) {
        String cacheKey = buildCacheKey("health_profile", userId, LocalDate.now().toString());
        try {
            return redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.warn("获取健康画像缓存失败: userId={}, error={}", userId, e.getMessage());
            return null;
        }
    }

    /**
     * 设置用户健康画像缓存
     */
    public void setUserHealthProfile(Long userId, ComprehensiveHealthProfile profile) {
        String cacheKey = buildCacheKey("health_profile", userId, LocalDate.now().toString());
        try {
            String jsonValue = objectMapper.writeValueAsString(profile);
            redisTemplate.opsForValue().set(cacheKey, jsonValue, PROFILE_DATA_TTL, TimeUnit.SECONDS);
            log.debug("设置健康画像缓存成功: userId={}", userId);
        } catch (Exception e) {
            log.error("设置健康画像缓存失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    /**
     * 获取健康趋势分析缓存
     */
    public String getHealthTrends(Long userId, int days) {
        String cacheKey = buildCacheKey("health_trends", userId, String.valueOf(days));
        try {
            return redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.warn("获取健康趋势缓存失败: userId={}, days={}, error={}", userId, days, e.getMessage());
            return null;
        }
    }

    /**
     * 设置健康趋势分析缓存
     */
    public void setHealthTrends(Long userId, int days, Object trendsData) {
        String cacheKey = buildCacheKey("health_trends", userId, String.valueOf(days));
        try {
            String jsonValue = objectMapper.writeValueAsString(trendsData);
            redisTemplate.opsForValue().set(cacheKey, jsonValue, TREND_DATA_TTL, TimeUnit.SECONDS);
            log.debug("设置健康趋势缓存成功: userId={}, days={}", userId, days);
        } catch (Exception e) {
            log.error("设置健康趋势缓存失败: userId={}, days={}, error={}", userId, days, e.getMessage());
        }
    }

    /**
     * 清除用户相关的所有缓存
     */
    public void invalidateUserCache(Long userId) {
        try {
            // 构建所有可能的缓存键模式
            String[] patterns = {
                buildCacheKey("health_summary", userId),
                buildCacheKey("health_baseline", userId, "*"),
                buildCacheKey("health_score", userId, "*"),
                buildCacheKey("health_profile", userId, "*"),
                buildCacheKey("health_trends", userId, "*")
            };
            
            for (String pattern : patterns) {
                // 对于带通配符的模式，需要先查找匹配的键
                if (pattern.contains("*")) {
                    var keys = redisTemplate.keys(pattern);
                    if (keys != null && !keys.isEmpty()) {
                        redisTemplate.delete(keys);
                        log.debug("清除缓存键: {}", keys);
                    }
                } else {
                    // 直接删除精确匹配的键
                    Boolean deleted = redisTemplate.delete(pattern);
                    if (Boolean.TRUE.equals(deleted)) {
                        log.debug("清除缓存键: {}", pattern);
                    }
                }
            }
            
            log.info("用户{}的所有健康数据缓存已清除", userId);
            
        } catch (Exception e) {
            log.error("清除用户缓存失败: userId={}, error={}", userId, e.getMessage());
        }
    }

    /**
     * 批量清除缓存
     */
    public void batchInvalidateCache(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return;
        }
        
        try {
            log.info("开始批量清除{}个用户的缓存", userIds.size());
            
            for (Long userId : userIds) {
                invalidateUserCache(userId);
            }
            
            log.info("批量清除缓存完成");
            
        } catch (Exception e) {
            log.error("批量清除缓存失败: error={}", e.getMessage());
        }
    }

    /**
     * 获取缓存统计信息
     */
    public CacheStatistics getCacheStatistics() {
        try {
            CacheStatistics stats = new CacheStatistics();
            
            // 统计各类型缓存数量
            stats.setHealthSummaryCount(countCacheKeys("health_summary:*"));
            stats.setBaselineCount(countCacheKeys("health_baseline:*"));
            stats.setScoreCount(countCacheKeys("health_score:*"));
            stats.setProfileCount(countCacheKeys("health_profile:*"));
            stats.setTrendsCount(countCacheKeys("health_trends:*"));
            
            // 计算总计
            int totalCount = stats.getHealthSummaryCount() + stats.getBaselineCount() + 
                           stats.getScoreCount() + stats.getProfileCount() + stats.getTrendsCount();
            stats.setTotalCount(totalCount);
            
            // 获取Redis内存使用情况
            try {
                String memoryInfo = redisTemplate.getConnectionFactory().getConnection().info("memory").toString();
                // 解析内存使用信息（简化处理）
                stats.setMemoryUsage("Memory info available in Redis INFO");
            } catch (Exception e) {
                stats.setMemoryUsage("Memory info not available");
            }
            
            log.info("缓存统计: 总计={}, 摘要={}, 基线={}, 评分={}, 画像={}, 趋势={}", 
                totalCount, stats.getHealthSummaryCount(), stats.getBaselineCount(),
                stats.getScoreCount(), stats.getProfileCount(), stats.getTrendsCount());
            
            return stats;
            
        } catch (Exception e) {
            log.error("获取缓存统计信息失败: error={}", e.getMessage());
            return new CacheStatistics();
        }
    }

    /**
     * 预热缓存
     */
    public void warmupCache(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return;
        }
        
        log.info("开始预热{}个用户的缓存", userIds.size());
        
        try {
            for (Long userId : userIds) {
                // 这里可以预先加载常用数据到缓存
                // 例如用户基本健康摘要等
                log.debug("预热用户{}的缓存", userId);
            }
            
            log.info("缓存预热完成");
            
        } catch (Exception e) {
            log.error("缓存预热失败: error={}", e.getMessage());
        }
    }

    /**
     * 清理过期缓存
     */
    public void cleanExpiredCache() {
        try {
            log.info("开始清理过期缓存");
            
            // Redis会自动清理过期键，这里主要做一些手动清理逻辑
            // 比如清理某些业务逻辑过期的数据
            
            log.info("过期缓存清理完成");
            
        } catch (Exception e) {
            log.error("清理过期缓存失败: error={}", e.getMessage());
        }
    }

    // 私有辅助方法

    /**
     * 构建缓存键
     */
    private String buildCacheKey(String prefix, Object... parts) {
        StringBuilder sb = new StringBuilder("health:");
        sb.append(prefix);
        
        for (Object part : parts) {
            sb.append(":").append(part);
        }
        
        return sb.toString();
    }

    /**
     * 统计匹配模式的缓存键数量
     */
    private int countCacheKeys(String pattern) {
        try {
            var keys = redisTemplate.keys(pattern);
            return keys != null ? keys.size() : 0;
        } catch (Exception e) {
            log.warn("统计缓存键数量失败: pattern={}, error={}", pattern, e.getMessage());
            return 0;
        }
    }

    /**
     * 解析JSON字符串为对象
     */
    public <T> T parseJsonToObject(String json, Class<T> clazz) {
        try {
            return objectMapper.readValue(json, clazz);
        } catch (JsonProcessingException e) {
            log.error("解析JSON失败: json={}, class={}, error={}", json, clazz.getSimpleName(), e.getMessage());
            return null;
        }
    }

    /**
     * 缓存统计信息内部类
     */
    public static class CacheStatistics {
        private int totalCount;
        private int healthSummaryCount;
        private int baselineCount;
        private int scoreCount;
        private int profileCount;
        private int trendsCount;
        private String memoryUsage;
        private long timestamp = System.currentTimeMillis();

        // Getters and Setters
        public int getTotalCount() { return totalCount; }
        public void setTotalCount(int totalCount) { this.totalCount = totalCount; }
        
        public int getHealthSummaryCount() { return healthSummaryCount; }
        public void setHealthSummaryCount(int healthSummaryCount) { this.healthSummaryCount = healthSummaryCount; }
        
        public int getBaselineCount() { return baselineCount; }
        public void setBaselineCount(int baselineCount) { this.baselineCount = baselineCount; }
        
        public int getScoreCount() { return scoreCount; }
        public void setScoreCount(int scoreCount) { this.scoreCount = scoreCount; }
        
        public int getProfileCount() { return profileCount; }
        public void setProfileCount(int profileCount) { this.profileCount = profileCount; }
        
        public int getTrendsCount() { return trendsCount; }
        public void setTrendsCount(int trendsCount) { this.trendsCount = trendsCount; }
        
        public String getMemoryUsage() { return memoryUsage; }
        public void setMemoryUsage(String memoryUsage) { this.memoryUsage = memoryUsage; }
        
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }
}