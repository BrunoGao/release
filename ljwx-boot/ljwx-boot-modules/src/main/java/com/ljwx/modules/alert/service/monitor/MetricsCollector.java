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

package com.ljwx.modules.alert.service.monitor;

import com.ljwx.infrastructure.util.RedisUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 指标收集器
 * 收集和记录系统性能指标
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.monitor.MetricsCollector
 * @CreateTime 2024-08-30 - 20:30:00
 */
@Slf4j
@Service
public class MetricsCollector {

    private static final String METRICS_PREFIX = "alert_metrics:";
    private static final String DAILY_METRICS_PREFIX = "alert_daily_metrics:";
    
    // 内存中的计数器（为了性能）
    private final AtomicLong successCount = new AtomicLong(0);
    private final AtomicLong failureCount = new AtomicLong(0);
    private final AtomicLong totalProcessingTime = new AtomicLong(0);
    private final AtomicLong processedCount = new AtomicLong(0);

    /**
     * 记录告警处理成功
     */
    public void recordAlertProcessingSuccess(long processingTime) {
        try {
            // 更新内存计数器
            successCount.incrementAndGet();
            totalProcessingTime.addAndGet(processingTime);
            processedCount.incrementAndGet();
            
            // 异步更新Redis
            updateRedisMetricsAsync("success", processingTime);
            
            log.debug("记录告警处理成功: processingTime={}ms", processingTime);
            
        } catch (Exception e) {
            log.error("记录处理成功指标失败", e);
        }
    }

    /**
     * 记录告警处理失败
     */
    public void recordAlertProcessingFailure(long processingTime, String errorType) {
        try {
            // 更新内存计数器
            failureCount.incrementAndGet();
            totalProcessingTime.addAndGet(processingTime);
            processedCount.incrementAndGet();
            
            // 异步更新Redis
            updateRedisMetricsAsync("failure", processingTime, errorType);
            
            log.debug("记录告警处理失败: processingTime={}ms, errorType={}", processingTime, errorType);
            
        } catch (Exception e) {
            log.error("记录处理失败指标失败", e);
        }
    }

    /**
     * 记录队列操作
     */
    public void recordQueueOperation(String operation, int taskCount, long operationTime) {
        try {
            String key = METRICS_PREFIX + "queue:" + operation;
            
            // 记录操作次数
            RedisUtil.incr(key + ":count", 1);
            
            // 记录任务数量
            if (taskCount > 0) {
                RedisUtil.incr(key + ":tasks", taskCount);
            }
            
            // 记录操作时间
            if (operationTime > 0) {
                String timeKey = key + ":time";
                RedisUtil.incr(timeKey, operationTime);
            }
            
            log.debug("记录队列操作: operation={}, taskCount={}, time={}ms", 
                    operation, taskCount, operationTime);
            
        } catch (Exception e) {
            log.error("记录队列操作指标失败", e);
        }
    }

    /**
     * 记录通知分发
     */
    public void recordNotificationDistribution(String channel, boolean success, long deliveryTime) {
        try {
            String baseKey = METRICS_PREFIX + "notification:" + channel;
            
            // 记录总数
            RedisUtil.incr(baseKey + ":total", 1);
            
            // 记录成功/失败
            if (success) {
                RedisUtil.incr(baseKey + ":success", 1);
            } else {
                RedisUtil.incr(baseKey + ":failure", 1);
            }
            
            // 记录投递时间
            if (deliveryTime > 0) {
                RedisUtil.incr(baseKey + ":delivery_time", deliveryTime);
            }
            
            log.debug("记录通知分发: channel={}, success={}, deliveryTime={}ms", 
                    channel, success, deliveryTime);
            
        } catch (Exception e) {
            log.error("记录通知分发指标失败", e);
        }
    }

    /**
     * 记录AI分析性能
     */
    public void recordAIAnalysisPerformance(String analysisType, long analysisTime, double confidence) {
        try {
            String baseKey = METRICS_PREFIX + "ai:" + analysisType;
            
            // 记录分析次数
            RedisUtil.incr(baseKey + ":count", 1);
            
            // 记录分析时间
            RedisUtil.incr(baseKey + ":time", analysisTime);
            
            // 记录置信度（累计，用于计算平均值）
            long confidenceValue = Math.round(confidence * 1000); // 保留3位小数
            RedisUtil.incr(baseKey + ":confidence", confidenceValue);
            
            log.debug("记录AI分析性能: type={}, time={}ms, confidence={}", 
                    analysisType, analysisTime, confidence);
            
        } catch (Exception e) {
            log.error("记录AI分析性能指标失败", e);
        }
    }

