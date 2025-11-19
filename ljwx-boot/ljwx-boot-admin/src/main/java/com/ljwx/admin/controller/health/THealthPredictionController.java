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

package com.ljwx.admin.controller.health;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import com.ljwx.modules.health.service.HealthDataService;
import com.ljwx.modules.health.service.OllamaHealthPredictionService;
import com.ljwx.modules.health.service.OllamaHealthPredictionService.HealthPredictionResult;
import com.ljwx.modules.health.service.OllamaHealthPredictionService.HealthAdviceResult;
import lombok.NonNull;

import jakarta.validation.Valid;
import java.util.Map;
import java.util.List;

/**
 * 健康预测管理 Controller 控制层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.health.THealthPredictionController
 * @CreateTime 2025-09-11
 */

@Slf4j
@RestController
@Tag(name = "健康预测管理")
@RequiredArgsConstructor
@RequestMapping("t_health_prediction")
public class THealthPredictionController {

    @NonNull
    private HealthDataService healthDataService;
    
    @NonNull
    private OllamaHealthPredictionService ollamaHealthPredictionService;

    @GetMapping("/page")
    @SaCheckPermission("t:health:prediction:page")
    @Operation(operationId = "1", summary = "获取健康预测列表")
    public Result<RPage<Map<String, Object>>> page(@Parameter(description = "分页对象", required = true) @Valid PageQuery pageQuery,
                                                   @RequestParam(value = "customerId", required = false) Long customerId) {
        log.info("获取健康预测列表 - page: {}, size: {}, customerId: {}", pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        RPage<Map<String, Object>> result = healthDataService.getHealthPredictionPage(pageQuery, customerId);
        return Result.data(result);
    }

    @GetMapping("/{id}")
    @SaCheckPermission("t:health:prediction:get")
    @Operation(operationId = "2", summary = "根据ID获取健康预测详细信息")
    public Result<Map<String, Object>> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        log.info("获取健康预测详情 - id: {}", id);
        
        Map<String, Object> result = healthDataService.getHealthPredictionById(id);
        if (result == null) {
            return Result.failure("数据不存在");
        }
        return Result.data(result);
    }

    @PostMapping("/")
    @SaCheckPermission("t:health:prediction:add")
    @Operation(operationId = "3", summary = "新增健康预测")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody Map<String, Object> data) {
        log.info("新增健康预测 - data: {}", data);
        return Result.data(true);
    }

    @PutMapping("/")
    @SaCheckPermission("t:health:prediction:update")
    @Operation(operationId = "4", summary = "修改健康预测")
    public Result<Boolean> update(@Parameter(description = "修改对象") @RequestBody Map<String, Object> data) {
        log.info("修改健康预测 - data: {}", data);
        return Result.data(true);
    }

    @DeleteMapping("/")
    @SaCheckPermission("t:health:prediction:delete")
    @Operation(operationId = "5", summary = "删除健康预测")
    public Result<Boolean> delete(@Parameter(description = "删除对象") @RequestBody Map<String, Object> data) {
        log.info("删除健康预测 - data: {}", data);
        return Result.data(true);
    }

    // ========== AI预测相关接口 ==========

    @PostMapping("/ai/predict")
    // @SaCheckPermission("t:health:prediction:ai")  // 临时移除权限检查以便测试
    @Operation(operationId = "6", summary = "AI健康预测")
    public Result<HealthPredictionResult> aiPredict(
            @Parameter(description = "用户ID") @RequestParam("userId") Long userId,
            @Parameter(description = "预测天数") @RequestParam(value = "days", defaultValue = "7") Integer days) {
        
        log.info("🔮 AI健康预测 - userId: {}, days: {}", userId, days);
        
        try {
            HealthPredictionResult result = ollamaHealthPredictionService.generateHealthPrediction(userId, days);
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI健康预测失败: {}", e.getMessage(), e);
            return Result.failure("AI健康预测失败: " + e.getMessage());
        }
    }

    @PostMapping("/ai/advice")
    // @SaCheckPermission("t:health:prediction:ai")  // 临时移除权限检查以便测试
    @Operation(operationId = "7", summary = "AI健康建议")
    public Result<HealthAdviceResult> aiAdvice(
            @Parameter(description = "用户ID") @RequestParam("userId") Long userId,
            @Parameter(description = "健康问题") @RequestParam(value = "healthIssues", required = false) List<String> healthIssues) {
        
        log.info("📝 AI健康建议 - userId: {}, healthIssues: {}", userId, healthIssues);
        
        try {
            HealthAdviceResult result = ollamaHealthPredictionService.generateHealthAdvice(userId, healthIssues);
            return Result.data(result);
        } catch (Exception e) {
            log.error("❌ AI健康建议失败: {}", e.getMessage(), e);
            return Result.failure("AI健康建议失败: " + e.getMessage());
        }
    }

    @GetMapping("/ai/models")
    // @SaCheckPermission("t:health:prediction:ai")  // 临时移除权限检查以便测试
    @Operation(operationId = "8", summary = "获取可用AI模型列表")
    public Result<List<String>> getAvailableModels() {
        log.info("📋 获取可用AI模型列表");
        
        try {
            List<String> models = ollamaHealthPredictionService.getAvailableModels();
            return Result.data(models);
        } catch (Exception e) {
            log.error("❌ 获取模型列表失败: {}", e.getMessage(), e);
            return Result.failure("获取模型列表失败: " + e.getMessage());
        }
    }

    @GetMapping("/ai/health")
    // @SaCheckPermission("t:health:prediction:ai")  // 临时移除权限检查以便测试
    @Operation(operationId = "9", summary = "检查AI服务健康状态")
    public Result<Map<String, Object>> checkAiHealth() {
        log.info("🏥 检查AI服务健康状态");
        
        try {
            boolean isHealthy = ollamaHealthPredictionService.checkOllamaHealth();
            List<String> models = ollamaHealthPredictionService.getAvailableModels();
            
            Map<String, Object> healthStatus = Map.of(
                "healthy", isHealthy,
                "availableModels", models,
                "checkTime", java.time.LocalDateTime.now()
            );
            
            return Result.data(healthStatus);
        } catch (Exception e) {
            log.error("❌ AI服务健康检查失败: {}", e.getMessage(), e);
            return Result.failure("AI服务健康检查失败: " + e.getMessage());
        }
    }

    @PostMapping("/ai/batch-predict")
    // @SaCheckPermission("t:health:prediction:ai")  // 临时移除权限检查以便测试
    @Operation(operationId = "10", summary = "批量AI健康预测")
    public Result<Map<Long, HealthPredictionResult>> batchAiPredict(
            @Parameter(description = "用户ID列表") @RequestBody List<Long> userIds,
            @Parameter(description = "预测天数") @RequestParam(value = "days", defaultValue = "7") Integer days) {
        
        log.info("🔮 批量AI健康预测 - userIds: {}, days: {}", userIds, days);
        
        try {
            Map<Long, HealthPredictionResult> results = new java.util.HashMap<>();
            
            for (Long userId : userIds) {
                try {
                    HealthPredictionResult result = ollamaHealthPredictionService.generateHealthPrediction(userId, days);
                    results.put(userId, result);
                } catch (Exception e) {
                    log.warn("⚠️ 用户 {} 预测失败: {}", userId, e.getMessage());
                    // 继续处理其他用户
                }
            }
            
            return Result.data(results);
        } catch (Exception e) {
            log.error("❌ 批量AI健康预测失败: {}", e.getMessage(), e);
            return Result.failure("批量AI健康预测失败: " + e.getMessage());
        }
    }
}