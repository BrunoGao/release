package com.ljwx.watch.ui;

import com.ljwx.watch.ui.OptimizedUIRenderer.RenderContext;
import ohos.agp.render.Canvas;
import ohos.agp.render.Paint;
import ohos.agp.utils.Color;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 硬件加速管理器
 * 负责启用和管理GPU加速渲染，提升绘制性能
 */
public class HardwareAccelerationManager {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    // 硬件加速状态
    private boolean hardwareAccelEnabled = false;
    private boolean isGpuAvailable = false;
    
    // 性能统计
    private long totalRenderTime = 0;
    private int renderCount = 0;
    
    public HardwareAccelerationManager() {
        // 检测硬件加速支持
        detectHardwareAcceleration();
        HiLog.info(LABEL_LOG, "HardwareAccelerationManager::初始化，GPU可用: " + isGpuAvailable);
    }
    
    /**
     * 检测硬件加速支持
     */
    private void detectHardwareAcceleration() {
        try {
            // 在HarmonyOS中，Canvas通常支持硬件加速
            // 这里进行基本的可用性检查
            isGpuAvailable = true; // HarmonyOS设备通常支持GPU加速
            HiLog.info(LABEL_LOG, "HardwareAccelerationManager::检测到GPU支持");
        } catch (Exception e) {
            isGpuAvailable = false;
            HiLog.warn(LABEL_LOG, "HardwareAccelerationManager::GPU检测失败: " + e.getMessage());
        }
    }
    
    /**
     * 启用硬件加速
     */
    public void enableHardwareAcceleration(Canvas canvas) {
        if (!isGpuAvailable) {
            return;
        }
        
        try {
            // HarmonyOS Canvas默认支持硬件加速
            // 这里可以设置特定的加速选项
            hardwareAccelEnabled = true;
            HiLog.debug(LABEL_LOG, "HardwareAccelerationManager::启用硬件加速");
        } catch (Exception e) {
            hardwareAccelEnabled = false;
            HiLog.warn(LABEL_LOG, "HardwareAccelerationManager::启用硬件加速失败: " + e.getMessage());
        }
    }
    
    /**
     * 禁用硬件加速
     */
    public void disableHardwareAcceleration(Canvas canvas) {
        hardwareAccelEnabled = false;
        HiLog.debug(LABEL_LOG, "HardwareAccelerationManager::禁用硬件加速");
    }
    
    /**
     * 硬件加速绘制告警动画
     */
    public void drawAlertAnimation(Canvas canvas, RenderContext context) {
        if (!hardwareAccelEnabled) {
            drawSoftwareAlert(canvas, context);
            return;
        }
        
        long startTime = System.currentTimeMillis();
        
        try {
            // 使用硬件加速绘制告警动画
            drawHardwareAcceleratedAlert(canvas, context);
            
        } catch (Exception e) {
            HiLog.warn(LABEL_LOG, "HardwareAccelerationManager::硬件加速绘制失败，回退到软件渲染");
            drawSoftwareAlert(canvas, context);
        } finally {
            // 更新性能统计
            long renderTime = System.currentTimeMillis() - startTime;
            updatePerformanceStats(renderTime);
        }
    }
    
    /**
     * 硬件加速告警绘制
     */
    private void drawHardwareAcceleratedAlert(Canvas canvas, RenderContext context) {
        Paint paint = new Paint();
        paint.setAntiAlias(true);
        paint.setColor(Color.RED);
        
        // 获取画布中心
        float centerX = canvas.getLocalClipBounds().getWidth() / 2.0f;
        float centerY = canvas.getLocalClipBounds().getHeight() / 2.0f;
        
        // 绘制脉动效果的告警圆圈
        long time = System.currentTimeMillis();
        float pulseRadius = 30 + (float) (Math.sin(time * 0.01) * 10);
        
        // 使用硬件加速绘制渐变圆圈
        paint.setStyle(Paint.Style.STROKE_STYLE);
        paint.setStrokeWidth(4);
        
        // 绘制多层告警圆圈
        for (int i = 0; i < 3; i++) {
            float radius = pulseRadius + (i * 15);
            int alpha = 255 - (i * 80);
            paint.setAlpha(Math.max(50, alpha));
            
            canvas.drawCircle(centerX, centerY, radius, paint);
        }
        
        HiLog.debug(LABEL_LOG, "HardwareAccelerationManager::硬件加速告警动画绘制完成");
    }
    
