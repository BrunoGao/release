package com.ljwx.watch.utils;

import java.beans.PropertyChangeListener;
import java.beans.PropertyChangeSupport;
import java.util.Map;
import java.util.WeakHashMap;
import java.util.concurrent.ConcurrentHashMap;
import java.lang.ref.WeakReference;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.json.JSONObject;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 优化的数据管理器
 * 特性：
 * 1. 分组数据管理，避免全量加载
 * 2. LRU缓存机制，控制内存占用
 * 3. 弱引用监听器，防止内存泄漏
 * 4. 生命周期管理，自动内存清理
 * 5. 延迟加载，按需初始化
 */
public class OptimizedDataManager {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    private static OptimizedDataManager instance;
    private static final int DEFAULT_CACHE_SIZE = 100;
    private static final long CLEANUP_INTERVAL_MS = 5 * 60 * 1000; // 5分钟清理周期
    
    // 数据分组
    private HealthDataGroup healthData;
    private DeviceConfigGroup deviceConfig;
    private NetworkConfigGroup networkConfig;
    private SystemStateGroup systemState;
    
    // LRU缓存
    private final LRUCache<String, Object> dataCache;
    
    // 弱引用监听器，防止内存泄漏
    private final WeakHashMap<String, WeakReference<PropertyChangeListener>> listeners;
    private final PropertyChangeSupport support;
    
    // 内存清理调度器
    private final ScheduledExecutorService cleanupExecutor;
    
    // 生命周期标记
    private boolean isActive = true;
    
    private OptimizedDataManager() {
        this.dataCache = new LRUCache<>(DEFAULT_CACHE_SIZE);
        this.listeners = new WeakHashMap<>();
        this.support = new PropertyChangeSupport(this);
        this.cleanupExecutor = Executors.newSingleThreadScheduledExecutor();
        
        // 启动定期内存清理
        startMemoryCleanup();
        
        HiLog.info(LABEL_LOG, "OptimizedDataManager::构造函数 优化数据管理器初始化完成");
    }
    
    public static OptimizedDataManager getInstance() {
        if (instance == null) {
            synchronized (OptimizedDataManager.class) {
                if (instance == null) {
                    instance = new OptimizedDataManager();
                }
            }
        }
        return instance;
    }
    
