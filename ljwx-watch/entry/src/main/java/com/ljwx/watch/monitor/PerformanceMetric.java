package com.ljwx.watch.monitor;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 性能指标类
 * 存储和管理单个性能指标的历史数据
 */
public class PerformanceMetric {
    private final String name;
    private final String unit;
    private final List<MetricDataPoint> history;
    private final int maxHistorySize;
    
    private double currentValue;
    private double minValue = Double.MAX_VALUE;
    private double maxValue = Double.MIN_VALUE;
    private double avgValue = 0.0;
    private long lastUpdateTime;
    
    public PerformanceMetric(String name, String unit, double initialValue) {
        this(name, unit, initialValue, 100);
    }
    
    public PerformanceMetric(String name, String unit, double initialValue, int maxHistorySize) {
        this.name = name;
        this.unit = unit;
        this.currentValue = initialValue;
        this.maxHistorySize = maxHistorySize;
        this.history = new ArrayList<>();
        this.lastUpdateTime = System.currentTimeMillis();
        
        updateStatistics(initialValue);
    }
    
    /**
     * 更新指标值
     */
    public synchronized void updateValue(double newValue) {
        this.currentValue = newValue;
        this.lastUpdateTime = System.currentTimeMillis();
        
        // 添加到历史记录
        history.add(new MetricDataPoint(newValue, lastUpdateTime));
        
        // 维护历史记录大小
        while (history.size() > maxHistorySize) {
            history.remove(0);
        }
        
        // 更新统计数据
        updateStatistics(newValue);
    }
    
    /**
     * 更新统计数据
     */
    private void updateStatistics(double value) {
        // 更新最小值和最大值
        minValue = Math.min(minValue, value);
        maxValue = Math.max(maxValue, value);
        
        // 计算平均值
        if (!history.isEmpty()) {
            double sum = history.stream().mapToDouble(MetricDataPoint::getValue).sum();
            avgValue = sum / history.size();
        }
    }
    
    /**
     * 获取指标名称
     */
    public String getName() {
        return name;
    }
    
    /**
     * 获取单位
     */
    public String getUnit() {
        return unit;
    }
    
    /**
     * 获取当前值
     */
    public synchronized double getCurrentValue() {
        return currentValue;
    }
    
    /**
     * 获取最小值
     */
    public synchronized double getMinValue() {
        return minValue;
    }
    
    /**
     * 获取最大值
     */
    public synchronized double getMaxValue() {
        return maxValue;
    }
    
    /**
     * 获取平均值
     */
    public synchronized double getAvgValue() {
        return avgValue;
    }
    
    /**
     * 获取最后更新时间
     */
    public synchronized long getLastUpdateTime() {
        return lastUpdateTime;
    }
    
    /**
     * 获取历史数据点数量
     */
    public synchronized int getHistorySize() {
        return history.size();
    }
    
    /**
     * 获取历史数据的只读副本
     */
    public synchronized List<MetricDataPoint> getHistory() {
        return Collections.unmodifiableList(new ArrayList<>(history));
    }
    
    /**
     * 获取最近N个数据点的平均值
     */
    public synchronized double getRecentAverage(int count) {
        if (history.isEmpty()) {
            return currentValue;
        }
        
        int size = Math.min(count, history.size());
        double sum = 0.0;
        
        for (int i = history.size() - size; i < history.size(); i++) {
            sum += history.get(i).getValue();
        }
        
        return sum / size;
    }
    
    /**
     * 获取趋势 (正数表示上升，负数表示下降，0表示稳定)
     */
    public synchronized double getTrend() {
        if (history.size() < 2) {
            return 0.0;
        }
        
        // 简单线性趋势计算 - 比较最近25%和前25%的平均值
        int quarterSize = Math.max(1, history.size() / 4);
        
        double recentAvg = getRecentAverage(quarterSize);
        double earlierAvg = 0.0;
        
        for (int i = 0; i < quarterSize && i < history.size(); i++) {
            earlierAvg += history.get(i).getValue();
        }
        earlierAvg /= quarterSize;
        
        return recentAvg - earlierAvg;
    }
    
    /**
     * 获取变化率 (相对于最小值的百分比)
     */
    public synchronized double getChangeRate() {
        if (minValue == maxValue) {
            return 0.0;
        }
        
        return ((currentValue - minValue) / (maxValue - minValue)) * 100;
    }
    
    /**
     * 清除历史数据
     */
    public synchronized void clearHistory() {
        history.clear();
        minValue = currentValue;
        maxValue = currentValue;
        avgValue = currentValue;
    }
    
    /**
     * 获取指标摘要
     */
    public synchronized String getSummary() {
        return String.format("%s: 当前=%.2f%s, 平均=%.2f%s, 范围=%.2f~%.2f%s, 趋势=%.2f, 数据点=%d", 
                           name, currentValue, unit, avgValue, unit, 
                           minValue, maxValue, unit, getTrend(), history.size());
    }
    
    @Override
    public synchronized String toString() {
        return String.format("PerformanceMetric{name='%s', value=%.2f%s, updated=%s}", 
                           name, currentValue, unit, new java.util.Date(lastUpdateTime));
    }
    
    /**
     * 性能数据点类
     */
    public static class MetricDataPoint {
        private final double value;
        private final long timestamp;
        
        public MetricDataPoint(double value, long timestamp) {
            this.value = value;
            this.timestamp = timestamp;
        }
        
        public double getValue() {
            return value;
        }
        
        public long getTimestamp() {
            return timestamp;
        }
        
        @Override
        public String toString() {
            return String.format("DataPoint{value=%.2f, time=%s}", 
                               value, new java.util.Date(timestamp));
        }
    }
}