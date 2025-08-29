package com.ljwx.modules.customer.service;

import com.ljwx.infrastructure.config.LogoConfig;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/**
 * Logo文件上传服务
 * 使用统一的LogoConfig配置管理文件路径
 * 
 * @author jjgao
 */
@Slf4j
@Service
public class LogoUploadService {

    @Autowired
    private LogoConfig logoConfig;
    
    // 允许的图片格式
    private static final List<String> ALLOWED_LOGO_EXTENSIONS = Arrays.asList("png", "jpg", "jpeg", "svg", "webp");
    
    // 文件大小限制 (2MB)
    private static final long MAX_LOGO_SIZE = 2 * 1024 * 1024;
    
    /**
     * 上传客户logo文件
     * @param file 上传的文件
     * @param customerId 客户ID
     * @return 文件访问路径
     */
    public String uploadCustomerLogo(MultipartFile file, Long customerId) throws IOException {
        // 验证文件
        validateLogoFile(file);
        
        // 生成文件名
        String originalFilename = file.getOriginalFilename();
        String fileExtension = getFileExtension(originalFilename);
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        String newFileName = "logo_" + timestamp + "_" + UUID.randomUUID().toString().substring(0, 8) + "." + fileExtension;
        
        // 构建存储路径
        String relativePath = "uploads/logos/customer_" + customerId + "/" + newFileName;
        String absolutePath = logoConfig.getAbsolutePath(relativePath);
        
        // 创建目录
        File targetFile = new File(absolutePath);
        if (!targetFile.getParentFile().exists()) {
            boolean created = targetFile.getParentFile().mkdirs();
            log.info("Created logo directory: {}, success: {}", targetFile.getParentFile().getAbsolutePath(), created);
        }
        
        // 保存文件
        file.transferTo(targetFile);
        
        log.info("Logo uploaded successfully: customerId={}, fileName={}, absolutePath={}", 
                customerId, newFileName, absolutePath);
        
        // 返回相对路径用于数据库存储和Web访问
        return "/" + relativePath;
    }
    
    /**
     * 删除客户logo文件
     * @param logoUrl logo文件路径
     * @return 删除是否成功
     */
    public boolean deleteCustomerLogo(String logoUrl) {
        if (logoUrl == null || logoUrl.isEmpty()) {
            return true;
        }
        
        try {
            String absolutePath = logoConfig.getAbsolutePath(logoUrl);
            
            File file = new File(absolutePath);
            if (file.exists()) {
                boolean deleted = file.delete();
                log.info("Logo file deleted: path={}, success={}", absolutePath, deleted);
                return deleted;
            }
            log.info("Logo file not exists, consider as deleted: {}", absolutePath);
            return true; // 文件不存在也认为删除成功
        } catch (Exception e) {
            log.error("Failed to delete logo file: {}", logoUrl, e);
            return false;
        }
    }
    
    /**
     * 检查文件是否存在
     */
    public boolean fileExists(String logoUrl) {
        if (logoUrl == null || logoUrl.isEmpty()) {
            return false;
        }
        
        try {
            String absolutePath = logoConfig.getAbsolutePath(logoUrl);
            boolean exists = new File(absolutePath).exists();
            log.debug("Check file exists: {} -> {}", absolutePath, exists);
            return exists;
        } catch (Exception e) {
            log.error("Failed to check file exists: {}", logoUrl, e);
            return false;
        }
    }
    
    /**
     * 验证logo文件
     */
    private void validateLogoFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("文件不能为空");
        }
        
        // 检查文件大小
        if (file.getSize() > MAX_LOGO_SIZE) {
            throw new IllegalArgumentException("文件大小不能超过2MB");
        }
        
        // 检查文件格式
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null) {
            throw new IllegalArgumentException("文件名不能为空");
        }
        
        String fileExtension = getFileExtension(originalFilename).toLowerCase();
        if (!ALLOWED_LOGO_EXTENSIONS.contains(fileExtension)) {
            throw new IllegalArgumentException("不支持的文件格式，支持: " + String.join(", ", ALLOWED_LOGO_EXTENSIONS));
        }
        
        // 检查文件内容类型
        String contentType = file.getContentType();
        if (contentType == null || !contentType.startsWith("image/")) {
            throw new IllegalArgumentException("文件必须是图片类型");
        }
    }
    
    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf(".") + 1);
    }
}