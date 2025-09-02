package com.ljwx.watch.scheduler;

import java.util.ArrayList;
import java.util.List;

/**
 * 任务执行信息统计类
 * 记录和分析任务的执行历史和性能数据
 * 
 * @author ljwx-tech
 * @version 1.0
 */
public class TaskExecutionInfo {
    
    private final String taskId;
    private final long creationTime;
    
    // 执行统计
    private int totalExecutions = 0;
    private int successfulExecutions = 0;
    private int failedExecutions = 0;
    
    // 时间统计
    private long lastExecutionTime = 0;
    private long totalExecutionTime = 0;
    private long minExecutionTime = Long.MAX_VALUE;
    private long maxExecutionTime = 0;
    
    // 执行历史记录 (保留最近的执行记录)
    private static final int MAX_HISTORY_SIZE = 100;
    private List<ExecutionRecord> executionHistory = new ArrayList<>();
    
    // 性能分析
    private long lastSuccessTime = 0;
    private long lastFailureTime = 0;
    private int consecutiveFailures = 0;
    private int maxConsecutiveFailures = 0;
    
    public TaskExecutionInfo(String taskId) {
        this.taskId = taskId;
        this.creationTime = System.currentTimeMillis();
    }
    
    /**
     * 记录一次任务执行
     * @param success 是否执行成功
     * @param executionTime 执行耗时(毫秒)
     */
    public synchronized void recordExecution(boolean success, long executionTime) {
        totalExecutions++;
        lastExecutionTime = System.currentTimeMillis();
        
        // 更新执行时间统计
        totalExecutionTime += executionTime;
        if (executionTime < minExecutionTime) {
            minExecutionTime = executionTime;
        }
        if (executionTime > maxExecutionTime) {
            maxExecutionTime = executionTime;
        }
        
        // 更新成功/失败统计
        if (success) {
            successfulExecutions++;
            lastSuccessTime = lastExecutionTime;
            consecutiveFailures = 0; // 重置连续失败计数
        } else {
            failedExecutions++;
            lastFailureTime = lastExecutionTime;
            consecutiveFailures++;
            if (consecutiveFailures > maxConsecutiveFailures) {
                maxConsecutiveFailures = consecutiveFailures;
            }
        }
        
        // 添加到执行历史
        ExecutionRecord record = new ExecutionRecord(lastExecutionTime, success, executionTime);
        executionHistory.add(record);
        
        // 保持历史记录大小限制
        if (executionHistory.size() > MAX_HISTORY_SIZE) {
            executionHistory.remove(0); // 移除最老的记录
        }
    }
    
    /**
     * 获取任务成功率
     * @return 成功率 (0.0 - 1.0)
     */
    public double getSuccessRate() {
        if (totalExecutions == 0) {
            return 0.0;
        }
        return (double) successfulExecutions / totalExecutions;
    }
    
    /**
     * 获取平均执行时间
     * @return 平均执行时间(毫秒)
     */
    public double getAverageExecutionTime() {
        if (totalExecutions == 0) {
            return 0.0;
        }
        return (double) totalExecutionTime / totalExecutions;
    }
    
