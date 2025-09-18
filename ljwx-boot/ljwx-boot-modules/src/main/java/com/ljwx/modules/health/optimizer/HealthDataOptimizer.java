/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.optimizer;

import com.ljwx.common.api.vo.Result;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 健康数据性能优化器
 * 
 * 基于ljwx-bigscreen的HealthDataOptimizer优化算法，提供：
 * - CPU自适应批处理
 * - 异步队列处理
 * - 重复数据检测
 * - 性能监控和自适应调整
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName HealthDataOptimizer
 * @CreateTime 2024-12-16
 */
@Slf4j
@Component
public class HealthDataOptimizer {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private ITUserHealthDataService userHealthDataService;
    
    @Autowired
    private ITDeviceInfoService deviceInfoService;
    
    // CPU自适应配置
    private final int cpuCores = Runtime.getRuntime().availableProcessors();
    private final long memoryMb = Runtime.getRuntime().maxMemory() / (1024 * 1024);
    
    // 动态批次配置：CPU核心数 × 25，限制在50-500之间
    private final int batchSize = Math.max(50, Math.min(500, cpuCores * 25));
    private final int batchTimeoutSeconds = 2;
    
    // 动态线程池配置：CPU核心数 × 2.5 (I/O密集型)
    private final int maxWorkers = Math.max(4, Math.min(32, (int) (cpuCores * 2.5)));
    
    // 批处理队列和线程池
    private final BlockingQueue<HealthDataBatch> batchQueue = new LinkedBlockingQueue<>(5000);
    private final ThreadPoolExecutor executor;
    private volatile boolean running = true;
    
    // 统计信息
    private final AtomicLong processedCount = new AtomicLong(0);
    private final AtomicLong batchCount = new AtomicLong(0);
    private final AtomicLong errorCount = new AtomicLong(0);
    private final AtomicLong duplicateCount = new AtomicLong(0);
    
    // 已处理记录键值集合（防重复）
    private final Set<String> processedKeys = ConcurrentHashMap.newKeySet();
    
    // 性能监控
    private final List<Long> performanceWindow = Collections.synchronizedList(new ArrayList<>());
    private volatile long lastAdjustmentTime = System.currentTimeMillis();

    public HealthDataOptimizer(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        
        // 初始化线程池
        this.executor = new ThreadPoolExecutor(
            maxWorkers / 2,  // 核心线程数
            maxWorkers,      // 最大线程数
            60L,             // 空闲时间
            TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),
            r -> new Thread(r, "health-data-optimizer-" + System.currentTimeMillis())
        );
        
        log.info("🚀 HealthDataOptimizer 初始化:");
        log.info("   CPU核心: {}, 内存: {}MB", cpuCores, memoryMb);
        log.info("   批次大小: {}, 工作线程: {}", batchSize, maxWorkers);
        
