package com.ljwx.common.license;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.ljwx.common.api.Result;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.HashMap;
import java.util.Map;

/**
 * 许可证管理API
 * 提供许可证状态查询和硬件指纹生成功能
 */
@Slf4j
@RestController
@RequestMapping("/api/license")
public class LicenseController {

    @Autowired
    private LicenseManager licenseManager;
    
    @Autowired
    private HardwareFingerprintService fingerprintService;
    
    @Autowired
    private LicenseWarningService warningService;
    
    /**
     * 获取许可证状态
     */
    @GetMapping("/status")
    public Result<Map<String, Object>> getLicenseStatus() {
        try {
            Map<String, Object> status = new HashMap<>();
            
            LicenseInfo licenseInfo = licenseManager.getLicenseInfo();
            if (licenseInfo != null) {
                status.put("valid", licenseManager.isLicenseValid());
                status.put("customerName", licenseInfo.getCustomerName());  
                status.put("licenseType", licenseInfo.getLicenseType());
                status.put("startDate", licenseInfo.getStartDate());
                status.put("endDate", licenseInfo.getEndDate());
                status.put("remainingDays", licenseManager.getRemainingDays());
                status.put("maxUsers", licenseInfo.getMaxUsers());
                status.put("maxDevices", licenseInfo.getMaxDevices());
                status.put("features", licenseInfo.getFeatures());
            } else {
                status.put("valid", false);
                status.put("mode", "trial");
                status.put("message", "运行在试用模式");
            }
            
            return Result.data(status);
            
        } catch (Exception e) {
            log.error("获取许可证状态失败", e);
            return Result.failure("获取许可证状态失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取硬件指纹
     */
    @GetMapping("/fingerprint")
    public Result<Map<String, Object>> getHardwareFingerprint() {
        try {
            Map<String, Object> result = new HashMap<>();
            result.put("fingerprint", fingerprintService.generateFingerprint());
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("获取硬件指纹失败", e);
            return Result.failure("获取硬件指纹失败: " + e.getMessage());
        }
    }
    
    /**
     * 检查功能权限
     */
    @GetMapping("/feature/{feature}")
    public Result<Map<String, Object>> checkFeature(@PathVariable String feature) {
        try {
            boolean hasFeature = licenseManager.hasFeature(feature);
            long usageCount = licenseManager.getFeatureUsageCount(feature);
            
            Map<String, Object> result = new HashMap<>();
            result.put("feature", feature);
            result.put("allowed", hasFeature);
            result.put("usageCount", usageCount);
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("检查功能权限失败", e);
            return Result.failure("检查功能权限失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取使用统计
     */
    @GetMapping("/usage")
    public Result<Map<String, Object>> getUsageStats() {
        try {
            Map<String, Object> usage = new HashMap<>();
            
            // 获取各功能使用统计
            String[] features = {"user_login", "device_add", "health_data", "big_screen", "ai_analysis"};
            for (String feature : features) {
                usage.put(feature, licenseManager.getFeatureUsageCount(feature));
            }
            
            return Result.data(usage);
            
        } catch (Exception e) {
            log.error("获取使用统计失败", e);
            return Result.failure("获取使用统计失败: " + e.getMessage());
        }
    }
    
    /**
     * 验证硬件指纹
     */
    @PostMapping("/verify")
    public Result<Map<String, Object>> verifyFingerprint(@RequestBody Map<String, String> request) {
        try {
            String expectedFingerprint = request.get("fingerprint");
            if (expectedFingerprint == null || expectedFingerprint.isEmpty()) {
                return Result.failure("硬件指纹不能为空");
            }
            
            boolean matches = fingerprintService.verifyFingerprint(expectedFingerprint);
            
            Map<String, Object> result = new HashMap<>();
            result.put("matches", matches);
            result.put("currentFingerprint", fingerprintService.generateFingerprint());
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("验证硬件指纹失败", e);
            return Result.failure("验证硬件指纹失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取许可证预警信息
     */
    @GetMapping("/warning")
    public Result<LicenseWarningInfo> getLicenseWarning() {
        try {
            LicenseWarningInfo warningInfo = warningService.checkLicenseStatus();
            return Result.data(warningInfo);
            
        } catch (Exception e) {
            log.error("获取许可证预警信息失败", e);
            return Result.failure("获取许可证预警信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 上传新的许可证文件
     */
    @PostMapping("/upload")
    public Result<Map<String, Object>> uploadLicense(@RequestParam("file") MultipartFile file) {
        try {
            if (file.isEmpty()) {
                return Result.failure("许可证文件不能为空");
            }
            
            // 验证文件扩展名
            String originalFilename = file.getOriginalFilename();
            if (originalFilename == null || !originalFilename.endsWith(".lic")) {
                return Result.failure("许可证文件必须是.lic格式");
            }
            
            // 创建许可证目录
            String licenseDir = "./license";
            File dir = new File(licenseDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }
            
            // 备份现有许可证文件
            String currentLicensePath = licenseManager.getLicenseFilePath();
            File currentFile = new File(currentLicensePath);
            if (currentFile.exists()) {
                String backupPath = currentLicensePath + ".backup." + System.currentTimeMillis();
                Files.copy(currentFile.toPath(), Paths.get(backupPath), StandardCopyOption.REPLACE_EXISTING);
                log.info("已备份现有许可证文件到: {}", backupPath);
            }
            
            // 保存新许可证文件
            Path targetPath = Paths.get(currentLicensePath);
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
            
            // 重新加载许可证
            licenseManager.reloadLicense();
            
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("filename", originalFilename);
            result.put("size", file.getSize());
            result.put("uploadTime", System.currentTimeMillis());
            
            log.info("许可证文件上传成功: {}", originalFilename);
            return Result.data(result);
            
        } catch (IOException e) {
            log.error("上传许可证文件失败", e);
            return Result.failure("上传许可证文件失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("处理许可证文件失败", e);
            return Result.failure("处理许可证文件失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取许可证详细信息
     */
    @GetMapping("/info")
    public Result<LicenseInfo> getLicenseInfo() {
        try {
            LicenseInfo licenseInfo = licenseManager.getCurrentLicenseInfo();
            if (licenseInfo != null) {
                return Result.data(licenseInfo);
            } else {
                return Result.failure("许可证信息不可用");
            }
            
        } catch (Exception e) {
            log.error("获取许可证详细信息失败", e);
            return Result.failure("获取许可证详细信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 刷新许可证缓存
     */
    @PostMapping("/refresh")
    public Result<String> refreshLicense() {
        try {
            licenseManager.reloadLicense();
            return Result.success("许可证缓存刷新成功");
            
        } catch (Exception e) {
            log.error("刷新许可证缓存失败", e);
            return Result.failure("刷新许可证缓存失败: " + e.getMessage());
        }
    }
}