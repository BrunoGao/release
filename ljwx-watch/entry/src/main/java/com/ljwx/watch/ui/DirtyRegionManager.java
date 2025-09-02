package com.ljwx.watch.ui;

import ohos.agp.utils.RectFloat;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 脏区域管理器
 * 负责跟踪UI组件的变化区域，只重绘变化的部分
 */
public class DirtyRegionManager {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    // 脏区域存储 - 按元素ID跟踪
    private final Map<String, RectFloat> dirtyRegions = new ConcurrentHashMap<>();
    
    // 全屏标记
    private boolean fullScreenDirty = false;
    
    // 屏幕尺寸
    private float screenWidth = 240;  // 默认智能手表屏幕尺寸
    private float screenHeight = 240;
    
    /**
     * 标记指定区域为脏区域
     */
    public void markDirty(String elementId, RectFloat region) {
        if (elementId == null || region == null) {
            return;
        }
        
        // 合并现有脏区域
        RectFloat existingDirty = dirtyRegions.get(elementId);
        if (existingDirty != null) {
            // 计算并集
            float left = Math.min(existingDirty.left, region.left);
            float top = Math.min(existingDirty.top, region.top);
            float right = Math.max(existingDirty.right, region.right);
            float bottom = Math.max(existingDirty.bottom, region.bottom);
            
            dirtyRegions.put(elementId, new RectFloat(left, top, right, bottom));
        } else {
            dirtyRegions.put(elementId, new RectFloat(region));
        }
        
        HiLog.debug(LABEL_LOG, "DirtyRegionManager::标记脏区域: " + elementId + " " + region);
    }
    
    /**
     * 标记全屏为脏区域
     */
    public void markFullScreenDirty() {
        fullScreenDirty = true;
        dirtyRegions.clear(); // 全屏脏区域时清除局部区域
        HiLog.debug(LABEL_LOG, "DirtyRegionManager::标记全屏脏区域");
    }
    
    /**
     * 获取需要重绘的脏区域
     */
    public RectFloat getDirtyRegion(OptimizedUIRenderer.RenderContext context) {
        if (fullScreenDirty) {
            return new RectFloat(0, 0, screenWidth, screenHeight);
        }
        
        String elementId = context.getElementId();
        RectFloat dirtyRegion = dirtyRegions.get(elementId);
        
        if (dirtyRegion != null) {
            return new RectFloat(dirtyRegion);
        }
        
        // 如果没有脏区域，检查是否有全局变化
        if (!dirtyRegions.isEmpty()) {
            // 计算所有脏区域的并集
            RectFloat unionRegion = null;
            for (RectFloat region : dirtyRegions.values()) {
                if (unionRegion == null) {
                    unionRegion = new RectFloat(region);
                } else {
                    float left = Math.min(unionRegion.left, region.left);
                    float top = Math.min(unionRegion.top, region.top);
                    float right = Math.max(unionRegion.right, region.right);
                    float bottom = Math.max(unionRegion.bottom, region.bottom);
                    
                    unionRegion = new RectFloat(left, top, right, bottom);
                }
            }
            return unionRegion;
        }
        
        // 返回空区域
        return new RectFloat(0, 0, 0, 0);
    }
    
    /**
     * 清除指定元素的脏区域标记
     */
    public void clearDirtyRegion(String elementId) {
        if (elementId != null) {
            dirtyRegions.remove(elementId);
            HiLog.debug(LABEL_LOG, "DirtyRegionManager::清除脏区域: " + elementId);
        }
    }
    
    /**
     * 清除全屏脏区域标记
     */
    public void clearFullScreenDirty() {
        fullScreenDirty = false;
        HiLog.debug(LABEL_LOG, "DirtyRegionManager::清除全屏脏区域标记");
    }
    
    /**
     * 清除所有脏区域
     */
    public void clear() {
        dirtyRegions.clear();
        fullScreenDirty = false;
        HiLog.debug(LABEL_LOG, "DirtyRegionManager::清除所有脏区域");
    }
    
    /**
     * 获取脏区域数量
     */
    public int getDirtyRegionCount() {
        return fullScreenDirty ? 1 : dirtyRegions.size();
    }
    
    /**
     * 检查是否有脏区域需要重绘
     */
    public boolean hasDirtyRegions() {
        return fullScreenDirty || !dirtyRegions.isEmpty();
    }
    
    /**
     * 设置屏幕尺寸
     */
    public void setScreenSize(float width, float height) {
        this.screenWidth = width;
        this.screenHeight = height;
        HiLog.info(LABEL_LOG, "DirtyRegionManager::设置屏幕尺寸: " + width + "x" + height);
    }
    
    /**
     * 优化脏区域 - 合并相邻区域，避免过度分割
     */
    public void optimizeDirtyRegions() {
        if (dirtyRegions.size() <= 1) {
            return;
        }
        
        // 简化算法：如果脏区域过多或重叠率高，直接标记全屏脏区域
        if (dirtyRegions.size() > 5 || calculateOverlapRatio() > 0.6) {
            markFullScreenDirty();
            HiLog.debug(LABEL_LOG, "DirtyRegionManager::脏区域过多，优化为全屏重绘");
        }
    }
    
    /**
     * 计算脏区域重叠率
     */
    private double calculateOverlapRatio() {
        if (dirtyRegions.size() < 2) {
            return 0.0;
        }
        
        // 计算总面积和重叠面积的估算
        double totalArea = 0;
        double screenArea = screenWidth * screenHeight;
        
        for (RectFloat region : dirtyRegions.values()) {
            double area = (region.right - region.left) * (region.bottom - region.top);
            totalArea += area;
        }
        
        // 如果总面积超过屏幕面积的60%，认为重叠率高
        return totalArea / screenArea;
    }
}