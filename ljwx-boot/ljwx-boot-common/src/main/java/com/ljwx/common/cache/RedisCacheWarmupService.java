package com.ljwx.common.cache;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;

import jakarta.annotation.PostConstruct;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.stream.Collectors;

/**
 * Redis缓存预热和更新服务
 * 系统启动时自动预热核心关系数据，定时更新热点数据
 */
@Slf4j
@Service
public class RedisCacheWarmupService implements ApplicationRunner, ICacheWarmupService {

    @Autowired
    private RedisRelationCacheService relationCacheService;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    // 分批处理大小
    private static final int BATCH_SIZE = 1000;
    
    // 预热状态追踪
    private boolean warmupCompleted = false;
    
    /**
     * 应用启动后自动执行缓存预热
     */
    @Override
    public void run(ApplicationArguments args) {
        log.info("开始执行Redis缓存预热...");
        long startTime = System.currentTimeMillis();
        
        try {
            // 并行执行预热任务
            CompletableFuture<Void> tenantWarmup = warmupTenantRelations();
            CompletableFuture<Void> userOrgWarmup = warmupUserOrgRelations(); 
            CompletableFuture<Void> deviceWarmup = warmupDeviceRelations();
            CompletableFuture<Void> orgHierarchyWarmup = warmupOrgHierarchy();
            
            // 等待所有预热任务完成
            CompletableFuture.allOf(tenantWarmup, userOrgWarmup, deviceWarmup, orgHierarchyWarmup).join();
            
            warmupCompleted = true;
            long duration = System.currentTimeMillis() - startTime;
            log.info("Redis缓存预热完成，耗时: {}ms", duration);
            
        } catch (Exception e) {
            log.error("Redis缓存预热失败", e);
        }
    }
    
    /**
     * 预热租户关系数据
     */
    @Override
    @Async
    public CompletableFuture<Void> warmupTenantRelations() {
        log.info("开始预热租户关系数据...");
        
        try {
            // 1. 预热租户-用户关系
            String userSql = """
                SELECT customer_id, GROUP_CONCAT(id) as user_ids
                FROM sys_user 
                WHERE is_deleted = 0 AND status = '1' 
                GROUP BY customer_id
                """;
            
            List<Map<String, Object>> tenantUsers = jdbcTemplate.queryForList(userSql);
            for (Map<String, Object> row : tenantUsers) {
                Long customerId = ((Number) row.get("customer_id")).longValue();
                String userIdsStr = (String) row.get("user_ids");
                if (userIdsStr != null) {
                    Set<Long> userIds = Arrays.stream(userIdsStr.split(","))
                            .map(Long::valueOf)
                            .collect(Collectors.toSet());
                    relationCacheService.cacheTenantUsers(customerId, userIds);
                }
            }
            
            // 2. 预热租户-部门关系
            String orgSql = """
                SELECT customer_id, GROUP_CONCAT(id) as org_ids
                FROM sys_org_units 
                WHERE is_deleted = 0 AND status = '1'
                GROUP BY customer_id
                """;
            
            List<Map<String, Object>> tenantOrgs = jdbcTemplate.queryForList(orgSql);
            for (Map<String, Object> row : tenantOrgs) {
                Long customerId = ((Number) row.get("customer_id")).longValue();
                String orgIdsStr = (String) row.get("org_ids");
                if (orgIdsStr != null) {
                    Set<Long> orgIds = Arrays.stream(orgIdsStr.split(","))
                            .map(Long::valueOf)
                            .collect(Collectors.toSet());
                    relationCacheService.cacheTenantOrgs(customerId, orgIds);
                }
            }
            
            log.info("租户关系数据预热完成: {} 个租户", tenantUsers.size());
            
        } catch (Exception e) {
            log.error("租户关系数据预热失败", e);
        }
        
        return CompletableFuture.completedFuture(null);
    }
    
