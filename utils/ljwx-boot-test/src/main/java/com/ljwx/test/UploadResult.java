package com.ljwx.test;

/**
 * 上传结果封装类
 */
public class UploadResult {
    
    private boolean success;
    private String endpoint;
    private String deviceSn;
    private String message;
    private int statusCode;
    private long responseTimeMs;
    private int processedCount;
    private int duplicateCount;
    private long processingTimeMs;
    
    public UploadResult() {
    }
    
    public UploadResult(boolean success, String endpoint, String deviceSn, String message) {
        this.success = success;
        this.endpoint = endpoint;
        this.deviceSn = deviceSn;
        this.message = message;
    }
    
    public UploadResult(boolean success, String endpoint, String deviceSn, String message, 
                       int statusCode, long responseTimeMs) {
        this(success, endpoint, deviceSn, message);
        this.statusCode = statusCode;
        this.responseTimeMs = responseTimeMs;
    }
    
    // Getters and Setters
    public boolean isSuccess() {
        return success;
    }
    
    public void setSuccess(boolean success) {
        this.success = success;
    }
    
    public String getEndpoint() {
        return endpoint;
    }
    
    public void setEndpoint(String endpoint) {
        this.endpoint = endpoint;
    }
    
    public String getDeviceSn() {
        return deviceSn;
    }
    
    public void setDeviceSn(String deviceSn) {
        this.deviceSn = deviceSn;
    }
    
    public String getMessage() {
        return message;
    }
    
    public void setMessage(String message) {
        this.message = message;
    }
    
    public int getStatusCode() {
        return statusCode;
    }
    
    public void setStatusCode(int statusCode) {
        this.statusCode = statusCode;
    }
    
    public long getResponseTimeMs() {
        return responseTimeMs;
    }
    
    public void setResponseTimeMs(long responseTimeMs) {
        this.responseTimeMs = responseTimeMs;
    }
    
    public int getProcessedCount() {
        return processedCount;
    }
    
    public void setProcessedCount(int processedCount) {
        this.processedCount = processedCount;
    }
    
    public int getDuplicateCount() {
        return duplicateCount;
    }
    
    public void setDuplicateCount(int duplicateCount) {
        this.duplicateCount = duplicateCount;
    }
    
    public long getProcessingTimeMs() {
        return processingTimeMs;
    }
    
    public void setProcessingTimeMs(long processingTimeMs) {
        this.processingTimeMs = processingTimeMs;
    }
    
    @Override
    public String toString() {
        return "UploadResult{" +
                "success=" + success +
                ", endpoint='" + endpoint + '\'' +
                ", deviceSn='" + deviceSn + '\'' +
                ", message='" + message + '\'' +
                ", statusCode=" + statusCode +
                ", responseTimeMs=" + responseTimeMs +
                ", processedCount=" + processedCount +
                ", duplicateCount=" + duplicateCount +
                ", processingTimeMs=" + processingTimeMs +
                '}';
    }
}