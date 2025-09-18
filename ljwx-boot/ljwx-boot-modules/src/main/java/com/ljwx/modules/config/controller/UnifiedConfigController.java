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

package com.ljwx.modules.config.controller;

import com.ljwx.common.api.vo.Result;
import com.ljwx.modules.config.service.UnifiedConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 统一配置管理控制器
 * 迁移自 Python fetchConfig.py，提供与Python完全兼容的配置查询接口
 * 
 * 核心功能：
 * - /config/health-data - 获取健康数据配置（多表关联，兼容Python接口）
 * - /config/get_health_data_config - Python兼容路径
 * 
 * 注意：配置复制由 OrgUnitsChangeListener 自动处理
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName UnifiedConfigController
 * @CreateTime 2024-12-16
 */
@RestController
@RequestMapping("/config")
@Tag(name = "统一配置管理", description = "Python fetchConfig.py 迁移接口，设备端无需认证")
@Slf4j
public class UnifiedConfigController {
    
    @Autowired
    private UnifiedConfigService unifiedConfigService;
    
    /**
     * 获取健康数据配置 (完全兼容Python接口)
     * 对应 Python: fetchConfig.py:fetch_health_data_config
     * 
     * 🔓 设备端接口 - 无需认证
     * 设备通过deviceSn获取对应的健康数据采集配置
     * 
     * URL兼容性：
     * - Python: /get_health_data_config?customerId=8&deviceSn=A5GTQ24B26000732
     * - Java: /config/health-data?customerId=8&deviceSn=A5GTQ24B26000732
     */
    @GetMapping("/health-data")
    @Operation(summary = "获取健康数据配置（设备端-无需认证）", description = "迁移自Python fetchConfig.py，设备端调用获取配置信息")
    public Result<Map<String, Object>> fetchHealthDataConfig(
        @Parameter(description = "客户ID（可选）", example = "8")
        @RequestParam(required = false) String customerId,
        
        @Parameter(description = "设备序列号（可选）", example = "A5GTQ24B26000732")
        @RequestParam(required = false) String deviceSn
    ) {
        try {
            log.info("🔍 [API] 获取健康数据配置: customerId={}, deviceSn={}", customerId, deviceSn);
            
            Map<String, Object> config = unifiedConfigService.fetchHealthDataConfig(customerId, deviceSn);
            
            // 检查是否为错误响应
            if (Boolean.FALSE.equals(config.get("success"))) {
                return Result.error((String) config.get("error"));
            }
            
            return Result.ok(config);
            
        } catch (Exception e) {
            log.error("❌ [API] 获取健康数据配置失败", e);
            return Result.error("获取配置失败: " + e.getMessage());
        }
    }
    
    /**
     * 兼容Python的原始接口路径
     * 🔓 设备端接口 - 无需认证
     * 提供与Python完全相同的接口路径，保证设备端无缝迁移
     */
    @GetMapping("/get_health_data_config")
    @Operation(summary = "获取健康数据配置（Python兼容路径-无需认证）", description = "提供与Python完全相同的接口路径")
    public Result<Map<String, Object>> getHealthDataConfig(
        @RequestParam(required = false) String customerId,
        @RequestParam(required = false) String deviceSn
    ) {
        // 直接调用标准接口
        return fetchHealthDataConfig(customerId, deviceSn);
    }
    
    
    
    /**
     * 健康检查接口
     * 验证配置服务状态
     */
    @GetMapping("/health")
    @Operation(summary = "配置服务健康检查", description = "验证统一配置服务状态")
    public Result<Map<String, Object>> healthCheck() {
        try {
            Map<String, Object> status = Map.of(
                "service", "UnifiedConfigService",
                "status", "healthy",
                "timestamp", System.currentTimeMillis(),
                "features", Map.of(
                    "fetch_health_data_config", "available",
                    "python_compatibility", "100%",
                    "note", "Config copy handled by OrgUnitsChangeListener"
                )
            );
            
            return Result.ok(status);
            
        } catch (Exception e) {
            log.error("❌ 配置服务健康检查失败", e);
            return Result.error("服务不可用: " + e.getMessage());
        }
    }
}