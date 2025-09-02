package com.ljwx.watch.scheduler;

import ohos.app.Context;
import com.ljwx.watch.network.NetworkStateManager;

/**
 * 定时任务抽象基类
 * 所有需要被统一调度器管理的任务都应该继承此类
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public abstract class ScheduledTask {
    
    // 任务基本属性
    private final String taskId;
    private final UnifiedTaskScheduler.TaskPriority priority;
    private final int baseInterval; // 基础执行间隔(秒)
    private final boolean requiresNetwork; // 是否需要网络连接
    
    // 任务状态
    private boolean suspended = false;
    private long lastExecutionTime = 0;
    private int executionCount = 0;
    
    /**
     * 构造函数
     * @param taskId 任务ID
     * @param priority 任务优先级
     * @param baseInterval 基础执行间隔(秒)
     * @param requiresNetwork 是否需要网络连接
     */
    public ScheduledTask(String taskId, UnifiedTaskScheduler.TaskPriority priority, 
                        int baseInterval, boolean requiresNetwork) {
        this.taskId = taskId;
        this.priority = priority;
        this.baseInterval = baseInterval;
        this.requiresNetwork = requiresNetwork;
    }
    
    /**
     * 任务执行方法 - 子类必须实现
     * @param context 应用上下文
     * @return 执行是否成功
     */
    public abstract boolean execute(Context context);
    
    /**
     * 计算动态调整倍数 - 子类可以重写以实现自定义调整逻辑
     * @param deviceState 设备状态
     * @param batteryLevel 电池电量百分比
     * @param networkState 网络状态
     * @return 调整倍数 (1.0表示不调整)
     */
    public double calculateDynamicMultiplier(UnifiedTaskScheduler.DeviceState deviceState,
                                           int batteryLevel,
                                           NetworkStateManager.NetworkState networkState) {
        return 1.0; // 默认不调整，子类可重写
    }
    
    /**
     * 判断当前条件下任务是否应该被执行 - 子类可以重写
     * @param deviceState 设备状态
     * @param batteryLevel 电池电量百分比
     * @param networkState 网络状态
     * @return 是否应该执行
     */
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 默认逻辑：网络任务需要网络连接
        if (requiresNetwork && !networkState.isConnected()) {
            return false;
        }
        
        // 默认逻辑：电量极低时暂停非关键任务
        if (batteryLevel < 5 && priority != UnifiedTaskScheduler.TaskPriority.CRITICAL) {
            return false;
        }
        
        return true;
    }
    
    /**
     * 任务执行前的准备工作 - 子类可以重写
     * @param context 应用上下文
     * @return 准备是否成功
     */
    protected boolean prepare(Context context) {
        return true; // 默认总是准备成功
    }
    
    /**
     * 任务执行后的清理工作 - 子类可以重写
     * @param context 应用上下文
     * @param success 任务执行是否成功
     */
    protected void cleanup(Context context, boolean success) {
        // 默认不执行任何清理工作
    }
    
    /**
     * 最终执行方法（带准备和清理）
     * @param context 应用上下文
     * @return 执行是否成功
     */
    public final boolean executeWithLifecycle(Context context) {
        if (suspended) {
            return false;
        }
        
        boolean prepared = false;
        boolean executed = false;
        
        try {
            // 准备阶段
            prepared = prepare(context);
            if (!prepared) {
                return false;
            }
            
            // 记录执行信息
            lastExecutionTime = System.currentTimeMillis();
            executionCount++;
            
            // 执行任务
            executed = execute(context);
            
            return executed;
        } finally {
            // 清理阶段
            if (prepared) {
                cleanup(context, executed);
            }
        }
    }
    
    // Getter方法
    public String getTaskId() { return taskId; }
    public UnifiedTaskScheduler.TaskPriority getPriority() { return priority; }
    public int getBaseInterval() { return baseInterval; }
    public boolean requiresNetwork() { return requiresNetwork; }
    public boolean isSuspended() { return suspended; }
    public long getLastExecutionTime() { return lastExecutionTime; }
    public int getExecutionCount() { return executionCount; }
    
    // Setter方法
    public void setSuspended(boolean suspended) { this.suspended = suspended; }
    
    /**
     * 获取任务描述
     * @return 任务描述字符串
     */
    public String getDescription() {
        return String.format("Task[%s] - Priority: %s, Interval: %ds, Network: %s, Executions: %d",
                           taskId, priority.getDisplayName(), baseInterval, requiresNetwork, executionCount);
    }
    
    /**
     * 重置执行统计
     */
    public void resetExecutionStats() {
        lastExecutionTime = 0;
        executionCount = 0;
    }
    
    /**
     * 检查任务是否过期未执行
     * @param maxIdleTime 最大空闲时间(毫秒)
     * @return 是否过期
     */
    public boolean isExpired(long maxIdleTime) {
        if (lastExecutionTime == 0) {
            return false; // 从未执行过，不算过期
        }
        
        return System.currentTimeMillis() - lastExecutionTime > maxIdleTime;
    }
    
    @Override
    public String toString() {
        return getDescription();
    }
    
    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        
        ScheduledTask that = (ScheduledTask) obj;
        return taskId.equals(that.taskId);
    }
    
    @Override
    public int hashCode() {
        return taskId.hashCode();
    }
}