    /**
     * 预热用户-部门关系（基于闭包表）
     */
    @Override
    @Async
    public CompletableFuture<Void> warmupUserOrgRelations() {
        log.info("开始预热用户-部门关系数据...");
        
        try {
            // 1. 预热用户-部门关系
            String userOrgSql = """
                SELECT uo.user_id, GROUP_CONCAT(uo.org_id) as org_ids
                FROM sys_user_org uo
                INNER JOIN sys_user u ON uo.user_id = u.id
                WHERE uo.is_deleted = 0 AND u.is_deleted = 0
                GROUP BY uo.user_id
                """;
            
            List<Map<String, Object>> userOrgs = jdbcTemplate.queryForList(userOrgSql);
            for (Map<String, Object> row : userOrgs) {
                Long userId = ((Number) row.get("user_id")).longValue();
                String orgIdsStr = (String) row.get("org_ids");
                if (orgIdsStr != null) {
                    Set<Long> orgIds = Arrays.stream(orgIdsStr.split(","))
                            .map(Long::valueOf)
                            .collect(Collectors.toSet());
                    relationCacheService.cacheUserOrgs(userId, orgIds);
                }
            }
            
            // 2. 预热部门-用户关系（包含子部门用户）
            String orgUserSql = """
                SELECT o.id as org_id,
                       GROUP_CONCAT(DISTINCT u.id) as direct_user_ids
                FROM sys_org_units o
                LEFT JOIN sys_user_org uo ON o.id = uo.org_id AND uo.is_deleted = 0
                LEFT JOIN sys_user u ON uo.user_id = u.id AND u.is_deleted = 0
                WHERE o.is_deleted = 0 AND o.status = '1'
                GROUP BY o.id
                """;
            
            List<Map<String, Object>> orgUsers = jdbcTemplate.queryForList(orgUserSql);
            for (Map<String, Object> row : orgUsers) {
                Long orgId = ((Number) row.get("org_id")).longValue();
                String userIdsStr = (String) row.get("direct_user_ids");
                
                // 获取包含子部门的所有用户
                Set<Long> allUserIds = getAllOrgUsers(orgId);
                if (!allUserIds.isEmpty()) {
                    relationCacheService.cacheOrgUsers(orgId, allUserIds);
                }
            }
            
            log.info("用户-部门关系数据预热完成: {} 个用户, {} 个部门", userOrgs.size(), orgUsers.size());
            
        } catch (Exception e) {
            log.error("用户-部门关系数据预热失败", e);
        }
        
        return CompletableFuture.completedFuture(null);
    }
    
    /**
     * 预热设备关系数据
     */
    @Override
    @Async
    public CompletableFuture<Void> warmupDeviceRelations() {
        log.info("开始预热设备关系数据...");
        
        try {
            // 1. 预热用户-设备关系 (解决字符集冲突问题)
            String userDeviceSql = """
                SELECT du.user_id, GROUP_CONCAT(du.device_sn) as device_sns
                FROM t_device_user du
                INNER JOIN sys_user u ON du.user_id = u.id
                INNER JOIN t_device_info d ON du.device_sn COLLATE utf8mb4_general_ci = d.serial_number
                WHERE u.is_deleted = 0 AND d.status = 'online'
                GROUP BY du.user_id
                """;
            
            List<Map<String, Object>> userDevices = jdbcTemplate.queryForList(userDeviceSql);
            for (Map<String, Object> row : userDevices) {
                Long userId = ((Number) row.get("user_id")).longValue();
                String deviceSnsStr = (String) row.get("device_sns");
                if (deviceSnsStr != null) {
                    Set<String> deviceSns = Arrays.stream(deviceSnsStr.split(","))
                            .collect(Collectors.toSet());
                    relationCacheService.cacheUserDevices(userId, deviceSns);
                }
            }
            
            // 2. 预热设备-用户关系 (解决字符集冲突问题)
            String deviceUserSql = """
                SELECT du.device_sn, du.user_id
                FROM t_device_user du
                INNER JOIN sys_user u ON du.user_id = u.id
                INNER JOIN t_device_info d ON du.device_sn COLLATE utf8mb4_general_ci = d.serial_number
                WHERE u.is_deleted = 0 AND d.status = 'online'
                """;
            
            List<Map<String, Object>> deviceUsers = jdbcTemplate.queryForList(deviceUserSql);
            for (Map<String, Object> row : deviceUsers) {
                String deviceSn = (String) row.get("device_sn");
                Long userId = ((Number) row.get("user_id")).longValue();
                relationCacheService.cacheDeviceUser(deviceSn, userId);
            }
            
            // 3. 预热设备-部门关系 (解决字符集冲突问题)
            String deviceOrgSql = """
                SELECT d.serial_number, uo.org_id
                FROM t_device_info d
                INNER JOIN t_device_user du ON d.serial_number = du.device_sn COLLATE utf8mb4_general_ci
                INNER JOIN sys_user u ON du.user_id = u.id
                INNER JOIN sys_user_org uo ON u.id = uo.user_id
                WHERE d.status = 'online' AND u.is_deleted = 0 AND uo.is_deleted = 0
                """;
            
            List<Map<String, Object>> deviceOrgs = jdbcTemplate.queryForList(deviceOrgSql);
            for (Map<String, Object> row : deviceOrgs) {
                String deviceSn = (String) row.get("serial_number");
                Long orgId = ((Number) row.get("org_id")).longValue();
                relationCacheService.cacheDeviceOrg(deviceSn, orgId);
            }
            
            // 4. 预热部门-设备关系（包含子部门设备）
            preloadOrgDevices();
            
            log.info("设备关系数据预热完成: {} 个用户设备, {} 个设备用户", userDevices.size(), deviceUsers.size());
            
        } catch (Exception e) {
            log.error("设备关系数据预热失败", e);
        }
        
        return CompletableFuture.completedFuture(null);
    }
    
