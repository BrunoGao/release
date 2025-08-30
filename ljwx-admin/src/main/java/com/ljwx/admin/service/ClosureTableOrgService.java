package com.ljwx.admin.service;

import com.ljwx.admin.entity.SysOrgUnits;
import com.ljwx.admin.entity.SysOrgClosure;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.BeanPropertyRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 组织架构闭包表高性能服务
 * 
 * 核心特性:
 * - O(1)复杂度的层级查询
 * - 批量查询优化
 * - 智能缓存策略
 * - 性能监控
 * 
 * @author Claude Code Assistant
 * @since 2025-08-30
 */
@Slf4j
@Service
public class ClosureTableOrgService {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Autowired
    private ThreadPoolExecutor orgQueryExecutor;

    private static final String CACHE_NAME = "org_closure";
    private static final int MAX_BATCH_SIZE = 1000;

    // ================== 高性能查询方法 ==================

    /**
     * 查找所有子部门 - O(1)复杂度
     * 
     * @param parentId 父部门ID
     * @param customerId 租户ID
     * @return 子部门列表，按层级和排序排列
     */
    @Cacheable(value = CACHE_NAME, key = "'children_' + #parentId + '_' + #customerId")
    public List<SysOrgUnits> findAllChildren(Long parentId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            String sql = """
                SELECT o.id, o.name, o.code, o.level, o.parent_id, 
                       o.customer_id, o.status, o.sort, c.depth
                FROM sys_org_units_optimized o
                INNER JOIN sys_org_closure c ON o.id = c.descendant_id
                WHERE c.ancestor_id = ? 
                  AND c.customer_id = ?
                  AND c.depth > 0
                  AND o.status = '1' 
                  AND o.is_deleted = 0
                ORDER BY c.depth ASC, o.sort ASC, o.id ASC
                """;

            List<SysOrgUnits> results = jdbcTemplate.query(sql, 
                new BeanPropertyRowMapper<>(SysOrgUnits.class), 
                parentId, customerId);

            stopWatch.stop();
            logPerformance("findAllChildren", parentId, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findAllChildren", parentId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("查找子部门失败: parentId={}, customerId={}", parentId, customerId, e);
            return Collections.emptyList();
        }
    }

    /**
     * 查找直接子部门 - O(1)复杂度
     * 
     * @param parentId 父部门ID  
     * @param customerId 租户ID
     * @return 直接子部门列表
     */
    @Cacheable(value = CACHE_NAME, key = "'direct_children_' + #parentId + '_' + #customerId")
    public List<SysOrgUnits> findDirectChildren(Long parentId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            String sql = """
                SELECT o.id, o.name, o.code, o.level, o.parent_id, 
                       o.customer_id, o.status, o.sort
                FROM sys_org_units_optimized o
                INNER JOIN sys_org_closure c ON o.id = c.descendant_id  
                WHERE c.ancestor_id = ?
                  AND c.customer_id = ?
                  AND c.depth = 1
                  AND o.status = '1'
                  AND o.is_deleted = 0
                ORDER BY o.sort ASC, o.id ASC
                """;

            List<SysOrgUnits> results = jdbcTemplate.query(sql, 
                new BeanPropertyRowMapper<>(SysOrgUnits.class),
                parentId, customerId);

            stopWatch.stop();
            logPerformance("findDirectChildren", parentId, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findDirectChildren", parentId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("查找直接子部门失败: parentId={}, customerId={}", parentId, customerId, e);
            return Collections.emptyList();
        }
    }

    /**
     * 查找祖先路径 - O(1)复杂度
     * 
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return 祖先路径，从根节点到目标节点
     */
    @Cacheable(value = CACHE_NAME, key = "'ancestors_' + #orgId + '_' + #customerId")
    public List<SysOrgUnits> findAncestorPath(Long orgId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            String sql = """
                SELECT o.id, o.name, o.code, o.level, o.parent_id, 
                       o.customer_id, o.status, o.sort, c.depth
                FROM sys_org_units_optimized o
                INNER JOIN sys_org_closure c ON o.id = c.ancestor_id
                WHERE c.descendant_id = ?
                  AND c.customer_id = ?  
                  AND o.status = '1'
                  AND o.is_deleted = 0
                ORDER BY c.depth DESC
                """;

            List<SysOrgUnits> results = jdbcTemplate.query(sql, 
                new BeanPropertyRowMapper<>(SysOrgUnits.class),
                orgId, customerId);

            stopWatch.stop();
            logPerformance("findAncestorPath", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findAncestorPath", orgId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("查找祖先路径失败: orgId={}, customerId={}", orgId, customerId, e);
            return Collections.emptyList();
        }
    }