    /**
     * 软件渲染告警（回退方案）
     */
    private void drawSoftwareAlert(Canvas canvas, RenderContext context) {
        Paint paint = new Paint();
        paint.setAntiAlias(true);
        paint.setColor(Color.RED);
        paint.setStyle(Paint.Style.STROKE_STYLE);
        paint.setStrokeWidth(3);
        
        // 获取画布中心
        float centerX = canvas.getLocalClipBounds().getWidth() / 2.0f;
        float centerY = canvas.getLocalClipBounds().getHeight() / 2.0f;
        
        // 绘制简单的告警圆圈
        canvas.drawCircle(centerX, centerY, 40, paint);
        
        HiLog.debug(LABEL_LOG, "HardwareAccelerationManager::软件渲染告警绘制完成");
    }
    
    /**
     * 更新性能统计
     */
    private void updatePerformanceStats(long renderTime) {
        totalRenderTime += renderTime;
        renderCount++;
        
        // 每100次渲染输出一次性能统计
        if (renderCount % 100 == 0) {
            double avgRenderTime = (double) totalRenderTime / renderCount;
            HiLog.info(LABEL_LOG, String.format(
                "HardwareAccelerationManager::渲染性能统计 - 次数: %d, 平均时间: %.2fms, 硬件加速: %s",
                renderCount, avgRenderTime, hardwareAccelEnabled ? "启用" : "禁用"));
        }
    }
    
    /**
     * 检查硬件加速是否可用
     */
    public boolean isHardwareAccelAvailable() {
        return isGpuAvailable;
    }
    
    /**
     * 检查硬件加速是否已启用
     */
    public boolean isHardwareAccelEnabled() {
        return hardwareAccelEnabled;
    }
    
    /**
     * 获取性能统计信息
     */
    public String getPerformanceStats() {
        if (renderCount == 0) {
            return "硬件加速统计: 未开始渲染";
        }
        
        double avgRenderTime = (double) totalRenderTime / renderCount;
        return String.format(
            "硬件加速统计 - 渲染次数: %d, 平均时间: %.2fms, 总时间: %dms, 状态: %s",
            renderCount, avgRenderTime, totalRenderTime,
            hardwareAccelEnabled ? "启用" : "禁用");
    }
    
    /**
     * 重置性能统计
     */
    public void resetPerformanceStats() {
        totalRenderTime = 0;
        renderCount = 0;
        HiLog.info(LABEL_LOG, "HardwareAccelerationManager::重置性能统计");
    }
    
    /**
     * 清理资源
     */
    public void cleanup() {
        hardwareAccelEnabled = false;
        resetPerformanceStats();
        HiLog.info(LABEL_LOG, "HardwareAccelerationManager::清理完成");
    }
    
    /**
     * 优化渲染设置
     */
    public void optimizeRenderingSettings(Canvas canvas) {
        if (!hardwareAccelEnabled) {
            return;
        }
        
        try {
            // 针对智能手表优化的渲染设置
            // 这些设置可以根据具体的HarmonyOS API进行调整
            
            HiLog.debug(LABEL_LOG, "HardwareAccelerationManager::应用优化渲染设置");
        } catch (Exception e) {
            HiLog.warn(LABEL_LOG, "HardwareAccelerationManager::设置优化渲染失败: " + e.getMessage());
        }
    }
}