package com.ljwx.watch.ui.drawable;

import com.ljwx.watch.ui.DrawCache;
import ohos.agp.render.Canvas;
import ohos.agp.render.Paint;
import ohos.agp.utils.Color;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 触摸反馈绘制组件
 * 提供视觉触摸反馈效果
 */
public class TouchFeedbackDrawable extends DrawCache.BaseCachedDrawable {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    private final Paint feedbackPaint;
    private float touchX = 0;
    private float touchY = 0;
    private float rippleRadius = 0;
    private boolean isActive = false;
    
    public TouchFeedbackDrawable() {
        super(500); // 500ms缓存有效期
        
        this.feedbackPaint = new Paint();
        feedbackPaint.setAntiAlias(true);
        feedbackPaint.setStyle(Paint.Style.FILL_AND_STROKE_STYLE);
        feedbackPaint.setColor(new Color(Color.getIntColor("#4DFFFFFF"))); // 半透明白色
        
        HiLog.info(LABEL_LOG, "TouchFeedbackDrawable::创建触摸反馈绘制组件");
    }
    
    @Override
    public void draw(Canvas canvas) {
        if (!isActive) {
            return;
        }
        
        try {
            // 绘制触摸涟漪效果
            drawRippleEffect(canvas);
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "TouchFeedbackDrawable::绘制失败: " + e.getMessage());
        }
    }
    
    /**
     * 绘制涟漪效果
     */
    private void drawRippleEffect(Canvas canvas) {
        if (rippleRadius <= 0) {
            return;
        }
        
        // 计算透明度（随着半径增大而减少）
        float maxRadius = 60.0f;
        float alpha = Math.max(0.1f, 1.0f - (rippleRadius / maxRadius));
        
        // 设置透明度
        int alphaInt = (int) (alpha * 77); // 77 = 0x4D (30% of 255)
        feedbackPaint.setColor(Color.argb(alphaInt, 255, 255, 255));
        
        // 绘制涟漪圆圈
        canvas.drawCircle(touchX, touchY, rippleRadius, feedbackPaint);
        
        // 绘制内圈高光
        if (rippleRadius < 20) {
            feedbackPaint.setColor(Color.argb((int) (alpha * 128), 255, 255, 255));
            canvas.drawCircle(touchX, touchY, rippleRadius * 0.5f, feedbackPaint);
        }
        
        HiLog.debug(LABEL_LOG, "TouchFeedbackDrawable::绘制涟漪效果，半径: " + rippleRadius);
    }
    
    /**
     * 开始触摸反馈动画
     */
    public void startTouchFeedback(float x, float y) {
        this.touchX = x;
        this.touchY = y;
        this.rippleRadius = 5.0f;
        this.isActive = true;
        
        HiLog.debug(LABEL_LOG, "TouchFeedbackDrawable::开始触摸反馈: (" + x + ", " + y + ")");
    }
    
    /**
     * 更新动画进度
     */
    public void updateAnimation(float progress) {
        if (!isActive) {
            return;
        }
        
        // progress: 0.0 to 1.0
        float maxRadius = 50.0f;
        rippleRadius = progress * maxRadius;
        
        // 动画完成时停止
        if (progress >= 1.0f) {
            stopTouchFeedback();
        }
        
        HiLog.debug(LABEL_LOG, "TouchFeedbackDrawable::更新动画进度: " + progress);
    }
    
    /**
     * 停止触摸反馈动画
     */
    public void stopTouchFeedback() {
        this.isActive = false;
        this.rippleRadius = 0;
        
        HiLog.debug(LABEL_LOG, "TouchFeedbackDrawable::停止触摸反馈");
    }
    
    /**
     * 检查动画是否激活
     */
    public boolean isAnimationActive() {
        return isActive;
    }
    
    /**
     * 获取当前涟漪半径
     */
    public float getRippleRadius() {
        return rippleRadius;
    }
    
    /**
     * 设置触摸反馈颜色
     */
    public void setFeedbackColor(Color color) {
        feedbackPaint.setColor(color);
    }
    
    /**
     * 设置触摸反馈透明度
     */
    public void setFeedbackAlpha(float alpha) {
        alpha = Math.max(0.0f, Math.min(1.0f, alpha));
        int alphaInt = (int) (alpha * 255);
        
        Color currentColor = feedbackPaint.getColor();
        feedbackPaint.setColor(Color.argb(alphaInt, 
                                        currentColor.getRed(), 
                                        currentColor.getGreen(), 
                                        currentColor.getBlue()));
    }
    
    @Override
    public boolean isExpired() {
        // 如果动画正在进行，不要过期
        if (isActive) {
            return false;
        }
        
        // 动画结束后按时间过期
        return super.isExpired();
    }
}