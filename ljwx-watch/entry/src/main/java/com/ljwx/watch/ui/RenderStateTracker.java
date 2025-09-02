package com.ljwx.watch.ui;

import com.ljwx.watch.ui.OptimizedUIRenderer.RenderContext;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 渲染状态跟踪器
 * 跟踪UI元素的渲染状态，优化重绘策略
 */
public class RenderStateTracker {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    // 元素渲染状态存储
    private final Map<String, ElementRenderState> elementStates = new ConcurrentHashMap<>();
    
    // 全局渲染统计
    private int totalRenderCount = 0;
    private int skippedRenderCount = 0;
    private long totalRenderTime = 0;
    
    /**
     * 更新元素的渲染状态
     */
    public void updateRenderState(RenderContext context) {
        String elementId = context.getElementId();
        long currentTime = System.currentTimeMillis();
        
        ElementRenderState state = elementStates.get(elementId);
        if (state == null) {
            state = new ElementRenderState(elementId);
            elementStates.put(elementId, state);
        }
        
        state.updateRenderState(currentTime, context.getPriority());
        totalRenderCount++;
        
        HiLog.debug(LABEL_LOG, "RenderStateTracker::更新渲染状态: " + elementId);
    }
    
    /**
     * 检查元素是否需要渲染
     */
    public boolean shouldRender(String elementId, OptimizedUIRenderer.RenderPriority priority) {
        ElementRenderState state = elementStates.get(elementId);
        if (state == null) {
            return true; // 首次渲染
        }
        
        boolean shouldRender = state.shouldRender(priority);
        if (!shouldRender) {
            skippedRenderCount++;
            HiLog.debug(LABEL_LOG, "RenderStateTracker::跳过渲染: " + elementId);
        }
        
        return shouldRender;
    }
    
    /**
     * 记录渲染时间
     */
    public void recordRenderTime(String elementId, long renderTime) {
        ElementRenderState state = elementStates.get(elementId);
        if (state != null) {
            state.recordRenderTime(renderTime);
        }
        
        totalRenderTime += renderTime;
    }
    
    /**
     * 获取元素渲染频率
     */
    public double getElementRenderFrequency(String elementId) {
        ElementRenderState state = elementStates.get(elementId);
        return state != null ? state.getRenderFrequency() : 0.0;
    }
    
    /**
     * 获取整体渲染统计
     */
    public String getRenderStatistics() {
        double skipRate = totalRenderCount > 0 ? 
            (double) skippedRenderCount / totalRenderCount * 100 : 0.0;
        double avgRenderTime = totalRenderCount > 0 ? 
            (double) totalRenderTime / totalRenderCount : 0.0;
        
        return String.format(
            "渲染统计 - 总计: %d, 跳过: %d (%.1f%%), 平均时间: %.2fms, 元素数: %d",
            totalRenderCount, skippedRenderCount, skipRate, avgRenderTime, elementStates.size());
    }
    
    /**
     * 清理长时间未活动的元素状态
     */
    public void cleanupInactiveElements() {
        long currentTime = System.currentTimeMillis();
        long inactiveThreshold = 60000; // 1分钟未活动视为无效
        
        elementStates.entrySet().removeIf(entry -> {
            ElementRenderState state = entry.getValue();
            boolean isInactive = (currentTime - state.getLastRenderTime()) > inactiveThreshold;
            if (isInactive) {
                HiLog.debug(LABEL_LOG, "RenderStateTracker::清理非活动元素: " + entry.getKey());
            }
            return isInactive;
        });
    }
    
    /**
     * 重置统计信息
     */
    public void resetStatistics() {
        totalRenderCount = 0;
        skippedRenderCount = 0;
        totalRenderTime = 0;
        elementStates.clear();
        HiLog.info(LABEL_LOG, "RenderStateTracker::重置统计信息");
    }
    
    /**
     * 单个元素的渲染状态
     */
    private static class ElementRenderState {
        private final String elementId;
        private long lastRenderTime;
        private long totalRenderTime;
        private int renderCount;
        private OptimizedUIRenderer.RenderPriority lastPriority;
        private long createTime;
        
        public ElementRenderState(String elementId) {
            this.elementId = elementId;
            this.createTime = System.currentTimeMillis();
            this.lastRenderTime = createTime;
            this.lastPriority = OptimizedUIRenderer.RenderPriority.NORMAL;
        }
        
        /**
         * 更新渲染状态
         */
        public void updateRenderState(long renderTime, OptimizedUIRenderer.RenderPriority priority) {
            this.lastRenderTime = renderTime;
            this.lastPriority = priority;
            this.renderCount++;
        }
        
        /**
         * 记录渲染时间
         */
        public void recordRenderTime(long renderTime) {
            this.totalRenderTime += renderTime;
        }
        
        /**
         * 判断是否应该渲染
         */
        public boolean shouldRender(OptimizedUIRenderer.RenderPriority priority) {
            long currentTime = System.currentTimeMillis();
            long timeSinceLastRender = currentTime - lastRenderTime;
            
            // 根据优先级确定最小渲染间隔
            long minInterval = getMinRenderInterval(priority);
            
            // 关键优先级总是渲染
            if (priority == OptimizedUIRenderer.RenderPriority.CRITICAL) {
                return true;
            }
            
            // 检查是否满足最小间隔要求
            return timeSinceLastRender >= minInterval;
        }
        
        /**
         * 根据优先级获取最小渲染间隔
         */
        private long getMinRenderInterval(OptimizedUIRenderer.RenderPriority priority) {
            switch (priority) {
                case CRITICAL:
                    return 0; // 立即渲染
                case HIGH:
                    return 16; // ~60 FPS
                case NORMAL:
                    return 33; // ~30 FPS
                case LOW:
                    return 100; // ~10 FPS
                default:
                    return 33;
            }
        }
        
        /**
         * 获取渲染频率（次/秒）
         */
        public double getRenderFrequency() {
            long currentTime = System.currentTimeMillis();
            long elapsedTime = currentTime - createTime;
            
            if (elapsedTime == 0 || renderCount == 0) {
                return 0.0;
            }
            
            return (double) renderCount * 1000 / elapsedTime;
        }
        
        /**
         * 获取最后渲染时间
         */
        public long getLastRenderTime() {
            return lastRenderTime;
        }
        
        /**
         * 获取平均渲染时间
         */
        public double getAverageRenderTime() {
            return renderCount > 0 ? (double) totalRenderTime / renderCount : 0.0;
        }
        
        /**
         * 获取元素状态摘要
         */
        public String getSummary() {
            return String.format("%s: 渲染%d次, 频率%.1f/s, 平均时间%.2fms, 优先级%s",
                               elementId, renderCount, getRenderFrequency(), 
                               getAverageRenderTime(), lastPriority);
        }
    }
}