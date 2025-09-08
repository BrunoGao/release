package com.ljwx.modules.health.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 权重计算服务 - 基于ljwx-bigscreen的权重计算逻辑的Java实现
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.WeightCalculationService
 * @CreateTime 2025-01-26
 */
@Slf4j
@Service
public class WeightCalculationService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 验证所有客户的权重配置
     */
    @Transactional(rollbackFor = Exception.class)
    public void validateAllCustomerWeights() {
        log.info("🔍 开始验证所有客户权重配置");
        
        try {
            // 获取所有客户ID
            String customerQuery = "SELECT DISTINCT customer_id FROM t_health_data_config WHERE is_enabled = 1";
            List<Long> customerIds = jdbcTemplate.queryForList(customerQuery, Long.class);
            
            int fixedCustomers = 0;
            for (Long customerId : customerIds) {
                boolean fixed = validateAndFixCustomerWeights(customerId);
                if (fixed) {
                    fixedCustomers++;
                }
            }
            
            log.info("✅ 权重配置验证完成，验证了 {} 个客户，修复了 {} 个客户的权重配置", 
                customerIds.size(), fixedCustomers);
            
        } catch (Exception e) {
            log.error("❌ 权重配置验证失败: {}", e.getMessage(), e);
            throw new RuntimeException("权重配置验证失败: " + e.getMessage(), e);
        }
    }

    /**
     * 验证并修复单个客户的权重配置
     */
    private boolean validateAndFixCustomerWeights(Long customerId) {
        try {
            boolean needsFix = false;
            
            // 1. 获取客户的所有健康指标配置
            List<Map<String, Object>> configs = jdbcTemplate.queryForList("""
                SELECT data_type, weight, is_enabled 
                FROM t_health_data_config 
                WHERE customer_id = ? AND is_enabled = 1
                ORDER BY data_type
                """, customerId);
            
            if (configs.isEmpty()) {
                log.warn("⚠️ 客户 {} 无启用的健康指标配置", customerId);
                return false;
            }
            
            // 2. 应用标准化权重分配
            Map<String, Double> standardWeights = getStandardHealthMetricWeights();
            
            // 3. 检查并修复每个指标的权重
            for (Map<String, Object> config : configs) {
                String dataType = (String) config.get("data_type");
                Double currentWeight = convertToDouble(config.get("weight"));
                Double standardWeight = standardWeights.get(dataType);
                
                if (standardWeight == null) {
                    standardWeight = 0.05; // 未定义指标的默认权重
                }
                
                // 如果当前权重为空、0或与标准权重差异过大，则需要修复
                if (currentWeight == null || currentWeight <= 0 || 
                    Math.abs(currentWeight - standardWeight) > 0.05) {
                    needsFix = true;
                    break;
                }
            }
            
            // 4. 执行权重修复
            if (needsFix) {
                applyStandardWeights(customerId, standardWeights);
                log.info("🔧 已修复客户 {} 的权重配置", customerId);
                return true;
            }
            
            return false;
            
        } catch (Exception e) {
            log.error("❌ 客户 {} 权重验证失败: {}", customerId, e.getMessage(), e);
            return false;
        }
    }


    /**
     * 更新每日权重缓存
     */
    @Transactional(rollbackFor = Exception.class)
    public void updateDailyWeights() {
        log.info("🔄 开始更新每日权重缓存");
        
        try {
            // 清理昨日权重缓存
            cleanupOldWeightCache();
            
            // 生成今日权重缓存
            generateWeightCache();
            
            log.info("✅ 每日权重缓存更新完成");
            
        } catch (Exception e) {
            log.error("❌ 更新每日权重缓存失败: {}", e.getMessage(), e);
            throw new RuntimeException("更新每日权重缓存失败: " + e.getMessage(), e);
        }
    }

    /**
     * 清理旧的权重缓存
     */
    private void cleanupOldWeightCache() {
        try {
            // 首先检查表是否存在
            if (!isTableExists("t_health_weight_cache")) {
                log.warn("⚠️ t_health_weight_cache 表不存在，跳过清理操作");
                return;
            }
            
            LocalDate cutoffDate = LocalDate.now().minusDays(7); // 保留7天
            String cleanupQuery = "DELETE FROM t_health_weight_cache WHERE cache_date < ?";
            int deletedRows = jdbcTemplate.update(cleanupQuery, cutoffDate);
            
            if (deletedRows > 0) {
                log.info("🧹 清理了 {} 条过期权重缓存", deletedRows);
            }
            
        } catch (Exception e) {
            log.warn("⚠️ 清理权重缓存失败，但不影响主流程: {}", e.getMessage());
        }
    }

    /**
     * 生成权重缓存
     */
    private void generateWeightCache() {
        try {
            // 首先检查表是否存在
            if (!isTableExists("t_health_weight_cache")) {
                log.warn("⚠️ t_health_weight_cache 表不存在，跳过权重缓存生成");
                return;
            }
            
            String today = LocalDate.now().toString();
            
            // 检查今日缓存是否已存在
            String checkQuery = "SELECT COUNT(*) FROM t_health_weight_cache WHERE cache_date = ?";
            Integer existingCache = jdbcTemplate.queryForObject(checkQuery, Integer.class, today);
            
            if (existingCache != null && existingCache > 0) {
                log.info("ℹ️ 今日权重缓存已存在，跳过生成");
                return;
            }
            
            // 生成权重缓存 - 结合体征权重和岗位权重
            String cacheQuery = """
                INSERT INTO t_health_weight_cache (
                    user_id, customer_id, metric_name, 
                    base_weight, position_risk_multiplier, combined_weight, normalized_weight,
                    position_id, position_risk_level, cache_date, create_time
                )
                SELECT 
                    ui.id as user_id,
                    ui.customer_id,
                    hdc.data_type as metric_name,
                    COALESCE(hdc.weight, 0.15) as base_weight,
                    CASE 
                        WHEN p.risk_level = 'low' THEN 0.8
                        WHEN p.risk_level = 'normal' THEN 1.0  
                        WHEN p.risk_level = 'medium' THEN 1.2
                        WHEN p.risk_level = 'high' THEN 1.5
                        WHEN p.risk_level = 'critical' THEN 2.0
                        ELSE 1.0 
                    END as position_risk_multiplier,
                    COALESCE(hdc.weight, 0.15) * 
                    CASE 
                        WHEN p.risk_level = 'low' THEN 0.8
                        WHEN p.risk_level = 'normal' THEN 1.0
                        WHEN p.risk_level = 'medium' THEN 1.2  
                        WHEN p.risk_level = 'high' THEN 1.5
                        WHEN p.risk_level = 'critical' THEN 2.0
                        ELSE 1.0
                    END as combined_weight,
                    0 as normalized_weight, -- 将在后续步骤中计算
                    COALESCE(up.position_id, 0) as position_id,
                    COALESCE(p.risk_level, 'normal') as position_risk_level,
                    ? as cache_date,
                    NOW() as create_time
                FROM sys_user ui
                CROSS JOIN t_health_data_config hdc
                LEFT JOIN sys_user_position up ON ui.id = up.user_id AND up.is_deleted = 0
                LEFT JOIN sys_position p ON up.position_id = p.id AND p.is_deleted = 0
                WHERE ui.customer_id = hdc.customer_id 
                AND ui.is_deleted = 0 
                AND hdc.is_enabled = 1
                """;
            
            int cacheRows = jdbcTemplate.update(cacheQuery, today);
            
            // 归一化权重 - 确保每个用户的所有指标权重总和为1
            normalizeWeightCache(today);
            
            log.info("✅ 生成权重缓存完成，共 {} 条记录", cacheRows);
            
        } catch (Exception e) {
            log.error("❌ 生成权重缓存失败: {}", e.getMessage(), e);
            throw new RuntimeException("生成权重缓存失败: " + e.getMessage(), e);
        }
    }

    /**
     * 归一化权重缓存
     */
    private void normalizeWeightCache(String cacheDate) {
        try {
            // 计算每个用户的权重总和
            String updateQuery = """
                UPDATE t_health_weight_cache wc1
                JOIN (
                    SELECT user_id, SUM(combined_weight) as total_weight
                    FROM t_health_weight_cache 
                    WHERE cache_date = ?
                    GROUP BY user_id
                ) wc2 ON wc1.user_id = wc2.user_id
                SET wc1.normalized_weight = CASE 
                    WHEN wc2.total_weight > 0 THEN wc1.combined_weight / wc2.total_weight
                    ELSE wc1.combined_weight 
                END
                WHERE wc1.cache_date = ?
                """;
                
            int normalizedRows = jdbcTemplate.update(updateQuery, cacheDate, cacheDate);
            log.info("🔧 权重归一化完成，处理了 {} 条记录", normalizedRows);
            
        } catch (Exception e) {
            log.error("❌ 权重归一化失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 获取用户的权重配置
     */
    public Map<String, Object> getUserWeights(Long userId, Long customerId) {
        try {
            String today = LocalDate.now().toString();
            String query = """
                SELECT 
                    metric_name,
                    base_weight,
                    position_risk_multiplier,
                    combined_weight,
                    normalized_weight,
                    position_risk_level
                FROM t_health_weight_cache 
                WHERE user_id = ? AND customer_id = ? AND cache_date = ?
                ORDER BY metric_name
                """;
                
            List<Map<String, Object>> weights = jdbcTemplate.queryForList(query, userId, customerId, today);
            
            if (weights.isEmpty()) {
                // 如果缓存不存在，实时计算
                log.warn("⚠️ 用户 {} 权重缓存不存在，进行实时计算", userId);
                return calculateUserWeightsRealtime(userId, customerId);
            }
            
            return Map.of("weights", weights, "cached", true);
            
        } catch (Exception e) {
            log.error("❌ 获取用户权重失败: {}", e.getMessage(), e);
            return Map.of("error", e.getMessage());
        }
    }

    /**
     * 实时计算用户权重（当缓存不存在时）
     */
    private Map<String, Object> calculateUserWeightsRealtime(Long userId, Long customerId) {
        try {
            String query = """
                SELECT 
                    hdc.data_type as metric_name,
                    COALESCE(hdc.weight, 0.15) as base_weight,
                    CASE 
                        WHEN p.risk_level = 'low' THEN 0.8
                        WHEN p.risk_level = 'normal' THEN 1.0
                        WHEN p.risk_level = 'medium' THEN 1.2
                        WHEN p.risk_level = 'high' THEN 1.5  
                        WHEN p.risk_level = 'critical' THEN 2.0
                        ELSE 1.0
                    END as position_risk_multiplier,
                    COALESCE(p.risk_level, 'normal') as position_risk_level
                FROM t_health_data_config hdc
                LEFT JOIN sys_user_position up ON up.user_id = ? AND up.is_deleted = 0
                LEFT JOIN sys_position p ON up.position_id = p.id AND p.is_deleted = 0
                WHERE hdc.customer_id = ? AND hdc.is_enabled = 1
                ORDER BY hdc.data_type
                """;
                
            List<Map<String, Object>> rawWeights = jdbcTemplate.queryForList(query, userId, customerId);
            
            // 计算综合权重和归一化权重
            double totalCombinedWeight = 0.0;
            for (Map<String, Object> weight : rawWeights) {
                Double baseWeight = convertToDouble(weight.get("base_weight"));
                Double riskMultiplier = convertToDouble(weight.get("position_risk_multiplier"));
                Double combinedWeight = baseWeight * riskMultiplier;
                weight.put("combined_weight", combinedWeight);
                totalCombinedWeight += combinedWeight;
            }
            
            // 归一化
            for (Map<String, Object> weight : rawWeights) {
                Double combinedWeight = convertToDouble(weight.get("combined_weight"));
                Double normalizedWeight = totalCombinedWeight > 0 ? combinedWeight / totalCombinedWeight : combinedWeight;
                weight.put("normalized_weight", normalizedWeight);
            }
            
            return Map.of("weights", rawWeights, "cached", false);
            
        } catch (Exception e) {
            log.error("❌ 实时计算用户权重失败: {}", e.getMessage(), e);
            return Map.of("error", e.getMessage());
        }
    }

    /**
     * 获取权重统计信息
     */
    public Map<String, Object> getWeightStatistics(Long customerId) {
        try {
            String today = LocalDate.now().toString();
            
            // 统计信息查询
            String statsQuery = """
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    COUNT(DISTINCT metric_name) as total_metrics,
                    AVG(normalized_weight) as avg_weight,
                    MIN(normalized_weight) as min_weight,
                    MAX(normalized_weight) as max_weight,
                    COUNT(DISTINCT position_risk_level) as risk_levels
                FROM t_health_weight_cache 
                WHERE customer_id = ? AND cache_date = ?
                """;
                
            Map<String, Object> stats = jdbcTemplate.queryForMap(statsQuery, customerId, today);
            
            // 风险等级分布
            String riskDistQuery = """
                SELECT 
                    position_risk_level,
                    COUNT(DISTINCT user_id) as user_count,
                    AVG(normalized_weight) as avg_weight
                FROM t_health_weight_cache 
                WHERE customer_id = ? AND cache_date = ?
                GROUP BY position_risk_level
                ORDER BY position_risk_level
                """;
                
            List<Map<String, Object>> riskDistribution = jdbcTemplate.queryForList(riskDistQuery, customerId, today);
            
            stats.put("risk_distribution", riskDistribution);
            stats.put("cache_date", today);
            
            return stats;
            
        } catch (Exception e) {
            log.error("❌ 获取权重统计信息失败: {}", e.getMessage(), e);
            return Map.of("error", e.getMessage());
        }
    }

    /**
     * 检查表是否存在
     */
    private boolean isTableExists(String tableName) {
        try {
            String checkTableQuery = """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = DATABASE() AND table_name = ?
                """;
            Integer count = jdbcTemplate.queryForObject(checkTableQuery, Integer.class, tableName);
            return count != null && count > 0;
        } catch (Exception e) {
            log.warn("⚠️ 检查表 {} 是否存在失败: {}", tableName, e.getMessage());
            return false;
        }
    }

    /**
     * 获取标准化的健康指标权重配置
     * 基于医学重要性和实际监测需要设计的权重分配
     */
    private Map<String, Double> getStandardHealthMetricWeights() {
        Map<String, Double> standardWeights = new HashMap<>();
        
        // 核心生命体征权重 (总和: 0.65)
        standardWeights.put("heart_rate", 0.20);      // 心率 - 最重要的生命体征
        standardWeights.put("blood_oxygen", 0.18);    // 血氧 - 呼吸系统核心指标
        standardWeights.put("temperature", 0.15);     // 体温 - 基础生命体征
        standardWeights.put("pressure_high", 0.06);   // 收缩压
        standardWeights.put("pressure_low", 0.06);    // 舒张压
        
        // 健康状态指标权重 (总和: 0.20)
        standardWeights.put("stress", 0.12);          // 压力指数 - 心理健康重要指标
        standardWeights.put("sleep", 0.08);           // 睡眠质量
        
        // 运动健康指标权重 (总和: 0.10)
        standardWeights.put("step", 0.04);            // 步数
        standardWeights.put("distance", 0.03);        // 距离  
        standardWeights.put("calorie", 0.03);         // 卡路里
        
        // 辅助指标权重 (总和: 0.05)
        standardWeights.put("ecg", 0.02);             // 心电图
        standardWeights.put("location", 0.01);        // 位置
        standardWeights.put("work_out", 0.01);        // 锻炼
        standardWeights.put("wear", 0.005);           // 佩戴状态
        standardWeights.put("exercise_daily", 0.005); // 日常锻炼
        
        log.info("📊 标准权重配置加载完成，总权重: {}", 
            standardWeights.values().stream().mapToDouble(Double::doubleValue).sum());
        
        return standardWeights;
    }
    
    /**
     * 应用标准权重到客户配置
     */
    private void applyStandardWeights(Long customerId, Map<String, Double> standardWeights) {
        try {
            int updatedCount = 0;
            
            for (Map.Entry<String, Double> entry : standardWeights.entrySet()) {
                String dataType = entry.getKey();
                Double weight = entry.getValue();
                
                // 只更新存在的指标
                String updateQuery = """
                    UPDATE t_health_data_config 
                    SET weight = ?, update_time = NOW()
                    WHERE customer_id = ? AND data_type = ? AND is_enabled = 1
                    """;
                    
                int updated = jdbcTemplate.update(updateQuery, weight, customerId, dataType);
                if (updated > 0) {
                    updatedCount++;
                }
            }
            
            log.info("🔧 客户 {} 应用标准权重完成，更新了 {} 个指标", customerId, updatedCount);
            
        } catch (Exception e) {
            log.error("❌ 客户 {} 应用标准权重失败: {}", customerId, e.getMessage(), e);
        }
    }

    /**
     * 批量修复所有客户的权重配置
     */
    @Transactional(rollbackFor = Exception.class) 
    public void rationalizeAllWeights() {
        log.info("🔄 开始批量修复所有客户权重配置");
        
        try {
            // 获取所有客户
            List<Long> customerIds = jdbcTemplate.queryForList(
                "SELECT DISTINCT customer_id FROM t_health_data_config WHERE is_enabled = 1", 
                Long.class);
            
            Map<String, Double> standardWeights = getStandardHealthMetricWeights();
            int fixedCustomers = 0;
            
            for (Long customerId : customerIds) {
                try {
                    applyStandardWeights(customerId, standardWeights);
                    fixedCustomers++;
                } catch (Exception e) {
                    log.error("❌ 修复客户 {} 权重配置失败: {}", customerId, e.getMessage());
                }
            }
            
            log.info("🎉 批量权重修复完成，处理了 {} 个客户中的 {} 个", customerIds.size(), fixedCustomers);
            
        } catch (Exception e) {
            log.error("❌ 批量权重修复失败: {}", e.getMessage(), e);
            throw new RuntimeException("批量权重修复失败: " + e.getMessage(), e);
        }
    }

    /**
     * 安全地将对象转换为 Double
     */
    private Double convertToDouble(Object value) {
        if (value == null) {
            return 0.0;
        }
        if (value instanceof BigDecimal) {
            return ((BigDecimal) value).doubleValue();
        }
        if (value instanceof Double) {
            return (Double) value;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.valueOf(value.toString());
        } catch (NumberFormatException e) {
            log.warn("⚠️ 无法转换值为Double: {}, 返回默认值0.0", value);
            return 0.0;
        }
    }
}