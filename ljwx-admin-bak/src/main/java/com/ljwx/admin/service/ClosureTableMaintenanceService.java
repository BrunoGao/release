package com.ljwx.admin.service;

import com.ljwx.admin.entity.SysOrgUnits;
import com.ljwx.admin.entity.SysOrgClosure;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.PreparedStatementCallback;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.util.StopWatch;
import org.springframework.cache.annotation.CacheEvict;

import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 闭包表维护操作服务
 * 
 * 提供组织架构闭包表的所有维护操作：
 * - 插入新节点
 * - 删除节点及子树  
 * - 移动节点
 * - 批量操作
 * - 数据一致性检查
 * 
 * @author Claude Code Assistant
 * @since 2025-08-30
 */
@Slf4j
@Service
public class ClosureTableMaintenanceService {

    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private TransactionTemplate transactionTemplate;
    
    @Autowired
    private ClosureTableOrgService queryService;

    private static final String CACHE_NAME = "org_closure";
    private static final int BATCH_SIZE = 500;

    // ================== 节点插入操作 ==================

    /**
     * 插入新组织节点并维护闭包关系
     * 
     * @param orgUnit 新组织节点信息
     * @return 新插入的组织ID
     * @throws RuntimeException 插入失败时抛出异常
     */
    @Transactional(rollbackFor = Exception.class)
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public Long insertOrgWithClosure(SysOrgUnits orgUnit) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            // 1. 计算新节点的层级
            int level = calculateNodeLevel(orgUnit.getParentId(), orgUnit.getCustomerId());
            orgUnit.setLevel(level);
            
            // 2. 插入组织基本信息
            Long newOrgId = insertOrgUnit(orgUnit);
            orgUnit.setId(newOrgId);
            
            // 3. 插入自引用闭包关系
            insertSelfReference(newOrgId, orgUnit.getCustomerId());
            
            // 4. 如果有父节点，插入祖先关系
            if (orgUnit.getParentId() != null && orgUnit.getParentId() > 0) {
                insertAncestorRelations(newOrgId, orgUnit.getParentId(), orgUnit.getCustomerId());
            }
            
            stopWatch.stop();
            logMaintenanceOperation("insertOrgWithClosure", newOrgId, orgUnit.getCustomerId(), 
                stopWatch.getTotalTimeMillis(), 1, true, null);
            
            log.info("✅ 成功插入组织节点: id={}, name={}, parentId={}, level={}, 耗时={}ms", 
                newOrgId, orgUnit.getName(), orgUnit.getParentId(), level, stopWatch.getTotalTimeMillis());
            
