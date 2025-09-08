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

package com.ljwx.modules.health.controller;

import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.service.HealthDataConfigQueryService;
import com.ljwx.modules.health.service.UnifiedHealthDataQueryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 统一健康数据查询控制器
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.controller.UnifiedHealthDataController
 * @CreateTime 2025-09-08
 */
@Slf4j
@RestController
@RequestMapping("/health/unified")
@Tag(name = "统一健康数据查询", description = "提供统一的健康数据查询接口，支持分表、快慢表、配置验证等功能")
@Validated
public class UnifiedHealthDataController {

    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;
    
    @Autowired
    private HealthDataConfigQueryService configService;

    @PostMapping("/query")
    @Operation(summary = "统一健康数据查询", 
               description = "支持分表查询、快慢表查询、指标配置验证的统一查询接口")
    public ResponseEntity<Map<String, Object>> queryHealthData(
            @Valid @RequestBody UnifiedHealthQueryDTO queryDTO) {
        
        try {
            log.info("🔍 接收统一健康数据查询请求: customerId={}, userId={}, 时间范围={} ~ {}", 
                queryDTO.getCustomerId(), queryDTO.getUserId(), 
                queryDTO.getStartDate(), queryDTO.getEndDate());

            Map<String, Object> result = unifiedQueryService.queryHealthData(queryDTO);
            
            if ((Boolean) result.get("success")) {
                return ResponseEntity.ok(result);
            } else {
                return ResponseEntity.badRequest().body(result);
            }
            
        } catch (Exception e) {
            log.error("❌ 统一健康数据查询失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @GetMapping("/query/simple")
    @Operation(summary = "简化健康数据查询", description = "提供简化参数的健康数据查询接口")
    public ResponseEntity<Map<String, Object>> queryHealthDataSimple(
            @Parameter(description = "客户ID", required = true) @RequestParam Long customerId,
            @Parameter(description = "用户ID") @RequestParam(required = false) Long userId,
            @Parameter(description = "组织ID") @RequestParam(required = false) Long orgId,
            @Parameter(description = "设备序列号") @RequestParam(required = false) String deviceSn,
            @Parameter(description = "开始时间") @RequestParam LocalDateTime startDate,
            @Parameter(description = "结束时间") @RequestParam LocalDateTime endDate,
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") Integer page,
            @Parameter(description = "每页大小") @RequestParam(defaultValue = "20") Integer pageSize,
            @Parameter(description = "是否最新记录") @RequestParam(defaultValue = "false") Boolean latest,
            @Parameter(description = "指标名称") @RequestParam(required = false) String metric,
            @Parameter(description = "查询模式") @RequestParam(defaultValue = "all") String queryMode) {
        
        try {
            UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
            queryDTO.setCustomerId(customerId);
            queryDTO.setUserId(userId);
            queryDTO.setOrgId(orgId);
            queryDTO.setDeviceSn(deviceSn);
            queryDTO.setStartDate(startDate);
            queryDTO.setEndDate(endDate);
            queryDTO.setPage(page);
            queryDTO.setPageSize(pageSize);
            queryDTO.setLatest(latest);
            queryDTO.setMetric(metric);
            queryDTO.setQueryMode(queryMode);

            return queryHealthData(queryDTO);
            
        } catch (Exception e) {
            log.error("❌ 简化健康数据查询失败: {}", e.getMessage(), e);
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @GetMapping("/metrics/supported")
    @Operation(summary = "获取支持的健康指标", description = "根据客户ID获取支持的健康指标列表")
    public ResponseEntity<Map<String, Object>> getSupportedMetrics(
            @Parameter(description = "客户ID", required = true) @RequestParam Long customerId) {
        
        try {
            Set<String> metrics = configService.getSupportedMetrics(customerId);
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "data", metrics,
                "total", metrics.size(),
                "customerId", customerId,
                "timestamp", LocalDateTime.now()
            ));
            
        } catch (Exception e) {
            log.error("❌ 获取支持的健康指标失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @GetMapping("/metrics/config")
    @Operation(summary = "获取健康指标配置", description = "根据客户ID获取健康指标的详细配置")
    public ResponseEntity<Map<String, Object>> getHealthMetricsConfig(
            @Parameter(description = "客户ID", required = true) @RequestParam Long customerId) {
        
        try {
            var configs = configService.getHealthDataConfigs(customerId);
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "data", configs,
                "total", configs.size(),
                "customerId", customerId,
                "timestamp", LocalDateTime.now()
            ));
            
        } catch (Exception e) {
            log.error("❌ 获取健康指标配置失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @GetMapping("/metrics/filter")
    @Operation(summary = "过滤支持的健康指标", description = "从给定列表中过滤出客户支持的健康指标")
    public ResponseEntity<Map<String, Object>> filterSupportedMetrics(
            @Parameter(description = "客户ID", required = true) @RequestParam Long customerId,
            @Parameter(description = "指标列表", required = true) @RequestParam List<String> metrics) {
        
        try {
            List<String> supportedMetrics = configService.filterSupportedMetrics(customerId, metrics);
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "data", supportedMetrics,
                "total", supportedMetrics.size(),
                "originalTotal", metrics.size(),
                "customerId", customerId,
                "timestamp", LocalDateTime.now()
            ));
            
        } catch (Exception e) {
            log.error("❌ 过滤支持的健康指标失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @PostMapping("/cache/clear")
    @Operation(summary = "清除配置缓存", description = "清除指定客户的健康配置缓存")
    public ResponseEntity<Map<String, Object>> clearConfigCache(
            @Parameter(description = "客户ID") @RequestParam(required = false) Long customerId) {
        
        try {
            if (customerId != null) {
                configService.clearCustomerCache(customerId);
            } else {
                configService.clearAllCache();
            }
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", customerId != null ? 
                    "已清除客户 " + customerId + " 的配置缓存" : "已清除所有配置缓存",
                "timestamp", LocalDateTime.now()
            ));
            
        } catch (Exception e) {
            log.error("❌ 清除配置缓存失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }

    @GetMapping("/table/info")
    @Operation(summary = "获取表信息", description = "获取健康数据表的分表信息")
    public ResponseEntity<Map<String, Object>> getTableInfo(
            @Parameter(description = "开始时间") @RequestParam LocalDateTime startDate,
            @Parameter(description = "结束时间") @RequestParam LocalDateTime endDate) {
        
        try {
            // 使用工具类获取表信息
            com.ljwx.modules.health.util.HealthDataTableUtil tableUtil;
            List<String> tableNames = com.ljwx.modules.health.util.HealthDataTableUtil.getTableNames(startDate, endDate);
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "data", Map.of(
                    "tableNames", tableNames,
                    "startDate", startDate,
                    "endDate", endDate,
                    "crossMonth", !startDate.toLocalDate().withDayOfMonth(1)
                                  .equals(endDate.toLocalDate().withDayOfMonth(1)),
                    "tableCount", tableNames.size()
                ),
                "timestamp", LocalDateTime.now()
            ));
            
        } catch (Exception e) {
            log.error("❌ 获取表信息失败: {}", e.getMessage(), e);
            return ResponseEntity.internalServerError().body(Map.of(
                "success", false,
                "error", e.getMessage(),
                "timestamp", LocalDateTime.now()
            ));
        }
    }
}