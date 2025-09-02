package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

/**
 * 许可证配置类
 * 启用许可证控制功能
 */
@Slf4j
@Configuration
@EnableAspectJAutoProxy(proxyTargetClass = true)
@ConditionalOnProperty(name = "ljwx.license.enabled", havingValue = "true", matchIfMissing = true)
public class LicenseConfiguration {
    
    public LicenseConfiguration() {
        log.info("🔐 LJWX许可证控制系统已启用");
        log.info("📋 功能特性:");
        log.info("   - 硬件指纹绑定");
        log.info("   - 用户和设备数量限制");
        log.info("   - 功能模块权限控制");
        log.info("   - 使用情况统计和监控");
        log.info("   - 离线验证支持");
    }
}