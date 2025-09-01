package com.ljwx.watch.scheduler.tasks;

import ohos.app.Context;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;
import com.ljwx.watch.scheduler.ScheduledTask;
import com.ljwx.watch.scheduler.UnifiedTaskScheduler;
import com.ljwx.watch.network.NetworkStateManager;
import com.ljwx.watch.utils.DataManager;
import com.ljwx.watch.HttpService;

/**
 * 健康数据上传任务
 * 负责将收集的健康数据上传到服务器
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class HealthDataUploadTask extends ScheduledTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(3, 0xD001100, "HealthDataUploadTask");
    
    private DataManager dataManager;
    private HttpService httpService;
    private long lastSuccessfulUploadTime = 0;
    private int consecutiveFailures = 0;
    
    // 缓存配置
    private static final int MAX_CACHE_SIZE = 100; // 最大缓存条数
    private static final long MAX_CACHE_AGE = 24 * 60 * 60 * 1000; // 24小时
    
    public HealthDataUploadTask() {
        super(
            "healthDataUpload", 
            UnifiedTaskScheduler.TaskPriority.HIGH, 
            60,     // 60秒基础间隔
            true    // 需要网络连接
        );
        this.dataManager = DataManager.getInstance();
        this.httpService = new HttpService();
    }
    
    @Override
    public boolean execute(Context context) {
        try {
            HiLog.debug(LABEL_LOG, "开始执行健康数据上传任务");
            
            // 检查是否有待上传的数据
            if (!hasDataToUpload()) {
                HiLog.debug(LABEL_LOG, "暂无待上传的健康数据");
                return true; // 没有数据不算失败
            }
            
            // 准备上传数据
            String uploadData = prepareUploadData();
            if (uploadData == null || uploadData.isEmpty()) {
                HiLog.warn(LABEL_LOG, "准备上传数据失败");
                return false;
            }
            
            // 执行数据上传
            boolean uploadSuccess = uploadHealthData(uploadData);
            
            if (uploadSuccess) {
                lastSuccessfulUploadTime = System.currentTimeMillis();
                consecutiveFailures = 0;
                
                // 清理已上传的缓存数据
                clearUploadedCache();
                
                HiLog.info(LABEL_LOG, "健康数据上传成功");
                return true;
            } else {
                consecutiveFailures++;
                HiLog.warn(LABEL_LOG, "健康数据上传失败，连续失败次数: " + consecutiveFailures);
                
                // 缓存上传失败的数据
                cacheFailedUploadData(uploadData);
                
                return false;
            }
        } catch (Exception e) {
            consecutiveFailures++;
            HiLog.error(LABEL_LOG, "健康数据上传任务执行异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }
    
    /**
     * 检查是否有待上传的数据
     * @return 是否有数据需要上传
     */
    private boolean hasDataToUpload() {
        try {
            // 检查DataManager中的数据是否已更新
            long lastDataUpdateTime = dataManager.getLastDataUpdateTime();
            
            // 如果数据有更新或者有缓存的失败数据，则需要上传
            return lastDataUpdateTime > lastSuccessfulUploadTime || hasCachedData();
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "检查待上传数据异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 检查是否有缓存的失败数据
     * @return 是否有缓存数据
     */
    private boolean hasCachedData() {
        // TODO: 实现缓存数据检查逻辑
        return false;
    }
    
    /**
     * 准备上传数据
     * @return 格式化的上传数据JSON字符串
     */
    private String prepareUploadData() {
        try {
            // 收集当前健康数据
            int heartRate = dataManager.getHeartRate();
            int spO2 = dataManager.getSpO2();
            double temperature = dataManager.getTemperature();
            int stress = dataManager.getStress();
            int step = dataManager.getStep();
            int sleep = dataManager.getSleep();
            
            // 构建上传数据JSON
            StringBuilder jsonBuilder = new StringBuilder();
            jsonBuilder.append("{");
            jsonBuilder.append("\"deviceSn\":\"").append(dataManager.getDeviceSN()).append("\",");
            jsonBuilder.append("\"timestamp\":").append(System.currentTimeMillis()).append(",");
            jsonBuilder.append("\"heartRate\":").append(heartRate).append(",");
            jsonBuilder.append("\"spO2\":").append(spO2).append(",");
            jsonBuilder.append("\"temperature\":").append(temperature).append(",");
            jsonBuilder.append("\"stress\":").append(stress).append(",");
            jsonBuilder.append("\"step\":").append(step).append(",");
            jsonBuilder.append("\"sleep\":").append(sleep).append(",");
            jsonBuilder.append("\"batteryLevel\":").append(getBatteryLevel()).append(",");
            jsonBuilder.append("\"uploadType\":\"health_data\"");
            jsonBuilder.append("}");
            
            String uploadData = jsonBuilder.toString();
            HiLog.debug(LABEL_LOG, "准备上传数据: " + uploadData);
            
            return uploadData;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "准备上传数据异常: " + e.getMessage());
            return null;
        }
    }
    
    /**
     * 执行健康数据上传
     * @param data 要上传的数据
     * @return 上传是否成功
     */
    private boolean uploadHealthData(String data) {
        try {
            // 使用HttpService执行上传
            // TODO: 需要HttpService提供相应的上传接口
            
            // 模拟上传过程
            HiLog.debug(LABEL_LOG, "正在上传健康数据...");
            
            // 这里应该调用实际的HTTP上传逻辑
            // 暂时返回随机结果用于测试
            boolean success = Math.random() > 0.2; // 80%成功率
            
            if (success) {
                HiLog.info(LABEL_LOG, "健康数据上传到服务器成功");
            } else {
                HiLog.warn(LABEL_LOG, "健康数据上传到服务器失败");
            }
            
            return success;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "上传健康数据异常: " + e.getMessage());
            return false;
        }
    }
    
    /**
     * 缓存上传失败的数据
     * @param data 失败的数据
     */
    private void cacheFailedUploadData(String data) {
        try {
            // TODO: 实现数据缓存逻辑
            // 可以使用本地存储或DataManager的缓存机制
            HiLog.debug(LABEL_LOG, "缓存失败的上传数据");
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "缓存失败数据异常: " + e.getMessage());
        }
    }
    
    /**
     * 清理已上传的缓存数据
     */
    private void clearUploadedCache() {
        try {
            // TODO: 实现缓存清理逻辑
            HiLog.debug(LABEL_LOG, "清理已上传的缓存数据");
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "清理缓存异常: " + e.getMessage());
        }
    }
    
    /**
     * 获取电池电量
     * @return 电池电量百分比
     */
    private int getBatteryLevel() {
        // TODO: 从BatteryMonitor获取电池电量
        return 50; // 临时返回50%
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
        
        if (networkState == NetworkStateManager.NetworkState.MOBILE_WEAK) {
            multiplier *= 3.0; // 网络信号弱时延长间隔
        }
        
        // 设备状态影响
        switch (deviceState) {
            case NOT_WEARING:
                multiplier *= 5.0; // 未佩戴时延长间隔
                break;
            case PASSIVE_WEARING:
                multiplier *= 2.0; // 静止时适度延长
                break;
            case ACTIVE_WEARING:
                multiplier *= 1.0; // 活跃时保持正常
                break;
            case CHARGING:
                multiplier *= 0.5; // 充电时可以更频繁上传
                break;
            case LOW_BATTERY:
                multiplier *= 4.0; // 低电量时减少上传频率
                break;
        }
        
        // 连续失败次数影响
        if (consecutiveFailures > 0) {
            multiplier *= Math.min(consecutiveFailures * 2.0, 10.0); // 失败次数越多间隔越长，最多10倍
        }
        
        // 电量影响
        if (batteryLevel < 10) {
            multiplier *= 5.0;
        } else if (batteryLevel < 20) {
            multiplier *= 2.0;
        }
        
        return multiplier;
    }
    
    @Override
    public boolean shouldExecuteUnderConditions(UnifiedTaskScheduler.DeviceState deviceState,
                                               int batteryLevel,
                                               NetworkStateManager.NetworkState networkState) {
        // 必须有网络连接
        if (!networkState.isConnected()) {
            HiLog.debug(LABEL_LOG, "网络未连接，跳过数据上传");
            return false;
        }
        
        // 极低电量时暂停上传
        if (batteryLevel < 5) {
            HiLog.warn(LABEL_LOG, "电量极低(" + batteryLevel + "%)，暂停数据上传");
            return false;
        }
        
        // 连续失败过多时暂时停止
        if (consecutiveFailures >= 10) {
            HiLog.warn(LABEL_LOG, "连续失败次数过多(" + consecutiveFailures + ")，暂时停止上传");
            return false;
        }
        
        return true;
    }
    
    @Override
    protected boolean prepare(Context context) {
        try {
            // 检查网络连接状态
            NetworkStateManager networkManager = NetworkStateManager.getInstance();
            NetworkStateManager.NetworkState networkState = networkManager.getCurrentNetworkState();
            
            if (!networkState.isConnected()) {
                HiLog.debug(LABEL_LOG, "网络未连接，跳过数据上传准备");
                return false;
            }
            
            HiLog.debug(LABEL_LOG, "健康数据上传任务准备完成");
            return true;
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "健康数据上传任务准备失败: " + e.getMessage());
            return false;
        }
    }
    
    @Override
    protected void cleanup(Context context, boolean success) {
        try {
            if (!success && consecutiveFailures >= 5) {
                HiLog.warn(LABEL_LOG, "数据上传连续失败，可能需要检查网络配置");
            }
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "健康数据上传任务清理异常: " + e.getMessage());
        }
    }
}