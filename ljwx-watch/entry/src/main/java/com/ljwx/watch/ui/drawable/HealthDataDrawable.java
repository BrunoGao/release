package com.ljwx.watch.ui.drawable;

import com.ljwx.watch.ui.DrawCache;
import com.ljwx.watch.utils.DataManagerAdapter;
import ohos.agp.render.Canvas;
import ohos.agp.render.Paint;
import ohos.agp.utils.Color;
import ohos.agp.utils.TextAlignment;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 健康数据绘制组件
 * 优化的健康数据显示，支持缓存和智能刷新
 */
public class HealthDataDrawable extends DrawCache.BaseCachedDrawable {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    private final DataManagerAdapter dataManager;
    private final Paint textPaint;
    private final Paint valuePaint;
    
    // 健康数据缓存
    private int cachedHeartRate = -1;
    private int cachedBloodOxygen = -1;
    private float cachedTemperature = -1;
    private int cachedStress = -1;
    
    public HealthDataDrawable(DataManagerAdapter dataManager) {
        super(10000); // 10秒缓存有效期
        this.dataManager = dataManager;
        
        // 初始化画笔
        this.textPaint = new Paint();
        textPaint.setAntiAlias(true);
        textPaint.setColor(Color.WHITE);
        textPaint.setTextAlign(TextAlignment.CENTER);
        textPaint.setTextSize(24);
        
        this.valuePaint = new Paint();
        valuePaint.setAntiAlias(true);
        valuePaint.setTextAlign(TextAlignment.CENTER);
        valuePaint.setTextSize(32);
        
        // 缓存当前健康数据
        cacheHealthData();
        
        HiLog.info(LABEL_LOG, "HealthDataDrawable::创建健康数据绘制组件");
    }
    
