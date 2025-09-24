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

package com.ljwx.modules.health.upload;

import com.ljwx.common.api.vo.Result;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.entity.TDeviceInfoHistory;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.entity.THealthDataSlowDaily;
import com.ljwx.modules.health.domain.entity.THealthDataSlowWeekly;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.service.ITDeviceInfoHistoryService;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.health.service.ITHealthDataSlowDailyService;
import com.ljwx.modules.health.service.ITHealthDataSlowWeeklyService;
import com.ljwx.modules.health.service.BatchAlertProcessor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

/**
 * 数据上传处理器
 * 
 * 基于ljwx-bigscreen的HealthDataOptimizer优化算法，提供：
 * - CPU自适应批处理
 * - 异步队列处理
 * - 重复数据检测
 * - 性能监控和自适应调整
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DataUpload
 * @CreateTime 2024-12-16
 */
@Slf4j
@Component
public class DataUpload {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private ITUserHealthDataService userHealthDataService;
    
    @Autowired
    private ITDeviceInfoService deviceInfoService;
    
    @Autowired
    private ITDeviceInfoHistoryService deviceInfoHistoryService;
    
    @Autowired
    private ITHealthDataSlowDailyService userHealthDataDailyService;
    
    @Autowired
    private ITHealthDataSlowWeeklyService userHealthDataWeeklyService;
    
    @Autowired
    private BatchAlertProcessor batchAlertProcessor;
    
    // JSON处理器
    private final ObjectMapper objectMapper = new ObjectMapper();
    
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
    private final AtomicLong alertTriggeredCount = new AtomicLong(0);
    
    // 已处理记录键值集合（防重复）
    private final Set<String> processedKeys = ConcurrentHashMap.newKeySet();
    
    // 性能监控
    private final List<Long> performanceWindow = Collections.synchronizedList(new ArrayList<>());
    private volatile long lastAdjustmentTime = System.currentTimeMillis();

    public DataUpload(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
        
        // 初始化线程池
        this.executor = new ThreadPoolExecutor(
            maxWorkers / 2,  // 核心线程数
            maxWorkers,      // 最大线程数
            60L,             // 空闲时间
            TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(1000),
            r -> new Thread(r, "data-upload-" + System.currentTimeMillis())
        );
        
        log.info("🚀 DataUpload 初始化:");
        log.info("   CPU核心: {}, 内存: {}MB", cpuCores, memoryMb);
        log.info("   批次大小: {}, 工作线程: {}", batchSize, maxWorkers);
        
        // 启动批处理任务
        startBatchProcessor();
    }
    
    // ============= Python功能迁移 - 快慢字段分离策略 =============
    
    /**
     * 快字段列表 (对应Python中的fast_fields)
     * 存储在主表 t_user_health_data 中，用于实时查询和快速更新
     */
    private static final Set<String> FAST_FIELDS = Set.of(
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", "pressure_low",
        "stress", "step", "distance", "calorie", "latitude", "longitude", "altitude", "sleep"
    );
    
    /**
     * 慢字段-日报列表 (对应Python中的slow_daily_fields)
     * 存储在日报表 t_user_health_data_daily 中，用于每日统计分析
     */
    private static final Set<String> SLOW_DAILY_FIELDS = Set.of(
        "sleep_data", "exercise_daily_data", "workout_data", "scientific_sleep_data"
    );
    
    /**
     * 慢字段-周报列表 (对应Python中的slow_weekly_fields)
     * 存储在周报表 t_user_health_data_weekly 中，用于每周统计分析
     */
    private static final Set<String> SLOW_WEEKLY_FIELDS = Set.of(
        "exercise_week_data"
    );

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
            
            // 基础字段映射 (支持手表端字段格式)
            String deviceSn = getStringValue(data, "deviceSn", "device_sn", "device_id");
            log.debug("设备序列号映射: deviceSn={}", deviceSn);
            healthData.setDeviceSn(deviceSn);
            
            // 验证必要字段
            if (deviceSn == null || deviceSn.trim().isEmpty()) {
                log.warn("设备序列号为空，跳过此条数据: {}", data);
                return null;
            }
            
            // 用户ID - 支持字符串和数字格式
            Long userId = parseLong(data.get("userId"), data.get("user_id"));
            healthData.setUserId(userId);
            
            // 组织ID - 支持超大数字
            Long orgId = parseLong(data.get("orgId"), data.get("org_id"));
            healthData.setOrgId(orgId);
            
