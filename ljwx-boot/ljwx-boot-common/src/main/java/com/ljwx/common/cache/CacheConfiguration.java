package com.ljwx.common.cache;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 缓存配置类
 * 启用异步和定时任务支持
 */
@Slf4j
@Configuration
@EnableAsync
@EnableScheduling
@EnableAspectJAutoProxy(proxyTargetClass = true)
@ConditionalOnProperty(name = "ljwx.cache.enabled", havingValue = "true", matchIfMissing = true)
public class CacheConfiguration {
    
    public CacheConfiguration() {
        log.info("🚀 Redis缓存高性能查询服务已启用");
        log.info("📊 支持的功能:");
        log.info("   - 租户级别查询优化");
        log.info("   - 用户-部门关联查询优化");
        log.info("   - 用户-设备关联查询优化"); 
        log.info("   - 部门-设备关联查询优化");
        log.info("   - 业务数据缓存优化");
        log.info("   - 自动缓存预热和定时刷新");
        log.info("   - 批量查询性能优化");
    }
}