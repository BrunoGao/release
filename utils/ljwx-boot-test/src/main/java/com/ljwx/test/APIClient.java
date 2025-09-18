package com.ljwx.test;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * API客户端，用于调用ljwx-boot的批量上传接口
 * 对应Python版本的APITester类
 */
public class APIClient {
    
    private static final Logger logger = LoggerFactory.getLogger(APIClient.class);
    
    private final String baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    // API端点
    private static final String HEALTH_DATA_ENDPOINT = "/batch/upload_health_data";
    private static final String DEVICE_INFO_ENDPOINT = "/batch/upload_device_info";
    private static final String COMMON_EVENT_ENDPOINT = "/batch/upload_common_event";
    
    public APIClient(String baseUrl) {
        this.baseUrl = baseUrl;
        this.objectMapper = new ObjectMapper();
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }
    
    /**
     * 上传健康数据
     * @param healthDataList 健康数据列表
     * @return 上传结果
     */
    public UploadResult uploadHealthData(List<Map<String, Object>> healthDataList) {
        return makeRequest(HEALTH_DATA_ENDPOINT, healthDataList, "upload_health_data");
    }
    
    /**
     * 上传设备信息
     * @param deviceInfoList 设备信息列表
     * @return 上传结果
     */
    public UploadResult uploadDeviceInfo(List<Map<String, Object>> deviceInfoList) {
        return makeRequest(DEVICE_INFO_ENDPOINT, deviceInfoList, "upload_device_info");
    }
    
    /**
     * 上传通用事件
     * @param commonEvent 通用事件数据
     * @return 上传结果
     */
    public UploadResult uploadCommonEvent(Map<String, Object> commonEvent) {
        return makeRequest(COMMON_EVENT_ENDPOINT, commonEvent, "upload_common_event");
    }
    
    /**
     * 发送HTTP请求
     * @param endpoint API端点
     * @param data 请求数据
     * @param operationType 操作类型
     * @return 上传结果
     */
    private UploadResult makeRequest(String endpoint, Object data, String operationType) {
        try {
            // 序列化请求数据
            String jsonData = objectMapper.writeValueAsString(data);
            
            // 构建HTTP请求
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + endpoint))
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(jsonData))
                    .timeout(Duration.ofSeconds(30))
                    .build();
            
            // 发送请求
            long startTime = System.currentTimeMillis();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            long responseTime = System.currentTimeMillis() - startTime;
            
            // 解析响应
            UploadResult result = parseResponse(response, operationType, responseTime);
            
            if (logger.isDebugEnabled()) {
                logger.debug("API调用: {} | 状态码: {} | 响应时间: {}ms | 成功: {}", 
                           endpoint, response.statusCode(), responseTime, result.isSuccess());
            }
            
            return result;
            
        } catch (IOException e) {
            String errorMsg = "网络请求失败: " + e.getMessage();
            logger.error("API调用失败 [{}]: {}", operationType, errorMsg);
            return new UploadResult(false, operationType, null, errorMsg);
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            String errorMsg = "请求被中断: " + e.getMessage();
            logger.error("API调用中断 [{}]: {}", operationType, errorMsg);
            return new UploadResult(false, operationType, null, errorMsg);
            
        } catch (Exception e) {
            String errorMsg = "未知错误: " + e.getMessage();
            logger.error("API调用异常 [{}]: {}", operationType, errorMsg, e);
            return new UploadResult(false, operationType, null, errorMsg);
        }
    }
    
    /**
     * 解析HTTP响应
     * @param response HTTP响应
     * @param operationType 操作类型
     * @param responseTime 响应时间
     * @return 上传结果
     */
    private UploadResult parseResponse(HttpResponse<String> response, String operationType, long responseTime) {
        try {
            // 检查HTTP状态码
            int statusCode = response.statusCode();
            String responseBody = response.body();
            
            if (statusCode != 200) {
                String errorMsg = String.format("HTTP错误: %d, 响应: %s", statusCode, responseBody);
                return new UploadResult(false, operationType, null, errorMsg, statusCode, responseTime);
            }
            
            // 解析JSON响应
            Map<String, Object> responseMap = objectMapper.readValue(responseBody, new TypeReference<Map<String, Object>>() {});
            
            // 检查业务成功状态
            boolean success = isSuccessResponse(responseMap);
            String message = extractMessage(responseMap);
            
            UploadResult result = new UploadResult(success, operationType, null, message, statusCode, responseTime);
            
            // 提取详细信息
            if (responseMap.containsKey("result") && responseMap.get("result") instanceof Map) {
                Map<String, Object> resultData = (Map<String, Object>) responseMap.get("result");
                result.setProcessedCount(extractIntValue(resultData, "processed", 0));
                result.setDuplicateCount(extractIntValue(resultData, "duplicates", 0));
                result.setProcessingTimeMs(extractLongValue(resultData, "processing_time_ms", responseTime));
            }
            
            return result;
            
        } catch (Exception e) {
            String errorMsg = "响应解析失败: " + e.getMessage();
            logger.error("响应解析异常 [{}]: {}", operationType, errorMsg, e);
            return new UploadResult(false, operationType, null, errorMsg, response.statusCode(), responseTime);
        }
    }
    
    /**
     * 判断响应是否成功
     */
    private boolean isSuccessResponse(Map<String, Object> response) {
        // 检查success字段
        Object success = response.get("success");
        if (success instanceof Boolean) {
            return (Boolean) success;
        }
        
        // 检查code字段
        Object code = response.get("code");
        if (code instanceof Number) {
            return ((Number) code).intValue() == 200;
        }
        
        // 默认根据是否有错误信息判断
        return !response.containsKey("error") && !response.containsKey("message") 
               || response.containsKey("result");
    }
    
    /**
     * 提取响应消息
     */
    private String extractMessage(Map<String, Object> response) {
        Object message = response.get("message");
        if (message instanceof String) {
            return (String) message;
        }
        
        Object error = response.get("error");
        if (error instanceof String) {
            return (String) error;
        }
        
        return "无消息";
    }
    
    /**
     * 提取整数值
     */
    private int extractIntValue(Map<String, Object> data, String key, int defaultValue) {
        Object value = data.get(key);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return defaultValue;
    }
    
    /**
     * 提取长整数值
     */
    private long extractLongValue(Map<String, Object> data, String key, long defaultValue) {
        Object value = data.get(key);
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        return defaultValue;
    }
    
    /**
     * 测试API连通性
     * @return 是否连通
     */
    public boolean testConnection() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/batch/health"))
                    .header("Accept", "application/json")
                    .GET()
                    .timeout(Duration.ofSeconds(5))
                    .build();
            
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            return response.statusCode() == 200;
            
        } catch (Exception e) {
            logger.warn("连通性测试失败: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 获取服务统计信息
     * @return 统计信息，如果失败返回null
     */
    public Map<String, Object> getServiceStats() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/batch/stats"))
                    .header("Accept", "application/json")
                    .GET()
                    .timeout(Duration.ofSeconds(5))
                    .build();
            
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() == 200) {
                Map<String, Object> responseMap = objectMapper.readValue(response.body(), new TypeReference<Map<String, Object>>() {});
                if (responseMap.containsKey("result")) {
                    return (Map<String, Object>) responseMap.get("result");
                }
            }
        } catch (Exception e) {
            logger.warn("获取统计信息失败: {}", e.getMessage());
        }
        return null;
    }
}