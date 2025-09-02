package com.ljwx.watch.utils;

import java.beans.PropertyChangeListener;
import java.util.List;
import java.util.Map;
import java.math.BigDecimal;
import org.json.JSONObject;
import ohos.bluetooth.ble.BlePeripheralDevice;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * DataManager适配器
 * 提供与原DataManager兼容的接口，内部使用OptimizedDataManager
 * 这样现有代码可以无缝迁移到优化版本
 */
public class DataManagerAdapter {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    private static DataManagerAdapter instance;
    private final OptimizedDataManager optimizedManager;
    
    // 传统DataManager的旧接口兼容（延迟加载）
    private DataManager legacyDataManager;
    
    private DataManagerAdapter() {
        optimizedManager = OptimizedDataManager.getInstance();
        HiLog.info(LABEL_LOG, "DataManagerAdapter::构造函数 适配器初始化完成");
    }
    
    public static DataManagerAdapter getInstance() {
        if (instance == null) {
            synchronized (DataManagerAdapter.class) {
                if (instance == null) {
                    instance = new DataManagerAdapter();
                }
            }
        }
        return instance;
    }
    
    /**
     * 获取传统DataManager实例（延迟加载）
     * 仅在需要复杂功能时初始化
     */
    private DataManager getLegacyManager() {
        if (legacyDataManager == null) {
            legacyDataManager = DataManager.getInstance();
            HiLog.info(LABEL_LOG, "DataManagerAdapter::getLegacyManager 延迟初始化传统DataManager");
        }
        return legacyDataManager;
    }
    
    // ==================== 健康数据相关方法 ====================
    
    public int getHeartRate() {
        return optimizedManager.getHealthData().getHeartRate();
    }
    
    public void setHeartRate(int heartRate) {
        optimizedManager.getHealthData().setHeartRate(heartRate);
    }
    
    public int getBloodOxygen() {
        return optimizedManager.getHealthData().getBloodOxygen();
    }
    
    public void setBloodOxygen(int bloodOxygen) {
        optimizedManager.getHealthData().setBloodOxygen(bloodOxygen);
    }
    
    public double getTemperature() {
        return optimizedManager.getHealthData().getTemperature();
    }
    
    public void setTemperature(double temperature) {
        optimizedManager.getHealthData().setTemperature(temperature);
    }
    
    public int getStress() {
        return optimizedManager.getHealthData().getStress();
    }
    
    public void setStress(int stress) {
        optimizedManager.getHealthData().setStress(stress);
    }
    
    public int getStep() {
        return optimizedManager.getHealthData().getStep();
    }
    
    public void setStep(int step) {
        optimizedManager.getHealthData().setStep(step);
    }
    
    public double getDistance() {
        return optimizedManager.getHealthData().getDistance();
    }
    
    public void setDistance(double distance) {
        optimizedManager.getHealthData().setDistance(distance);
    }
    
    public double getCalorie() {
        return optimizedManager.getHealthData().getCalorie();
    }
    
    public void setCalorie(double calorie) {
        optimizedManager.getHealthData().setCalorie(calorie);
    }
    
    public int getPressureHigh() {
        return optimizedManager.getHealthData().getPressureHigh();
    }
    
    public void setPressureHigh(int pressureHigh) {
        optimizedManager.getHealthData().setPressureHigh(pressureHigh);
    }
    
    public int getPressureLow() {
        return optimizedManager.getHealthData().getPressureLow();
    }
    
    public void setPressureLow(int pressureLow) {
        optimizedManager.getHealthData().setPressureLow(pressureLow);
    }
    
    // ==================== 设备配置相关方法 ====================
    
    public String getDeviceSn() {
        return optimizedManager.getDeviceConfig().getDeviceSn();
    }
    
    public void setDeviceSn(String deviceSn) {
        optimizedManager.getDeviceConfig().setDeviceSn(deviceSn);
    }
    
    public String getCustomerId() {
        return optimizedManager.getDeviceConfig().getCustomerId();
    }
    
    public void setCustomerId(String customerId) {
        optimizedManager.getDeviceConfig().setCustomerId(customerId);
    }
    
    public String getOrgId() {
        return optimizedManager.getDeviceConfig().getOrgId();
    }
    