    /**
     * 批量查找部门主管 - 高性能批量查询，告警系统关键优化
     * 
     * @param orgIds 组织ID列表
     * @param customerId 租户ID
     * @return Map<部门ID, 主管用户ID列表>
     */
    public Map<Long, List<Long>> batchFindDepartmentManagers(List<Long> orgIds, Long customerId) {
        if (orgIds == null || orgIds.isEmpty()) {
            return Collections.emptyMap();
        }

        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            // 分批处理，避免IN子句过长
            Map<Long, List<Long>> results = new HashMap<>();
            
            for (int i = 0; i < orgIds.size(); i += MAX_BATCH_SIZE) {
                List<Long> batch = orgIds.subList(i, Math.min(i + MAX_BATCH_SIZE, orgIds.size()));
                
                String placeholders = String.join(",", Collections.nCopies(batch.size(), "?"));
                String sql = String.format("""
                    SELECT DISTINCT uo.org_id, uo.user_id
                    FROM sys_user_org_optimized uo
                    INNER JOIN sys_org_closure c ON uo.org_id = c.descendant_id
                    WHERE c.ancestor_id IN (%s)
                      AND c.customer_id = ?
                      AND uo.principal = '1'
                      AND uo.is_deleted = 0
                      AND uo.customer_id = ?
                    """, placeholders);

                Object[] params = new Object[batch.size() + 2];
                for (int j = 0; j < batch.size(); j++) {
                    params[j] = batch.get(j);
                }
                params[batch.size()] = customerId;
                params[batch.size() + 1] = customerId;

                List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql, params);
                
                // 按部门分组
                Map<Long, List<Long>> batchResults = rows.stream().collect(
                    Collectors.groupingBy(
                        row -> (Long) row.get("org_id"),
                        Collectors.mapping(
                            row -> (Long) row.get("user_id"), 
                            Collectors.toList()
                        )
                    )
                );
                
                results.putAll(batchResults);
            }

            stopWatch.stop();
            logPerformance("batchFindDepartmentManagers", null, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            log.debug("批量查找部门主管完成: 查询{}个部门, 找到{}个部门有主管, 耗时{}ms", 
                orgIds.size(), results.size(), stopWatch.getTotalTimeMillis());

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("batchFindDepartmentManagers", null, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("批量查找部门主管失败: orgIds={}, customerId={}", orgIds, customerId, e);
            return Collections.emptyMap();
        }
    }

    /**
     * 查找租户级管理员
     * 
     * @param customerId 租户ID
     * @return 管理员用户ID列表
     */
    @Cacheable(value = CACHE_NAME, key = "'tenant_admins_' + #customerId")
    public List<Long> findTenantAdmins(Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            // 查找根级别组织的主管作为租户管理员
            String sql = """
                SELECT DISTINCT uo.user_id
                FROM sys_user_org_optimized uo
                INNER JOIN sys_org_units_optimized o ON uo.org_id = o.id
                WHERE o.customer_id = ?
                  AND o.parent_id IS NULL
                  AND o.level = 0
                  AND uo.principal = '1'
                  AND uo.is_deleted = 0
                  AND o.is_deleted = 0
                  AND o.status = '1'
                """;

            List<Long> results = jdbcTemplate.queryForList(sql, Long.class, customerId);

            stopWatch.stop();
            logPerformance("findTenantAdmins", null, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findTenantAdmins", null, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("查找租户管理员失败: customerId={}", customerId, e);
            return Collections.emptyList();
        }
    }

    /**
     * 判断是否为祖先关系 - O(1)复杂度
     * 
     * @param ancestorId 祖先节点ID
     * @param descendantId 后代节点ID
     * @param customerId 租户ID
     * @return true表示存在祖先关系
     */
    public boolean isAncestor(Long ancestorId, Long descendantId, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            String sql = """
                SELECT COUNT(1) FROM sys_org_closure 
                WHERE ancestor_id = ? 
                  AND descendant_id = ?
                  AND customer_id = ?
                  AND depth > 0
                """;

            Integer count = jdbcTemplate.queryForObject(sql, Integer.class, 
                ancestorId, descendantId, customerId);

            boolean result = count != null && count > 0;

            stopWatch.stop();
            logPerformance("isAncestor", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), result ? 1 : 0, true, null);

