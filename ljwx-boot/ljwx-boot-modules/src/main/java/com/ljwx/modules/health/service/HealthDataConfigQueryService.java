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

package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.customer.repository.mapper.THealthDataConfigMapper;
import com.ljwx.modules.system.service.ISysOrgClosureService;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * 健康数据配置统一查询服务
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.HealthDataConfigQueryService
 * @CreateTime 2025-09-08
 */
@Slf4j
@Service
public class HealthDataConfigQueryService {

    @Autowired
    private THealthDataConfigMapper healthDataConfigMapper;

    @Autowired
    private ISysOrgClosureService sysOrgClosureService;

    // 本地缓存，避免频繁查询数据库
    private final Map<Long, HealthMetricsResult> customerMetricsCache = new ConcurrentHashMap<>();

    /**
     * 健康指标结果数据结构
     */
    @Data
    public static class HealthMetricsResult {
        private Set<String> fullEnabledMetrics;        // 所有启用的指标（给客户端表格用）
        private Set<String> basicEnabledMetrics;       // 基础启用的指标（用于数据分析）
        private List<String> actualDatabaseFields;     // 实际数据库字段
        private Map<String, BigDecimal> metricWeights; // 指标权重
        private Map<String, THealthDataConfig> configMap; // 配置映射
    }

    /**
     * 基础健康指标定义 - 对应 t_user_health_data 快字段，用于数据分析
     * 包括主表快字段和daily/weekly慢字段
     */
    private static final Set<String> BASIC_METRICS = Set.of(
        // 主表快字段
        "heart_rate",         // 心率
        "blood_oxygen",       // 血氧
        "temperature",        // 体温
        "step",              // 步数
        "distance",          // 距离
        "calorie",           // 卡路里
        "stress",            // 压力
        "pressure_high",     // 收缩压
        "pressure_low",      // 舒张压
        "location",          // 位置坐标
        
        // Daily表慢字段 - 支持多种命名方式
        "sleepData",         // 睡眠数据（驼峰命名）
        "sleep",             // 睡眠数据（下划线命名）
        "exerciseDailyData", // 日常运动数据（驼峰命名）
        "exercise_daily",    // 日常运动数据（下划线命名）
        "workoutData",       // 锻炼数据（驼峰命名）  
        "work_out",          // 锻炼数据（下划线命名）
        "scientificSleepData", // 科学睡眠数据（驼峰命名）
        "scientific_sleep",  // 科学睡眠数据（下划线命名）
        
        // Weekly表慢字段
        "exerciseWeekData",  // 周运动数据（驼峰命名）
        "exercise_week"      // 周运动数据（下划线命名）
    );

    /**
     * 默认权重，用于没有配置权重的指标
     */
    private static final BigDecimal DEFAULT_WEIGHT = new BigDecimal("0.05");

    /**
     * 获取客户健康指标完整信息（支持的指标、实际数据库字段、权重配置）
     */
    @Cacheable(value = "health_metrics_complete", key = "#customerId")
    public HealthMetricsResult getHealthMetricsComplete(Long customerId) {
        try {
            // 验证并获取真实的顶级customerId
            Long actualCustomerId = validateAndGetTopLevelCustomerId(customerId);
            if (actualCustomerId == null) {
                log.warn("无法获取有效的顶级customerId: {}", customerId);
                return getEmptyHealthMetricsResult();
            }
            
            // 先检查本地缓存
            if (customerMetricsCache.containsKey(actualCustomerId)) {
                return customerMetricsCache.get(actualCustomerId);
            }

            // 直接查询数据库
            LambdaQueryWrapper<THealthDataConfig> query = new LambdaQueryWrapper<>();
            query.eq(THealthDataConfig::getCustomerId, actualCustomerId)
                 .eq(THealthDataConfig::getIsEnabled, 1)
                 .eq(THealthDataConfig::getIsDeleted, 0);

            List<THealthDataConfig> configs = healthDataConfigMapper.selectList(query);
            
            // 构建结果
            HealthMetricsResult result = buildHealthMetricsResult(configs, actualCustomerId);
            
            // 缓存结果
            customerMetricsCache.put(actualCustomerId, result);
            
            log.debug("客户 {} (实际customerId: {}) 健康指标完整信息: 全部启用{}个指标, 基础启用{}个指标, 实际字段{}个", 
                customerId, actualCustomerId, result.getFullEnabledMetrics().size(), 
                result.getBasicEnabledMetrics().size(), result.getActualDatabaseFields().size());
            
            return result;
            
        } catch (Exception e) {
            log.error("获取客户 {} 健康指标完整信息失败: {}", customerId, e.getMessage(), e);
            return getEmptyHealthMetricsResult();
        }
    }