        // 启动批处理任务
        startBatchProcessor();
    }
    
    // ============= Python功能迁移 =============
    
    /**
     * Python字段映射表 (从health_data_batch_processor.py迁移)
     */
    private static final Map<String, String> PYTHON_FIELD_MAPPING;
    static {
        Map<String, String> mapping = new HashMap<>();
        mapping.put("heart_rate", "heart_rate");
        mapping.put("blood_oxygen", "blood_oxygen");
        mapping.put("temperature", "body_temperature");
        mapping.put("pressure_high", "blood_pressure_systolic");
        mapping.put("pressure_low", "blood_pressure_diastolic");
        mapping.put("stress", "stress");
        mapping.put("step", "step");
        mapping.put("distance", "distance");
        mapping.put("calorie", "calorie");
        mapping.put("latitude", "latitude");
        mapping.put("longitude", "longitude");
        mapping.put("altitude", "altitude");
        mapping.put("sleep", "sleepData");
        mapping.put("sleep_data", "sleepData");
        mapping.put("workout_data", "workoutData");
        PYTHON_FIELD_MAPPING = Collections.unmodifiableMap(mapping);
    }
    
    /**
     * 健康数据批量上传 (迁移自 Python health_data_batch_processor.py:upload_health_data)
     */
    public Result<Map<String, Object>> uploadHealthData(List<Map<String, Object>> healthDataList) {
        long startTime = System.currentTimeMillis();
        log.info("🚀 开始健康数据批量上传，数据量: {}", healthDataList.size());
        
        try {
            // 1. 数据验证和转换 (复用Python验证逻辑)
            List<TUserHealthData> validatedData = validateAndTransformHealthData(healthDataList);
            log.debug("数据验证完成，有效数据: {}", validatedData.size());
            
            // 2. 重复检测 (复用Python去重逻辑)
            List<TUserHealthData> deduplicatedData = performDuplicateDetection(validatedData);
            log.debug("去重完成，最终数据: {}", deduplicatedData.size());
            
            // 3. 分片批处理 (复用Python的分片策略)
            processDataInAdaptiveShards(deduplicatedData);
            
            // 4. 更新统计信息
            long processed = deduplicatedData.size();
            long duplicates = validatedData.size() - processed;
            
            processedCount.addAndGet(processed);
            batchCount.incrementAndGet();
            duplicateCount.addAndGet(duplicates);
            
            // 5. 构建响应结果 (保持Python接口兼容)
            long processingTime = System.currentTimeMillis() - startTime;
            Map<String, Object> result = buildSuccessResponse(processed, duplicates, processingTime);
            
            log.info("✅ 批量健康数据处理完成: 处理{}条，去重{}条，耗时{}ms", 
                processed, duplicates, processingTime);
            
            return Result.ok(result);
            
        } catch (Exception e) {
            errorCount.incrementAndGet();
            long errorTime = System.currentTimeMillis() - startTime;
            log.error("❌ 批量健康数据处理失败，耗时{}ms", errorTime, e);
            
            return Result.error("上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 设备信息批量上传 (迁移自 Python device_batch_processor.py)
     */
    public Result<Map<String, Object>> uploadDeviceInfo(List<Map<String, Object>> deviceDataList) {
        long startTime = System.currentTimeMillis();
        log.info("🚀 开始设备信息批量上传，数据量: {}", deviceDataList.size());
        
        try {
            // 1. 设备数据验证和转换
            List<TDeviceInfo> validatedDevices = validateAndTransformDeviceData(deviceDataList);
            
            // 2. 设备信息去重
            List<TDeviceInfo> deduplicatedDevices = removeDuplicateDevices(validatedDevices);
            
            // 3. 批量处理设备数据
            processDeviceDataInBatches(deduplicatedDevices);
            
            long processingTime = System.currentTimeMillis() - startTime;
            Map<String, Object> result = Map.of(
                "success", true,
                "processed", deduplicatedDevices.size(),
                "total", deviceDataList.size(),
                "duplicates", validatedDevices.size() - deduplicatedDevices.size(),
                "processing_time_ms", processingTime
            );
            
            log.info("✅ 批量设备信息处理完成: {}", result);
            return Result.ok(result);
            
        } catch (Exception e) {
            log.error("❌ 批量设备信息处理失败", e);
            return Result.error("设备信息上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 通用事件上传 (迁移自 Python upload_common_event逻辑)
     */
    public Result<Map<String, Object>> uploadCommonEvent(Map<String, Object> eventData) {
        log.info("🚀 开始处理通用事件");
        
        try {
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            
            // 1. 处理健康数据部分
            if (eventData.containsKey("health_data")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> healthData = (List<Map<String, Object>>) eventData.get("health_data");
                Result<Map<String, Object>> healthResult = uploadHealthData(healthData);
                result.put("health_result", healthResult.getResult());
            }
            
            // 2. 处理设备信息部分
            if (eventData.containsKey("device_info")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> deviceData = (List<Map<String, Object>>) eventData.get("device_info");
                Result<Map<String, Object>> deviceResult = uploadDeviceInfo(deviceData);
                result.put("device_result", deviceResult.getResult());
            }
            
            // 3. 处理其他事件数据
            if (eventData.containsKey("alert_data")) {
                // 集成告警处理
                processAlertEvents(eventData.get("alert_data"));
                result.put("alert_result", Map.of("success", true));
            }
            
            log.info("✅ 通用事件处理完成");
            return Result.ok(result);
            
        } catch (Exception e) {
            log.error("❌ 通用事件处理失败", e);
            return Result.error("通用事件处理失败: " + e.getMessage());
        }
    }
    
    /**
     * 数据验证和转换 (Python字段映射逻辑)
     */
    private List<TUserHealthData> validateAndTransformHealthData(List<Map<String, Object>> healthDataList) {
        return healthDataList.parallelStream()
            .map(this::transformSingleHealthData)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
    }
    
    /**
     * 单条健康数据转换 (复用Python的字段映射)
     */
    private TUserHealthData transformSingleHealthData(Map<String, Object> data) {
        try {
            TUserHealthData healthData = new TUserHealthData();
            
            // 基础字段映射 (修正字段类型)
            healthData.setDeviceSn(getStringValue(data, "device_id"));
            healthData.setUserId(parseLong(data.get("user_id")));
            healthData.setOrgId(parseLong(data.get("org_id")));
            healthData.setCustomerId(parseLong(data.get("customer_id")));
            
            // 健康指标字段映射 (使用Python的mapping逻辑)
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
            
        } catch (Exception e) {
            log.warn("健康数据转换失败: {}", data, e);
            return null;
        }
    }
    
    /**
     * 重复检测 (Python去重算法)
     */
    private List<TUserHealthData> performDuplicateDetection(List<TUserHealthData> dataList) {
        Set<String> currentBatchKeys = new HashSet<>();
        
        return dataList.stream()
            .filter(data -> {
                String duplicateKey = generateDuplicateKey(data);
                
                // 检查Redis缓存中的重复记录 (Python逻辑)
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
    
    /**
     * CPU自适应分片处理 (Python分片策略)
     */
    private void processDataInAdaptiveShards(List<TUserHealthData> dataList) {
        // 按设备ID分片 (Python算法)
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
    
    /**
     * 获取优化器统计信息 (兼容Python接口)
     */
    public Map<String, Object> getOptimizerStats() {
        return Map.of(
            "processed", processedCount.get(),
            "batches", batchCount.get(),
            "errors", errorCount.get(),
            "duplicates", duplicateCount.get(),
            "queue_size", executor.getQueue().size(),
            "active_threads", executor.getActiveCount(),
            "cpu_cores", cpuCores,
            "batch_size", batchSize
        );
    }
    
    // ============= 辅助方法 =============
    
    private String generateDuplicateKey(TUserHealthData data) {
        return String.format("%s_%s_%s", 
            data.getDeviceSn(), 
            data.getCreateTime(), 
            data.getHeartRate()
        );
    }
    
    private Map<String, Object> buildSuccessResponse(long processed, long duplicates, long processingTime) {
        return Map.of(
            "success", true,
            "message", "数据处理成功",
            "processed", processed,
            "duplicates", duplicates,
            "processing_time_ms", processingTime,
            "batch_size", batchSize,
            "shard_count", cpuCores
        );
    }
    
    private String getStringValue(Map<String, Object> data, String key) {
        Object value = data.get(key);
        return value != null ? value.toString() : null;
    }
    
    private void setHealthDataField(TUserHealthData healthData, String field, Object value) {
        // 根据字段名设置相应的值
        try {
            switch (field) {
                case "heart_rate" -> healthData.setHeartRate(parseInt(value));
                case "blood_oxygen" -> healthData.setBloodOxygen(parseInt(value));
                case "temperature" -> healthData.setTemperature(parseDouble(value));
                case "pressure_high" -> healthData.setPressureHigh(parseInt(value));
                case "pressure_low" -> healthData.setPressureLow(parseInt(value));
                case "stress" -> healthData.setStress(parseInt(value));
                case "step" -> healthData.setStep(parseInt(value));
                case "distance" -> healthData.setDistance(parseDouble(value));
                case "calorie" -> healthData.setCalorie(parseDouble(value));
                case "latitude" -> healthData.setLatitude(parseDouble(value));
                case "longitude" -> healthData.setLongitude(parseDouble(value));
                case "altitude" -> healthData.setAltitude(parseDouble(value));
                default -> log.debug("未识别的字段: {}", field);
            }
        } catch (Exception e) {
            log.warn("设置字段值失败: field={}, value={}", field, value, e);
        }
    }
    
    private Double parseDouble(Object value) {
        if (value == null) return null;
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    private Integer parseInt(Object value) {
        if (value == null) return null;
        try {
            return Integer.parseInt(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    private Long parseLong(Object value) {
        if (value == null) return null;
        try {
            return Long.parseLong(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    private LocalDateTime parseDateTime(Object value) {
        if (value == null) return LocalDateTime.now();
        try {
            if (value instanceof String) {
                return LocalDateTime.parse((String) value, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
            }
            return LocalDateTime.now();
        } catch (Exception e) {
            return LocalDateTime.now();
        }
    }
    
    // 设备数据处理相关方法
    private List<TDeviceInfo> validateAndTransformDeviceData(List<Map<String, Object>> deviceDataList) {
        // 设备数据转换逻辑
        return deviceDataList.stream()
            .map(this::transformSingleDeviceData)
            .filter(Objects::nonNull)
            .collect(Collectors.toList());
    }
    
    private TDeviceInfo transformSingleDeviceData(Map<String, Object> data) {
        // 简化的设备数据转换
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
    
    private List<TDeviceInfo> removeDuplicateDevices(List<TDeviceInfo> devices) {
        // 设备去重逻辑
        return devices.stream()
            .collect(Collectors.toMap(
                TDeviceInfo::getSerialNumber,
                device -> device,
                (existing, replacement) -> existing
            ))
            .values()
            .stream()
            .collect(Collectors.toList());
    }
    
    private void processDeviceDataInBatches(List<TDeviceInfo> devices) {
        // 批量处理设备数据
        deviceInfoService.saveBatch(devices);
    }
    
    private void processAlertEvents(Object alertData) {
        // 告警事件处理逻辑
        log.info("处理告警事件: {}", alertData);
    }
    
    private void processSingleShard(List<TUserHealthData> shardData) {
        try {
            // 批量插入到数据库
            userHealthDataService.saveBatch(shardData, batchSize);
            log.debug("分片处理完成，数据量: {}", shardData.size());
        } catch (Exception e) {
            log.error("分片处理失败", e);
            errorCount.addAndGet(shardData.size());
        }
    }

    /**
     * 优化的健康数据上传处理
     */
    public CompletableFuture<HealthDataProcessResult> optimizedUpload(List<TUserHealthData> healthDataList) {
        
        log.info("🔄 开始优化处理 {} 条健康数据", healthDataList.size());
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                // 数据预处理和去重
                List<TUserHealthData> processedData = preprocessHealthData(healthDataList);
                
                // 分批处理
                List<CompletableFuture<Void>> batchFutures = new ArrayList<>();
                for (int i = 0; i < processedData.size(); i += batchSize) {
                    int endIndex = Math.min(i + batchSize, processedData.size());
                    List<TUserHealthData> batch = processedData.subList(i, endIndex);
                    
                    HealthDataBatch healthBatch = new HealthDataBatch(
                        UUID.randomUUID().toString(),
                        batch,
                        System.currentTimeMillis()
                    );
                    
                    batchFutures.add(processBatchAsync(healthBatch));
                }
                
                // 等待所有批次处理完成
                CompletableFuture.allOf(batchFutures.toArray(new CompletableFuture[0])).join();
                
                return HealthDataProcessResult.builder()
                    .success(true)
                    .processedCount(processedData.size())
                    .batchCount(batchFutures.size())
                    .processingTimeMs(System.currentTimeMillis())
                    .build();
                    
            } catch (Exception e) {
                log.error("❌ 优化处理健康数据失败: {}", e.getMessage(), e);
                errorCount.incrementAndGet();
                
                return HealthDataProcessResult.builder()
                    .success(false)
                    .errorMessage(e.getMessage())
                    .build();
            }
        }, executor);
    }

    /**
     * 数据预处理和去重
     */
    private List<TUserHealthData> preprocessHealthData(List<TUserHealthData> healthDataList) {
        
        List<TUserHealthData> processedData = new ArrayList<>();
        
        for (TUserHealthData data : healthDataList) {
            // 生成数据唯一键
            String dataKey = generateDataKey(data);
            
            // 检查重复数据
            if (processedKeys.contains(dataKey)) {
                duplicateCount.incrementAndGet();
                log.debug("⏭️ 跳过重复数据: {}", dataKey);
                continue;
            }
            
            // 数据验证和清理
            if (validateAndCleanData(data)) {
                processedKeys.add(dataKey);
                processedData.add(data);
            }
        }
        
        log.info("📊 数据预处理完成: 原始 {} 条，处理后 {} 条，重复 {} 条", 
            healthDataList.size(), processedData.size(), duplicateCount.get());
        
        return processedData;
    }

    /**
     * 异步处理批次
     */
    private CompletableFuture<Void> processBatchAsync(HealthDataBatch batch) {
        
        return CompletableFuture.runAsync(() -> {
            long startTime = System.currentTimeMillis();
            
            try {
                log.debug("⚡ 处理批次 {} ({} 条数据)", batch.getBatchId(), batch.getData().size());
                
                // 实际的批量数据处理逻辑将在这里实现
                // 这里需要调用实际的数据库插入服务
                processBatchData(batch.getData());
                
                long processingTime = System.currentTimeMillis() - startTime;
                
                // 更新统计信息
                processedCount.addAndGet(batch.getData().size());
                batchCount.incrementAndGet();
                
                // 性能监控
                synchronized (performanceWindow) {
                    performanceWindow.add(processingTime);
                    if (performanceWindow.size() > 100) {
                        performanceWindow.remove(0);  // 保持窗口大小
                    }
                }
                
                log.debug("✅ 批次 {} 处理完成，耗时 {}ms", batch.getBatchId(), processingTime);
                
            } catch (Exception e) {
                log.error("❌ 批次 {} 处理失败: {}", batch.getBatchId(), e.getMessage(), e);
                errorCount.incrementAndGet();
                throw e;
            }
            
        }, executor);
    }

    /**
     * 批量数据处理（待实现具体数据库操作）
     */
    @Transactional(rollbackFor = Exception.class)
    private void processBatchData(List<TUserHealthData> dataList) {
        // TODO: 实现批量数据库插入逻辑
        // 这里需要与ITUserHealthDataService集成
        log.debug("📝 批量处理 {} 条健康数据", dataList.size());
        
        // 模拟处理时间
        try {
            Thread.sleep(10);  // 临时模拟，实际实现时移除
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /**
     * 启动批处理器
     */
    private void startBatchProcessor() {
        executor.submit(() -> {
            while (running) {
                try {
                    HealthDataBatch batch = batchQueue.poll(batchTimeoutSeconds, TimeUnit.SECONDS);
                    if (batch != null) {
                        processBatchAsync(batch);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    log.error("❌ 批处理器异常: {}", e.getMessage(), e);
                }
            }
        });
    }

    /**
     * 生成数据唯一键
     */
    private String generateDataKey(TUserHealthData data) {
        return String.format("%s_%s_%s", 
            data.getUserId(), 
            data.getDeviceSn(), 
            data.getCreateTime());
    }

    /**
     * 数据验证和清理
     */
    private boolean validateAndCleanData(TUserHealthData data) {
        if (data == null) return false;
        if (data.getUserId() == null) return false;
        if (!org.springframework.util.StringUtils.hasText(data.getDeviceSn())) return false;
        
        // 设置默认创建时间
        if (data.getCreateTime() == null) {
            data.setCreateTime(LocalDateTime.now());
        }
        
        return true;
    }

    /**
     * 获取性能统计信息
     */
    public Map<String, Object> getPerformanceStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("processedCount", processedCount.get());
        stats.put("batchCount", batchCount.get());
        stats.put("errorCount", errorCount.get());
        stats.put("duplicateCount", duplicateCount.get());
        stats.put("batchSize", batchSize);
        stats.put("maxWorkers", maxWorkers);
        stats.put("cpuCores", cpuCores);
        stats.put("memoryMb", memoryMb);
        
        synchronized (performanceWindow) {
            if (!performanceWindow.isEmpty()) {
                double avgTime = performanceWindow.stream().mapToLong(Long::longValue).average().orElse(0);
                stats.put("avgProcessingTimeMs", avgTime);
                stats.put("maxProcessingTimeMs", Collections.max(performanceWindow));
                stats.put("minProcessingTimeMs", Collections.min(performanceWindow));
            }
        }
        
        return stats;
    }

    /**
     * 关闭优化器
     */
    public void shutdown() {
        running = false;
        executor.shutdown();
        try {
            if (!executor.awaitTermination(60, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }
        log.info("🔒 HealthDataOptimizer 已关闭");
    }

    /**
     * 健康数据批次
     */
    public static class HealthDataBatch {
        private final String batchId;
        private final List<TUserHealthData> data;
        private final long timestamp;

        public HealthDataBatch(String batchId, List<TUserHealthData> data, long timestamp) {
            this.batchId = batchId;
            this.data = data;
            this.timestamp = timestamp;
        }

        public String getBatchId() { return batchId; }
        public List<TUserHealthData> getData() { return data; }
        public long getTimestamp() { return timestamp; }
    }

    /**
     * 处理结果
     */
    public static class HealthDataProcessResult {
        private boolean success;
        private long processedCount;
        private long batchCount;
        private long processingTimeMs;
        private String errorMessage;

        public static HealthDataProcessResultBuilder builder() {
            return new HealthDataProcessResultBuilder();
        }

        public static class HealthDataProcessResultBuilder {
            private boolean success;
            private long processedCount;
            private long batchCount;
            private long processingTimeMs;
            private String errorMessage;

            public HealthDataProcessResultBuilder success(boolean success) {
                this.success = success;
                return this;
            }

            public HealthDataProcessResultBuilder processedCount(long processedCount) {
                this.processedCount = processedCount;
                return this;
            }

            public HealthDataProcessResultBuilder batchCount(long batchCount) {
                this.batchCount = batchCount;
                return this;
            }

            public HealthDataProcessResultBuilder processingTimeMs(long processingTimeMs) {
                this.processingTimeMs = processingTimeMs;
                return this;
            }

            public HealthDataProcessResultBuilder errorMessage(String errorMessage) {
                this.errorMessage = errorMessage;
                return this;
            }

            public HealthDataProcessResult build() {
                HealthDataProcessResult result = new HealthDataProcessResult();
                result.success = this.success;
                result.processedCount = this.processedCount;
                result.batchCount = this.batchCount;
                result.processingTimeMs = this.processingTimeMs;
                result.errorMessage = this.errorMessage;
                return result;
            }
        }

        // Getters
        public boolean isSuccess() { return success; }
        public long getProcessedCount() { return processedCount; }
        public long getBatchCount() { return batchCount; }
        public long getProcessingTimeMs() { return processingTimeMs; }
        public String getErrorMessage() { return errorMessage; }
    }
}