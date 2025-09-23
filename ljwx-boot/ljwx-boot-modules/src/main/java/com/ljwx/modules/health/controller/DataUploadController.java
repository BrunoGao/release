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

import com.ljwx.common.api.vo.Result;
import com.ljwx.modules.health.upload.DataUpload;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 数据上传控制器 - 统一数据上传API入口
 * 支持健康数据、设备信息、通用事件等多种数据类型上传
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DataUploadController
 * @CreateTime 2024-12-16
 */
@Slf4j
@RestController
@RequestMapping("/api")
@Tag(name = "数据上传API", description = "统一数据上传接口，支持健康数据、设备信息、通用事件等")
public class DataUploadController {

    @Autowired
    private DataUpload dataUpload;

    /**
     * 健康数据上传 (替换upload_health_data)
     * 完整实现Python health_data_batch_processor.py功能
     * 支持快慢字段分离，自动处理到主表、日报表、周报表
     */
    @PostMapping("/health/upload")
    @Operation(summary = "健康数据上传", description = "支持快慢字段分离的健康数据上传，自动分表存储，完整迁移Python系统功能")
    public Result<Map<String, Object>> uploadHealthDataWithSeparation(@RequestBody Map<String, Object> healthData) {
        log.info("🚀 收到健康数据上传请求 (快慢字段分离模式)");
        
        try {
            // 使用完整迁移的Python系统功能
            return dataUpload.optimizedUploadHealthDataWithSeparation(healthData);
            
        } catch (Exception e) {
            log.error("❌ 优化健康数据上传失败", e);
            return Result.error("上传失败: " + e.getMessage());
        }
    }

    /**
     * 健康数据批量上传 (兼容模式)
     * 保持原有批量上传接口的向后兼容性
     */
    @PostMapping("/health/batch")
    @Operation(summary = "健康数据批量上传", description = "批量健康数据上传接口，保持向后兼容")
    public Result<Map<String, Object>> uploadHealthDataBatch(@RequestBody java.util.List<Map<String, Object>> healthDataList) {
        log.info("🚀 收到健康数据批量上传请求，数据量: {}", healthDataList.size());
        
        try {
            return dataUpload.uploadHealthData(healthDataList);
            
        } catch (Exception e) {
            log.error("❌ 传统批量健康数据上传失败", e);
            return Result.error("批量上传失败: " + e.getMessage());
        }
    }

    /**
     * 设备信息上传 (替换upload_device_info)
     * 支持多种设备信息字段格式，自动数据清洗和去重
     */
    @PostMapping("/device/upload")
    @Operation(summary = "设备信息上传", description = "支持多格式设备信息上传，自动数据验证和去重处理")
    public Result<Map<String, Object>> uploadDeviceInfo(@RequestBody java.util.List<Map<String, Object>> deviceDataList) {
        log.info("🚀 收到设备信息批量上传请求，数据量: {}", deviceDataList.size());
        
        try {
            return dataUpload.uploadDeviceInfo(deviceDataList);
            
        } catch (Exception e) {
            log.error("❌ 设备信息批量上传失败", e);
            return Result.error("设备信息上传失败: " + e.getMessage());
        }
    }

    /**
     * 通用事件上传 (替换upload_common_event)
     * 支持混合数据类型：健康数据、设备信息、告警数据等
     */
    @PostMapping("/alert/upload")
    @Operation(summary = "通用事件上传", description = "支持混合数据类型的通用事件上传，可包含健康数据、设备信息、告警等")
    public Result<Map<String, Object>> uploadCommonEvent(@RequestBody Map<String, Object> eventData) {
        log.info("🚀 收到通用事件上传请求");
        
        try {
            return dataUpload.uploadCommonEvent(eventData);
            
        } catch (Exception e) {
            log.error("❌ 通用事件上传失败", e);
            return Result.error("事件上传失败: " + e.getMessage());
        }
    }

    /**
     * 获取数据上传统计信息
     */
    @GetMapping("/stats")
    @Operation(summary = "获取数据上传统计信息", description = "查看数据上传处理器的运行统计信息")
    public Result<Map<String, Object>> getUploadStats() {
        try {
            Map<String, Object> stats = dataUpload.getOptimizerStats();
            return Result.ok(stats);
            
        } catch (Exception e) {
            log.error("❌ 获取数据上传统计信息失败", e);
            return Result.error("获取统计信息失败: " + e.getMessage());
        }
    }

    /**
     * 获取性能统计信息
     */
    @GetMapping("/performance")
    @Operation(summary = "获取性能统计信息", description = "查看数据处理的性能统计信息")
    public Result<Map<String, Object>> getPerformanceStats() {
        try {
            Map<String, Object> stats = dataUpload.getPerformanceStats();
            return Result.ok(stats);
            
        } catch (Exception e) {
            log.error("❌ 获取性能统计信息失败", e);
            return Result.error("获取性能统计信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取告警规则缓存统计信息
     */
    @GetMapping("/cache/stats")
    @Operation(summary = "获取告警规则缓存统计信息", description = "查看告警规则缓存管理器的详细统计信息")
    public Result<Map<String, Object>> getAlertCacheStats() {
        try {
            // 通过DataUpload获取BatchAlertProcessor的缓存统计
            Map<String, Object> stats = dataUpload.getOptimizerStats();
            return Result.ok(stats);
            
        } catch (Exception e) {
            log.error("❌ 获取告警缓存统计信息失败", e);
            return Result.error("获取告警缓存统计信息失败: " + e.getMessage());
        }
    }
}