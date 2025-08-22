package com.ljwx.watch;

import ohos.app.Context;
import ohos.data.DatabaseHelper;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import ohos.data.preferences.Preferences;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashMap;
import com.ljwx.watch.utils.DataManager;

/**
 * 多接口数据缓存管理器
 * 支持三种数据类型的独立环形缓存：
 * 1. health_data - 健康数据缓存
 * 2. upload_device_info - 设备信息上传缓存
 * 3. upload_common_event - 通用事件上传缓存
 */
public class HealthDataCache{
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    private static HealthDataCache instance;
    private DataManager dataManager = DataManager.getInstance();
    private static Preferences preferences;
    private static Context sContext;
    private static final int MAX_CACHE_SIZE = 100;  // 最大缓存条数
    
    // 数据类型枚举
    public enum DataType {
        HEALTH_DATA("health_data_cache", "健康数据"),
        DEVICE_INFO("device_info_cache", "设备信息"),
        COMMON_EVENT("common_event_cache", "通用事件");
        
        private final String cacheKey;
        private final String displayName;
        
        DataType(String cacheKey, String displayName) {
            this.cacheKey = cacheKey;
            this.displayName = displayName;
        }
        
        public String getCacheKey() { return cacheKey; }
        public String getDisplayName() { return displayName; }
    }
    
    // 三个独立的环形缓存队列
    private Map<DataType, BlockingQueue<String>> cacheQueues;

    private HealthDataCache() {
        dataManager = DataManager.getInstance();
        int maxSize = Math.min(dataManager.getCacheMaxCount(), MAX_CACHE_SIZE);
        
        // 初始化三个独立的环形缓存队列
        cacheQueues = new HashMap<>();
        for (DataType type : DataType.values()) {
            cacheQueues.put(type, new ArrayBlockingQueue<>(maxSize));
        }
        
        // 加载所有类型的缓存数据
        loadAllCaches();
    }
       /**
     * 在 Ability 或 Service 启动时，先调用一次 init()，传入它的 Context
     */
    public static void init(Context ctx) {
        // 用 getApplicationContext() 保证不会误持有某个 Ability 的短生命周期 Context
        sContext = ctx.getApplicationContext();
    }

    public static synchronized HealthDataCache getInstance() {
        if (instance == null) {
            instance = new HealthDataCache();
        }
        return instance;
    }

    /**
     * 添加健康数据到缓存 (向后兼容接口)
     */
    public void addToCache(String healthData) {
        addToCache(DataType.HEALTH_DATA, healthData);
    }
    
