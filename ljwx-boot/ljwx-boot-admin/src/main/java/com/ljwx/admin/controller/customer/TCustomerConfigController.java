/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.admin.controller.customer;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.config.LogoConfig;
import com.ljwx.modules.customer.service.LogoUploadService;
import com.ljwx.common.license.CustomerLicenseService;
import com.ljwx.common.license.CustomerLicenseStatus;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;
import com.ljwx.modules.customer.facade.ITCustomerConfigFacade;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.system.domain.dto.org.units.DepartmentDeletePreCheckDTO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.NonNull;
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
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 *  Controller 控制层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName customer.controller.com.ljwx.admin.TCustomerConfigController
 * @CreateTime 2024-12-29 - 15:33:30
 */

@RestController
@Tag(name = "客户配置管理")
@RequiredArgsConstructor
@RequestMapping("t_customer_config")
@Slf4j
public class TCustomerConfigController {

    @NonNull
    private ITCustomerConfigFacade tCustomerConfigFacade;
    
    @NonNull
    private ITCustomerConfigService tCustomerConfigService;
    
    @NonNull
    private LogoConfig logoConfig;
    
    @NonNull
    private LogoUploadService logoUploadService;
    
    @NonNull
    private CustomerLicenseService customerLicenseService;

    @GetMapping("/page")
    @SaCheckPermission("t:customer:config:page")
    @Operation(operationId = "1", summary = "获取列表")
    public Result<RPage<TCustomerConfigVO>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                 @Parameter(description = "查询对象") TCustomerConfigSearchDTO tCustomerConfigSearchDTO) {
        return Result.data(tCustomerConfigFacade.listTCustomerConfigPage(pageQuery, tCustomerConfigSearchDTO));
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:customer:config:get")
    @Operation(operationId = "2", summary = "根据ID获取详细信息")
    public Result<TCustomerConfigVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        return Result.data(tCustomerConfigFacade.get(id));
    }

    @PostMapping("/")
    @SaCheckPermission("t:customer:config:add")
    @Operation(operationId = "3", summary = "新增")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TCustomerConfigAddDTO tCustomerConfigAddDTO) {
        return Result.status(tCustomerConfigFacade.add(tCustomerConfigAddDTO));
    }

    @PutMapping("/")
    @SaCheckPermission("t:customer:config:update")
    @Operation(operationId = "4", summary = "更新信息")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO) {
        return Result.status(tCustomerConfigFacade.update(tCustomerConfigUpdateDTO));
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "5", summary = "批量删除信息")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        return Result.status(tCustomerConfigFacade.batchDelete(tCustomerConfigDeleteDTO));
    }
    
    @DeleteMapping("/{id}")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "13", summary = "删除单个租户")
    public Result<Boolean> deleteTenant(@Parameter(description = "租户ID") @PathVariable("id") Long id) {
        try {
            TCustomerConfigDeleteDTO deleteDTO = new TCustomerConfigDeleteDTO();
            deleteDTO.setIds(List.of(id));
            
            // 使用现有的级联删除逻辑
            return Result.status(tCustomerConfigFacade.tenantCascadeDelete(deleteDTO));
            
        } catch (Exception e) {
            log.error("删除租户失败: id=" + id, e);
            return Result.failure("删除租户失败: " + e.getMessage());
        }
    }
    
    @PostMapping("/tenant-delete-precheck/{id}")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "14", summary = "删除单个租户前置检查")
    public Result<DepartmentDeletePreCheckDTO> tenantDeletePrecheck(@Parameter(description = "租户ID") @PathVariable("id") Long id) {
        try {
            TCustomerConfigDeleteDTO deleteDTO = new TCustomerConfigDeleteDTO();
            deleteDTO.setIds(List.of(id));
            
            return Result.data(tCustomerConfigFacade.tenantDeletePreCheck(deleteDTO));
            
        } catch (Exception e) {
            log.error("租户删除前置检查失败: id=" + id, e);
            return Result.failure("前置检查失败: " + e.getMessage());
        }
    }

    @PostMapping("/tenant-delete-precheck")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "6", summary = "删除租户前置检查 - 分析影响的部门、用户和设备")
    public Result<DepartmentDeletePreCheckDTO> tenantDeletePrecheck(@Parameter(description = "删除对象") @RequestBody TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        return Result.data(tCustomerConfigFacade.tenantDeletePreCheck(tCustomerConfigDeleteDTO));
    }

    @DeleteMapping("/tenant-cascade-delete")
    @SaCheckPermission("t:customer:config:delete")
    @Operation(operationId = "7", summary = "级联删除租户 - 包含部门、用户和设备")
    public Result<Boolean> tenantCascadeDelete(@Parameter(description = "删除对象") @RequestBody TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        return Result.status(tCustomerConfigFacade.tenantCascadeDelete(tCustomerConfigDeleteDTO));
    }

    // ==================== Logo管理相关接口 ====================
    
    /**
     * 上传客户logo
     */
    @PostMapping("/logo/upload")
    @SaCheckPermission("t:customer:config:logo:upload")
    @Operation(operationId = "6", summary = "上传客户logo")
    public Result<Map<String, Object>> uploadLogo(
            @Parameter(description = "logo文件", required = true) 
            @RequestParam("file") MultipartFile file,
            @Parameter(description = "客户ID", required = true) 
            @RequestParam("customerId") Long customerId) {
        
        try {
            log.info("管理端上传客户logo: customerId={}, fileName={}, size={}", 
                    customerId, file.getOriginalFilename(), file.getSize());
            
            // 检查客户是否存在
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            // 删除旧的logo文件
            if (customerConfig.getLogoUrl() != null) {
                logoUploadService.deleteCustomerLogo(customerConfig.getLogoUrl());
                log.info("删除旧logo文件: {}", customerConfig.getLogoUrl());
            }
            
            // 上传新文件
            String logoUrl = logoUploadService.uploadCustomerLogo(file, customerId);
            String fileName = file.getOriginalFilename();
            
            // 更新数据库
            customerConfig.setLogoUrl(logoUrl);
            customerConfig.setLogoFileName(fileName);
            customerConfig.setLogoUploadTime(LocalDateTime.now());
            tCustomerConfigService.updateById(customerConfig);
            
            // 返回结果
            Map<String, Object> result = new HashMap<>();
            result.put("logoUrl", logoUrl);
            result.put("fileName", fileName);
            result.put("uploadTime", customerConfig.getLogoUploadTime());
            result.put("customerId", customerId);
            
            log.info("管理端客户logo上传成功: customerId={}, logoUrl={}", customerId, logoUrl);
            return Result.success("Logo上传成功", result);
            
        } catch (Exception e) {
            log.error("管理端上传客户logo失败: customerId=" + customerId, e);
            return Result.failure("上传失败: " + e.getMessage());
        }
    }

    /**
     * 获取客户logo文件
     */
    @GetMapping("/logo/{customerId}")
    @Operation(operationId = "7", summary = "获取客户logo")
    public ResponseEntity<Resource> getLogo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
            String logoUrl;
            
            if (customerConfig != null && customerConfig.getLogoUrl() != null && 
                logoUploadService.fileExists(customerConfig.getLogoUrl())) {
                // 使用客户自定义logo
                logoUrl = customerConfig.getLogoUrl();
                log.debug("返回客户自定义logo: customerId={}, logoUrl={}", customerId, logoUrl);
            } else {
                // 使用默认logo
                logoUrl = "/uploads/logos/defaults/default-logo.svg";
                log.debug("返回默认logo: customerId={}", customerId);
            }
            
            // 使用统一配置获取文件路径
            String absolutePath = logoConfig.getAbsolutePath(logoUrl);
            
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
            headers.setCacheControl("max-age=3600"); // 管理端缓存1小时即可
            
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
    @DeleteMapping("/logo/{customerId}")
    @SaCheckPermission("t:customer:config:logo:delete")
    @Operation(operationId = "8", summary = "删除客户logo")
    public Result<String> deleteLogo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            if (customerConfig.getLogoUrl() == null) {
                return Result.success("客户未设置自定义logo");
            }
            
            // 删除文件
            boolean fileDeleted = logoUploadService.deleteCustomerLogo(customerConfig.getLogoUrl());
            
            // 清除数据库记录
            customerConfig.setLogoUrl(null);
            customerConfig.setLogoFileName(null);
            customerConfig.setLogoUploadTime(null);
            tCustomerConfigService.updateById(customerConfig);
            
            log.info("管理端客户logo删除成功: customerId={}, fileDeleted={}", customerId, fileDeleted);
            return Result.success("Logo删除成功，已恢复默认logo");
            
        } catch (Exception e) {
            log.error("管理端删除客户logo失败: customerId=" + customerId, e);
            return Result.failure("删除失败: " + e.getMessage());
        }
    }

    /**
     * 获取客户logo信息
     */
    @GetMapping("/logo/info/{customerId}")
    @SaCheckPermission("t:customer:config:logo:info")
    @Operation(operationId = "9", summary = "获取客户logo信息")
    public Result<Map<String, Object>> getLogoInfo(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
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
            info.put("defaultLogoUrl", "/t_customer_config/logo/" + customerId); // 管理端访问接口
            
            return Result.data(info);
            
        } catch (Exception e) {
            log.error("获取客户logo信息失败: customerId=" + customerId, e);
            return Result.failure("获取信息失败: " + e.getMessage());
        }
    }
    
    // ==================== 许可证管理相关接口 ====================
    
    /**
     * 获取客户许可证状态
     */
    @GetMapping("/license/status/{customerId}")
    @SaCheckPermission("t:customer:config:license:status")
    @Operation(operationId = "10", summary = "获取客户许可证状态")
    public Result<CustomerLicenseStatus> getCustomerLicenseStatus(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId) {
        
        try {
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            CustomerLicenseStatus status = customerLicenseService.getCustomerLicenseStatus(
                customerId, customerConfig.getIsSupportLicense());
            
            return Result.data(status);
            
        } catch (Exception e) {
            log.error("获取客户许可证状态失败: customerId=" + customerId, e);
            return Result.failure("获取许可证状态失败: " + e.getMessage());
        }
    }
    
    /**
     * 更新客户许可证支持状态
     */
    @PutMapping("/license/support/{customerId}")
    @SaCheckPermission("t:customer:config:license:update")
    @Operation(operationId = "11", summary = "更新客户许可证支持状态")
    public Result<String> updateCustomerLicenseSupport(
            @Parameter(description = "客户ID", required = true) 
            @PathVariable Long customerId,
            @Parameter(description = "是否支持许可证", required = true)
            @RequestParam Boolean supportLicense) {
        
        try {
            TCustomerConfig customerConfig = tCustomerConfigService.getById(customerId);
            if (customerConfig == null) {
                return Result.failure("客户不存在: " + customerId);
            }
            
            Boolean oldValue = customerConfig.getIsSupportLicense();
            customerConfig.setIsSupportLicense(supportLicense);
            tCustomerConfigService.updateById(customerConfig);
            
            log.info("更新客户许可证支持状态: customerId={}, {} -> {}", 
                    customerId, oldValue, supportLicense);
            
            return Result.success("许可证支持状态更新成功");
            
        } catch (Exception e) {
            log.error("更新客户许可证支持状态失败: customerId=" + customerId, e);
            return Result.failure("更新失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取所有可用的客户列表（用于客户选择器）
     */
    @GetMapping("/all-customers")
    @Operation(operationId = "12", summary = "获取所有可用的客户列表")
    public Result<List<Map<String, Object>>> getAllAvailableCustomers() {
        try {
            List<TCustomerConfig> customerConfigs = tCustomerConfigService.list();
            
            List<Map<String, Object>> customers = customerConfigs.stream()
                    .filter(config -> config.getIsDeleted() == null || config.getIsDeleted() == 0) // 过滤未删除的
                    .map(config -> {
                        Map<String, Object> customer = new HashMap<>();
                        customer.put("customerId", config.getCustomerId()); // 返回顶级部门ID，用于前端选择
                        customer.put("customerName", config.getCustomerName());
                        customer.put("configId", config.getId()); // 添加配置记录ID，备用
                        log.debug("Customer: configId={}, customerId={}, name={}, isDeleted={}", 
                                config.getId(), config.getCustomerId(), config.getCustomerName(), config.getIsDeleted());
                        return customer;
                    })
                    .collect(Collectors.toList());
            
            log.info("获取可用客户列表成功，共{}个客户", customers.size());
            return Result.data(customers);
            
        } catch (Exception e) {
            log.error("获取可用客户列表失败", e);
            return Result.failure("获取客户列表失败: " + e.getMessage());
        }
    }

}