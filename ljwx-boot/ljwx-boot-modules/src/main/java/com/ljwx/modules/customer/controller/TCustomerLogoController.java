package com.ljwx.modules.customer.controller;

import com.ljwx.common.util.FileUploadUtil;
import com.ljwx.common.api.Result;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 客户Logo管理控制器
 * @author jjgao
 */
@Tag(name = "客户Logo管理", description = "客户Logo上传、获取、删除等操作")
@RestController
@RequestMapping("/customer/logo")
@RequiredArgsConstructor
@Slf4j
public class TCustomerLogoController {

    private final ITCustomerConfigService customerConfigService;

    /**
     * 上传客户logo
     */
    @Operation(summary = "上传客户logo", description = "上传并设置指定客户的自定义logo")
    @PostMapping("/upload")
    public Result<Map<String, Object>> uploadLogo(
            @Parameter(description = "logo文件", required = true) 
            @RequestParam("file") MultipartFile file,
            @Parameter(description = "客户ID", required = true) 
            @RequestParam("customerId") Long customerId) {
        
        try {
            log.info("开始上传客户logo: customerId={}, fileName={}, size={}", 
                    customerId, file.getOriginalFilename(), file.getSize());
            
            // 检查客户是否存在
            TCustomerConfig customerConfig = customerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            // 删除旧的logo文件
            if (customerConfig.getLogoUrl() != null) {
                FileUploadUtil.deleteCustomerLogo(customerConfig.getLogoUrl());
                log.info("删除旧logo文件: {}", customerConfig.getLogoUrl());
            }
            
            // 上传新文件
            String logoUrl = FileUploadUtil.uploadCustomerLogo(file, customerId);
            String fileName = file.getOriginalFilename();
            
            // 更新数据库
            customerConfig.setLogoUrl(logoUrl);
            customerConfig.setLogoFileName(fileName);
            customerConfig.setLogoUploadTime(LocalDateTime.now());
            customerConfigService.updateById(customerConfig);
            
            // 返回结果
            Map<String, Object> result = new HashMap<>();
            result.put("logoUrl", logoUrl);
            result.put("fileName", fileName);
            result.put("uploadTime", customerConfig.getLogoUploadTime());
            result.put("customerId", customerId);
            
            log.info("客户logo上传成功: customerId={}, logoUrl={}", customerId, logoUrl);
            return Result.success("Logo上传成功", result);
            
        } catch (Exception e) {
            log.error("上传客户logo失败: customerId=" + customerId, e);
            return Result.failure("上传失败: " + e.getMessage());
        }
    }

    /**
     * 获取客户logo文件
     */
    @Operation(summary = "获取客户logo", description = "获取指定客户的logo文件")
    @GetMapping("/{customerId}")
    public ResponseEntity<Resource> getLogo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = customerConfigService.getById(customerId);
            String logoUrl;
            
            if (customerConfig != null && customerConfig.getLogoUrl() != null && 
                FileUploadUtil.fileExists(customerConfig.getLogoUrl())) {
                // 使用客户自定义logo
                logoUrl = customerConfig.getLogoUrl();
                log.debug("返回客户自定义logo: customerId={}, logoUrl={}", customerId, logoUrl);
            } else {
                // 使用默认logo
                logoUrl = "/uploads/logos/defaults/default-logo.svg";
                log.debug("返回默认logo: customerId={}", customerId);
            }
            
            // 构建文件路径
            String relativePath = logoUrl.startsWith("/") ? logoUrl.substring(1) : logoUrl;
            String absolutePath = System.getProperty("user.dir") + File.separator + 
                                relativePath.replace("/", File.separator);
            
            File file = new File(absolutePath);
            if (!file.exists()) {
                log.warn("Logo文件不存在: {}", absolutePath);
                return ResponseEntity.notFound().build();
            }
            
            Resource resource = new FileSystemResource(file);
            
            // 设置响应头
            HttpHeaders headers = new HttpHeaders();
            String fileName = file.getName();
            if (fileName.endsWith(".svg")) {
                headers.setContentType(MediaType.valueOf("image/svg+xml"));
            } else {
                headers.setContentType(MediaType.IMAGE_PNG);
            }
            headers.setCacheControl("max-age=86400"); // 缓存1天
            
            return ResponseEntity.ok()
                    .headers(headers)
                    .body(resource);
                    
        } catch (Exception e) {
            log.error("获取客户logo失败: customerId=" + customerId, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 删除客户logo
     */
    @Operation(summary = "删除客户logo", description = "删除指定客户的自定义logo，恢复使用默认logo")
    @DeleteMapping("/{customerId}")
    public Result<String> deleteLogo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = customerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            if (customerConfig.getLogoUrl() == null) {
                return Result.success("客户未设置自定义logo");
            }
            
            // 删除文件
            boolean fileDeleted = FileUploadUtil.deleteCustomerLogo(customerConfig.getLogoUrl());
            
            // 清除数据库记录
            customerConfig.setLogoUrl(null);
            customerConfig.setLogoFileName(null);
            customerConfig.setLogoUploadTime(null);
            customerConfigService.updateById(customerConfig);
            
            log.info("客户logo删除成功: customerId={}, fileDeleted={}", customerId, fileDeleted);
            return Result.success("Logo删除成功，已恢复默认logo");
            
        } catch (Exception e) {
            log.error("删除客户logo失败: customerId=" + customerId, e);
            return Result.failure("删除失败: " + e.getMessage());
        }
    }

    /**
     * 获取客户logo信息
     */
    @Operation(summary = "获取客户logo信息", description = "获取指定客户的logo相关信息")
    @GetMapping("/info/{customerId}")
    public Result<Map<String, Object>> getLogoInfo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = customerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            Map<String, Object> info = new HashMap<>();
            info.put("customerId", customerId);
            info.put("customerName", customerConfig.getCustomerName());
            info.put("hasCustomLogo", customerConfig.getLogoUrl() != null);
            info.put("logoUrl", customerConfig.getLogoUrl());
            info.put("logoFileName", customerConfig.getLogoFileName());
            info.put("logoUploadTime", customerConfig.getLogoUploadTime());
            info.put("defaultLogoUrl", "/customer/logo/" + customerId); // 统一访问接口
            
            return Result.data(info);
            
        } catch (Exception e) {
            log.error("获取客户logo信息失败: customerId=" + customerId, e);
            return Result.failure("获取信息失败: " + e.getMessage());
        }
    }
}