    /**
     * 添加数据到指定类型的缓存
     * @param dataType 数据类型
     * @param data 要缓存的数据
     */
    public void addToCache(DataType dataType, String data) {
        try {
            BlockingQueue<String> queue = cacheQueues.get(dataType);
            if (queue == null) {
                HiLog.error(LABEL_LOG, "HealthDataCache::addToCache 未知的数据类型: " + dataType);
                return;
            }
            
            // 检查队列是否已满，如果满了就移除最旧的数据
            if (queue.size() >= dataManager.getCacheMaxCount()) {
                String oldestData = queue.poll(); // 移除最旧的数据
                HiLog.info(LABEL_LOG, "HealthDataCache::addToCache [" + dataType.getDisplayName() + "] 移除最旧数据: " + (oldestData != null ? oldestData.substring(0, Math.min(50, oldestData.length())) + "..." : "null"));
            }
            
            boolean added = queue.offer(data);
            if (added) {
                HiLog.info(LABEL_LOG, "HealthDataCache::addToCache [" + dataType.getDisplayName() + "] 添加新数据成功，当前缓存大小: " + queue.size());
                saveCache(dataType);
            } else {
                HiLog.error(LABEL_LOG, "HealthDataCache::addToCache [" + dataType.getDisplayName() + "] 添加新数据失败，队列已满");
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataCache::addToCache [" + dataType.getDisplayName() + "] error: " + e.getMessage());
        }
    }

    /**
     * 获取健康数据缓存 (向后兼容接口)
     */
    public List<String> getAllCachedData() {
        return getAllCachedData(DataType.HEALTH_DATA);
    }
    
    /**
     * 获取指定类型的所有缓存数据
     * @param dataType 数据类型
     * @return 缓存数据列表
     */
    public List<String> getAllCachedData(DataType dataType) {
        List<String> result = new ArrayList<>();
        try {
            BlockingQueue<String> queue = cacheQueues.get(dataType);
            if (queue == null) {
                HiLog.error(LABEL_LOG, "HealthDataCache::getAllCachedData 未知的数据类型: " + dataType);
                return result;
            }
            
            // 使用迭代器而不是drainTo，这样不会清空队列
            for (String data : queue) {
                result.add(data);
            }
            HiLog.info(LABEL_LOG, "HealthDataCache::getAllCachedData [" + dataType.getDisplayName() + "] 获取缓存数据: " + result.size() + "条");
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataCache::getAllCachedData [" + dataType.getDisplayName() + "] error: " + e.getMessage());
        }
        return result;
    }

    /**
     * 清空健康数据缓存 (向后兼容接口)
     */
    public void clearCache() {
        clearCache(DataType.HEALTH_DATA);
    }
    
    /**
     * 清空指定类型的缓存
     * @param dataType 数据类型
     */
    public void clearCache(DataType dataType) {
        try {
            BlockingQueue<String> queue = cacheQueues.get(dataType);
            if (queue == null) {
                HiLog.error(LABEL_LOG, "HealthDataCache::clearCache 未知的数据类型: " + dataType);
                return;
            }
            
            int originalSize = queue.size();
            queue.clear();
            HiLog.info(LABEL_LOG, "HealthDataCache::clearCache [" + dataType.getDisplayName() + "] 清空缓存，原大小: " + originalSize);
            saveCache(dataType);
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataCache::clearCache [" + dataType.getDisplayName() + "] error: " + e.getMessage());
        }
    }
    
    /**
     * 清空所有类型的缓存
     */
    public void clearAllCaches() {
        for (DataType type : DataType.values()) {
            clearCache(type);
        }
        HiLog.info(LABEL_LOG, "HealthDataCache::clearAllCaches 清空所有缓存完成");
    }
    private static Preferences getPreferences() {
        if (preferences == null) {
            // 这里拿到的就是你在 init() 里传进来的 Context
            DatabaseHelper databaseHelper = new DatabaseHelper(sContext);
            String fileName = "pref";
            preferences = databaseHelper.getPreferences(fileName);
        }
        return preferences;
    }
    public static void storeValue(String key, String value) {
        Preferences prefs = getPreferences();
        prefs.putString(key, value);
        prefs.flush();
    }

    public static String fetchValue(String key, String defaultVal) {
        Preferences prefs = getPreferences();
        String v = prefs.getString(key, defaultVal);
        return v != null ? v : defaultVal;
    }
    /**
     * 保存所有类型的缓存数据
     */
    private void saveAllCaches() {
        for (DataType type : DataType.values()) {
            saveCache(type);
        }
    }
    
    /**
     * 保存指定类型的缓存数据
     * @param dataType 数据类型
     */
    private void saveCache(DataType dataType) {
        try {
            BlockingQueue<String> queue = cacheQueues.get(dataType);
            if (queue == null) {
                HiLog.error(LABEL_LOG, "HealthDataCache::saveCache 未知的数据类型: " + dataType);
                return;
            }
            
            List<String> cacheList = new ArrayList<>(queue);
            String cacheKey = dataType.getCacheKey();
            
            if(cacheList.isEmpty()){
                // 清空所有缓存键
                for(int i=0;i<10;i++){
                    storeValue(cacheKey + (i == 0 ? "" : "_" + i), "");
                }
                HiLog.info(LABEL_LOG, "HealthDataCache::saveCache [" + dataType.getDisplayName() + "] 清空缓存");
                return;
            }
            
            // 分片存储，每片最大7000字符(留余量)
            final int MAX_CHUNK_SIZE=7000;
            String fullCacheStr=String.join("|",cacheList);
            int totalLen=fullCacheStr.length();
            
            if(totalLen<=MAX_CHUNK_SIZE){
                // 单片存储
                storeValue(cacheKey, fullCacheStr);
                // 清空其他片
                for(int i=1;i<10;i++){
                    storeValue(cacheKey + "_" + i, "");
                }
                HiLog.info(LABEL_LOG,"HealthDataCache::saveCache [" + dataType.getDisplayName() + "] 单片存储,大小:" + totalLen);
            }else{
                // 多片存储
                int chunkCount=(totalLen+MAX_CHUNK_SIZE-1)/MAX_CHUNK_SIZE;
                for(int i=0;i<chunkCount&&i<10;i++){
                    int start=i*MAX_CHUNK_SIZE;
                    int end=Math.min(start+MAX_CHUNK_SIZE,totalLen);
                    String chunk=fullCacheStr.substring(start,end);
                    storeValue(cacheKey + (i == 0 ? "" : "_" + i), chunk);
                }
                // 清空未使用的片
                for(int i=chunkCount;i<10;i++){
                    storeValue(cacheKey + (i == 0 ? "" : "_" + i), "");
                }
                HiLog.info(LABEL_LOG,"HealthDataCache::saveCache [" + dataType.getDisplayName() + "] 多片存储,片数:" + chunkCount + ",总大小:" + totalLen);
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataCache::saveCache [" + dataType.getDisplayName() + "] error: " + e.getMessage());
        }
    }

    /**
     * 加载所有类型的缓存数据
     */
    private void loadAllCaches() {
        for (DataType type : DataType.values()) {
            loadCache(type);
        }
        HiLog.info(LABEL_LOG, "HealthDataCache::loadAllCaches 加载所有缓存完成");
    }
    
    /**
     * 加载指定类型的缓存数据
     * @param dataType 数据类型
     */
    private void loadCache(DataType dataType) {
        try {
            BlockingQueue<String> queue = cacheQueues.get(dataType);
            if (queue == null) {
                HiLog.error(LABEL_LOG, "HealthDataCache::loadCache 未知的数据类型: " + dataType);
                return;
            }
            
            String cacheKey = dataType.getCacheKey();
            
            // 尝试多片加载
            StringBuilder fullCacheStr = new StringBuilder();
            for(int i = 0; i < 10; i++){
                String chunk = fetchValue(cacheKey + (i == 0 ? "" : "_" + i), "");
                if(!chunk.isEmpty()){
                    fullCacheStr.append(chunk);
                }else if(i > 0){
                    break; // 遇到空片且不是第一片，停止加载
                }
            }
            
            String cachedData = fullCacheStr.toString();
            if(!cachedData.isEmpty()){
                String[] items = cachedData.split("\\|");
                int loadedCount = 0;
                for(String item : items){
                    if(!item.isEmpty()){
                        boolean added = queue.offer(item);
                        if(!added){
                            HiLog.warn(LABEL_LOG,"HealthDataCache::loadCache [" + dataType.getDisplayName() + "] 缓存已满，无法加载更多数据");
                            break;
                        }
                        loadedCount++;
                    }
                }
                HiLog.info(LABEL_LOG,"HealthDataCache::loadCache [" + dataType.getDisplayName() + "] 加载缓存成功，大小:" + loadedCount + ",总字符数:" + cachedData.length());
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataCache::loadCache [" + dataType.getDisplayName() + "] error: " + e.getMessage());
        }
    }
    
    // ==================== 便利方法 ====================
    
    /**
     * 添加设备信息数据到缓存
     */
    public void addDeviceInfoToCache(String deviceInfoData) {
        addToCache(DataType.DEVICE_INFO, deviceInfoData);
    }
    
    /**
     * 添加通用事件数据到缓存
     */
    public void addCommonEventToCache(String commonEventData) {
        addToCache(DataType.COMMON_EVENT, commonEventData);
    }
    
    /**
     * 获取设备信息缓存数据
     */
    public List<String> getDeviceInfoCache() {
        return getAllCachedData(DataType.DEVICE_INFO);
    }
    
    /**
     * 获取通用事件缓存数据
     */
    public List<String> getCommonEventCache() {
        return getAllCachedData(DataType.COMMON_EVENT);
    }
    
    /**
     * 清空设备信息缓存
     */
    public void clearDeviceInfoCache() {
        clearCache(DataType.DEVICE_INFO);
    }
    
    /**
     * 清空通用事件缓存
     */
    public void clearCommonEventCache() {
        clearCache(DataType.COMMON_EVENT);
    }
    
    // ==================== 缓存状态查询 ====================
    
    /**
     * 获取指定类型缓存的大小
     */
    public int getCacheSize(DataType dataType) {
        BlockingQueue<String> queue = cacheQueues.get(dataType);
        return queue != null ? queue.size() : 0;
    }
    
    /**
     * 获取健康数据缓存大小 (向后兼容)
     */
    public int getCacheSize() {
        return getCacheSize(DataType.HEALTH_DATA);
    }
    
    /**
     * 检查指定类型的缓存是否为空
     */
    public boolean isCacheEmpty(DataType dataType) {
        return getCacheSize(dataType) == 0;
    }
    
    /**
     * 检查是否所有缓存都为空
     */
    public boolean areAllCachesEmpty() {
        for (DataType type : DataType.values()) {
            if (!isCacheEmpty(type)) {
                return false;
            }
        }
        return true;
    }
    
    /**
     * 获取缓存状态摘要
     */
    public String getCacheStatusSummary() {
        StringBuilder summary = new StringBuilder("缓存状态摘要: ");
        for (DataType type : DataType.values()) {
            int size = getCacheSize(type);
            summary.append(type.getDisplayName()).append("=").append(size).append("条, ");
        }
        return summary.toString();
    }
    
    /**
     * 打印缓存状态到日志
     */
    public void logCacheStatus() {
        for (DataType type : DataType.values()) {
            int size = getCacheSize(type);
            int maxSize = dataManager.getCacheMaxCount();
            HiLog.info(LABEL_LOG, "HealthDataCache::logCacheStatus [" + type.getDisplayName() + "] " + size + "/" + maxSize + " 条数据");
        }
    }
} 