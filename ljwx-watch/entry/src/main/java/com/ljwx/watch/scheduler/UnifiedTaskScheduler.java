package com.ljwx.watch.scheduler;

import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.locks.ReentrantLock;
import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import ohos.batterymanager.BatteryInfo;
import ohos.batterymanager.BatteryManager;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;

/**
 * 统一定时任务调度器
 * 集中管理所有定时任务，实现智能调度和电池续航优化
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class UnifiedTaskScheduler {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "TaskScheduler");
    
    private static UnifiedTaskScheduler instance;
    private static final ReentrantLock instanceLock = new ReentrantLock();
    
    // 核心组件
    private Timer masterTimer;
    private NetworkStateManager networkStateManager;
    private DataManager dataManager;
    private DeviceStateMonitor deviceStateMonitor;
    private BatteryMonitor batteryMonitor;
    
    // 调度配置
    private static final int MASTER_INTERVAL = 30; // 主定时器30秒周期
    private long globalTick = 0;
    
    // 任务注册表
    private Map<String, ScheduledTask> registeredTasks = new HashMap<>();
    private Map<String, TaskExecutionInfo> taskExecutionHistory = new HashMap<>();
    
    // 状态监听器
    private List<TaskSchedulerListener> listeners = new ArrayList<>();
    
    /**
     * 任务优先级定义
     */
    public enum TaskPriority {
        CRITICAL(1, "关键任务"),      // 关键任务：心率、血氧等生命体征
        HIGH(5, "高优先级"),          // 高优先级：体温、压力等健康指标  
        MEDIUM(30, "中等优先级"),      // 中等优先级：步数、卡路里等运动数据
        LOW(300, "低优先级");         // 低优先级：设备信息上传、消息获取等

        private final int baseInterval; // 基础间隔(秒)
        private final String displayName;

        TaskPriority(int baseInterval, String displayName) {
            this.baseInterval = baseInterval;
            this.displayName = displayName;
        }

        public int getBaseInterval() { return baseInterval; }
        public String getDisplayName() { return displayName; }
    }

    /**
     * 设备状态枚举
     */
    public enum DeviceState {
        ACTIVE_WEARING("活跃佩戴状态"),     // 活跃佩戴状态
        PASSIVE_WEARING("静止佩戴状态"),    // 静止佩戴状态
        NOT_WEARING("未佩戴状态"),          // 未佩戴状态
        CHARGING("充电状态"),              // 充电状态
        LOW_BATTERY("低电量状态");          // 低电量状态

        private final String displayName;

        DeviceState(String displayName) {
            this.displayName = displayName;
        }

        public String getDisplayName() { return displayName; }
    }

    /**
     * 电池省电模式
     */
    public enum PowerSavingMode {
        NORMAL(1.0, "正常模式"),        // 正常模式
        ECO(2.0, "节能模式"),          // 节能模式：频率降低2倍
        ULTRA_SAVE(5.0, "超级节能"),   // 超级节能：频率降低5倍
        EMERGENCY(10.0, "紧急模式");   // 紧急模式：频率降低10倍

        private final double multiplier;
        private final String displayName;

        PowerSavingMode(double multiplier, String displayName) {
            this.multiplier = multiplier;
            this.displayName = displayName;
        }

        public double getMultiplier() { return multiplier; }
        public String getDisplayName() { return displayName; }
    }

    /**
     * 任务调度监听器接口
     */
    public interface TaskSchedulerListener {
        void onTaskExecuted(String taskId, boolean success, long executionTime);
        void onSchedulerStateChanged(boolean running);
        void onPowerModeChanged(PowerSavingMode oldMode, PowerSavingMode newMode);
    }

    private UnifiedTaskScheduler() {
        networkStateManager = NetworkStateManager.getInstance();
        dataManager = DataManager.getInstance();
        deviceStateMonitor = new DeviceStateMonitor();
        batteryMonitor = new BatteryMonitor();
        
        HiLog.info(LABEL_LOG, "UnifiedTaskScheduler初始化完成");
    }

    /**
     * 获取单例实例 - 线程安全
     */
    public static UnifiedTaskScheduler getInstance() {
        if (instance == null) {
            instanceLock.lock();
            try {
                if (instance == null) {
                    instance = new UnifiedTaskScheduler();
                }
            } finally {
                instanceLock.unlock();
            }
        }
        return instance;
    }

    /**
     * 启动统一调度器
     */
    public void startScheduler() {
        if (masterTimer != null) {
            HiLog.warn(LABEL_LOG, "调度器已经在运行中");
            return;
        }

        HiLog.info(LABEL_LOG, "启动统一任务调度器，周期: " + MASTER_INTERVAL + "秒");
        
        masterTimer = new Timer("UnifiedTaskScheduler");
        
        masterTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                try {
                    globalTick++;
                    executeScheduledTasks();
                    
                    // 防止计数器溢出，每天重置
                    if (globalTick >= 2880) { // 24小时 * 60分钟 / 30秒
                        globalTick = 0;
                        HiLog.info(LABEL_LOG, "全局计数器重置");
                    }
                } catch (Exception e) {
                    HiLog.error(LABEL_LOG, "调度器执行异常: " + e.getMessage());
                    e.printStackTrace();
                }
            }
        }, 0, MASTER_INTERVAL * 1000);

        notifySchedulerStateChanged(true);
        HiLog.info(LABEL_LOG, "统一任务调度器启动成功");
    }

    /**
     * 停止统一调度器
     */
    public void stopScheduler() {
        if (masterTimer != null) {
            masterTimer.cancel();
            masterTimer = null;
            notifySchedulerStateChanged(false);
            HiLog.info(LABEL_LOG, "统一任务调度器已停止");
        }
    }

    /**
     * 注册定时任务
     */
    public void registerTask(String taskId, ScheduledTask task) {
        if (taskId == null || task == null) {
            HiLog.error(LABEL_LOG, "任务ID或任务对象不能为空");
            return;
        }

        registeredTasks.put(taskId, task);
        taskExecutionHistory.put(taskId, new TaskExecutionInfo(taskId));
        
        HiLog.info(LABEL_LOG, "注册任务: " + taskId + ", 优先级: " + task.getPriority().getDisplayName() + 
                             ", 基础间隔: " + task.getBaseInterval() + "秒");
    }

    /**
     * 注销定时任务
     */
    public void unregisterTask(String taskId) {
        if (registeredTasks.remove(taskId) != null) {
            taskExecutionHistory.remove(taskId);
            HiLog.info(LABEL_LOG, "注销任务: " + taskId);
        }
    }

    /**
     * 暂停指定任务
     */
    public void suspendTask(String taskId) {
        ScheduledTask task = registeredTasks.get(taskId);
        if (task != null) {
            task.setSuspended(true);
            HiLog.info(LABEL_LOG, "暂停任务: " + taskId);
        }
    }

    /**
     * 恢复指定任务
     */
    public void resumeTask(String taskId) {
        ScheduledTask task = registeredTasks.get(taskId);
        if (task != null) {
            task.setSuspended(false);
            HiLog.info(LABEL_LOG, "恢复任务: " + taskId);
        }
    }

    /**
     * 执行所有已注册的定时任务
     */
    private void executeScheduledTasks() {
        Context context = getContext();
        if (context == null) {
            HiLog.warn(LABEL_LOG, "上下文为空，跳过任务执行");
            return;
        }

        DeviceState deviceState = deviceStateMonitor.getCurrentState(context);
        int batteryLevel = batteryMonitor.getBatteryLevel(context);
        NetworkStateManager.NetworkState networkState = networkStateManager.getCurrentNetworkState(context);
        PowerSavingMode powerMode = determinePowerMode(batteryLevel, deviceState);

        HiLog.debug(LABEL_LOG, String.format("执行调度 - 设备状态: %s, 电量: %d%%, 网络: %s, 省电模式: %s", 
                                            deviceState.getDisplayName(), batteryLevel, 
                                            networkState.getDisplayName(), powerMode.getDisplayName()));

        int executedTaskCount = 0;
        int skippedTaskCount = 0;

        for (Map.Entry<String, ScheduledTask> entry : registeredTasks.entrySet()) {
            String taskId = entry.getKey();
            ScheduledTask task = entry.getValue();

            if (shouldExecuteTask(task, deviceState, batteryLevel, networkState, powerMode)) {
                long startTime = System.currentTimeMillis();
                boolean success = executeTask(taskId, task, context);
                long executionTime = System.currentTimeMillis() - startTime;

                // 更新执行历史
                TaskExecutionInfo executionInfo = taskExecutionHistory.get(taskId);
                if (executionInfo != null) {
                    executionInfo.recordExecution(success, executionTime);
                }

                // 通知监听器
                notifyTaskExecuted(taskId, success, executionTime);

                executedTaskCount++;
                
                HiLog.debug(LABEL_LOG, String.format("任务执行完成: %s, 成功: %s, 耗时: %dms", 
                                                   taskId, success, executionTime));
            } else {
                skippedTaskCount++;
                HiLog.debug(LABEL_LOG, "跳过任务: " + taskId);
            }
        }

        if (executedTaskCount > 0 || skippedTaskCount > 0) {
            HiLog.debug(LABEL_LOG, String.format("本轮调度完成 - 执行: %d个任务, 跳过: %d个任务", 
                                                executedTaskCount, skippedTaskCount));
        }
    }

    /**
     * 判断是否应该执行任务
     */
    private boolean shouldExecuteTask(ScheduledTask task, DeviceState deviceState,
                                    int batteryLevel, NetworkStateManager.NetworkState networkState,
                                    PowerSavingMode powerMode) {
        
        // 检查任务是否被暂停
        if (task.isSuspended()) {
            return false;
        }

        // 检查任务是否需要网络，如果需要则检查网络状态
        if (task.requiresNetwork() && !networkState.isConnected()) {
            return false;
        }

        // 计算动态执行间隔
        int dynamicInterval = calculateDynamicInterval(task, deviceState, batteryLevel, 
                                                      networkState, powerMode);

        // 转换为tick间隔
        int tickInterval = Math.max(1, dynamicInterval / MASTER_INTERVAL);

        // 检查是否到达执行时间
        return globalTick % tickInterval == 0;
    }

    /**
     * 计算动态任务执行间隔
     */
    private int calculateDynamicInterval(ScheduledTask task, DeviceState deviceState,
                                       int batteryLevel, NetworkStateManager.NetworkState networkState,
                                       PowerSavingMode powerMode) {
        
        int baseInterval = task.getBaseInterval();
        double multiplier = 1.0;

        // 应用省电模式倍数
        multiplier *= powerMode.getMultiplier();

        // 应用任务自定义的动态调整
        multiplier *= task.calculateDynamicMultiplier(deviceState, batteryLevel, networkState);

        // 设备状态调整
        switch (deviceState) {
            case NOT_WEARING:
                if (task.getPriority() == TaskPriority.CRITICAL) {
                    multiplier *= 10.0; // 关键任务降低10倍频率
                } else {
                    multiplier *= 50.0; // 其他任务大幅降低频率
                }
                break;
            case PASSIVE_WEARING:
                multiplier *= 2.0; // 静止佩戴时适度降低频率
                break;
            case CHARGING:
                multiplier *= 0.8; // 充电时可以稍微提高频率
                break;
            case LOW_BATTERY:
                multiplier *= 5.0; // 低电量时大幅降低频率
                break;
        }

        // 电池电量微调
        if (batteryLevel < 10) {
            multiplier *= 3.0; // 极低电量
        } else if (batteryLevel < 20) {
            multiplier *= 2.0; // 低电量
        } else if (batteryLevel < 30) {
            multiplier *= 1.5; // 偏低电量
        }

        // 网络状态调整（仅影响网络任务）
        if (task.requiresNetwork()) {
            if (networkState == NetworkStateManager.NetworkState.OFFLINE) {
                multiplier *= 10.0; // 离线时大幅降低网络任务频率
            } else if (networkState == NetworkStateManager.NetworkState.MOBILE_CONNECTED) {
                multiplier *= 2.0; // 移动网络时适度降低频率
            }
        }

        int finalInterval = (int) (baseInterval * multiplier);
        
        // 确保最小间隔不小于30秒
        return Math.max(30, finalInterval);
    }

    /**
     * 执行具体任务
     */
    private boolean executeTask(String taskId, ScheduledTask task, Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行任务: " + taskId);
            boolean result = task.execute(context);
            
            if (result) {
                HiLog.debug(LABEL_LOG, "任务执行成功: " + taskId);
            } else {
                HiLog.warn(LABEL_LOG, "任务执行失败: " + taskId);
            }
            
            return result;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "任务执行异常: " + taskId + ", " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    /**
     * 确定当前电源管理模式
     */
    private PowerSavingMode determinePowerMode(int batteryLevel, DeviceState deviceState) {
        // 紧急模式：电量<5%
        if (batteryLevel < 5) {
            return PowerSavingMode.EMERGENCY;
        }

        // 超级节能：电量<15%或长时间未佩戴
        if (batteryLevel < 15 || deviceState == DeviceState.NOT_WEARING) {
            return PowerSavingMode.ULTRA_SAVE;
        }

        // 节能模式：电量<30%或静止佩戴
        if (batteryLevel < 30 || deviceState == DeviceState.PASSIVE_WEARING) {
            return PowerSavingMode.ECO;
        }

        return PowerSavingMode.NORMAL;
    }

    /**
     * 获取应用上下文（需要子类实现或依赖注入）
     */
    private Context getContext() {
        // 这里需要根据实际情况获取Context
        // 可以通过依赖注入或其他方式获取
        return null; // TODO: 实现获取Context的逻辑
    }

    /**
     * 添加调度器监听器
     */
    public void addListener(TaskSchedulerListener listener) {
        if (listener != null && !listeners.contains(listener)) {
            listeners.add(listener);
        }
    }

    /**
     * 移除调度器监听器
     */
    public void removeListener(TaskSchedulerListener listener) {
        listeners.remove(listener);
    }

    /**
     * 通知任务执行完成
     */
    private void notifyTaskExecuted(String taskId, boolean success, long executionTime) {
        for (TaskSchedulerListener listener : listeners) {
            try {
                listener.onTaskExecuted(taskId, success, executionTime);
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "通知监听器异常: " + e.getMessage());
            }
        }
    }

    /**
     * 通知调度器状态变化
     */
    private void notifySchedulerStateChanged(boolean running) {
        for (TaskSchedulerListener listener : listeners) {
            try {
                listener.onSchedulerStateChanged(running);
            } catch (Exception e) {
                HiLog.error(LABEL_LOG, "通知调度器状态变化异常: " + e.getMessage());
            }
        }
    }

    /**
     * 获取任务执行统计信息
     */
    public Map<String, TaskExecutionInfo> getTaskExecutionStats() {
        return new HashMap<>(taskExecutionHistory);
    }

    /**
     * 获取调度器运行状态
     */
    public boolean isRunning() {
        return masterTimer != null;
    }

    /**
     * 获取已注册的任务列表
     */
    public Map<String, ScheduledTask> getRegisteredTasks() {
        return new HashMap<>(registeredTasks);
    }

    /**
     * 获取当前全局计数器值
     */
    public long getCurrentTick() {
        return globalTick;
    }

    /**
     * 强制执行指定任务（忽略调度规则）
     */
    public boolean forceExecuteTask(String taskId) {
        ScheduledTask task = registeredTasks.get(taskId);
        if (task == null) {
            HiLog.error(LABEL_LOG, "任务不存在: " + taskId);
            return false;
        }

        Context context = getContext();
        if (context == null) {
            HiLog.error(LABEL_LOG, "上下文为空，无法强制执行任务: " + taskId);
            return false;
        }

        HiLog.info(LABEL_LOG, "强制执行任务: " + taskId);
        long startTime = System.currentTimeMillis();
        boolean success = executeTask(taskId, task, context);
        long executionTime = System.currentTimeMillis() - startTime;

        // 更新执行历史
        TaskExecutionInfo executionInfo = taskExecutionHistory.get(taskId);
        if (executionInfo != null) {
            executionInfo.recordExecution(success, executionTime);
        }

        notifyTaskExecuted(taskId, success, executionTime);
        return success;
    }

    /**
     * 获取调度器状态诊断信息
     */
    public SchedulerDiagnosticInfo getDiagnosticInfo() {
        Context context = getContext();
        DeviceState deviceState = context != null ? deviceStateMonitor.getCurrentState(context) : DeviceState.NOT_WEARING;
        int batteryLevel = context != null ? batteryMonitor.getBatteryLevel(context) : 0;
        NetworkStateManager.NetworkState networkState = context != null ? 
                                                        networkStateManager.getCurrentNetworkState(context) : 
                                                        NetworkStateManager.NetworkState.UNKNOWN;
        PowerSavingMode powerMode = determinePowerMode(batteryLevel, deviceState);

        return new SchedulerDiagnosticInfo(
            isRunning(),
            globalTick,
            registeredTasks.size(),
            deviceState,
            batteryLevel,
            networkState,
            powerMode,
            System.currentTimeMillis()
        );
    }

    /**
     * 调度器诊断信息类
     */
    public static class SchedulerDiagnosticInfo {
        private final boolean running;
        private final long currentTick;
        private final int registeredTaskCount;
        private final DeviceState deviceState;
        private final int batteryLevel;
        private final NetworkStateManager.NetworkState networkState;
        private final PowerSavingMode powerMode;
        private final long timestamp;

        public SchedulerDiagnosticInfo(boolean running, long currentTick, int registeredTaskCount,
                                     DeviceState deviceState, int batteryLevel,
                                     NetworkStateManager.NetworkState networkState,
                                     PowerSavingMode powerMode, long timestamp) {
            this.running = running;
            this.currentTick = currentTick;
            this.registeredTaskCount = registeredTaskCount;
            this.deviceState = deviceState;
            this.batteryLevel = batteryLevel;
            this.networkState = networkState;
            this.powerMode = powerMode;
            this.timestamp = timestamp;
        }

        // Getters
        public boolean isRunning() { return running; }
        public long getCurrentTick() { return currentTick; }
        public int getRegisteredTaskCount() { return registeredTaskCount; }
        public DeviceState getDeviceState() { return deviceState; }
        public int getBatteryLevel() { return batteryLevel; }
        public NetworkStateManager.NetworkState getNetworkState() { return networkState; }
        public PowerSavingMode getPowerMode() { return powerMode; }
        public long getTimestamp() { return timestamp; }

        @Override
        public String toString() {
            return String.format("SchedulerDiagnostic{running=%s, tick=%d, tasks=%d, device=%s, battery=%d%%, network=%s, power=%s}",
                               running, currentTick, registeredTaskCount, deviceState, batteryLevel, networkState, powerMode);
        }
    }
}