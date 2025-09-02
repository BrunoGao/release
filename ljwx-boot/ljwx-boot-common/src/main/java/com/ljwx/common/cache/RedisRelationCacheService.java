package com.ljwx.common.cache;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;

import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * Redis关系缓存服务 - 高性能多维度关联查询
 * 基于闭包表和Redis实现毫秒级查询响应
 */
@Service
public class RedisRelationCacheService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    // =====================================================
    // 缓存KEY常量定义
    // =====================================================
    
    // 租户相关
    private static final String TENANT_USERS = "tenant:users:";        // 租户-用户映射
    private static final String TENANT_ORGS = "tenant:orgs:";          // 租户-部门映射
    private static final String TENANT_DEVICES = "tenant:devices:";    // 租户-设备映射
    
    // 用户关联
    private static final String USER_ORGS = "user:orgs:";              // 用户-部门映射
    private static final String USER_DEVICES = "user:devices:";        // 用户-设备映射
    private static final String USER_POSITIONS = "user:positions:";    // 用户-岗位映射
    
    // 部门关联
    private static final String ORG_USERS = "org:users:";              // 部门-用户映射
    private static final String ORG_DEVICES = "org:devices:";          // 部门-设备映射
    private static final String ORG_DESCENDANTS = "org:descendants:";  // 部门-后代映射
    private static final String ORG_ANCESTORS = "org:ancestors:";      // 部门-祖先映射
    
    // 设备关联
    private static final String DEVICE_USER = "device:user:";          // 设备-用户映射
    private static final String DEVICE_ORG = "device:org:";            // 设备-部门映射
    
    // 业务数据关联
    private static final String USER_HEALTH_LATEST = "user:health:latest:";     // 用户最新健康数据
    private static final String ORG_HEALTH_SUMMARY = "org:health:summary:";     // 部门健康数据汇总
    private static final String USER_ALERTS_ACTIVE = "user:alerts:active:";     // 用户活跃告警
    private static final String ORG_ALERTS_SUMMARY = "org:alerts:summary:";     // 部门告警汇总
    
    // 缓存过期时间（秒）
    private static final long CACHE_EXPIRE_SHORT = 300;    // 5分钟 - 频繁变更数据
    private static final long CACHE_EXPIRE_MEDIUM = 1800;  // 30分钟 - 一般关系数据
    private static final long CACHE_EXPIRE_LONG = 3600;    // 1小时 - 相对稳定数据

    // =====================================================
    // 租户级别查询 - 顶层缓存
    // =====================================================
    
    /**
     * 获取租户下所有用户ID列表
     */
    public Set<Long> getTenantUsers(Long customerId) {
        String key = TENANT_USERS + customerId;
        Set<Object> userIds = redisTemplate.opsForSet().members(key);
        return convertToLongSet(userIds);
    }
    
    /**
     * 缓存租户用户关系
     */
    public void cacheTenantUsers(Long customerId, Set<Long> userIds) {
        String key = TENANT_USERS + customerId;
        if (!CollectionUtils.isEmpty(userIds)) {
            redisTemplate.opsForSet().add(key, userIds.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_LONG, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取租户下所有部门ID列表
     */
    public Set<Long> getTenantOrgs(Long customerId) {
        String key = TENANT_ORGS + customerId;
        Set<Object> orgIds = redisTemplate.opsForSet().members(key);
        return convertToLongSet(orgIds);
    }
    
    /**
     * 缓存租户部门关系
     */
    public void cacheTenantOrgs(Long customerId, Set<Long> orgIds) {
        String key = TENANT_ORGS + customerId;
        if (!CollectionUtils.isEmpty(orgIds)) {
            redisTemplate.opsForSet().add(key, orgIds.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_LONG, TimeUnit.SECONDS);
        }
    }

    // =====================================================
    // 用户-部门关联查询 (基于闭包表优化)
    // =====================================================
    
    /**
     * 获取用户所属部门列表（包含层级关系）
     */
    public Set<Long> getUserOrgs(Long userId) {
        String key = USER_ORGS + userId;
        Set<Object> orgIds = redisTemplate.opsForSet().members(key);
        return convertToLongSet(orgIds);
    }
    
    /**
     * 缓存用户部门关系
     */
    public void cacheUserOrgs(Long userId, Set<Long> orgIds) {
        String key = USER_ORGS + userId;
        redisTemplate.delete(key); // 清除旧数据
        if (!CollectionUtils.isEmpty(orgIds)) {
            redisTemplate.opsForSet().add(key, orgIds.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取部门下所有用户（包含子部门用户）
     */
    public Set<Long> getOrgUsers(Long orgId) {
        String key = ORG_USERS + orgId;
        Set<Object> userIds = redisTemplate.opsForSet().members(key);
        return convertToLongSet(userIds);
    }
    
    /**
     * 缓存部门用户关系（包含子部门）
     */
    public void cacheOrgUsers(Long orgId, Set<Long> userIds) {
        String key = ORG_USERS + orgId;
        redisTemplate.delete(key);
        if (!CollectionUtils.isEmpty(userIds)) {
            redisTemplate.opsForSet().add(key, userIds.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取部门所有后代部门ID（基于闭包表）
     */
    public Set<Long> getOrgDescendants(Long orgId) {
        String key = ORG_DESCENDANTS + orgId;
        Set<Object> descendants = redisTemplate.opsForSet().members(key);
        return convertToLongSet(descendants);
    }
    
    /**
     * 缓存部门后代关系
     */
    public void cacheOrgDescendants(Long orgId, Set<Long> descendants) {
        String key = ORG_DESCENDANTS + orgId;
        redisTemplate.delete(key);
        if (!CollectionUtils.isEmpty(descendants)) {
            redisTemplate.opsForSet().add(key, descendants.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_LONG, TimeUnit.SECONDS); // 层级关系相对稳定
        }
    }

    // =====================================================
    // 用户-设备关联查询
    // =====================================================
    
    /**
     * 获取用户关联的设备列表
     */
    public Set<String> getUserDevices(Long userId) {
        String key = USER_DEVICES + userId;
        Set<Object> deviceSns = redisTemplate.opsForSet().members(key);
        return convertToStringSet(deviceSns);
    }
    
    /**
     * 缓存用户设备关系
     */
    public void cacheUserDevices(Long userId, Set<String> deviceSns) {
        String key = USER_DEVICES + userId;
        redisTemplate.delete(key);
        if (!CollectionUtils.isEmpty(deviceSns)) {
            redisTemplate.opsForSet().add(key, deviceSns.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取设备关联的用户
     */
    public Long getDeviceUser(String deviceSn) {
        String key = DEVICE_USER + deviceSn;
        Object userId = redisTemplate.opsForValue().get(key);
        return userId != null ? Long.valueOf(userId.toString()) : null;
    }
    
    /**
     * 缓存设备用户关系
     */
    public void cacheDeviceUser(String deviceSn, Long userId) {
        String key = DEVICE_USER + deviceSn;
        redisTemplate.opsForValue().set(key, userId, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
    }

    // =====================================================
    // 部门-设备关联查询  
    // =====================================================
    
    /**
     * 获取部门下所有设备（包含子部门设备）
     */
    public Set<String> getOrgDevices(Long orgId) {
        String key = ORG_DEVICES + orgId;
        Set<Object> deviceSns = redisTemplate.opsForSet().members(key);
        return convertToStringSet(deviceSns);
    }
    
    /**
     * 缓存部门设备关系
     */
    public void cacheOrgDevices(Long orgId, Set<String> deviceSns) {
        String key = ORG_DEVICES + orgId;
        redisTemplate.delete(key);
        if (!CollectionUtils.isEmpty(deviceSns)) {
            redisTemplate.opsForSet().add(key, deviceSns.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取设备所属部门
     */
    public Long getDeviceOrg(String deviceSn) {
        String key = DEVICE_ORG + deviceSn;
        Object orgId = redisTemplate.opsForValue().get(key);
        return orgId != null ? Long.valueOf(orgId.toString()) : null;
    }
    
    /**
     * 缓存设备部门关系
     */
    public void cacheDeviceOrg(String deviceSn, Long orgId) {
        String key = DEVICE_ORG + deviceSn;
        redisTemplate.opsForValue().set(key, orgId, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
    }

    // =====================================================
    // 业务数据缓存查询
    // =====================================================
    
    /**
     * 获取用户最新健康数据
     */
    public Map<String, Object> getUserLatestHealth(Long userId) {
        String key = USER_HEALTH_LATEST + userId;
        Map<Object, Object> healthData = redisTemplate.opsForHash().entries(key);
        return convertToStringObjectMap(healthData);
    }
    
    /**
     * 缓存用户最新健康数据
     */
    public void cacheUserLatestHealth(Long userId, Map<String, Object> healthData) {
        String key = USER_HEALTH_LATEST + userId;
        if (!CollectionUtils.isEmpty(healthData)) {
            redisTemplate.opsForHash().putAll(key, healthData);
            redisTemplate.expire(key, CACHE_EXPIRE_SHORT, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取用户活跃告警列表
     */
    public Set<Long> getUserActiveAlerts(Long userId) {
        String key = USER_ALERTS_ACTIVE + userId;
        Set<Object> alertIds = redisTemplate.opsForSet().members(key);
        return convertToLongSet(alertIds);
    }
    
    /**
     * 缓存用户活跃告警
     */
    public void cacheUserActiveAlerts(Long userId, Set<Long> alertIds) {
        String key = USER_ALERTS_ACTIVE + userId;
        redisTemplate.delete(key);
        if (!CollectionUtils.isEmpty(alertIds)) {
            redisTemplate.opsForSet().add(key, alertIds.toArray());
            redisTemplate.expire(key, CACHE_EXPIRE_SHORT, TimeUnit.SECONDS);
        }
    }
    
    /**
     * 获取部门健康数据汇总
     */
    public Map<String, Object> getOrgHealthSummary(Long orgId) {
        String key = ORG_HEALTH_SUMMARY + orgId;
        Map<Object, Object> summary = redisTemplate.opsForHash().entries(key);
        return convertToStringObjectMap(summary);
    }
    
    /**
     * 缓存部门健康数据汇总
     */
    public void cacheOrgHealthSummary(Long orgId, Map<String, Object> summary) {
        String key = ORG_HEALTH_SUMMARY + orgId;
        if (!CollectionUtils.isEmpty(summary)) {
            redisTemplate.opsForHash().putAll(key, summary);
            redisTemplate.expire(key, CACHE_EXPIRE_MEDIUM, TimeUnit.SECONDS);
        }
    }

    // =====================================================
    // 批量操作优化
    // =====================================================
    
    /**
     * 批量获取用户设备关系
     */
    public Map<Long, Set<String>> batchGetUserDevices(Set<Long> userIds) {
        if (CollectionUtils.isEmpty(userIds)) {
            return new HashMap<>();
        }
        
        Map<Long, Set<String>> result = new HashMap<>();
        
        // 逐个查询，因为Redis Set操作不支持批量获取members
        for (Long userId : userIds) {
            Set<String> devices = getUserDevices(userId);
            if (!devices.isEmpty()) {
                result.put(userId, devices);
            }
        }
        
        return result;
    }
    
    /**
     * 批量获取部门用户关系
     */
    public Map<Long, Set<Long>> batchGetOrgUsers(Set<Long> orgIds) {
        if (CollectionUtils.isEmpty(orgIds)) {
            return new HashMap<>();
        }
        
        Map<Long, Set<Long>> result = new HashMap<>();
        
        for (Long orgId : orgIds) {
            Set<Long> users = getOrgUsers(orgId);
            if (!CollectionUtils.isEmpty(users)) {
                result.put(orgId, users);
            }
        }
        
        return result;
    }

    // =====================================================
    // 缓存失效和清理
    // =====================================================
    
    /**
     * 清除用户相关缓存
     */
    public void evictUserCache(Long userId) {
        Set<String> keys = redisTemplate.keys("*:*:" + userId + "*");
        if (!CollectionUtils.isEmpty(keys)) {
            redisTemplate.delete(keys);
        }
    }
    
    /**
     * 清除部门相关缓存
     */
    public void evictOrgCache(Long orgId) {
        Set<String> keys = redisTemplate.keys("*:*:" + orgId + "*");
        if (!CollectionUtils.isEmpty(keys)) {
            redisTemplate.delete(keys);
        }
    }
    
    /**
     * 清除设备相关缓存
     */
    public void evictDeviceCache(String deviceSn) {
        Set<String> keys = redisTemplate.keys("*:*:" + deviceSn + "*");
        if (!CollectionUtils.isEmpty(keys)) {
            redisTemplate.delete(keys);
        }
    }
    
    /**
     * 清除租户相关缓存
     */
    public void evictTenantCache(Long customerId) {
        Set<String> keys = redisTemplate.keys("tenant:*:" + customerId + "*");
        if (!CollectionUtils.isEmpty(keys)) {
            redisTemplate.delete(keys);
        }
    }

    // =====================================================
    // 工具方法
    // =====================================================
    
    private Set<Long> convertToLongSet(Set<Object> objects) {
        if (CollectionUtils.isEmpty(objects)) {
            return new HashSet<>();
        }
        return objects.stream()
                .map(obj -> Long.valueOf(obj.toString()))
                .collect(Collectors.toSet());
    }
    
    private Set<String> convertToStringSet(Set<Object> objects) {
        if (CollectionUtils.isEmpty(objects)) {
            return new HashSet<>();
        }
        return objects.stream()
                .map(Object::toString)
                .collect(Collectors.toSet());
    }
    
    private Map<String, Object> convertToStringObjectMap(Map<Object, Object> objectMap) {
        if (CollectionUtils.isEmpty(objectMap)) {
            return new HashMap<>();
        }
        return objectMap.entrySet().stream()
                .collect(Collectors.toMap(
                    entry -> entry.getKey().toString(),
                    Map.Entry::getValue
                ));
    }
    
    /**
     * 检查缓存是否存在
     */
    public boolean cacheExists(String keyPrefix, Object id) {
        String key = keyPrefix + id;
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }
    
    /**
     * 获取缓存剩余过期时间
     */
    public long getCacheExpire(String keyPrefix, Object id) {
        String key = keyPrefix + id;
        return redisTemplate.getExpire(key, TimeUnit.SECONDS);
    }
}