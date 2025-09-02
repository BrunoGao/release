package com.ljwx.common.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/**
 * 文件上传工具类
 * 
 * @author jjgao
 */
@Slf4j
public class FileUploadUtil {

    // 支持的图片格式
    private static final List<String> ALLOWED_IMAGE_EXTENSIONS = Arrays.asList(
        "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"
    );
    
    // 最大文件大小 (5MB)
    private static final long MAX_FILE_SIZE = 5 * 1024 * 1024;
    
    // 基础上传目录
    private static final String BASE_UPLOAD_DIR = "uploads";
    
    // 客户logo上传目录
    private static final String CUSTOMER_LOGO_DIR = "logos/customers";
    
    // 默认logo目录
    private static final String DEFAULT_LOGO_DIR = "logos/defaults";

    /**
     * 上传客户logo文件
     * 
     * @param file 上传的文件
     * @param customerId 客户ID
     * @return 上传后的相对路径
     * @throws IOException 上传失败时抛出异常
     */
    public static String uploadCustomerLogo(MultipartFile file, Long customerId) throws IOException {
        // 参数校验
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("上传文件不能为空");
        }
        
        if (customerId == null || customerId <= 0) {
            throw new IllegalArgumentException("客户ID不能为空");
        }
        
        // 文件大小检查
        if (file.getSize() > MAX_FILE_SIZE) {
            throw new IllegalArgumentException("文件大小不能超过5MB");
        }
        