    /**
     * 预热组织层级结构（基于闭包表）
     */
    @Override
    @Async
    public CompletableFuture<Void> warmupOrgHierarchy() {
        log.info("开始预热组织层级结构数据...");
        
        try {
            // 预热部门后代关系
            String descendantsSql = """
                SELECT ancestor_id, GROUP_CONCAT(descendant_id) as descendant_ids
                FROM sys_org_closure
                WHERE depth > 0
                GROUP BY ancestor_id
                """;
            
            List<Map<String, Object>> orgDescendants = jdbcTemplate.queryForList(descendantsSql);
            for (Map<String, Object> row : orgDescendants) {
                Long ancestorId = ((Number) row.get("ancestor_id")).longValue();
                String descendantIdsStr = (String) row.get("descendant_ids");
                if (descendantIdsStr != null) {
                    Set<Long> descendantIds = Arrays.stream(descendantIdsStr.split(","))
                            .map(Long::valueOf)
                            .collect(Collectors.toSet());
                    relationCacheService.cacheOrgDescendants(ancestorId, descendantIds);
                }
            }
            
            log.info("组织层级结构预热完成: {} 个层级关系", orgDescendants.size());
            
        } catch (Exception e) {
            log.error("组织层级结构预热失败", e);
        }
        
        return CompletableFuture.completedFuture(null);
    }
    
    /**
     * 定时更新热点数据缓存 - 每5分钟执行
     */
    @Override
    @Scheduled(fixedRate = 300000)
    public void refreshHotDataCache() {
        if (!warmupCompleted) {
            return;
        }
        
        log.debug("开始刷新热点数据缓存...");
        
        try {
            // 1. 刷新用户最新健康数据
            refreshUserLatestHealthData();
            
            // 2. 刷新用户活跃告警数据
            refreshUserActiveAlerts();
            
            // 3. 刷新部门健康数据汇总
            refreshOrgHealthSummary();
            
        } catch (Exception e) {
            log.error("热点数据缓存刷新失败", e);
        }
    }
    
    /**
     * 刷新用户最新健康数据
     */
    private void refreshUserLatestHealthData() {
        String sql = """
            SELECT h.user_id,
                   h.heart_rate,
                   h.pressure_high,
                   h.pressure_low,
                   h.blood_oxygen,
                   h.temperature,
                   h.timestamp
            FROM t_user_health_data h
            INNER JOIN (
                SELECT user_id, MAX(timestamp) as latest_time
                FROM t_user_health_data
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                  AND is_deleted = 0
                GROUP BY user_id
            ) latest ON h.user_id = latest.user_id AND h.timestamp = latest.latest_time
            WHERE h.is_deleted = 0
            """;
        
        List<Map<String, Object>> latestHealthData = jdbcTemplate.queryForList(sql);
        for (Map<String, Object> row : latestHealthData) {
            Long userId = ((Number) row.get("user_id")).longValue();
            Map<String, Object> healthData = new HashMap<>(row);
            healthData.remove("user_id");
            relationCacheService.cacheUserLatestHealth(userId, healthData);
        }
        
        log.debug("刷新用户最新健康数据: {} 条", latestHealthData.size());
    }
    
