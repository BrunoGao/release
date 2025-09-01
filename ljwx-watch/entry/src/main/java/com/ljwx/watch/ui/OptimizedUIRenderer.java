package com.ljwx.watch.ui;

import com.ljwx.watch.utils.DataManagerAdapter;
import ohos.agp.components.Component;
import ohos.agp.render.Canvas;
import ohos.agp.render.Paint;
import ohos.agp.utils.Color;
import ohos.agp.utils.RectFloat;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 优化的UI渲染器
 * 特性：
 * 1. 脏区域检测 - 只重绘发生变化的区域
 * 2. 绘制缓存 - 缓存复杂的绘制对象
 * 3. 帧率控制 - 智能控制重绘频率
 * 4. 硬件加速支持 - 启用GPU加速渲染
 * 5. 渲染优先级管理 - 关键UI优先渲染
 */
public class OptimizedUIRenderer {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    // 渲染优化配置
    private static final int MAX_FPS = 30; // 最大帧率限制
    private static final long FRAME_INTERVAL = 1000 / MAX_FPS; // 帧间隔
    private static final int CACHE_SIZE = 50; // 绘制缓存大小
    
    // 脏区域管理
    private final DirtyRegionManager dirtyRegionManager;
    
    // 绘制缓存
    private final DrawCache drawCache;
    
    // 帧率控制
    private final FrameRateController frameRateController;
    
    // 数据管理器
    private final DataManagerAdapter dataManager;
    
    // 渲染状态跟踪
    private final RenderStateTracker renderStateTracker;
    
    // 硬件加速管理
    private final HardwareAccelerationManager hwAccelManager;
    
    public OptimizedUIRenderer() {
        this.dataManager = DataManagerAdapter.getInstance();
        this.dirtyRegionManager = new DirtyRegionManager();
        this.drawCache = new DrawCache(CACHE_SIZE);
        this.frameRateController = new FrameRateController(MAX_FPS);
        this.renderStateTracker = new RenderStateTracker();
        this.hwAccelManager = new HardwareAccelerationManager();
        
        HiLog.info(LABEL_LOG, "OptimizedUIRenderer::优化UI渲染器初始化完成");
    }
    
    /**
     * 优化的渲染入口
     */
    public void optimizedRender(Component component, Canvas canvas, RenderContext context) {
        try {
            // 1. 帧率控制检查
            if (!frameRateController.shouldRender()) {
                return;
            }
            
            // 2. 脏区域检测
            RectFloat dirtyRegion = dirtyRegionManager.getDirtyRegion(context);
            if (dirtyRegion.isEmpty()) {
                return; // 无需重绘
            }
            
            // 3. 启用硬件加速
            hwAccelManager.enableHardwareAcceleration(canvas);
            
            // 4. 优化绘制流程
            performOptimizedDraw(component, canvas, context, dirtyRegion);
            
            // 5. 更新渲染状态
            renderStateTracker.updateRenderState(context);
            
            // 6. 记录帧完成
            frameRateController.onFrameComplete();
            
        } catch (Exception e) {
            HiLog.error(LABEL_LOG, "OptimizedUIRenderer::渲染异常: " + e.getMessage());
        }
    }
    
    /**
     * 执行优化的绘制流程
     */
    private void performOptimizedDraw(Component component, Canvas canvas, RenderContext context, RectFloat dirtyRegion) {
        // 设置裁剪区域，只绘制脏区域
        canvas.clipRect(dirtyRegion);
        
        // 根据渲染优先级分层绘制
        if (context.getPriority() == RenderPriority.CRITICAL) {
            renderCriticalElements(canvas, context);
        } else if (context.getPriority() == RenderPriority.HIGH) {
            renderHighPriorityElements(canvas, context);
        } else {
            renderNormalElements(canvas, context);
        }
        
        // 清除脏区域标记
        dirtyRegionManager.clearDirtyRegion(context.getElementId());
    }
    
    /**
     * 渲染关键元素（健康数据显示）
     */
    private void renderCriticalElements(Canvas canvas, RenderContext context) {
        // 健康数据显示 - 最高优先级
        if (context.hasElement("health_data")) {
            renderHealthData(canvas, context);
        }
        
        // 告警显示 - 关键优先级
        if (context.hasElement("alert_display")) {
            renderAlertDisplay(canvas, context);
        }
    }
    
    /**
     * 渲染高优先级元素（交互控件）
     */
    private void renderHighPriorityElements(Canvas canvas, RenderContext context) {
        // 触摸反馈
        if (context.hasElement("touch_feedback")) {
            renderTouchFeedback(canvas, context);
        }
        
        // 动画效果
        if (context.hasElement("animations")) {
            renderAnimations(canvas, context);
        }
    }
    
    /**
     * 渲染普通元素（背景、装饰）
     */
    private void renderNormalElements(Canvas canvas, RenderContext context) {
        // 背景渲染
        if (context.hasElement("background")) {
            renderBackground(canvas, context);
        }
        
        // 装饰元素
        if (context.hasElement("decorations")) {
            renderDecorations(canvas, context);
        }
    }
    
