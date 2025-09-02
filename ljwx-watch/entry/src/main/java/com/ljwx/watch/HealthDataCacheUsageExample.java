package com.ljwx.watch;

import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import java.util.List;

/**
 * HealthDataCache 使用示例
 * 演示如何使用扩展后的三路缓存系统
 */
public class HealthDataCacheUsageExample {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-usage");
    
    public static void demonstrateUsage() {
        HealthDataCache cache = HealthDataCache.getInstance();
        
        // ==================== 基本使用 ====================
        
        // 1. 添加不同类型的数据到缓存
        HiLog.info(LABEL_LOG, "=== 添加数据到缓存 ===");
        
        // 健康数据 (向后兼容的方式)
        cache.addToCache("{\"heartRate\": 75, \"timestamp\": \"2025-08-22T10:00:00Z\"}");
        
        // 设备信息数据
        cache.addDeviceInfoToCache("{\"deviceId\": \"LJWX001\", \"batteryLevel\": 85, \"timestamp\": \"2025-08-22T10:00:00Z\"}");
        
        // 通用事件数据  
        cache.addCommonEventToCache("{\"eventType\": \"BUTTON_PRESS\", \"timestamp\": \"2025-08-22T10:00:00Z\"}");
        
        // 或者使用通用接口
        cache.addToCache(HealthDataCache.DataType.HEALTH_DATA, "{\"bloodOxygen\": 98, \"timestamp\": \"2025-08-22T10:01:00Z\"}");
        cache.addToCache(HealthDataCache.DataType.DEVICE_INFO, "{\"temperature\": 36.5, \"timestamp\": \"2025-08-22T10:01:00Z\"}");
        cache.addToCache(HealthDataCache.DataType.COMMON_EVENT, "{\"eventType\": \"ALARM\", \"timestamp\": \"2025-08-22T10:01:00Z\"}");
        
        // ==================== 查询缓存状态 ====================
        
        HiLog.info(LABEL_LOG, "=== 查询缓存状态 ===");
        
        // 打印缓存状态摘要
        HiLog.info(LABEL_LOG, cache.getCacheStatusSummary());
        
        // 详细打印每种缓存的状态
        cache.logCacheStatus();
        
        // 检查特定类型的缓存
        HiLog.info(LABEL_LOG, "健康数据缓存大小: " + cache.getCacheSize(HealthDataCache.DataType.HEALTH_DATA));
        HiLog.info(LABEL_LOG, "设备信息缓存大小: " + cache.getCacheSize(HealthDataCache.DataType.DEVICE_INFO));
        HiLog.info(LABEL_LOG, "通用事件缓存大小: " + cache.getCacheSize(HealthDataCache.DataType.COMMON_EVENT));
        
        // ==================== 获取缓存数据 ====================
        
        HiLog.info(LABEL_LOG, "=== 获取缓存数据 ===");
        
        // 获取健康数据缓存 (向后兼容)
        List<String> healthData = cache.getAllCachedData();
        HiLog.info(LABEL_LOG, "健康数据缓存: " + healthData.size() + " 条");
        
        // 获取设备信息缓存
        List<String> deviceInfo = cache.getDeviceInfoCache();
        HiLog.info(LABEL_LOG, "设备信息缓存: " + deviceInfo.size() + " 条");
        for (String data : deviceInfo) {
            HiLog.info(LABEL_LOG, "设备信息: " + data);
        }
        
        // 获取通用事件缓存
        List<String> commonEvents = cache.getCommonEventCache();
        HiLog.info(LABEL_LOG, "通用事件缓存: " + commonEvents.size() + " 条");
        for (String event : commonEvents) {
            HiLog.info(LABEL_LOG, "通用事件: " + event);
        }
        
        // ==================== 模拟网络恢复后上传 ====================
        
        HiLog.info(LABEL_LOG, "=== 模拟网络恢复后批量上传 ===");
        
        // 模拟上传健康数据
        List<String> healthDataToUpload = cache.getAllCachedData(HealthDataCache.DataType.HEALTH_DATA);
        if (!healthDataToUpload.isEmpty()) {
            HiLog.info(LABEL_LOG, "准备上传 " + healthDataToUpload.size() + " 条健康数据");
            // 这里调用实际的上传接口
            // uploadHealthData(healthDataToUpload);
            // 上传成功后清空缓存
            cache.clearCache(HealthDataCache.DataType.HEALTH_DATA);
        }
        
        // 模拟上传设备信息
        List<String> deviceInfoToUpload = cache.getDeviceInfoCache();
        if (!deviceInfoToUpload.isEmpty()) {
            HiLog.info(LABEL_LOG, "准备上传 " + deviceInfoToUpload.size() + " 条设备信息");
            // uploadDeviceInfo(deviceInfoToUpload);
            cache.clearDeviceInfoCache();
        }
        
        // 模拟上传通用事件
        List<String> eventsToUpload = cache.getCommonEventCache();
        if (!eventsToUpload.isEmpty()) {
            HiLog.info(LABEL_LOG, "准备上传 " + eventsToUpload.size() + " 条通用事件");
            // uploadCommonEvents(eventsToUpload);
            cache.clearCommonEventCache();
        }
        
        // ==================== 缓存管理 ====================
        
        HiLog.info(LABEL_LOG, "=== 缓存管理操作 ===");
        
        // 检查所有缓存是否都为空
        if (cache.areAllCachesEmpty()) {
            HiLog.info(LABEL_LOG, "所有缓存都已清空");
        }
        
        // 最终状态检查
        cache.logCacheStatus();
    }
    
    /**
     * 演示向后兼容性
     */
    public static void demonstrateBackwardCompatibility() {
        HiLog.info(LABEL_LOG, "=== 向后兼容性演示 ===");
        
        HealthDataCache cache = HealthDataCache.getInstance();
        
        // 使用原有的API，应该仍然正常工作
        cache.addToCache("{\"heartRate\": 80, \"timestamp\": \"2025-08-22T10:05:00Z\"}");
        
        List<String> cachedData = cache.getAllCachedData();
        HiLog.info(LABEL_LOG, "使用原有API获取到 " + cachedData.size() + " 条数据");
        
        int cacheSize = cache.getCacheSize();
        HiLog.info(LABEL_LOG, "使用原有API获取缓存大小: " + cacheSize);
        
        cache.clearCache();
        HiLog.info(LABEL_LOG, "使用原有API清空缓存完成");
    }
}