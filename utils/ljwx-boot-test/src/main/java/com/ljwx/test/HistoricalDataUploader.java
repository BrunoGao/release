package com.ljwx.test;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

/**
 * ljwx-boot 历史数据上传测试工具
 * 仿照 start_30day_upload.py 实现
 * 
 * 功能:
 * - 模拟客户手表每分钟上传一次数据
 * - 高并发批量上传
 * - 支持30天历史数据回放
 * - 统计上传成功率和性能指标
 */
public class HistoricalDataUploader {
    
    private static final Logger logger = LoggerFactory.getLogger(HistoricalDataUploader.class);
    
    // 配置参数
    private final String baseUrl;
    private final int maxWorkers;
    private final ExecutorService executor;
    private final ObjectMapper objectMapper;
    private volatile boolean running = false;
    
    // API客户端池
    private final BlockingQueue<APIClient> clientPool;
    
    // 统计信息
    private final AtomicLong totalUploads = new AtomicLong(0);
    private final AtomicLong successfulUploads = new AtomicLong(0);
    private final AtomicLong failedUploads = new AtomicLong(0);
    private LocalDateTime startTime;
    
    // 设备列表
    private final List<String> deviceList;
    
    public HistoricalDataUploader(String baseUrl, int maxWorkers, List<String> devices) {
        this.baseUrl = baseUrl != null ? baseUrl : "http://localhost:8080";
        this.maxWorkers = maxWorkers > 0 ? maxWorkers : 20;
        this.deviceList = devices != null ? devices : generateDefaultDevices();
        this.objectMapper = new ObjectMapper();
        this.executor = Executors.newFixedThreadPool(this.maxWorkers);
        this.clientPool = new LinkedBlockingQueue<>();
        
        // 初始化API客户端池
        for (int i = 0; i < this.maxWorkers; i++) {
            this.clientPool.offer(new APIClient(this.baseUrl));
        }
        
        logger.info("🚀 HistoricalDataUploader 初始化完成");
        logger.info("   • 基础URL: {}", this.baseUrl);
        logger.info("   • 线程池大小: {}", this.maxWorkers);
        logger.info("   • 设备数量: {}", this.deviceList.size());
    }
    