            return result;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("isAncestor", ancestorId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("判断祖先关系失败: ancestorId={}, descendantId={}, customerId={}", 
                ancestorId, descendantId, customerId, e);
            return false;
        }
    }

    /**
     * 查找指定深度的组织
     * 
     * @param rootId 根节点ID
     * @param depth 目标深度
     * @param customerId 租户ID
     * @return 指定深度的组织列表
     */
    public List<SysOrgUnits> findByDepth(Long rootId, int depth, Long customerId) {
        StopWatch stopWatch = new StopWatch();
        stopWatch.start();

        try {
            String sql = """
                SELECT o.id, o.name, o.code, o.level, o.parent_id, 
                       o.customer_id, o.status, o.sort
                FROM sys_org_units_optimized o
                INNER JOIN sys_org_closure c ON o.id = c.descendant_id
                WHERE c.ancestor_id = ?
                  AND c.customer_id = ?
                  AND c.depth = ?
                  AND o.status = '1'
                  AND o.is_deleted = 0  
                ORDER BY o.sort ASC, o.id ASC
                """;

            List<SysOrgUnits> results = jdbcTemplate.query(sql, 
                new BeanPropertyRowMapper<>(SysOrgUnits.class),
                rootId, customerId, depth);

            stopWatch.stop();
            logPerformance("findByDepth", rootId, customerId, 
                stopWatch.getTotalTimeMillis(), results.size(), true, null);

            return results;

        } catch (Exception e) {
            stopWatch.stop();
            logPerformance("findByDepth", rootId, customerId, 
                stopWatch.getTotalTimeMillis(), 0, false, e.getMessage());
            
            log.error("按深度查找组织失败: rootId={}, depth={}, customerId={}", 
                rootId, depth, customerId, e);
            return Collections.emptyList();
        }
    }

    // ================== 异步批量查询方法 ==================

    /**
     * 异步批量查找子部门 - 提升并发性能
     * 
     * @param parentIds 父部门ID列表
     * @param customerId 租户ID
     * @return 异步结果Map<父部门ID, 子部门列表>
     */
    public CompletableFuture<Map<Long, List<SysOrgUnits>>> asyncBatchFindChildren(
            List<Long> parentIds, Long customerId) {
        
        return CompletableFuture.supplyAsync(() -> {
            Map<Long, List<SysOrgUnits>> results = new HashMap<>();
            
            // 并行处理
            List<CompletableFuture<Void>> futures = parentIds.stream()
                .map(parentId -> CompletableFuture.runAsync(() -> {
                    List<SysOrgUnits> children = findAllChildren(parentId, customerId);
                    synchronized (results) {
                        results.put(parentId, children);
                    }
                }, orgQueryExecutor))
                .collect(Collectors.toList());
            
            // 等待所有任务完成
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
            
            return results;
        }, orgQueryExecutor);
    }

    // ================== 缓存管理方法 ==================

    /**
     * 清除组织相关缓存
     * 
     * @param orgId 组织ID (可选)
     * @param customerId 租户ID
     */
    @CacheEvict(value = CACHE_NAME, allEntries = true)
    public void clearOrgCache(Long orgId, Long customerId) {
        log.info("清除组织缓存: orgId={}, customerId={}", orgId, customerId);
    }

    // ================== 性能监控方法 ==================

    /**
     * 记录性能日志
     */
    private void logPerformance(String operation, Long orgId, Long customerId, 
                               long executionTime, int resultCount, boolean success, String errorMessage) {
        try {
            String insertSql = """
                INSERT INTO sys_org_performance_log 
                (operation_type, customer_id, org_id, execution_time_ms, result_count, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """;
            
            jdbcTemplate.update(insertSql, operation, customerId, orgId, 
                executionTime, resultCount, success ? 1 : 0, errorMessage);
            
            // 性能告警
            if (executionTime > 100) { // 超过100ms告警
                log.warn("⚠️ 组织查询性能告警: operation={}, executionTime={}ms, resultCount={}", 
                    operation, executionTime, resultCount);
            }
            
        } catch (Exception e) {
            // 记录性能日志失败不应影响业务逻辑
            log.debug("记录性能日志失败", e);
        }
    }

    /**
     * 获取性能统计
     * 
     * @param hours 统计时间范围(小时)
     * @return 性能统计信息
     */
    public Map<String, Object> getPerformanceStats(int hours) {
        String sql = """
            SELECT 
                operation_type,
                COUNT(*) as total_calls,
                AVG(execution_time_ms) as avg_time_ms,
                MAX(execution_time_ms) as max_time_ms,
                MIN(execution_time_ms) as min_time_ms,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count
            FROM sys_org_performance_log 
            WHERE create_time >= DATE_SUB(NOW(), INTERVAL ? HOUR)
            GROUP BY operation_type
            ORDER BY total_calls DESC
            """;

        List<Map<String, Object>> stats = jdbcTemplate.queryForList(sql, hours);
        
        Map<String, Object> result = new HashMap<>();
        result.put("timeRange", hours + " hours");
        result.put("operations", stats);
        result.put("generatedAt", LocalDateTime.now());
        
        return result;
    }
}