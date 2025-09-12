package com.ljwx.modules.health.task;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.ljwx.modules.health.service.UnifiedHealthProcessingService;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 健康数据定时任务 - 使用统一处理服务
 * 统一处理baseline, score, prediction, recommendation, profile
 * 遵循：租户 → 部门 → 用户 → 汇总 的处理逻辑
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @CreateTime 2025-09-12
 */
@Slf4j
@Component
public class HealthBaselineScoreTasks {

    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private UnifiedHealthProcessingService unifiedHealthProcessingService;
    
    @Autowired
    private com.ljwx.modules.health.service.WeightCalculationService weightCalculationService;
    
    private final DateTimeFormatter TABLE_SUFFIX_FORMATTER = DateTimeFormatter.ofPattern("yyyyMM");

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
     * 1. 生成用户健康基线 - 每日02:00执行
     * 使用统一的健康数据处理服务
     */
    @Scheduled(cron = "0 0 2 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateUserHealthBaseline() {
        log.info("📊 开始生成用户健康基线");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("baseline", 30);
            log.info("✅ 用户健康基线生成完成");
        } catch (Exception e) {
            log.error("❌ 用户健康基线生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("用户健康基线生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 2. 生成健康评分 - 每日04:00执行
     */
    @Scheduled(cron = "0 0 4 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthScore() {
        log.info("📈 开始生成健康评分");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("score", 7);
            log.info("✅ 健康评分生成完成");
        } catch (Exception e) {
            log.error("❌ 健康评分生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 3. 生成健康预测 - 每日03:00执行
     */
    @Scheduled(cron = "0 0 3 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthPrediction() {
        log.info("🔮 开始生成健康预测");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("prediction", 60);
            log.info("✅ 健康预测生成完成");
        } catch (Exception e) {
            log.error("❌ 健康预测生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康预测生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 4. 生成健康建议 - 每日05:00执行
     */
    @Scheduled(cron = "0 0 5 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthRecommendation() {
        log.info("💡 开始生成健康建议");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("recommendation", 14);
            log.info("✅ 健康建议生成完成");
        } catch (Exception e) {
            log.error("❌ 健康建议生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康建议生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 5. 生成健康档案 - 每日06:00执行
     */
    @Scheduled(cron = "0 0 6 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void generateHealthProfile() {
        log.info("📋 开始生成健康档案");
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData("profile", 90);
            log.info("✅ 健康档案生成完成");
        } catch (Exception e) {
            log.error("❌ 健康档案生成失败: {}", e.getMessage(), e);
            throw new RuntimeException("健康档案生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 6. 数据清理任务 - 每日07:00执行
     */
    @Scheduled(cron = "0 0 7 * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void cleanupOldData() {
        log.info("🧹 开始数据清理任务");
        
        try {
            // 清理老旧的基线数据 (保留90天)
            String cleanBaselineSql = "DELETE FROM t_health_baseline WHERE baseline_date < ? AND is_current = 0";
            LocalDate cutoffDate = LocalDate.now().minusDays(90);
            
            int deletedBaselines = jdbcTemplate.update(cleanBaselineSql, cutoffDate);
            log.info("🗑️ 清理老旧基线数据: {} 条", deletedBaselines);
            
            // 清理老旧的评分数据 (保留30天)
            String cleanScoreSql = "DELETE FROM t_health_score WHERE score_date < ? AND is_deleted = 0";
            LocalDate scoreCutoffDate = LocalDate.now().minusDays(30);
            
            int deletedScores = jdbcTemplate.update(cleanScoreSql, scoreCutoffDate);
            log.info("🗑️ 清理老旧评分数据: {} 条", deletedScores);
            
            log.info("✅ 数据清理任务完成");
            
        } catch (Exception e) {
            log.error("❌ 数据清理任务失败: {}", e.getMessage(), e);
            throw new RuntimeException("数据清理任务失败: " + e.getMessage(), e);
        }
    }

    /**
     * 7. 按月分表任务 - 每月1日凌晨执行
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
     * 立即执行健康数据处理 - 用于测试和手动触发
     * @param processType 处理类型: baseline, score, prediction, recommendation, profile
     * @param days 统计天数
     */
    public void executeImmediately(String processType, Integer days) {
        log.info("🚀 立即执行健康数据处理: type={}, days={}", processType, days);
        
        try {
            unifiedHealthProcessingService.processUnifiedHealthData(processType, days);
            log.info("✅ 立即执行完成: type={}", processType);
        } catch (Exception e) {
            log.error("❌ 立即执行失败: type={}, error={}", processType, e.getMessage(), e);
            throw new RuntimeException("立即执行失败: " + e.getMessage(), e);
        }
    }
}