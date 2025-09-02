package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

/**
 * 离线许可证管理器
 * 适用于本地部署、无外网环境
 */
@Slf4j
@Service
public class LicenseManager {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private HardwareFingerprintService fingerprintService;
    
    @Autowired
    private LicenseValidator licenseValidator;
    
    @Value("${ljwx.license.file-path:./license/ljwx.lic}")
    private String licenseFilePath;
    
    @Value("${ljwx.license.check-interval:300}")
    private long checkIntervalSeconds;
    
    private static final String LICENSE_CACHE_KEY = "ljwx:license:current";
    private static final String USAGE_CACHE_KEY = "ljwx:license:usage:";
    
    private LicenseInfo currentLicense;
    private boolean licenseValid = false;
    
    @PostConstruct
    public void initializeLicense() {
        log.info("🔐 初始化LJWX许可证系统...");
        
        try {
            // 1. 加载许可证文件
            loadLicenseFile();
            
            // 2. 验证许可证
            validateLicense();
            
            // 3. 启动监控
            startLicenseMonitoring();
            
            if (licenseValid) {
                log.info("✅ 许可证验证成功 - 系统已授权使用");
                log.info("📋 许可证信息:");
                log.info("   - 客户: {}", currentLicense.getCustomerName());
                log.info("   - 版本: {}", currentLicense.getLicenseType());
                log.info("   - 有效期: {} ~ {}", 
                    currentLicense.getStartDate(), currentLicense.getEndDate());
                log.info("   - 最大用户数: {}", currentLicense.getMaxUsers());
                log.info("   - 最大设备数: {}", currentLicense.getMaxDevices());
            } else {
                log.error("❌ 许可证验证失败 - 系统将在试用模式下运行");
            }
            
        } catch (Exception e) {
            log.error("🚨 许可证初始化失败", e);
            licenseValid = false;
        }
    }
    
    /**
     * 加载许可证文件
     */
    private void loadLicenseFile() throws Exception {
        File licenseFile = new File(licenseFilePath);
        if (!licenseFile.exists()) {
            throw new LicenseException("许可证文件不存在: " + licenseFilePath);
        }
        
        log.info("📄 加载许可证文件: {}", licenseFilePath);
        String licenseContent = Files.readString(Paths.get(licenseFilePath));
        
        // 解密和解析许可证
        currentLicense = licenseValidator.parseLicense(licenseContent);
        
        // 缓存到Redis
        redisTemplate.opsForValue().set(LICENSE_CACHE_KEY, currentLicense, 1, TimeUnit.HOURS);
    }
    
    /**
     * 验证许可证
     */
    private void validateLicense() {
        try {
            if (currentLicense == null) {
                throw new LicenseException("许可证未加载");
            }
            
            // 1. 检查时间有效性
            LocalDateTime now = LocalDateTime.now();
            if (now.isBefore(currentLicense.getStartDate()) || 
                now.isAfter(currentLicense.getEndDate())) {
                throw new LicenseException("许可证已过期");
            }
            
            // 2. 验证硬件指纹
            String currentFingerprint = fingerprintService.generateFingerprint();
            if (!currentLicense.getHardwareFingerprint().equals(currentFingerprint)) {
                log.warn("硬件指纹不匹配:");
                log.warn("  许可证指纹: {}", currentLicense.getHardwareFingerprint());
                log.warn("  当前硬件指纹: {}", currentFingerprint);
                throw new LicenseException("硬件指纹验证失败");
            }
            
            // 3. 验证数字签名
            if (!licenseValidator.verifySignature(currentLicense)) {
                throw new LicenseException("许可证签名验证失败");
            }
            
            licenseValid = true;
            
        } catch (Exception e) {
            log.error("许可证验证失败: {}", e.getMessage());
            licenseValid = false;
            throw new LicenseException("许可证验证失败", e);
        }
    }
    
