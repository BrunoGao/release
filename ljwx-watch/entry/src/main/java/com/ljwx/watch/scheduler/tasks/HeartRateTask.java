package com.ljwx.watch.scheduler.tasks;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.UnifiedTaskScheduler;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;

/**
 * 心率监测任务
 * 关键任务，优先级最高，负责定期采集心率数据
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class HeartRateTask extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "HeartRateTask");
    
    private DataManager dataManager;
    private int lastHeartRate = 0;
    private long lastValidReadingTime = 0;
    
    public HeartRateTask() {
        super(
            "heartRate", 
            UnifiedTaskScheduler.TaskPriority.CRITICAL, 
            5,      // 5秒基础间隔
            false   // 不需要网络连接
        );
        this.dataManager = DataManager.getInstance();
    }
    
    @Override
    public boolean execute(Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行心率监测任务");
            
            // 读取当前心率
            int currentHeartRate = readHeartRate();
            
            // 验证心率数据有效性
            if (isValidHeartRate(currentHeartRate)) {
                // 更新DataManager中的心率数据
                dataManager.setHeartRate(currentHeartRate);
                lastHeartRate = currentHeartRate;
                lastValidReadingTime = System.currentTimeMillis();
                
                HiLog.info(LABEL_LOG, "心率监测成功: " + currentHeartRate + " bpm");
                
                // 检查心率异常
                checkHeartRateAlert(currentHeartRate);
                
                return true;
            } else {
                HiLog.warn(LABEL_LOG, "心率数据无效: " + currentHeartRate);
                
                // 如果连续多次读取失败，可能需要特殊处理
                if (System.currentTimeMillis() - lastValidReadingTime > 300000) { // 5分钟
                    HiLog.error(LABEL_LOG, "心率监测长时间失败，可能需要检查传感器");
                    // 可以触发传感器重新初始化或用户提醒
                }
                
                return false;
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "心率监测任务执行异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * 读取心率数据的具体实现
     * @return 心率值 (bpm)
     */
    private int readHeartRate() {
        try {
            // 这里应该调用实际的心率传感器API
            // 示例实现：从DataManager获取当前心率（可能来自传感器回调）
            int heartRate = dataManager.getHeartRate();
            
            // 如果DataManager中的心率为0或异常值，可能需要主动读取传感器
            if (heartRate == 0 || heartRate == 1000) {
                // 调用传感器读取接口
                heartRate = readFromHeartRateSensor();
            }
            
            return heartRate;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "读取心率数据异常: " + e.getMessage());
            return 0;
        }
    }
    
    /**
     * 从心率传感器读取数据
     * @return 心率值
     */
    private int readFromHeartRateSensor() {
        try {
            // TODO: 实现实际的传感器读取逻辑
            // 这里需要根据具体的硬件接口实现
            
            // 模拟心率读取（实际实现中应该调用硬件API）
            // 返回一个合理的心率值用于测试
            if (lastHeartRate > 0) {
                // 基于上次心率值生成一个小幅波动的值
                int variation = (int) (Math.random() * 10 - 5); // -5到+5的随机变化
                return Math.max(50, Math.min(150, lastHeartRate + variation));
            } else {
                // 首次读取，返回一个正常范围内的值
                return 72 + (int) (Math.random() * 16); // 72-88之间
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "传感器读取异常: " + e.getMessage());
            return 0;
        }
    }
    
    /**
     * 验证心率数据是否有效
     * @param heartRate 心率值
     * @return 是否有效
     */
    private boolean isValidHeartRate(int heartRate) {
        // 心率正常范围：40-200 bpm
        if (heartRate < 40 || heartRate > 200) {
            return false;
        }
        
        // 检查与上次心率的差异是否过大
        if (lastHeartRate > 0) {
            int difference = Math.abs(heartRate - lastHeartRate);
            if (difference > 50) { // 心率变化超过50 bpm认为异常
                HiLog.warn(LABEL_LOG, "心率变化过大: " + lastHeartRate + " -> " + heartRate);
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 检查心率告警
     * @param heartRate 当前心率
     */
    private void checkHeartRateAlert(int heartRate) {
        try {
            int highThreshold = dataManager.getHeartRateWarningHigh();
            int lowThreshold = dataManager.getHeartRateWarningLow();
            
            boolean isHigh = (highThreshold > 0 && heartRate > highThreshold);
            boolean isLow = (lowThreshold > 0 && heartRate < lowThreshold);
            
            if (isHigh || isLow) {
                String alertType = isHigh ? "心率过高" : "心率过低";
                String alertMessage = String.format("%s告警: 当前心率 %d bpm, 阈值: %d-%d bpm", 
                                                   alertType, heartRate, lowThreshold, highThreshold);
                
                HiLog.warn(LABEL_LOG, alertMessage);
                
                // 设置心率超限标志
                dataManager.setIsheartRateExceeded(true);
                
                // 触发告警事件（可以通过DataManager的commonEvent机制）
                String eventType = isHigh ? "com.tdtech.ohos.health.action.HEARTRATE_HIGH_ALERT" : 
                                          "com.tdtech.ohos.health.action.HEARTRATE_LOW_ALERT";
                dataManager.setCommonEvent(eventType + ":" + heartRate);
                
            } else {
                // 心率恢复正常，清除超限标志
                if (dataManager.getIsheartRateExceeded()) {
                    dataManager.setIsheartRateExceeded(false);
                    HiLog.info(LABEL_LOG, "心率恢复正常: " + heartRate + " bpm");
                }
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "心率告警检查异常: " + e.getMessage());
        }
    }
    
    @Override
    public double calculateDynamicMultiplier(UnifiedTaskScheduler.DeviceState deviceState,
                                           int batteryLevel,
                                           NetworkStateManager.NetworkState networkState) {
        double multiplier = 1.0;
        
        // 心率监测的智能调整策略
        switch (deviceState) {
            case NOT_WEARING:
                // 未佩戴时大幅降低频率，但不完全停止（可能需要检测重新佩戴）
                multiplier = 20.0; // 5秒变为100秒
                break;
            case PASSIVE_WEARING:
                // 静止佩戴时适度降低频率
                multiplier = 3.0; // 5秒变为15秒
                break;
            case ACTIVE_WEARING:
                // 活跃佩戴时保持正常频率，甚至可以提高
                multiplier = 1.0;
                break;
            case CHARGING:
                // 充电时可以保持正常或稍微提高频率
                multiplier = 0.8; // 5秒变为4秒
                break;
            case LOW_BATTERY:
                // 低电量时降低频率但仍保持监测
                multiplier = 4.0; // 5秒变为20秒
                break;
        }
        
        // 电量影响（心率是关键指标，即使低电量也需要保持基本监测）
        if (batteryLevel < 5) {
            multiplier *= 6.0; // 极低电量时进一步降低频率
        } else if (batteryLevel < 10) {
            multiplier *= 3.0;
        } else if (batteryLevel < 20) {
            multiplier *= 2.0;
        }
        
        return multiplier;
    }
    
    @Override
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 心率监测是关键任务，几乎在所有情况下都需要执行
        // 只有在电量极度不足时才考虑暂停
        if (batteryLevel < 3) {
            HiLog.warn(LABEL_LOG, "电量极低(" + batteryLevel + "%)，暂停心率监测");
            return false;
        }
        
        return true;
    }
    
    @Override
    protected boolean prepare(Context context) {
        try {
            // 准备心率传感器
            // TODO: 实现传感器初始化逻辑
            
            HiLog.debug(LABEL_LOG, "心率监测任务准备完成");
            return true;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "心率监测任务准备失败: " + e.getMessage());
            return false;
        }
    }
    
    @Override
    protected void cleanup(Context context, boolean success) {
        try {
            // 清理工作
            if (!success) {
                HiLog.warn(LABEL_LOG, "心率监测任务执行失败，执行清理");
                // 可以在这里执行一些故障恢复操作
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "心率监测任务清理异常: " + e.getMessage());
        }
    }
}