    /**
     * 生成默认设备列表
     */
    private List<String> generateDefaultDevices() {
        List<String> devices = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            devices.add("DEVICE_" + String.format("%03d", i));
        }
        return devices;
    }
    
    /**
     * 上传历史数据
     * @param days 天数
     */
    public void uploadHistoricalData(double days) {
        logger.info("🚀 开始上传{}天历史数据", days);
        
        // 计算时间范围
        LocalDateTime endTime = LocalDateTime.now();
        LocalDateTime startTime = endTime.minusMinutes((long)(days * 24 * 60));
        
        // 生成时间点（每分钟一次）
        List<LocalDateTime> timePoints = generateTimePoints(startTime, endTime);
        
        int totalOperations = deviceList.size() * timePoints.size() * 3; // 3个API接口
        
        logger.info("📊 上传统计:");
        logger.info("   • 设备数量: {}", deviceList.size());
        logger.info("   • 时间范围: {} 到 {}", 
                   startTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")),
                   endTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")));
        logger.info("   • 时间点数量: {} (每分钟)", timePoints.size());
        logger.info("   • 总操作数: {}", totalOperations);
        logger.info("   • 线程池大小: {}", maxWorkers);
        logger.info("   • 预计耗时: {:.1f} 分钟 (假设100次/分钟)", totalOperations / 100.0 / 60.0);
        
        this.running = true;
        this.startTime = LocalDateTime.now();
        
        // 创建所有上传任务
        List<CompletableFuture<List<UploadResult>>> futures = new ArrayList<>();
        
        for (int timeIdx = 0; timeIdx < timePoints.size(); timeIdx++) {
            if (!running) break;
            
            LocalDateTime timePoint = timePoints.get(timeIdx);
            for (String deviceSn : deviceList) {
                if (!running) break;
                
                final int currentTimeIdx = timeIdx;
                CompletableFuture<List<UploadResult>> future = CompletableFuture.supplyAsync(
                    () -> uploadDeviceData(deviceSn, timePoint, currentTimeIdx, timePoints.size()),
                    executor
                );
                futures.add(future);
            }
        }
        
        logger.info("已创建 {} 个上传任务", futures.size());
        
        // 等待所有任务完成并显示进度
        int completedCount = 0;
        for (CompletableFuture<List<UploadResult>> future : futures) {
            if (!running) break;
            
            try {
                List<UploadResult> results = future.get(60, TimeUnit.SECONDS);
                completedCount++;
                
                // 更新统计信息
                for (UploadResult result : results) {
                    totalUploads.incrementAndGet();
                    if (result.isSuccess()) {
                        successfulUploads.incrementAndGet();
                    } else {
                        failedUploads.incrementAndGet();
                    }
                }
                
                // 每完成10个任务显示进度
                if (completedCount % 10 == 0 || completedCount == futures.size()) {
                    printProgress(completedCount, futures.size());
                }
                
            } catch (Exception e) {
                logger.error("任务执行失败: {}", e.getMessage());
                completedCount++;
            }
        }
        
        printFinalStats();
    }
    
    /**
     * 生成时间点列表
     */
    private List<LocalDateTime> generateTimePoints(LocalDateTime start, LocalDateTime end) {
        List<LocalDateTime> timePoints = new ArrayList<>();
        LocalDateTime current = start;
        
        while (current.isBefore(end) || current.equals(end)) {
            timePoints.add(current);
            current = current.plusMinutes(1);
        }
        
        return timePoints;
    }
    
    /**
     * 上传单个设备的数据
     */
    private List<UploadResult> uploadDeviceData(String deviceSn, LocalDateTime timePoint, int timeIdx, int totalTimePoints) {
        APIClient client = null;
        try {
            // 从连接池获取客户端
            client = clientPool.poll(5, TimeUnit.SECONDS);
            if (client == null) {
                throw new RuntimeException("无法获取API客户端");
            }
            
            // 生成数据
            Map<String, Object> dataSet = generateDataForTime(deviceSn, timePoint);
            List<UploadResult> results = new ArrayList<>();
            
            // 上传健康数据
            try {
                List<Map<String, Object>> healthDataList = Arrays.asList((Map<String, Object>) dataSet.get("health_data"));
                UploadResult healthResult = client.uploadHealthData(healthDataList);
                healthResult.setDeviceSn(deviceSn);
                healthResult.setEndpoint("upload_health_data");
                results.add(healthResult);
            } catch (Exception e) {
                results.add(new UploadResult(false, "upload_health_data", deviceSn, e.getMessage()));
            }
            
            // 上传设备信息
            try {
                List<Map<String, Object>> deviceInfoList = Arrays.asList((Map<String, Object>) dataSet.get("device_info"));
                UploadResult deviceResult = client.uploadDeviceInfo(deviceInfoList);
                deviceResult.setDeviceSn(deviceSn);
                deviceResult.setEndpoint("upload_device_info");
                results.add(deviceResult);
            } catch (Exception e) {
                results.add(new UploadResult(false, "upload_device_info", deviceSn, e.getMessage()));
            }
            
            // 上传通用事件
            try {
                Map<String, Object> commonEvent = (Map<String, Object>) dataSet.get("common_event");
                UploadResult eventResult = client.uploadCommonEvent(commonEvent);
                eventResult.setDeviceSn(deviceSn);
                eventResult.setEndpoint("upload_common_event");
                results.add(eventResult);
            } catch (Exception e) {
                results.add(new UploadResult(false, "upload_common_event", deviceSn, e.getMessage()));
            }
            
            return results;
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return Arrays.asList(new UploadResult(false, "all", deviceSn, "任务被中断"));
        } finally {
            // 归还客户端到连接池
            if (client != null) {
                clientPool.offer(client);
            }
        }
    }
    
    /**
     * 为指定时间生成测试数据
     */
    private Map<String, Object> generateDataForTime(String deviceSn, LocalDateTime timePoint) {
        String timestampStr = timePoint.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        Random random = new Random();
        
        // 健康数据
        Map<String, Object> healthData = new HashMap<>();
        healthData.put("device_id", deviceSn);
        healthData.put("user_id", "123");
        healthData.put("org_id", "456");
        healthData.put("customer_id", "8");
        healthData.put("heart_rate", 60 + random.nextInt(60));
        healthData.put("blood_oxygen", random.nextDouble() > 0.3 ? 95 + random.nextInt(5) : 0);
        healthData.put("temperature", 36.0 + random.nextDouble() * 1.5);
        healthData.put("pressure_high", 110 + random.nextInt(30));
        healthData.put("pressure_low", 70 + random.nextInt(20));
        healthData.put("stress", random.nextInt(100));
        healthData.put("step", random.nextInt(15000));
        healthData.put("distance", random.nextDouble() * 10);
        healthData.put("calorie", random.nextDouble() * 500);
        healthData.put("sleep", null);
        healthData.put("workout_data", null);
        healthData.put("create_time", timestampStr);
        
        // 设备信息
        Map<String, Object> deviceInfo = new HashMap<>();
        deviceInfo.put("device_id", deviceSn);
        deviceInfo.put("device_name", "HUAWEI WATCH B7-" + (500 + random.nextInt(100)));
        deviceInfo.put("customer_id", "8");
        deviceInfo.put("battery_level", 10 + random.nextInt(90));
        deviceInfo.put("firmware_version", "2.1." + random.nextInt(10));
        deviceInfo.put("timestamp", timestampStr);
        
        // 通用事件
        Map<String, Object> commonEvent = new HashMap<>();
        commonEvent.put("eventType", "WEAR_STATUS_CHANGED");
        commonEvent.put("eventLevel", "INFO");
        commonEvent.put("deviceSn", deviceSn);
        commonEvent.put("userId", "123");
        commonEvent.put("customerId", "8");
        commonEvent.put("orgId", "456");
        commonEvent.put("eventDescription", "设备状态变化");
        commonEvent.put("eventTime", System.currentTimeMillis());
        commonEvent.put("priority", 3);
        commonEvent.put("immediateNotification", false);
        
        Map<String, Object> location = new HashMap<>();
        location.put("lat", 22.5 + random.nextDouble() * 0.1);
        location.put("lng", 114.0 + random.nextDouble() * 0.1);
        commonEvent.put("location", location);
        
        Map<String, Object> result = new HashMap<>();
        result.put("health_data", healthData);
        result.put("device_info", deviceInfo);
        result.put("common_event", commonEvent);
        
        return result;
    }
    
    /**
     * 显示进度
     */
    private void printProgress(int completed, int total) {
        long currentTime = System.currentTimeMillis();
        long elapsedSeconds = (currentTime - startTime.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli()) / 1000;
        
        double progress = (double) completed / total * 100;
        long totalOps = totalUploads.get();
        long successOps = successfulUploads.get();
        double successRate = totalOps > 0 ? (double) successOps / totalOps * 100 : 0;
        double uploadSpeed = elapsedSeconds > 0 ? (double) totalOps / elapsedSeconds : 0;
        
        logger.info("📊 进度: {:.1f}% | {}/{} | 成功率: {:.1f}% | 速度: {:.1f} 次/秒", 
                   progress, completed, total, successRate, uploadSpeed);
    }
    
    /**
     * 打印最终统计
     */
    private void printFinalStats() {
        logger.info("=" + "=".repeat(80));
        logger.info("📊 高速上传完成统计");
        logger.info("=" + "=".repeat(80));
        
        if (startTime != null) {
            long duration = ChronoUnit.SECONDS.between(startTime, LocalDateTime.now());
            logger.info("总耗时: {} 秒", duration);
            
            // 计算速度
            long totalOps = totalUploads.get();
            if (totalOps > 0 && duration > 0) {
                double uploadSpeed = (double) totalOps / duration;
                logger.info("平均上传速度: {:.2f} 次/秒", uploadSpeed);
                logger.info("峰值处理能力: {:.0f} 次/分钟", uploadSpeed * 60);
            }
        }
        
        logger.info("设备数量: {}", deviceList.size());
        logger.info("总操作数: {}", totalUploads.get());
        logger.info("成功次数: {}", successfulUploads.get());
        logger.info("失败次数: {}", failedUploads.get());
        
        long totalOps = totalUploads.get();
        if (totalOps > 0) {
            double successRate = (double) successfulUploads.get() / totalOps * 100;
            logger.info("成功率: {:.2f}%", successRate);
        }
    }
    
    /**
     * 停止上传
     */
    public void stop() {
        running = false;
        executor.shutdown();
        try {
            if (!executor.awaitTermination(10, TimeUnit.SECONDS)) {
                executor.shutdownNow();
            }
        } catch (InterruptedException e) {
            executor.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}