    /**
     * 获取实时统计数据
     */
    public AlertMetricsSnapshot getMetricsSnapshot() {
        try {
            long currentSuccessCount = successCount.get();
            long currentFailureCount = failureCount.get();
            long currentTotalTime = totalProcessingTime.get();
            long currentProcessedCount = processedCount.get();
            
            double avgProcessingTime = currentProcessedCount > 0 ? 
                    (double) currentTotalTime / currentProcessedCount : 0;
            
            double errorRate = (currentSuccessCount + currentFailureCount) > 0 ?
                    (double) currentFailureCount / (currentSuccessCount + currentFailureCount) : 0;
            
            return AlertMetricsSnapshot.builder()
                    .timestamp(LocalDateTime.now())
                    .successCount(currentSuccessCount)
                    .failureCount(currentFailureCount)
                    .totalProcessed(currentProcessedCount)
                    .avgProcessingTime(avgProcessingTime)
                    .errorRate(errorRate)
                    .throughput(calculateThroughput())
                    .build();
            
        } catch (Exception e) {
            log.error("获取指标快照失败", e);
            return AlertMetricsSnapshot.builder()
                    .timestamp(LocalDateTime.now())
                    .build();
        }
    }

    /**
     * 重置计数器（通常在每日统计后调用）
     */
    public void resetCounters() {
        try {
            successCount.set(0);
            failureCount.set(0);
            totalProcessingTime.set(0);
            processedCount.set(0);
            
            log.info("指标计数器已重置");
            
        } catch (Exception e) {
            log.error("重置计数器失败", e);
        }
    }

    /**
     * 生成每日统计报告
     */
    public void generateDailyReport() {
        try {
            String today = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
            String dailyKey = DAILY_METRICS_PREFIX + today;
            
            AlertMetricsSnapshot snapshot = getMetricsSnapshot();
            
            // 保存每日统计
            RedisUtil.set(dailyKey + ":success_count", snapshot.getSuccessCount(), 30 * 24 * 60 * 60); // 30天
            RedisUtil.set(dailyKey + ":failure_count", snapshot.getFailureCount(), 30 * 24 * 60 * 60);
            RedisUtil.set(dailyKey + ":total_processed", snapshot.getTotalProcessed(), 30 * 24 * 60 * 60);
            RedisUtil.set(dailyKey + ":avg_processing_time", snapshot.getAvgProcessingTime(), 30 * 24 * 60 * 60);
            RedisUtil.set(dailyKey + ":error_rate", snapshot.getErrorRate(), 30 * 24 * 60 * 60);
            RedisUtil.set(dailyKey + ":throughput", snapshot.getThroughput(), 30 * 24 * 60 * 60);
            
            log.info("生成每日统计报告: date={}, processed={}, errorRate={:.2%}", 
                    today, snapshot.getTotalProcessed(), snapshot.getErrorRate());
            
            // 重置计数器
            resetCounters();
            
        } catch (Exception e) {
            log.error("生成每日统计报告失败", e);
        }
    }

    /**
     * 异步更新Redis指标
     */
    @Async("metricsExecutor")
    protected void updateRedisMetricsAsync(String result, long processingTime) {
        updateRedisMetricsAsync(result, processingTime, null);
    }

    /**
     * 异步更新Redis指标
     */
    @Async("metricsExecutor")
    protected void updateRedisMetricsAsync(String result, long processingTime, String errorType) {
        try {
            // 更新基础计数
            RedisUtil.incr(METRICS_PREFIX + result + "_count", 1);
            
            // 更新处理时间
            RedisUtil.incr(METRICS_PREFIX + "total_processing_time", processingTime);
            RedisUtil.incr(METRICS_PREFIX + "total_processed_count", 1);
            
            // 更新平均处理时间
            updateAverageProcessingTime(processingTime);
            
            // 如果是失败，记录错误类型
            if ("failure".equals(result) && errorType != null) {
                RedisUtil.incr(METRICS_PREFIX + "error_type:" + errorType, 1);
            }
            
            // 更新吞吐量（每分钟）
            updateThroughputMetrics();
            
        } catch (Exception e) {
            log.error("异步更新Redis指标失败", e);
        }
    }

