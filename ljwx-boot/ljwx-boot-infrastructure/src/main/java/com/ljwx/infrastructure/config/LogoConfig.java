package com.ljwx.infrastructure.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.io.File;

/**
 * Logo上传配置类
 * 支持本地开发和Docker环境的路径配置
 * 
 * @author jjgao
 */
@Data
@Component
@ConfigurationProperties(prefix = "ljwx.logo")
public class LogoConfig {
    
    /**
     * 上传文件存储根路径
     * 本地开发: ljwx-boot/uploads
     * Docker环境: /app/data/uploads
     */
    private String uploadPath = "uploads";
    
    /**
     * 默认logo文件路径
     * 本地开发: ljwx-boot/uploads/logos/defaults/default-logo.svg
     * Docker环境: /app/data/uploads/logos/defaults/default-logo.svg
     */
    private String defaultLogo = "uploads/logos/defaults/default-logo.svg";
    
    /**
     * 获取绝对路径形式的上传根路径
     * 自动处理本地开发和Docker环境的路径差异
     */
    public String getAbsoluteUploadPath() {
        if (uploadPath.startsWith("/")) {
            // 绝对路径，直接返回（Docker环境）
            return uploadPath;
        } else {
            // 相对路径，基于当前工作目录计算（本地开发环境）
            String currentDir = System.getProperty("user.dir");
            
            // 如果当前目录以yunxiang结尾，说明是从项目根目录启动的
            if (currentDir.endsWith("yunxiang")) {
                return currentDir + File.separator + uploadPath;
            } else if (currentDir.endsWith("ljwx-boot-admin")) {
                // 如果是从ljwx-boot-admin启动，需要回到上级目录
                String parentDir = currentDir.substring(0, currentDir.length() - "/ljwx-boot-admin".length());
                return parentDir + File.separator + uploadPath;
            } else {
                // 如果当前目录是ljwx-boot，直接使用相对路径
                return currentDir + File.separator + uploadPath;
            }
        }
    }
    
    /**
     * 获取绝对路径形式的默认Logo路径
     */
    public String getAbsoluteDefaultLogoPath() {
        if (defaultLogo.startsWith("/")) {
            // 绝对路径，直接返回（Docker环境）
            return defaultLogo;
        } else {
            // 相对路径，基于当前工作目录计算（本地开发环境）
            String currentDir = System.getProperty("user.dir");
            
            // 如果当前目录以yunxiang结尾，说明是从项目根目录启动的
            if (currentDir.endsWith("yunxiang")) {
                return currentDir + File.separator + defaultLogo;
            } else if (currentDir.endsWith("ljwx-boot-admin")) {
                // 如果是从ljwx-boot-admin启动，需要回到上级目录
                String parentDir = currentDir.substring(0, currentDir.length() - "/ljwx-boot-admin".length());
                return parentDir + File.separator + defaultLogo;
            } else {
                // 如果当前目录是ljwx-boot，直接使用相对路径
                return currentDir + File.separator + defaultLogo;
            }
        }
    }
    
    /**
     * 根据相对路径获取绝对路径
     * 
     * @param relativePath 相对路径，如 "uploads/logos/customer_1/logo.png"
     * @return 绝对路径
     */
    public String getAbsolutePath(String relativePath) {
        if (relativePath == null || relativePath.trim().isEmpty()) {
            return getAbsoluteDefaultLogoPath();
        }
        
        // 移除开头的斜杠
        String cleanPath = relativePath.startsWith("/") ? relativePath.substring(1) : relativePath;
        
        String currentDir = System.getProperty("user.dir");
        
        // 如果当前目录以yunxiang结尾，说明是从项目根目录启动的
        if (currentDir.endsWith("yunxiang")) {
            return currentDir + File.separator + "ljwx-boot" + File.separator + cleanPath;
        } else if (currentDir.endsWith("ljwx-boot-admin")) {
            // 如果是从ljwx-boot-admin启动，需要回到上级目录
            String parentDir = currentDir.substring(0, currentDir.length() - "/ljwx-boot-admin".length());
            return parentDir + File.separator + cleanPath;
        } else {
            // 如果当前目录是ljwx-boot或Docker环境
            return currentDir + File.separator + cleanPath;
        }
    }
}