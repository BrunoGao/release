package com.ljwx.common.license;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 许可证信息实体
 */
@Data
public class LicenseInfo {
    
    /**
     * 许可证ID
     */
    private String licenseId;
    
    /**
     * 客户名称
     */
    private String customerName;
    
    /**
     * 客户ID
     */
    private String customerId;
    
    /**
     * 许可证类型
     */
    private String licenseType;
    
    /**
     * 生效日期
     */
    private LocalDateTime startDate;
    
    /**
     * 过期日期
     */
    private LocalDateTime endDate;
    
    /**
     * 硬件指纹
     */
    private String hardwareFingerprint;
    
    /**
     * 最大用户数
     */
    private long maxUsers;
    
    /**
     * 最大设备数
     */
    private long maxDevices;
    
    /**
     * 最大组织数
     */
    private long maxOrganizations;
    
    /**
     * 允许的功能列表
     */
    private List<String> features;
    
    /**
     * 数字签名
     */
    private String signature;
    
    /**
     * 版本号
     */
    private String version;
    
    /**
     * 创建时间
     */
    private LocalDateTime createTime;
    
    /**
     * 备注信息
     */
    private String remarks;
    
    /**
     * 检查许可证是否过期
     */
    public boolean isExpired() {
        return LocalDateTime.now().isAfter(endDate);
    }
    
    /**
     * 检查许可证是否生效
     */
    public boolean isActive() {
        LocalDateTime now = LocalDateTime.now();
        return now.isAfter(startDate) && now.isBefore(endDate);
    }
    
    /**
     * 获取剩余天数
     */
    public long getRemainingDays() {
        if (isExpired()) {
            return 0;
        }
        return java.time.Duration.between(LocalDateTime.now(), endDate).toDays();
    }
    
    /**
     * 检查是否包含指定功能
     */
    public boolean hasFeature(String feature) {
        return features != null && features.contains(feature);
    }
    
    // 兼容性方法别名
    public String getCustomer() {
        return customerName;
    }
    
    public LocalDateTime getIssueDate() {
        return startDate;
    }
    
    public LocalDateTime getExpirationDate() {
        return endDate;
    }
}