    /**
     * 优化的健康数据渲染
     */
    private void renderHealthData(Canvas canvas, RenderContext context) {
        String cacheKey = "health_data_" + getHealthDataHash();
        
        // 尝试从缓存获取
        CachedDrawable cached = drawCache.get(cacheKey);
        if (cached != null && !cached.isExpired()) {
            cached.draw(canvas);
            return;
        }
        
        // 创建新的绘制对象
        HealthDataDrawable healthDrawable = new HealthDataDrawable(dataManager);
        healthDrawable.draw(canvas);
        
        // 缓存绘制结果
        drawCache.put(cacheKey, healthDrawable);
    }
    
    /**
     * 优化的告警显示渲染
     */
    private void renderAlertDisplay(Canvas canvas, RenderContext context) {
        // 告警状态检查
        boolean hasAlert = checkAlertState();
        if (!hasAlert) {
            return;
        }
        
        // 使用硬件加速绘制告警动画
        hwAccelManager.drawAlertAnimation(canvas, context);
    }
    
    /**
     * 渲染触摸反馈
     */
    private void renderTouchFeedback(Canvas canvas, RenderContext context) {
        TouchFeedbackDrawable feedback = new TouchFeedbackDrawable();
        feedback.draw(canvas);
    }
    
    /**
     * 渲染动画效果
     */
    private void renderAnimations(Canvas canvas, RenderContext context) {
        AnimationRenderer animationRenderer = new AnimationRenderer();
        animationRenderer.render(canvas, context);
    }
    
    /**
     * 渲染背景
     */
    private void renderBackground(Canvas canvas, RenderContext context) {
        String cacheKey = "background";
        CachedDrawable cached = drawCache.get(cacheKey);
        
        if (cached == null) {
            BackgroundDrawable background = new BackgroundDrawable();
            background.draw(canvas);
            drawCache.put(cacheKey, background);
        } else {
            cached.draw(canvas);
        }
    }
    
    /**
     * 渲染装饰元素
     */
    private void renderDecorations(Canvas canvas, RenderContext context) {
        DecorationRenderer decorationRenderer = new DecorationRenderer();
        decorationRenderer.render(canvas, context);
    }
    
    /**
     * 获取健康数据哈希值（用于缓存键）
     */
    private int getHealthDataHash() {
        return dataManager.getHeartRate() + 
               dataManager.getBloodOxygen() + 
               (int)(dataManager.getTemperature() * 10) + 
               dataManager.getStress();
    }
    
    /**
     * 检查告警状态
     */
    private boolean checkAlertState() {
        // 简化的告警检查逻辑
        return dataManager.getHeartRate() > 100 || 
               dataManager.getBloodOxygen() < 90 || 
               dataManager.getTemperature() > 37.5;
    }
    
    /**
     * 标记区域为脏区域
     */
    public void markDirty(String elementId, RectFloat region) {
        dirtyRegionManager.markDirty(elementId, region);
    }
    
    /**
     * 标记全屏为脏区域
     */
    public void markFullScreenDirty() {
        dirtyRegionManager.markFullScreenDirty();
    }
    
    /**
     * 获取渲染统计信息
     */
    public String getRenderStats() {
        return String.format("FPS: %.1f, 缓存命中率: %.2f%%, 脏区域数: %d", 
                           frameRateController.getCurrentFPS(),
                           drawCache.getHitRate() * 100,
                           dirtyRegionManager.getDirtyRegionCount());
    }
    
    /**
     * 清理资源
     */
    public void cleanup() {
        drawCache.clear();
        dirtyRegionManager.clear();
        frameRateController.reset();
        hwAccelManager.cleanup();
        HiLog.info(LABEL_LOG, "OptimizedUIRenderer::资源清理完成");
    }
    
    // ==================== 渲染优先级枚举 ====================
    
    public enum RenderPriority {
        CRITICAL,  // 关键（健康数据、告警）
        HIGH,      // 高优先级（交互、动画）
        NORMAL,    // 普通（背景、装饰）
        LOW        // 低优先级（可延迟渲染）
    }
    
    // ==================== 渲染上下文 ====================
    
    public static class RenderContext {
        private final Map<String, Object> elements = new ConcurrentHashMap<>();
        private RenderPriority priority = RenderPriority.NORMAL;
        private String elementId;
        
        public RenderContext(String elementId) {
            this.elementId = elementId;
        }
        
        public boolean hasElement(String key) {
            return elements.containsKey(key);
        }
        
        public void addElement(String key, Object value) {
            elements.put(key, value);
        }
        
        public RenderPriority getPriority() {
            return priority;
        }
        
        public void setPriority(RenderPriority priority) {
            this.priority = priority;
        }
        
        public String getElementId() {
            return elementId;
        }
    }
}