package com.ljwx.modules.health.task;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.ljwx.modules.health.util.HealthDataTableUtil;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 改进的健康数据基线和评分定时任务 - 统一表结构，层级聚合
 * 
 * 主要改进：
 * 1. 统一以userId为主键查询健康数据，生成用户级基线
 * 2. 基于组织闭包表实现部门级聚合（用户→部门→租户）
 * 3. 优化数据查询性能，支持分表架构
 * 4. 加强数据质量检查和异常处理
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.task.ImprovedHealthBaselineScoreTasks
 * @CreateTime 2025-09-08
 */
@Slf4j
@Component
public class ImprovedHealthBaselineScoreTasks {

    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private com.ljwx.modules.health.service.WeightCalculationService weightCalculationService;
    
    @Autowired
    private com.ljwx.modules.health.service.HealthRecommendationService healthRecommendationService;
    
    private final DateTimeFormatter TABLE_SUFFIX_FORMATTER = DateTimeFormatter.ofPattern("yyyyMM");
    private final ExecutorService executorService = Executors.newFixedThreadPool(10); // 优化线程池大小
    
    // 健康特征字段配置 - 支持所有主要健康指标
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
        "pressure_low", "stress", "step", "calorie", "distance", "sleep"
    };

    /**
     * 1. 生成用户健康基线 - 基于userId统一查询 - 每日02:00执行
     * 改进：统一使用userId作为主要标识，支持多表查询
     */
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateUserHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康基线（改进版-基于userId），日期: {}", dateStr);
        
        try {
            // 获取所有相关表数据
            List<String> tablesToQuery = getHealthDataTables(yesterday);
            Long totalDataCount = getTotalHealthDataCount(tablesToQuery, dateStr);
                
            if (totalDataCount == 0) {
                log.warn("⚠️ 日期 {} 无健康数据，跳过基线生成", dateStr);
                return;
            }
            
            log.info("📊 总计 {} 条健康数据记录", totalDataCount);
            
            // 并行处理多个健康特征
            CompletableFuture<Void>[] futures = new CompletableFuture[HEALTH_FEATURES.length];
            
            for (int i = 0; i < HEALTH_FEATURES.length; i++) {
                final String feature = HEALTH_FEATURES[i];
                futures[i] = CompletableFuture.runAsync(() -> {
                    generateUserBaselineForFeature(tablesToQuery, feature, dateStr);
                }, executorService);
            }
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures).join();
            
            // 数据质量检查
            performDataQualityCheck(dateStr);
            
            log.info("🎉 用户健康基线生成完成（改进版），日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 用户健康基线生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("用户健康基线生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 生成单个特征的用户基线数据 - 改进版：优先使用userId
     */
    private void generateUserBaselineForFeature(List<String> tableNames, String feature, String date) {
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
            
            // 构建优化的多表联合查询SQL - 优先使用userId分组
            StringBuilder unionSql = new StringBuilder();
            boolean hasValidTables = false;
            
            for (String tableName : tableNames) {
                if (tableName.equals("t_user_health_data") || tableExists(tableName)) {
                    if (hasValidTables) {
                        unionSql.append(" UNION ALL ");
                    }
                    unionSql.append(buildUserBaselineQuery(tableName, feature, date));
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
                    COALESCE(device_sn, CONCAT('USER_', user_id)) as device_sn,
                    user_id, 
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
                GROUP BY user_id, org_id
                HAVING COUNT(*) >= 5 AND user_id IS NOT NULL AND user_id > 0
                """, feature, date, getMinStandardDeviation(feature), unionSql.toString());
                
            int rows = jdbcTemplate.update(finalSql);
            log.info("✅ [用户基线-{}] 生成完成，共 {} 条记录", feature, rows);
            
        } catch (Exception e) {
            log.error("❌ [用户基线-{}] 生成失败: {}", feature, e.getMessage(), e);
        }
    }

    /**
     * 构建单表的用户基线查询SQL - 改进版：优先使用userId
     */
    private String buildUserBaselineQuery(String tableName, String feature, String date) {
        return String.format("""
            SELECT 
                device_sn, user_id, org_id, %s as value, timestamp
            FROM %s 
            WHERE DATE(timestamp) = '%s'
            AND user_id IS NOT NULL 
            AND user_id > 0
            AND %s IS NOT NULL 
            AND %s > 0
            AND %s BETWEEN %s AND %s
            """, feature, tableName, date, feature, feature, feature, 
            getFeatureMinValue(feature), getFeatureMaxValue(feature));
    }

    /**
     * 2. 生成部门健康基线聚合 - 每日02:05执行 
     * 改进：基于用户基线数据和组织闭包表进行层级聚合
     */
    @Scheduled(cron = "0 5 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成部门健康基线聚合（改进版-基于userId），日期: {}", dateStr);
        
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_baseline WHERE baseline_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理部门旧基线数据: {} 条", deletedRows);
            }
            
            // 并行处理多个健康特征的部门聚合
            CompletableFuture<Void>[] futures = new CompletableFuture[HEALTH_FEATURES.length];
            
            for (int i = 0; i < HEALTH_FEATURES.length; i++) {
                final String feature = HEALTH_FEATURES[i];
                futures[i] = CompletableFuture.runAsync(() -> {
                    aggregateDepartmentBaselineForFeature(feature, dateStr);
                }, executorService);
            }
            
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 部门健康基线聚合完成（改进版），日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 部门健康基线聚合失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("部门健康基线聚合失败: " + e.getMessage(), e);
        }
    }

    /**
     * 为单个特征聚合部门基线 - 改进版：基于userId的层级聚合
     */
    private void aggregateDepartmentBaselineForFeature(String feature, String dateStr) {
        try {
            String aggregationSql = """
                INSERT INTO t_org_health_baseline (
                    org_id, feature_name, baseline_date, mean_value, std_value,
                    min_value, max_value, user_count, sample_count, 
                    create_time, update_time
                )
                SELECT 
                    dept.department_id as org_id,
                    ? as feature_name,
                    ? as baseline_date,
                    AVG(hb.mean_value) as mean_value,
                    GREATEST(COALESCE(STD(hb.mean_value), 0), ?) as std_value,
                    MIN(hb.min_value) as min_value,
                    MAX(hb.max_value) as max_value,
                    COUNT(DISTINCT hb.user_id) as user_count,
                    SUM(hb.sample_count) as sample_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        c.ancestor_id as department_id,
                        uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    WHERE c.depth >= 0
                      AND uo.is_deleted = 0
                ) dept
                JOIN t_health_baseline hb ON hb.user_id = dept.user_id
                WHERE hb.feature_name = ?
                  AND hb.baseline_date = ?
                  AND hb.mean_value IS NOT NULL
                  AND hb.user_id IS NOT NULL
                GROUP BY dept.department_id
                HAVING COUNT(DISTINCT hb.user_id) >= 2
                """;
                
            int aggregatedCount = jdbcTemplate.update(aggregationSql, 
                feature, dateStr, getMinStandardDeviation(feature), feature, dateStr);
            
            if (aggregatedCount > 0) {
                log.info("✅ [部门基线-{}] 聚合完成，共 {} 个部门", feature, aggregatedCount);
            }
            
        } catch (Exception e) {
            log.error("❌ [部门基线-{}] 聚合失败: {}", feature, e.getMessage());
        }
    }

    /**
     * 3. 生成租户健康基线 - 每日02:10执行
     * 改进：基于部门数据聚合到租户级别
     */
    @Scheduled(cron = "0 10 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateTenantHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成租户健康基线（改进版-基于customerId），日期: {}", dateStr);
        
        try {
            // 并行处理多个健康特征的租户聚合
            CompletableFuture<Void>[] futures = new CompletableFuture[HEALTH_FEATURES.length];
            
            for (int i = 0; i < HEALTH_FEATURES.length; i++) {
                final String feature = HEALTH_FEATURES[i];
                futures[i] = CompletableFuture.runAsync(() -> {
                    aggregateTenantBaselineForFeature(feature, dateStr);
                }, executorService);
            }
            
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 租户健康基线聚合完成（改进版），日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 租户健康基线聚合失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("租户健康基线聚合失败: " + e.getMessage(), e);
        }
    }

    /**
     * 为单个特征聚合租户基线 - 新增：基于customer_id的最高级聚合
     */
    private void aggregateTenantBaselineForFeature(String feature, String dateStr) {
        try {
            // 首先清理租户级别的数据（org_id设为customer_id）
            String deleteSql = """
                DELETE FROM t_org_health_baseline 
                WHERE feature_name = ? AND baseline_date = ?
                AND org_id IN (
                    SELECT DISTINCT customer_id 
                    FROM t_health_baseline 
                    WHERE baseline_date = ? AND feature_name = ? AND user_id IS NOT NULL
                )
                """;
            jdbcTemplate.update(deleteSql, feature, dateStr, dateStr, feature);
            
            String tenantAggregationSql = """
                INSERT INTO t_org_health_baseline (
                    org_id, feature_name, baseline_date, mean_value, std_value,
                    min_value, max_value, user_count, sample_count, 
                    create_time, update_time
                )
                SELECT 
                    tenant.customer_id as org_id,
                    ? as feature_name,
                    ? as baseline_date,
                    AVG(hb.mean_value) as mean_value,
                    GREATEST(COALESCE(STD(hb.mean_value), 0), ?) as std_value,
                    MIN(hb.min_value) as min_value,
                    MAX(hb.max_value) as max_value,
                    COUNT(DISTINCT hb.user_id) as user_count,
                    SUM(hb.sample_count) as sample_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        u.customer_id,
                        u.id as user_id
                    FROM sys_user u
                    WHERE u.is_deleted = 0
                      AND u.customer_id IS NOT NULL
                      AND u.id IS NOT NULL
                ) tenant
                JOIN t_health_baseline hb ON hb.user_id = tenant.user_id
                WHERE hb.feature_name = ?
                  AND hb.baseline_date = ?
                  AND hb.mean_value IS NOT NULL
                  AND hb.user_id IS NOT NULL
                GROUP BY tenant.customer_id
                HAVING COUNT(DISTINCT hb.user_id) >= 5
                """;
                
            int tenantCount = jdbcTemplate.update(tenantAggregationSql, 
                feature, dateStr, getMinStandardDeviation(feature), feature, dateStr);
            
            if (tenantCount > 0) {
                log.info("✅ [租户基线-{}] 聚合完成，共 {} 个租户", feature, tenantCount);
            }
            
        } catch (Exception e) {
            log.error("❌ [租户基线-{}] 聚合失败: {}", feature, e.getMessage());
        }
    }

    /**
     * 4. 生成用户健康评分 - 每日04:00执行
     * 改进：基于userId的评分计算，支持权重配置
     */
    @Scheduled(cron = "0 0 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateUserHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康评分（改进版-基于userId），日期: {}", dateStr);
        
        try {
            // 首先更新权重缓存
            weightCalculationService.updateDailyWeights();
            
            List<String> tablesToQuery = getHealthDataTables(yesterday);
            
            // 检查是否有基线数据
            Long baselineCount = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM t_health_baseline WHERE baseline_date = ? AND user_id IS NOT NULL",
                Long.class, dateStr);
                
            if (baselineCount == null || baselineCount == 0) {
                log.warn("⚠️ 日期 {} 无用户基线数据，跳过评分生成", dateStr);
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
                    generateUserScoreForFeature(tablesToQuery, feature, dateStr);
                }, executorService);
            }
            
            CompletableFuture.allOf(futures).join();
            
            log.info("🎉 用户健康评分生成完成（改进版），日期: {}", dateStr);
            
        } catch (Exception e) {
            log.error("❌ 用户健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("用户健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 生成单个特征的用户评分数据 - 改进版：基于userId的评分
     */
    private void generateUserScoreForFeature(List<String> tableNames, String feature, String date) {
        try {
            // 构建多表联合查询的评分SQL - 基于userId
            StringBuilder unionSql = new StringBuilder();
            boolean hasValidTables = false;
            
            for (String tableName : tableNames) {
                if (tableName.equals("t_user_health_data") || tableExists(tableName)) {
                    if (hasValidTables) {
                        unionSql.append(" UNION ALL ");
                    }
                    unionSql.append(buildUserScoreQuery(tableName, feature, date));
                    hasValidTables = true;
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
                    COALESCE(h.device_sn, CONCAT('USER_', h.user_id)) as device_sn,
                    h.user_id,
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
                JOIN t_health_baseline b ON h.user_id = b.user_id 
                    AND b.feature_name = '%s'
                    AND b.baseline_date = DATE('%s')
                WHERE h.value IS NOT NULL AND h.value > 0
                  AND h.user_id IS NOT NULL AND h.user_id > 0
                GROUP BY h.user_id, h.org_id, b.mean_value, b.std_value, 
                         b.max_value, b.min_value, b.baseline_time
                HAVING COUNT(*) >= 5
                """, feature, date, unionSql.toString(), feature, date);
                
            int rows = jdbcTemplate.update(sql);
            log.info("✅ [用户评分-{}] 生成完成，共 {} 条记录", feature, rows);
            
        } catch (Exception e) {
            log.error("❌ [用户评分-{}] 生成失败: {}", feature, e.getMessage(), e);
        }
    }

    /**
     * 构建单表的用户评分查询SQL - 改进版：基于userId
     */
    private String buildUserScoreQuery(String tableName, String feature, String date) {
        return String.format("""
            SELECT 
                device_sn, user_id, org_id, %s as value
            FROM %s 
            WHERE DATE(timestamp) = '%s'
            AND user_id IS NOT NULL 
            AND user_id > 0
            AND %s IS NOT NULL 
            AND %s > 0
            AND %s BETWEEN %s AND %s
            """, feature, tableName, date, feature, feature, feature,
            getFeatureMinValue(feature), getFeatureMaxValue(feature));
    }

    /**
     * 5. 生成部门健康评分 - 每日04:05执行
     * 改进：基于用户评分聚合到部门级别
     */
    @Scheduled(cron = "0 5 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成部门健康评分（改进版-基于userId），日期: {}", dateStr);
        
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_score WHERE score_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理部门旧评分数据: {} 条", deletedRows);
            }
            
            String sql = """
                INSERT INTO t_org_health_score (
                    org_id, feature_name, score_date, mean_score, std_score,
                    min_score, max_score, user_count, create_time, update_time
                )
                SELECT 
                    dept.department_id as org_id,
                    hs.feature_name,
                    hs.score_date,
                    AVG(hs.score_value - COALESCE(hs.penalty_value, 0)) as mean_score,
                    COALESCE(STD(hs.score_value - COALESCE(hs.penalty_value, 0)), 0) as std_score,
                    MIN(hs.score_value - COALESCE(hs.penalty_value, 0)) as min_score,
                    MAX(hs.score_value - COALESCE(hs.penalty_value, 0)) as max_score,
                    COUNT(DISTINCT hs.user_id) as user_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        c.ancestor_id as department_id,
                        uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    WHERE c.depth >= 0
                      AND uo.is_deleted = 0
                ) dept
                JOIN t_health_score hs ON hs.user_id = dept.user_id
                WHERE hs.score_date = ?
                  AND hs.score_value IS NOT NULL
                  AND hs.user_id IS NOT NULL
                GROUP BY dept.department_id, hs.feature_name
                HAVING COUNT(DISTINCT hs.user_id) >= 2
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            log.info("🎉 部门健康评分生成完成（改进版），日期: {}, 共 {} 条记录", dateStr, rows);
            
        } catch (Exception e) {
            log.error("❌ 部门健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("部门健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 6. 生成租户健康评分 - 每日04:10执行
     * 新增：基于部门评分聚合到租户级别
     */
    @Scheduled(cron = "0 10 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateTenantHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成租户健康评分（改进版-基于customerId），日期: {}", dateStr);
        
        try {
            String sql = """
                INSERT IGNORE INTO t_org_health_score (
                    org_id, feature_name, score_date, mean_score, std_score,
                    min_score, max_score, user_count, create_time, update_time
                )
                SELECT 
                    tenant.customer_id as org_id,
                    hs.feature_name,
                    hs.score_date,
                    AVG(hs.score_value - COALESCE(hs.penalty_value, 0)) as mean_score,
                    COALESCE(STD(hs.score_value - COALESCE(hs.penalty_value, 0)), 0) as std_score,
                    MIN(hs.score_value - COALESCE(hs.penalty_value, 0)) as min_score,
                    MAX(hs.score_value - COALESCE(hs.penalty_value, 0)) as max_score,
                    COUNT(DISTINCT hs.user_id) as user_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        u.customer_id,
                        u.id as user_id
                    FROM sys_user u
                    WHERE u.is_deleted = 0
                      AND u.customer_id IS NOT NULL
                ) tenant
                JOIN t_health_score hs ON hs.user_id = tenant.user_id
                WHERE hs.score_date = ?
                  AND hs.score_value IS NOT NULL
                  AND hs.user_id IS NOT NULL
                GROUP BY tenant.customer_id, hs.feature_name
                HAVING COUNT(DISTINCT hs.user_id) >= 5
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            log.info("🎉 租户健康评分生成完成（改进版），日期: {}, 共 {} 条记录", dateStr, rows);
            
        } catch (Exception e) {
            log.error("❌ 租户健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("租户健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 数据质量检查 - 检查userId相关的数据完整性
     */
    private void performDataQualityCheck(String dateStr) {
        try {
            log.info("🔍 开始数据质量检查，日期: {}", dateStr);
            
            // 检查用户基线数据质量
            String userBaselineQualityQuery = """
                SELECT 
                    COUNT(*) as total_baselines,
                    COUNT(CASE WHEN user_id IS NULL OR user_id = 0 THEN 1 END) as missing_user_id,
                    COUNT(CASE WHEN device_sn IS NULL OR device_sn = '' THEN 1 END) as missing_device_sn,
                    COUNT(CASE WHEN sample_count < 5 THEN 1 END) as low_sample_count,
                    COUNT(CASE WHEN std_value = 0 OR std_value IS NULL THEN 1 END) as zero_std
                FROM t_health_baseline 
                WHERE baseline_date = ?
                """;
            
            Map<String, Object> qualityResult = jdbcTemplate.queryForMap(userBaselineQualityQuery, dateStr);
            
            log.info("📊 基线数据质量报告: 总数 {}, 缺少userId {}, 缺少设备号 {}, 样本不足 {}, 标准差为0 {}", 
                qualityResult.get("total_baselines"), qualityResult.get("missing_user_id"),
                qualityResult.get("missing_device_sn"), qualityResult.get("low_sample_count"),
                qualityResult.get("zero_std"));
            
            // 检查用户-部门-租户数据对应关系
            checkHierarchicalDataConsistency(dateStr);
            
            log.info("✅ 数据质量检查完成");
            
        } catch (Exception e) {
            log.error("❌ 数据质量检查失败: {}", e.getMessage());
        }
    }

    /**
     * 检查层级数据一致性
     */
    private void checkHierarchicalDataConsistency(String dateStr) {
        try {
            // 检查用户->部门->租户的数据覆盖率
            for (String feature : HEALTH_FEATURES) {
                String consistencyQuery = """
                    SELECT 
                        COUNT(DISTINCT hb.user_id) as user_baseline_count,
                        COUNT(DISTINCT ohb.org_id) as dept_baseline_count,
                        (SELECT COUNT(DISTINCT customer_id) 
                         FROM sys_user WHERE is_deleted = 0 AND customer_id IS NOT NULL) as total_tenants,
                        (SELECT COUNT(DISTINCT org_id) 
                         FROM t_org_health_baseline 
                         WHERE baseline_date = ? AND feature_name = ?) as tenant_baseline_count
                    FROM t_health_baseline hb
                    LEFT JOIN t_org_health_baseline ohb ON DATE(ohb.baseline_date) = DATE(hb.baseline_date)
                        AND ohb.feature_name = hb.feature_name
                    WHERE hb.baseline_date = ? AND hb.feature_name = ?
                      AND hb.user_id IS NOT NULL
                    """;
                
                try {
                    Map<String, Object> consistency = jdbcTemplate.queryForMap(consistencyQuery, 
                        dateStr, feature, dateStr, feature);
                    
                    log.debug("🔗 [{}] 层级一致性: 用户基线 {}, 部门基线 {}, 租户基线 {}", 
                        feature, consistency.get("user_baseline_count"), 
                        consistency.get("dept_baseline_count"), consistency.get("tenant_baseline_count"));
                        
                } catch (Exception e) {
                    log.warn("⚠️ 特征 {} 一致性检查失败: {}", feature, e.getMessage());
                }
            }
        } catch (Exception e) {
            log.error("❌ 层级数据一致性检查失败: {}", e.getMessage());
        }
    }

    // 工具方法 - 复用现有的方法
    
    private List<String> getHealthDataTables(LocalDate date) {
        List<String> potentialTables = HealthDataTableUtil.getTableNames(
            date.atStartOfDay(), 
            date.atTime(23, 59, 59));
        
        List<String> tables = new ArrayList<>();
        
        for (String tableName : potentialTables) {
            if (tableExists(tableName)) {
                tables.add(tableName);
                log.info("✅ 月表存在: {}", tableName);
            }
        }
        
        tables.add("t_user_health_data");
        log.info("🔍 将查询以下表: {}", tables);
        return tables;
    }
    
    private boolean tableExists(String tableName) {
        try {
            Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = ?",
                Integer.class, tableName);
            return count != null && count > 0;
        } catch (Exception e) {
            return false;
        }
    }
    
    private Long getTotalHealthDataCount(List<String> tableNames, String dateStr) {
        Long totalCount = 0L;
        for (String tableName : tableNames) {
            try {
                String sql = "SELECT COUNT(*) FROM " + tableName + " WHERE DATE(timestamp) = ? AND user_id IS NOT NULL AND user_id > 0";
                Long count = jdbcTemplate.queryForObject(sql, Long.class, dateStr);
                totalCount += (count != null ? count : 0);
                log.info("📊 表 {} 用户数据: {} 条", tableName, count);
            } catch (Exception e) {
                log.warn("⚠️ 查询表 {} 数据量失败: {}", tableName, e.getMessage());
            }
        }
        return totalCount;
    }
    
    // 特征值范围和标准差配置 - 复用现有方法
    
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
     * 手动触发改进版基线和评分生成
     */
    public void manualGenerateImprovedBaselinesAndScores(String startDate, String endDate) {
        log.info("🔧 开始手动生成改进版健康基线和评分，时间范围: {} - {}", startDate, endDate);
        
        try {
            LocalDate start = LocalDate.parse(startDate);
            LocalDate end = LocalDate.parse(endDate);
            
            while (!start.isAfter(end)) {
                String dateStr = start.toString();
                
                // 1. 生成用户基线
                List<String> tablesToQuery = getHealthDataTables(start);
                for (String feature : HEALTH_FEATURES) {
                    generateUserBaselineForFeature(tablesToQuery, feature, dateStr);
                }
                
                // 2. 生成部门基线
                for (String feature : HEALTH_FEATURES) {
                    aggregateDepartmentBaselineForFeature(feature, dateStr);
                }
                
                // 3. 生成租户基线
                for (String feature : HEALTH_FEATURES) {
                    aggregateTenantBaselineForFeature(feature, dateStr);
                }
                
                // 4. 生成用户评分
                for (String feature : HEALTH_FEATURES) {
                    generateUserScoreForFeature(tablesToQuery, feature, dateStr);
                }
                
                log.info("✅ 日期 {} 改进版处理完成", dateStr);
                start = start.plusDays(1);
            }
            
            log.info("🎉 手动改进版生成完成");
            
        } catch (Exception e) {
            log.error("❌ 手动改进版生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("手动生成失败: " + e.getMessage(), e);
        }
    }
    
    public void destroy() {
        if (executorService != null && !executorService.isShutdown()) {
            executorService.shutdown();
            log.info("🔒 改进版健康任务线程池已关闭");
        }
    }
}