package com.ljwx.infrastructure.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * 静态资源配置
 * 用于配置上传文件的访问路径
 * @author jjgao
 */
@Configuration
@Slf4j
public class StaticResourceConfig implements WebMvcConfigurer {

    @Autowired
    private LogoConfig logoConfig;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 使用统一的配置获取上传路径
        String uploadsPath = "file:" + logoConfig.getAbsoluteUploadPath() + "/";
        
        log.info("配置静态资源访问路径: /uploads/** -> {}", uploadsPath);
        
        // 配置uploads目录的静态资源映射
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations(uploadsPath)
                .setCachePeriod(86400); // 缓存1天
        
        // 兼容性配置：支持直接通过/logos访问logo文件
        registry.addResourceHandler("/logos/**")
                .addResourceLocations(uploadsPath + "logos/")
                .setCachePeriod(86400); // 缓存1天
    }
}