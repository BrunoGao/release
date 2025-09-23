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

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.infrastructure.util.SpringUtil;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.domain.model.HealthDataEvent;
import com.ljwx.modules.health.domain.model.AlertResult;
import com.ljwx.modules.health.domain.model.CompiledRuleSet;
import com.ljwx.modules.health.domain.model.CompiledSingleRule;
import com.ljwx.modules.health.domain.model.CompiledCompositeRule;
import com.ljwx.modules.health.domain.model.CompiledComplexRule;
import com.ljwx.modules.health.domain.model.CompiledCondition;
import com.ljwx.modules.health.repository.mapper.TAlertRulesMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.math.BigDecimal;
import java.time.Duration;
import java.time.LocalTime;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

/**
 * 增强版告警规则引擎服务
 * 支持单体征、复合、复杂规则评估
 * 实现三层缓存架构和异步处理
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertRuleEngineService
 * @CreateTime 2025-09-10
 */
@Service
@Slf4j
public class AlertRuleEngineService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private TAlertRulesMapper alertRulesMapper;
    
    @Autowired
    private AlertRulesCacheManager alertRulesCacheManager;
    
    // JVM本地缓存
    private final Map<String, CacheEntry> localCache = new ConcurrentHashMap<>();
    
    // 规则执行器线程池
    private ExecutorService ruleExecutorPool;
    
    // 本地缓存TTL (5分钟)
    private static final long LOCAL_CACHE_TTL = 5 * 60 * 1000L;
    
    // Redis缓存TTL (24小时)  
    private static final Duration REDIS_CACHE_TTL = Duration.ofHours(24);
    
    @PostConstruct
    public void init() {
        // 初始化线程池
        ruleExecutorPool = new ThreadPoolExecutor(
            4, 16, 60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),
            r -> {
                Thread t = new Thread(r, "alert-rule-executor-" + r.hashCode());
                t.setDaemon(true);
                return t;
            }
        );
        log.info("告警规则引擎服务已初始化，线程池大小: {}", ((ThreadPoolExecutor) ruleExecutorPool).getCorePoolSize());
    }
    
    /**
     * 规则评估主入口
     */
    public List<AlertResult> evaluateRules(HealthDataEvent healthData) {
        if (healthData == null || healthData.getCustomerId() == null) {
            return Collections.emptyList();
        }
        
        try {
            String customerId = String.valueOf(healthData.getCustomerId());
            
            // 1. 获取缓存的规则
            List<TAlertRules> rules = getCachedRules(customerId);
            if (rules.isEmpty()) {
                log.debug("客户{}未配置告警规则", customerId);
                return Collections.emptyList();
            }
            
            // 2. 规则预编译和分组
            CompiledRuleSet compiledRules = compileRules(rules);
            
            // 3. 并行评估
            return evaluateRulesParallel(healthData, compiledRules);
            
        } catch (Exception e) {
            log.error("规则评估异常: {}", e.getMessage(), e);
            return Collections.emptyList();
        }
    }
    
    /**
     * 三层缓存获取规则 - 集成AlertRulesCacheManager
     */
    private List<TAlertRules> getCachedRules(String customerId) {
        String cacheKey = "alert_rules:" + customerId;
        
        try {
            // L1: JVM本地缓存 (5分钟) - 最快响应
            CacheEntry cacheEntry = localCache.get(cacheKey);
            if (cacheEntry != null && !cacheEntry.isExpired()) {
                log.debug("L1缓存命中: {}", customerId);
                return cacheEntry.getRules();
            }
            
            // L2: Redis缓存 (24小时) - 通过AlertRulesCacheManager管理
            @SuppressWarnings("unchecked")
            List<TAlertRules> rules = (List<TAlertRules>) redisTemplate.opsForValue().get(cacheKey);
            if (rules != null && !rules.isEmpty()) {
                log.debug("L2缓存命中: {}", customerId);
                // 回填L1缓存
                localCache.put(cacheKey, new CacheEntry(rules, System.currentTimeMillis()));
                return rules;
            }
            
            // L3: 数据库 + 异步缓存更新
            rules = loadRulesFromDatabase(Long.valueOf(customerId));
            
            // 使用AlertRulesCacheManager异步更新缓存，避免阻塞
            if (!rules.isEmpty()) {
                // 立即更新本地缓存
                localCache.put(cacheKey, new CacheEntry(rules, System.currentTimeMillis()));
                
                // 异步通过缓存管理器更新Redis缓存和同步状态
                alertRulesCacheManager.updateAlertRulesCacheAsync(Long.valueOf(customerId));
                
                log.debug("从数据库加载规则，已触发异步缓存更新: customer={}, count={}", customerId, rules.size());
            }
            
            return rules;
            
        } catch (Exception e) {
            log.error("获取缓存规则失败: customerId={}", customerId, e);
            // 兜底直接查数据库
            return loadRulesFromDatabase(Long.valueOf(customerId));
        }
    }
    
    /**
     * 从数据库加载规则
     */
    private List<TAlertRules> loadRulesFromDatabase(Long customerId) {
        try {
            LambdaQueryWrapper<TAlertRules> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(TAlertRules::getCustomerId, customerId)
                   .eq(TAlertRules::getIsEnabled, true)
                   .eq(TAlertRules::getDeleted, 0)  // 0表示未删除
                   .orderBy(true, true, TAlertRules::getPriorityLevel);
            
            List<TAlertRules> rules = alertRulesMapper.selectList(wrapper);
            return rules != null ? rules : Collections.emptyList();
            
        } catch (Exception e) {
            log.error("从数据库加载规则失败: customerId={}", customerId, e);
            return Collections.emptyList();
        }
    }
    
    /**
     * 规则预编译
     */
    private CompiledRuleSet compileRules(List<TAlertRules> rules) {
        CompiledRuleSet compiledRules = new CompiledRuleSet();
        
        for (TAlertRules rule : rules) {
            if (!isRuleEnabled(rule)) {
                continue;
            }
            
            try {
                String category = rule.getRuleCategory();
                if (category == null) category = "SINGLE"; // 向下兼容
                
                switch (category.toUpperCase()) {
                    case "SINGLE":
                        CompiledSingleRule singleRule = compileSingleRule(rule);
                        if (singleRule != null) {
                            compiledRules.addSingleRule(singleRule);
                        }
                        break;
                        
                    case "COMPOSITE":
                        CompiledCompositeRule compositeRule = compileCompositeRule(rule);
                        if (compositeRule != null) {
                            compiledRules.addCompositeRule(compositeRule);
                        }
                        break;
                        
                    case "COMPLEX":
                        CompiledComplexRule complexRule = compileComplexRule(rule);
                        if (complexRule != null) {
                            compiledRules.addComplexRule(complexRule);
                        }
                        break;
                        
                    default:
                        log.warn("未知规则类型: {}, ruleId={}", category, rule.getId());
                }
                
            } catch (Exception e) {
                log.error("编译规则失败: ruleId={}, error={}", rule.getId(), e.getMessage());
            }
        }
        
        return compiledRules;
    }
    
    /**
     * 检查规则是否启用和在生效时间内
     */
    private boolean isRuleEnabled(TAlertRules rule) {
        if (!Boolean.TRUE.equals(rule.getIsEnabled())) {
            return false;
        }
        
        // 检查生效时间
        if (rule.getEffectiveTimeStart() != null && rule.getEffectiveTimeEnd() != null) {
            LocalTime now = LocalTime.now();
            LocalTime start = parseTimeString(rule.getEffectiveTimeStart());
            LocalTime end = parseTimeString(rule.getEffectiveTimeEnd());
            
            if (start != null && end != null && start.isAfter(end)) {
                // 跨天情况，如 22:00 - 06:00
                if (!(now.isAfter(start) || now.isBefore(end))) {
                    return false;
                }
            } else if (start != null && end != null) {
                // 普通情况，如 09:00 - 17:00
                if (!(now.isAfter(start) && now.isBefore(end))) {
                    return false;
                }
            }
        }
        
        // 检查生效星期
        if (rule.getEffectiveDays() != null && !rule.getEffectiveDays().isEmpty()) {
            int dayOfWeek = Calendar.getInstance().get(Calendar.DAY_OF_WEEK);
            // 转换为1-7格式（周一到周日）
            int targetDay = dayOfWeek == 1 ? 7 : dayOfWeek - 1;
            
            if (!rule.getEffectiveDays().contains(String.valueOf(targetDay))) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 编译单体征规则
     */
    private CompiledSingleRule compileSingleRule(TAlertRules rule) {
        if (rule.getPhysicalSign() == null) {
            log.warn("单体征规则缺少physical_sign: ruleId={}", rule.getId());
            return null;
        }
        
        return CompiledSingleRule.builder()
            .ruleId(rule.getId())
            .physicalSign(rule.getPhysicalSign())
            .thresholdMin(rule.getThresholdMin())
            .thresholdMax(rule.getThresholdMax())
            .trendDuration(rule.getTrendDuration() != null ? rule.getTrendDuration() : 1)
            .timeWindowSeconds(rule.getTimeWindowSeconds() != null ? rule.getTimeWindowSeconds() : 300)
            .cooldownSeconds(rule.getCooldownSeconds() != null ? rule.getCooldownSeconds() : 600)
            .priorityLevel(rule.getPriorityLevel() != null ? rule.getPriorityLevel() : 3)
            .severityLevel(rule.getLevel())
            .alertMessage(rule.getAlertMessage())
            .enabledChannels(parseEnabledChannels(rule.getEnabledChannels()))
            .build();
    }
    
    /**
     * 编译复合规则
     */
    private CompiledCompositeRule compileCompositeRule(TAlertRules rule) {
        if (rule.getConditionExpression() == null) {
            log.warn("复合规则缺少condition_expression: ruleId={}", rule.getId());
            return null;
        }
        
        try {
            JSONObject conditionExpr = JSON.parseObject(rule.getConditionExpression().toString());
            JSONArray conditions = conditionExpr.getJSONArray("conditions");
            String logicalOperator = conditionExpr.getString("logical_operator");
            
            if (conditions == null || conditions.isEmpty()) {
                log.warn("复合规则条件为空: ruleId={}", rule.getId());
                return null;
            }
            
            List<CompiledCondition> compiledConditions = new ArrayList<>();
            for (int i = 0; i < conditions.size(); i++) {
                JSONObject condition = conditions.getJSONObject(i);
                CompiledCondition compiledCondition = compileCondition(condition);
                if (compiledCondition != null) {
                    compiledConditions.add(compiledCondition);
                }
            }
            
            if (compiledConditions.isEmpty()) {
                return null;
            }
            
            return CompiledCompositeRule.builder()
                .ruleId(rule.getId())
                .conditions(compiledConditions)
                .logicalOperator(logicalOperator != null ? logicalOperator : "AND")
                .timeWindowSeconds(rule.getTimeWindowSeconds() != null ? rule.getTimeWindowSeconds() : 300)
                .cooldownSeconds(rule.getCooldownSeconds() != null ? rule.getCooldownSeconds() : 600)
                .priorityLevel(rule.getPriorityLevel() != null ? rule.getPriorityLevel() : 3)
                .severityLevel(rule.getLevel())
                .alertMessage(rule.getAlertMessage())
                .enabledChannels(parseEnabledChannels(rule.getEnabledChannels()))
                .build();
                
        } catch (Exception e) {
            log.error("编译复合规则失败: ruleId={}", rule.getId(), e);
            return null;
        }
    }
    
    /**
     * 编译复杂规则
     */
    private CompiledComplexRule compileComplexRule(TAlertRules rule) {
        // 复杂规则暂时不实现，返回null
        log.debug("复杂规则暂未实现: ruleId={}", rule.getId());
        return null;
    }
    
    /**
     * 编译单个条件
     */
    private CompiledCondition compileCondition(JSONObject condition) {
        try {
            return CompiledCondition.builder()
                .physicalSign(condition.getString("physical_sign"))
                .operator(condition.getString("operator"))
                .threshold(condition.getBigDecimal("threshold"))
                .durationSeconds(condition.getIntValue("duration_seconds"))
                .build();
        } catch (Exception e) {
            log.error("编译条件失败: {}", condition, e);
            return null;
        }
    }
    
    /**
     * 解析启用的通知渠道
     */
    private List<String> parseEnabledChannels(Object enabledChannels) {
        if (enabledChannels == null) {
            return Arrays.asList("message"); // 默认内部消息
        }
        
        try {
            if (enabledChannels instanceof String) {
                JSONArray array = JSON.parseArray((String) enabledChannels);
                return array.toJavaList(String.class);
            } else if (enabledChannels instanceof List) {
                @SuppressWarnings("unchecked")
                List<String> channels = (List<String>) enabledChannels;
                return channels;
            }
        } catch (Exception e) {
            log.warn("解析通知渠道失败: {}", enabledChannels, e);
        }
        
        return Arrays.asList("message");
    }
    
    /**
     * 并行规则评估
     */
    private List<AlertResult> evaluateRulesParallel(HealthDataEvent healthData, CompiledRuleSet compiledRules) {
        List<CompletableFuture<List<AlertResult>>> futures = new ArrayList<>();
        
        // 单体征规则并行评估
        if (!compiledRules.getSingleRules().isEmpty()) {
            futures.add(CompletableFuture.supplyAsync(() -> 
                evaluateSingleRules(healthData, compiledRules.getSingleRules()), ruleExecutorPool));
        }
        
        // 复合规则并行评估
        if (!compiledRules.getCompositeRules().isEmpty()) {
            futures.add(CompletableFuture.supplyAsync(() -> 
                evaluateCompositeRules(healthData, compiledRules.getCompositeRules()), ruleExecutorPool));
        }
        
        // 复杂规则并行评估
        if (!compiledRules.getComplexRules().isEmpty()) {
            futures.add(CompletableFuture.supplyAsync(() -> 
                evaluateComplexRules(healthData, compiledRules.getComplexRules()), ruleExecutorPool));
        }
        
        // 合并结果
        try {
            return futures.stream()
                .map(future -> {
                    try {
                        return future.get(5, TimeUnit.SECONDS); // 5秒超时
                    } catch (Exception e) {
                        log.error("规则评估超时或异常", e);
                        return Collections.<AlertResult>emptyList();
                    }
                })
                .flatMap(List::stream)
                .collect(Collectors.toList());
        } catch (Exception e) {
            log.error("并行规则评估异常", e);
            return Collections.emptyList();
        }
    }
    
    /**
     * 评估单体征规则
     */
    private List<AlertResult> evaluateSingleRules(HealthDataEvent healthData, List<CompiledSingleRule> rules) {
        List<AlertResult> results = new ArrayList<>();
        
        for (CompiledSingleRule rule : rules) {
            try {
                AlertResult result = evaluateSingleRule(healthData, rule);
                if (result != null) {
                    results.add(result);
                }
            } catch (Exception e) {
                log.error("单体征规则评估失败: ruleId={}", rule.getRuleId(), e);
            }
        }
        
        return results;
    }
    
    /**
     * 评估单个单体征规则
     */
    private AlertResult evaluateSingleRule(HealthDataEvent healthData, CompiledSingleRule rule) {
        Object valueObj = healthData.getValue(rule.getPhysicalSign());
        if (valueObj == null) {
            return null; // 没有对应的健康数据
        }
        
        BigDecimal value;
        try {
            if (valueObj instanceof Number) {
                value = new BigDecimal(valueObj.toString());
            } else {
                value = new BigDecimal(valueObj.toString());
            }
        } catch (NumberFormatException e) {
            log.warn("健康数据值格式错误: {}={}", rule.getPhysicalSign(), valueObj);
            return null;
        }
        
        // 检查是否超出阈值
        boolean isViolated = false;
        String violationType = null;
        
        if (rule.getThresholdMin() != null && value.compareTo(rule.getThresholdMin()) < 0) {
            isViolated = true;
            violationType = "min";
        } else if (rule.getThresholdMax() != null && value.compareTo(rule.getThresholdMax()) > 0) {
            isViolated = true;
            violationType = "max";
        }
        
        if (!isViolated) {
            return null; // 没有违反阈值
        }
        
        // TODO: 实现趋势持续检查 (需要历史数据支持)
        
        // 构建告警结果
        return AlertResult.builder()
            .ruleId(rule.getRuleId())
            .ruleType("SINGLE")
            .physicalSign(rule.getPhysicalSign())
            .currentValue(value)
            .violationType(violationType)
            .thresholdMin(rule.getThresholdMin())
            .thresholdMax(rule.getThresholdMax())
            .severityLevel(rule.getSeverityLevel())
            .alertMessage(formatAlertMessage(rule.getAlertMessage(), healthData, rule, value))
            .enabledChannels(rule.getEnabledChannels())
            .deviceSn(healthData.getDeviceSn())
            .customerId(healthData.getCustomerId())
            .timestamp(System.currentTimeMillis())
            .build();
    }
    
    /**
     * 评估复合规则
     */
    private List<AlertResult> evaluateCompositeRules(HealthDataEvent healthData, List<CompiledCompositeRule> rules) {
        List<AlertResult> results = new ArrayList<>();
        
        for (CompiledCompositeRule rule : rules) {
            try {
                AlertResult result = evaluateCompositeRule(healthData, rule);
                if (result != null) {
                    results.add(result);
                }
            } catch (Exception e) {
                log.error("复合规则评估失败: ruleId={}", rule.getRuleId(), e);
            }
        }
        
        return results;
    }
    
    /**
     * 评估单个复合规则
     */
    private AlertResult evaluateCompositeRule(HealthDataEvent healthData, CompiledCompositeRule rule) {
        List<Boolean> conditionResults = new ArrayList<>();
        StringBuilder violationDetails = new StringBuilder();
        
        for (CompiledCondition condition : rule.getConditions()) {
            boolean conditionMet = evaluateCondition(healthData, condition);
            conditionResults.add(conditionMet);
            
            if (conditionMet) {
                if (violationDetails.length() > 0) {
                    violationDetails.append(", ");
                }
                Object value = healthData.getValue(condition.getPhysicalSign());
                violationDetails.append(String.format("%s: %s %s %s", 
                    condition.getPhysicalSign(), value, condition.getOperator(), condition.getThreshold()));
            }
        }
        
        // 根据逻辑操作符判断最终结果
        boolean finalResult;
        if ("OR".equalsIgnoreCase(rule.getLogicalOperator())) {
            finalResult = conditionResults.stream().anyMatch(Boolean::booleanValue);
        } else { // 默认AND
            finalResult = conditionResults.stream().allMatch(Boolean::booleanValue);
        }
        
        if (!finalResult) {
            return null;
        }
        
        // 构建告警结果
        return AlertResult.builder()
            .ruleId(rule.getRuleId())
            .ruleType("COMPOSITE")
            .physicalSign("COMPOSITE")
            .violationType("composite")
            .severityLevel(rule.getSeverityLevel())
            .alertMessage(formatAlertMessage(rule.getAlertMessage(), healthData, rule, null))
            .enabledChannels(rule.getEnabledChannels())
            .deviceSn(healthData.getDeviceSn())
            .customerId(healthData.getCustomerId())
            .timestamp(System.currentTimeMillis())
            .evaluationContext(violationDetails.toString())
            .build();
    }
    
    /**
     * 评估单个条件
     */
    private boolean evaluateCondition(HealthDataEvent healthData, CompiledCondition condition) {
        Object valueObj = healthData.getValue(condition.getPhysicalSign());
        if (valueObj == null) {
            return false;
        }
        
        BigDecimal value;
        try {
            value = new BigDecimal(valueObj.toString());
        } catch (NumberFormatException e) {
            return false;
        }
        
        BigDecimal threshold = condition.getThreshold();
        String operator = condition.getOperator();
        
        switch (operator.toUpperCase()) {
            case ">":
                return value.compareTo(threshold) > 0;
            case "<":
                return value.compareTo(threshold) < 0;
            case ">=":
                return value.compareTo(threshold) >= 0;
            case "<=":
                return value.compareTo(threshold) <= 0;
            case "==":
            case "=":
                return value.compareTo(threshold) == 0;
            case "!=":
                return value.compareTo(threshold) != 0;
            default:
                log.warn("未知的操作符: {}", operator);
                return false;
        }
    }
    
    /**
     * 评估复杂规则 (暂未实现)
     */
    private List<AlertResult> evaluateComplexRules(HealthDataEvent healthData, List<CompiledComplexRule> rules) {
        // 复杂规则暂时不实现
        return Collections.emptyList();
    }
    
    /**
     * 格式化告警消息
     */
    private String formatAlertMessage(String template, HealthDataEvent healthData, Object rule, BigDecimal value) {
        if (template == null || template.isEmpty()) {
            return "健康指标异常告警";
        }
        
        // 简单的模板替换
        String message = template;
        message = message.replace("{device_sn}", String.valueOf(healthData.getDeviceSn()));
        message = message.replace("{customer_id}", String.valueOf(healthData.getCustomerId()));
        
        if (value != null) {
            message = message.replace("{value}", value.toString());
        }
        
        // 添加时间戳
        message = message.replace("{timestamp}", new Date().toString());
        
        return message;
    }
    
    /**
     * 清空本地缓存
     */
    public void clearLocalCache() {
        localCache.clear();
        log.info("本地缓存已清空");
    }
    
    /**
     * 清空指定客户的缓存 - 集成AlertRulesCacheManager
     */
    public void clearCustomerCache(String customerId) {
        String cacheKey = "alert_rules:" + customerId;
        
        // 清空本地缓存
        localCache.remove(cacheKey);
        
        // 通过AlertRulesCacheManager清空Redis缓存和同步状态
        alertRulesCacheManager.clearCustomerCache(Long.valueOf(customerId));
        
        log.info("客户{}的缓存已清空(通过缓存管理器)", customerId);
    }
    
    /**
     * 获取缓存统计信息 - 集成AlertRulesCacheManager统计
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> stats = new HashMap<>();
        
        // AlertRuleEngineService统计
        stats.put("localCacheSize", localCache.size());
        stats.put("threadPoolSize", ((ThreadPoolExecutor) ruleExecutorPool).getPoolSize());
        stats.put("activeThreads", ((ThreadPoolExecutor) ruleExecutorPool).getActiveCount());
        stats.put("queueSize", ((ThreadPoolExecutor) ruleExecutorPool).getQueue().size());
        
        // AlertRulesCacheManager统计
        try {
            Map<String, Object> cacheManagerStats = alertRulesCacheManager.getCacheStats();
            stats.put("cacheManager", cacheManagerStats);
        } catch (Exception e) {
            log.warn("获取缓存管理器统计失败", e);
            stats.put("cacheManager", "unavailable");
        }
        
        return stats;
    }
    
    // 内部类定义
    
    /**
     * 缓存条目
     */
    private static class CacheEntry {
        private final List<TAlertRules> rules;
        private final long timestamp;
        
        public CacheEntry(List<TAlertRules> rules, long timestamp) {
            this.rules = rules;
            this.timestamp = timestamp;
        }
        
        public List<TAlertRules> getRules() {
            return rules;
        }
        
        public boolean isExpired() {
            return System.currentTimeMillis() - timestamp > LOCAL_CACHE_TTL;
        }
    }
    
    /**
     * 解析时间字符串为LocalTime
     */
    private LocalTime parseTimeString(String timeString) {
        if (timeString == null || timeString.trim().isEmpty()) {
            return LocalTime.now();
        }
        
        try {
            // 直接解析HH:mm:ss格式
            if (timeString.matches("^\\d{2}:\\d{2}:\\d{2}$")) {
                return LocalTime.parse(timeString);
            }
            
            // 如果是HH:mm格式，补充秒
            if (timeString.matches("^\\d{2}:\\d{2}$")) {
                return LocalTime.parse(timeString + ":00");
            }
            
            // 其他格式，返回当前时间
            return LocalTime.now();
        } catch (Exception e) {
            log.warn("解析时间字符串失败: {}, 使用当前时间", timeString, e);
            return LocalTime.now();
        }
    }
}