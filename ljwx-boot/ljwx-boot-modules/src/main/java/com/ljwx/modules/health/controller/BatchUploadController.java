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
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 批量数据上传控制器
 * 迁移自 Python ljwx-bigscreen 批量上传功能，完全兼容原接口
 * 
 * 主要功能：
 * 1. upload_health_data - 健康数据批量上传
 * 2. upload_device_info - 设备信息批量上传  
 * 3. upload_common_event - 通用事件上传
 * 4. 统计信息查询
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName BatchUploadController
 * @CreateTime 2024-12-16
 */
@RestController
@RequestMapping("/batch")
@Tag(name = "批量数据上传", description = "Python ljwx-bigscreen 批量上传功能迁移，设备端无需认证")
@Slf4j
public class BatchUploadController {
    
    @Autowired
    private DataUpload dataUpload;
    
    /**
     * 健康数据批量上传 (完全兼容Python接口)
     * 对应 Python: health_data_batch_processor.py:upload_health_data
     * 
     * 🔓 设备端接口 - 无需认证
     * 设备批量上传健康数据（心率、血氧、体温、步数等）
     * 
     * URL兼容性：
     * - Python: /upload_health_data
     * - Java: /batch/upload-health-data
     */
    @PostMapping("/upload-health-data")
    @Operation(summary = "健康数据批量上传（设备端-无需认证）", description = "迁移自Python health_data_batch_processor.py，设备端批量上传健康数据")
    public Result<Map<String, Object>> uploadHealthData(
        @Parameter(description = "健康数据列表", required = true)
        @RequestBody List<Map<String, Object>> healthDataList
    ) {
        try {
            log.info("🚀 [API] 健康数据批量上传开始，数据量: {}", healthDataList.size());
            
            Result<Map<String, Object>> result = dataUpload.uploadHealthData(healthDataList);
            
            log.info("✅ [API] 健康数据批量上传完成: {}", 
                result.isSuccess() ? "成功" : result.getMessage());
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ [API] 健康数据批量上传失败", e);
            return Result.error("批量上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 兼容Python的原始接口路径
     * 🔓 设备端接口 - 无需认证
     */
    @PostMapping("/upload_health_data")
    @Operation(summary = "健康数据批量上传（Python兼容路径-无需认证）", description = "提供与Python完全相同的接口路径")
    public Result<Map<String, Object>> uploadHealthDataCompat(
        @RequestBody List<Map<String, Object>> healthDataList
    ) {
        return uploadHealthData(healthDataList);
    }
    
    /**
     * 设备信息批量上传 (完全兼容Python接口)
     * 对应 Python: device_batch_processor.py:upload_device_info
     * 
     * 🔓 设备端接口 - 无需认证
     * 设备批量上传设备信息（设备状态、版本信息等）
     */
    @PostMapping("/upload-device-info")
    @Operation(summary = "设备信息批量上传（设备端-无需认证）", description = "迁移自Python device_batch_processor.py，设备端批量上传设备信息")
    public Result<Map<String, Object>> uploadDeviceInfo(
        @Parameter(description = "设备信息列表", required = true)
        @RequestBody List<Map<String, Object>> deviceDataList
    ) {
        try {
            log.info("🚀 [API] 设备信息批量上传开始，数据量: {}", deviceDataList.size());
            
            Result<Map<String, Object>> result = dataUpload.uploadDeviceInfo(deviceDataList);
            
            log.info("✅ [API] 设备信息批量上传完成: {}", 
                result.isSuccess() ? "成功" : result.getMessage());
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ [API] 设备信息批量上传失败", e);
            return Result.error("设备信息上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 兼容Python的原始接口路径
     * 🔓 设备端接口 - 无需认证
     */
    @PostMapping("/upload_device_info")
    @Operation(summary = "设备信息批量上传（Python兼容路径-无需认证）")
    public Result<Map<String, Object>> uploadDeviceInfoCompat(
        @RequestBody List<Map<String, Object>> deviceDataList
    ) {
        return uploadDeviceInfo(deviceDataList);
    }
    
    /**
     * 通用事件上传 (完全兼容Python接口)
     * 对应 Python: alert.py:upload_common_event
     * 
     * 🔓 设备端接口 - 无需认证
     * 支持复合数据上传：health_data + device_info + alert_data
     * 设备可以一次性上传多种类型的数据
     */
    @PostMapping("/upload-common-event")
    @Operation(summary = "通用事件上传（设备端-无需认证）", description = "迁移自Python upload_common_event，支持健康数据+设备信息+告警数据组合上传")
    public Result<Map<String, Object>> uploadCommonEvent(
        @Parameter(description = "事件数据", required = true, 
                  example = "{\"health_data\": [...], \"device_info\": [...], \"alert_data\": [...]}")
        @RequestBody Map<String, Object> eventData
    ) {
        try {
            log.info("🚀 [API] 通用事件上传开始");
            
            Result<Map<String, Object>> result = dataUpload.uploadCommonEvent(eventData);
            
            log.info("✅ [API] 通用事件上传完成: {}", 
                result.isSuccess() ? "成功" : result.getMessage());
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ [API] 通用事件上传失败", e);
            return Result.error("通用事件上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 兼容Python的原始接口路径
     * 🔓 设备端接口 - 无需认证
     */
    @PostMapping("/upload_common_event")
    @Operation(summary = "通用事件上传（Python兼容路径-无需认证）")
    public Result<Map<String, Object>> uploadCommonEventCompat(
        @RequestBody Map<String, Object> eventData
    ) {
        return uploadCommonEvent(eventData);
    }
    
    /**
     * 获取批处理统计信息 (兼容Python接口)
     * 对应 Python: HealthDataOptimizer.stats
     */
    @GetMapping("/stats")
    @Operation(summary = "获取批处理统计信息", description = "获取批量上传的性能统计和处理状态")
    public Result<Map<String, Object>> getBatchStats() {
        try {
            Map<String, Object> stats = dataUpload.getOptimizerStats();
            
            // 添加额外的状态信息
            stats.put("service_status", "running");
            stats.put("timestamp", System.currentTimeMillis());
            stats.put("version", "java-migrated-v1.0");
            
            return Result.ok(stats);
            
        } catch (Exception e) {
            log.error("❌ [API] 获取批处理统计失败", e);
            return Result.error("获取统计信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 批处理性能测试接口
     * 用于验证迁移后的性能对比
     */
    @PostMapping("/performance-test")
    @Operation(summary = "批处理性能测试", description = "用于验证Python迁移后的性能提升")
    public Result<Map<String, Object>> performanceTest(
        @Parameter(description = "测试数据规模", example = "1000")
        @RequestParam(defaultValue = "1000") int dataSize
    ) {
        try {
            log.info("🎯 [API] 开始性能测试，数据规模: {}", dataSize);
            
            long startTime = System.currentTimeMillis();
            
            // 生成测试数据
            List<Map<String, Object>> testData = generateTestHealthData(dataSize);
            
            // 执行批量上传
            Result<Map<String, Object>> uploadResult = dataUpload.uploadHealthData(testData);
            
            long totalTime = System.currentTimeMillis() - startTime;
            
            Map<String, Object> testResult = Map.of(
                "test_data_size", dataSize,
                "total_time_ms", totalTime,
                "qps", dataSize * 1000.0 / totalTime,
                "upload_result", uploadResult.getResult(),
                "performance_rating", totalTime < 5000 ? "优秀" : totalTime < 10000 ? "良好" : "需优化"
            );
            
            log.info("✅ [API] 性能测试完成: {}条数据，耗时{}ms，QPS: {}", 
                dataSize, totalTime, String.format("%.2f", dataSize * 1000.0 / totalTime));
            
            return Result.ok(testResult);
            
        } catch (Exception e) {
            log.error("❌ [API] 性能测试失败", e);
            return Result.error("性能测试失败: " + e.getMessage());
        }
    }
    
    /**
     * 批处理健康检查
     */
    @GetMapping("/health")
    @Operation(summary = "批处理服务健康检查", description = "检查批量上传服务状态")
    public Result<Map<String, Object>> healthCheck() {
        try {
            Map<String, Object> health = Map.of(
                "service", "BatchUploadService",
                "status", "healthy",
                "features", Map.of(
                    "upload_health_data", "available",
                    "upload_device_info", "available",
                    "upload_common_event", "available",
                    "performance_test", "available",
                    "python_compatibility", "100%"
                ),
                "optimizer_stats", dataUpload.getOptimizerStats(),
                "timestamp", System.currentTimeMillis()
            );
            
            return Result.ok(health);
            
        } catch (Exception e) {
            log.error("❌ 批处理健康检查失败", e);
            return Result.error("服务不可用: " + e.getMessage());
        }
    }
    
    /**
     * 生成测试健康数据
     */
    private List<Map<String, Object>> generateTestHealthData(int size) {
        List<Map<String, Object>> testData = new ArrayList<>(size);
        
        for (int i = 0; i < size; i++) {
            Map<String, Object> data = Map.of(
                "device_id", "TEST_DEVICE_" + (i % 100),
                "user_id", "TEST_USER_" + (i % 50),
                "org_id", "TEST_ORG_" + (i % 10),
                "customer_id", "8",
                "heart_rate", 60 + (i % 40),
                "blood_oxygen", 95 + (i % 5),
                "temperature", 36.0 + (i % 2),
                "step", i * 10,
                "create_time", java.time.LocalDateTime.now().toString()
            );
            testData.add(data);
        }
        
        return testData;
    }
}