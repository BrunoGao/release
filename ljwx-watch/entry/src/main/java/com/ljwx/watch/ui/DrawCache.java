package com.ljwx.watch.ui;

import ohos.agp.render.Canvas;
import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 绘制缓存管理器
 * 缓存复杂的绘制操作，避免重复计算和绘制
 */
public class DrawCache {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    private final int maxSize;
    private final LRUCache<String, CachedDrawable> cache;
    
    // 统计信息
    private int hitCount = 0;
    private int missCount = 0;
    
    public DrawCache(int maxSize) {
        this.maxSize = maxSize;
        this.cache = new LRUCache<>(maxSize);
        HiLog.info(LABEL_LOG, "DrawCache::初始化缓存，最大大小: " + maxSize);
    }
    
    /**
     * 获取缓存的绘制对象
     */
    public CachedDrawable get(String key) {
        CachedDrawable drawable = cache.get(key);
        if (drawable != null && !drawable.isExpired()) {
            hitCount++;
            HiLog.debug(LABEL_LOG, "DrawCache::缓存命中: " + key);
            return drawable;
        } else {
            if (drawable != null) {
                // 过期缓存，移除
                cache.remove(key);
            }
            missCount++;
            HiLog.debug(LABEL_LOG, "DrawCache::缓存未命中: " + key);
            return null;
        }
    }
    
    /**
     * 缓存绘制对象
     */
    public void put(String key, CachedDrawable drawable) {
        if (key != null && drawable != null) {
            cache.put(key, drawable);
            HiLog.debug(LABEL_LOG, "DrawCache::缓存绘制对象: " + key);
        }
    }
    
    /**
     * 移除缓存项
     */
    public void remove(String key) {
        CachedDrawable removed = cache.remove(key);
        if (removed != null) {
            HiLog.debug(LABEL_LOG, "DrawCache::移除缓存: " + key);
        }
    }
    
    /**
     * 清除所有缓存
     */
    public void clear() {
        cache.clear();
        hitCount = 0;
        missCount = 0;
        HiLog.info(LABEL_LOG, "DrawCache::清除所有缓存");
    }
    
    /**
     * 获取缓存大小
     */
    public int size() {
        return cache.size();
    }
    
    /**
     * 获取缓存命中率
     */
    public double getHitRate() {
        int total = hitCount + missCount;
        return total == 0 ? 0.0 : (double) hitCount / total;
    }
    
    /**
     * 获取缓存统计信息
     */
    public String getStats() {
        return String.format("缓存统计 - 大小: %d/%d, 命中: %d, 未命中: %d, 命中率: %.2f%%", 
                           size(), maxSize, hitCount, missCount, getHitRate() * 100);
    }
    
    /**
     * 清理过期缓存
     */
    public void evictExpired() {
        cache.entrySet().removeIf(entry -> entry.getValue().isExpired());
        HiLog.debug(LABEL_LOG, "DrawCache::清理过期缓存，当前大小: " + size());
    }
    
    /**
     * LRU缓存实现
     */
    private static class LRUCache<K, V> extends LinkedHashMap<K, V> {
        private final int maxSize;
        
        public LRUCache(int maxSize) {
            super(16, 0.75f, true); // accessOrder = true for LRU
            this.maxSize = maxSize;
        }
        
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > maxSize;
        }
    }
    
    /**
     * 可缓存的绘制对象接口
     */
    public interface CachedDrawable {
        void draw(Canvas canvas);
        boolean isExpired();
        long getCreatedTime();
    }
    
    /**
     * 基础缓存绘制对象实现
     */
    public static abstract class BaseCachedDrawable implements CachedDrawable {
        private final long createdTime;
        private final long ttl; // Time to live in milliseconds
        
        protected BaseCachedDrawable(long ttl) {
            this.createdTime = System.currentTimeMillis();
            this.ttl = ttl;
        }
        
        protected BaseCachedDrawable() {
            this(30000); // 默认30秒过期
        }
        
        @Override
        public boolean isExpired() {
            return ttl > 0 && (System.currentTimeMillis() - createdTime) > ttl;
        }
        
        @Override
        public long getCreatedTime() {
            return createdTime;
        }
    }
}