            // 客户ID - 支持超大数字
            Long customerId = parseLong(data.get("customerId"), data.get("customer_id"));
            healthData.setCustomerId(customerId);
            
            // 健康指标字段映射 (支持手表端字段格式)
            
            // 心率
            if (data.get("heart_rate") != null) {
                healthData.setHeartRate(parseInt(data.get("heart_rate")));
            }
            
            // 血氧
            if (data.get("blood_oxygen") != null) {
                healthData.setBloodOxygen(parseInt(data.get("blood_oxygen")));
            }
            
            // 体温 - 支持body_temperature字段
            if (data.get("body_temperature") != null) {
                healthData.setTemperature(parseDouble(data.get("body_temperature")));
            }
            
            // 步数
            if (data.get("step") != null) {
                healthData.setStep(parseInt(data.get("step")));
            }
            
            // 距离
            if (data.get("distance") != null) {
                healthData.setDistance(parseDouble(data.get("distance")));
            }
            
            // 卡路里
            if (data.get("calorie") != null) {
                healthData.setCalorie(parseDouble(data.get("calorie")));
            }
            
            // 位置信息
            if (data.get("latitude") != null) {
                healthData.setLatitude(parseDouble(data.get("latitude")));
            }
            if (data.get("longitude") != null) {
                healthData.setLongitude(parseDouble(data.get("longitude")));
            }
            if (data.get("altitude") != null) {
                healthData.setAltitude(parseDouble(data.get("altitude")));
            }
            
            // 压力指数
            if (data.get("stress") != null) {
                healthData.setStress(parseInt(data.get("stress")));
            }
            
            // 血压 - 支持手表端字段名
            if (data.get("blood_pressure_systolic") != null) {
                healthData.setPressureHigh(parseInt(data.get("blood_pressure_systolic")));
            }
            if (data.get("blood_pressure_diastolic") != null) {
                healthData.setPressureLow(parseInt(data.get("blood_pressure_diastolic")));
            }
            
            // 扩展数据字段处理 - 处理慢字段数据到分表
            processExtendedDataFields(data, healthData);
            
            // 时间字段处理 - 支持timestamp字段
            String timestampStr = getStringValue(data, "timestamp", "create_time");
            if (timestampStr != null) {
                try {
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                    healthData.setCreateTime(LocalDateTime.parse(timestampStr, formatter));
                } catch (Exception e) {
                    log.warn("时间戳解析失败: {}", timestampStr);
                    healthData.setCreateTime(LocalDateTime.now());
                }
            } else {
                healthData.setCreateTime(LocalDateTime.now());
            }
            
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
            .filter(data -> data.getDeviceSn() != null) // 过滤掉deviceSn为null的数据
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
        Map<String, Object> stats = new HashMap<>();
        stats.put("processed", processedCount.get());
        stats.put("batches", batchCount.get());
        stats.put("errors", errorCount.get());
        stats.put("duplicates", duplicateCount.get());
        stats.put("alerts_triggered", alertTriggeredCount.get());
        stats.put("queue_size", executor.getQueue().size());
        stats.put("active_threads", executor.getActiveCount());
        stats.put("cpu_cores", cpuCores);
        stats.put("batch_size", batchSize);
        
        // 告警相关统计
        long totalProcessed = processedCount.get();
        if (totalProcessed > 0) {
            stats.put("alert_rate_percent", (alertTriggeredCount.get() * 100.0) / totalProcessed);
        } else {
            stats.put("alert_rate_percent", 0.0);
        }
        
        // 集成批量告警处理器统计
        try {
            Map<String, Object> alertStats = batchAlertProcessor.getStatistics();
            stats.put("alert_processor_stats", alertStats);
        } catch (Exception e) {
            log.warn("获取告警处理器统计失败", e);
        }
        
