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

import com.ljwx.common.api.Result;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Health Feature Controller 健康特征控制器
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName health.controller.com.ljwx.admin.HealthFeatureController
 * @CreateTime 2025-08-18
 */
@Slf4j
@RestController
@Tag(name = "健康特征管理")
@RequiredArgsConstructor
@RequestMapping("health/feature")
public class HealthFeatureController {

    @NonNull
    private ITHealthDataConfigService healthDataConfigService;

    @Operation(summary = "获取基础健康特征列表")
    @GetMapping(value = "/base")
    public Result<List<Map<String, String>>> getBaseFeatures(@RequestParam("customerId") Long customerId) {
        try {
            log.info("📈 获取基础健康特征配置 - customerId: {}", customerId);
            
            // 直接使用customerId查询t_health_data_config表获取基础体征配置
            List<THealthDataConfig> configs = healthDataConfigService.getBaseConfigsByCustomerId(customerId);
            
            log.info("✅ 查询到 {} 个基础体征配置", configs.size());
            configs.forEach(config -> 
                log.debug("  - {}: {} (enabled: {}, weight: {})", 
                    config.getDataType(), getDataTypeLabel(config.getDataType()), 
                    config.getIsEnabled(), config.getWeight())
            );

            List<Map<String, String>> features = configs.stream()
                .map(config -> {
                    Map<String, String> feature = new HashMap<>();
                    String dataType = config.getDataType();
                    feature.put("value", dataType);
                    feature.put("label", getDataTypeLabel(dataType));
                    return feature;
                })
                .collect(Collectors.toList());

            return Result.data(features);
        } catch (Exception e) {
            log.error("❌ 获取基础健康特征失败 - customerId: {}", customerId, e);
            return Result.failure("获取健康特征失败");
        }
    }

    @Operation(summary = "获取全量健康特征列表")
    @GetMapping(value = "/full")
    public Result<List<Map<String, String>>> getFullFeatures(@RequestParam("customerId") Long customerId) {
        try {
            log.info("📈 获取全量健康特征配置 - customerId: {}", customerId);
            
            // 直接使用customerId查询t_health_data_config表获取所有启用的特征配置
            List<THealthDataConfig> configs = healthDataConfigService.getEnabledConfigsByCustomerId(customerId);
            
            log.info("✅ 查询到 {} 个全量特征配置", configs.size());

            List<Map<String, String>> features = configs.stream()
                .map(config -> {
                    Map<String, String> feature = new HashMap<>();
                    String dataType = config.getDataType();
                    feature.put("value", dataType);
                    feature.put("label", getDataTypeLabel(dataType));
                    return feature;
                })
                .collect(Collectors.toList());

            return Result.data(features);
        } catch (Exception e) {
            log.error("❌ 获取全量健康特征失败 - customerId: {}", customerId, e);
            return Result.failure("获取健康特征失败");
        }
    }

    @Operation(summary = "获取特征映射关系")
    @GetMapping(value = "/mapping")
    public Result<Map<String, String[]>> getFeatureMapping() {
        Map<String, String[]> mapping = new HashMap<>();
        mapping.put("heart_rate", new String[]{"心率"});
        mapping.put("blood_oxygen", new String[]{"血氧"});
        mapping.put("temperature", new String[]{"体温"});
        mapping.put("blood_pressure", new String[]{"血压"});
        mapping.put("step", new String[]{"步数"});
        mapping.put("sleep", new String[]{"睡眠"});
        mapping.put("stress", new String[]{"压力"});
        mapping.put("calorie", new String[]{"卡路里"});
        mapping.put("distance", new String[]{"距离"});
        
        return Result.data(mapping);
    }

    private String getDataTypeLabel(String dataType) {
        switch (dataType) {
            case "heart_rate": return "心率";
            case "blood_oxygen": return "血氧";
            case "temperature": return "体温";
            case "blood_pressure": return "血压";
            case "step": return "步数";
            case "sleep": return "睡眠";
            case "stress": return "压力";
            case "calorie": return "卡路里";
            case "distance": return "距离";
            default: return dataType;
        }
    }
}