package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.concurrent.TimeUnit;

/**
 * 许可证预警服务
 * 提前7天开始每日预警
 */
@Slf4j
@Service
public class LicenseWarningService {

    @Autowired
    private LicenseManager licenseManager;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    private static final String WARNING_CACHE_KEY = "license:warning:sent:";
    private static final int WARNING_DAYS = 7; // 提前7天预警
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    
    /**
     * 每日定时检查许可证到期预警
     * 每天凌晨1点执行
     */
    @Scheduled(cron = "0 0 1 * * ?")
    public void checkLicenseExpiration() {
        try {
            if (!licenseManager.isLicenseEnabled()) {
                log.debug("许可证功能未启用，跳过预警检查");
                return;
            }
            
            LicenseInfo licenseInfo = licenseManager.getCurrentLicenseInfo();
            if (licenseInfo == null) {
                log.warn("许可证信息不可用，无法进行预警检查");
                return;
            }
            
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime expirationDate = licenseInfo.getExpirationDate();
            
            if (expirationDate == null) {
                log.warn("许可证无过期时间，跳过预警检查");
                return;
            }
            
            // 计算距离过期的天数
            long daysUntilExpiration = ChronoUnit.DAYS.between(now, expirationDate);
            
            // 检查是否需要预警
            if (daysUntilExpiration <= WARNING_DAYS && daysUntilExpiration >= 0) {
                String today = now.format(DATE_FORMATTER);
                String warningKey = WARNING_CACHE_KEY + today;
                
                // 检查今天是否已发送预警
                if (!Boolean.TRUE.equals(redisTemplate.hasKey(warningKey))) {
                    sendLicenseWarning(licenseInfo, daysUntilExpiration);
                    // 标记今天已发送预警，缓存到第二天凌晨2点
                    redisTemplate.opsForValue().set(warningKey, true, 25, TimeUnit.HOURS);
                }
            } else if (daysUntilExpiration < 0) {
                // 许可证已过期
                log.error("许可证已过期 {} 天", Math.abs(daysUntilExpiration));
                sendLicenseExpiredAlert(licenseInfo, Math.abs(daysUntilExpiration));
            }
            
        } catch (Exception e) {
            log.error("许可证预警检查异常", e);
        }
    }
    
    /**
     * 发送许可证预警通知
     */
    private void sendLicenseWarning(LicenseInfo licenseInfo, long daysUntilExpiration) {
        try {
            String message = String.format(
                "⚠️ 许可证到期预警\n" +
                "许可证ID: %s\n" +
                "客户: %s\n" +
                "剩余天数: %d 天\n" +
                "到期时间: %s\n" +
                "请及时续期以避免服务中断",
                licenseInfo.getLicenseId(),
                licenseInfo.getCustomer(),
                daysUntilExpiration,
                licenseInfo.getExpirationDate().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
            );
            
            log.warn("许可证预警: {}", message);
            
            // 存储预警记录到Redis
            String alertKey = "license:alert:warning:" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            redisTemplate.opsForHash().put(alertKey, "type", "WARNING");
            redisTemplate.opsForHash().put(alertKey, "message", message);
            redisTemplate.opsForHash().put(alertKey, "daysLeft", daysUntilExpiration);
            redisTemplate.opsForHash().put(alertKey, "timestamp", LocalDateTime.now().toString());
            redisTemplate.expire(alertKey, 30, TimeUnit.DAYS);
            
            // 发送系统通知（可扩展集成邮件、短信等）
            sendSystemNotification("LICENSE_WARNING", message);
            
        } catch (Exception e) {
            log.error("发送许可证预警失败", e);
        }
    }
    
    /**
     * 发送许可证过期通知
     */
    private void sendLicenseExpiredAlert(LicenseInfo licenseInfo, long daysExpired) {
        try {
            String message = String.format(
                "🚨 许可证已过期\n" +
                "许可证ID: %s\n" +
                "客户: %s\n" +
                "已过期: %d 天\n" +
                "过期时间: %s\n" +
                "系统功能已受限，请立即续期",
                licenseInfo.getLicenseId(),
                licenseInfo.getCustomer(),
                daysExpired,
                licenseInfo.getExpirationDate().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
            );
            
            log.error("许可证已过期: {}", message);
            
            // 存储过期记录到Redis
            String alertKey = "license:alert:expired:" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
            redisTemplate.opsForHash().put(alertKey, "type", "EXPIRED");
            redisTemplate.opsForHash().put(alertKey, "message", message);
            redisTemplate.opsForHash().put(alertKey, "daysExpired", daysExpired);
            redisTemplate.opsForHash().put(alertKey, "timestamp", LocalDateTime.now().toString());
            redisTemplate.expire(alertKey, 90, TimeUnit.DAYS);
            
            // 发送紧急通知
            sendSystemNotification("LICENSE_EXPIRED", message);
            
        } catch (Exception e) {
            log.error("发送许可证过期通知失败", e);
        }
    }
    
    /**
     * 手动检查许可证状态
     */
    public LicenseWarningInfo checkLicenseStatus() {
        try {
            if (!licenseManager.isLicenseEnabled()) {
                return LicenseWarningInfo.builder()
                    .status("DISABLED")
                    .message("许可证功能未启用")
                    .build();
            }
            
            LicenseInfo licenseInfo = licenseManager.getCurrentLicenseInfo();
            if (licenseInfo == null) {
                return LicenseWarningInfo.builder()
                    .status("INVALID")
                    .message("许可证信息不可用")
                    .build();
            }
            
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime expirationDate = licenseInfo.getExpirationDate();
            
            if (expirationDate == null) {
                return LicenseWarningInfo.builder()
                    .status("NO_EXPIRATION")
                    .message("许可证无过期时间")
                    .licenseInfo(licenseInfo)
                    .build();
            }
            
            long daysUntilExpiration = ChronoUnit.DAYS.between(now, expirationDate);
            
            if (daysUntilExpiration < 0) {
                return LicenseWarningInfo.builder()
                    .status("EXPIRED")
                    .message(String.format("许可证已过期 %d 天", Math.abs(daysUntilExpiration)))
                    .daysLeft(daysUntilExpiration)
                    .licenseInfo(licenseInfo)
                    .build();
            } else if (daysUntilExpiration <= WARNING_DAYS) {
                return LicenseWarningInfo.builder()
                    .status("WARNING")
                    .message(String.format("许可证将在 %d 天后过期", daysUntilExpiration))
                    .daysLeft(daysUntilExpiration)
                    .licenseInfo(licenseInfo)
                    .build();
            } else {
                return LicenseWarningInfo.builder()
                    .status("VALID")
                    .message(String.format("许可证正常，剩余 %d 天", daysUntilExpiration))
                    .daysLeft(daysUntilExpiration)
                    .licenseInfo(licenseInfo)
                    .build();
            }
            
        } catch (Exception e) {
            log.error("检查许可证状态异常", e);
            return LicenseWarningInfo.builder()
                .status("ERROR")
                .message("检查许可证状态时发生异常: " + e.getMessage())
                .build();
        }
    }
    
    /**
     * 发送系统通知
     */
    private void sendSystemNotification(String type, String message) {
        try {
            // 可以在这里集成邮件、短信、WebSocket推送等通知方式
            log.info("发送系统通知 [{}]: {}", type, message);
            
            // 存储到Redis供前端查询
            String notificationKey = "license:notification:" + type.toLowerCase();
            redisTemplate.opsForValue().set(notificationKey, message, 7, TimeUnit.DAYS);
            
        } catch (Exception e) {
            log.error("发送系统通知失败", e);
        }
    }
}