    /**
     * 获取任务健康度评分 (0-100)
     * 基于成功率、执行时间稳定性、连续失败情况等综合评估
     * @return 健康度评分
     */
    public int getHealthScore() {
        if (totalExecutions == 0) {
            return 100; // 未执行时认为是健康的
        }
        
        int score = 100;
        
        // 成功率影响 (权重: 40%)
        double successRate = getSuccessRate();
        score -= (int) ((1.0 - successRate) * 40);
        
        // 连续失败影响 (权重: 30%)
        if (consecutiveFailures > 0) {
            score -= Math.min(consecutiveFailures * 10, 30);
        }
        
        // 执行时间稳定性影响 (权重: 20%)
        if (totalExecutions > 1) {
            double avgTime = getAverageExecutionTime();
            double timeVariance = calculateExecutionTimeVariance();
            if (avgTime > 0 && timeVariance / avgTime > 0.5) { // 方差超过均值50%认为不稳定
                score -= 20;
            }
        }
        
        // 最近执行情况影响 (权重: 10%)
        long timeSinceLastExecution = System.currentTimeMillis() - lastExecutionTime;
        if (timeSinceLastExecution > 3600000) { // 超过1小时未执行
            score -= 10;
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * 计算执行时间方差
     * @return 执行时间方差
     */
    private double calculateExecutionTimeVariance() {
        if (executionHistory.size() < 2) {
            return 0.0;
        }
        
        double avgTime = getAverageExecutionTime();
        double sumSquaredDiff = 0.0;
        
        for (ExecutionRecord record : executionHistory) {
            double diff = record.executionTime - avgTime;
            sumSquaredDiff += diff * diff;
        }
        
        return sumSquaredDiff / executionHistory.size();
    }
    
    /**
     * 获取最近N次执行的成功率
     * @param recentCount 最近执行次数
     * @return 最近的成功率
     */
    public double getRecentSuccessRate(int recentCount) {
        if (executionHistory.isEmpty()) {
            return 0.0;
        }
        
        int size = executionHistory.size();
        int startIndex = Math.max(0, size - recentCount);
        int recentSuccesses = 0;
        int recentTotal = 0;
        
        for (int i = startIndex; i < size; i++) {
            if (executionHistory.get(i).success) {
                recentSuccesses++;
            }
            recentTotal++;
        }
        
        return recentTotal > 0 ? (double) recentSuccesses / recentTotal : 0.0;
    }
    
    /**
     * 检查任务是否处于异常状态
     * @return 是否异常
     */
    public boolean isAbnormal() {
        // 连续失败超过5次
        if (consecutiveFailures >= 5) {
            return true;
        }
        
        // 最近10次执行成功率低于30%
        if (totalExecutions >= 10 && getRecentSuccessRate(10) < 0.3) {
            return true;
        }
        
        // 平均执行时间超过30秒
        if (getAverageExecutionTime() > 30000) {
            return true;
        }
        
        return false;
    }
    
    /**
     * 重置统计信息
     */
    public synchronized void reset() {
        totalExecutions = 0;
        successfulExecutions = 0;
        failedExecutions = 0;
        lastExecutionTime = 0;
        totalExecutionTime = 0;
        minExecutionTime = Long.MAX_VALUE;
        maxExecutionTime = 0;
        lastSuccessTime = 0;
        lastFailureTime = 0;
        consecutiveFailures = 0;
        maxConsecutiveFailures = 0;
        executionHistory.clear();
    }
    
    /**
     * 获取执行历史记录的副本
     * @return 执行历史记录列表
     */
    public List<ExecutionRecord> getExecutionHistory() {
        return new ArrayList<>(executionHistory);
    }
    
    /**
     * 获取最近的执行记录
     * @param count 记录数量
     * @return 最近的执行记录
     */
    public List<ExecutionRecord> getRecentExecutions(int count) {
        List<ExecutionRecord> recent = new ArrayList<>();
        int size = executionHistory.size();
        int startIndex = Math.max(0, size - count);
        
        for (int i = startIndex; i < size; i++) {
            recent.add(executionHistory.get(i));
        }
        
        return recent;
    }
    
    // Getter方法
    public String getTaskId() { return taskId; }
    public long getCreationTime() { return creationTime; }
    public int getTotalExecutions() { return totalExecutions; }
    public int getSuccessfulExecutions() { return successfulExecutions; }
    public int getFailedExecutions() { return failedExecutions; }
    public long getLastExecutionTime() { return lastExecutionTime; }
    public long getTotalExecutionTime() { return totalExecutionTime; }
    public long getMinExecutionTime() { return minExecutionTime == Long.MAX_VALUE ? 0 : minExecutionTime; }
    public long getMaxExecutionTime() { return maxExecutionTime; }
    public long getLastSuccessTime() { return lastSuccessTime; }
    public long getLastFailureTime() { return lastFailureTime; }
    public int getConsecutiveFailures() { return consecutiveFailures; }
    public int getMaxConsecutiveFailures() { return maxConsecutiveFailures; }
    
    @Override
    public String toString() {
        return String.format("TaskExecutionInfo{taskId='%s', executions=%d, success=%.1f%%, avgTime=%.1fms, health=%d}",
                           taskId, totalExecutions, getSuccessRate() * 100, 
                           getAverageExecutionTime(), getHealthScore());
    }
    
    /**
     * 执行记录内部类
     */
    public static class ExecutionRecord {
        public final long timestamp;
        public final boolean success;
        public final long executionTime;
        
        public ExecutionRecord(long timestamp, boolean success, long executionTime) {
            this.timestamp = timestamp;
            this.success = success;
            this.executionTime = executionTime;
        }
        
        public long getTimestamp() { return timestamp; }
        public boolean isSuccess() { return success; }
        public long getExecutionTime() { return executionTime; }
        
        @Override
        public String toString() {
            return String.format("ExecutionRecord{time=%d, success=%s, duration=%dms}", 
                               timestamp, success, executionTime);
        }
    }
}