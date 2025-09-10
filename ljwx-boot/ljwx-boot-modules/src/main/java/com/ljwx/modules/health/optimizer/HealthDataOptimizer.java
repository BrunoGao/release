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

import com.ljwx.modules.health.domain.entity.TUserHealthData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

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