        // 获取原始文件名和扩展名
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || originalFilename.trim().isEmpty()) {
            throw new IllegalArgumentException("文件名不能为空");
        }
        
        String fileExtension = getFileExtension(originalFilename).toLowerCase();
        if (!ALLOWED_IMAGE_EXTENSIONS.contains(fileExtension)) {
            throw new IllegalArgumentException("不支持的文件格式，请上传图片文件");
        }
        
        // 生成新的文件名
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String uuid = UUID.randomUUID().toString().substring(0, 8);
        String newFileName = String.format("customer_%d_%s_%s.%s", customerId, timestamp, uuid, fileExtension);
        
        // 确保上传目录存在
        String uploadDir = BASE_UPLOAD_DIR + File.separator + CUSTOMER_LOGO_DIR;
        Path uploadPath = Paths.get(uploadDir);
        createDirectories(uploadPath);
        
        // 保存文件
        Path filePath = uploadPath.resolve(newFileName);
        Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
        
        // 返回相对路径 (用于数据库存储和URL访问)
        String relativePath = "/" + BASE_UPLOAD_DIR + "/" + CUSTOMER_LOGO_DIR + "/" + newFileName;
        
        log.info("客户logo上传成功: customerId={}, originalName={}, savedPath={}", 
                customerId, originalFilename, relativePath);
        
        return relativePath;
    }
    
    /**
     * 删除客户logo文件
     * 
     * @param logoUrl 文件相对路径
     * @return 是否删除成功
     */
    public static boolean deleteCustomerLogo(String logoUrl) {
        if (logoUrl == null || logoUrl.trim().isEmpty()) {
            return false;
        }
        
        try {
            // 将相对路径转换为绝对路径
            String relativePath = logoUrl.startsWith("/") ? logoUrl.substring(1) : logoUrl;
            Path filePath = Paths.get(relativePath);
            
            if (Files.exists(filePath)) {
                Files.delete(filePath);
                log.info("客户logo删除成功: {}", logoUrl);
                return true;
            } else {
                log.warn("要删除的logo文件不存在: {}", logoUrl);
                return false;
            }
        } catch (IOException e) {
            log.error("删除客户logo失败: " + logoUrl, e);
            return false;
        }
    }
    
    /**
     * 检查文件是否存在
     * 
     * @param logoUrl 文件相对路径
     * @return 文件是否存在
     */
    public static boolean fileExists(String logoUrl) {
        if (logoUrl == null || logoUrl.trim().isEmpty()) {
            return false;
        }
        
        try {
            String relativePath = logoUrl.startsWith("/") ? logoUrl.substring(1) : logoUrl;
            return Files.exists(Paths.get(relativePath));
        } catch (Exception e) {
            log.warn("检查文件存在性失败: " + logoUrl, e);
            return false;
        }
    }
    
    /**
     * 初始化默认logo文件
     * 创建默认logo目录并复制默认logo文件
     */
    public static void initDefaultLogo() {
        try {
            // 创建默认logo目录
            String defaultLogoDir = BASE_UPLOAD_DIR + File.separator + DEFAULT_LOGO_DIR;
            Path defaultLogoPath = Paths.get(defaultLogoDir);
            createDirectories(defaultLogoPath);
            
            // 创建简单的默认SVG logo
            String defaultLogoContent = createDefaultSvgLogo();
            Path defaultLogoFile = defaultLogoPath.resolve("default-logo.svg");
            
            if (!Files.exists(defaultLogoFile)) {
                Files.write(defaultLogoFile, defaultLogoContent.getBytes("UTF-8"));
                log.info("默认logo文件创建成功: {}", defaultLogoFile.toString());
            }
            
        } catch (Exception e) {
            log.error("初始化默认logo失败", e);
        }
    }
    
    /**
     * 获取文件扩展名
     * 
     * @param filename 文件名
     * @return 扩展名 (不包含点号)
     */
    private static String getFileExtension(String filename) {
        if (filename == null || filename.trim().isEmpty()) {
            return "";
        }
        
        int lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex == -1 || lastDotIndex == filename.length() - 1) {
            return "";
        }
        
        return filename.substring(lastDotIndex + 1);
    }
    
    /**
     * 创建目录 (如果不存在)
     * 
     * @param dirPath 目录路径
     * @throws IOException 创建失败时抛出异常
     */
    private static void createDirectories(Path dirPath) throws IOException {
        if (!Files.exists(dirPath)) {
            Files.createDirectories(dirPath);
            log.info("创建上传目录: {}", dirPath.toString());
        }
    }
    
    /**
     * 创建默认的SVG logo内容
     * 
     * @return SVG内容字符串
     */
    private static String createDefaultSvgLogo() {
        return """
<?xml version="1.0" encoding="UTF-8"?>
<svg width="120" height="120" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4F46E5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7C3AED;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- 背景圆形 -->
  <circle cx="60" cy="60" r="55" fill="url(#grad1)" stroke="#E5E7EB" stroke-width="2"/>
  
  <!-- 中心图标 -->
  <g transform="translate(30, 30)">
    <!-- 公司/企业图标 -->
    <rect x="15" y="25" width="30" height="25" rx="2" fill="white" opacity="0.9"/>
    <rect x="20" y="30" width="5" height="5" fill="#4F46E5"/>
    <rect x="30" y="30" width="5" height="5" fill="#4F46E5"/>
    <rect x="20" y="40" width="5" height="5" fill="#4F46E5"/>
    <rect x="30" y="40" width="5" height="5" fill="#4F46E5"/>
    
    <!-- 文字 -->
    <text x="30" y="20" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="bold" fill="white">
      LJWX
    </text>
  </g>
  
  <!-- 底部文字 -->
  <text x="60" y="95" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="white" opacity="0.8">
    灵境万象
  </text>
</svg>""";
    }
    
    /**
     * 获取文件的MIME类型
     * 
     * @param filename 文件名
     * @return MIME类型
     */
    public static String getContentType(String filename) {
        if (filename == null) {
            return "application/octet-stream";
        }
        
        String extension = getFileExtension(filename).toLowerCase();
        return switch (extension) {
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "gif" -> "image/gif";
            case "bmp" -> "image/bmp";
            case "webp" -> "image/webp";
            case "svg" -> "image/svg+xml";
            default -> "application/octet-stream";
        };
    }
}