    /**
     * 刷新用户活跃告警数据
     */
    private void refreshUserActiveAlerts() {
        String sql = """
            SELECT user_id, GROUP_CONCAT(id) as alert_ids
            FROM t_alert_info
            WHERE alert_status IN ('PENDING', 'IN_PROGRESS')
              AND create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY user_id
            """;
        
        List<Map<String, Object>> activeAlerts = jdbcTemplate.queryForList(sql);
        for (Map<String, Object> row : activeAlerts) {
            Long userId = ((Number) row.get("user_id")).longValue();
            String alertIdsStr = (String) row.get("alert_ids");
            if (alertIdsStr != null) {
                Set<Long> alertIds = Arrays.stream(alertIdsStr.split(","))
                        .map(Long::valueOf)
                        .collect(Collectors.toSet());
                relationCacheService.cacheUserActiveAlerts(userId, alertIds);
            }
        }
        
        log.debug("刷新用户活跃告警数据: {} 个用户", activeAlerts.size());
    }
    
    /**
     * 刷新部门健康数据汇总
     */
    private void refreshOrgHealthSummary() {
        String sql = """
            SELECT uo.org_id,
                   COUNT(h.id) as total_records,
                   AVG(h.heart_rate) as avg_heart_rate,
                   AVG(h.pressure_high) as avg_pressure_high,
                   AVG(h.pressure_low) as avg_pressure_low,
                   AVG(h.blood_oxygen) as avg_blood_oxygen
            FROM sys_user_org uo
            INNER JOIN sys_user u ON uo.user_id = u.id
            LEFT JOIN t_user_health_data h ON u.id = h.user_id 
                AND h.timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND h.is_deleted = 0
            WHERE uo.is_deleted = 0 AND u.is_deleted = 0
            GROUP BY uo.org_id
            HAVING total_records > 0
            """;
        
        List<Map<String, Object>> orgSummaries = jdbcTemplate.queryForList(sql);
        for (Map<String, Object> row : orgSummaries) {
            Long orgId = ((Number) row.get("org_id")).longValue();
            Map<String, Object> summary = new HashMap<>(row);
            summary.remove("org_id");
            relationCacheService.cacheOrgHealthSummary(orgId, summary);
        }
        
        log.debug("刷新部门健康数据汇总: {} 个部门", orgSummaries.size());
    }
    
    /**
     * 获取部门及其子部门的所有用户
     */
    private Set<Long> getAllOrgUsers(Long orgId) {
        // 使用闭包表获取所有后代部门
        String sql = """
            SELECT DISTINCT u.id
            FROM sys_org_closure c
            INNER JOIN sys_user_org uo ON c.descendant_id = uo.org_id
            INNER JOIN sys_user u ON uo.user_id = u.id
            WHERE c.ancestor_id = ? AND uo.is_deleted = 0 AND u.is_deleted = 0
            """;
        
        List<Long> userIds = jdbcTemplate.queryForList(sql, Long.class, orgId);
        return new HashSet<>(userIds);
    }
    
    /**
     * 预加载部门设备关系
     */
    private void preloadOrgDevices() {
        // 获取所有部门ID
        List<Long> orgIds = jdbcTemplate.queryForList(
            "SELECT id FROM sys_org_units WHERE is_deleted = 0", Long.class);
        
        for (Long orgId : orgIds) {
            // 获取部门及其子部门的所有设备 (解决字符集冲突问题)
            String sql = """
                SELECT DISTINCT d.serial_number
                FROM sys_org_closure c
                INNER JOIN sys_user_org uo ON c.descendant_id = uo.org_id
                INNER JOIN sys_user u ON uo.user_id = u.id
                INNER JOIN t_device_user du ON u.id = du.user_id
                INNER JOIN t_device_info d ON du.device_sn COLLATE utf8mb4_general_ci = d.serial_number
                WHERE c.ancestor_id = ? 
                  AND uo.is_deleted = 0 
                  AND u.is_deleted = 0 
                  AND d.status = 'online'
                """;
            
            List<String> deviceSns = jdbcTemplate.queryForList(sql, String.class, orgId);
            if (!deviceSns.isEmpty()) {
                relationCacheService.cacheOrgDevices(orgId, new HashSet<>(deviceSns));
            }
        }
    }
    
    /**
     * 手动触发缓存预热
     */
    @Override
    public void manualWarmup() {
        log.info("手动触发缓存预热...");
        warmupCompleted = false;
        run(null);
    }
    
    /**
     * 获取预热状态
     */
    @Override
    public boolean isWarmupCompleted() {
        return warmupCompleted;
    }
}