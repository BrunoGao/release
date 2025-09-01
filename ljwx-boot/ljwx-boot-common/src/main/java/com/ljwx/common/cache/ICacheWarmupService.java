package com.ljwx.common.cache;

import java.util.concurrent.CompletableFuture;

/**
 * 缓存预热服务接口
 */
public interface ICacheWarmupService {
    
    /**
     * 手动触发缓存预热
     */
    void manualWarmup();
    
    /**
     * 获取预热状态
     */
    boolean isWarmupCompleted();
    
    /**
     * 定时刷新热点数据缓存
     */
    void refreshHotDataCache();
    
    /**
     * 预热租户关系数据
     */
    CompletableFuture<Void> warmupTenantRelations();
    
    /**
     * 预热用户-部门关系
     */
    CompletableFuture<Void> warmupUserOrgRelations();
    
    /**
     * 预热设备关系数据
     */
    CompletableFuture<Void> warmupDeviceRelations();
    
    /**
     * 预热组织层级结构
     */
    CompletableFuture<Void> warmupOrgHierarchy();
}