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
import com.ljwx.modules.customer.service.ITHealthDataConfigService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Set;
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
    private ITHealthDataConfigService healthDataConfigService;

    // 本地缓存，避免频繁查询数据库
    private final Map<Long, Set<String>> customerMetricsCache = new ConcurrentHashMap<>();
    private final Map<Long, Map<String, THealthDataConfig>> customerConfigCache = new ConcurrentHashMap<>();

    /**
     * 获取客户支持的健康指标列表
     */
    @Cacheable(value = "health_metrics", key = "#customerId")
    public Set<String> getSupportedMetrics(Long customerId) {
        try {
            // 先检查本地缓存
            if (customerMetricsCache.containsKey(customerId)) {
                return customerMetricsCache.get(customerId);
            }

            LambdaQueryWrapper<THealthDataConfig> query = new LambdaQueryWrapper<>();
            query.eq(THealthDataConfig::getCustomerId, customerId)
                 .eq(THealthDataConfig::getIsEnabled, true)
                 .select(THealthDataConfig::getDataType);

            List<THealthDataConfig> configs = healthDataConfigService.list(query);
            
            Set<String> metrics = configs.stream()
                    .map(THealthDataConfig::getDataType)
                    .collect(Collectors.toSet());

            // 缓存结果
            customerMetricsCache.put(customerId, metrics);
            
            log.debug("客户 {} 支持的健康指标: {}", customerId, metrics);
            return metrics;
            
        } catch (Exception e) {
            log.error("获取客户 {} 支持的健康指标失败: {}", customerId, e.getMessage(), e);
            return getDefaultMetrics();
        }
    }

    /**
     * 获取客户健康指标配置详情
     */
    @Cacheable(value = "health_config", key = "#customerId")
    public Map<String, THealthDataConfig> getHealthDataConfigs(Long customerId) {
        try {
            // 先检查本地缓存
            if (customerConfigCache.containsKey(customerId)) {
                return customerConfigCache.get(customerId);
            }

            LambdaQueryWrapper<THealthDataConfig> query = new LambdaQueryWrapper<>();
            query.eq(THealthDataConfig::getCustomerId, customerId)
                 .eq(THealthDataConfig::getIsEnabled, true);

            List<THealthDataConfig> configs = healthDataConfigService.list(query);
            
            Map<String, THealthDataConfig> configMap = configs.stream()
                    .collect(Collectors.toMap(
                        THealthDataConfig::getDataType,
                        config -> config,
                        (existing, replacement) -> replacement
                    ));

            // 缓存结果
            customerConfigCache.put(customerId, configMap);
            
            log.debug("客户 {} 健康指标配置数量: {}", customerId, configMap.size());
            return configMap;
            
        } catch (Exception e) {
            log.error("获取客户 {} 健康指标配置失败: {}", customerId, e.getMessage(), e);
            return Map.of();
        }
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
        customerConfigCache.remove(customerId);
        log.info("已清除客户 {} 的配置缓存", customerId);
    }

    /**
     * 清除所有缓存
     */
    public void clearAllCache() {
        customerMetricsCache.clear();
        customerConfigCache.clear();
        log.info("已清除所有配置缓存");
    }

    /**
     * 获取默认支持的健康指标
     */
    private Set<String> getDefaultMetrics() {
        return Set.of(
            "heart_rate", "blood_oxygen", "temperature",
            "pressure_high", "pressure_low", "stress",
            "step", "calorie", "distance", "sleep"
        );
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
}