# ljwx-boot 数据上传API详细流程分析

## 概述

本文档详细分析 ljwx-boot 系统中三个核心数据上传API的实现流程：
- `upload_health_data` - 健康数据上传
- `upload_device_info` - 设备信息上传  
- `upload_common_event` - 通用事件上传

这些API是从 Python ljwx-bigscreen 迁移而来，保持完全兼容性的同时提供了更高的性能和更好的扩展性。

## API架构概览

### 系统架构
```
设备端/客户端
    ↓ HTTP POST
Controller层 (BatchUploadController / HealthDataStreamController)
    ↓ 业务逻辑
Service层 (HealthDataOptimizer / Stream Services)
    ↓ 数据处理
数据持久化层 (MyBatis-Plus / Redis缓存)
```

### 认证与安全
- 🔓 **设备端接口无需认证** - 所有上传接口在 `InterceptorConfiguration` 中配置为免认证
- 支持Python兼容路径（下划线）和Java标准路径（连字符）
- 全局请求拦截器记录请求日志和性能指标

## 1. upload_health_data API 详细分析

### 1.1 接口定义

#### 控制器层
**主要实现**: `BatchUploadController.java:70-102`

```java
@PostMapping("/upload-health-data")  // Java标准路径
@PostMapping("/upload_health_data")  // Python兼容路径
public Result<Map<String, Object>> uploadHealthData(
    @RequestBody List<Map<String, Object>> healthDataList
)
```

#### Stream接口
**备用实现**: `HealthDataStreamController.java:78-99`

```java
@PostMapping("/upload_health_data")
public Result<Map<String, Object>> uploadHealthData(
    @RequestBody HealthDataUploadRequest request,
    @RequestHeader(value = "X-Device-SN", required = false) String deviceSn,
    @RequestHeader(value = "X-Customer-ID", required = false) String customerId
)
```

### 1.2 数据处理流程

#### 1.2.1 数据接收与验证
```
接收健康数据列表 → 数据验证 → 字段映射转换
```

**Python字段映射** (`HealthDataOptimizer.java:124-143`):
```java
private static final Map<String, String> PYTHON_FIELD_MAPPING = {
    "heart_rate" → "heart_rate",
    "blood_oxygen" → "blood_oxygen", 
    "temperature" → "body_temperature",
    "pressure_high" → "blood_pressure_systolic",
    "pressure_low" → "blood_pressure_diastolic",
    "stress" → "stress",
    "step" → "step",
    "distance" → "distance",
    "calorie" → "calorie",
    "sleep" → "sleepData",
    "workout_data" → "workoutData"
};
```

#### 1.2.2 数据转换与验证 (`HealthDataOptimizer.java:270-308`)

```java
private TUserHealthData transformSingleHealthData(Map<String, Object> data) {
    TUserHealthData healthData = new TUserHealthData();
    
    // 基础字段映射
    healthData.setDeviceSn(getStringValue(data, "device_id"));
    healthData.setUserId(parseLong(data.get("user_id")));
    healthData.setOrgId(parseLong(data.get("org_id")));
    healthData.setCustomerId(parseLong(data.get("customer_id")));
    
    // 健康指标字段映射
    for (Map.Entry<String, String> mapping : PYTHON_FIELD_MAPPING.entrySet()) {
        String pythonField = mapping.getKey();
        Object value = data.get(pythonField);
        if (value != null) {
            setHealthDataField(healthData, pythonField, value);
        }
    }
    
    // 时间字段处理
    healthData.setCreateTime(parseDateTime(data.get("create_time")));
    
    return healthData;
}
```

#### 1.2.3 重复检测机制 (`HealthDataOptimizer.java:313-335`)

```java
private List<TUserHealthData> performDuplicateDetection(List<TUserHealthData> dataList) {
    Set<String> currentBatchKeys = new HashSet<>();
    
    return dataList.stream()
        .filter(data -> {
            String duplicateKey = generateDuplicateKey(data);
            
            // 检查Redis缓存中的重复记录
            String redisKey = "health_data_key:" + duplicateKey;
            Boolean exists = redisTemplate.hasKey(redisKey);
            
            if (Boolean.TRUE.equals(exists) || currentBatchKeys.contains(duplicateKey)) {
                duplicateCount.incrementAndGet();
                return false;
            }
            
            // 记录到Redis缓存 (24小时过期)
            redisTemplate.opsForValue().set(redisKey, "1", Duration.ofHours(24));
            currentBatchKeys.add(duplicateKey);
            return true;
        })
        .collect(Collectors.toList());
}
```

