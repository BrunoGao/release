package com.ljwx.watch.scheduler;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.utils.DataManager;

/**
 * 设备状态监控器
 * 负责监控设备的佩戴状态、活动状态等
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class DeviceStateMonitor {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "DeviceStateMonitor");
    
    private DataManager dataManager;
    
    // 状态缓存
    private UnifiedTaskScheduler.DeviceState cachedState = UnifiedTaskScheduler.DeviceState.NOT_WEARING;
    private long lastStateCheckTime = 0;
    private static final long STATE_CACHE_DURATION = 30000; // 30秒缓存
    
    // 活动检测相关
    private int lastStepCount = 0;
    private long lastActivityCheckTime = 0;
    private static final long ACTIVITY_CHECK_INTERVAL = 60000; // 1分钟检测间隔
    private static final int ACTIVITY_THRESHOLD = 10; // 活动阈值：每分钟步数
    
    public DeviceStateMonitor() {
        dataManager = DataManager.getInstance();
    }
    
    /**
     * 获取当前设备状态
     * @param context 应用上下文
     * @return 设备状态
     */
    public UnifiedTaskScheduler.DeviceState getCurrentState(Context context) {
        long currentTime = System.currentTimeMillis();
        
        // 检查缓存有效性
        if (currentTime - lastStateCheckTime < STATE_CACHE_DURATION) {
            return cachedState;
        }
        
        // 重新检测设备状态
        UnifiedTaskScheduler.DeviceState newState = detectDeviceState(context);
        
        // 状态变化时记录日志
        if (newState != cachedState) {
            HiLog.info(LABEL_LOG, "设备状态变化: " + cachedState.getDisplayName() + " -> " + newState.getDisplayName());
        }
        
        cachedState = newState;
        lastStateCheckTime = currentTime;
        
        return cachedState;
    }
    
    /**
     * 检测设备状态的核心逻辑
     * @param context 应用上下文
     * @return 检测到的设备状态
     */
    private UnifiedTaskScheduler.DeviceState detectDeviceState(Context context) {
        try {
            // 1. 检查充电状态
            if (isCharging(context)) {
                HiLog.debug(LABEL_LOG, "检测到充电状态");
                return UnifiedTaskScheduler.DeviceState.CHARGING;
            }
            
            // 2. 检查电量状态
            if (isBatteryLow(context)) {
                HiLog.debug(LABEL_LOG, "检测到低电量状态");
                return UnifiedTaskScheduler.DeviceState.LOW_BATTERY;
            }
            
            // 3. 检查佩戴状态
            if (!isWearing()) {
                HiLog.debug(LABEL_LOG, "检测到未佩戴状态");
                return UnifiedTaskScheduler.DeviceState.NOT_WEARING;
            }
            
            // 4. 检查活动状态
            if (isActivelyWearing()) {
                HiLog.debug(LABEL_LOG, "检测到活跃佩戴状态");
                return UnifiedTaskScheduler.DeviceState.ACTIVE_WEARING;
            } else {
                HiLog.debug(LABEL_LOG, "检测到静止佩戴状态");
                return UnifiedTaskScheduler.DeviceState.PASSIVE_WEARING;
            }
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "设备状态检测异常: " + e.getMessage());
            return UnifiedTaskScheduler.DeviceState.NOT_WEARING; // 异常时默认未佩戴
        }
    }
    
    /**
     * 检查是否正在充电
     * @param context 应用上下文
     * @return 是否在充电
     */
    private boolean isCharging(Context context) {
        try {
            // 这里需要根据HarmonyOS的实际API来检查充电状态
            // 示例代码，需要根据实际API调整
            return false; // TODO: 实现充电状态检测
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "充电状态检测异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 检查电量是否过低
     * @param context 应用上下文
     * @return 是否低电量
     */
    private boolean isBatteryLow(Context context) {
        try {
            // 这里需要根据HarmonyOS的实际API来检查电量
            // 示例：电量低于20%认为是低电量状态
            return false; // TODO: 实现电量检测
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "电量状态检测异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 检查是否正在佩戴
     * @return 是否佩戴
     */
    private boolean isWearing() {
        try {
            // 从DataManager获取佩戴状态
            int wearState = dataManager.getWearState();
            
            // wearState: 0-未佩戴, 1-已佩戴
            boolean wearing = wearState == 1;
            
            HiLog.debug(LABEL_LOG, "佩戴状态检测: wearState=" + wearState + ", wearing=" + wearing);
            return wearing;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "佩戴状态检测异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 检查是否处于活跃佩戴状态
     * @return 是否活跃佩戴
     */
    private boolean isActivelyWearing() {
        try {
            long currentTime = System.currentTimeMillis();
            
            // 如果距离上次检测时间不足1分钟，使用缓存结果
            if (currentTime - lastActivityCheckTime < ACTIVITY_CHECK_INTERVAL) {
                // 根据历史数据判断，这里简化为检查步数变化
                return isRecentActivityDetected();
            }
            
            // 获取当前步数
            int currentStepCount = dataManager.getStep();
            
            // 计算步数变化
            int stepDiff = currentStepCount - lastStepCount;
            boolean isActive = stepDiff >= ACTIVITY_THRESHOLD;
            
            HiLog.debug(LABEL_LOG, String.format("活动状态检测: 当前步数=%d, 上次步数=%d, 变化=%d, 活跃=%s", 
                                                currentStepCount, lastStepCount, stepDiff, isActive));
            
            // 更新记录
            lastStepCount = currentStepCount;
            lastActivityCheckTime = currentTime;
            
            return isActive;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "活动状态检测异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 检查是否有近期活动
     * @return 是否有近期活动
     */
    private boolean isRecentActivityDetected() {
        try {
            // 检查心率变化 - 活跃时心率通常会有变化
            int heartRate = dataManager.getHeartRate();
            if (heartRate > 80) { // 心率较高，可能在活动
                return true;
            }
            
            // 检查压力水平 - 活动时压力可能会变化
            int stress = dataManager.getStress();
            if (stress > 50) { // 压力较高，可能在活动
                return true;
            }
            
            // 可以添加更多的活动检测指标
            return false;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "近期活动检测异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 获取详细的设备状态信息
     * @param context 应用上下文
     * @return 设备状态详细信息
     */
    public DeviceStateInfo getDetailedState(Context context) {
        UnifiedTaskScheduler.DeviceState currentState = getCurrentState(context);
        
        return new DeviceStateInfo(
            currentState,
            isWearing(),
            isActivelyWearing(),
            isCharging(context),
            isBatteryLow(context),
            dataManager.getWearState(),
            dataManager.getStep(),
            dataManager.getHeartRate(),
            dataManager.getStress(),
            System.currentTimeMillis()
        );
    }
    
    /**
     * 强制刷新设备状态（清除缓存）
     * @param context 应用上下文
     * @return 新的设备状态
     */
    public UnifiedTaskScheduler.DeviceState refreshState(Context context) {
        lastStateCheckTime = 0; // 清除缓存时间
        return getCurrentState(context);
    }
    
    /**
     * 设备状态详细信息类
     */
    public static class DeviceStateInfo {
        private final UnifiedTaskScheduler.DeviceState deviceState;
        private final boolean wearing;
        private final boolean activelyWearing;
        private final boolean charging;
        private final boolean batteryLow;
        private final int wearStateValue;
        private final int stepCount;
        private final int heartRate;
        private final int stress;
        private final long timestamp;
        
        public DeviceStateInfo(UnifiedTaskScheduler.DeviceState deviceState, boolean wearing, 
                             boolean activelyWearing, boolean charging, boolean batteryLow,
                             int wearStateValue, int stepCount, int heartRate, int stress, long timestamp) {
            this.deviceState = deviceState;
            this.wearing = wearing;
            this.activelyWearing = activelyWearing;
            this.charging = charging;
            this.batteryLow = batteryLow;
            this.wearStateValue = wearStateValue;
            this.stepCount = stepCount;
            this.heartRate = heartRate;
            this.stress = stress;
            this.timestamp = timestamp;
        }
        
        // Getter方法
        public UnifiedTaskScheduler.DeviceState getDeviceState() { return deviceState; }
        public boolean isWearing() { return wearing; }
        public boolean isActivelyWearing() { return activelyWearing; }
        public boolean isCharging() { return charging; }
        public boolean isBatteryLow() { return batteryLow; }
        public int getWearStateValue() { return wearStateValue; }
        public int getStepCount() { return stepCount; }
        public int getHeartRate() { return heartRate; }
        public int getStress() { return stress; }
        public long getTimestamp() { return timestamp; }
        
        @Override
        public String toString() {
            return String.format("DeviceStateInfo{state=%s, wearing=%s, active=%s, charging=%s, lowBattery=%s, steps=%d, hr=%d, stress=%d}",
                               deviceState, wearing, activelyWearing, charging, batteryLow, stepCount, heartRate, stress);
        }
    }
}