    /**
     * 更新平均处理时间
     */
    private void updateAverageProcessingTime(long processingTime) {
        try {
            String avgTimeKey = METRICS_PREFIX + "avg_processing_time";
            
            // 获取当前平均值和计数
            Object currentAvgObj = RedisUtil.get(avgTimeKey);
            Object countObj = RedisUtil.get(METRICS_PREFIX + "total_processed_count");
            
            double currentAvg = currentAvgObj instanceof Number ? 
                    ((Number) currentAvgObj).doubleValue() : 0;
            long count = countObj instanceof Number ? 
                    ((Number) countObj).longValue() : 1;
            
            // 计算新的平均值
            double newAvg = ((currentAvg * (count - 1)) + processingTime) / count;
            
            RedisUtil.set(avgTimeKey, newAvg, 24 * 60 * 60); // 24小时过期
            
        } catch (Exception e) {
            log.error("更新平均处理时间失败", e);
        }
    }

    /**
     * 更新吞吐量指标
     */
    private void updateThroughputMetrics() {
        try {
            String minuteKey = METRICS_PREFIX + "throughput:" + 
                    (System.currentTimeMillis() / (60 * 1000)); // 按分钟分组
            
            RedisUtil.incr(minuteKey, 1);
            RedisUtil.expire(minuteKey, 60 * 60); // 1小时过期
            
        } catch (Exception e) {
            log.error("更新吞吐量指标失败", e);
        }
    }

    /**
     * 计算当前吞吐量
     */
    private double calculateThroughput() {
        try {
            // 计算过去5分钟的平均吞吐量
            long currentMinute = System.currentTimeMillis() / (60 * 1000);
            long totalMessages = 0;
            
            for (int i = 0; i < 5; i++) {
                String minuteKey = METRICS_PREFIX + "throughput:" + (currentMinute - i);
                Object count = RedisUtil.get(minuteKey);
                if (count instanceof Number) {
                    totalMessages += ((Number) count).longValue();
                }
            }
            
            return totalMessages / 5.0; // 平均每分钟消息数
            
        } catch (Exception e) {
            log.error("计算吞吐量失败", e);
            return 0.0;
        }
    }

    /**
     * 指标快照数据类
     */
    public static class AlertMetricsSnapshot {
        private LocalDateTime timestamp;
        private long successCount;
        private long failureCount;
        private long totalProcessed;
        private double avgProcessingTime;
        private double errorRate;
        private double throughput;

        // Builder pattern
        public static Builder builder() {
            return new Builder();
        }

        public static class Builder {
            private final AlertMetricsSnapshot snapshot = new AlertMetricsSnapshot();

            public Builder timestamp(LocalDateTime timestamp) {
                snapshot.timestamp = timestamp;
                return this;
            }

            public Builder successCount(long successCount) {
                snapshot.successCount = successCount;
                return this;
            }

            public Builder failureCount(long failureCount) {
                snapshot.failureCount = failureCount;
                return this;
            }

            public Builder totalProcessed(long totalProcessed) {
                snapshot.totalProcessed = totalProcessed;
                return this;
            }

            public Builder avgProcessingTime(double avgProcessingTime) {
                snapshot.avgProcessingTime = avgProcessingTime;
                return this;
            }

            public Builder errorRate(double errorRate) {
                snapshot.errorRate = errorRate;
                return this;
            }

            public Builder throughput(double throughput) {
                snapshot.throughput = throughput;
                return this;
            }

            public AlertMetricsSnapshot build() {
                return snapshot;
            }
        }

        // Getters
        public LocalDateTime getTimestamp() { return timestamp; }
        public long getSuccessCount() { return successCount; }
        public long getFailureCount() { return failureCount; }
        public long getTotalProcessed() { return totalProcessed; }
        public double getAvgProcessingTime() { return avgProcessingTime; }
        public double getErrorRate() { return errorRate; }
        public double getThroughput() { return throughput; }
    }
}