    /**
     * 获取所有启用的健康指标列表（给客户端表格用）
     */
    public Set<String> getFullEnabledMetrics(Long customerId) {
        return getHealthMetricsComplete(customerId).getFullEnabledMetrics();
    }

    /**
     * 获取基础启用的健康指标列表（用于数据分析）
     */
    public Set<String> getBasicEnabledMetrics(Long customerId) {
        return getHealthMetricsComplete(customerId).getBasicEnabledMetrics();
    }

    /**
     * 获取客户支持的健康指标列表（向后兼容）
     */
    public Set<String> getSupportedMetrics(Long customerId) {
        return getFullEnabledMetrics(customerId);
    }

    /**
     * 获取客户健康指标配置详情（向后兼容）
     */
    public Map<String, THealthDataConfig> getHealthDataConfigs(Long customerId) {
        return getHealthMetricsComplete(customerId).getConfigMap();
    }

    /**
     * 获取指标权重信息
     */
    public Map<String, BigDecimal> getMetricWeights(Long customerId) {
        return getHealthMetricsComplete(customerId).getMetricWeights();
    }

    /**
     * 获取指定指标的配置
     */
    public THealthDataConfig getMetricConfig(Long customerId, String metricName) {
        Map<String, THealthDataConfig> configs = getHealthDataConfigs(customerId);
        return configs.get(metricName);
    }

    /**
     * 检查指标是否被支持
     */
    public boolean isMetricSupported(Long customerId, String metricName) {
        return getSupportedMetrics(customerId).contains(metricName);
    }

    /**
     * 过滤支持的指标
     */
    public List<String> filterSupportedMetrics(Long customerId, List<String> metrics) {
        Set<String> supported = getSupportedMetrics(customerId);
        return metrics.stream()
                .filter(supported::contains)
                .collect(Collectors.toList());
    }

    /**
     * 获取实际数据库字段映射（处理特殊字段映射规则）- 优化版本
     */
    public List<String> getActualDatabaseFields(Long customerId, List<String> requestedFields) {
        HealthMetricsResult metricsResult = getHealthMetricsComplete(customerId);
        return metricsResult.getActualDatabaseFields().stream()
                .filter(field -> requestedFields.isEmpty() || 
                        requestedFields.stream().anyMatch(requested -> isFieldRelated(requested, field)))
                .collect(Collectors.toList());
    }

    /**
     * 检查字段是否相关
     */
    private boolean isFieldRelated(String requestedField, String actualField) {
        // 直接匹配
        if (requestedField.equals(actualField)) {
            return true;
        }
        // heart_rate 包含 pressure_high 和 pressure_low
        if ("heart_rate".equals(requestedField) && 
            (actualField.equals("pressure_high") || actualField.equals("pressure_low"))) {
            return true;
        }
        // location 包含 latitude, longitude, altitude
        if ("location".equals(requestedField) && 
            (actualField.equals("latitude") || actualField.equals("longitude") || actualField.equals("altitude"))) {
            return true;
        }
        return false;
    }

    /**
     * 获取指标的单位 (实体类中暂无此字段)
     */
    public String getMetricUnit(Long customerId, String metricName) {
        // TODO: 实体类中暂无unit字段，返回默认值
        return getDefaultUnit(metricName);
    }

    /**
     * 获取指标的权重
     */
    public Double getMetricWeight(Long customerId, String metricName) {
        THealthDataConfig config = getMetricConfig(customerId, metricName);
        return config != null && config.getWeight() != null ? config.getWeight().doubleValue() : 0.15; // 默认权重
    }

    /**
     * 获取指标的正常范围 (基于存在的字段)
     */
    public Map<String, Object> getMetricRange(Long customerId, String metricName) {
        THealthDataConfig config = getMetricConfig(customerId, metricName);
        if (config == null) return Map.of();
        
        // 使用实际存在的字段
        Map<String, Object> range = getDefaultRange(metricName);
        range.put("warning_low", config.getWarningLow() != null ? config.getWarningLow() : 0);
        range.put("warning_high", config.getWarningHigh() != null ? config.getWarningHigh() : 1000);
        
        return range;
    }