        return stats;
    }
    
    // ============= 辅助方法 =============
    
    private String generateDuplicateKey(TUserHealthData data) {
        return String.format("%s_%s_%s", 
            data.getDeviceSn() != null ? data.getDeviceSn() : "UNKNOWN", 
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
    
    // 支持多个值的查找
    private Long parseLong(Object... values) {
        for (Object value : values) {
            if (value != null) {
                try {
                    return Long.parseLong(value.toString());
                } catch (NumberFormatException e) {
                    // 继续尝试下一个值
                }
            }
        }
        return null;
    }
    
    private Integer parseInteger(Object value) {
        if (value == null) return null;
        try {
            return Integer.parseInt(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    // 支持多字段名的字符串值获取
    private String getStringValue(Map<String, Object> data, String... keys) {
        for (String key : keys) {
            Object value = data.get(key);
            if (value != null) {
                return value.toString();
            }
        }
        return null;
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
        // 完整的设备数据转换，支持多种字段格式
        try {
            TDeviceInfo deviceInfo = new TDeviceInfo();
            
            // 系统软件版本
            deviceInfo.setSystemSoftwareVersion(getStringValue(data, "System Software Version", "system_software_version"));
            
            // WiFi地址
            deviceInfo.setWifiAddress(getStringValue(data, "Wifi Address", "wifi_address"));
            
            // 蓝牙地址
            deviceInfo.setBluetoothAddress(getStringValue(data, "Bluetooth Address", "bluetooth_address"));
            
            // IP地址
            deviceInfo.setIpAddress(getStringValue(data, "IP Address", "ip_address"));
            
            // 网络访问模式
            deviceInfo.setNetworkAccessMode(getStringValue(data, "Network Access Mode", "network_access_mode"));
            
            // 设备序列号 - 支持多种字段名
            String serialNumber = getStringValue(data, "SerialNumber", "serialNumber", "device_id", "serial_number");
            deviceInfo.setSerialNumber(serialNumber);
            
            // 设备名称
            deviceInfo.setDeviceName(getStringValue(data, "Device Name", "device_name", "deviceName"));
            
            // IMEI
            deviceInfo.setImei(getStringValue(data, "IMEI", "imei"));
            
            // 电池电量
            Integer batteryLevel = parseInteger(data.get("batteryLevel"));
            if (batteryLevel == null) {
                batteryLevel = parseInteger(data.get("battery_level"));
            }
            deviceInfo.setBatteryLevel(batteryLevel);
            
            // 电压
            deviceInfo.setVoltage(parseInteger(data.get("voltage")));
            
            // 充电状态 - 枚举值：NONE(没有充电), CHARGING(充电)
            deviceInfo.setChargingStatus(getStringValue(data, "chargingStatus", "charging_status"));
            
            // 设备状态
            deviceInfo.setStatus(getStringValue(data, "status"));
            
            // 佩戴状态 - 映射数字值到枚举：0/NOT_WORN(未佩戴), 1/WORN(佩戴)
            String wearState = getStringValue(data, "wearState", "wear_state");
            if (wearState != null) {
                if ("1".equals(wearState) || "WORN".equalsIgnoreCase(wearState)) {
                    deviceInfo.setWearableStatus("WORN");
                } else if ("0".equals(wearState) || "NOT_WORN".equalsIgnoreCase(wearState)) {
                    deviceInfo.setWearableStatus("NOT_WORN");
                } else {
                    deviceInfo.setWearableStatus(wearState); // 保持原值
                }
            }
            
            // 时间戳处理
            String timestampStr = getStringValue(data, "timestamp");
            if (timestampStr != null) {
                try {
                    // 支持多种时间格式
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
                    deviceInfo.setTimestamp(LocalDateTime.parse(timestampStr, formatter));
                } catch (Exception e) {
                    log.warn("时间戳解析失败: {}", timestampStr);
                    deviceInfo.setTimestamp(LocalDateTime.now());
                }
            } else {
                deviceInfo.setTimestamp(LocalDateTime.now());
            }
            
            // 租户ID (支持字符串形式的大数字)
            Long customerId = parseLong(data.get("customerId"));
            if (customerId == null) {
                customerId = parseLong(data.get("customer_id"));
            }
            deviceInfo.setCustomerId(customerId != null ? customerId : 8L);
            
            // 组织ID
            Long orgId = parseLong(data.get("orgId"));
            if (orgId == null) {
                orgId = parseLong(data.get("org_id"));
            }
            deviceInfo.setOrgId(orgId != null ? orgId : 1L);
            
            // 用户ID
            Long userId = parseLong(data.get("userId"));
            if (userId == null) {
                userId = parseLong(data.get("user_id"));
            }
            deviceInfo.setUserId(userId != null ? userId : 101L);
            
            // 设置创建时间和更新时间
            LocalDateTime now = LocalDateTime.now();
            deviceInfo.setCreatedAt(now);
            deviceInfo.setUpdateTime(now);
            
            // 验证必要字段
            if (deviceInfo.getSerialNumber() == null || deviceInfo.getSerialNumber().trim().isEmpty()) {
                log.warn("设备序列号为空，跳过该设备: {}", data);
                return null;
            }
            
            log.debug("设备数据转换成功: 序列号={}, 设备名={}", 
                deviceInfo.getSerialNumber(), deviceInfo.getDeviceName());
            
            return deviceInfo;
            
        } catch (Exception e) {
            log.error("设备数据转换失败: {}", data, e);
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
        try {
            // 1. 处理设备信息更新和历史记录插入
            List<TDeviceInfoHistory> historyRecords = new ArrayList<>();
            
            for (TDeviceInfo device : devices) {
                // 更新或插入设备主表记录
                processDeviceMainTable(device);
                
                // 创建历史记录
                TDeviceInfoHistory history = createDeviceHistoryFromDevice(device);
                historyRecords.add(history);
            }
            
            // 2. 批量插入历史记录
            if (!historyRecords.isEmpty()) {
                boolean historySuccess = deviceInfoHistoryService.saveBatch(historyRecords);
                if (historySuccess) {
                    log.debug("✅ 设备历史记录批量插入成功，数量: {}", historyRecords.size());
                } else {
                    log.warn("⚠️ 设备历史记录批量插入失败");
                }
            }
            
        } catch (Exception e) {
            log.error("❌ 设备数据批量处理失败", e);
            throw e;
        }
    }
    
    /**
     * 处理设备主表更新逻辑
     * 如果设备存在则更新，不存在则插入
     */
    private void processDeviceMainTable(TDeviceInfo device) {
        try {
            // 根据序列号查询是否存在
            TDeviceInfo existingDevice = deviceInfoService.getBySerialNumber(device.getSerialNumber());
            
            LocalDateTime now = LocalDateTime.now();
            
            if (existingDevice != null) {
                // 更新现有设备记录
                device.setId(existingDevice.getId());
                device.setCreatedAt(existingDevice.getCreatedAt()); // 保持原创建时间
                device.setUpdateTime(now);
                
                boolean updateSuccess = deviceInfoService.updateById(device);
                if (updateSuccess) {
                    log.debug("✅ 设备信息更新成功: serialNumber={}", device.getSerialNumber());
                } else {
                    log.warn("⚠️ 设备信息更新失败: serialNumber={}", device.getSerialNumber());
                }
            } else {
                // 插入新设备记录
                device.setCreatedAt(now);
                device.setUpdateTime(now);
                
                boolean insertSuccess = deviceInfoService.save(device);
                if (insertSuccess) {
                    log.debug("✅ 新设备信息插入成功: serialNumber={}", device.getSerialNumber());
                } else {
                    log.warn("⚠️ 新设备信息插入失败: serialNumber={}", device.getSerialNumber());
                }
            }
            
        } catch (Exception e) {
            log.error("❌ 处理设备主表失败: serialNumber={}", device.getSerialNumber(), e);
            throw e;
        }
    }
    
    /**
     * 从设备信息创建历史记录
     */
    private TDeviceInfoHistory createDeviceHistoryFromDevice(TDeviceInfo device) {
        return TDeviceInfoHistory.builder()
                .serialNumber(device.getSerialNumber())
                .timestamp(device.getTimestamp() != null ? device.getTimestamp() : LocalDateTime.now())
                .systemSoftwareVersion(device.getSystemSoftwareVersion())
                .batteryLevel(device.getBatteryLevel())
                .wearableStatus(device.getWearableStatus())
                .chargingStatus(device.getChargingStatus())
                .voltage(device.getVoltage())
                .ipAddress(device.getIpAddress())
                .networkAccessMode(device.getNetworkAccessMode())
                .status(device.getStatus())
                .userId(device.getUserId())
                .orgId(device.getOrgId())
                .customerId(device.getCustomerId())
                .createTime(LocalDateTime.now())
                .updateTime(LocalDateTime.now())
                .build();
    }
    
    private void processAlertEvents(Object alertData) {
        // 告警事件处理逻辑
        log.info("处理告警事件: {}", alertData);
    }
    
    private void processSingleShard(List<TUserHealthData> shardData) {
        try {
            // 1. 批量插入到数据库
            userHealthDataService.saveBatch(shardData, batchSize);
            log.debug("分片处理完成，数据量: {}", shardData.size());
            
            // 2. 异步执行告警检查（不阻塞数据插入）
            CompletableFuture.runAsync(() -> {
                try {
                    Map<String, Object> alertResult = batchAlertProcessor.processBatchAlerts(shardData);
                    
                    // 更新告警统计
                    if (alertResult != null && alertResult.containsKey("alerts_triggered")) {
                        int alertsTriggered = (Integer) alertResult.get("alerts_triggered");
                        alertTriggeredCount.addAndGet(alertsTriggered);
                        
                        if (alertsTriggered > 0) {
                            log.info("🚨 分片告警检查完成: 数据{}条，触发告警{}个", 
                                shardData.size(), alertsTriggered);
                        }
                    }
                } catch (Exception e) {
                    log.warn("分片告警检查失败", e);
                }
            }, executor);
            
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
            data.getDeviceSn() != null ? data.getDeviceSn() : "UNKNOWN", 
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
        log.info("🔒 DataUpload 已关闭");
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

    // ============= 快慢字段分离处理 (Python系统完整迁移) =============

    /**
     * 扩展数据字段处理 - 完整实现Python的快慢字段分离策略
     * 参照Python: health_data_batch_processor.py:585-640行
     */
    private void processExtendedDataFields(Map<String, Object> data, TUserHealthData healthData) {
        try {
            log.debug("🔧 开始处理快慢字段分离: deviceSn={}", healthData.getDeviceSn());

            // 获取时间戳，用于确定日期和周
            LocalDateTime timestamp = healthData.getCreateTime() != null ? 
                healthData.getCreateTime() : LocalDateTime.now();
            LocalDate date = timestamp.toLocalDate();

            // ========== 处理日报慢字段 (slow_daily_fields) ==========
            Map<String, Object> dailyFields = extractSlowDailyFields(data);
            if (!dailyFields.isEmpty()) {
                processDailySlowFields(dailyFields, healthData, date);
            }

            // ========== 处理周报慢字段 (slow_weekly_fields) ==========
            Map<String, Object> weeklyFields = extractSlowWeeklyFields(data);
            if (!weeklyFields.isEmpty()) {
                processWeeklySlowFields(weeklyFields, healthData, date);
            }

            log.debug("✅ 快慢字段分离处理完成: deviceSn={}", healthData.getDeviceSn());

        } catch (Exception e) {
            log.error("❌ 扩展数据字段处理失败: deviceSn={}", healthData.getDeviceSn(), e);
        }
    }

    /**
     * 提取日报慢字段数据
     * 对应Python: slow_daily_fields=['sleep_data','exercise_daily_data','workout_data','scientific_sleep_data']
     */
    private Map<String, Object> extractSlowDailyFields(Map<String, Object> data) {
        Map<String, Object> dailyFields = new HashMap<>();

        // 映射Python字段名到Java字段名
        Map<String, String> fieldMapping = Map.of(
            "sleepData", "sleep_data",
            "exerciseDailyData", "exercise_daily_data", 
            "workoutData", "workout_data",
            "scientificSleepData", "scientific_sleep_data"
        );

        for (Map.Entry<String, String> entry : fieldMapping.entrySet()) {
            String javaField = entry.getKey();
            String pythonField = entry.getValue();
            
            Object value = data.get(javaField);
            if (value != null) {
                // 确保JSON数据是字符串格式
                if (value instanceof String) {
                    dailyFields.put(pythonField, value);
                } else {
                    try {
                        dailyFields.put(pythonField, objectMapper.writeValueAsString(value));
                    } catch (JsonProcessingException e) {
                        log.warn("JSON序列化失败: field={}, value={}", javaField, value);
                    }
                }
            }
        }

        return dailyFields;
    }

    /**
     * 提取周报慢字段数据
     * 对应Python: slow_weekly_fields=['exercise_week_data']
     */
    private Map<String, Object> extractSlowWeeklyFields(Map<String, Object> data) {
        Map<String, Object> weeklyFields = new HashMap<>();

        Object exerciseWeekData = data.get("exerciseWeekData");
        if (exerciseWeekData != null) {
            if (exerciseWeekData instanceof String) {
                weeklyFields.put("exercise_week_data", exerciseWeekData);
            } else {
                try {
                    weeklyFields.put("exercise_week_data", objectMapper.writeValueAsString(exerciseWeekData));
                } catch (JsonProcessingException e) {
                    log.warn("JSON序列化失败: exerciseWeekData={}", exerciseWeekData);
                }
            }
        }

        return weeklyFields;
    }

    /**
     * 处理日报慢字段数据
     * 对应Python: health_data_batch_processor.py:614-625行
     */
    private void processDailySlowFields(Map<String, Object> dailyFields, TUserHealthData healthData, LocalDate date) {
        try {
            log.debug("📅 处理日报慢字段: deviceSn={}, date={}, fields={}", 
                healthData.getDeviceSn(), date, dailyFields.keySet());

            // 构建日报数据对象
            THealthDataSlowDaily dailyData = THealthDataSlowDaily.builder()
                .deviceSn(healthData.getDeviceSn())
                .userId(healthData.getUserId())
                .orgId(healthData.getOrgId())
                .customerId(healthData.getCustomerId())
                .timestamp(date) // 使用LocalDate作为日期
                .build();

            // 设置慢字段数据
            if (dailyFields.containsKey("sleep_data")) {
                dailyData.setSleepData((String) dailyFields.get("sleep_data"));
            }
            if (dailyFields.containsKey("exercise_daily_data")) {
                dailyData.setExerciseDailyData((String) dailyFields.get("exercise_daily_data"));
            }
            if (dailyFields.containsKey("workout_data")) {
                dailyData.setWorkoutData((String) dailyFields.get("workout_data"));
            }
            if (dailyFields.containsKey("scientific_sleep_data")) {
                dailyData.setScientificSleepData((String) dailyFields.get("scientific_sleep_data"));
            }

            // 异步保存到日报表
            CompletableFuture.runAsync(() -> {
                try {
                    boolean success = userHealthDataDailyService.saveOrUpdate(dailyData);
                    if (success) {
                        log.debug("✅ 日报数据保存成功: deviceSn={}, date={}", healthData.getDeviceSn(), date);
                    } else {
                        log.warn("⚠️ 日报数据保存失败: deviceSn={}, date={}", healthData.getDeviceSn(), date);
                    }
                } catch (Exception e) {
                    log.error("❌ 异步保存日报数据失败: deviceSn={}, date={}", healthData.getDeviceSn(), date, e);
                }
            }, executor);

        } catch (Exception e) {
            log.error("❌ 处理日报慢字段失败: deviceSn={}, date={}", healthData.getDeviceSn(), date, e);
        }
    }

    /**
     * 处理周报慢字段数据
     * 对应Python: health_data_batch_processor.py:627-639行
     */
    private void processWeeklySlowFields(Map<String, Object> weeklyFields, TUserHealthData healthData, LocalDate date) {
        try {
            // 获取周开始日期 (周一)
            LocalDate weekStart = userHealthDataWeeklyService.getWeekStart(date);
            
            log.debug("📊 处理周报慢字段: deviceSn={}, weekStart={}, fields={}", 
                healthData.getDeviceSn(), weekStart, weeklyFields.keySet());

            // 构建周报数据对象
            THealthDataSlowWeekly weeklyData = THealthDataSlowWeekly.builder()
                .deviceSn(healthData.getDeviceSn())
                .userId(healthData.getUserId())
                .orgId(healthData.getOrgId())
                .customerId(healthData.getCustomerId())
                .timestamp(weekStart) // 使用周开始日期
                .build();

            // 设置慢字段数据
            if (weeklyFields.containsKey("exercise_week_data")) {
                weeklyData.setExerciseWeekData((String) weeklyFields.get("exercise_week_data"));
            }

            // 异步保存到周报表
            CompletableFuture.runAsync(() -> {
                try {
                    boolean success = userHealthDataWeeklyService.saveOrUpdate(weeklyData);
                    if (success) {
                        log.debug("✅ 周报数据保存成功: deviceSn={}, weekStart={}", healthData.getDeviceSn(), weekStart);
                    } else {
                        log.warn("⚠️ 周报数据保存失败: deviceSn={}, weekStart={}", healthData.getDeviceSn(), weekStart);
                    }
                } catch (Exception e) {
                    log.error("❌ 异步保存周报数据失败: deviceSn={}, weekStart={}", healthData.getDeviceSn(), weekStart, e);
                }
            }, executor);

        } catch (Exception e) {
            log.error("❌ 处理周报慢字段失败: deviceSn={}, date={}", healthData.getDeviceSn(), date, e);
        }
    }

    /**
     * 优化的健康数据上传 - 完整实现Python系统架构
     * 对应Python: health_data_batch_processor.py:optimized_upload_health_data
     */
    public Result<Map<String, Object>> optimizedUploadHealthDataWithSeparation(Map<String, Object> healthData) {
        long startTime = System.currentTimeMillis();
        log.info("🚀 开始优化健康数据上传 (快慢字段分离)");

        try {
            Object dataObj = healthData.get("data");
            List<Map<String, Object>> dataList;

            // 处理不同的数据格式
            if (dataObj instanceof List) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> tempList = (List<Map<String, Object>>) dataObj;
                dataList = tempList;
            } else if (dataObj instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> singleData = (Map<String, Object>) dataObj;
                dataList = List.of(singleData);
            } else {
                return Result.error("无效的数据格式");
            }

            log.info("📊 检测到数据量: {}", dataList.size());

            // 使用Python同样的批量处理策略
            if (dataList.size() > 10) {
                return processBatchHealthDataWithSeparation(dataList, startTime);
            } else {
                return processSmallBatchHealthDataWithSeparation(dataList, startTime);
            }

        } catch (Exception e) {
            long errorTime = System.currentTimeMillis() - startTime;
            log.error("❌ 优化健康数据上传失败，耗时{}ms", errorTime, e);
            return Result.error("上传失败: " + e.getMessage());
        }
    }

    /**
     * 大批量数据处理 (对应Python中的大批量处理逻辑)
     */
    private Result<Map<String, Object>> processBatchHealthDataWithSeparation(List<Map<String, Object>> dataList, long startTime) {
        log.info("🏥 大批量处理模式: {}条数据", dataList.size());
        
        int successCount = 0;
        int duplicateCount = 0;
        int errorCount = 0;

        for (int i = 0; i < dataList.size(); i++) {
            Map<String, Object> item = dataList.get(i);
            String deviceSn = getStringValue(item, "deviceSn", "id");
            
            if (deviceSn != null) {
                try {
                    List<TUserHealthData> healthDataList = List.of(transformSingleHealthData(item));
                    if (!healthDataList.isEmpty() && healthDataList.get(0) != null) {
                        List<TUserHealthData> processedData = performDuplicateDetection(healthDataList);
                        if (!processedData.isEmpty()) {
                            processDataInAdaptiveShards(processedData);
                            successCount++;
                        } else {
                            duplicateCount++;
                        }
                    } else {
                        errorCount++;
                    }
                } catch (Exception e) {
                    log.warn("处理第{}条数据失败: deviceSn={}", i + 1, deviceSn, e);
                    errorCount++;
                }
            } else {
                log.warn("第{}条数据缺少设备SN", i + 1);
                errorCount++;
            }
        }

        long processingTime = System.currentTimeMillis() - startTime;
        String message = String.format("批量处理完成，成功%d条，重复%d条，失败%d条", successCount, duplicateCount, errorCount);
        
        Map<String, Object> result = Map.of(
            "success", true,
            "message", message,
            "details", Map.of(
                "success", successCount,
                "duplicate", duplicateCount,
                "error", errorCount,
                "processing_time_ms", processingTime
            )
        );

        log.info("✅ {}, 耗时{}ms", message, processingTime);
        return Result.ok(result);
    }

    /**
     * 小批量数据处理 (对应Python中的小批量直接处理)
     */
    private Result<Map<String, Object>> processSmallBatchHealthDataWithSeparation(List<Map<String, Object>> dataList, long startTime) {
        log.info("🏥 小批量处理模式: {}条数据", dataList.size());
        
        try {
            List<TUserHealthData> validatedData = validateAndTransformHealthData(dataList);
            List<TUserHealthData> deduplicatedData = performDuplicateDetection(validatedData);
            processDataInAdaptiveShards(deduplicatedData);

            long processingTime = System.currentTimeMillis() - startTime;
            long processed = deduplicatedData.size();
            long duplicates = validatedData.size() - processed;

            Map<String, Object> result = buildSuccessResponse(processed, duplicates, processingTime);
            
            log.info("✅ 小批量处理完成: 处理{}条，去重{}条，耗时{}ms", processed, duplicates, processingTime);
            return Result.ok(result);

        } catch (Exception e) {
            long errorTime = System.currentTimeMillis() - startTime;
            log.error("❌ 小批量处理失败，耗时{}ms", errorTime, e);
            return Result.error("小批量处理失败: " + e.getMessage());
        }
    }
}