package com.ljwx.common.license;

import lombok.Data;

/**
 * 客户许可证状态信息
 */
@Data
public class CustomerLicenseStatus {
    
    /**
     * 客户ID
     */
    private Long customerId;
    
    /**
     * 客户配置是否支持许可证
     */
    private Boolean customerSupportLicense;
    
    /**
     * 系统许可证功能是否启用
     */
    private Boolean systemLicenseEnabled;
    
    /**
     * 系统许可证是否有效
     */
    private Boolean systemLicenseValid;
    
    /**
     * 有效的许可证状态（综合判断结果）
     */
    private Boolean effectiveLicenseEnabled;
    
    /**
     * 许可证详细信息
     */
    private LicenseInfo licenseInfo;
    
    /**
     * 剩余天数
     */
    private Long remainingDays;
    
    /**
     * 状态信息
     */
    private String message;
    
    /**
     * 错误信息
     */
    private String error;
    
    /**
     * 创建错误状态
     */
    public static CustomerLicenseStatus error(Long customerId, String error) {
        CustomerLicenseStatus status = new CustomerLicenseStatus();
        status.setCustomerId(customerId);
        status.setError(error);
        status.setEffectiveLicenseEnabled(false);
        return status;
    }
}