    /**
     * 清除指定客户的缓存
     */
    public void clearCustomerCache(Long customerId) {
        customerMetricsCache.remove(customerId);
        log.info("已清除客户 {} 的配置缓存", customerId);
    }

    /**
     * 清除所有缓存
     */
    public void clearAllCache() {
        customerMetricsCache.clear();
        log.info("已清除所有配置缓存");
    }

    /**
     * 构建健康指标结果对象 - 双列表系统
     */
    private HealthMetricsResult buildHealthMetricsResult(List<THealthDataConfig> configs, Long customerId) {
        HealthMetricsResult result = new HealthMetricsResult();
        
        // 1. 获取所有启用的指标（Full Enabled Metrics）
        Set<String> fullEnabledMetrics = new HashSet<>();
        Map<String, BigDecimal> metricWeights = new HashMap<>();
        Map<String, THealthDataConfig> configMap = new HashMap<>();
        
        // 处理客户配置的指标
        for (THealthDataConfig config : configs) {
            String dataType = config.getDataType();
            fullEnabledMetrics.add(dataType);
            configMap.put(dataType, config);
            
            // 使用配置的权重，如果没有配置权重则使用默认值
            BigDecimal weight = (config.getWeight() != null && config.getWeight().compareTo(BigDecimal.ZERO) > 0) 
                ? config.getWeight() 
                : DEFAULT_WEIGHT;
            metricWeights.put(dataType, weight);
        }
        
        // 2. 计算基础启用的指标（Basic Enabled Metrics = Basic ∩ Full Enabled）
        Set<String> basicEnabledMetrics = new HashSet<>(BASIC_METRICS);
        
        // 添加调试日志：显示交集计算前的状态
        log.info("🔍 字段匹配调试 - 客户{}: BASIC_METRICS={}, fullEnabledMetrics={}", 
                customerId, BASIC_METRICS, fullEnabledMetrics);
        
        basicEnabledMetrics.retainAll(fullEnabledMetrics); // 取交集
        
        // 添加调试日志：显示交集计算后的结果
        log.info("🔍 字段匹配结果 - 客户{}: basicEnabledMetrics={}", customerId, basicEnabledMetrics);
        
        // 如果没有任何配置，返回空结果
        if (fullEnabledMetrics.isEmpty()) {
            log.warn("客户 {} 没有配置任何健康指标", customerId);
            return getEmptyHealthMetricsResult();
        }
        
        // 3. 构建实际数据库字段（基于所有启用的指标）
        List<String> actualDatabaseFields = buildActualDatabaseFields(fullEnabledMetrics);
        
        result.setFullEnabledMetrics(fullEnabledMetrics);
        result.setBasicEnabledMetrics(basicEnabledMetrics);
        result.setActualDatabaseFields(actualDatabaseFields);
        result.setMetricWeights(metricWeights);
        result.setConfigMap(configMap);
        
        log.debug("客户 {} 构建结果: 全部启用指标={}, 基础启用指标={}, 实际字段={}, 权重数={}", 
            customerId, fullEnabledMetrics.size(), basicEnabledMetrics.size(), 
            actualDatabaseFields.size(), metricWeights.size());
        
        return result;
    }

    /**
     * 构建实际数据库字段列表（应用映射规则）
     */
    private List<String> buildActualDatabaseFields(Set<String> supportedMetrics) {
        Set<String> actualFields = new HashSet<>();
        
        for (String metric : supportedMetrics) {
            // 规则1: location不是真实字段，映射为latitude、longitude、altitude
            if ("location".equals(metric)) {
                actualFields.add("latitude");
                actualFields.add("longitude");
                actualFields.add("altitude");
                continue;
            }
            
            // 规则2: heart_rate同时包含pressure_low和pressure_high
            if ("heart_rate".equals(metric)) {
                actualFields.add("heart_rate");
                actualFields.add("pressure_low");
                actualFields.add("pressure_high");
                continue;
            }
            
            // 规则3: 忽略ecg和wear字段
            if ("ecg".equals(metric) || "wear".equals(metric)) {
                log.debug("忽略字段: {}", metric);
                continue;
            }
            
            // 其他字段直接添加
            actualFields.add(metric);
        }
        
        return new ArrayList<>(actualFields);
    }

