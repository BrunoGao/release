package com.ljwx.watch.ui;

import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 帧率控制器
 * 智能控制UI重绘频率，根据设备状态和电量调整渲染策略
 */
public class FrameRateController {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    // 帧率配置
    private final int maxFPS;
    private final long frameInterval; // 最小帧间隔 (ms)
    
    // 动态帧率控制
    private int currentFPS;
    private long lastFrameTime = 0;
    
    // 帧率统计
    private int frameCount = 0;
    private long statisticsStartTime = System.currentTimeMillis();
    
    // 动态调整参数
    private boolean isLowPowerMode = false;
    private boolean isInactive = false;
    private int batteryLevel = 100;
    
    public FrameRateController(int maxFPS) {
        this.maxFPS = maxFPS;
        this.frameInterval = 1000 / maxFPS;
        this.currentFPS = maxFPS;
        
        HiLog.info(LABEL_LOG, "FrameRateController::初始化，最大FPS: " + maxFPS + 
                           ", 帧间隔: " + frameInterval + "ms");
    }
    
    /**
     * 检查是否应该进行渲染
     */
    public boolean shouldRender() {
        long currentTime = System.currentTimeMillis();
        long timeSinceLastFrame = currentTime - lastFrameTime;
        
        // 计算当前应该使用的帧间隔
        long adaptiveFrameInterval = calculateAdaptiveFrameInterval();
        
        if (timeSinceLastFrame >= adaptiveFrameInterval) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 记录帧完成
     */
    public void onFrameComplete() {
        lastFrameTime = System.currentTimeMillis();
        frameCount++;
        
        // 每秒更新一次FPS统计
        updateFPSStatistics();
    }
    
    /**
     * 计算自适应帧间隔
     */
    private long calculateAdaptiveFrameInterval() {
        // 基础帧间隔
        long baseInterval = frameInterval;
        
        // 根据电量调整
        if (batteryLevel <= 20) {
            // 低电量：降低到15FPS
            baseInterval = Math.max(baseInterval, 1000 / 15);
        } else if (batteryLevel <= 50) {
            // 中等电量：降低到20FPS  
            baseInterval = Math.max(baseInterval, 1000 / 20);
        }
        
        // 根据低功耗模式调整
        if (isLowPowerMode) {
            // 低功耗模式：最多10FPS
            baseInterval = Math.max(baseInterval, 1000 / 10);
        }
        
        // 根据活动状态调整
        if (isInactive) {
            // 非活动状态：最多5FPS
            baseInterval = Math.max(baseInterval, 1000 / 5);
        }
        
        return baseInterval;
    }
    
    /**
     * 更新FPS统计
     */
    private void updateFPSStatistics() {
        long currentTime = System.currentTimeMillis();
        long elapsedTime = currentTime - statisticsStartTime;
        
        if (elapsedTime >= 1000) { // 每秒更新一次
            currentFPS = (int) (frameCount * 1000.0 / elapsedTime);
            
            HiLog.debug(LABEL_LOG, "FrameRateController::当前FPS: " + currentFPS + 
                                 ", 目标间隔: " + calculateAdaptiveFrameInterval() + "ms");
            
            // 重置统计
            frameCount = 0;
            statisticsStartTime = currentTime;
        }
    }
    
    /**
     * 设置电池电量
     */
    public void setBatteryLevel(int batteryLevel) {
        this.batteryLevel = Math.max(0, Math.min(100, batteryLevel));
        HiLog.debug(LABEL_LOG, "FrameRateController::设置电池电量: " + this.batteryLevel + "%");
    }
    
    /**
     * 设置低功耗模式
     */
    public void setLowPowerMode(boolean enabled) {
        this.isLowPowerMode = enabled;
        HiLog.info(LABEL_LOG, "FrameRateController::低功耗模式: " + (enabled ? "开启" : "关闭"));
    }
    
    /**
     * 设置活动状态
     */
    public void setInactive(boolean inactive) {
        this.isInactive = inactive;
        HiLog.debug(LABEL_LOG, "FrameRateController::活动状态: " + (inactive ? "非活动" : "活动"));
    }
    
    /**
     * 获取当前FPS
     */
    public float getCurrentFPS() {
        return currentFPS;
    }
    
    /**
     * 获取最大FPS
     */
    public int getMaxFPS() {
        return maxFPS;
    }
    
    /**
     * 获取目标FPS（基于当前状态）
     */
    public int getTargetFPS() {
        return (int) (1000.0 / calculateAdaptiveFrameInterval());
    }
    
    /**
     * 强制下一帧渲染
     */
    public void forceNextFrame() {
        lastFrameTime = 0;
        HiLog.debug(LABEL_LOG, "FrameRateController::强制下一帧渲染");
    }
    
    /**
     * 重置统计信息
     */
    public void reset() {
        frameCount = 0;
        currentFPS = 0;
        statisticsStartTime = System.currentTimeMillis();
        lastFrameTime = 0;
        HiLog.info(LABEL_LOG, "FrameRateController::重置统计信息");
    }
    
    /**
     * 获取帧率控制状态
     */
    public String getStatus() {
        return String.format("FPS状态 - 当前: %d, 目标: %d, 最大: %d, 电量: %d%%, 低功耗: %s, 活动: %s", 
                           currentFPS, getTargetFPS(), maxFPS, batteryLevel,
                           isLowPowerMode ? "是" : "否", 
                           isInactive ? "否" : "是");
    }
    
    /**
     * 根据场景预设帧率策略
     */
    public void setFrameRateStrategy(FrameRateStrategy strategy) {
        switch (strategy) {
            case HIGH_PERFORMANCE:
                // 高性能模式：不限制FPS
                setLowPowerMode(false);
                setInactive(false);
                break;
                
            case BALANCED:
                // 平衡模式：适中的FPS限制
                setLowPowerMode(false);
                break;
                
            case POWER_SAVE:
                // 省电模式：严格限制FPS
                setLowPowerMode(true);
                break;
                
            case ULTRA_POWER_SAVE:
                // 超级省电模式：最严格的FPS限制
                setLowPowerMode(true);
                setInactive(true);
                break;
        }
        
        HiLog.info(LABEL_LOG, "FrameRateController::设置帧率策略: " + strategy);
    }
    
    /**
     * 帧率策略枚举
     */
    public enum FrameRateStrategy {
        HIGH_PERFORMANCE,  // 高性能
        BALANCED,          // 平衡
        POWER_SAVE,        // 省电
        ULTRA_POWER_SAVE   // 超级省电
    }
}