**去重键生成算法**:
```java
private String generateDuplicateKey(TUserHealthData data) {
    return String.format("%s_%s_%s", 
        data.getDeviceSn(), 
        data.getCreateTime(), 
        data.getHeartRate()
    );
}
```

#### 1.2.4 CPU自适应分片处理 (`HealthDataOptimizer.java:340-357`)

```java
private void processDataInAdaptiveShards(List<TUserHealthData> dataList) {
    // 按设备ID分片 (利用CPU核心数)
    Map<Integer, List<TUserHealthData>> shards = dataList.stream()
        .collect(Collectors.groupingBy(data -> 
            Math.abs(data.getDeviceSn().hashCode()) % cpuCores
        ));
    
    // 并行处理各分片
    List<CompletableFuture<Void>> futures = shards.entrySet().stream()
        .map(entry -> CompletableFuture.runAsync(
            () -> processSingleShard(entry.getValue()),
            executor
        ))
        .collect(Collectors.toList());
    
    // 等待所有分片完成
    CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
}
```

#### 1.2.5 性能优化配置 (`HealthDataOptimizer.java:69-83`)

```java
// CPU自适应配置
private final int cpuCores = Runtime.getRuntime().availableProcessors();
private final long memoryMb = Runtime.getRuntime().maxMemory() / (1024 * 1024);

// 动态批次配置：CPU核心数 × 25，限制在50-500之间
private final int batchSize = Math.max(50, Math.min(500, cpuCores * 25));
private final int batchTimeoutSeconds = 2;

// 动态线程池配置：CPU核心数 × 2.5 (I/O密集型)
private final int maxWorkers = Math.max(4, Math.min(32, (int) (cpuCores * 2.5)));
```

### 1.3 处理结果响应

**成功响应格式** (`HealthDataOptimizer.java:385-395`):
```json
{
    "success": true,
    "message": "数据处理成功",
    "processed": 1250,
    "duplicates": 15,
    "processing_time_ms": 856,
    "batch_size": 200,
    "shard_count": 8
}
```

## 2. upload_device_info API 详细分析

### 2.1 接口定义

#### 控制器层
**主要实现**: `BatchUploadController.java:111-143`

```java
@PostMapping("/upload-device-info")  // Java标准路径
@PostMapping("/upload_device_info")  // Python兼容路径
public Result<Map<String, Object>> uploadDeviceInfo(
    @RequestBody List<Map<String, Object>> deviceDataList
)
```

### 2.2 数据处理流程

#### 2.2.1 设备数据转换 (`HealthDataOptimizer.java:465-485`)

```java
private List<TDeviceInfo> validateAndTransformDeviceData(List<Map<String, Object>> deviceDataList) {
    return deviceDataList.stream()
        .map(this::transformSingleDeviceData)
        .filter(Objects::nonNull)
        .collect(Collectors.toList());
}

private TDeviceInfo transformSingleDeviceData(Map<String, Object> data) {
    try {
        TDeviceInfo deviceInfo = new TDeviceInfo();
        deviceInfo.setSerialNumber(getStringValue(data, "device_id"));
        deviceInfo.setDeviceName(getStringValue(data, "device_name"));
        deviceInfo.setCustomerId(parseLong(data.get("customer_id")));
        return deviceInfo;
    } catch (Exception e) {
        log.warn("设备数据转换失败: {}", data, e);
        return null;
    }
}
```

#### 2.2.2 设备去重机制 (`HealthDataOptimizer.java:487-498`)

```java
private List<TDeviceInfo> removeDuplicateDevices(List<TDeviceInfo> devices) {
    return devices.stream()
        .collect(Collectors.toMap(
            TDeviceInfo::getSerialNumber,  // 以设备序列号为键
            device -> device,
            (existing, replacement) -> existing  // 保留已存在的设备
        ))
        .values()
        .stream()
        .collect(Collectors.toList());
}
```

#### 2.2.3 批量处理 (`HealthDataOptimizer.java:500-503`)

```java
private void processDeviceDataInBatches(List<TDeviceInfo> devices) {
    // 批量处理设备数据
    deviceInfoService.saveBatch(devices);
}
```

### 2.3 处理结果响应

