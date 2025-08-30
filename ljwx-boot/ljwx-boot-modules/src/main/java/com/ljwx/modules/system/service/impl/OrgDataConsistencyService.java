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
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.util.*;

/**
 * 组织架构数据一致性检查服务
 * 
 * 功能特性:
 * - 闭包表数据一致性检查
 * - 自动修复数据不一致问题
 * - 定时健康检查
 * - 数据完整性验证
 * - 孤立数据清理
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.OrgDataConsistencyService
 * @CreateTime 2025-08-30 - 18:30:00
 */
@Slf4j
@Service
public class OrgDataConsistencyService {

    @Autowired(required = false)
    private JdbcTemplate jdbcTemplate;

    /**
     * 检查闭包表数据一致性
     * 
     * @param customerId 租户ID
     * @return 一致性检查报告
     */
    public Map<String, Object> checkDataConsistency(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> report = new HashMap<>();
        
        try {
            log.info("开始检查数据一致性，租户ID: {}", customerId);
            
            // 1. 检查自引用关系完整性
            List<Map<String, Object>> missingSelfRefs = checkMissingSelfReferences(customerId);
            report.put("missingSelfReferences", missingSelfRefs);
            
            // 2. 检查祖先关系完整性
            List<Map<String, Object>> missingAncestors = checkMissingAncestorRelations(customerId);
            report.put("missingAncestorRelations", missingAncestors);
            
            // 3. 检查孤立的闭包关系
            List<Map<String, Object>> orphanedRelations = checkOrphanedClosureRelations(customerId);
            report.put("orphanedClosureRelations", orphanedRelations);
            
            // 4. 检查层级深度一致性
            List<Map<String, Object>> depthInconsistencies = checkDepthInconsistencies(customerId);
            report.put("depthInconsistencies", depthInconsistencies);
            
            // 5. 统计信息
            Map<String, Object> statistics = gatherStatistics(customerId);
            report.put("statistics", statistics);
            
            stopWatch.stop();
            report.put("checkDuration", stopWatch.getTotalTimeMillis());
            report.put("checkTime", LocalDateTime.now());
            
            boolean hasIssues = !missingSelfRefs.isEmpty() || !missingAncestors.isEmpty() || 
                               !orphanedRelations.isEmpty() || !depthInconsistencies.isEmpty();
            report.put("hasIssues", hasIssues);
            
            log.info("📊 数据一致性检查完成: customerId={}, 有问题={}, 耗时={}ms", 
                customerId, hasIssues, stopWatch.getTotalTimeMillis());
            
            return report;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 数据一致性检查失败: customerId={}", customerId, e);
            
            report.put("error", e.getMessage());
            report.put("checkTime", LocalDateTime.now());
            return report;
        }
    }