    public void setOrgId(String orgId) {
        optimizedManager.getDeviceConfig().setOrgId(orgId);
    }
    
    public String getUserId() {
        return optimizedManager.getDeviceConfig().getUserId();
    }
    
    public void setUserId(String userId) {
        optimizedManager.getDeviceConfig().setUserId(userId);
    }
    
    public String getCustomerName() {
        return optimizedManager.getDeviceConfig().getCustomerName();
    }
    
    public void setCustomerName(String customerName) {
        optimizedManager.getDeviceConfig().setCustomerName(customerName);
    }
    
    public boolean getIsHealthServiceReady() {
        return optimizedManager.getDeviceConfig().getIsHealthServiceReady();
    }
    
    public void setIsHealthServiceReady(boolean isHealthServiceReady) {
        optimizedManager.getDeviceConfig().setIsHealthServiceReady(isHealthServiceReady);
    }
    
    public int getWearState() {
        return optimizedManager.getDeviceConfig().getWearState();
    }
    
    public void setWearState(int wearState) {
        optimizedManager.getDeviceConfig().setWearState(wearState);
    }
    
    // ==================== 网络配置相关方法 ====================
    
    public String getPlatformUrl() {
        return optimizedManager.getNetworkConfig().getPlatformUrl();
    }
    
    public void setPlatformUrl(String platformUrl) {
        optimizedManager.getNetworkConfig().setPlatformUrl(platformUrl);
    }
    
    public String getUploadMethod() {
        return optimizedManager.getNetworkConfig().getUploadMethod();
    }
    
    public void setUploadMethod(String uploadMethod) {
        optimizedManager.getNetworkConfig().setUploadMethod(uploadMethod);
    }
    
    public String getApiAuthorization() {
        return optimizedManager.getNetworkConfig().getApiAuthorization();
    }
    
    public void setApiAuthorization(String apiAuthorization) {
        optimizedManager.getNetworkConfig().setApiAuthorization(apiAuthorization);
    }
    
    public String getUploadHealthDataUrl() {
        return optimizedManager.getNetworkConfig().getUploadHealthDataUrl();
    }
    
    public void setUploadHealthDataUrl(String uploadHealthDataUrl) {
        optimizedManager.getNetworkConfig().setUploadHealthDataUrl(uploadHealthDataUrl);
    }
    
    public String getUploadDeviceInfoUrl() {
        return optimizedManager.getNetworkConfig().getUploadDeviceInfoUrl();
    }
    
    public void setUploadDeviceInfoUrl(String uploadDeviceInfoUrl) {
        optimizedManager.getNetworkConfig().setUploadDeviceInfoUrl(uploadDeviceInfoUrl);
    }
    
    public String getFetchMessageUrl() {
        return optimizedManager.getNetworkConfig().getFetchMessageUrl();
    }
    
    public void setFetchMessageUrl(String fetchMessageUrl) {
        optimizedManager.getNetworkConfig().setFetchMessageUrl(fetchMessageUrl);
    }
    
    public JSONObject getConfig() {
        return optimizedManager.getNetworkConfig().getConfig();
    }
    
    public void setConfig(JSONObject config) {
        optimizedManager.getNetworkConfig().setConfig(config);
    }
    
    // ==================== 系统状态相关方法 ====================
    
    public boolean getScanStatus() {
        return optimizedManager.getSystemState().getScanStatus();
    }
    
    public void setScanStatus(boolean isScanning) {
        optimizedManager.getSystemState().setScanStatus(isScanning);
    }
    
    public boolean getConnectStatus() {
        return optimizedManager.getSystemState().getConnectStatus();
    }
    
    public void setConnectStatus(boolean isConnected) {
        optimizedManager.getSystemState().setConnectStatus(isConnected);
    }
    
    public boolean isLicenseExceeded() {
        return optimizedManager.getSystemState().isLicenseExceeded();
    }
    
    public void setLicenseExceeded(boolean licenseExceeded) {
        optimizedManager.getSystemState().setLicenseExceeded(licenseExceeded);
    }
    
    public String getAppStatus() {
        return optimizedManager.getSystemState().getAppStatus();
    }
    
    public void setAppStatus(String appStatus) {
        optimizedManager.getSystemState().setAppStatus(appStatus);
    }
    