    @Override
    public void draw(Canvas canvas) {
        long startTime = System.currentTimeMillis();
        
        try {
            // 获取画布尺寸
            float canvasWidth = canvas.getLocalClipBounds().getWidth();
            float canvasHeight = canvas.getLocalClipBounds().getHeight();
            float centerX = canvasWidth / 2.0f;
            float centerY = canvasHeight / 2.0f;
            
            // 绘制健康数据
            drawHealthMetrics(canvas, centerX, centerY);
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "HealthDataDrawable::绘制失败: " + e.getMessage());
        } finally {
            long renderTime = System.currentTimeMillis() - startTime;
            HiLog.debug(LABEL_LOG, "HealthDataDrawable::绘制耗时: " + renderTime + "ms");
        }
    }
    
    /**
     * 绘制健康指标
     */
    private void drawHealthMetrics(Canvas canvas, float centerX, float centerY) {
        float spacing = 45; // 行间距
        float currentY = centerY - 60; // 起始Y坐标
        
        // 心率
        drawHealthMetric(canvas, "心率", cachedHeartRate, "bpm", 
                        centerX, currentY, getHeartRateColor());
        currentY += spacing;
        
        // 血氧
        drawHealthMetric(canvas, "血氧", cachedBloodOxygen, "%", 
                        centerX, currentY, getBloodOxygenColor());
        currentY += spacing;
        
        // 体温
        drawTemperatureMetric(canvas, "体温", cachedTemperature, "°C", 
                             centerX, currentY, getTemperatureColor());
        currentY += spacing;
        
        // 压力
        drawHealthMetric(canvas, "压力", cachedStress, "", 
                        centerX, currentY, getStressColor());
    }
    
    /**
     * 绘制单个健康指标
     */
    private void drawHealthMetric(Canvas canvas, String label, int value, String unit, 
                                 float x, float y, Color valueColor) {
        // 绘制标签
        textPaint.setColor(Color.WHITE);
        canvas.drawText(textPaint, label, x - 60, y);
        
        // 绘制数值
        valuePaint.setColor(valueColor);
        String valueText = value >= 0 ? String.valueOf(value) : "-";
        canvas.drawText(valuePaint, valueText, x + 20, y);
        
        // 绘制单位
        if (!unit.isEmpty()) {
            textPaint.setTextSize(20);
            canvas.drawText(textPaint, unit, x + 60, y);
            textPaint.setTextSize(24); // 恢复原始大小
        }
    }
    
    /**
     * 绘制体温指标（支持小数）
     */
    private void drawTemperatureMetric(Canvas canvas, String label, float value, String unit, 
                                      float x, float y, Color valueColor) {
        // 绘制标签
        textPaint.setColor(Color.WHITE);
        canvas.drawText(textPaint, label, x - 60, y);
        
        // 绘制数值
        valuePaint.setColor(valueColor);
        String valueText = value >= 0 ? String.format("%.1f", value) : "-";
        canvas.drawText(valuePaint, valueText, x + 20, y);
        
        // 绘制单位
        textPaint.setTextSize(20);
        canvas.drawText(textPaint, unit, x + 60, y);
        textPaint.setTextSize(24);
    }
    
    /**
     * 缓存健康数据
     */
    private void cacheHealthData() {
        cachedHeartRate = dataManager.getHeartRate();
        cachedBloodOxygen = dataManager.getBloodOxygen();
        cachedTemperature = (float) dataManager.getTemperature();
        cachedStress = dataManager.getStress();
        
        HiLog.debug(LABEL_LOG, String.format(
            "HealthDataDrawable::缓存健康数据 - 心率:%d, 血氧:%d, 体温:%.1f, 压力:%d", 
            cachedHeartRate, cachedBloodOxygen, cachedTemperature, cachedStress));
    }
    
    /**
     * 检查数据是否有变化
     */
    public boolean hasDataChanged() {
        return cachedHeartRate != dataManager.getHeartRate() ||
               cachedBloodOxygen != dataManager.getBloodOxygen() ||
               Math.abs(cachedTemperature - dataManager.getTemperature()) > 0.1 ||
               cachedStress != dataManager.getStress();
    }
    
    /**
     * 刷新缓存数据
     */
    public void refreshCache() {
        cacheHealthData();
    }
    
    @Override
    public boolean isExpired() {
        // 如果数据有变化，立即过期
        if (hasDataChanged()) {
            HiLog.debug(LABEL_LOG, "HealthDataDrawable::数据变化，缓存过期");
            return true;
        }
        
        // 否则按时间过期
        return super.isExpired();
    }
    
    /**
     * 获取心率颜色
     */
    private Color getHeartRateColor() {
        if (cachedHeartRate < 0) return Color.GRAY;
        if (cachedHeartRate > 100 || cachedHeartRate < 60) {
            return Color.RED; // 异常心率
        }
        return new Color(Color.getIntColor("#00FF00")); // 正常心率为绿色
    }
    
    /**
     * 获取血氧颜色
     */
    private Color getBloodOxygenColor() {
        if (cachedBloodOxygen < 0) return Color.GRAY;
        if (cachedBloodOxygen < 95) {
            return Color.RED; // 血氧偏低
        }
        return new Color(Color.getIntColor("#00FF00")); // 正常血氧为绿色
    }
    
    /**
     * 获取体温颜色
     */
    private Color getTemperatureColor() {
        if (cachedTemperature < 0) return Color.GRAY;
        if (cachedTemperature > 37.5 || cachedTemperature < 36.0) {
            return Color.RED; // 体温异常
        }
        return new Color(Color.getIntColor("#FFFF00")); // 正常体温为黄色
    }
    
    /**
     * 获取压力颜色
     */
    private Color getStressColor() {
        if (cachedStress < 0) return Color.GRAY;
        if (cachedStress > 80) {
            return Color.RED; // 高压力
        } else if (cachedStress > 60) {
            return new Color(Color.getIntColor("#FFA500")); // 中等压力为橙色
        }
        return new Color(Color.getIntColor("#00FF00")); // 低压力为绿色
    }
}