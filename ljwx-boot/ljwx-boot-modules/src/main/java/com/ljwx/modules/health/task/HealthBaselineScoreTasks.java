package com.ljwx.modules.health.task;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.ljwx.modules.health.util.HealthDataTableUtil;
import com.ljwx.modules.health.job.DepartmentHealthAggregationJob;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 健康数据基线和评分定时任务 - 支持分表架构
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.task.HealthBaselineScoreTasks
 * @CreateTime 2025-01-26
 */
@Slf4j
@Component
public class HealthBaselineScoreTasks {

    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private DepartmentHealthAggregationJob departmentHealthAggregationJob;
    
    @Autowired
    private com.ljwx.modules.health.service.WeightCalculationService weightCalculationService;
    
    @Autowired
    private com.ljwx.modules.health.service.HealthPredictionService healthPredictionService;
    
    @Autowired
    private com.ljwx.modules.health.service.HealthRecommendationService healthRecommendationService;
    
    @Autowired
    private com.ljwx.modules.health.service.UnifiedHealthBaselineService unifiedHealthBaselineService;
    
    @Autowired
    private com.ljwx.modules.health.service.HealthProfileService healthProfileService;
    
    private final DateTimeFormatter TABLE_SUFFIX_FORMATTER = DateTimeFormatter.ofPattern("yyyyMM");
    private final ExecutorService executorService = Executors.newFixedThreadPool(8); // #优化线程池大小
    
