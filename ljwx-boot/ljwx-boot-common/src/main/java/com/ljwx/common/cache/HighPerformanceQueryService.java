package com.ljwx.common.cache;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StopWatch;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * 高性能关联查询服务
 * 基于Redis缓存和闭包表实现毫秒级多维度关联查询
 */
@Slf4j
@Service  
public class HighPerformanceQueryService {

    @Autowired
    private RedisRelationCacheService cacheService;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    private static final DateTimeFormatter TIMESTAMP_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    // =====================================================
    // 租户级别高效查询
    // =====================================================
    
    /**
     * 获取租户下所有用户（优先从缓存）
     * 性能目标: <5ms
     */
    public Set<Long> getTenantUsers(Long customerId) {
        StopWatch stopWatch = new StopWatch("getTenantUsers");
        stopWatch.start("cache-lookup");
        
        // 1. 尝试从缓存获取
        Set<Long> cachedUsers = cacheService.getTenantUsers(customerId);
        if (!CollectionUtils.isEmpty(cachedUsers)) {
            stopWatch.stop();
            log.debug("从缓存获取租户用户: customerId={}, users={}, time={}ms", 
                customerId, cachedUsers.size(), stopWatch.getTotalTimeMillis());
            return cachedUsers;
        }
        
        stopWatch.start("db-query");
        
        // 2. 缓存未命中，查询数据库
        String sql = """
            SELECT id FROM sys_user 
            WHERE customer_id = ? AND is_deleted = 0 AND status = '1'
            """;
        
        List<Long> userIds = jdbcTemplate.queryForList(sql, Long.class, customerId);
        Set<Long> users = new HashSet<>(userIds);
        
        stopWatch.stop();
        
        // 3. 更新缓存
        if (!users.isEmpty()) {
            cacheService.cacheTenantUsers(customerId, users);
        }
        
        log.debug("从数据库获取租户用户: customerId={}, users={}, time={}ms", 
            customerId, users.size(), stopWatch.getTotalTimeMillis());
        
        return users;
    }
    