    public String getCommonEvent() {
        return optimizedManager.getSystemState().getCommonEvent();
    }
    
    public void setCommonEvent(String commonEvent) {
        optimizedManager.getSystemState().setCommonEvent(commonEvent);
    }
    
    // ==================== 监听器管理 ====================
    
    public void addPropertyChangeListener(String key, PropertyChangeListener pcl) {
        optimizedManager.addWeakPropertyChangeListener(key, pcl);
    }
    
    public void removePropertyChangeListener(String key) {
        optimizedManager.removePropertyChangeListener(key);
    }
    
    // ==================== 复杂功能代理到传统DataManager ====================
    
    // 这些复杂功能仍然代理到传统DataManager，避免重复实现
    
    public List<String> getDeviceNames() {
        return getLegacyManager().getDeviceNames();
    }
    
    public void setDeviceNames(List<String> names) {
        getLegacyManager().setDeviceNames(names);
    }
    
    public Map getDeviceList() {
        return getLegacyManager().getDeviceList();
    }
    
    public void setDeviceList(Map deviceList) {
        getLegacyManager().setDeviceList(deviceList);
    }
    
    public BlePeripheralDevice getDefaultDevice() {
        return getLegacyManager().getDefaultDevice();
    }
    
    public void setDefaultDevice(BlePeripheralDevice defaultDevice) {
        getLegacyManager().setDefaultDevice(defaultDevice);
    }
    
    // 大量配置相关方法代理到传统DataManager
    // （这里只列出几个示例，实际需要根据使用情况添加）
    
    public boolean isSupportHeartRate() {
        return getLegacyManager().isSupportHeartRate();
    }
    
    public void setSupportHeartRate(boolean supportHeartRate) {
        getLegacyManager().setSupportHeartRate(supportHeartRate);
    }
    
    public long getHeartRateMeasurePeriod() {
        return getLegacyManager().getHeartRateMeasurePeriod();
    }
    
    public void setHeartRateMeasurePeriod(int heartRateMeasurePeriod) {
        getLegacyManager().setHeartRateMeasurePeriod(heartRateMeasurePeriod);
    }
    
    public boolean isSupportBloodOxygen() {
        return getLegacyManager().isSupportBloodOxygen();
    }
    
    public void setSupportBloodOxygen(boolean supportBloodOxygen) {
        getLegacyManager().setSupportBloodOxygen(supportBloodOxygen);
    }
    
    public long getBloodOxygenMeasurePeriod() {
        return getLegacyManager().getBloodOxygenMeasurePeriod();
    }
    
    public void setBloodOxygenMeasurePeriod(long bloodOxygenMeasurePeriod) {
        getLegacyManager().setBloodOxygenMeasurePeriod(bloodOxygenMeasurePeriod);
    }
    
    public boolean isSupportTemperature() {
        return getLegacyManager().isSupportTemperature();
    }
    
    public void setSupportTemperature(boolean supportTemperature) {
        getLegacyManager().setSupportTemperature(supportTemperature);
    }
    
    public boolean isSupportStress() {
        return getLegacyManager().isSupportStress();
    }
    
    public void setSupportStress(boolean supportStress) {
        getLegacyManager().setSupportStress(supportStress);
    }
    
    public boolean isSupportStep() {
        return getLegacyManager().isSupportStep();
    }
    
    public void setSupportStep(boolean supportStep) {
        getLegacyManager().setSupportStep(supportStep);
    }
    
    // 更多支持状态和配置方法...（根据实际使用需求添加）
    
    // ==================== 内存管理方法 ====================
    
    /**
     * 手动触发内存清理
     */
    public void cleanupMemory() {
        optimizedManager.cleanupMemory();
    }
    
    /**
     * 获取内存使用统计
     */
    public String getMemoryStats() {
        return optimizedManager.getMemoryStats();
    }
    
    /**
     * 销毁适配器和底层优化管理器
     */
    public void destroy() {
        optimizedManager.destroy();
        legacyDataManager = null;
        HiLog.info(LABEL_LOG, "DataManagerAdapter::destroy 适配器销毁完成");
    }
    
    /**
     * 获取底层优化管理器（用于高级操作）
     */
    public OptimizedDataManager getOptimizedManager() {
        return optimizedManager;
    }
}