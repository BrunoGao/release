package com.ljwx.common.license;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 许可证预警信息
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LicenseWarningInfo {
    
    /**
     * 许可证状态
     * VALID: 正常
     * WARNING: 预警（7天内到期）
     * EXPIRED: 已过期
     * INVALID: 无效
     * DISABLED: 未启用
     * ERROR: 检查异常
     */
    private String status;
    
    /**
     * 状态描述信息
     */
    private String message;
    
    /**
     * 剩余天数（负数表示已过期天数）
     */
    private Long daysLeft;
    
    /**
     * 许可证详细信息
     */
    private LicenseInfo licenseInfo;
}