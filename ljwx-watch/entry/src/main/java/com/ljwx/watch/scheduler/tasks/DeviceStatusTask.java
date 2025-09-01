package com.ljwx.watch.scheduler.tasks;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.UnifiedTaskScheduler;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;
import com.ljwx.watch.scheduler.BatteryMonitor;

/**
 * 设备状态上报任务
 * 负责定期上报设备状态信息，包括电池、网络、传感器状态等
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class DeviceStatusTask extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "DeviceStatusTask");
    
    private DataManager dataManager;
    private BatteryMonitor batteryMonitor;
    private NetworkStateManager networkStateManager;
    private long lastStatusReportTime = 0;
    
    public DeviceStatusTask() {
        super(
            "deviceStatus", 
            UnifiedTaskScheduler.TaskPriority.MEDIUM, 
            300,    // 5分钟基础间隔
            true    // 需要网络连接
        );
        this.dataManager = DataManager.getInstance();
        this.batteryMonitor = new BatteryMonitor();
        this.networkStateManager = NetworkStateManager.getInstance();
    }
    
    @Override
    public boolean execute(Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行设备状态上报任务");
            
            // 收集设备状态信息
            DeviceStatus deviceStatus = collectDeviceStatus(context);
            if (deviceStatus == null) {
                HiLog.warn(LABEL_LOG, "设备状态收集失败");
                return false;
            }
            
            // 检查是否需要上报（状态有明显变化或者超过最大间隔）
            if (!shouldReportStatus(deviceStatus)) {
                HiLog.debug(LABEL_LOG, "设备状态无显著变化，跳过本次上报");
                return true;
            }
            
            // 上报设备状态
            boolean reportSuccess = reportDeviceStatus(deviceStatus);
            
            if (reportSuccess) {
                lastStatusReportTime = System.currentTimeMillis();
                HiLog.info(LABEL_LOG, "设备状态上报成功");
                return true;
            } else {
                HiLog.warn(LABEL_LOG, "设备状态上报失败");
                return false;
            }
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "设备状态上报任务执行异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * 收集设备状态信息
     * @param context 应用上下文
     * @return 设备状态信息
     */
    private DeviceStatus collectDeviceStatus(Context context) {
        try {
            // 收集电池状态
            BatteryMonitor.BatteryStatus batteryStatus = batteryMonitor.getBatteryStatus(context);
            
            // 收集网络状态
            NetworkStateManager.NetworkState networkState = networkStateManager.getCurrentNetworkState();
            
            // 收集传感器状态
            int wearState = dataManager.getWearState();
            
            // 收集系统信息
            long freeMemory = Runtime.getRuntime().freeMemory();
            long totalMemory = Runtime.getRuntime().totalMemory();
            int memoryUsagePercent = (int) ((totalMemory - freeMemory) * 100 / totalMemory);
            
            // 收集应用运行时间
            long currentTime = System.currentTimeMillis();
            long appStartTime = dataManager.getAppStartTime();
            long runningTime = currentTime - appStartTime;
            
            return new DeviceStatus(
                dataManager.getDeviceSN(),
                currentTime,
                batteryStatus,
                networkState,
                wearState,
                memoryUsagePercent,
                runningTime,
                getAppVersion()
            );
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "收集设备状态异常: " + e.getMessage());
            return null;
        }
    }
    
    /**
     * 检查是否需要上报状态
     * @param currentStatus 当前状态
     * @return 是否需要上报
     */
    private boolean shouldReportStatus(DeviceStatus currentStatus) {
        // 首次上报
        if (lastStatusReportTime == 0) {
            return true;
        }
        
        // 超过最大间隔（30分钟）必须上报
        long timeSinceLastReport = System.currentTimeMillis() - lastStatusReportTime;
        if (timeSinceLastReport > 30 * 60 * 1000) { // 30分钟
            HiLog.debug(LABEL_LOG, "距离上次上报超过30分钟，强制上报");
            return true;
        }
        
        // TODO: 实现状态变化检测逻辑
        // 比较与上次状态的差异，如电量变化超过10%、网络状态变化等
        
        return false;
    }
    
    /**
     * 上报设备状态到服务器
     * @param deviceStatus 设备状态
     * @return 上报是否成功
     */
    private boolean reportDeviceStatus(DeviceStatus deviceStatus) {
        try {
            // 构建上报数据JSON
            String statusJson = deviceStatus.toJson();
            
            HiLog.debug(LABEL_LOG, "上报设备状态: " + statusJson);
            
            // TODO: 使用HttpService上报状态数据
            // 这里应该调用实际的HTTP上报逻辑
            
            // 模拟上报过程
            boolean success = Math.random() > 0.1; // 90%成功率
            
            if (success) {
                HiLog.info(LABEL_LOG, "设备状态上报到服务器成功");
            } else {
                HiLog.warn(LABEL_LOG, "设备状态上报到服务器失败");
            }
            
            return success;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "上报设备状态异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 获取应用版本
     * @return 应用版本号
     */
    private String getAppVersion() {
        // TODO: 获取实际的应用版本号
        return "1.0.0";
    }
    
    @Override
    public double calculateDynamicMultiplier(UnifiedTaskScheduler.DeviceState deviceState,
                                           int batteryLevel,
                                           NetworkStateManager.NetworkState networkState) {
        double multiplier = 1.0;
        
        // 网络状态影响
        if (!networkState.isConnected()) {
            return 10.0; // 无网络时大幅延长间隔
        }
        
        // 设备状态影响
        switch (deviceState) {
            case NOT_WEARING:
                multiplier *= 3.0; // 未佩戴时减少上报频率
                break;
            case PASSIVE_WEARING:
                multiplier *= 1.5; // 静止时适度减少
                break;
            case ACTIVE_WEARING:
                multiplier *= 1.0; // 活跃时保持正常
                break;
            case CHARGING:
                multiplier *= 0.5; // 充电时可以更频繁上报
                break;
            case LOW_BATTERY:
                multiplier *= 2.0; // 低电量时减少频率，但仍需要上报电池状态
                break;
        }
        
        // 电量影响
        if (batteryLevel < 10) {
            multiplier *= 2.0; // 低电量时减少频率，但需要保持状态上报
        } else if (batteryLevel < 20) {
            multiplier *= 1.5;
        }
        
        return multiplier;
    }
    
    @Override
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 必须有网络连接
        if (!networkState.isConnected()) {
            HiLog.debug(LABEL_LOG, "网络未连接，跳过设备状态上报");
            return false;
        }
        
        // 即使是极低电量也需要上报电池状态
        return true;
    }
    
    @Override
    protected boolean prepare(Context context) {
        try {
            // 检查网络连接状态
            NetworkStateManager.NetworkState networkState = networkStateManager.getCurrentNetworkState();
            
            if (!networkState.isConnected()) {
                HiLog.debug(LABEL_LOG, "网络未连接，跳过设备状态上报准备");
                return false;
            }
            
            HiLog.debug(LABEL_LOG, "设备状态上报任务准备完成");
            return true;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "设备状态上报任务准备失败: " + e.getMessage());
            return false;
        }
    }
    
    @Override
    protected void cleanup(Context context, boolean success) {
        try {
            if (!success) {
                HiLog.warn(LABEL_LOG, "设备状态上报失败，将在下次调度时重试");
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "设备状态上报任务清理异常: " + e.getMessage());
        }
    }
    
    /**
     * 设备状态信息类
     */
    private static class DeviceStatus {
        private final String deviceSn;
        private final long timestamp;
        private final BatteryMonitor.BatteryStatus batteryStatus;
        private final NetworkStateManager.NetworkState networkState;
        private final int wearState;
        private final int memoryUsagePercent;
        private final long runningTime;
        private final String appVersion;
        
        public DeviceStatus(String deviceSn, long timestamp, 
                          BatteryMonitor.BatteryStatus batteryStatus,
                          NetworkStateManager.NetworkState networkState,
                          int wearState, int memoryUsagePercent, 
                          long runningTime, String appVersion) {
            this.deviceSn = deviceSn;
            this.timestamp = timestamp;
            this.batteryStatus = batteryStatus;
            this.networkState = networkState;
            this.wearState = wearState;
            this.memoryUsagePercent = memoryUsagePercent;
            this.runningTime = runningTime;
            this.appVersion = appVersion;
        }
        
        /**
         * 转换为JSON字符串
         * @return JSON字符串
         */
        public String toJson() {
            StringBuilder jsonBuilder = new StringBuilder();
            jsonBuilder.append("{");
            jsonBuilder.append("\"deviceSn\":\"").append(deviceSn).append("\",");
            jsonBuilder.append("\"timestamp\":").append(timestamp).append(",");
            jsonBuilder.append("\"batteryLevel\":").append(batteryStatus.getBatteryLevel()).append(",");
            jsonBuilder.append("\"isCharging\":").append(batteryStatus.isCharging()).append(",");
            jsonBuilder.append("\"batteryTemperature\":").append(batteryStatus.getTemperature() / 10.0).append(",");
            jsonBuilder.append("\"networkState\":\"").append(networkState.name()).append("\",");
            jsonBuilder.append("\"wearState\":").append(wearState).append(",");
            jsonBuilder.append("\"memoryUsage\":").append(memoryUsagePercent).append(",");
            jsonBuilder.append("\"runningTime\":").append(runningTime).append(",");
            jsonBuilder.append("\"appVersion\":\"").append(appVersion).append("\",");
            jsonBuilder.append("\"reportType\":\"device_status\"");
            jsonBuilder.append("}");
            
            return jsonBuilder.toString();
        }
    }
}