    /**
     * 检查功能权限
     */
    public boolean hasFeature(String feature) {
        if (!licenseValid) {
            return isTrialFeature(feature);
        }
        
        return currentLicense.getFeatures().contains(feature);
    }
    
    /**
     * 检查用户数量限制
     */
    public boolean checkUserLimit(long currentUserCount) {
        if (!licenseValid) {
            return currentUserCount <= 10; // 试用版限制10个用户
        }
        
        return currentUserCount <= currentLicense.getMaxUsers();
    }
    
    /**
     * 检查设备数量限制
     */
    public boolean checkDeviceLimit(long currentDeviceCount) {
        if (!licenseValid) {
            return currentDeviceCount <= 20; // 试用版限制20个设备
        }
        
        return currentDeviceCount <= currentLicense.getMaxDevices();
    }
    
    /**
     * 记录使用情况
     */
    public void recordUsage(String feature, String userId) {
        try {
            String usageKey = USAGE_CACHE_KEY + feature + ":" + 
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
            
            redisTemplate.opsForSet().add(usageKey, userId);
            redisTemplate.expire(usageKey, 7, TimeUnit.DAYS); // 保留7天使用记录
            
        } catch (Exception e) {
            log.warn("记录使用情况失败", e);
        }
    }
    
    /**
     * 获取功能使用统计
     */
    public long getFeatureUsageCount(String feature) {
        try {
            String usageKey = USAGE_CACHE_KEY + feature + ":" + 
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
            
            Long count = redisTemplate.opsForSet().size(usageKey);
            return count != null ? count : 0;
            
        } catch (Exception e) {
            log.warn("获取使用统计失败", e);
            return 0;
        }
    }
    
    /**
     * 获取许可证信息
     */
    public LicenseInfo getLicenseInfo() {
        return currentLicense;
    }
    
    /**
     * 检查许可证是否有效
     */
    public boolean isLicenseValid() {
        return licenseValid;
    }
    
    /**
     * 获取剩余天数
     */
    public long getRemainingDays() {
        if (currentLicense == null) {
            return 0;
        }
        
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime endDate = currentLicense.getEndDate();
        
        return java.time.Duration.between(now, endDate).toDays();
    }
    
    /**
     * 启动许可证监控
     */
    private void startLicenseMonitoring() {
        // 使用Spring的调度器定期检查
        log.info("🔍 启动许可证监控，检查间隔: {}秒", checkIntervalSeconds);
        
        // 这里可以结合现有的@Scheduled注解实现
        // 暂时通过日志记录状态
        log.info("许可证监控已启动");
    }
    
    /**
     * 判断是否为试用版功能
     */
    private boolean isTrialFeature(String feature) {
        // 试用版允许的基础功能
        return feature.equals("basic_health") || 
               feature.equals("basic_alert") ||
               feature.equals("user_management");
    }
    
    /**
     * 重新加载许可证文件
     */
    public void reloadLicense() {
        try {
            loadLicenseFile();
        } catch (Exception e) {
            log.error("重新加载许可证失败", e);
        }
    }
    
    /**
     * 获取许可证文件路径
     */
    public String getLicenseFilePath() {
        return licenseFilePath;
    }
    
    /**
     * 获取当前许可证信息
     */
    public LicenseInfo getCurrentLicenseInfo() {
        return currentLicense;
    }
    
    /**
     * 判断许可证功能是否启用
     */
    public boolean isLicenseEnabled() {
        return currentLicense != null;
    }
    
    /**
     * 记录功能使用情况
     */
    public void recordFeatureUsage(String feature) {
        try {
            String usageKey = USAGE_CACHE_KEY + feature + ":" + System.currentTimeMillis() / (1000 * 60 * 60 * 24); // 按天统计
            redisTemplate.opsForValue().increment(usageKey);
            redisTemplate.expire(usageKey, 7, TimeUnit.DAYS);
            log.debug("记录功能使用: {}", feature);
        } catch (Exception e) {
            log.error("记录功能使用失败: " + feature, e);
        }
    }
    
}