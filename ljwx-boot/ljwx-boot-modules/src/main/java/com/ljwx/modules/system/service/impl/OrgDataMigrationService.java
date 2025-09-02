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

package com.ljwx.modules.system.service.impl;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 组织架构数据迁移服务
 * 
 * 功能特性:
 * - 从传统ancestors字符串迁移到闭包表
 * - 安全的数据备份和恢复
 * - 性能对比测试
 * - 迁移进度跟踪
 * - 回滚支持
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.OrgDataMigrationService
 * @CreateTime 2025-08-30 - 19:00:00
 */
@Slf4j
@Service
public class OrgDataMigrationService {

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    @Autowired(required = false)
    private OrgDataConsistencyService consistencyService;

    /**
     * 执行完整的数据迁移流程
     * 
     * @param customerId 租户ID (null表示迁移所有租户)
     * @return 迁移结果报告
     */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> performCompleteMigration(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> report = new HashMap<>();
        List<String> steps = new ArrayList<>();
        
        try {
            log.info("🚀 开始完整数据迁移流程，租户ID: {}", customerId);
            
            // 步骤1: 数据备份
            steps.add("步骤1: 创建数据备份");
            Map<String, Object> backupResult = createDataBackup(customerId);
            report.put("backupResult", backupResult);
            
            // 步骤2: 数据验证和清理
            steps.add("步骤2: 数据验证和清理");
            Map<String, Object> validationResult = validateAndCleanData(customerId);
            report.put("validationResult", validationResult);
            
            // 步骤3: 构建闭包表
            steps.add("步骤3: 构建闭包关系表");
            Map<String, Object> migrationResult = migrateToClosureTable(customerId);
            report.put("migrationResult", migrationResult);
            
            // 步骤4: 数据一致性验证
            steps.add("步骤4: 数据一致性验证");
            if (consistencyService != null) {
                Map<String, Object> consistencyResult = consistencyService.checkDataConsistency(customerId);
                report.put("consistencyResult", consistencyResult);
            }
            
            // 步骤5: 性能对比测试
            steps.add("步骤5: 性能对比测试");
            Map<String, Object> performanceResult = performPerformanceComparison(customerId);
            report.put("performanceResult", performanceResult);
            
            // 步骤6: 生成回滚脚本
            steps.add("步骤6: 生成回滚脚本");
            String rollbackScript = generateRollbackScript();
            report.put("rollbackScript", rollbackScript);
            
            stopWatch.stop();
            report.put("migrationSteps", steps);
            report.put("migrationDuration", stopWatch.getTotalTimeMillis());
            report.put("migrationTime", LocalDateTime.now());
            report.put("success", true);
            
            log.info("✅ 完整数据迁移流程完成，耗时={}ms", stopWatch.getTotalTimeMillis());
            
            return report;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 数据迁移失败: customerId={}", customerId, e);
            
            report.put("success", false);
            report.put("error", e.getMessage());
            report.put("failedAt", steps.size() > 0 ? steps.get(steps.size() - 1) : "初始化阶段");
            report.put("migrationTime", LocalDateTime.now());
            
            return report;
        }
    }