**成功响应格式**:
```json
{
    "success": true,
    "processed": 45,
    "total": 50,
    "duplicates": 5,
    "processing_time_ms": 234
}
```

## 3. upload_common_event API 详细分析

### 3.1 接口定义

#### 控制器层
**主要实现**: `BatchUploadController.java:153-186`

```java
@PostMapping("/upload-common-event")  // Java标准路径
@PostMapping("/upload_common_event")  // Python兼容路径
public Result<Map<String, Object>> uploadCommonEvent(
    @RequestBody Map<String, Object> eventData
)
```

#### Stream接口
**详细实现**: `HealthDataStreamController.java:130-147`

```java
@PostMapping("/upload_common_event")
public Result<Map<String, Object>> uploadCommonEvent(
    @RequestBody CommonEventUploadRequest request
)
```

### 3.2 复合数据处理流程

#### 3.2.1 事件数据分离处理 (`HealthDataOptimizer.java:228-265`)

```java
public Result<Map<String, Object>> uploadCommonEvent(Map<String, Object> eventData) {
    Map<String, Object> result = new HashMap<>();
    result.put("success", true);
    
    // 1. 处理健康数据部分
    if (eventData.containsKey("health_data")) {
        List<Map<String, Object>> healthData = (List<Map<String, Object>>) eventData.get("health_data");
        Result<Map<String, Object>> healthResult = uploadHealthData(healthData);
        result.put("health_result", healthResult.getResult());
    }
    
    // 2. 处理设备信息部分
    if (eventData.containsKey("device_info")) {
        List<Map<String, Object>> deviceData = (List<Map<String, Object>>) eventData.get("device_info");
        Result<Map<String, Object>> deviceResult = uploadDeviceInfo(deviceData);
        result.put("device_result", deviceResult.getResult());
    }
    
    // 3. 处理其他事件数据
    if (eventData.containsKey("alert_data")) {
        processAlertEvents(eventData.get("alert_data"));
        result.put("alert_result", Map.of("success", true));
    }
    
    return Result.ok(result);
}
```

### 3.3 事件处理详细流程 (`CommonEventStreamServiceImpl.java`)

#### 3.3.1 单个事件处理 (`CommonEventStreamServiceImpl.java:79-145`)

```java
private Result<Map<String, Object>> processSingleEvent(CommonEventUploadRequest request) {
    // 基础验证
    if (!StringUtils.hasText(request.getEventType())) {
        return Result.failure("事件类型不能为空");
    }
    
    if (!StringUtils.hasText(request.getDeviceSn()) && !StringUtils.hasText(request.getUserId())) {
        return Result.failure("设备SN或用户ID至少需要提供一个");
    }
    
    // 构建告警数据
    Map<String, Object> alertData = buildAlertData(request);
    
    // 根据事件类型和级别确定处理优先级
    boolean isEmergency = isEmergencyEvent(request.getEventType(), request.getEventLevel());
    
    if (isEmergency) {
        // 紧急事件立即处理
        boolean processed = processEmergencyEvent(alertData);
        if (processed) {
            result.put("priority", "emergency");
            result.put("immediateAlert", true);
        }
    } else {
        // 普通事件异步处理
        boolean queued = queueNormalEvent(alertData);
        if (queued) {
            result.put("priority", "normal");
            result.put("queued", true);
        }
    }
    
    return Result.data(result);
}
```

#### 3.3.2 紧急事件识别 (`CommonEventStreamServiceImpl.java:282-290`)

```java
private boolean isEmergencyEvent(String eventType, String eventLevel) {
    // 紧急事件类型
    Set<String> emergencyTypes = Set.of("SOS", "FALL", "HEART_ATTACK", "ABNORMAL_HEART_RATE");
    
    // 紧急级别
    Set<String> emergencyLevels = Set.of("CRITICAL", "EMERGENCY");
    
    return emergencyTypes.contains(eventType) || emergencyLevels.contains(eventLevel);
}
```

#### 3.3.3 告警数据构建 (`CommonEventStreamServiceImpl.java:214-277`)