    /**
     * 获取租户下所有部门（基于闭包表缓存）
     * 性能目标: <5ms
     */
    public Set<Long> getTenantOrgs(Long customerId) {
        // 1. 尝试从缓存获取
        Set<Long> cachedOrgs = cacheService.getTenantOrgs(customerId);
        if (!CollectionUtils.isEmpty(cachedOrgs)) {
            return cachedOrgs;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT id FROM sys_org_units 
            WHERE customer_id = ? AND is_deleted = 0 AND status = '1'
            """;
        
        List<Long> orgIds = jdbcTemplate.queryForList(sql, Long.class, customerId);
        Set<Long> orgs = new HashSet<>(orgIds);
        
        // 3. 更新缓存
        if (!orgs.isEmpty()) {
            cacheService.cacheTenantOrgs(customerId, orgs);
        }
        
        return orgs;
    }

    // =====================================================
    // 用户-部门关联查询（基于闭包表优化）
    // =====================================================
    
    /**
     * 获取用户所属所有部门（包含层级关系）
     * 性能目标: <3ms
     */
    public Set<Long> getUserOrgs(Long userId) {
        // 1. 尝试从缓存获取
        Set<Long> cachedOrgs = cacheService.getUserOrgs(userId);
        if (!CollectionUtils.isEmpty(cachedOrgs)) {
            return cachedOrgs;
        }
        
        // 2. 基于闭包表查询用户所属的所有层级部门
        String sql = """
            SELECT DISTINCT c.ancestor_id as org_id
            FROM sys_user_org uo
            INNER JOIN sys_org_closure c ON uo.org_id = c.descendant_id
            WHERE uo.user_id = ? AND uo.is_deleted = 0
            """;
        
        List<Long> orgIds = jdbcTemplate.queryForList(sql, Long.class, userId);
        Set<Long> orgs = new HashSet<>(orgIds);
        
        // 3. 缓存结果
        cacheService.cacheUserOrgs(userId, orgs);
        
        return orgs;
    }
    
    /**
     * 获取部门下所有用户（包含子部门用户）
     * 性能目标: <3ms
     */
    public Set<Long> getOrgUsers(Long orgId) {
        // 1. 尝试从缓存获取
        Set<Long> cachedUsers = cacheService.getOrgUsers(orgId);
        if (!CollectionUtils.isEmpty(cachedUsers)) {
            return cachedUsers;
        }
        
        // 2. 基于闭包表查询部门及其子部门的所有用户
        String sql = """
            SELECT DISTINCT uo.user_id
            FROM sys_org_closure c
            INNER JOIN sys_user_org uo ON c.descendant_id = uo.org_id
            INNER JOIN sys_user u ON uo.user_id = u.id
            WHERE c.ancestor_id = ? 
              AND uo.is_deleted = 0 
              AND u.is_deleted = 0 
              AND u.status = '1'
            """;
        
        List<Long> userIds = jdbcTemplate.queryForList(sql, Long.class, orgId);
        Set<Long> users = new HashSet<>(userIds);
        
        // 3. 缓存结果
        cacheService.cacheOrgUsers(orgId, users);
        
        return users;
    }
    
    /**
     * 获取部门所有后代部门（基于闭包表）
     * 性能目标: <2ms
     */
    public Set<Long> getOrgDescendants(Long orgId) {
        // 1. 尝试从缓存获取
        Set<Long> cachedDescendants = cacheService.getOrgDescendants(orgId);
        if (!CollectionUtils.isEmpty(cachedDescendants)) {
            return cachedDescendants;
        }
        
        // 2. 查询闭包表
        String sql = """
            SELECT descendant_id FROM sys_org_closure 
            WHERE ancestor_id = ? AND depth > 0
            """;
        
        List<Long> descendantIds = jdbcTemplate.queryForList(sql, Long.class, orgId);
        Set<Long> descendants = new HashSet<>(descendantIds);
        
        // 3. 缓存结果
        cacheService.cacheOrgDescendants(orgId, descendants);
        
        return descendants;
    }

    // =====================================================
    // 用户-设备关联查询
    // =====================================================
    
    /**
     * 获取用户关联的所有设备
     * 性能目标: <3ms
     */
    public Set<String> getUserDevices(Long userId) {
        // 1. 尝试从缓存获取
        Set<String> cachedDevices = cacheService.getUserDevices(userId);
        if (!CollectionUtils.isEmpty(cachedDevices)) {
            return cachedDevices;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT du.device_sn
            FROM t_device_user du
            INNER JOIN t_device_info d ON du.device_sn = d.serial_number
            WHERE du.user_id = ? 
              AND du.status = 'BIND' 
              AND d.status = 'online'
            """;
        
        List<String> deviceSns = jdbcTemplate.queryForList(sql, String.class, userId);
        Set<String> devices = new HashSet<>(deviceSns);
        
        // 3. 缓存结果
        cacheService.cacheUserDevices(userId, devices);
        
        return devices;
    }
    
    /**
     * 获取设备关联的用户
     * 性能目标: <2ms
     */
    public Long getDeviceUser(String deviceSn) {
        // 1. 尝试从缓存获取
        Long cachedUser = cacheService.getDeviceUser(deviceSn);
        if (cachedUser != null) {
            return cachedUser;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT du.user_id
            FROM t_device_user du
            INNER JOIN sys_user u ON du.user_id = u.id
            WHERE du.device_sn = ? 
              AND du.status = 'BIND' 
              AND u.is_deleted = 0
            """;
        
        List<Long> userIds = jdbcTemplate.queryForList(sql, Long.class, deviceSn);
        Long userId = userIds.isEmpty() ? null : userIds.get(0);
        
        // 3. 缓存结果
        if (userId != null) {
            cacheService.cacheDeviceUser(deviceSn, userId);
        }
        
        return userId;
    }

    // =====================================================
    // 部门-设备关联查询
    // =====================================================
    
    /**
     * 获取部门下所有设备（包含子部门设备）
     * 性能目标: <5ms
     */
    public Set<String> getOrgDevices(Long orgId) {
        // 1. 尝试从缓存获取
        Set<String> cachedDevices = cacheService.getOrgDevices(orgId);
        if (!CollectionUtils.isEmpty(cachedDevices)) {
            return cachedDevices;
        }
        
        // 2. 基于闭包表查询部门及其子部门的所有设备
        String sql = """
            SELECT DISTINCT du.device_sn
            FROM sys_org_closure c
            INNER JOIN sys_user_org uo ON c.descendant_id = uo.org_id
            INNER JOIN sys_user u ON uo.user_id = u.id
            INNER JOIN t_device_user du ON u.id = du.user_id
            INNER JOIN t_device_info d ON du.device_sn = d.serial_number
            WHERE c.ancestor_id = ? 
              AND uo.is_deleted = 0 
              AND u.is_deleted = 0 
              AND du.status = 'BIND' 
              AND d.status = 'online'
            """;
        
        List<String> deviceSns = jdbcTemplate.queryForList(sql, String.class, orgId);
        Set<String> devices = new HashSet<>(deviceSns);
        
        // 3. 缓存结果
        cacheService.cacheOrgDevices(orgId, devices);
        
        return devices;
    }
    
    /**
     * 获取设备所属部门
     * 性能目标: <3ms
     */
    public Long getDeviceOrg(String deviceSn) {
        // 1. 尝试从缓存获取
        Long cachedOrg = cacheService.getDeviceOrg(deviceSn);
        if (cachedOrg != null) {
            return cachedOrg;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT uo.org_id
            FROM t_device_user du
            INNER JOIN sys_user u ON du.user_id = u.id
            INNER JOIN sys_user_org uo ON u.id = uo.user_id
            WHERE du.device_sn = ? 
              AND du.status = 'BIND' 
              AND u.is_deleted = 0 
              AND uo.is_deleted = 0
            LIMIT 1
            """;
        
        List<Long> orgIds = jdbcTemplate.queryForList(sql, Long.class, deviceSn);
        Long orgId = orgIds.isEmpty() ? null : orgIds.get(0);
        
        // 3. 缓存结果
        if (orgId != null) {
            cacheService.cacheDeviceOrg(deviceSn, orgId);
        }
        
        return orgId;
    }

    // =====================================================
    // 业务数据关联查询
    // =====================================================
    
    /**
     * 获取用户最新健康数据
     * 性能目标: <3ms
     */
    public Map<String, Object> getUserLatestHealth(Long userId) {
        // 1. 尝试从缓存获取
        Map<String, Object> cachedHealth = cacheService.getUserLatestHealth(userId);
        if (!CollectionUtils.isEmpty(cachedHealth)) {
            return cachedHealth;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT heart_rate, pressure_high, pressure_low, blood_oxygen, 
                   temperature, step, calorie, timestamp
            FROM t_user_health_data 
            WHERE user_id = ? 
              AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
              AND is_deleted = 0
            ORDER BY timestamp DESC 
            LIMIT 1
            """;
        
        List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, userId);
        Map<String, Object> healthData = results.isEmpty() ? new HashMap<>() : results.get(0);
        
        // 3. 缓存结果
        if (!healthData.isEmpty()) {
            cacheService.cacheUserLatestHealth(userId, healthData);
        }
        
        return healthData;
    }
    
    /**
     * 获取用户活跃告警
     * 性能目标: <3ms
     */
    public Set<Long> getUserActiveAlerts(Long userId) {
        // 1. 尝试从缓存获取
        Set<Long> cachedAlerts = cacheService.getUserActiveAlerts(userId);
        if (!CollectionUtils.isEmpty(cachedAlerts)) {
            return cachedAlerts;
        }
        
        // 2. 查询数据库
        String sql = """
            SELECT id FROM t_alert_info
            WHERE user_id = ? 
              AND alert_status IN ('PENDING', 'IN_PROGRESS')
              AND create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """;
        
        List<Long> alertIds = jdbcTemplate.queryForList(sql, Long.class, userId);
        Set<Long> alerts = new HashSet<>(alertIds);
        
        // 3. 缓存结果
        cacheService.cacheUserActiveAlerts(userId, alerts);
        
        return alerts;
    }
    
    /**
     * 获取部门健康数据汇总
     * 性能目标: <5ms
     */
    public Map<String, Object> getOrgHealthSummary(Long orgId) {
        // 1. 尝试从缓存获取
        Map<String, Object> cachedSummary = cacheService.getOrgHealthSummary(orgId);
        if (!CollectionUtils.isEmpty(cachedSummary)) {
            return cachedSummary;
        }
        
        // 2. 基于闭包表查询部门健康数据汇总
        String sql = """
            SELECT COUNT(h.id) as total_records,
                   COUNT(DISTINCT h.user_id) as total_users,
                   AVG(h.heart_rate) as avg_heart_rate,
                   AVG(h.pressure_high) as avg_pressure_high,
                   AVG(h.pressure_low) as avg_pressure_low,
                   AVG(h.blood_oxygen) as avg_blood_oxygen,
                   SUM(h.step) as total_steps,
                   SUM(h.calorie) as total_calories
            FROM sys_org_closure c
            INNER JOIN sys_user_org uo ON c.descendant_id = uo.org_id
            INNER JOIN sys_user u ON uo.user_id = u.id
            INNER JOIN t_user_health_data h ON u.id = h.user_id
            WHERE c.ancestor_id = ? 
              AND uo.is_deleted = 0 
              AND u.is_deleted = 0 
              AND h.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
              AND h.is_deleted = 0
            """;
        
        List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, orgId);
        Map<String, Object> summary = results.isEmpty() ? new HashMap<>() : results.get(0);
        
        // 3. 缓存结果
        if (!summary.isEmpty()) {
            cacheService.cacheOrgHealthSummary(orgId, summary);
        }
        
        return summary;
    }

    // =====================================================
    // 批量查询优化
    // =====================================================
    
    /**
     * 批量获取用户设备关系
     * 性能目标: <10ms for 100 users
     */
    public Map<Long, Set<String>> batchGetUserDevices(Set<Long> userIds) {
        if (CollectionUtils.isEmpty(userIds)) {
            return new HashMap<>();
        }
        
        StopWatch stopWatch = new StopWatch("batchGetUserDevices");
        stopWatch.start("cache-batch-lookup");
        
        // 1. 批量从缓存获取
        Map<Long, Set<String>> result = cacheService.batchGetUserDevices(userIds);
        
        // 2. 找出缓存未命中的用户
        Set<Long> missingUsers = userIds.stream()
                .filter(userId -> !result.containsKey(userId))
                .collect(Collectors.toSet());
        
        stopWatch.stop();
        
        if (!missingUsers.isEmpty()) {
            stopWatch.start("db-batch-query");
            
            // 3. 批量查询数据库
            String inClause = missingUsers.stream()
                    .map(String::valueOf)
                    .collect(Collectors.joining(","));
            
            String sql = String.format("""
                SELECT du.user_id, GROUP_CONCAT(du.device_sn) as device_sns
                FROM t_device_user du
                INNER JOIN t_device_info d ON du.device_sn = d.serial_number
                WHERE du.user_id IN (%s) 
                  AND du.status = 'BIND' 
                  AND d.status = 'online'
                GROUP BY du.user_id
                """, inClause);
            
            List<Map<String, Object>> dbResults = jdbcTemplate.queryForList(sql);
            
            // 4. 处理查询结果并更新缓存
            for (Map<String, Object> row : dbResults) {
                Long userId = ((Number) row.get("user_id")).longValue();
                String deviceSnsStr = (String) row.get("device_sns");
                if (deviceSnsStr != null) {
                    Set<String> devices = Arrays.stream(deviceSnsStr.split(","))
                            .collect(Collectors.toSet());
                    result.put(userId, devices);
                    
                    // 异步更新缓存
                    CompletableFuture.runAsync(() -> 
                        cacheService.cacheUserDevices(userId, devices));
                }
            }
            
            stopWatch.stop();
        }
        
        log.debug("批量获取用户设备关系: users={}, cache_hits={}, db_queries={}, time={}ms",
            userIds.size(), userIds.size() - missingUsers.size(), missingUsers.size(), 
            stopWatch.getTotalTimeMillis());
        
        return result;
    }
    
    /**
     * 批量获取部门用户关系
     * 性能目标: <15ms for 50 orgs
     */
    public Map<Long, Set<Long>> batchGetOrgUsers(Set<Long> orgIds) {
        if (CollectionUtils.isEmpty(orgIds)) {
            return new HashMap<>();
        }
        
        // 1. 批量从缓存获取
        Map<Long, Set<Long>> result = cacheService.batchGetOrgUsers(orgIds);
        
        // 2. 找出缓存未命中的部门
        Set<Long> missingOrgs = orgIds.stream()
                .filter(orgId -> !result.containsKey(orgId))
                .collect(Collectors.toSet());
        
        if (!missingOrgs.isEmpty()) {
            // 3. 并行查询数据库
            missingOrgs.parallelStream().forEach(orgId -> {
                Set<Long> users = getOrgUsers(orgId); // 这个方法内部会处理缓存
                if (!users.isEmpty()) {
                    result.put(orgId, users);
                }
            });
        }
        
        return result;
    }

    // =====================================================
    // 复合查询场景
    // =====================================================
    
    /**
     * 获取用户完整关系信息（用户-部门-设备-健康数据）
     * 性能目标: <8ms
     */
    public Map<String, Object> getUserCompleteRelations(Long userId) {
        Map<String, Object> result = new HashMap<>();
        
        // 并行获取各种关系数据
        CompletableFuture<Set<Long>> orgsFuture = CompletableFuture
                .supplyAsync(() -> getUserOrgs(userId));
        
        CompletableFuture<Set<String>> devicesFuture = CompletableFuture
                .supplyAsync(() -> getUserDevices(userId));
        
        CompletableFuture<Map<String, Object>> healthFuture = CompletableFuture
                .supplyAsync(() -> getUserLatestHealth(userId));
        
        CompletableFuture<Set<Long>> alertsFuture = CompletableFuture
                .supplyAsync(() -> getUserActiveAlerts(userId));
        
        // 等待所有异步任务完成
        CompletableFuture.allOf(orgsFuture, devicesFuture, healthFuture, alertsFuture).join();
        
        try {
            result.put("orgs", orgsFuture.get());
            result.put("devices", devicesFuture.get());  
            result.put("latestHealth", healthFuture.get());
            result.put("activeAlerts", alertsFuture.get());
            result.put("timestamp", LocalDateTime.now().format(TIMESTAMP_FORMAT));
        } catch (Exception e) {
            log.error("获取用户完整关系信息失败: userId={}", userId, e);
        }
        
        return result;
    }
    
    /**
     * 获取部门完整关系信息（部门-用户-设备-健康汇总）
     * 性能目标: <10ms
     */
    public Map<String, Object> getOrgCompleteRelations(Long orgId) {
        Map<String, Object> result = new HashMap<>();
        
        // 并行获取各种关系数据
        CompletableFuture<Set<Long>> usersFuture = CompletableFuture
                .supplyAsync(() -> getOrgUsers(orgId));
        
        CompletableFuture<Set<String>> devicesFuture = CompletableFuture
                .supplyAsync(() -> getOrgDevices(orgId));
        
        CompletableFuture<Set<Long>> descendantsFuture = CompletableFuture
                .supplyAsync(() -> getOrgDescendants(orgId));
        
        CompletableFuture<Map<String, Object>> healthSummaryFuture = CompletableFuture
                .supplyAsync(() -> getOrgHealthSummary(orgId));
        
        // 等待所有异步任务完成
        CompletableFuture.allOf(usersFuture, devicesFuture, descendantsFuture, healthSummaryFuture).join();
        
        try {
            result.put("users", usersFuture.get());
            result.put("devices", devicesFuture.get());
            result.put("descendants", descendantsFuture.get());
            result.put("healthSummary", healthSummaryFuture.get());
            result.put("timestamp", LocalDateTime.now().format(TIMESTAMP_FORMAT));
        } catch (Exception e) {
            log.error("获取部门完整关系信息失败: orgId={}", orgId, e);
        }
        
        return result;
    }

    // =====================================================
    // 缓存管理工具方法
    // =====================================================
    
    /**
     * 刷新用户相关缓存
     */
    public void refreshUserCache(Long userId) {
        log.info("刷新用户相关缓存: userId={}", userId);
        
        // 清除旧缓存
        cacheService.evictUserCache(userId);
        
        // 预热新缓存
        CompletableFuture.runAsync(() -> {
            getUserOrgs(userId);
            getUserDevices(userId);
            getUserLatestHealth(userId);
            getUserActiveAlerts(userId);
        });
    }
    
    /**
     * 刷新部门相关缓存
     */
    public void refreshOrgCache(Long orgId) {
        log.info("刷新部门相关缓存: orgId={}", orgId);
        
        // 清除旧缓存
        cacheService.evictOrgCache(orgId);
        
        // 预热新缓存
        CompletableFuture.runAsync(() -> {
            getOrgUsers(orgId);
            getOrgDevices(orgId);
            getOrgDescendants(orgId);
            getOrgHealthSummary(orgId);
        });
    }
    
    /**
     * 刷新设备相关缓存
     */
    public void refreshDeviceCache(String deviceSn) {
        log.info("刷新设备相关缓存: deviceSn={}", deviceSn);
        
        // 清除旧缓存
        cacheService.evictDeviceCache(deviceSn);
        
        // 预热新缓存
        CompletableFuture.runAsync(() -> {
            getDeviceUser(deviceSn);
            getDeviceOrg(deviceSn);
        });
    }
}