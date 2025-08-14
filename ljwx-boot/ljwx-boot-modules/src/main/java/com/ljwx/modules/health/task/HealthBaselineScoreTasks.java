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
    
    private final DateTimeFormatter TABLE_SUFFIX_FORMATTER = DateTimeFormatter.ofPattern("yyyyMM");
    private final ExecutorService executorService = Executors.newFixedThreadPool(8); // #优化线程池大小
    
    // 健康特征字段配置 - 支持所有主要健康指标
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
        "pressure_low", "stress", "step", "calorie", "distance", "sleep"
    };

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
     * 支持多表查询（主表+分表）
     */
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateUserHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康基线，日期: {}", dateStr);
        
        try {
            // 获取所有相关表数据
            List<String> tablesToQuery = getHealthDataTables(yesterday);
            Long totalDataCount = 0L;
            
            for (String tableName : tablesToQuery) {
                Long tableDataCount = getHealthDataCount(tableName, dateStr);
                totalDataCount += tableDataCount;
                log.info("📊 表 {} 找到 {} 条记录", tableName, tableDataCount);
            }
                
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
                    generateBaselineForFeatureMultiTable(tablesToQuery, feature, dateStr);
                }, executorService);
            }
            
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
                GROUP BY device_sn, org_id
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
     * 3. 生成组织健康基线 - 每日02:10执行
     */
    @Scheduled(cron = "0 10 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateOrgHealthBaseline() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成组织健康基线，日期: {}", dateStr);
        
        try {
            // 清理当日旧数据
            String deleteSql = "DELETE FROM t_org_health_baseline WHERE baseline_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理组织旧基线数据: {} 条", deletedRows);
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
                HAVING COUNT(DISTINCT b.device_sn) >= 2
                """;
                
            int rows = jdbcTemplate.update(sql, dateStr);
            log.info("🎉 组织健康基线生成完成，日期: {}, 共 {} 条记录", dateStr, rows);
            
        } catch (Exception e) {
            log.error("❌ 组织健康基线生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("组织健康基线生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 4. 生成用户健康评分 - 每日04:00执行
     */
    @Scheduled(cron = "0 0 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthScore() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成用户健康评分，日期: {}", dateStr);
        
        try {
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
                GROUP BY h.device_sn, h.org_id, b.mean_value, b.std_value, 
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
     * 5. 生成组织健康评分 - 每日04:10执行
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
     * 6. 数据清理任务 - 每日05:00执行
     */
    @Scheduled(cron = "0 0 5 * * ?")
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