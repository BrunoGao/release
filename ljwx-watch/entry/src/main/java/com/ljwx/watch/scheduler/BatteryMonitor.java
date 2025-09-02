package com.ljwx.watch.scheduler;

import ohos.app.Context;
import ohos.batterymanager.BatteryInfo;
import ohos.batterymanager.BatteryManager;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 电池监控器
 * 负责监控设备电池状态和电量信息
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class BatteryMonitor {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "BatteryMonitor");
    
    // 状态缓存
    private BatteryStatus cachedStatus = null;
    private long lastStatusCheckTime = 0;
    private static final long STATUS_CACHE_DURATION = 60000; // 60秒缓存
    
    // 电量变化阈值
    private static final int BATTERY_CHANGE_THRESHOLD = 1; // 1%变化才更新
    
    /**
     * 获取电池电量百分比
     * @param context 应用上下文
     * @return 电量百分比 (0-100)
     */
    public int getBatteryLevel(Context context) {
        BatteryStatus status = getBatteryStatus(context);
        return status != null ? status.getBatteryLevel() : 0;
    }
    
    /**
     * 检查是否正在充电
     * @param context 应用上下文
     * @return 是否正在充电
     */
    public boolean isCharging(Context context) {
        BatteryStatus status = getBatteryStatus(context);
        return status != null ? status.isCharging() : false;
    }
    
    /**
     * 检查电量是否过低
     * @param context 应用上下文
     * @param threshold 低电量阈值百分比
     * @return 是否低电量
     */
    public boolean isBatteryLow(Context context, int threshold) {
        int batteryLevel = getBatteryLevel(context);
        return batteryLevel <= threshold;
    }
    
    /**
     * 使用默认阈值检查电量是否过低 (20%)
     * @param context 应用上下文
     * @return 是否低电量
     */
    public boolean isBatteryLow(Context context) {
        return isBatteryLow(context, 20);
    }
    
    /**
     * 获取完整的电池状态信息
     * @param context 应用上下文
     * @return 电池状态信息
     */
    public BatteryStatus getBatteryStatus(Context context) {
        long currentTime = System.currentTimeMillis();
        
        // 检查缓存有效性
        if (cachedStatus != null && currentTime - lastStatusCheckTime < STATUS_CACHE_DURATION) {
            return cachedStatus;
        }
        
        // 重新获取电池状态
        BatteryStatus newStatus = readBatteryStatus(context);
        
        // 检查是否需要更新缓存（电量变化超过阈值或状态发生变化）
        boolean shouldUpdate = cachedStatus == null ||
                             Math.abs(newStatus.getBatteryLevel() - cachedStatus.getBatteryLevel()) >= BATTERY_CHANGE_THRESHOLD ||
                             newStatus.isCharging() != cachedStatus.isCharging() ||
                             newStatus.getChargingStatus() != cachedStatus.getChargingStatus();
        
        if (shouldUpdate) {
            // 记录电池状态变化
            if (cachedStatus != null) {
                logBatteryStatusChange(cachedStatus, newStatus);
            }
            
            cachedStatus = newStatus;
            lastStatusCheckTime = currentTime;
        }
        
        return cachedStatus;
    }
    
    /**
     * 读取电池状态的核心实现
     * @param context 应用上下文
     * @return 电池状态
     */
    private BatteryStatus readBatteryStatus(Context context) {
        try {
            BatteryManager batteryManager = new BatteryManager();
            BatteryInfo batteryInfo = batteryManager.getBatteryInfo();
            
            if (batteryInfo == null) {
                HiLog.warn(LABEL_LOG, "无法获取电池信息，使用默认值");
                return new BatteryStatus(0, false, BatteryStatus.ChargingStatus.UNKNOWN, 
                                       0, BatteryStatus.HealthStatus.UNKNOWN);
            }
            
            // 获取电池电量
            int batteryLevel = batteryInfo.getCapacity();
            
            // 获取充电状态
            int chargingState = batteryInfo.getChargingStatus();
            boolean isCharging = (chargingState == BatteryInfo.OHOS_BATTERY_STATUS_CHARGING);
            BatteryStatus.ChargingStatus chargingStatus = mapChargingStatus(chargingState);
            
            // 获取电池温度
            int temperature = batteryInfo.getBatteryTemperature();
            
            // 获取电池健康状态
            int healthState = batteryInfo.getBatteryHealthState();
            BatteryStatus.HealthStatus healthStatus = mapHealthStatus(healthState);
            
            BatteryStatus status = new BatteryStatus(batteryLevel, isCharging, chargingStatus, 
                                                   temperature, healthStatus);
            
            HiLog.debug(LABEL_LOG, "电池状态读取成功: " + status.toString());
            return status;
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "读取电池状态异常: " + e.getMessage());
            // 返回默认状态
            return new BatteryStatus(0, false, BatteryStatus.ChargingStatus.UNKNOWN, 
                                   0, BatteryStatus.HealthStatus.UNKNOWN);
        }
    }
    
    /**
     * 映射充电状态
     * @param chargingState HarmonyOS充电状态值
     * @return 充电状态枚举
     */
    private BatteryStatus.ChargingStatus mapChargingStatus(int chargingState) {
        switch (chargingState) {
            case BatteryInfo.OHOS_BATTERY_STATUS_CHARGING:
                return BatteryStatus.ChargingStatus.CHARGING;
            case BatteryInfo.OHOS_BATTERY_STATUS_DISCHARGING:
                return BatteryStatus.ChargingStatus.DISCHARGING;
            case BatteryInfo.OHOS_BATTERY_STATUS_NOT_CHARGING:
                return BatteryStatus.ChargingStatus.NOT_CHARGING;
            case BatteryInfo.OHOS_BATTERY_STATUS_FULL:
                return BatteryStatus.ChargingStatus.FULL;
            default:
                return BatteryStatus.ChargingStatus.UNKNOWN;
        }
    }
    
    /**
     * 映射电池健康状态
     * @param healthState HarmonyOS健康状态值
     * @return 健康状态枚举
     */
    private BatteryStatus.HealthStatus mapHealthStatus(int healthState) {
        switch (healthState) {
            case BatteryInfo.OHOS_BATTERY_HEALTH_GOOD:
                return BatteryStatus.HealthStatus.GOOD;
            case BatteryInfo.OHOS_BATTERY_HEALTH_OVERHEAT:
                return BatteryStatus.HealthStatus.OVERHEAT;
            case BatteryInfo.OHOS_BATTERY_HEALTH_OVER_VOLTAGE:
                return BatteryStatus.HealthStatus.OVER_VOLTAGE;
            case BatteryInfo.OHOS_BATTERY_HEALTH_COLD:
                return BatteryStatus.HealthStatus.COLD;
            default:
                return BatteryStatus.HealthStatus.UNKNOWN;
        }
    }
    
    /**
     * 记录电池状态变化
     * @param oldStatus 旧状态
     * @param newStatus 新状态
     */
    private void logBatteryStatusChange(BatteryStatus oldStatus, BatteryStatus newStatus) {
        StringBuilder changeLog = new StringBuilder("电池状态变化: ");
        
        // 电量变化
        if (oldStatus.getBatteryLevel() != newStatus.getBatteryLevel()) {
            changeLog.append(String.format("电量 %d%% -> %d%%, ", 
                           oldStatus.getBatteryLevel(), newStatus.getBatteryLevel()));
        }
        
        // 充电状态变化
        if (oldStatus.isCharging() != newStatus.isCharging()) {
            changeLog.append(String.format("充电状态 %s -> %s, ", 
                           oldStatus.isCharging() ? "充电中" : "未充电", 
                           newStatus.isCharging() ? "充电中" : "未充电"));
        }
        
        // 充电状态详细变化
        if (oldStatus.getChargingStatus() != newStatus.getChargingStatus()) {
            changeLog.append(String.format("充电详情 %s -> %s, ", 
                           oldStatus.getChargingStatus().getDisplayName(), 
                           newStatus.getChargingStatus().getDisplayName()));
        }
        
        // 温度变化 (变化超过5度才记录)
        if (Math.abs(oldStatus.getTemperature() - newStatus.getTemperature()) >= 50) { // 温度单位是0.1度
            changeLog.append(String.format("温度 %.1f°C -> %.1f°C, ", 
                           oldStatus.getTemperature() / 10.0, newStatus.getTemperature() / 10.0));
        }
        
        // 健康状态变化
        if (oldStatus.getHealthStatus() != newStatus.getHealthStatus()) {
            changeLog.append(String.format("健康状态 %s -> %s, ", 
                           oldStatus.getHealthStatus().getDisplayName(), 
                           newStatus.getHealthStatus().getDisplayName()));
        }
        
        if (changeLog.length() > "电池状态变化: ".length()) {
            // 移除末尾的逗号和空格
            changeLog.setLength(changeLog.length() - 2);
            HiLog.info(LABEL_LOG, changeLog.toString());
        }
    }
    
    /**
     * 强制刷新电池状态（清除缓存）
     * @param context 应用上下文
     * @return 新的电池状态
     */
    public BatteryStatus refreshStatus(Context context) {
        lastStatusCheckTime = 0; // 清除缓存时间
        return getBatteryStatus(context);
    }
    
    /**
     * 获取电池温度（摄氏度）
     * @param context 应用上下文
     * @return 电池温度
     */
    public double getBatteryTemperature(Context context) {
        BatteryStatus status = getBatteryStatus(context);
        return status != null ? status.getTemperature() / 10.0 : 0.0; // 转换为摄氏度
    }
    
    /**
     * 检查电池是否过热
     * @param context 应用上下文
     * @return 是否过热
     */
    public boolean isBatteryOverheat(Context context) {
        BatteryStatus status = getBatteryStatus(context);
        if (status == null) {
            return false;
        }
        
        return status.getHealthStatus() == BatteryStatus.HealthStatus.OVERHEAT ||
               status.getTemperature() > 450; // 45度以上认为过热
    }
    
    /**
     * 根据电池状态推荐省电模式
     * @param context 应用上下文
     * @return 推荐的省电模式
     */
    public UnifiedTaskScheduler.PowerSavingMode recommendPowerMode(Context context) {
        BatteryStatus status = getBatteryStatus(context);
        if (status == null) {
            return UnifiedTaskScheduler.PowerSavingMode.NORMAL;
        }
        
        int batteryLevel = status.getBatteryLevel();
        boolean isCharging = status.isCharging();
        
        // 充电时可以使用正常模式
        if (isCharging && batteryLevel > 20) {
            return UnifiedTaskScheduler.PowerSavingMode.NORMAL;
        }
        
        // 根据电量推荐模式
        if (batteryLevel < 5) {
            return UnifiedTaskScheduler.PowerSavingMode.EMERGENCY;
        } else if (batteryLevel < 15) {
            return UnifiedTaskScheduler.PowerSavingMode.ULTRA_SAVE;
        } else if (batteryLevel < 30) {
            return UnifiedTaskScheduler.PowerSavingMode.ECO;
        } else {
            return UnifiedTaskScheduler.PowerSavingMode.NORMAL;
        }
    }
    
    /**
     * 电池状态信息类
     */
    public static class BatteryStatus {
        public enum ChargingStatus {
            CHARGING("充电中"),
            DISCHARGING("放电中"),
            NOT_CHARGING("未充电"),
            FULL("充满"),
            UNKNOWN("未知");
            
            private final String displayName;
            ChargingStatus(String displayName) { this.displayName = displayName; }
            public String getDisplayName() { return displayName; }
        }
        
        public enum HealthStatus {
            GOOD("良好"),
            OVERHEAT("过热"),
            OVER_VOLTAGE("过压"),
            COLD("过冷"),
            UNKNOWN("未知");
            
            private final String displayName;
            HealthStatus(String displayName) { this.displayName = displayName; }
            public String getDisplayName() { return displayName; }
        }
        
        private final int batteryLevel;      // 电量百分比 (0-100)
        private final boolean isCharging;    // 是否正在充电
        private final ChargingStatus chargingStatus; // 详细充电状态
        private final int temperature;       // 电池温度 (0.1度为单位)
        private final HealthStatus healthStatus; // 电池健康状态
        private final long timestamp;        // 状态时间戳
        
        public BatteryStatus(int batteryLevel, boolean isCharging, ChargingStatus chargingStatus,
                           int temperature, HealthStatus healthStatus) {
            this.batteryLevel = batteryLevel;
            this.isCharging = isCharging;
            this.chargingStatus = chargingStatus;
            this.temperature = temperature;
            this.healthStatus = healthStatus;
            this.timestamp = System.currentTimeMillis();
        }
        
        // Getter方法
        public int getBatteryLevel() { return batteryLevel; }
        public boolean isCharging() { return isCharging; }
        public ChargingStatus getChargingStatus() { return chargingStatus; }
        public int getTemperature() { return temperature; }
        public HealthStatus getHealthStatus() { return healthStatus; }
        public long getTimestamp() { return timestamp; }
        
        /**
         * 检查状态是否过期
         * @param maxAge 最大有效期(毫秒)
         * @return 是否过期
         */
        public boolean isStale(long maxAge) {
            return System.currentTimeMillis() - timestamp > maxAge;
        }
        
        @Override
        public String toString() {
            return String.format("BatteryStatus{level=%d%%, charging=%s, status=%s, temp=%.1f°C, health=%s}",
                               batteryLevel, isCharging, chargingStatus.getDisplayName(), 
                               temperature / 10.0, healthStatus.getDisplayName());
        }
    }
}