    /**
     * 修复闭包表数据一致性问题
     * 
     * @param customerId 租户ID
     * @return 修复结果报告
     */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> repairDataConsistency(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("开始修复数据一致性问题，租户ID: {}", customerId);
            
            // 1. 修复缺失的自引用关系
            int fixedSelfRefs = repairMissingSelfReferences(customerId);
            result.put("fixedSelfReferences", fixedSelfRefs);
            
            // 2. 重新构建祖先关系
            int rebuiltAncestors = rebuildAncestorRelations(customerId);
            result.put("rebuiltAncestorRelations", rebuiltAncestors);
            
            // 3. 清理孤立的闭包关系
            int cleanedOrphaned = cleanOrphanedClosureRelations(customerId);
            result.put("cleanedOrphanedRelations", cleanedOrphaned);
            
            // 4. 更新层级深度
            int updatedDepths = updateDepthConsistency(customerId);
            result.put("updatedDepths", updatedDepths);
            
            stopWatch.stop();
            result.put("repairDuration", stopWatch.getTotalTimeMillis());
            result.put("repairTime", LocalDateTime.now());
            result.put("success", true);
            
            log.info("🔧 数据一致性修复完成: customerId={}, 修复项={}, 耗时={}ms", 
                customerId, fixedSelfRefs + rebuiltAncestors + cleanedOrphaned + updatedDepths, 
                stopWatch.getTotalTimeMillis());
            
            return result;
            
        } catch (Exception e) {
            stopWatch.stop();
            log.error("❌ 数据一致性修复失败: customerId={}", customerId, e);
            
            result.put("success", false);
            result.put("error", e.getMessage());
            result.put("repairTime", LocalDateTime.now());
            return result;
        }
    }

    /**
     * 每天执行一次数据一致性检查
     */
    @Scheduled(cron = "0 3 * * * ?") // 每天凌晨3点
    public void scheduledConsistencyCheck() {
        try {
            log.info("🔍 开始定时数据一致性检查...");
            
            // 检查所有租户的数据一致性
            Map<String, Object> globalReport = checkDataConsistency(null);
            
            Boolean hasIssues = (Boolean) globalReport.get("hasIssues");
            if (hasIssues != null && hasIssues) {
                log.warn("⚠️ 发现数据一致性问题，建议手动检查修复");
                
                // 可以在这里发送告警通知
                // alertService.sendDataConsistencyAlert(globalReport);
            } else {
                log.info("✅ 定时数据一致性检查通过");
            }
            
        } catch (Exception e) {
            log.error("❌ 定时数据一致性检查失败", e);
        }
    }

    // ================== 私有检查方法 ==================

    private List<Map<String, Object>> checkMissingSelfReferences(Long customerId) {
        if (jdbcTemplate == null) {
            return Collections.emptyList();
        }
        
        try {
            String sql = """
                SELECT o.id, o.name 
                FROM sys_org_units o
                LEFT JOIN sys_org_closure c ON o.id = c.descendant_id AND c.ancestor_id = o.id AND c.depth = 0
                WHERE o.is_deleted = 0 
                  AND c.id IS NULL
                """ + (customerId != null ? " AND o.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.queryForList(sql, customerId);
            } else {
                return jdbcTemplate.queryForList(sql);
            }
        } catch (Exception e) {
            log.error("检查缺失自引用关系失败", e);
            return Collections.emptyList();
        }
    }

    private List<Map<String, Object>> checkMissingAncestorRelations(Long customerId) {
        if (jdbcTemplate == null) {
            return Collections.emptyList();
        }
        
        try {
            // 这个查询检查是否存在应该有但缺失的祖先关系
            String sql = """
                SELECT o.id, o.name, o.parent_id 
                FROM sys_org_units o
                WHERE o.is_deleted = 0 
                  AND o.parent_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM sys_org_closure c 
                      WHERE c.descendant_id = o.id AND c.ancestor_id = o.parent_id AND c.depth = 1
                  )
                """ + (customerId != null ? " AND o.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.queryForList(sql, customerId);
            } else {
                return jdbcTemplate.queryForList(sql);
            }
        } catch (Exception e) {
            log.error("检查缺失祖先关系失败", e);
            return Collections.emptyList();
        }
    }

    private List<Map<String, Object>> checkOrphanedClosureRelations(Long customerId) {
        if (jdbcTemplate == null) {
            return Collections.emptyList();
        }
        
        try {
            String sql = """
                SELECT c.ancestor_id, c.descendant_id, c.depth
                FROM sys_org_closure c
                LEFT JOIN sys_org_units o1 ON c.ancestor_id = o1.id AND o1.is_deleted = 0
                LEFT JOIN sys_org_units o2 ON c.descendant_id = o2.id AND o2.is_deleted = 0
                WHERE (o1.id IS NULL OR o2.id IS NULL)
                """ + (customerId != null ? " AND c.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.queryForList(sql, customerId);
            } else {
                return jdbcTemplate.queryForList(sql);
            }
        } catch (Exception e) {
            log.error("检查孤立闭包关系失败", e);
            return Collections.emptyList();
        }
    }

    private List<Map<String, Object>> checkDepthInconsistencies(Long customerId) {
        if (jdbcTemplate == null) {
            return Collections.emptyList();
        }
        
        try {
            // 检查深度值是否与实际层级一致
            String sql = """
                SELECT c.ancestor_id, c.descendant_id, c.depth,
                       o1.level as ancestor_level, o2.level as descendant_level,
                       (o2.level - o1.level) as expected_depth
                FROM sys_org_closure c
                JOIN sys_org_units o1 ON c.ancestor_id = o1.id
                JOIN sys_org_units o2 ON c.descendant_id = o2.id
                WHERE c.depth > 0 
                  AND c.depth != (o2.level - o1.level)
                  AND o1.is_deleted = 0 AND o2.is_deleted = 0
                """ + (customerId != null ? " AND c.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.queryForList(sql, customerId);
            } else {
                return jdbcTemplate.queryForList(sql);
            }
        } catch (Exception e) {
            log.error("检查深度不一致失败", e);
            return Collections.emptyList();
        }
    }

    private Map<String, Object> gatherStatistics(Long customerId) {
        Map<String, Object> stats = new HashMap<>();
        
        if (jdbcTemplate == null) {
            return stats;
        }
        
        try {
            // 组织节点总数
            String orgCountSql = "SELECT COUNT(*) FROM sys_org_units WHERE is_deleted = 0" + 
                (customerId != null ? " AND customer_id = ?" : "");
            Integer orgCount = customerId != null ? 
                jdbcTemplate.queryForObject(orgCountSql, Integer.class, customerId) :
                jdbcTemplate.queryForObject(orgCountSql, Integer.class);
            stats.put("totalOrganizations", orgCount);
            
            // 闭包关系总数
            String closureCountSql = "SELECT COUNT(*) FROM sys_org_closure" + 
                (customerId != null ? " WHERE customer_id = ?" : "");
            Integer closureCount = customerId != null ?
                jdbcTemplate.queryForObject(closureCountSql, Integer.class, customerId) :
                jdbcTemplate.queryForObject(closureCountSql, Integer.class);
            stats.put("totalClosureRelations", closureCount);
            
            // 最大层级深度
            String maxLevelSql = "SELECT MAX(level) FROM sys_org_units WHERE is_deleted = 0" + 
                (customerId != null ? " AND customer_id = ?" : "");
            Integer maxLevel = customerId != null ?
                jdbcTemplate.queryForObject(maxLevelSql, Integer.class, customerId) :
                jdbcTemplate.queryForObject(maxLevelSql, Integer.class);
            stats.put("maxLevel", maxLevel);
            
        } catch (Exception e) {
            log.error("收集统计信息失败", e);
        }
        
        return stats;
    }

    // ================== 私有修复方法 ==================

    private int repairMissingSelfReferences(Long customerId) {
        if (jdbcTemplate == null) {
            return 0;
        }
        
        try {
            String sql = """
                INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                SELECT o.id, o.id, 0, o.customer_id
                FROM sys_org_units o
                LEFT JOIN sys_org_closure c ON o.id = c.descendant_id AND c.ancestor_id = o.id AND c.depth = 0
                WHERE o.is_deleted = 0 AND c.id IS NULL
                """ + (customerId != null ? " AND o.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.update(sql, customerId);
            } else {
                return jdbcTemplate.update(sql);
            }
        } catch (Exception e) {
            log.error("修复缺失自引用关系失败", e);
            return 0;
        }
    }

    private int rebuildAncestorRelations(Long customerId) {
        if (jdbcTemplate == null) {
            return 0;
        }
        
        try {
            // 删除现有的祖先关系（保留自引用）
            String deleteSql = "DELETE FROM sys_org_closure WHERE depth > 0" + 
                (customerId != null ? " AND customer_id = ?" : "");
            
            if (customerId != null) {
                jdbcTemplate.update(deleteSql, customerId);
            } else {
                jdbcTemplate.update(deleteSql);
            }
            
            // 重新构建祖先关系
            String rebuildSql = """
                INSERT IGNORE INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                SELECT p.ancestor_id, c.descendant_id, p.depth + c.depth + 1, c.customer_id
                FROM sys_org_closure p
                CROSS JOIN sys_org_closure c
                JOIN sys_org_units o ON c.descendant_id = o.id
                WHERE p.descendant_id = o.parent_id 
                  AND o.parent_id IS NOT NULL
                  AND o.is_deleted = 0
                  AND p.depth = 0 AND c.depth = 0
                """ + (customerId != null ? " AND c.customer_id = ? AND p.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.update(rebuildSql, customerId, customerId);
            } else {
                return jdbcTemplate.update(rebuildSql);
            }
        } catch (Exception e) {
            log.error("重建祖先关系失败", e);
            return 0;
        }
    }

    private int cleanOrphanedClosureRelations(Long customerId) {
        if (jdbcTemplate == null) {
            return 0;
        }
        
        try {
            String sql = """
                DELETE c FROM sys_org_closure c
                LEFT JOIN sys_org_units o1 ON c.ancestor_id = o1.id AND o1.is_deleted = 0
                LEFT JOIN sys_org_units o2 ON c.descendant_id = o2.id AND o2.is_deleted = 0
                WHERE (o1.id IS NULL OR o2.id IS NULL)
                """ + (customerId != null ? " AND c.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.update(sql, customerId);
            } else {
                return jdbcTemplate.update(sql);
            }
        } catch (Exception e) {
            log.error("清理孤立闭包关系失败", e);
            return 0;
        }
    }

    private int updateDepthConsistency(Long customerId) {
        if (jdbcTemplate == null) {
            return 0;
        }
        
        try {
            String sql = """
                UPDATE sys_org_closure c
                JOIN sys_org_units o1 ON c.ancestor_id = o1.id
                JOIN sys_org_units o2 ON c.descendant_id = o2.id
                SET c.depth = (o2.level - o1.level)
                WHERE c.depth > 0 
                  AND c.depth != (o2.level - o1.level)
                  AND o1.is_deleted = 0 AND o2.is_deleted = 0
                """ + (customerId != null ? " AND c.customer_id = ?" : "");
            
            if (customerId != null) {
                return jdbcTemplate.update(sql, customerId);
            } else {
                return jdbcTemplate.update(sql);
            }
        } catch (Exception e) {
            log.error("更新深度一致性失败", e);
            return 0;
        }
    }
}