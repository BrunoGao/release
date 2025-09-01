package com.ljwx.watch.scheduler.tasks;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.UnifiedTaskScheduler;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;

/**
 * 血氧监测任务
 * 关键任务，负责定期采集血氧饱和度数据
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class SpO2Task extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "SpO2Task");
    
    private DataManager dataManager;
    private int lastSpO2 = 0;
    private long lastValidReadingTime = 0;
    
    public SpO2Task() {
        super(
            "spO2", 
            UnifiedTaskScheduler.TaskPriority.CRITICAL, 
            10,     // 10秒基础间隔
            false   // 不需要网络连接
        );
        this.dataManager = DataManager.getInstance();
    }
    
    @Override
    public boolean execute(Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行血氧监测任务");
            
            // 读取当前血氧值
            int currentSpO2 = readSpO2();
            
            // 验证血氧数据有效性
            if (isValidSpO2(currentSpO2)) {
                // 更新DataManager中的血氧数据
                dataManager.setSpO2(currentSpO2);
                lastSpO2 = currentSpO2;
                lastValidReadingTime = System.currentTimeMillis();
                
                HiLog.info(LABEL_LOG, "血氧监测成功: " + currentSpO2 + "%");
                
                // 检查血氧异常
                checkSpO2Alert(currentSpO2);
                
                return true;
            } else {
                HiLog.warn(LABEL_LOG, "血氧数据无效: " + currentSpO2);
                
                // 如果连续多次读取失败，可能需要特殊处理
                if (System.currentTimeMillis() - lastValidReadingTime > 600000) { // 10分钟
                    HiLog.error(LABEL_LOG, "血氧监测长时间失败，可能需要检查传感器");
                }
                
                return false;
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "血氧监测任务执行异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * 读取血氧数据的具体实现
     * @return 血氧值 (%)
     */
    private int readSpO2() {
        try {
            // 从DataManager获取当前血氧值
            int spO2 = dataManager.getSpO2();
            
            // 如果DataManager中的血氧为0或异常值，主动读取传感器
            if (spO2 == 0 || spO2 == 1000) {
                spO2 = readFromSpO2Sensor();
            }
            
            return spO2;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "读取血氧数据异常: " + e.getMessage());
            return 0;
        }
    }
    
    /**
     * 从血氧传感器读取数据
     * @return 血氧值
     */
    private int readFromSpO2Sensor() {
        try {
            // TODO: 实现实际的传感器读取逻辑
            
            // 模拟血氧读取（实际实现中应该调用硬件API）
            if (lastSpO2 > 0) {
                // 基于上次血氧值生成一个小幅波动的值
                int variation = (int) (Math.random() * 4 - 2); // -2到+2的随机变化
                return Math.max(85, Math.min(100, lastSpO2 + variation));
            } else {
                // 首次读取，返回一个正常范围内的值
                return 96 + (int) (Math.random() * 4); // 96-99之间
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "传感器读取异常: " + e.getMessage());
            return 0;
        }
    }
    
    /**
     * 验证血氧数据是否有效
     * @param spO2 血氧值
     * @return 是否有效
     */
    private boolean isValidSpO2(int spO2) {
        // 血氧正常范围：80-100%
        if (spO2 < 80 || spO2 > 100) {
            return false;
        }
        
        // 检查与上次血氧的差异是否过大
        if (lastSpO2 > 0) {
            int difference = Math.abs(spO2 - lastSpO2);
            if (difference > 15) { // 血氧变化超过15%认为异常
                HiLog.warn(LABEL_LOG, "血氧变化过大: " + lastSpO2 + "% -> " + spO2 + "%");
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 检查血氧告警
     * @param spO2 当前血氧值
     */
    private void checkSpO2Alert(int spO2) {
        try {
            int lowThreshold = dataManager.getSpO2WarningLow();
            
            boolean isLow = (lowThreshold > 0 && spO2 < lowThreshold);
            
            if (isLow) {
                String alertMessage = String.format("血氧过低告警: 当前血氧 %d%%, 阈值: >%d%%", 
                                                   spO2, lowThreshold);
                
                HiLog.warn(LABEL_LOG, alertMessage);
                
                // 设置血氧超限标志
                dataManager.setIsSpO2Exceeded(true);
                
                // 触发告警事件
                String eventType = "com.tdtech.ohos.health.action.SPO2_LOW_ALERT";
                dataManager.setCommonEvent(eventType + ":" + spO2);
                
            } else {
                // 血氧恢复正常，清除超限标志
                if (dataManager.getIsSpO2Exceeded()) {
                    dataManager.setIsSpO2Exceeded(false);
                    HiLog.info(LABEL_LOG, "血氧恢复正常: " + spO2 + "%");
                }
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "血氧告警检查异常: " + e.getMessage());
        }
    }
    
    @Override
    public double calculateDynamicMultiplier(UnifiedTaskScheduler.DeviceState deviceState,
                                           int batteryLevel,
                                           NetworkStateManager.NetworkState networkState) {
        double multiplier = 1.0;
        
        // 血氧监测的智能调整策略
        switch (deviceState) {
            case NOT_WEARING:
                // 未佩戴时大幅降低频率
                multiplier = 30.0; // 10秒变为300秒(5分钟)
                break;
            case PASSIVE_WEARING:
                // 静止佩戴时适度降低频率
                multiplier = 2.0; // 10秒变为20秒
                break;
            case ACTIVE_WEARING:
                // 活跃佩戴时保持正常频率
                multiplier = 1.0;
                break;
            case CHARGING:
                // 充电时可以稍微提高频率
                multiplier = 0.8; // 10秒变为8秒
                break;
            case LOW_BATTERY:
                // 低电量时降低频率
                multiplier = 3.0; // 10秒变为30秒
                break;
        }
        
        // 电量影响
        if (batteryLevel < 5) {
            multiplier *= 5.0; // 极低电量时进一步降低频率
        } else if (batteryLevel < 10) {
            multiplier *= 2.5;
        } else if (batteryLevel < 20) {
            multiplier *= 1.5;
        }
        
        return multiplier;
    }
    
    @Override
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 血氧监测是关键任务，几乎在所有情况下都需要执行
        if (batteryLevel < 3) {
            HiLog.warn(LABEL_LOG, "电量极低(" + batteryLevel + "%)，暂停血氧监测");
            return false;
        }
        
        return true;
    }
    
    @Override
    protected boolean prepare(Context context) {
        try {
            // 准备血氧传感器
            // TODO: 实现传感器初始化逻辑
            
            HiLog.debug(LABEL_LOG, "血氧监测任务准备完成");
            return true;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "血氧监测任务准备失败: " + e.getMessage());
            return false;
        }
    }
    
    @Override
    protected void cleanup(Context context, boolean success) {
        try {
            if (!success) {
                HiLog.warn(LABEL_LOG, "血氧监测任务执行失败，执行清理");
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "血氧监测任务清理异常: " + e.getMessage());
        }
    }
}