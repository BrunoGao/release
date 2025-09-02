package com.ljwx.common.util;

import org.springframework.web.multipart.MultipartFile;
import lombok.extern.slf4j.Slf4j;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/**
 * 文件上传工具类
 * @author jjgao
 */
@Slf4j
public class FileUploadUtil {
    
    // 基础上传目录
    private static final String BASE_UPLOAD_DIR = "uploads";
    
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
    public static String uploadCustomerLogo(MultipartFile file, Long customerId) throws IOException {
        // 验证文件
        validateLogoFile(file);
        
        // 生成文件名
        String originalFilename = file.getOriginalFilename();
        String fileExtension = getFileExtension(originalFilename);
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        String newFileName = "logo_" + timestamp + "_" + UUID.randomUUID().toString().substring(0, 8) + "." + fileExtension;
        
        // 构建存储路径
        String relativePath = BASE_UPLOAD_DIR + "/logos/customer_" + customerId + "/" + newFileName;
        String absolutePath = getAbsolutePath(relativePath);
        
        // 创建目录
        File targetFile = new File(absolutePath);
        if (!targetFile.getParentFile().exists()) {
            targetFile.getParentFile().mkdirs();
        }
        
        // 保存文件
        file.transferTo(targetFile);
        
        log.info("Logo uploaded successfully: customerId={}, fileName={}, path={}", 
                customerId, newFileName, relativePath);
        
        // 返回相对路径用于数据库存储
        return "/" + relativePath;
    }
    
    /**
     * 删除客户logo文件
     * @param logoUrl logo文件路径
     * @return 删除是否成功
     */
    public static boolean deleteCustomerLogo(String logoUrl) {
        if (logoUrl == null || logoUrl.isEmpty()) {
            return true;
        }
        
        try {
            // 去掉开头的斜杠
            String relativePath = logoUrl.startsWith("/") ? logoUrl.substring(1) : logoUrl;
            String absolutePath = getAbsolutePath(relativePath);
            
            File file = new File(absolutePath);
            if (file.exists()) {
                boolean deleted = file.delete();
                log.info("Logo file deleted: path={}, success={}", absolutePath, deleted);
                return deleted;
            }
            return true; // 文件不存在也认为删除成功
        } catch (Exception e) {
            log.error("Failed to delete logo file: {}", logoUrl, e);
            return false;
        }
    }
    
    /**
     * 验证logo文件
     */
    private static void validateLogoFile(MultipartFile file) {
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
    private static String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf(".") + 1);
    }
    
    /**
     * 获取绝对路径
     */
    private static String getAbsolutePath(String relativePath) {
        // 获取项目根目录
        String userDir = System.getProperty("user.dir");
        
        // 如果当前目录是ljwx-boot-admin，则回退到父目录
        // 保持与StaticResourceConfig相同的逻辑
        if (userDir.endsWith("ljwx-boot-admin")) {
            userDir = userDir.substring(0, userDir.length() - "/ljwx-boot-admin".length());
        }
        
        return userDir + File.separator + relativePath.replace("/", File.separator);
    }
    
    /**
     * 检查文件是否存在
     */
    public static boolean fileExists(String logoUrl) {
        if (logoUrl == null || logoUrl.isEmpty()) {
            return false;
        }
        
        String relativePath = logoUrl.startsWith("/") ? logoUrl.substring(1) : logoUrl;
        String absolutePath = getAbsolutePath(relativePath);
        return new File(absolutePath).exists();
    }
}