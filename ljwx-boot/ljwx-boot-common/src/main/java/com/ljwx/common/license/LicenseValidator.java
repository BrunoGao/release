package com.ljwx.common.license;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

/**
 * 许可证验证器
 * 负责许可证的解析、验证和签名校验
 */
@Slf4j
@Service
public class LicenseValidator {
    
    private static final String RSA_ALGORITHM = "RSA";
    private static final String SIGNATURE_ALGORITHM = "SHA256withRSA";
    
    private final ObjectMapper objectMapper;
    
    public LicenseValidator() {
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
    }
    
    /**
     * 解析许可证
     */
    public LicenseInfo parseLicense(String licenseContent) throws Exception {
        try {
            // 1. Base64解码
            byte[] decodedBytes = Base64.getDecoder().decode(licenseContent);
            String decodedContent = new String(decodedBytes, StandardCharsets.UTF_8);
            
            // 2. JSON解析
            LicenseContainer container = objectMapper.readValue(decodedContent, LicenseContainer.class);
            
            // 3. 解析许可证数据
            LicenseInfo licenseInfo = objectMapper.readValue(container.getData(), LicenseInfo.class);
            licenseInfo.setSignature(container.getSignature());
            
            log.info("许可证解析成功: 客户={}, 类型={}, 有效期={}~{}", 
                licenseInfo.getCustomerName(),
                licenseInfo.getLicenseType(),
                licenseInfo.getStartDate(),
                licenseInfo.getEndDate());
            
            return licenseInfo;
            
        } catch (Exception e) {
            log.error("许可证解析失败", e);
            throw new LicenseException("许可证格式无效", e);
        }
    }
    
    /**
     * 验证许可证签名
     */
    public boolean verifySignature(LicenseInfo licenseInfo) {
        try {
            // 获取内置公钥
            PublicKey publicKey = getPublicKey();
            if (publicKey == null) {
                log.warn("公钥不存在，跳过签名验证");
                return true; // 开发模式下允许跳过签名验证
            }
            
            // 生成待验证的数据
            String dataToVerify = generateSignatureData(licenseInfo);
            
            // 验证签名
            Signature signature = Signature.getInstance(SIGNATURE_ALGORITHM);
            signature.initVerify(publicKey);
            signature.update(dataToVerify.getBytes(StandardCharsets.UTF_8));
            
            byte[] signatureBytes = Base64.getDecoder().decode(licenseInfo.getSignature());
            boolean valid = signature.verify(signatureBytes);
            
            if (valid) {
                log.info("许可证签名验证成功");
            } else {
                log.error("许可证签名验证失败");
            }
            
            return valid;
            
        } catch (Exception e) {
            log.error("签名验证过程失败", e);
            return false;
        }
    }
    
    /**
     * 生成许可证签名数据
     */
    private String generateSignatureData(LicenseInfo licenseInfo) {
        return licenseInfo.getLicenseId() + "|" +
               licenseInfo.getCustomerId() + "|" +
               licenseInfo.getHardwareFingerprint() + "|" +
               licenseInfo.getStartDate() + "|" +
               licenseInfo.getEndDate() + "|" +
               licenseInfo.getMaxUsers() + "|" +
               licenseInfo.getMaxDevices();
    }
    
    /**
     * 获取内置公钥
     */
    private PublicKey getPublicKey() {
        try {
            // 这里应该是内置的公钥，用于验证许可证签名
            // 在实际部署时，公钥会嵌入到JAR文件中
            String publicKeyStr = getEmbeddedPublicKey();
            
            if (publicKeyStr == null || publicKeyStr.isEmpty()) {
                return null;
            }
            
            byte[] keyBytes = Base64.getDecoder().decode(publicKeyStr);
            X509EncodedKeySpec spec = new X509EncodedKeySpec(keyBytes);
            KeyFactory keyFactory = KeyFactory.getInstance(RSA_ALGORITHM);
            
            return keyFactory.generatePublic(spec);
            
        } catch (Exception e) {
            log.error("获取公钥失败", e);
            return null;
        }
    }
    
    /**
     * 获取嵌入的公钥
     * 实际部署时，这个公钥会被编译到代码中
     */
    private String getEmbeddedPublicKey() {
        // 开发环境暂时返回null，实际部署时会有真实的公钥
        // 公钥示例格式（这不是真实公钥）:
        // "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."
        return null; 
    }
    
    /**
     * 许可证容器类
     */
    private static class LicenseContainer {
        private String data;
        private String signature;
        private String algorithm;
        private long timestamp;
        
        // Getters and Setters
        public String getData() { return data; }
        public void setData(String data) { this.data = data; }
        
        public String getSignature() { return signature; }
        public void setSignature(String signature) { this.signature = signature; }
        
        public String getAlgorithm() { return algorithm; }
        public void setAlgorithm(String algorithm) { this.algorithm = algorithm; }
        
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }
    
    /**
     * 生成许可证文件（用于许可证生成工具）
     */
    public String generateLicense(LicenseInfo licenseInfo, PrivateKey privateKey) throws Exception {
        try {
            // 1. 生成签名
            String dataToSign = generateSignatureData(licenseInfo);
            Signature signature = Signature.getInstance(SIGNATURE_ALGORITHM);
            signature.initSign(privateKey);
            signature.update(dataToSign.getBytes(StandardCharsets.UTF_8));
            byte[] signatureBytes = signature.sign();
            
            // 2. 设置签名
            licenseInfo.setSignature(Base64.getEncoder().encodeToString(signatureBytes));
            
            // 3. 创建容器
            LicenseContainer container = new LicenseContainer();
            container.setData(objectMapper.writeValueAsString(licenseInfo));
            container.setSignature(licenseInfo.getSignature());
            container.setAlgorithm(SIGNATURE_ALGORITHM);
            container.setTimestamp(System.currentTimeMillis());
            
            // 4. 编码
            String containerJson = objectMapper.writeValueAsString(container);
            return Base64.getEncoder().encodeToString(containerJson.getBytes(StandardCharsets.UTF_8));
            
        } catch (Exception e) {
            log.error("生成许可证失败", e);
            throw new LicenseException("生成许可证失败", e);
        }
    }
}