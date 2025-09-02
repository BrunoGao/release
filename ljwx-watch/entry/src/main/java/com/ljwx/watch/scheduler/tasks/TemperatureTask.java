package com.ljwx.watch.scheduler.tasks;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.UnifiedTaskScheduler;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;

/**
 * 体温监测任务
 * 高优先级任务，负责定期采集体温数据
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class TemperatureTask extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "TemperatureTask");
    
    private DataManager dataManager;
    private double lastTemperature = 0.0;
    private long lastValidReadingTime = 0;
    
    // 体温异常阈值
    private static final double FEVER_THRESHOLD = 37.3; // 发热阈值
    private static final double LOW_TEMP_THRESHOLD = 35.5; // 体温过低阈值
    
    public TemperatureTask() {
        super(
            "temperature", 
            UnifiedTaskScheduler.TaskPriority.HIGH, 
            30,     // 30秒基础间隔
            false   // 不需要网络连接
        );
        this.dataManager = DataManager.getInstance();
    }
    
    @Override
    public boolean execute(Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行体温监测任务");
            
            // 读取当前体温
            double currentTemperature = readTemperature();
            
            // 验证体温数据有效性
            if (isValidTemperature(currentTemperature)) {
                // 更新DataManager中的体温数据
                dataManager.setTemperature(currentTemperature);
                lastTemperature = currentTemperature;
                lastValidReadingTime = System.currentTimeMillis();
                
                HiLog.info(LABEL_LOG, String.format("体温监测成功: %.1f°C", currentTemperature));
                
                // 检查体温异常
                checkTemperatureAlert(currentTemperature);
                
                return true;
            } else {
                HiLog.warn(LABEL_LOG, String.format("体温数据无效: %.1f", currentTemperature));
                
                // 如果连续多次读取失败，可能需要特殊处理
                if (System.currentTimeMillis() - lastValidReadingTime > 900000) { // 15分钟
                    HiLog.error(LABEL_LOG, "体温监测长时间失败，可能需要检查传感器");
                }
                
                return false;
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "体温监测任务执行异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * 读取体温数据的具体实现
     * @return 体温值 (°C)
     */
    private double readTemperature() {
        try {
            // 从DataManager获取当前体温值
            double temperature = dataManager.getTemperature();
            
            // 如果DataManager中的体温为0或异常值，主动读取传感器
            if (temperature == 0.0 || temperature == 1000.0) {
                temperature = readFromTemperatureSensor();
            }
            
            return temperature;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "读取体温数据异常: " + e.getMessage());
            return 0.0;
        }
    }
    
    /**
     * 从体温传感器读取数据
     * @return 体温值
     */
    private double readFromTemperatureSensor() {
        try {
            // TODO: 实现实际的传感器读取逻辑
            
            // 模拟体温读取（实际实现中应该调用硬件API）
            if (lastTemperature > 0) {
                // 基于上次体温值生成一个小幅波动的值
                double variation = (Math.random() * 0.4 - 0.2); // -0.2到+0.2的随机变化
                return Math.max(35.0, Math.min(42.0, lastTemperature + variation));
            } else {
                // 首次读取，返回一个正常范围内的值
                return 36.0 + (Math.random() * 1.5); // 36.0-37.5之间
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "传感器读取异常: " + e.getMessage());
            return 0.0;
        }
    }
    
    /**
     * 验证体温数据是否有效
     * @param temperature 体温值
     * @return 是否有效
     */
    private boolean isValidTemperature(double temperature) {
        // 体温正常范围：30-45°C (考虑环境温度和异常情况)
        if (temperature < 30.0 || temperature > 45.0) {
            return false;
        }
        
        // 检查与上次体温的差异是否过大
        if (lastTemperature > 0) {
            double difference = Math.abs(temperature - lastTemperature);
            if (difference > 3.0) { // 体温变化超过3°C认为异常
                HiLog.warn(LABEL_LOG, String.format("体温变化过大: %.1f°C -> %.1f°C", 
                                                   lastTemperature, temperature));
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * 检查体温告警
     * @param temperature 当前体温值
     */
    private void checkTemperatureAlert(double temperature) {
        try {
            boolean isFever = temperature >= FEVER_THRESHOLD;
            boolean isLowTemp = temperature <= LOW_TEMP_THRESHOLD;
            
            if (isFever || isLowTemp) {
                String alertType = isFever ? "发热" : "体温过低";
                String alertMessage = String.format("%s告警: 当前体温 %.1f°C", alertType, temperature);
                
                HiLog.warn(LABEL_LOG, alertMessage);
                
                // 设置体温超限标志
                dataManager.setIsTemperatureExceeded(true);
                
                // 触发告警事件
                String eventType = isFever ? 
                    "com.tdtech.ohos.health.action.TEMPERATURE_HIGH_ALERT" :
                    "com.tdtech.ohos.health.action.TEMPERATURE_LOW_ALERT";
                dataManager.setCommonEvent(eventType + ":" + temperature);
                
            } else {
                // 体温恢复正常，清除超限标志
                if (dataManager.getIsTemperatureExceeded()) {
                    dataManager.setIsTemperatureExceeded(false);
                    HiLog.info(LABEL_LOG, String.format("体温恢复正常: %.1f°C", temperature));
                }
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "体温告警检查异常: " + e.getMessage());
        }
    }
    
    @Override
    public double calculateDynamicMultiplier(UnifiedTaskScheduler.DeviceState deviceState,
                                           int batteryLevel,
                                           NetworkStateManager.NetworkState networkState) {
        double multiplier = 1.0;
        
        // 体温监测的智能调整策略
        switch (deviceState) {
            case NOT_WEARING:
                // 未佩戴时大幅降低频率，但仍需要检测环境温度
                multiplier = 20.0; // 30秒变为600秒(10分钟)
                break;
            case PASSIVE_WEARING:
                // 静止佩戴时适度降低频率
                multiplier = 2.0; // 30秒变为60秒
                break;
            case ACTIVE_WEARING:
                // 活跃佩戴时保持正常频率，运动时体温变化较快
                multiplier = 1.0;
                break;
            case CHARGING:
                // 充电时可以保持正常频率
                multiplier = 1.0;
                break;
            case LOW_BATTERY:
                // 低电量时适度降低频率
                multiplier = 3.0; // 30秒变为90秒
                break;
        }
        
        // 电量影响
        if (batteryLevel < 5) {
            multiplier *= 4.0;
        } else if (batteryLevel < 10) {
            multiplier *= 2.0;
        } else if (batteryLevel < 20) {
            multiplier *= 1.5;
        }
        
        return multiplier;
    }
    
    @Override
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 体温监测在极低电量时可以暂停
        if (batteryLevel < 3) {
            HiLog.warn(LABEL_LOG, "电量极低(" + batteryLevel + "%)，暂停体温监测");
            return false;
        }
        
        return true;
    }
    
    @Override
    protected boolean prepare(Context context) {
        try {
            // 准备体温传感器
            // TODO: 实现传感器初始化逻辑
            
            HiLog.debug(LABEL_LOG, "体温监测任务准备完成");
            return true;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "体温监测任务准备失败: " + e.getMessage());
            return false;
        }
    }
    
    @Override
    protected void cleanup(Context context, boolean success) {
        try {
            if (!success) {
                HiLog.warn(LABEL_LOG, "体温监测任务执行失败，执行清理");
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "体温监测任务清理异常: " + e.getMessage());
        }
    }
}