    // 健康特征字段配置 - 支持所有主要健康指标
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
        "pressure_low", "stress", "step", "calorie", "distance", "sleep"
    };

    /**
     * 0. 权重配置验证任务 - 每日01:00执行
     */
    @Scheduled(cron = "0 0 1 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void validateWeightConfigurations() {
        log.info("🔍 开始验证权重配置");
        
        try {
            weightCalculationService.validateAllCustomerWeights();
            log.info("✅ 权重配置验证完成");
        } catch (Exception e) {
            log.error("❌ 权重配置验证失败: {}", e.getMessage(), e);
            throw new RuntimeException("权重配置验证失败: " + e.getMessage(), e);
        }
    }

    /**
     * 1. 按月分表任务 - 每月1日凌晨执行
     * 支持现有的月度分表逻辑
     */
    @Scheduled(cron = "0 0 0 1 * ?")
    @Transactional(rollbackFor = Exception.class)
    public void archiveAndResetUserHealthTable() {
        LocalDate lastMonth = LocalDate.now().minusMonths(1);
        String suffix = lastMonth.format(TABLE_SUFFIX_FORMATTER);
        String archivedTable = "t_user_health_data_" + suffix;
        
        log.info("🔄 开始执行按月分表任务，目标表: {}", archivedTable);
        
        try {
            // 检查主表数据量
            Long recordCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM t_user_health_data", Long.class);
            log.info("📊 当前主表记录数: {}", recordCount);
            
            if (recordCount == null || recordCount == 0) {
                log.warn("⚠️ 主表无数据，跳过分表操作");
                return;
            }
            
            // 检查归档表是否已存在
            Integer tableExists = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?",
                Integer.class, archivedTable);
                
            if (tableExists != null && tableExists > 0) {
                log.warn("⚠️ 归档表 {} 已存在，跳过分表操作", archivedTable);
                return;
            }
            
            // 执行分表操作
            performTableArchiving(archivedTable, recordCount);
            
            log.info("🎉 按月分表任务完成，归档记录数: {}", recordCount);
            
        } catch (DataAccessException e) {
            log.error("❌ 按月分表失败，表名: {}, 错误: {}", archivedTable, e.getMessage(), e);
            throw new RuntimeException("归档表操作失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 执行表归档操作
     */
    private void performTableArchiving(String archivedTable, Long recordCount) {
        // Step 1: 重命名主表为归档表
        String renameSql = "RENAME TABLE t_user_health_data TO " + archivedTable;
        jdbcTemplate.execute(renameSql);
        log.info("✅ 已重命名 t_user_health_data 为 {}", archivedTable);

        // Step 2: 重建新主表
        String createSql = "CREATE TABLE t_user_health_data LIKE " + archivedTable;
        jdbcTemplate.execute(createSql);
        log.info("✅ 已重建空表 t_user_health_data");
        
        // Step 3: 创建归档表索引优化
        createArchiveTableIndexes(archivedTable);
        
        // Step 4: 更新表注释
        String suffix = archivedTable.replace("t_user_health_data_", "");
        String commentSql = String.format(
            "ALTER TABLE %s COMMENT = '健康数据归档表_%s'", 
            archivedTable, suffix);
        jdbcTemplate.execute(commentSql);
    }
    
    /**
     * 为归档表创建必要索引
     */
    private void createArchiveTableIndexes(String tableName) {
        try {
            String[] indexSqls = {
                String.format("CREATE INDEX idx_%s_device_time ON %s (device_sn, timestamp)", 
                    tableName.replace("t_user_health_data_", ""), tableName),
                String.format("CREATE INDEX idx_%s_org_time ON %s (org_id, timestamp)", 
                    tableName.replace("t_user_health_data_", ""), tableName),
                String.format("CREATE INDEX idx_%s_create_time ON %s (create_time)", 
                    tableName.replace("t_user_health_data_", ""), tableName)
            };
            
            for (String indexSql : indexSqls) {
                try {
                    jdbcTemplate.execute(indexSql);
                } catch (Exception e) {
                    log.warn("⚠️ 创建索引失败（可能已存在）: {}", e.getMessage());
                }
            }
            log.info("✅ 归档表索引创建完成: {}", tableName);
        } catch (Exception e) {
            log.error("❌ 创建归档表索引失败: {}", e.getMessage());
        }
    }

    /**
     * 2. 生成用户健康基线 - 每日02:00执行
     * 使用优化后的统一健康基线服务
     */
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateUserHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康基线（统一服务），日期: {}", dateStr);
        
        try {
            // 获取昨天有数据的用户列表
            List<Map<String, Object>> activeUsers = getActiveUsersForDate(dateStr);
            
            if (activeUsers.isEmpty()) {
                log.warn("⚠️ 日期 {} 无活跃用户，跳过基线生成", dateStr);
                return;
            }
            
            log.info("📊 找到 {} 个活跃用户需要生成基线", activeUsers.size());
            
            // 使用统一基线服务并行处理用户基线生成
            CompletableFuture<?>[] futures = activeUsers.stream()
                .map(user -> CompletableFuture.runAsync(() -> {
                    try {
                        Long userId = ((Number) user.get("user_id")).longValue();
                        Long customerId = ((Number) user.get("customer_id")).longValue();
                        
                        // 委托给优化的统一健康基线服务
                        unifiedHealthBaselineService.generatePersonalBaseline(userId, customerId, 30);
                        
                    } catch (Exception e) {
                        Long userId = ((Number) user.get("user_id")).longValue();
                        log.error("❌ 用户{}基线生成失败: {}", userId, e.getMessage());
                    }
                }, executorService))
                .toArray(CompletableFuture[]::new);
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 用户健康基线生成完成，日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 用户健康基线生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("用户健康基线生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 获取需要查询的健康数据表列表
     */
    private List<String> getHealthDataTables(LocalDate date) {
        List<String> potentialTables = HealthDataTableUtil.getTableNames(
            date.atStartOfDay(), 
            date.atTime(23, 59, 59));
        
        List<String> tables = new ArrayList<>();
        
        // 检查月表是否存在
        for (String tableName : potentialTables) {
            if (tableExists(tableName)) {
                tables.add(tableName);
                log.info("✅ 月表存在: {}", tableName);
            } else {
                log.warn("⚠️ 月表不存在，跳过: {}", tableName);
            }
        }
        
        // 添加主表
        tables.add("t_user_health_data");
        
        log.info("🔍 将查询以下表: {}", tables);
        return tables;
    }
    
    /**
     * 检查表是否存在
     */
    private boolean tableExists(String tableName) {
        try {
            Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?",
                Integer.class, tableName);
            return count != null && count > 0;
        } catch (Exception e) {
            log.warn("⚠️ 检查表存在性失败: {}, 错误: {}", tableName, e.getMessage());
            return false;
        }
    }
    
    /**
     * 获取指定表指定日期的健康数据数量
     */
    private Long getHealthDataCount(String tableName, String dateStr) {
        try {
            String sql = "SELECT COUNT(*) FROM " + tableName + " WHERE DATE(timestamp) = ?";
            return jdbcTemplate.queryForObject(sql, Long.class, dateStr);
        } catch (Exception e) {
            log.warn("⚠️ 查询表 {} 数据量失败: {}", tableName, e.getMessage());
            return 0L;
        }
    }
    
    /**
     * 生成单个特征的基线数据 - 支持多表查询
     */
    private void generateBaselineForFeatureMultiTable(List<String> tableNames, String feature, String date) {
        try {
            // 清理当日该特征的旧基线数据
            String deleteSql = """
                DELETE FROM t_health_baseline 
                WHERE feature_name = ? AND baseline_date = ?
                """;
            int deletedRows = jdbcTemplate.update(deleteSql, feature, date);
            if (deletedRows > 0) {
                log.info("🧹 清理旧基线数据: {} 特征, {} 条记录", feature, deletedRows);
            }
            
            // 构建多表联合查询的基线生成SQL - 只包含存在的表
            StringBuilder unionSql = new StringBuilder();
            boolean hasValidTables = false;
            
            for (String tableName : tableNames) {
                // 对于月表，检查是否存在；主表总是存在
                if (tableName.equals("t_user_health_data") || tableExists(tableName)) {
                    if (hasValidTables) {
                        unionSql.append(" UNION ALL ");
                    }
                    unionSql.append(buildSingleTableBaselineQuery(tableName, feature, date));
                    hasValidTables = true;
                } else {
                    log.warn("⚠️ 表 {} 不存在，跳过基线生成", tableName);
                }
            }
            
            if (!hasValidTables) {
                log.warn("⚠️ 没有可用的表用于生成基线，特征: {}, 日期: {}", feature, date);
                return;
            }
            
            String finalSql = String.format("""
                INSERT INTO t_health_baseline (
                    device_sn, user_id, org_id, feature_name, baseline_date, 
                    mean_value, std_value, min_value, max_value, sample_count, 
                    is_current, baseline_time, create_time, update_time
                )
                SELECT 
                    device_sn, 
                    COALESCE(user_id, 0) as user_id,
                    COALESCE(org_id, 1) as org_id,
                    '%s' as feature_name, 
                    '%s' as baseline_date,
                    AVG(value) as mean_value, 
                    GREATEST(COALESCE(STD(value), 0), %s) as std_value, 
                    MIN(value) as min_value, 
                    MAX(value) as max_value,
                    COUNT(*) as sample_count, 
                    1 as is_current, 
                    CURDATE() as baseline_time, 
                    NOW() as create_time, 
                    NOW() as update_time
                FROM (%s) as unified_data
                WHERE value IS NOT NULL AND value > 0
                GROUP BY device_sn, user_id, org_id
                HAVING COUNT(*) >= 3
                """, feature, date, getMinStandardDeviation(feature), unionSql.toString());
                
            int rows = jdbcTemplate.update(finalSql);
            log.info("✅ [基线-{}] 生成完成，共 {} 条记录", feature, rows);
            
        } catch (Exception e) {
            log.error("❌ [基线-{}] 生成失败: {}", feature, e.getMessage(), e);
        }
    }
    
    /**
     * 构建单表的基线查询SQL - 修复参数绑定问题，改进标准差计算
     */
    private String buildSingleTableBaselineQuery(String tableName, String feature, String date) {
        return String.format("""
            SELECT device_sn, user_id, org_id, %s as value, timestamp
            FROM %s 
            WHERE DATE(timestamp) = '%s'
            AND %s IS NOT NULL 
            AND %s > 0
            AND %s BETWEEN %s AND %s
            """, feature, tableName, date, feature, feature, feature, 
            getFeatureMinValue(feature), getFeatureMaxValue(feature));
    }
    
    /**
     * 获取特征的最小合理值
     */
    private double getFeatureMinValue(String feature) {
        return switch (feature) {
            case "heart_rate" -> 30.0;
            case "blood_oxygen" -> 70.0;  
            case "temperature" -> 30.0;
            case "pressure_high" -> 60.0;
            case "pressure_low" -> 40.0;
            case "stress" -> 0.0;
            case "step" -> 0.0;
            case "calorie" -> 0.0;
            case "distance" -> 0.0;
            case "sleep" -> 0.0;
            default -> 0.0;
        };
    }
    
    /**
     * 获取特征的最大合理值
     */
    private double getFeatureMaxValue(String feature) {
        return switch (feature) {
            case "heart_rate" -> 200.0;
            case "blood_oxygen" -> 100.0;
            case "temperature" -> 45.0;
            case "pressure_high" -> 250.0;
            case "pressure_low" -> 150.0;
            case "stress" -> 100.0;
            case "step" -> 50000.0;
            case "calorie" -> 5000.0;
            case "distance" -> 100.0;
            case "sleep" -> 24.0;
            default -> 10000.0;
        };
    }
    
    /**
     * 获取特征的最小标准差阈值，避免除零错误
     */
    private double getMinStandardDeviation(String feature) {
        return switch (feature) {
            case "heart_rate" -> 1.0;
            case "blood_oxygen" -> 0.5;
            case "temperature" -> 0.1;
            case "pressure_high" -> 2.0;
            case "pressure_low" -> 1.5;
            case "stress" -> 1.0;
            case "step" -> 100.0;
            case "calorie" -> 50.0;
            case "distance" -> 0.5;
            case "sleep" -> 0.2;
            default -> 0.1;
        };
    }

    /**
     * 3. 生成部门健康基线聚合 - 每日02:05执行 (利用组织闭包表)
     */
    @Scheduled(cron = "0 5 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthBaseline() {
        log.info("🔄 开始生成部门健康基线聚合 (基于组织闭包表)");
        
        try {
            departmentHealthAggregationJob.executeAggregation();
            log.info("🎉 部门健康基线聚合任务完成");
            
        } catch (Exception e) {
            log.error("❌ 部门健康基线聚合失败: {}", e.getMessage(), e);
            throw new RuntimeException("部门健康基线聚合失败: " + e.getMessage(), e);
        }
    }

    /**
     * 4. 生成组织健康基线 - 每日02:10执行
     * 使用统一健康基线服务
     */
    @Scheduled(cron = "0 10 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateOrgHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成组织健康基线（统一服务），日期: {}", dateStr);
        
        try {
            // 获取需要生成基线的组织列表
            List<Map<String, Object>> activeOrganizations = getActiveOrganizationsForDate(dateStr);
            
            if (activeOrganizations.isEmpty()) {
                log.warn("⚠️ 日期 {} 无活跃组织，跳过组织基线生成", dateStr);
                return;
            }
            
            log.info("📊 找到 {} 个活跃组织需要生成基线", activeOrganizations.size());
            
            // 使用统一基线服务并行处理组织基线生成
            CompletableFuture<?>[] futures = activeOrganizations.stream()
                .map(org -> CompletableFuture.runAsync(() -> {
                    try {
                        Long orgId = ((Number) org.get("org_id")).longValue();
                        Long customerId = ((Number) org.get("customer_id")).longValue();
                        
                        // 委托给优化的统一健康基线服务
                        unifiedHealthBaselineService.generateOrganizationBaseline(orgId, customerId, 90);
                        
                    } catch (Exception e) {
                        Long orgId = ((Number) org.get("org_id")).longValue();
                        log.error("❌ 组织{}基线生成失败: {}", orgId, e.getMessage());
                    }
                }, executorService))
                .toArray(CompletableFuture[]::new);
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 组织健康基线生成完成，日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 组织健康基线生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("组织健康基线生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 5. 生成部门健康评分 - 每日02:15执行 (基于部门基线)
     */
    @Scheduled(cron = "0 15 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthScore() {
        log.info("🔄 开始生成部门健康评分 (基于组织闭包表)");
        
        try {
            departmentHealthAggregationJob.generateDepartmentHealthScores();
            log.info("🎉 部门健康评分生成任务完成");
            
        } catch (Exception e) {
            log.error("❌ 部门健康评分生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("部门健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 6. 生成用户健康评分 - 每日04:00执行 (集成权重计算)
     */
    @Scheduled(cron = "0 0 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康评分，日期: {}", dateStr);
        
        try {
            // 首先更新权重缓存
            weightCalculationService.updateDailyWeights();
            
            List<String> tablesToQuery = getHealthDataTables(yesterday);
            
            // 检查是否有基线数据
            Long baselineCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM t_health_baseline WHERE baseline_date = ?",
                Long.class, dateStr);
                
            if (baselineCount == null || baselineCount == 0) {
                log.warn("⚠️ 日期 {} 无基线数据，跳过评分生成", dateStr);
                return;
            }
            
            // 清理当日旧评分数据
            String deleteSql = "DELETE FROM t_health_score WHERE score_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理旧评分数据: {} 条", deletedRows);
            }
            
            // 并行处理多个健康特征评分
            CompletableFuture<Void>[] futures = new CompletableFuture[HEALTH_FEATURES.length];
            
            for (int i = 0; i < HEALTH_FEATURES.length; i++) {
                final String feature = HEALTH_FEATURES[i];
                futures[i] = CompletableFuture.runAsync(() -> {
                    generateScoreForFeatureMultiTable(tablesToQuery, feature, dateStr);
                }, executorService);
            }
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 用户健康评分生成完成，日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 用户健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("用户健康评分生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 生成单个特征的评分数据 - 支持多表查询
     */
    private void generateScoreForFeatureMultiTable(List<String> tableNames, String feature, String date) {
        try {
            // 构建多表联合查询的评分SQL - 只包含存在的表
            StringBuilder unionSql = new StringBuilder();
            boolean hasValidTables = false;
            
            for (String tableName : tableNames) {
                // 对于月表，检查是否存在；主表总是存在
                if (tableName.equals("t_user_health_data") || tableExists(tableName)) {
                    if (hasValidTables) {
                        unionSql.append(" UNION ALL ");
                    }
                    unionSql.append(buildSingleTableScoreQuery(tableName, feature, date));
                    hasValidTables = true;
                } else {
                    log.warn("⚠️ 表 {} 不存在，跳过评分生成", tableName);
                }
            }
            
            if (!hasValidTables) {
                log.warn("⚠️ 没有可用的表用于生成评分，特征: {}, 日期: {}", feature, date);
                return;
            }
            
            String sql = String.format("""
                INSERT INTO t_health_score (
                    device_sn, user_id, org_id, feature_name, avg_value, z_score, 
                    score_value, penalty_value, baseline_time, score_date, 
                    create_time, update_time
                )
                SELECT 
                    h.device_sn,
                    COALESCE(h.user_id, 0) as user_id,
                    COALESCE(h.org_id, 1) as org_id,
                    '%s' as feature_name,
                    AVG(h.value) as avg_value,
                    CASE 
                        WHEN COALESCE(b.std_value, 0) > 0 
                        THEN GREATEST(-10, LEAST(10, (AVG(h.value) - b.mean_value) / b.std_value))
                        ELSE 0 
                    END as z_score,
                    GREATEST(0, LEAST(100, 
                        100 - ABS(
                            CASE 
                                WHEN COALESCE(b.std_value, 0) > 0 
                                THEN GREATEST(-10, LEAST(10, (AVG(h.value) - b.mean_value) / b.std_value))
                                ELSE 0 
                            END
                        ) * 10
                    )) as score_value,
                    CASE 
                        WHEN MAX(h.value) > b.max_value * 1.2 OR MIN(h.value) < b.min_value * 0.8 
                        THEN LEAST(20, ABS(
                            CASE 
                                WHEN MAX(h.value) > b.max_value * 1.2 
                                THEN (MAX(h.value) - b.max_value * 1.2) / b.max_value * 100
                                ELSE (b.min_value * 0.8 - MIN(h.value)) / b.min_value * 100
                            END
                        ))
                        ELSE 0 
                    END as penalty_value,
                    b.baseline_time,
                    DATE('%s') as score_date,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (%s) h
                JOIN t_health_baseline b ON h.device_sn = b.device_sn 
                    AND b.feature_name = '%s'
                    AND b.baseline_date = DATE('%s')
                WHERE h.value IS NOT NULL AND h.value > 0
                GROUP BY h.device_sn, h.user_id, h.org_id, b.mean_value, b.std_value, 
                         b.max_value, b.min_value, b.baseline_time
                HAVING COUNT(*) >= 3
                """, feature, date, unionSql.toString(), feature, date);
                
            int rows = jdbcTemplate.update(sql);
            log.info("✅ [评分-{}] 生成完成，共 {} 条记录", feature, rows);
            
        } catch (Exception e) {
            log.error("❌ [评分-{}] 生成失败: {}", feature, e.getMessage(), e);
        }
    }
    
    /**
     * 构建单表的评分查询SQL - 修复参数绑定问题，统一数据过滤条件
     */
    private String buildSingleTableScoreQuery(String tableName, String feature, String date) {
        return String.format("""
            SELECT device_sn, user_id, org_id, %s as value
            FROM %s 
            WHERE DATE(timestamp) = '%s'
            AND %s IS NOT NULL 
            AND %s > 0
            AND %s BETWEEN %s AND %s
            """, feature, tableName, date, feature, feature, feature,
            getFeatureMinValue(feature), getFeatureMaxValue(feature));
    }

    /**
     * 7. 生成组织健康评分 - 每日04:10执行
     */
    @Scheduled(cron = "0 10 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateOrgHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成组织健康评分，日期: {}", dateStr);
        
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_score WHERE score_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理组织旧评分数据: {} 条", deletedRows);
            }
            
            String sql = """
                INSERT INTO t_org_health_score (
                    org_id, feature_name, score_date, mean_score, std_score,
                    min_score, max_score, user_count, create_time, update_time
                )
                SELECT 
                    s.org_id, 
                    s.feature_name, 
                    s.score_date,
                    AVG(s.score_value - s.penalty_value) as mean_score, 
                    COALESCE(STD(s.score_value - s.penalty_value), 0) as std_score,
                    MIN(s.score_value - s.penalty_value) as min_score, 
                    MAX(s.score_value - s.penalty_value) as max_score,
                    COUNT(DISTINCT s.device_sn) as user_count, 
                    NOW() as create_time, 
                    NOW() as update_time
                FROM t_health_score s
                WHERE s.score_date = ?
                GROUP BY s.org_id, s.feature_name
                HAVING COUNT(DISTINCT s.device_sn) >= 2
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            log.info("🎉 组织健康评分生成完成，日期: {}, 共 {} 条记录", dateStr, rows);
            
        } catch (Exception e) {
            log.error("❌ 组织健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("组织健康评分生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 8. 生成健康预测 - 每日05:30执行
     */
    @Scheduled(cron = "0 30 5 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthPredictions() {
        log.info("🔮 开始生成健康预测");
        
        try {
            // 获取所有活跃用户
            List<Map<String, Object>> activeUsers = getActiveUsersForPrediction();
            log.info("📊 找到 {} 个用户需要生成健康预测", activeUsers.size());
            
            int processedUsers = 0;
            int successfulPredictions = 0;
            int failedPredictions = 0;
            
            for (Map<String, Object> user : activeUsers) {
                try {
                    Long userId = ((Number) user.get("user_id")).longValue();
                    Long customerId = ((Number) user.get("customer_id")).longValue();
                    
                    // 生成健康趋势预测（30天预测窗口）
                    List<?> trendPredictions = healthPredictionService.generateHealthTrendPredictions(
                        userId, customerId, 30);
                    
                    // 生成健康风险评估
                    List<?> riskAssessments = healthPredictionService.generateRiskAssessmentPredictions(
                        userId, customerId);
                    
                    successfulPredictions += (trendPredictions != null ? trendPredictions.size() : 0);
                    successfulPredictions += (riskAssessments != null ? riskAssessments.size() : 0);
                    processedUsers++;
                    
                    log.debug("✅ 用户 {} 预测生成完成", userId);
                    
                } catch (Exception e) {
                    Long userId = ((Number) user.get("user_id")).longValue();
                    log.warn("⚠️ 用户 {} 预测生成失败: {}", userId, e.getMessage());
                    failedPredictions++;
                }
                
                // 批次间短暂休息，避免数据库压力
                if (processedUsers % 20 == 0) {
                    Thread.sleep(500);
                }
            }
            
            log.info("🎉 健康预测生成完成 - 处理用户: {}, 成功预测: {}, 失败: {}", 
                processedUsers, successfulPredictions, failedPredictions);
                
        } catch (Exception e) {
            log.error("❌ 健康预测生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康预测生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 9. 生成健康建议 - 每日06:00执行
     */
    @Scheduled(cron = "0 0 6 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthRecommendations() {
        log.info("💡 开始生成健康建议");
        
        try {
            // 委托给专用的健康建议服务
            healthRecommendationService.generateDailyRecommendations();
            log.info("🎉 健康建议生成任务完成");
            
        } catch (Exception e) {
            log.error("❌ 健康建议生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康建议生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 10. 生成健康画像 - 每日06:30执行
     */
    @Scheduled(cron = "0 30 6 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthProfiles() {
        log.info("🎨 开始生成健康画像");
        
        try {
            // 获取所有活跃用户
            List<Map<String, Object>> activeUsers = getActiveUsersForProcessing();
            log.info("📊 找到 {} 个用户需要生成健康画像", activeUsers.size());
            
            int processedUsers = 0;
            int successfulProfiles = 0;
            int failedProfiles = 0;
            
            for (Map<String, Object> user : activeUsers) {
                try {
                    Long userId = ((Number) user.get("user_id")).longValue();
                    Long customerId = ((Number) user.get("customer_id")).longValue();
                    
                    // 生成用户健康画像
                    boolean profileGenerated = healthProfileService.generateUserHealthProfile(
                        userId, customerId, LocalDate.now());
                    
                    if (profileGenerated) {
                        successfulProfiles++;
                        log.debug("✅ 用户 {} 健康画像生成完成", userId);
                    } else {
                        failedProfiles++;
                        log.warn("⚠️ 用户 {} 健康画像生成失败", userId);
                    }
                    
                    processedUsers++;
                    
                } catch (Exception e) {
                    Long userId = ((Number) user.get("user_id")).longValue();
                    log.warn("⚠️ 用户 {} 健康画像生成异常: {}", userId, e.getMessage());
                    failedProfiles++;
                }
                
                // 批次间短暂休息，避免数据库压力
                if (processedUsers % 20 == 0) {
                    Thread.sleep(500);
                }
            }
            
            log.info("🎉 健康画像生成完成 - 处理用户: {}, 成功生成: {}, 失败: {}", 
                processedUsers, successfulProfiles, failedProfiles);
                
        } catch (Exception e) {
            log.error("❌ 健康画像生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康画像生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 11. 数据清理任务 - 每日07:00执行
     */
    @Scheduled(cron = "0 0 7 * * ?")
    public void cleanupOldData() {
        log.info("🔄 开始执行数据清理任务");
        
        try {
            LocalDate cutoffDate = LocalDate.now().minusDays(90); // 保留90天数据
            String cutoffDateStr = cutoffDate.toString();
            
            // 清理过期基线数据
            String cleanBaseline = "DELETE FROM t_health_baseline WHERE baseline_date < ? AND is_current = 0";
            int baselineDeleted = jdbcTemplate.update(cleanBaseline, cutoffDateStr);
            
            // 清理过期评分数据
            String cleanScore = "DELETE FROM t_health_score WHERE score_date < ?";
            int scoreDeleted = jdbcTemplate.update(cleanScore, cutoffDateStr);
            
            // 清理过期组织数据
            String cleanOrgBaseline = "DELETE FROM t_org_health_baseline WHERE baseline_date < ?";
            int orgBaselineDeleted = jdbcTemplate.update(cleanOrgBaseline, cutoffDateStr);
            
            String cleanOrgScore = "DELETE FROM t_org_health_score WHERE score_date < ?";
            int orgScoreDeleted = jdbcTemplate.update(cleanOrgScore, cutoffDateStr);
            
            // 清理过期任务日志
            String cleanTaskLog = "DELETE FROM t_health_task_log WHERE create_time < DATE_SUB(NOW(), INTERVAL 30 DAY)";
            int taskLogDeleted = jdbcTemplate.update(cleanTaskLog);
            
            log.info("🎉 数据清理完成 - 基线: {} 条, 评分: {} 条, 组织基线: {} 条, 组织评分: {} 条, 任务日志: {} 条", 
                baselineDeleted, scoreDeleted, orgBaselineDeleted, orgScoreDeleted, taskLogDeleted);
            
            // 异常值检测和预警
            performAnomalyDetection();
            
        } catch (Exception e) {
            log.error("❌ 数据清理失败: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 异常值检测和预警机制
     */
    private void performAnomalyDetection() {
        log.info("🔍 开始异常值检测");
        
        try {
            LocalDate yesterday = LocalDate.now().minusDays(1);
            String dateStr = yesterday.toString();
            
            // 1. 检测基线异常值
            String baselineAnomalyQuery = """
                SELECT device_sn, feature_name, mean_value, std_value, sample_count
                FROM t_health_baseline 
                WHERE baseline_date = ?
                AND (
                    std_value = 0 OR std_value IS NULL OR
                    sample_count < 10 OR
                    mean_value <= 0 OR mean_value > 10000
                )
                """;
            
            List<Map<String, Object>> baselineAnomalies = jdbcTemplate.queryForList(baselineAnomalyQuery, dateStr);
            
            if (!baselineAnomalies.isEmpty()) {
                log.warn("⚠️ 发现 {} 条基线异常数据:", baselineAnomalies.size());
                for (Map<String, Object> anomaly : baselineAnomalies) {
                    log.warn("  设备: {}, 特征: {}, 均值: {}, 标准差: {}, 样本数: {}", 
                        anomaly.get("device_sn"), anomaly.get("feature_name"), 
                        anomaly.get("mean_value"), anomaly.get("std_value"), anomaly.get("sample_count"));
                }
            }
            
            // 2. 检测评分异常值
            String scoreAnomalyQuery = """
                SELECT device_sn, feature_name, score_value, z_score, penalty_value
                FROM t_health_score 
                WHERE score_date = ?
                AND (
                    ABS(z_score) > 5 OR 
                    score_value < 0 OR score_value > 100 OR
                    penalty_value > 50
                )
                """;
            
            List<Map<String, Object>> scoreAnomalies = jdbcTemplate.queryForList(scoreAnomalyQuery, dateStr);
            
            if (!scoreAnomalies.isEmpty()) {
                log.warn("⚠️ 发现 {} 条评分异常数据:", scoreAnomalies.size());
                for (Map<String, Object> anomaly : scoreAnomalies) {
                    log.warn("  设备: {}, 特征: {}, 评分: {}, Z分数: {}, 惩罚: {}", 
                        anomaly.get("device_sn"), anomaly.get("feature_name"), 
                        anomaly.get("score_value"), anomaly.get("z_score"), anomaly.get("penalty_value"));
                }
                
                // 自动修复极端Z分数
                fixExtremeZScores(dateStr);
            }
            
            // 3. 检测数据覆盖率
            checkDataCoverage(dateStr);
            
            log.info("✅ 异常值检测完成");
            
        } catch (Exception e) {
            log.error("❌ 异常值检测失败: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 修复极端Z分数
     */
    private void fixExtremeZScores(String date) {
        try {
            String fixQuery = """
                UPDATE t_health_score 
                SET z_score = GREATEST(-10, LEAST(10, z_score)),
                    score_value = GREATEST(0, LEAST(100, 
                        100 - ABS(GREATEST(-10, LEAST(10, z_score))) * 10
                    )),
                    update_time = NOW()
                WHERE score_date = ? AND ABS(z_score) > 10
                """;
                
            int fixedRows = jdbcTemplate.update(fixQuery, date);
            if (fixedRows > 0) {
                log.info("🔧 已修复 {} 条极端Z分数记录", fixedRows);
            }
        } catch (Exception e) {
            log.error("❌ 修复极端Z分数失败: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 检测数据覆盖率
     */
    private void checkDataCoverage(String date) {
        try {
            // 检查每个特征的覆盖率
            for (String feature : HEALTH_FEATURES) {
                String coverageQuery = """
                    SELECT 
                        COUNT(DISTINCT b.device_sn) as baseline_users,
                        COUNT(DISTINCT s.device_sn) as score_users,
                        (SELECT COUNT(DISTINCT device_sn) 
                         FROM t_user_health_data 
                         WHERE DATE(timestamp) = ? 
                         AND %s IS NOT NULL AND %s > 0) as total_users
                    FROM t_health_baseline b
                    LEFT JOIN t_health_score s ON b.device_sn = s.device_sn 
                        AND b.feature_name = s.feature_name 
                        AND b.baseline_date = s.score_date
                    WHERE b.baseline_date = ? AND b.feature_name = ?
                    """.formatted(feature, feature);
                    
                Map<String, Object> coverage = jdbcTemplate.queryForMap(coverageQuery, date, date, feature);
                
                int baselineUsers = ((Number) coverage.get("baseline_users")).intValue();
                int scoreUsers = ((Number) coverage.get("score_users")).intValue();  
                int totalUsers = ((Number) coverage.get("total_users")).intValue();
                
                if (totalUsers > 0) {
                    double baselineCoverage = (double) baselineUsers / totalUsers * 100;
                    double scoreCoverage = (double) scoreUsers / totalUsers * 100;
                    
                    if (baselineCoverage < 80 || scoreCoverage < 80) {
                        log.warn("⚠️ 特征 {} 覆盖率不足: 基线 {:.1f}%, 评分 {:.1f}% (总用户: {})", 
                            feature, baselineCoverage, scoreCoverage, totalUsers);
                    }
                }
            }
        } catch (Exception e) {
            log.error("❌ 数据覆盖率检测失败: {}", e.getMessage(), e);
        }
    }
    
    /**
     * 获取需要生成预测的活跃用户列表
     */
    private List<Map<String, Object>> getActiveUsersForPrediction() {
        try {
            String sql = """
                SELECT DISTINCT 
                    u.user_id, 
                    u.customer_id, 
                    COUNT(*) as data_count
                FROM t_user_health_data u
                WHERE u.timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                AND u.is_deleted = 0
                AND (u.heart_rate > 0 OR u.blood_oxygen > 0 OR u.temperature > 0)
                GROUP BY u.user_id, u.customer_id
                HAVING data_count >= 10
                ORDER BY data_count DESC
                """;
            
            return jdbcTemplate.queryForList(sql);
            
        } catch (Exception e) {
            log.error("❌ 获取预测用户列表失败: {}", e.getMessage(), e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 获取指定日期的活跃用户列表（用于基线生成）
     */
    private List<Map<String, Object>> getActiveUsersForDate(String dateStr) {
        try {
            // 检查所有相关表，只获取有健康数据的用户ID
            List<String> tables = getHealthDataTables(LocalDate.parse(dateStr));
            StringBuilder unionQuery = new StringBuilder();
            
            for (int i = 0; i < tables.size(); i++) {
                if (i > 0) unionQuery.append(" UNION ALL ");
                
                unionQuery.append(String.format("""
                    SELECT DISTINCT user_id
                    FROM %s 
                    WHERE DATE(timestamp) = '%s'
                    AND is_deleted = 0
                    AND user_id > 0
                    AND (heart_rate > 0 OR blood_oxygen > 0 OR temperature > 0 
                         OR pressure_high > 0 OR pressure_low > 0)
                    """, tables.get(i), dateStr));
            }
            
            String userIdsSql = String.format("""
                SELECT DISTINCT user_id
                FROM (%s) unified_users
                ORDER BY user_id
                """, unionQuery.toString());
            
            List<Map<String, Object>> healthUsers = jdbcTemplate.queryForList(userIdsSql);
            List<Map<String, Object>> result = new ArrayList<>();
            
            // 为每个有健康数据的用户查询正确的customerId
            for (Map<String, Object> healthUser : healthUsers) {
                Long userId = ((Number) healthUser.get("user_id")).longValue();
                
                // 查询用户的正确customerId
                Long customerId = getUserCustomerId(userId);
                if (customerId != null) {
                    Map<String, Object> userInfo = new HashMap<>();
                    userInfo.put("user_id", userId);
                    userInfo.put("customer_id", customerId);
                    result.add(userInfo);
                }
            }
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 获取活跃用户列表失败: date={}, error={}", dateStr, e.getMessage(), e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 获取活跃用户列表（用于健康画像处理）
     */
    private List<Map<String, Object>> getActiveUsersForProcessing() {
        try {
            // 首先获取有健康数据的活跃用户
            String healthDataSql = """
                SELECT DISTINCT 
                    u.user_id,
                    COUNT(*) as data_count
                FROM t_user_health_data u
                WHERE u.timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                AND u.is_deleted = 0
                AND u.user_id > 0
                AND (u.heart_rate > 0 OR u.blood_oxygen > 0 OR u.temperature > 0 
                     OR u.pressure_high > 0 OR u.pressure_low > 0)
                GROUP BY u.user_id
                HAVING data_count >= 3
                """;
            
            List<Map<String, Object>> healthUsers = jdbcTemplate.queryForList(healthDataSql);
            List<Map<String, Object>> result = new ArrayList<>();
            
            // 为每个有健康数据的用户查询正确的customerId
            for (Map<String, Object> healthUser : healthUsers) {
                Long userId = ((Number) healthUser.get("user_id")).longValue();
                Long dataCount = ((Number) healthUser.get("data_count")).longValue();
                
                // 查询用户的正确customerId
                Long customerId = getUserCustomerId(userId);
                if (customerId != null) {
                    Map<String, Object> userInfo = new HashMap<>();
                    userInfo.put("user_id", userId);
                    userInfo.put("customer_id", customerId);
                    userInfo.put("data_count", dataCount);
                    result.add(userInfo);
                }
            }
            
            // 按数据量排序
            result.sort((a, b) -> {
                Long countA = ((Number) a.get("data_count")).longValue();
                Long countB = ((Number) b.get("data_count")).longValue();
                return countB.compareTo(countA);
            });
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 获取处理用户列表失败: {}", e.getMessage(), e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 根据用户ID获取正确的customerId
     * 逻辑：从用户所在部门向上查询到顶级部门ID作为customerId
     */
    private Long getUserCustomerId(Long userId) {
        try {
            // 首先尝试从sys_user表直接获取customerId
            String userSql = "SELECT customer_id FROM sys_user WHERE user_id = ? AND is_deleted = 0";
            List<Map<String, Object>> userResults = jdbcTemplate.queryForList(userSql, userId);
            
            if (!userResults.isEmpty()) {
                Object customerIdObj = userResults.get(0).get("customer_id");
                if (customerIdObj != null && !customerIdObj.equals(0L)) {
                    Long customerId = ((Number) customerIdObj).longValue();
                    log.debug("✅ 用户 {} 从sys_user表获取customerId: {}", userId, customerId);
                    return customerId;
                }
            }
            
            // 如果sys_user表中没有customerId，则从用户组织关系查询
            String orgSql = """
                SELECT DISTINCT uo.customer_id 
                FROM sys_user_org uo 
                WHERE uo.user_id = ? 
                AND uo.is_deleted = 0 
                AND uo.customer_id IS NOT NULL 
                AND uo.customer_id > 0
                LIMIT 1
                """;
            
            List<Map<String, Object>> orgResults = jdbcTemplate.queryForList(orgSql, userId);
            if (!orgResults.isEmpty()) {
                Object customerIdObj = orgResults.get(0).get("customer_id");
                if (customerIdObj != null) {
                    Long customerId = ((Number) customerIdObj).longValue();
                    log.debug("✅ 用户 {} 从sys_user_org表获取customerId: {}", userId, customerId);
                    
                    // 同步更新sys_user表的customerId
                    updateUserCustomerId(userId, customerId);
                    return customerId;
                }
            }
            
            // 如果仍然没有找到，尝试从用户的顶级部门查询
            Long topOrgId = getUserTopOrganizationId(userId);
            if (topOrgId != null) {
                log.debug("✅ 用户 {} 从顶级部门获取customerId: {}", userId, topOrgId);
                
                // 同步更新sys_user和sys_user_org表的customerId
                updateUserCustomerId(userId, topOrgId);
                updateUserOrgCustomerId(userId, topOrgId);
                return topOrgId;
            }
            
            log.warn("⚠️ 无法获取用户 {} 的customerId，使用默认值1", userId);
            return 1L; // 默认值
            
        } catch (Exception e) {
            log.error("❌ 获取用户 {} customerId失败: {}", userId, e.getMessage(), e);
            return 1L; // 默认值
        }
    }
    
    /**
     * 获取用户的顶级组织ID
     */
    private Long getUserTopOrganizationId(Long userId) {
        try {
            String sql = """
                WITH RECURSIVE org_hierarchy AS (
                    -- 获取用户直接所属的组织
                    SELECT o.org_id, o.parent_id, 1 as level
                    FROM sys_user_org uo
                    JOIN sys_org o ON uo.org_id = o.org_id
                    WHERE uo.user_id = ? AND uo.is_deleted = 0 AND o.is_deleted = 0
                    
                    UNION ALL
                    
                    -- 递归查询父级组织
                    SELECT o.org_id, o.parent_id, oh.level + 1
                    FROM sys_org o
                    JOIN org_hierarchy oh ON o.org_id = oh.parent_id
                    WHERE o.is_deleted = 0 AND oh.level < 10
                )
                SELECT org_id 
                FROM org_hierarchy 
                WHERE parent_id IS NULL OR parent_id = 0
                ORDER BY level DESC
                LIMIT 1
                """;
            
            List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, userId);
            if (!results.isEmpty()) {
                return ((Number) results.get(0).get("org_id")).longValue();
            }
            
            // 如果没有找到递归结果，尝试简单查询
            String simpleSql = """
                SELECT uo.org_id
                FROM sys_user_org uo
                WHERE uo.user_id = ? AND uo.is_deleted = 0
                LIMIT 1
                """;
            
            List<Map<String, Object>> simpleResults = jdbcTemplate.queryForList(simpleSql, userId);
            if (!simpleResults.isEmpty()) {
                return ((Number) simpleResults.get(0).get("org_id")).longValue();
            }
            
            return null;
            
        } catch (Exception e) {
            log.error("❌ 获取用户 {} 顶级组织失败: {}", userId, e.getMessage(), e);
            return null;
        }
    }
    
    /**
     * 更新用户表的customerId
     */
    private void updateUserCustomerId(Long userId, Long customerId) {
        try {
            String updateSql = "UPDATE sys_user SET customer_id = ? WHERE user_id = ?";
            int updated = jdbcTemplate.update(updateSql, customerId, userId);
            if (updated > 0) {
                log.debug("✅ 已更新用户 {} 的customerId为 {}", userId, customerId);
            }
        } catch (Exception e) {
            log.warn("⚠️ 更新用户 {} customerId失败: {}", userId, e.getMessage());
        }
    }
    
    /**
     * 更新用户组织关系表的customerId
     */
    private void updateUserOrgCustomerId(Long userId, Long customerId) {
        try {
            String updateSql = "UPDATE sys_user_org SET customer_id = ? WHERE user_id = ? AND customer_id IS NULL";
            int updated = jdbcTemplate.update(updateSql, customerId, userId);
            if (updated > 0) {
                log.debug("✅ 已更新用户组织关系 {} 的customerId为 {}", userId, customerId);
            }
        } catch (Exception e) {
            log.warn("⚠️ 更新用户组织关系 {} customerId失败: {}", userId, e.getMessage());
        }
    }
    
    /**
     * 获取组织的customerId
     * 逻辑：向上查询到顶级部门ID作为customerId
     */
    private Long getOrganizationCustomerId(Long orgId) {
        try {
            // 递归查询到顶级组织
            String sql = """
                WITH RECURSIVE org_hierarchy AS (
                    -- 起始组织
                    SELECT org_id, parent_id, 1 as level
                    FROM sys_org
                    WHERE org_id = ? AND is_deleted = 0
                    
                    UNION ALL
                    
                    -- 递归查询父级组织
                    SELECT o.org_id, o.parent_id, oh.level + 1
                    FROM sys_org o
                    JOIN org_hierarchy oh ON o.org_id = oh.parent_id
                    WHERE o.is_deleted = 0 AND oh.level < 10
                )
                SELECT org_id 
                FROM org_hierarchy 
                WHERE parent_id IS NULL OR parent_id = 0
                ORDER BY level DESC
                LIMIT 1
                """;
            
            List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, orgId);
            if (!results.isEmpty()) {
                Long topOrgId = ((Number) results.get(0).get("org_id")).longValue();
                log.debug("✅ 组织 {} 的顶级组织customerId: {}", orgId, topOrgId);
                return topOrgId;
            }
            
            // 如果没有找到递归结果，则使用当前组织ID
            log.debug("✅ 组织 {} 作为customerId（无父级）", orgId);
            return orgId;
            
        } catch (Exception e) {
            log.error("❌ 获取组织 {} customerId失败: {}", orgId, e.getMessage(), e);
            return orgId; // 默认使用当前组织ID
        }
    }
    
    /**
     * 获取指定日期的活跃组织列表（用于基线生成）
     */
    private List<Map<String, Object>> getActiveOrganizationsForDate(String dateStr) {
        try {
            // 检查所有相关表，获取有健康数据的组织ID
            List<String> tables = getHealthDataTables(LocalDate.parse(dateStr));
            StringBuilder unionQuery = new StringBuilder();
            
            for (int i = 0; i < tables.size(); i++) {
                if (i > 0) unionQuery.append(" UNION ALL ");
                
                unionQuery.append(String.format("""
                    SELECT DISTINCT org_id, user_id
                    FROM %s 
                    WHERE DATE(timestamp) = '%s'
                    AND is_deleted = 0
                    AND org_id > 0
                    AND user_id > 0
                    AND (heart_rate > 0 OR blood_oxygen > 0 OR temperature > 0)
                    """, tables.get(i), dateStr));
            }
            
            String orgUsersSql = String.format("""
                SELECT org_id, COUNT(DISTINCT user_id) as user_count
                FROM (%s) unified_orgs
                GROUP BY org_id
                HAVING user_count >= 2
                ORDER BY org_id
                """, unionQuery.toString());
            
            List<Map<String, Object>> orgUsers = jdbcTemplate.queryForList(orgUsersSql);
            List<Map<String, Object>> result = new ArrayList<>();
            
            // 为每个活跃组织获取正确的customerId
            for (Map<String, Object> orgData : orgUsers) {
                Long orgId = ((Number) orgData.get("org_id")).longValue();
                Long userCount = ((Number) orgData.get("user_count")).longValue();
                
                // 获取组织的customerId（可以从组织的顶级部门获取）
                Long customerId = getOrganizationCustomerId(orgId);
                if (customerId != null) {
                    Map<String, Object> orgInfo = new HashMap<>();
                    orgInfo.put("org_id", orgId);
                    orgInfo.put("customer_id", customerId);
                    orgInfo.put("user_count", userCount);
                    result.add(orgInfo);
                }
            }
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 获取活跃组织列表失败: date={}, error={}", dateStr, e.getMessage(), e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 手动触发基线生成（支持多表查询）
     */
    public void manualGenerateBaseline(String startDate, String endDate) {
        log.info("🔧 手动触发基线生成，时间范围: {} - {}", startDate, endDate);
        
        try {
            LocalDate start = LocalDate.parse(startDate);
            LocalDate end = LocalDate.parse(endDate);
            
            while (!start.isAfter(end)) {
                String dateStr = start.toString();
                List<String> tablesToQuery = getHealthDataTables(start);
                
                for (String feature : HEALTH_FEATURES) {
                    generateBaselineForFeatureMultiTable(tablesToQuery, feature, dateStr);
                }
                
                start = start.plusDays(1);
            }
            
            log.info("🎉 手动基线生成完成");
            
        } catch (Exception e) {
            log.error("❌ 手动基线生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("手动基线生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 手动触发评分生成（支持多表查询）
     */
    public void manualGenerateScore(String startDate, String endDate) {
        log.info("🔧 手动触发评分生成，时间范围: {} - {}", startDate, endDate);
        
        try {
            LocalDate start = LocalDate.parse(startDate);
            LocalDate end = LocalDate.parse(endDate);
            
            while (!start.isAfter(end)) {
                String dateStr = start.toString();
                List<String> tablesToQuery = getHealthDataTables(start);
                
                for (String feature : HEALTH_FEATURES) {
                    generateScoreForFeatureMultiTable(tablesToQuery, feature, dateStr);
                }
                
                start = start.plusDays(1);
            }
            
            log.info("🎉 手动评分生成完成");
            
        } catch (Exception e) {
            log.error("❌ 手动评分生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("手动评分生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 补充生成最近2个月的健康基线和评分
     */
    public void generateRecentBaselinesAndScores() {
        log.info("🔧 开始补充生成最近2个月的健康基线和评分");
        
        try {
            LocalDate endDate = LocalDate.now().minusDays(1); // 昨天
            LocalDate startDate = endDate.minusMonths(2); // 2个月前
            
            log.info("📅 生成时间范围: {} 到 {}", startDate, endDate);
            
            // 1. 生成用户基线
            log.info("🔄 开始生成用户基线...");
            manualGenerateBaseline(startDate.toString(), endDate.toString());
            
            // 2. 生成组织基线
            log.info("🔄 开始生成组织基线...");
            LocalDate current = startDate;
            while (!current.isAfter(endDate)) {
                generateOrgHealthBaselineForDate(current.toString());
                current = current.plusDays(1);
            }
            
            // 3. 生成用户评分
            log.info("🔄 开始生成用户评分...");
            manualGenerateScore(startDate.toString(), endDate.toString());
            
            // 4. 生成组织评分
            log.info("🔄 开始生成组织评分...");
            current = startDate;
            while (!current.isAfter(endDate)) {
                generateOrgHealthScoreForDate(current.toString());
                current = current.plusDays(1);
            }
            
            log.info("🎉 最近2个月健康基线和评分补充生成完成");
            
        } catch (Exception e) {
            log.error("❌ 补充生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("补充生成失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 生成指定日期的组织健康基线
     */
    private void generateOrgHealthBaselineForDate(String dateStr) {
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_baseline WHERE baseline_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理组织旧基线数据: {} 条 ({})", deletedRows, dateStr);
            }
            
            // 生成新的组织基线
            String sql = """
                INSERT INTO t_org_health_baseline (
                    org_id, feature_name, baseline_date, mean_value, std_value,
                    min_value, max_value, user_count, sample_count, create_time, update_time
                )
                SELECT 
                    b.org_id, 
                    b.feature_name, 
                    b.baseline_date,
                    AVG(b.mean_value) as mean_value, 
                    COALESCE(STD(b.mean_value), 0) as std_value, 
                    MIN(b.min_value) as min_value, 
                    MAX(b.max_value) as max_value,
                    COUNT(DISTINCT b.device_sn) as user_count, 
                    SUM(b.sample_count) as sample_count, 
                    NOW() as create_time, 
                    NOW() as update_time
                FROM t_health_baseline b
                WHERE b.baseline_date = ?
                GROUP BY b.org_id, b.feature_name
                HAVING COUNT(DISTINCT b.device_sn) >= 1
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            if (rows > 0) {
                log.info("✅ 组织基线生成: {} 共 {} 条记录", dateStr, rows);
            }
            
        } catch (Exception e) {
            log.error("❌ 组织基线生成失败，日期: {}, 错误: {}", dateStr, e.getMessage());
        }
    }
    
    /**
     * 生成指定日期的组织健康评分
     */
    private void generateOrgHealthScoreForDate(String dateStr) {
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_score WHERE score_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理组织旧评分数据: {} 条 ({})", deletedRows, dateStr);
            }
            
            String sql = """
                INSERT INTO t_org_health_score (
                    org_id, feature_name, score_date, mean_score, std_score,
                    min_score, max_score, user_count, create_time, update_time
                )
                SELECT 
                    s.org_id, 
                    s.feature_name, 
                    s.score_date,
                    AVG(s.score_value - s.penalty_value) as mean_score, 
                    COALESCE(STD(s.score_value - s.penalty_value), 0) as std_score,
                    MIN(s.score_value - s.penalty_value) as min_score, 
                    MAX(s.score_value - s.penalty_value) as max_score,
                    COUNT(DISTINCT s.device_sn) as user_count, 
                    NOW() as create_time, 
                    NOW() as update_time
                FROM t_health_score s
                WHERE s.score_date = ?
                GROUP BY s.org_id, s.feature_name
                HAVING COUNT(DISTINCT s.device_sn) >= 1
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            if (rows > 0) {
                log.info("✅ 组织评分生成: {} 共 {} 条记录", dateStr, rows);
            }
            
        } catch (Exception e) {
            log.error("❌ 组织评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage());
        }
    }
    
    /**
     * 销毁资源
     */
    public void destroy() {
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
            log.info("🔒 健康任务线程池已关闭");
        }
    }
} 