    /**
     * 创建数据备份
     */
    public Map<String, Object> createDataBackup(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            if (jdbcTemplate == null) {
                throw new RuntimeException("JdbcTemplate not available");
            }
            
            log.info("📂 开始创建数据备份...");
            
            // 创建备份表
            String createBackupTableSql = """
                CREATE TABLE IF NOT EXISTS `sys_org_units_backup` (
                    SELECT * FROM `sys_org_units` WHERE 1=1
                    """ + (customerId != null ? " AND customer_id = " + customerId : "") + """
                )
                """;
            
            jdbcTemplate.execute(createBackupTableSql);
            
            // 获取备份记录数
            String countSql = "SELECT COUNT(*) FROM sys_org_units_backup";
            Integer backupCount = jdbcTemplate.queryForObject(countSql, Integer.class);
            
            stopWatch.stop();
            result.put("backupTableCreated", true);
            result.put("backupRecordCount", backupCount);
            result.put("backupDuration", stopWatch.getTotalTimeMillis());
            result.put("success", true);
            
            log.info("✅ 数据备份完成，备份{}条记录，耗时={}ms", backupCount, stopWatch.getTotalTimeMillis());
            
            return result;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 创建数据备份失败", e);
            
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("backupDuration", stopWatch.getTotalTimeMillis());
            
            return result;
        }
    }

    /**
     * 数据验证和清理
     */
    public Map<String, Object> validateAndCleanData(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            if (jdbcTemplate == null) {
                throw new RuntimeException("JdbcTemplate not available");
            }
            
            log.info("🔍 开始数据验证和清理...");
            
            // 生成数据验证报告
            String validationSql = """
                SELECT 
                    'Data Validation Report' as report_type,
                    COUNT(*) as total_orgs,
                    COUNT(CASE WHEN parent_id IS NULL OR parent_id = 0 THEN 1 END) as root_orgs,
                    COUNT(CASE WHEN ancestors IS NULL OR ancestors = '' THEN 1 END) as orgs_without_ancestors,
                    COUNT(DISTINCT customer_id) as total_customers,
                    MAX(level) as max_level
                FROM sys_org_units 
                WHERE is_deleted = 0
                """ + (customerId != null ? " AND customer_id = " + customerId : "");
            
            List<Map<String, Object>> validationReport = jdbcTemplate.queryForList(validationSql);
            result.put("validationReport", validationReport.get(0));
            
            // 修复异常数据
            String fixLevelSql = """
                UPDATE sys_org_units 
                SET level = 0 
                WHERE (parent_id IS NULL OR parent_id = 0) AND level != 0 AND is_deleted = 0
                """ + (customerId != null ? " AND customer_id = " + customerId : "");
            
            int fixedLevels = jdbcTemplate.update(fixLevelSql);
            
            String fixAncestorsSql = """
                UPDATE sys_org_units 
                SET ancestors = '0' 
                WHERE (ancestors IS NULL OR ancestors = '') 
                  AND (parent_id IS NULL OR parent_id = 0) 
                  AND is_deleted = 0
                """ + (customerId != null ? " AND customer_id = " + customerId : "");
            
            int fixedAncestors = jdbcTemplate.update(fixAncestorsSql);
            
            stopWatch.stop();
            result.put("fixedLevels", fixedLevels);
            result.put("fixedAncestors", fixedAncestors);
            result.put("validationDuration", stopWatch.getTotalTimeMillis());
            result.put("success", true);
            
            log.info("✅ 数据验证和清理完成，修复level={}条，修复ancestors={}条，耗时={}ms", 
                fixedLevels, fixedAncestors, stopWatch.getTotalTimeMillis());
            
            return result;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 数据验证和清理失败", e);
            
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("validationDuration", stopWatch.getTotalTimeMillis());
            
            return result;
        }
    }

    /**
     * 迁移到闭包表
     */
    public Map<String, Object> migrateToClosureTable(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            if (jdbcTemplate == null) {
                throw new RuntimeException("JdbcTemplate not available");
            }
            
            log.info("🔄 开始迁移到闭包表...");
            
            // 清空目标闭包表
            String truncateSql = "TRUNCATE TABLE sys_org_closure";
            jdbcTemplate.execute(truncateSql);
            
            // 构建闭包关系
            int processedOrgs = buildClosureRelations(customerId);
            
            // 验证迁移结果
            String countSql = "SELECT COUNT(*) FROM sys_org_closure" + 
                (customerId != null ? " WHERE customer_id = " + customerId : "");
            Integer closureCount = jdbcTemplate.queryForObject(countSql, Integer.class);
            
            stopWatch.stop();
            result.put("processedOrganizations", processedOrgs);
            result.put("totalClosureRelations", closureCount);
            result.put("migrationDuration", stopWatch.getTotalTimeMillis());
            result.put("success", true);
            
            log.info("✅ 闭包表迁移完成，处理{}个组织，生成{}条关系，耗时={}ms", 
                processedOrgs, closureCount, stopWatch.getTotalTimeMillis());
            
            return result;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 迁移到闭包表失败", e);
            
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("migrationDuration", stopWatch.getTotalTimeMillis());
            
            return result;
        }
    }

    /**
     * 性能对比测试
     */
    public Map<String, Object> performPerformanceComparison(Long customerId) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            if (jdbcTemplate == null) {
                result.put("message", "JdbcTemplate not available, skipping performance test");
                return result;
            }
            
            log.info("⚡ 开始性能对比测试...");
            
            // 测试查询 - 查找某个组织的所有子组织
            Long testOrgId = getRandomOrgId(customerId);
            if (testOrgId == null) {
                result.put("message", "No organization found for testing");
                return result;
            }
            
            // 测试原有方案性能
            StopWatch oldMethodWatch = new StopWatch();
            oldMethodWatch.start();
            
            String oldMethodSql = """
                SELECT COUNT(*) FROM sys_org_units 
                WHERE ancestors LIKE CONCAT('%,', ?, ',%') 
                   OR ancestors LIKE CONCAT(?, ',%') 
                   OR ancestors LIKE CONCAT('%,', ?)
                   OR ancestors = CAST(? AS CHAR)
                """ + (customerId != null ? " AND customer_id = " + customerId : "");
            
            Integer oldResult = jdbcTemplate.queryForObject(oldMethodSql, Integer.class, 
                testOrgId, testOrgId, testOrgId, testOrgId);
            oldMethodWatch.stop();
            
            // 测试新方案性能  
            StopWatch newMethodWatch = new StopWatch();
            newMethodWatch.start();
            
            String newMethodSql = """
                SELECT COUNT(*) FROM sys_org_units o
                INNER JOIN sys_org_closure c ON o.id = c.descendant_id
                WHERE c.ancestor_id = ? AND c.depth > 0 AND o.is_deleted = 0
                """ + (customerId != null ? " AND o.customer_id = " + customerId : "");
            
            Integer newResult = jdbcTemplate.queryForObject(newMethodSql, Integer.class, testOrgId);
            newMethodWatch.stop();
            
            long oldTime = oldMethodWatch.getTotalTimeMillis();
            long newTime = newMethodWatch.getTotalTimeMillis();
            double improvement = oldTime > 0 ? (double) oldTime / newTime : 1.0;
            
            result.put("testOrgId", testOrgId);
            result.put("oldMethodTime", oldTime);
            result.put("newMethodTime", newTime);
            result.put("oldResult", oldResult);
            result.put("newResult", newResult);
            result.put("performanceImprovement", Math.round(improvement * 100.0) / 100.0);
            result.put("resultsMatch", Objects.equals(oldResult, newResult));
            result.put("success", true);
            
            log.info("✅ 性能对比完成，旧方法={}ms，新方法={}ms，性能提升={}x", 
                oldTime, newTime, Math.round(improvement * 100.0) / 100.0);
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 性能对比测试失败", e);
            
            result.put("success", false);
            result.put("error", e.getMessage());
            
            return result;
        }
    }

    /**
     * 生成回滚脚本
     */
    public String generateRollbackScript() {
        return String.format("""
            -- 回滚脚本 - 生成时间: %s
            -- 警告：执行前请确认数据备份完整性
            
            -- 1. 恢复原有组织表
            DROP TABLE IF EXISTS sys_org_units_new;
            RENAME TABLE sys_org_units TO sys_org_units_new;
            RENAME TABLE sys_org_units_backup TO sys_org_units;
            
            -- 2. 清理闭包表（可选）
            -- TRUNCATE TABLE sys_org_closure;
            
            -- 3. 清理管理员缓存表（可选）
            -- TRUNCATE TABLE sys_org_manager_cache;
            
            -- 回滚完成，请验证数据完整性
            SELECT '回滚脚本执行完成' as message;
            """, LocalDateTime.now());
    }

    // ================== 私有辅助方法 ==================

    private int buildClosureRelations(Long customerId) {
        if (jdbcTemplate == null) {
            return 0;
        }
        
        try {
            // 获取所有组织，按层级排序
            String orgSql = """
                SELECT id, parent_id, customer_id, level 
                FROM sys_org_units 
                WHERE is_deleted = 0
                """ + (customerId != null ? " AND customer_id = " + customerId : "") + """
                ORDER BY level, id
                """;
            
            List<Map<String, Object>> orgs = jdbcTemplate.queryForList(orgSql);
            
            for (Map<String, Object> org : orgs) {
                Long orgId = ((Number) org.get("id")).longValue();
                Object parentIdObj = org.get("parent_id");
                Long parentId = parentIdObj != null ? ((Number) parentIdObj).longValue() : null;
                Long customerIdValue = ((Number) org.get("customer_id")).longValue();
                
                // 插入自引用关系
                String selfRefSql = """
                    INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                    VALUES (?, ?, 0, ?)
                    """;
                jdbcTemplate.update(selfRefSql, orgId, orgId, customerIdValue);
                
                // 如果有父节点，插入祖先关系
                if (parentId != null && parentId > 0) {
                    String ancestorSql = """
                        INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                        SELECT ancestor_id, ?, depth + 1, customer_id
                        FROM sys_org_closure 
                        WHERE descendant_id = ? AND customer_id = ?
                        """;
                    jdbcTemplate.update(ancestorSql, orgId, parentId, customerIdValue);
                }
            }
            
            return orgs.size();
            
        } catch (Exception e) {
            log.error("构建闭包关系失败", e);
            return 0;
        }
    }

    private Long getRandomOrgId(Long customerId) {
        if (jdbcTemplate == null) {
            return null;
        }
        
        try {
            String sql = """
                SELECT id FROM sys_org_units 
                WHERE is_deleted = 0
                """ + (customerId != null ? " AND customer_id = " + customerId : "") + """
                ORDER BY RAND() 
                LIMIT 1
                """;
            
            return jdbcTemplate.queryForObject(sql, Long.class);
        } catch (Exception e) {
            log.debug("获取随机组织ID失败", e);
            return null;
        }
    }
}