package com.ljwx.watch.communication;

import ohos.hiviewdfx.HiLog;
import ohos.hiviewdfx.HiLogLabel;

/**
 * 通信任务抽象类
 * 封装HTTP通信任务的基本信息和回调处理
 */
public abstract class CommunicationTask {
    private static final HiLogLabel LABEL_LOG = new HiLogLabel(HiLog.LOG_APP, 0x01100, "ljwx-log");
    
    private final String taskId;
    private final String url;
    private final String method;
    private final String requestData;
    private final Priority priority;
    private final long createTime;
    
    private int retryCount = 0;
    private String lastError = null;
    
    /**
     * 任务优先级枚举
     */
    public enum Priority {
        LOW(1),
        MEDIUM(2), 
        HIGH(3),
        CRITICAL(4);
        
        private final int value;
        
        Priority(int value) {
            this.value = value;
        }
        
        public int getValue() {
            return value;
        }
    }
    
    public CommunicationTask(String taskId, String url, String method, String requestData, Priority priority) {
        this.taskId = taskId;
        this.url = url;
        this.method = method;
        this.requestData = requestData;
        this.priority = priority;
        this.createTime = System.currentTimeMillis();
    }
    
    /**
     * 成功回调
     */
    public abstract void onSuccess(String response);
    
    /**
     * 失败回调
     */
    public abstract void onError(String error);
    
    /**
     * 获取任务ID
     */
    public String getTaskId() {
        return taskId;
    }
    
    /**
     * 获取请求URL
     */
    public String getUrl() {
        return url;
    }
    
    /**
     * 获取HTTP方法
     */
    public String getMethod() {
        return method;
    }
    
    /**
     * 获取请求数据
     */
    public String getRequestData() {
        return requestData;
    }
    
    /**
     * 获取优先级数值
     */
    public int getPriority() {
        return priority.getValue();
    }
    
    /**
     * 获取创建时间
     */
    public long getCreateTime() {
        return createTime;
    }
    
    /**
     * 获取重试次数
     */
    public int getRetryCount() {
        return retryCount;
    }
    
    /**
     * 增加重试次数
     */
    public void incrementRetryCount() {
        this.retryCount++;
    }
    
    /**
     * 设置最后错误信息
     */
    public void setLastError(String error) {
        this.lastError = error;
    }
    
    /**
     * 获取最后错误信息
     */
    public String getLastError() {
        return lastError;
    }
    
    /**
     * 检查任务是否过期
     */
    public boolean isExpired(long maxAgeMs) {
        return (System.currentTimeMillis() - createTime) > maxAgeMs;
    }
    
    /**
     * 获取任务年龄（毫秒）
     */
    public long getAge() {
        return System.currentTimeMillis() - createTime;
    }
    
    @Override
    public String toString() {
        return String.format("CommunicationTask{id='%s', method='%s', url='%s', priority=%s, retries=%d, age=%dms}", 
                           taskId, method, url, priority, retryCount, getAge());
    }
    
    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        
        CommunicationTask task = (CommunicationTask) obj;
        return taskId.equals(task.taskId);
    }
    
    @Override
    public int hashCode() {
        return taskId.hashCode();
    }
}