    /**
     * 获取空的健康指标结果（降级处理）
     */
    private HealthMetricsResult getEmptyHealthMetricsResult() {
        HealthMetricsResult result = new HealthMetricsResult();
        result.setFullEnabledMetrics(new HashSet<>());
        result.setBasicEnabledMetrics(new HashSet<>());
        result.setActualDatabaseFields(new ArrayList<>());
        result.setMetricWeights(new HashMap<>());
        result.setConfigMap(new HashMap<>());
        return result;
    }

    /**
     * 获取默认支持的健康指标（向后兼容）- 返回空集合，强制从数据库读取
     */
    private Set<String> getDefaultMetrics() {
        log.warn("调用了getDefaultMetrics方法，应该从数据库配置中读取指标");
        return new HashSet<>();
    }
    
    /**
     * 获取指标的默认单位
     */
    private String getDefaultUnit(String metricName) {
        Map<String, String> defaultUnits = Map.of(
            "heart_rate", "bpm",
            "blood_oxygen", "%",
            "temperature", "°C", 
            "pressure_high", "mmHg",
            "pressure_low", "mmHg",
            "stress", "级",
            "step", "步",
            "calorie", "卡",
            "distance", "米",
            "sleep", "分钟"
        );
        return defaultUnits.getOrDefault(metricName, "");
    }
    
    /**
     * 获取指标的默认范围
     */
    private Map<String, Object> getDefaultRange(String metricName) {
        Map<String, Map<String, Object>> defaultRanges = Map.of(
            "heart_rate", Map.of("min", 50, "max", 150),
            "blood_oxygen", Map.of("min", 90, "max", 100),
            "temperature", Map.of("min", 36.0, "max", 37.5),
            "pressure_high", Map.of("min", 90, "max", 140),
            "pressure_low", Map.of("min", 60, "max", 90),
            "stress", Map.of("min", 0, "max", 100),
            "step", Map.of("min", 0, "max", 50000),
            "calorie", Map.of("min", 0, "max", 5000),
            "distance", Map.of("min", 0, "max", 50000),
            "sleep", Map.of("min", 300, "max", 600)
        );
        return defaultRanges.getOrDefault(metricName, Map.of("min", 0, "max", 1000));
    }

    /**
     * 获取快表指标列表
     */
    public Set<String> getFastTableMetrics() {
        return Set.of(
            "sleep_data", "exercise_daily_data", 
            "workout_data", "scientific_sleep_data"
        );
    }

    /**
     * 获取周表指标列表
     */
    public Set<String> getWeeklyTableMetrics() {
        return Set.of("exercise_week_data");
    }

    /**
     * 检查是否需要查询日汇总表
     */
    public boolean needsDailyTable(List<String> metrics) {
        Set<String> fastMetrics = getFastTableMetrics();
        return metrics.stream().anyMatch(fastMetrics::contains);
    }

    /**
     * 检查是否需要查询周汇总表
     */
    public boolean needsWeeklyTable(List<String> metrics) {
        Set<String> weeklyMetrics = getWeeklyTableMetrics();
        return metrics.stream().anyMatch(weeklyMetrics::contains);
    }

    /**
     * 验证并获取真实的顶级customerId
     * 如果传入的是orgId，会自动转换为对应的顶级customerId
     */
    private Long validateAndGetTopLevelCustomerId(Long inputId) {
        if (inputId == null) {
            return null;
        }
        
        try {
            // 尝试获取顶级customerId，如果传入的是orgId，会返回对应的顶级customerId
            // 如果传入的本身就是顶级customerId，也会正确返回
            Long topLevelCustomerId = sysOrgClosureService.getTopLevelCustomerIdByOrgId(inputId);
            
            if (topLevelCustomerId != null) {
                if (!topLevelCustomerId.equals(inputId)) {
                    log.debug("输入ID {} 转换为顶级customerId: {}", inputId, topLevelCustomerId);
                }
                return topLevelCustomerId;
            } else {
                // 如果闭包表中找不到，可能传入的就是顶级customerId，直接返回
                log.debug("输入ID {} 在闭包表中未找到，假设为顶级customerId", inputId);
                return inputId;
            }
            
        } catch (Exception e) {
            log.warn("验证customerId时出错，使用原始值: inputId={}, error={}", inputId, e.getMessage());
            return inputId;
        }
    }
}