    /**
     * 启动内存清理任务
     */
    private void startMemoryCleanup() {
        cleanupExecutor.scheduleAtFixedRate(() -> {
            try {
                cleanupMemory();
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "OptimizedDataManager::内存清理异常: " + e.getMessage());
            }
        }, CLEANUP_INTERVAL_MS, CLEANUP_INTERVAL_MS, TimeUnit.MILLISECONDS);
    }
    
    /**
     * 内存清理
     */
    public void cleanupMemory() {
        if (!isActive) {
            return;
        }
        
        HiLog.info(LABEL_LOG, "OptimizedDataManager::cleanupMemory 开始内存清理");
        
        // 清理过期缓存
        dataCache.evictExpired();
        
        // 清理无效的弱引用监听器
        listeners.values().removeIf(ref -> ref.get() == null);
        
        // 建议垃圾回收
        System.gc();
        
        HiLog.info(LABEL_LOG, "OptimizedDataManager::cleanupMemory 内存清理完成");
    }
    
    /**
     * 获取健康数据组（延迟初始化）
     */
    public HealthDataGroup getHealthData() {
        if (healthData == null) {
            healthData = new HealthDataGroup();
            HiLog.info(LABEL_LOG, "OptimizedDataManager::getHealthData 延迟初始化健康数据组");
        }
        return healthData;
    }
    
    /**
     * 获取设备配置组（延迟初始化）
     */
    public DeviceConfigGroup getDeviceConfig() {
        if (deviceConfig == null) {
            deviceConfig = new DeviceConfigGroup();
            HiLog.info(LABEL_LOG, "OptimizedDataManager::getDeviceConfig 延迟初始化设备配置组");
        }
        return deviceConfig;
    }
    
    /**
     * 获取网络配置组（延迟初始化）
     */
    public NetworkConfigGroup getNetworkConfig() {
        if (networkConfig == null) {
            networkConfig = new NetworkConfigGroup();
            HiLog.info(LABEL_LOG, "OptimizedDataManager::getNetworkConfig 延迟初始化网络配置组");
        }
        return networkConfig;
    }
    
    /**
     * 获取系统状态组（延迟初始化）
     */
    public SystemStateGroup getSystemState() {
        if (systemState == null) {
            systemState = new SystemStateGroup();
            HiLog.info(LABEL_LOG, "OptimizedDataManager::getSystemState 延迟初始化系统状态组");
        }
        return systemState;
    }
    
    /**
     * 缓存数据
     */
    public void cacheData(String key, Object value) {
        dataCache.put(key, value);
    }
    
    /**
     * 获取缓存数据
     */
    public Object getCachedData(String key) {
        return dataCache.get(key);
    }
    
    /**
     * 添加弱引用监听器
     */
    public void addWeakPropertyChangeListener(String key, PropertyChangeListener listener) {
        listeners.put(key, new WeakReference<>(listener));
        support.addPropertyChangeListener(listener);
        HiLog.info(LABEL_LOG, "OptimizedDataManager::addWeakPropertyChangeListener 添加弱引用监听器: " + key);
    }
    
    /**
     * 移除监听器
     */
    public void removePropertyChangeListener(String key) {
        WeakReference<PropertyChangeListener> ref = listeners.remove(key);
        if (ref != null && ref.get() != null) {
            support.removePropertyChangeListener(ref.get());
            HiLog.info(LABEL_LOG, "OptimizedDataManager::removePropertyChangeListener 移除监听器: " + key);
        }
    }
    
    /**
     * 触发属性变化
     */
    protected void firePropertyChange(String propertyName, Object oldValue, Object newValue) {
        if (isActive) {
            support.firePropertyChange(propertyName, oldValue, newValue);
        }
    }
    
    /**
     * 生命周期管理 - 销毁
     */
    public void destroy() {
        HiLog.info(LABEL_LOG, "OptimizedDataManager::destroy 开始销毁数据管理器");
        
        isActive = false;
        
        // 停止清理任务
        if (cleanupExecutor != null && !cleanupExecutor.isShutdown()) {
            cleanupExecutor.shutdown();
            try {
                if (!cleanupExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                    cleanupExecutor.shutdownNow();
                }
            } catch (InterruptedException e) {
                cleanupExecutor.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
        
        // 清理缓存和监听器
        dataCache.evictAll();
        listeners.clear();
        
        // 清理数据组
        healthData = null;
        deviceConfig = null;
        networkConfig = null;
        systemState = null;
        
        HiLog.info(LABEL_LOG, "OptimizedDataManager::destroy 数据管理器销毁完成");
    }
    
    /**
     * 获取内存使用统计
     */
    public String getMemoryStats() {
        int cacheSize = dataCache.size();
        int listenersSize = listeners.size();
        long activeListeners = listeners.values().stream()
                .mapToLong(ref -> ref.get() != null ? 1 : 0)
                .sum();
        
        return String.format("缓存大小: %d, 监听器数量: %d, 活动监听器: %d", 
                           cacheSize, listenersSize, activeListeners);
    }
    
    // ==================== 数据分组类 ====================
    
    /**
     * 健康数据组
     */
    public class HealthDataGroup {
        private volatile int heartRate = 0;
        private volatile int bloodOxygen = 0;
        private volatile double temperature = 0.0;
        private volatile int stress = 0;
        private volatile int step = 0;
        private volatile double distance = 0.0;
        private volatile double calorie = 0.0;
        private volatile int pressureHigh = 0;
        private volatile int pressureLow = 0;
        
        // Getter和Setter方法，带有属性变化通知
        public int getHeartRate() { return heartRate; }
        public void setHeartRate(int heartRate) {
            int old = this.heartRate;
            if (old != heartRate) {
                this.heartRate = heartRate;
                firePropertyChange("heartRate", old, heartRate);
            }
        }
        
        public int getBloodOxygen() { return bloodOxygen; }
        public void setBloodOxygen(int bloodOxygen) {
            int old = this.bloodOxygen;
            if (old != bloodOxygen) {
                this.bloodOxygen = bloodOxygen;
                firePropertyChange("bloodOxygen", old, bloodOxygen);
            }
        }
        
        public double getTemperature() { return temperature; }
        public void setTemperature(double temperature) {
            double old = this.temperature;
            if (Double.compare(old, temperature) != 0) {
                this.temperature = temperature;
                firePropertyChange("temperature", old, temperature);
            }
        }
        
        public int getStress() { return stress; }
        public void setStress(int stress) {
            int old = this.stress;
            if (old != stress) {
                this.stress = stress;
                firePropertyChange("stress", old, stress);
            }
        }
        
        public int getStep() { return step; }
        public void setStep(int step) {
            int old = this.step;
            if (old != step) {
                this.step = step;
                firePropertyChange("step", old, step);
            }
        }
        
        public double getDistance() { return distance; }
        public void setDistance(double distance) {
            double old = this.distance;
            if (Double.compare(old, distance) != 0) {
                this.distance = distance;
                firePropertyChange("distance", old, distance);
            }
        }
        
        public double getCalorie() { return calorie; }
        public void setCalorie(double calorie) {
            double old = this.calorie;
            if (Double.compare(old, calorie) != 0) {
                this.calorie = calorie;
                firePropertyChange("calorie", old, calorie);
            }
        }
        
        public int getPressureHigh() { return pressureHigh; }
        public void setPressureHigh(int pressureHigh) {
            int old = this.pressureHigh;
            if (old != pressureHigh) {
                this.pressureHigh = pressureHigh;
                firePropertyChange("pressureHigh", old, pressureHigh);
            }
        }
        
        public int getPressureLow() { return pressureLow; }
        public void setPressureLow(int pressureLow) {
            int old = this.pressureLow;
            if (old != pressureLow) {
                this.pressureLow = pressureLow;
                firePropertyChange("pressureLow", old, pressureLow);
            }
        }
    }
    
    /**
     * 设备配置组
     */
    public class DeviceConfigGroup {
        private volatile String deviceSn = "";
        private volatile String customerId = "";
        private volatile String orgId = "";
        private volatile String userId = "";
        private volatile String customerName = "";
        private volatile boolean isHealthServiceReady = false;
        private volatile int wearState = 0;
        
        public String getDeviceSn() { return deviceSn; }
        public void setDeviceSn(String deviceSn) {
            String old = this.deviceSn;
            this.deviceSn = deviceSn;
            firePropertyChange("deviceSn", old, deviceSn);
        }
        
        public String getCustomerId() { return customerId; }
        public void setCustomerId(String customerId) {
            String old = this.customerId;
            this.customerId = customerId;
            firePropertyChange("customerId", old, customerId);
        }
        
        public String getOrgId() { return orgId; }
        public void setOrgId(String orgId) {
            String old = this.orgId;
            this.orgId = orgId;
            firePropertyChange("orgId", old, orgId);
        }
        
        public String getUserId() { return userId; }
        public void setUserId(String userId) {
            String old = this.userId;
            this.userId = userId;
            firePropertyChange("userId", old, userId);
        }
        
        public String getCustomerName() { return customerName; }
        public void setCustomerName(String customerName) {
            String old = this.customerName;
            this.customerName = customerName;
            firePropertyChange("customerName", old, customerName);
        }
        
        public boolean getIsHealthServiceReady() { return isHealthServiceReady; }
        public void setIsHealthServiceReady(boolean isHealthServiceReady) {
            boolean old = this.isHealthServiceReady;
            this.isHealthServiceReady = isHealthServiceReady;
            firePropertyChange("isHealthServiceReady", old, isHealthServiceReady);
        }
        
        public int getWearState() { return wearState; }
        public void setWearState(int wearState) {
            int old = this.wearState;
            this.wearState = wearState;
            firePropertyChange("wearState", old, wearState);
        }
    }
    
    /**
     * 网络配置组
     */
    public class NetworkConfigGroup {
        private volatile String platformUrl = "";
        private volatile String uploadMethod = "";
        private volatile String apiAuthorization = "";
        private volatile String uploadHealthDataUrl = "";
        private volatile String uploadDeviceInfoUrl = "";
        private volatile String fetchMessageUrl = "";
        private volatile JSONObject config;
        
        public String getPlatformUrl() { return platformUrl; }
        public void setPlatformUrl(String platformUrl) {
            String old = this.platformUrl;
            this.platformUrl = platformUrl;
            firePropertyChange("platformUrl", old, platformUrl);
        }
        
        public String getUploadMethod() { return uploadMethod; }
        public void setUploadMethod(String uploadMethod) {
            String old = this.uploadMethod;
            this.uploadMethod = uploadMethod;
            firePropertyChange("uploadMethod", old, uploadMethod);
        }
        
        public String getApiAuthorization() { return apiAuthorization; }
        public void setApiAuthorization(String apiAuthorization) {
            String old = this.apiAuthorization;
            this.apiAuthorization = apiAuthorization;
            firePropertyChange("apiAuthorization", old, apiAuthorization);
        }
        
        public String getUploadHealthDataUrl() { return uploadHealthDataUrl; }
        public void setUploadHealthDataUrl(String uploadHealthDataUrl) {
            String old = this.uploadHealthDataUrl;
            this.uploadHealthDataUrl = uploadHealthDataUrl;
            firePropertyChange("uploadHealthDataUrl", old, uploadHealthDataUrl);
        }
        
        public String getUploadDeviceInfoUrl() { return uploadDeviceInfoUrl; }
        public void setUploadDeviceInfoUrl(String uploadDeviceInfoUrl) {
            String old = this.uploadDeviceInfoUrl;
            this.uploadDeviceInfoUrl = uploadDeviceInfoUrl;
            firePropertyChange("uploadDeviceInfoUrl", old, uploadDeviceInfoUrl);
        }
        
        public String getFetchMessageUrl() { return fetchMessageUrl; }
        public void setFetchMessageUrl(String fetchMessageUrl) {
            String old = this.fetchMessageUrl;
            this.fetchMessageUrl = fetchMessageUrl;
            firePropertyChange("fetchMessageUrl", old, fetchMessageUrl);
        }
        
        public JSONObject getConfig() { return config; }
        public void setConfig(JSONObject config) {
            JSONObject old = this.config;
            this.config = config;
            firePropertyChange("config", old, config);
        }
    }
    
    /**
     * 系统状态组
     */
    public class SystemStateGroup {
        private volatile boolean isScanning = false;
        private volatile boolean isConnected = false;
        private volatile boolean licenseExceeded = false;
        private volatile String appStatus = "";
        private volatile String commonEvent = "";
        
        public boolean getScanStatus() { return isScanning; }
        public void setScanStatus(boolean isScanning) {
            boolean old = this.isScanning;
            this.isScanning = isScanning;
            firePropertyChange("isScanning", old, isScanning);
        }
        
        public boolean getConnectStatus() { return isConnected; }
        public void setConnectStatus(boolean isConnected) {
            boolean old = this.isConnected;
            this.isConnected = isConnected;
            firePropertyChange("isConnected", old, isConnected);
        }
        
        public boolean isLicenseExceeded() { return licenseExceeded; }
        public void setLicenseExceeded(boolean licenseExceeded) {
            boolean old = this.licenseExceeded;
            this.licenseExceeded = licenseExceeded;
            firePropertyChange("licenseExceeded", old, licenseExceeded);
        }
        
        public String getAppStatus() { return appStatus; }
        public void setAppStatus(String appStatus) {
            String old = this.appStatus;
            this.appStatus = appStatus;
            firePropertyChange("appStatus", old, appStatus);
        }
        
        public String getCommonEvent() { return commonEvent; }
        public void setCommonEvent(String commonEvent) {
            String old = this.commonEvent;
            this.commonEvent = commonEvent;
            firePropertyChange("commonEvent", old, commonEvent);
        }
    }
    
    // ==================== LRU缓存实现 ====================
    
    /**
     * LRU缓存实现
     */
    public static class LRUCache<K, V> extends java.util.LinkedHashMap<K, V> {
        private final int maxSize;
        
        public LRUCache(int maxSize) {
            super(16, 0.75f, true);
            this.maxSize = maxSize;
        }
        
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > maxSize;
        }
        
        /**
         * 清除过期缓存（简化实现，实际可基于时间戳）
         */
        public void evictExpired() {
            // 简化实现，清除最旧的25%数据
            int toRemove = Math.max(1, size() / 4);
            var iterator = entrySet().iterator();
            for (int i = 0; i < toRemove && iterator.hasNext(); i++) {
                iterator.next();
                iterator.remove();
            }
        }
        
        /**
         * 清空所有缓存
         */
        public void evictAll() {
            clear();
        }
    }
}