```java
private Map<String, Object> buildAlertData(CommonEventUploadRequest request) {
    Map<String, Object> alertData = new HashMap<>();
    
    alertData.put("eventId", request.getEventId());
    alertData.put("eventType", request.getEventType());
    alertData.put("eventLevel", request.getEventLevel() != null ? request.getEventLevel() : "WARNING");
    alertData.put("deviceSn", request.getDeviceSn());
    alertData.put("userId", request.getUserId());
    alertData.put("customerId", request.getCustomerId());
    alertData.put("orgId", request.getOrgId());
    alertData.put("eventDescription", request.getEventDescription());
    alertData.put("priority", request.getPriority() != null ? request.getPriority() : 3);
    alertData.put("immediateNotification", request.getImmediateNotification() != null ? request.getImmediateNotification() : false);
    
    // 时间处理
    if (request.getEventTime() != null) {
        LocalDateTime eventTime = Instant.ofEpochMilli(request.getEventTime())
                .atZone(ZoneId.systemDefault())
                .toLocalDateTime();
        alertData.put("eventTime", eventTime);
    } else {
        alertData.put("eventTime", LocalDateTime.now());
    }
    
    // 位置、健康数据、事件详情等
    if (request.getLocation() != null) alertData.put("location", request.getLocation());
    if (request.getHealthData() != null) alertData.put("healthData", request.getHealthData());
    if (request.getEventDetails() != null) alertData.put("eventDetails", request.getEventDetails());
    
    return alertData;
}
```

#### 3.3.4 批量事件处理 (`CommonEventStreamServiceImpl.java:150-209`)

```java
private Result<Map<String, Object>> processBatchEvents(List<CommonEventUploadRequest> batchEvents) {
    int successCount = 0;
    int emergencyCount = 0;
    int errorCount = 0;
    List<Map<String, Object>> results = new ArrayList<>();
    
    for (int i = 0; i < batchEvents.size(); i++) {
        CommonEventUploadRequest event = batchEvents.get(i);
        
        try {
            Result<Map<String, Object>> eventResult = processSingleEvent(event);
            Map<String, Object> resultData = eventResult.getData();
            results.add(resultData);
            
            if (eventResult.getCode() == 200) {
                successCount++;
                if ("emergency".equals(resultData.get("priority"))) {
                    emergencyCount++;
                }
            } else {
                errorCount++;
            }
            
        } catch (Exception e) {
            errorCount++;
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("eventId", event.getEventId());
            errorResult.put("error", e.getMessage());
            results.add(errorResult);
        }
    }
    
    // 构建批量处理结果
    Map<String, Object> batchResult = new HashMap<>();
    batchResult.put("success", true);
    batchResult.put("totalCount", batchEvents.size());
    batchResult.put("successCount", successCount);
    batchResult.put("emergencyCount", emergencyCount);
    batchResult.put("errorCount", errorCount);
    batchResult.put("results", results);
    
    return Result.data(batchResult);
}
```

### 3.4 处理结果响应

**单个事件响应**:
```json
{
    "success": true,
    "eventId": "event_123",
    "eventType": "SOS", 
    "priority": "emergency",
    "immediateAlert": true,
    "processedCount": 1
}
```

**批量事件响应**:
```json
{
    "success": true,
    "totalCount": 100,
    "successCount": 95,
    "emergencyCount": 5,
    "errorCount": 5,
    "message": "批量事件处理完成: 成功95(紧急5), 失败5",
    "results": [...]
}
```

## 4. 统一技术特性

### 4.1 认证与权限

**免认证配置** (`InterceptorConfiguration.java:51-73`):
```java
// 设备端API放行接口（Python ljwx-bigscreen 迁移，设备端无需认证）
public final String[] deviceApiExcludePatterns = new String[]{
    "/batch/upload-health-data",      // 健康数据批量上传
    "/batch/upload_health_data",      // Python兼容路径
    "/batch/upload-device-info",      // 设备信息批量上传  
    "/batch/upload_device_info",      // Python兼容路径
    "/batch/upload-common-event",     // 通用事件上传
    "/batch/upload_common_event",     // Python兼容路径
    "/batch/stats",                   // 批处理统计信息
    "/batch/performance-test",        // 性能测试
    "/batch/health"                   // 批处理服务健康检查
};
```

### 4.2 性能监控

**统计信息接口** (`BatchUploadController.java:194-209`):
```java
@GetMapping("/batch/stats")
public Result<Map<String, Object>> getBatchStats() {
    Map<String, Object> stats = healthDataOptimizer.getOptimizerStats();
    
    stats.put("service_status", "running");
    stats.put("timestamp", System.currentTimeMillis());
    stats.put("version", "java-migrated-v1.0");
    
    return Result.ok(stats);
}
```

