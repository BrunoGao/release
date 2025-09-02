package com.ljwx.common.license;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.io.FileWriter;
import java.io.IOException;
import java.security.*;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Base64;
import java.util.List;
import java.util.Scanner;

/**
 * 许可证生成工具
 * 用于生成加密的许可证文件
 */
public class LicenseGenerator {
    
    private static final String RSA_ALGORITHM = "RSA";
    private static final int KEY_SIZE = 2048;
    
    private final ObjectMapper objectMapper;
    private final LicenseValidator licenseValidator;
    
    public LicenseGenerator() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.licenseValidator = new LicenseValidator();
    }
    
    public static void main(String[] args) {
        LicenseGenerator generator = new LicenseGenerator();
        Scanner scanner = new Scanner(System.in);
        
        try {
            System.out.println("=== LJWX 许可证生成工具 ===");
            System.out.println();
            
            // 1. 生成密钥对
            System.out.println("1. 生成RSA密钥对...");
            KeyPair keyPair = generator.generateKeyPair();
            System.out.println("✅ 密钥对生成成功");
            System.out.println();
            
            // 2. 获取硬件指纹
            System.out.print("请输入目标硬件指纹 (留空则提供示例): ");
            String hardwareFingerprint = scanner.nextLine().trim();
            if (hardwareFingerprint.isEmpty()) {
                // 这里可以提供一个示例指纹或者工具来生成
                hardwareFingerprint = "SAMPLE_" + System.currentTimeMillis();
                System.out.println("使用示例硬件指纹: " + hardwareFingerprint);
            }
            System.out.println();
            
            // 3. 创建许可证信息
            LicenseInfo licenseInfo = generator.createLicenseInfo(scanner, hardwareFingerprint);
            
            // 4. 生成许可证文件
            System.out.println("4. 生成许可证文件...");
            String licenseContent = generator.licenseValidator.generateLicense(licenseInfo, keyPair.getPrivate());
            
            // 5. 保存文件
            String fileName = "ljwx_" + licenseInfo.getCustomerId() + "_" + 
                             licenseInfo.getLicenseType() + ".lic";
            generator.saveLicenseFile(fileName, licenseContent);
            
            // 6. 保存公钥
            generator.savePublicKey("public_key.pem", keyPair.getPublic());
            
            System.out.println("✅ 许可证生成完成!");
            System.out.println("许可证文件: " + fileName);
            System.out.println("公钥文件: public_key.pem");
            System.out.println();
            System.out.println("请将公钥嵌入到应用程序中，将许可证文件交付给客户。");
            
        } catch (Exception e) {
            System.err.println("❌ 许可证生成失败: " + e.getMessage());
            e.printStackTrace();
        } finally {
            scanner.close();
        }
    }
    
    /**
     * 生成密钥对
     */
    private KeyPair generateKeyPair() throws NoSuchAlgorithmException {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance(RSA_ALGORITHM);
        keyGen.initialize(KEY_SIZE);
        return keyGen.generateKeyPair();
    }
    
    /**
     * 创建许可证信息
     */
    private LicenseInfo createLicenseInfo(Scanner scanner, String hardwareFingerprint) {
        System.out.println("2. 配置许可证信息:");
        
        LicenseInfo license = new LicenseInfo();
        
        // 基本信息
        System.out.print("客户名称: ");
        license.setCustomerName(scanner.nextLine().trim());
        
        System.out.print("客户ID: ");
        license.setCustomerId(scanner.nextLine().trim());
        
        // 许可证类型
        System.out.println("许可证类型:");
        System.out.println("1. trial (试用版)");
        System.out.println("2. standard (标准版)");
        System.out.println("3. professional (专业版)");
        System.out.println("4. enterprise (企业版)");
        System.out.print("请选择 (1-4): ");
        
        int typeChoice = Integer.parseInt(scanner.nextLine().trim());
        String[] types = {"trial", "standard", "professional", "enterprise"};
        license.setLicenseType(types[typeChoice - 1]);
        
        // 时间设置
        System.out.print("有效期开始日期 (YYYY-MM-DD, 留空为今天): ");
        String startDateStr = scanner.nextLine().trim();
        LocalDateTime startDate = startDateStr.isEmpty() ? 
            LocalDateTime.now() : LocalDateTime.parse(startDateStr + "T00:00:00");
        license.setStartDate(startDate);
        
        System.out.print("有效期结束日期 (YYYY-MM-DD): ");
        String endDateStr = scanner.nextLine().trim();
        LocalDateTime endDate = LocalDateTime.parse(endDateStr + "T23:59:59");
        license.setEndDate(endDate);
        
        // 数量限制
        System.out.print("最大用户数: ");
        license.setMaxUsers(Long.parseLong(scanner.nextLine().trim()));
        
        System.out.print("最大设备数: ");
        license.setMaxDevices(Long.parseLong(scanner.nextLine().trim()));
        
        System.out.print("最大组织数: ");
        license.setMaxOrganizations(Long.parseLong(scanner.nextLine().trim()));
        
        // 功能设置
        List<String> features = getFeaturesForType(license.getLicenseType());
        license.setFeatures(features);
        
        // 其他信息
        license.setLicenseId("LIC_" + System.currentTimeMillis());
        license.setHardwareFingerprint(hardwareFingerprint);
        license.setVersion("1.0");
        license.setCreateTime(LocalDateTime.now());
        
        System.out.print("备注信息 (可选): ");
        license.setRemarks(scanner.nextLine().trim());
        
        System.out.println();
        System.out.println("3. 许可证信息确认:");
        System.out.println("客户: " + license.getCustomerName());
        System.out.println("类型: " + license.getLicenseType());
        System.out.println("有效期: " + license.getStartDate().toLocalDate() + " ~ " + license.getEndDate().toLocalDate());
        System.out.println("用户数: " + license.getMaxUsers());
        System.out.println("设备数: " + license.getMaxDevices());
        System.out.println("功能: " + String.join(", ", features));
        System.out.println("硬件指纹: " + hardwareFingerprint);
        System.out.println();
        
        return license;
    }
    
    /**
     * 根据许可证类型获取功能列表
     */
    private List<String> getFeaturesForType(String licenseType) {
        switch (licenseType) {
            case "trial":
                return Arrays.asList("basic_health", "basic_alert", "user_management");
            case "standard":
                return Arrays.asList("health_monitoring", "alert_system", "user_management", "device_management", "basic_reports");
            case "professional":
                return Arrays.asList("health_monitoring", "alert_system", "user_management", "device_management", 
                                   "advanced_reports", "big_screen", "organization_management");
            case "enterprise":
                return Arrays.asList("health_monitoring", "alert_system", "user_management", "device_management",
                                   "advanced_reports", "big_screen", "organization_management", "ai_analysis", 
                                   "custom_integration", "priority_support");
            default:
                return Arrays.asList("basic_health");
        }
    }
    
    /**
     * 保存许可证文件
     */
    private void saveLicenseFile(String fileName, String content) throws IOException {
        try (FileWriter writer = new FileWriter(fileName)) {
            writer.write(content);
        }
        System.out.println("许可证文件已保存: " + fileName);
    }
    
    /**
     * 保存公钥文件
     */
    private void savePublicKey(String fileName, PublicKey publicKey) throws IOException {
        String publicKeyStr = Base64.getEncoder().encodeToString(publicKey.getEncoded());
        
        try (FileWriter writer = new FileWriter(fileName)) {
            writer.write("-----BEGIN PUBLIC KEY-----\n");
            // 每64个字符换行
            for (int i = 0; i < publicKeyStr.length(); i += 64) {
                int endIndex = Math.min(i + 64, publicKeyStr.length());
                writer.write(publicKeyStr.substring(i, endIndex) + "\n");
            }
            writer.write("-----END PUBLIC KEY-----\n");
        }
        
        System.out.println("公钥文件已保存: " + fileName);
        System.out.println("请将以下公钥嵌入到 LicenseValidator.getEmbeddedPublicKey() 方法中:");
        System.out.println("\"" + publicKeyStr + "\"");
    }
}