            return newOrgId;
            
        } catch (Exception e) {
            stopWatch.stop();
            logMaintenanceOperation("insertOrgWithClosure", null, orgUnit.getCustomerId(), 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
                
            log.error("❌ 插入组织节点失败: name={}, parentId={}", orgUnit.getName(), orgUnit.getParentId(), e);
            throw new RuntimeException("插入组织节点失败: " + e.getMessage(), e);
        }
    }

    /**
     * 批量插入组织节点
     * 
     * @param orgUnits 组织节点列表
     * @param customerId 租户ID
     * @return 插入成功的组织ID列表
     */
    @Transactional(rollbackFor = Exception.class)
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public List<Long> batchInsertOrgWithClosure(List<SysOrgUnits> orgUnits, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        List<Long> insertedIds = new ArrayList<>();
        
        try {
            // 按层级排序，确保父节点先于子节点插入
            orgUnits.sort(Comparator.comparing(org -> org.getLevel() != null ? org.getLevel() : 0));
            
            for (SysOrgUnits orgUnit : orgUnits) {
                orgUnit.setCustomerId(customerId);
                Long newId = insertOrgWithClosure(orgUnit);
                insertedIds.add(newId);
            }
            
            stopWatch.stop();
            logMaintenanceOperation("batchInsertOrgWithClosure", null, customerId, 
                stopWatch.getTotalTimeMillis(), insertedIds.size(), true, null);
            
            log.info("✅ 批量插入组织节点完成: 成功={}个, 耗时={}ms", insertedIds.size(), stopWatch.getTotalTimeMillis());
            
            return insertedIds;
            
        } catch (Exception e) {
            stopWatch.stop();
            logMaintenanceOperation("batchInsertOrgWithClosure", null, customerId, 
                stopWatch.getTotalTimeMillis(), insertedIds.size(), false, e.getMessage());
                
            log.error("❌ 批量插入组织节点失败: 已插入={}个", insertedIds.size(), e);
            throw new RuntimeException("批量插入失败: " + e.getMessage(), e);
        }
    }

    // ================== 节点删除操作 ==================

    /**
     * 删除组织节点及其所有子节点（软删除）
     * 
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return 删除的节点数量
     */
    @Transactional(rollbackFor = Exception.class)
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public int deleteOrgWithClosure(Long orgId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            // 1. 获取所有要删除的子孙节点
            List<Long> toDeleteIds = findAllDescendantIds(orgId, customerId);
            toDeleteIds.add(orgId); // 包含自己
            
            if (toDeleteIds.isEmpty()) {
                log.warn("⚠️ 未找到要删除的组织节点: orgId={}, customerId={}", orgId, customerId);
                return 0;
            }
            
            // 2. 软删除组织节点
            int deletedCount = softDeleteOrgUnits(toDeleteIds, customerId);
            
            // 3. 删除相关的闭包关系
            deleteClosureRelations(toDeleteIds, customerId);
            
            stopWatch.stop();
            logMaintenanceOperation("deleteOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), deletedCount, true, null);
            
            log.info("✅ 成功删除组织节点树: rootId={}, 删除节点数={}, 耗时={}ms", 
                orgId, deletedCount, stopWatch.getTotalTimeMillis());
            
            return deletedCount;
            
        } catch (Exception e) {
            stopWatch.stop();
            logMaintenanceOperation("deleteOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
                
            log.error("❌ 删除组织节点失败: orgId={}, customerId={}", orgId, customerId, e);
            throw new RuntimeException("删除组织节点失败: " + e.getMessage(), e);
        }
    }

    /**
     * 物理删除组织节点（谨慎使用）
     * 
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return 删除的节点数量
     */
    @Transactional(rollbackFor = Exception.class)
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public int hardDeleteOrgWithClosure(Long orgId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            // 1. 获取所有要删除的子孙节点
            List<Long> toDeleteIds = findAllDescendantIds(orgId, customerId);
            toDeleteIds.add(orgId);
            
            // 2. 删除用户组织关系
            deleteUserOrgRelations(toDeleteIds, customerId);
            
            // 3. 删除闭包关系
            deleteClosureRelations(toDeleteIds, customerId);
            
            // 4. 物理删除组织节点
            int deletedCount = hardDeleteOrgUnits(toDeleteIds);
            
            stopWatch.stop();
            logMaintenanceOperation("hardDeleteOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), deletedCount, true, null);
            
            log.warn("⚠️ 物理删除组织节点树: rootId={}, 删除节点数={}, 耗时={}ms", 
                orgId, deletedCount, stopWatch.getTotalTimeMillis());
            
            return deletedCount;
            
        } catch (Exception e) {
            stopWatch.stop();
            logMaintenanceOperation("hardDeleteOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
                
            log.error("❌ 物理删除组织节点失败: orgId={}, customerId={}", orgId, customerId, e);
            throw new RuntimeException("物理删除失败: " + e.getMessage(), e);
        }
    }

    // ================== 节点移动操作 ==================

    /**
     * 移动组织节点到新的父节点下
     * 
     * @param orgId 要移动的组织ID
     * @param newParentId 新父节点ID（null表示移动到根级）
     * @param customerId 租户ID
     * @return 是否移动成功
     */
    @Transactional(rollbackFor = Exception.class)
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public boolean moveOrgWithClosure(Long orgId, Long newParentId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        try {
            // 1. 数据验证
            if (!validateMoveOperation(orgId, newParentId, customerId)) {
                log.warn("⚠️ 移动操作验证失败: orgId={}, newParentId={}, customerId={}", 
                    orgId, newParentId, customerId);
                return false;
            }
            
            // 2. 获取要移动的子树所有节点
            List<Long> subtreeIds = findAllDescendantIds(orgId, customerId);
            subtreeIds.add(orgId);
            
            // 3. 删除旧的祖先关系（保留自引用关系）
            deleteOldAncestorRelations(subtreeIds, customerId);
            
            // 4. 建立新的祖先关系
            if (newParentId != null && newParentId > 0) {
                insertNewAncestorRelations(subtreeIds, newParentId, customerId);
            }
            
            // 5. 更新组织表的 parent_id 和 level
            updateOrgParentAndLevel(orgId, newParentId, customerId);
            
            stopWatch.stop();
            logMaintenanceOperation("moveOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), subtreeIds.size(), true, null);
            
            log.info("✅ 成功移动组织节点: orgId={}, newParentId={}, 影响节点数={}, 耗时={}ms", 
                orgId, newParentId, subtreeIds.size(), stopWatch.getTotalTimeMillis());
            
            return true;
            
        } catch (Exception e) {
            stopWatch.stop();
            logMaintenanceOperation("moveOrgWithClosure", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
                
            log.error("❌ 移动组织节点失败: orgId={}, newParentId={}, customerId={}", 
                orgId, newParentId, customerId, e);
            throw new RuntimeException("移动组织节点失败: " + e.getMessage(), e);
        }
    }

    // ================== 数据一致性检查 ==================

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
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public Map<String, Object> repairDataConsistency(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();
        
        Map<String, Object> result = new HashMap<>();
        
        try {
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

    // ================== 私有辅助方法 ==================

    private int calculateNodeLevel(Long parentId, Long customerId) {
        if (parentId == null || parentId == 0) {
            return 0; // 根节点
        }
        
        String sql = "SELECT level FROM sys_org_units_optimized WHERE id = ? AND customer_id = ? AND is_deleted = 0";
        Integer parentLevel = jdbcTemplate.queryForObject(sql, Integer.class, parentId, customerId);
        
        return parentLevel != null ? parentLevel + 1 : 0;
    }

    private Long insertOrgUnit(SysOrgUnits orgUnit) {
        String sql = """
            INSERT INTO sys_org_units_optimized 
            (name, code, parent_id, customer_id, level, status, sort, create_time, update_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, NOW(), NOW())
            """;
        
        jdbcTemplate.execute(sql, (PreparedStatementCallback<Void>) ps -> {
            ps.setString(1, orgUnit.getName());
            ps.setString(2, orgUnit.getCode());
            ps.setObject(3, orgUnit.getParentId());
            ps.setLong(4, orgUnit.getCustomerId());
            ps.setInt(5, orgUnit.getLevel() != null ? orgUnit.getLevel() : 0);
            ps.setString(6, orgUnit.getStatus() != null ? orgUnit.getStatus() : "1");
            ps.setInt(7, orgUnit.getSort() != null ? orgUnit.getSort() : 0);
            ps.executeUpdate();
            return null;
        });
        
        // 获取新插入的ID
        return jdbcTemplate.queryForObject("SELECT LAST_INSERT_ID()", Long.class);
    }

    private void insertSelfReference(Long orgId, Long customerId) {
        String sql = """
            INSERT INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
            VALUES (?, ?, 0, ?)
            """;
        jdbcTemplate.update(sql, orgId, orgId, customerId);
    }

    private void insertAncestorRelations(Long newOrgId, Long parentId, Long customerId) {
        String sql = """
            INSERT INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
            SELECT ancestor_id, ?, depth + 1, customer_id
            FROM sys_org_closure 
            WHERE descendant_id = ? AND customer_id = ?
            """;
        jdbcTemplate.update(sql, newOrgId, parentId, customerId);
    }

    private List<Long> findAllDescendantIds(Long orgId, Long customerId) {
        String sql = """
            SELECT DISTINCT descendant_id 
            FROM sys_org_closure 
            WHERE ancestor_id = ? AND customer_id = ? AND depth > 0
            """;
        return jdbcTemplate.queryForList(sql, Long.class, orgId, customerId);
    }

    private int softDeleteOrgUnits(List<Long> orgIds, Long customerId) {
        if (orgIds.isEmpty()) return 0;
        
        String placeholders = String.join(",", Collections.nCopies(orgIds.size(), "?"));
        String sql = String.format("""
            UPDATE sys_org_units_optimized 
            SET is_deleted = 1, status = '0', update_time = NOW()
            WHERE id IN (%s) AND customer_id = ?
            """, placeholders);
        
        Object[] params = new Object[orgIds.size() + 1];
        for (int i = 0; i < orgIds.size(); i++) {
            params[i] = orgIds.get(i);
        }
        params[orgIds.size()] = customerId;
        
        return jdbcTemplate.update(sql, params);
    }

    private void deleteClosureRelations(List<Long> orgIds, Long customerId) {
        if (orgIds.isEmpty()) return;
        
        String placeholders = String.join(",", Collections.nCopies(orgIds.size(), "?"));
        String sql = String.format("""
            DELETE FROM sys_org_closure 
            WHERE (ancestor_id IN (%s) OR descendant_id IN (%s)) 
              AND customer_id = ?
            """, placeholders, placeholders);
        
        Object[] params = new Object[orgIds.size() * 2 + 1];
        for (int i = 0; i < orgIds.size(); i++) {
            params[i] = orgIds.get(i);
            params[i + orgIds.size()] = orgIds.get(i);
        }
        params[orgIds.size() * 2] = customerId;
        
        jdbcTemplate.update(sql, params);
    }

    private boolean validateMoveOperation(Long orgId, Long newParentId, Long customerId) {
        // 1. 检查目标节点是否存在
        if (orgId == null) return false;
        
        // 2. 不能移动到自己
        if (Objects.equals(orgId, newParentId)) return false;
        
        // 3. 不能移动到自己的子孙节点下（避免循环引用）
        if (newParentId != null && queryService.isAncestor(orgId, newParentId, customerId)) {
            return false;
        }
        
        return true;
    }

    private void deleteOldAncestorRelations(List<Long> subtreeIds, Long customerId) {
        if (subtreeIds.isEmpty()) return;
        
        String placeholders = String.join(",", Collections.nCopies(subtreeIds.size(), "?"));
        String sql = String.format("""
            DELETE FROM sys_org_closure 
            WHERE descendant_id IN (%s) AND customer_id = ? AND depth > 0
            """, placeholders);
        
        Object[] params = new Object[subtreeIds.size() + 1];
        for (int i = 0; i < subtreeIds.size(); i++) {
            params[i] = subtreeIds.get(i);
        }
        params[subtreeIds.size()] = customerId;
        
        jdbcTemplate.update(sql, params);
    }

    private void insertNewAncestorRelations(List<Long> subtreeIds, Long newParentId, Long customerId) {
        for (Long subtreeId : subtreeIds) {
            String sql = """
                INSERT INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
                SELECT ancestor_id, ?, depth + 1, customer_id
                FROM sys_org_closure 
                WHERE descendant_id = ? AND customer_id = ?
                """;
            jdbcTemplate.update(sql, subtreeId, newParentId, customerId);
        }
    }

    private void updateOrgParentAndLevel(Long orgId, Long newParentId, Long customerId) {
        int newLevel = calculateNodeLevel(newParentId, customerId);
        
        String sql = """
            UPDATE sys_org_units_optimized 
            SET parent_id = ?, level = ?, update_time = NOW()
            WHERE id = ? AND customer_id = ?
            """;
        jdbcTemplate.update(sql, newParentId, newLevel, orgId, customerId);
    }

    // ================== 数据一致性检查辅助方法 ==================

    private List<Map<String, Object>> checkMissingSelfReferences(Long customerId) {
        String sql = """
            SELECT o.id, o.name 
            FROM sys_org_units_optimized o
            LEFT JOIN sys_org_closure c ON o.id = c.descendant_id AND c.ancestor_id = o.id AND c.depth = 0
            WHERE o.customer_id = ? AND o.is_deleted = 0 AND c.id IS NULL
            """;
        return jdbcTemplate.queryForList(sql, customerId);
    }

    private List<Map<String, Object>> checkMissingAncestorRelations(Long customerId) {
        // 这个查询比较复杂，检查是否存在应该有但缺失的祖先关系
        String sql = """
            SELECT o.id, o.name, o.parent_id 
            FROM sys_org_units_optimized o
            WHERE o.customer_id = ? AND o.is_deleted = 0 AND o.parent_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM sys_org_closure c 
                  WHERE c.descendant_id = o.id AND c.ancestor_id = o.parent_id AND c.depth = 1
              )
            """;
        return jdbcTemplate.queryForList(sql, customerId);
    }

    private List<Map<String, Object>> checkOrphanedClosureRelations(Long customerId) {
        String sql = """
            SELECT c.ancestor_id, c.descendant_id, c.depth
            FROM sys_org_closure c
            LEFT JOIN sys_org_units_optimized o1 ON c.ancestor_id = o1.id AND o1.is_deleted = 0
            LEFT JOIN sys_org_units_optimized o2 ON c.descendant_id = o2.id AND o2.is_deleted = 0
            WHERE c.customer_id = ? AND (o1.id IS NULL OR o2.id IS NULL)
            """;
        return jdbcTemplate.queryForList(sql, customerId);
    }

    private List<Map<String, Object>> checkDepthInconsistencies(Long customerId) {
        // 检查深度值是否与实际层级一致
        String sql = """
            SELECT c.ancestor_id, c.descendant_id, c.depth,
                   o1.level as ancestor_level, o2.level as descendant_level,
                   (o2.level - o1.level) as expected_depth
            FROM sys_org_closure c
            JOIN sys_org_units_optimized o1 ON c.ancestor_id = o1.id
            JOIN sys_org_units_optimized o2 ON c.descendant_id = o2.id
            WHERE c.customer_id = ? AND c.depth > 0 
              AND c.depth != (o2.level - o1.level)
              AND o1.is_deleted = 0 AND o2.is_deleted = 0
            """;
        return jdbcTemplate.queryForList(sql, customerId);
    }

    private Map<String, Object> gatherStatistics(Long customerId) {
        Map<String, Object> stats = new HashMap<>();
        
        // 组织节点总数
        String orgCountSql = "SELECT COUNT(*) FROM sys_org_units_optimized WHERE customer_id = ? AND is_deleted = 0";
        Integer orgCount = jdbcTemplate.queryForObject(orgCountSql, Integer.class, customerId);
        stats.put("totalOrganizations", orgCount);
        
        // 闭包关系总数
        String closureCountSql = "SELECT COUNT(*) FROM sys_org_closure WHERE customer_id = ?";
        Integer closureCount = jdbcTemplate.queryForObject(closureCountSql, Integer.class, customerId);
        stats.put("totalClosureRelations", closureCount);
        
        // 最大层级深度
        String maxLevelSql = "SELECT MAX(level) FROM sys_org_units_optimized WHERE customer_id = ? AND is_deleted = 0";
        Integer maxLevel = jdbcTemplate.queryForObject(maxLevelSql, Integer.class, customerId);
        stats.put("maxLevel", maxLevel);
        
        return stats;
    }

    // ================== 数据修复辅助方法 ==================

    private int repairMissingSelfReferences(Long customerId) {
        String sql = """
            INSERT INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
            SELECT o.id, o.id, 0, o.customer_id
            FROM sys_org_units_optimized o
            LEFT JOIN sys_org_closure c ON o.id = c.descendant_id AND c.ancestor_id = o.id AND c.depth = 0
            WHERE o.customer_id = ? AND o.is_deleted = 0 AND c.id IS NULL
            """;
        return jdbcTemplate.update(sql, customerId);
    }

    private int rebuildAncestorRelations(Long customerId) {
        // 删除现有的祖先关系（保留自引用）
        String deleteSql = "DELETE FROM sys_org_closure WHERE customer_id = ? AND depth > 0";
        jdbcTemplate.update(deleteSql, customerId);
        
        // 重新构建祖先关系
        String rebuildSql = """
            INSERT INTO sys_org_closure (ancestor_id, descendant_id, depth, customer_id)
            SELECT p.ancestor_id, c.descendant_id, p.depth + c.depth + 1, ?
            FROM sys_org_closure p
            CROSS JOIN sys_org_closure c
            JOIN sys_org_units_optimized o ON c.descendant_id = o.id
            WHERE p.customer_id = ? AND c.customer_id = ?
              AND p.descendant_id = o.parent_id 
              AND o.parent_id IS NOT NULL
              AND o.is_deleted = 0
            """;
        return jdbcTemplate.update(rebuildSql, customerId, customerId, customerId);
    }

    private int cleanOrphanedClosureRelations(Long customerId) {
        String sql = """
            DELETE c FROM sys_org_closure c
            LEFT JOIN sys_org_units_optimized o1 ON c.ancestor_id = o1.id AND o1.is_deleted = 0
            LEFT JOIN sys_org_units_optimized o2 ON c.descendant_id = o2.id AND o2.is_deleted = 0
            WHERE c.customer_id = ? AND (o1.id IS NULL OR o2.id IS NULL)
            """;
        return jdbcTemplate.update(sql, customerId);
    }

    private int updateDepthConsistency(Long customerId) {
        String sql = """
            UPDATE sys_org_closure c
            JOIN sys_org_units_optimized o1 ON c.ancestor_id = o1.id
            JOIN sys_org_units_optimized o2 ON c.descendant_id = o2.id
            SET c.depth = (o2.level - o1.level)
            WHERE c.customer_id = ? AND c.depth > 0 
              AND c.depth != (o2.level - o1.level)
              AND o1.is_deleted = 0 AND o2.is_deleted = 0
            """;
        return jdbcTemplate.update(sql, customerId);
    }

    private int hardDeleteOrgUnits(List<Long> orgIds) {
        if (orgIds.isEmpty()) return 0;
        
        String placeholders = String.join(",", Collections.nCopies(orgIds.size(), "?"));
        String sql = String.format("DELETE FROM sys_org_units_optimized WHERE id IN (%s)", placeholders);
        
        return jdbcTemplate.update(sql, orgIds.toArray());
    }

    private void deleteUserOrgRelations(List<Long> orgIds, Long customerId) {
        if (orgIds.isEmpty()) return;
        
        String placeholders = String.join(",", Collections.nCopies(orgIds.size(), "?"));
        String sql = String.format("""
            DELETE FROM sys_user_org_optimized 
            WHERE org_id IN (%s) AND customer_id = ?
            """, placeholders);
        
        Object[] params = new Object[orgIds.size() + 1];
        for (int i = 0; i < orgIds.size(); i++) {
            params[i] = orgIds.get(i);
        }
        params[orgIds.size()] = customerId;
        
        jdbcTemplate.update(sql, params);
    }

    /**
     * 记录维护操作日志
     */
    private void logMaintenanceOperation(String operation, Long orgId, Long customerId, 
                                       long executionTime, int affectedRows, boolean success, String errorMessage) {
        try {
            String sql = """
                INSERT INTO sys_org_performance_log 
                (operation_type, customer_id, org_id, execution_time_ms, result_count, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """;
            
            jdbcTemplate.update(sql, operation, customerId, orgId, 
                executionTime, affectedRows, success ? 1 : 0, errorMessage);
                
        } catch (Exception e) {
            // 记录日志失败不应影响主要业务逻辑
            log.debug("记录维护操作日志失败", e);
        }
    }
}