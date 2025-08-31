package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * 客户许可证集成服务
 * 与t_customer_config表的is_support_license字段集成
 */
@Slf4j
@Service
public class CustomerLicenseService {

    @Autowired
    private LicenseManager licenseManager;
    
    /**
     * 检查客户是否支持许可证功能
     * 结合系统许可证和客户配置进行双重验证
     */
    public boolean isCustomerLicenseEnabled(Long customerId, Boolean customerSupportLicense) {
        try {
            // 1. 首先检查系统级许可证是否启用
            if (!licenseManager.isLicenseEnabled()) {
                log.debug("系统许可证功能未启用，客户ID: {}", customerId);
                return false;
            }
            
            // 2. 检查系统许可证是否有效
            if (!licenseManager.isLicenseValid()) {
                log.warn("系统许可证无效，客户ID: {}", customerId);
                return false;
            }
            
            // 3. 检查客户配置是否支持许可证
            if (customerSupportLicense == null || !customerSupportLicense) {
                log.debug("客户配置不支持许可证，客户ID: {}", customerId);
                return false;
            }
            
            // 4. 检查许可证是否包含必要功能
            if (!licenseManager.hasFeature("user_management")) {
                log.warn("许可证不包含用户管理功能，客户ID: {}", customerId);
                return false;
            }
            
            return true;
            
        } catch (Exception e) {
            log.error("检查客户许可证状态异常，客户ID: {}", customerId, e);
            return false;
        }
    }
    
    /**
     * 验证客户操作权限
     * 在业务操作前进行权限检查
     */
    public boolean validateCustomerOperation(Long customerId, String operation, Boolean customerSupportLicense) {
        try {
            // 如果客户不支持许可证，允许基础操作
            if (!isCustomerLicenseEnabled(customerId, customerSupportLicense)) {
                return isBasicOperation(operation);
            }
            
            // 许可证启用时，检查具体功能权限
            return licenseManager.hasFeature(operation);
            
        } catch (Exception e) {
            log.error("验证客户操作权限异常，客户ID: {}, 操作: {}", customerId, operation, e);
            return false;
        }
    }
    
    /**
     * 记录客户功能使用
     */
    public void recordCustomerUsage(Long customerId, String feature, Boolean customerSupportLicense) {
        try {
            if (isCustomerLicenseEnabled(customerId, customerSupportLicense)) {
                licenseManager.recordFeatureUsage(feature);
                log.debug("记录客户功能使用，客户ID: {}, 功能: {}", customerId, feature);
            }
        } catch (Exception e) {
            log.error("记录客户功能使用异常，客户ID: {}, 功能: {}", customerId, feature, e);
        }
    }
    
    /**
     * 获取客户许可证状态信息
     */
    public CustomerLicenseStatus getCustomerLicenseStatus(Long customerId, Boolean customerSupportLicense) {
        try {
            CustomerLicenseStatus status = new CustomerLicenseStatus();
            status.setCustomerId(customerId);
            status.setCustomerSupportLicense(customerSupportLicense);
            status.setSystemLicenseEnabled(licenseManager.isLicenseEnabled());
            status.setSystemLicenseValid(licenseManager.isLicenseValid());
            status.setEffectiveLicenseEnabled(isCustomerLicenseEnabled(customerId, customerSupportLicense));
            
            if (licenseManager.isLicenseValid()) {
                LicenseInfo licenseInfo = licenseManager.getCurrentLicenseInfo();
                if (licenseInfo != null) {
                    status.setLicenseInfo(licenseInfo);
                    status.setRemainingDays(licenseManager.getRemainingDays());
                }
            }
            
            return status;
            
        } catch (Exception e) {
            log.error("获取客户许可证状态异常，客户ID: {}", customerId, e);
            return CustomerLicenseStatus.error(customerId, e.getMessage());
        }
    }
    
    /**
     * 判断是否为基础操作（无许可证时也允许）
     */
    private boolean isBasicOperation(String operation) {
        // 基础操作列表
        return operation.equals("basic_health") || 
               operation.equals("basic_query") ||
               operation.equals("system_info");
    }
}