**性能统计数据**:
```json
{
    "processed": 125870,
    "batches": 629,
    "errors": 15,
    "duplicates": 234,
    "queue_size": 0,
    "active_threads": 4,
    "cpu_cores": 8,
    "batch_size": 200,
    "service_status": "running",
    "timestamp": 1703587456789,
    "version": "java-migrated-v1.0"
}
```

### 4.3 健康检查

**服务健康检查** (`BatchUploadController.java:257-280`):
```java
@GetMapping("/batch/health")
public Result<Map<String, Object>> healthCheck() {
    Map<String, Object> health = Map.of(
        "service", "BatchUploadService",
        "status", "healthy",
        "features", Map.of(
            "upload_health_data", "available",
            "upload_device_info", "available", 
            "upload_common_event", "available",
            "performance_test", "available",
            "python_compatibility", "100%"
        ),
        "optimizer_stats", healthDataOptimizer.getOptimizerStats()
    );
    
    return Result.ok(health);
}
```

### 4.4 性能测试

**性能测试接口** (`BatchUploadController.java:216-251`):
```java
@PostMapping("/batch/performance-test")
public Result<Map<String, Object>> performanceTest(
    @RequestParam(defaultValue = "1000") int dataSize) {
    
    long startTime = System.currentTimeMillis();
    
    // 生成测试数据
    List<Map<String, Object>> testData = generateTestHealthData(dataSize);
    
    // 执行批量上传
    Result<Map<String, Object>> uploadResult = healthDataOptimizer.uploadHealthData(testData);
    
    long totalTime = System.currentTimeMillis() - startTime;
    
    Map<String, Object> testResult = Map.of(
        "test_data_size", dataSize,
        "total_time_ms", totalTime,
        "qps", dataSize * 1000.0 / totalTime,
        "upload_result", uploadResult.getResult(),
        "performance_rating", totalTime < 5000 ? "优秀" : totalTime < 10000 ? "良好" : "需优化"
    );
    
    return Result.ok(testResult);
}
```

## 5. 最佳实践建议

### 5.1 客户端调用示例

#### 健康数据上传
```bash
curl -X POST http://localhost:8080/batch/upload_health_data \
  -H "Content-Type: application/json" \
  -d '[{
    "device_id": "DEVICE_001",
    "user_id": "123",
    "org_id": "456", 
    "customer_id": "8",
    "heart_rate": 75,
    "blood_oxygen": 98,
    "temperature": 36.5,
    "step": 8500,
    "create_time": "2024-01-15 14:30:00"
  }]'
```

#### 设备信息上传
```bash
curl -X POST http://localhost:8080/batch/upload_device_info \
  -H "Content-Type: application/json" \
  -d '[{
    "device_id": "DEVICE_001",
    "device_name": "Smart Watch v2",
    "customer_id": "8",
    "battery_level": 85,
    "firmware_version": "2.1.3"
  }]'
```

#### 通用事件上传
```bash
curl -X POST http://localhost:8080/batch/upload_common_event \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "SOS",
    "eventLevel": "CRITICAL",
    "deviceSn": "DEVICE_001",
    "userId": "123",
    "customerId": "8",
    "eventDescription": "紧急求救",
    "immediateNotification": true,
    "location": {"lat": 39.9042, "lng": 116.4074}
  }'
```

### 5.2 错误处理

所有API都遵循统一的错误响应格式：
```json
{
    "code": 500,
    "message": "数据处理失败: 字段验证错误",
    "success": false,
    "result": null,
    "timestamp": 1703587456789
}
```

### 5.3 监控与告警

1. **定期检查服务健康状态**: `GET /batch/health`
2. **监控处理统计**: `GET /batch/stats`
3. **性能基准测试**: `POST /batch/performance-test`
4. **查看实时日志**: 关注 `BatchUploadController` 和 `HealthDataOptimizer` 的日志输出

## 6. 总结

ljwx-boot 的三个核心上传API通过以下技术特性实现了高性能和高可用性：

1. **Python兼容性**: 完全兼容原有Python接口，零成本迁移
2. **性能优化**: CPU自适应分片、并行处理、智能批处理
3. **数据完整性**: 去重检测、数据验证、事务处理
4. **监控完善**: 实时统计、健康检查、性能测试
5. **扩展性强**: 模块化设计、可配置参数、插件式架构

这些API为灵境万象系统提供了稳定可靠的数据接入能力，支撑了设备端到服务端的高效数据传输。