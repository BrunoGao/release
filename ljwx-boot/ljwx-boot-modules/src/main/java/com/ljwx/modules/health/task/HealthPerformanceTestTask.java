package com.ljwx.modules.health.task;

import com.ljwx.modules.health.service.*;
import com.ljwx.modules.health.service.HealthDataCacheService.CacheStatistics;
import com.ljwx.modules.health.service.HealthProfileService.ComprehensiveHealthProfile;
import com.ljwx.modules.health.service.HealthScoreCalculationService.HealthScoreDetail;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.stream.IntStream;

/**
 * 健康系统性能测试任务
 * 用于测试和验证健康基线评分画像系统的性能指标
 */
@Slf4j
@Component
public class HealthPerformanceTestTask {

    @Autowired
    private HealthBaselineService healthBaselineService;
    
    @Autowired
    private HealthScoreCalculationService healthScoreService;
    
    @Autowired
    private HealthRecommendationService healthRecommendationService;
    
    @Autowired
    private HealthProfileService healthProfileService;
    
    @Autowired
    private HealthDataCacheService cacheService;
    
    @Autowired
    private ISysUserService sysUserService;

    // 性能测试配置
    private static final int CONCURRENT_USERS = 50;  // 并发用户数
    private static final int TEST_ITERATIONS = 100;  // 测试迭代次数
    private static final long TEST_USER_ID = 1L;     // 测试用户ID

    /**
     * 执行完整的性能测试套件
     */
    public PerformanceTestReport executeFullPerformanceTest() {
        log.info("开始执行健康系统完整性能测试");
        
        PerformanceTestReport report = new PerformanceTestReport();
        report.setStartTime(LocalDateTime.now());
        
        try {
            // 1. 基线生成性能测试
            log.info("执行基线生成性能测试");
            BaselinePerformanceResult baselineResult = testBaselineGeneration();
            report.setBaselineResult(baselineResult);
            
            // 2. 评分计算性能测试
            log.info("执行评分计算性能测试");
            ScorePerformanceResult scoreResult = testScoreCalculation();
            report.setScoreResult(scoreResult);
            
            // 3. 画像生成性能测试
            log.info("执行画像生成性能测试");
            ProfilePerformanceResult profileResult = testProfileGeneration();
            report.setProfileResult(profileResult);
            
            // 4. 并发性能测试
            log.info("执行并发性能测试");
            ConcurrencyPerformanceResult concurrencyResult = testConcurrentAccess();
            report.setConcurrencyResult(concurrencyResult);
            
            // 5. 缓存性能测试
            log.info("执行缓存性能测试");
            CachePerformanceResult cacheResult = testCachePerformance();
            report.setCacheResult(cacheResult);
            
            // 6. 内存使用测试
            log.info("执行内存使用测试");
            MemoryUsageResult memoryResult = testMemoryUsage();
            report.setMemoryResult(memoryResult);
            
            report.setEndTime(LocalDateTime.now());
            report.setTotalDuration(java.time.Duration.between(report.getStartTime(), report.getEndTime()).toMillis());
            report.setSuccess(true);
            
            log.info("健康系统性能测试完成，总耗时: {}ms", report.getTotalDuration());
            
            // 打印测试报告摘要
            printTestReportSummary(report);
            
            return report;
            
        } catch (Exception e) {
            log.error("性能测试执行失败: error={}", e.getMessage(), e);
            report.setEndTime(LocalDateTime.now());
            report.setSuccess(false);
            report.setErrorMessage(e.getMessage());
            return report;
        }
    }

    /**
     * 测试基线生成性能
     */
    private BaselinePerformanceResult testBaselineGeneration() {
        BaselinePerformanceResult result = new BaselinePerformanceResult();
        List<Long> executionTimes = new ArrayList<>();
        
        log.info("开始基线生成性能测试，测试{}次", TEST_ITERATIONS);
        
        int successCount = 0;
        int failCount = 0;
        
        for (int i = 0; i < TEST_ITERATIONS; i++) {
            try {
                long startTime = System.currentTimeMillis();
                
                healthBaselineService.generatePersonalBaseline(TEST_USER_ID, 30);
                
                long endTime = System.currentTimeMillis();
                long duration = endTime - startTime;
                executionTimes.add(duration);
                successCount++;
                
                if (i % 20 == 0) {
                    log.debug("基线生成测试进度: {}/{}, 当前耗时: {}ms", i + 1, TEST_ITERATIONS, duration);
                }
                
            } catch (Exception e) {
                failCount++;
                log.debug("基线生成测试失败: iteration={}, error={}", i, e.getMessage());
            }
        }
        
        // 计算统计数据
        result.setTotalTests(TEST_ITERATIONS);
        result.setSuccessCount(successCount);
        result.setFailCount(failCount);
        result.setSuccessRate((double) successCount / TEST_ITERATIONS * 100);
        
        if (!executionTimes.isEmpty()) {
            result.setAverageTime(executionTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
            result.setMinTime(executionTimes.stream().mapToLong(Long::longValue).min().orElse(0L));
            result.setMaxTime(executionTimes.stream().mapToLong(Long::longValue).max().orElse(0L));
            result.setMedianTime(calculateMedian(executionTimes));
        }
        
        log.info("基线生成性能测试完成: 成功率={}%, 平均耗时={}ms", 
            String.format("%.2f", result.getSuccessRate()), 
            String.format("%.2f", result.getAverageTime()));
        
        return result;
    }

    /**
     * 测试评分计算性能
     */
    private ScorePerformanceResult testScoreCalculation() {
        ScorePerformanceResult result = new ScorePerformanceResult();
        List<Long> executionTimes = new ArrayList<>();
        
        log.info("开始评分计算性能测试，测试{}次", TEST_ITERATIONS);
        
        int successCount = 0;
        int failCount = 0;
        
        for (int i = 0; i < TEST_ITERATIONS; i++) {
            try {
                long startTime = System.currentTimeMillis();
                
                HealthScoreDetail scoreDetail = healthScoreService.calculateComprehensiveHealthScore(TEST_USER_ID, 30);
                
                long endTime = System.currentTimeMillis();
                long duration = endTime - startTime;
                executionTimes.add(duration);
                
                if (scoreDetail != null) {
                    successCount++;
                } else {
                    failCount++;
                }
                
                if (i % 20 == 0) {
                    log.debug("评分计算测试进度: {}/{}, 当前耗时: {}ms", i + 1, TEST_ITERATIONS, duration);
                }
                
            } catch (Exception e) {
                failCount++;
                log.debug("评分计算测试失败: iteration={}, error={}", i, e.getMessage());
            }
        }
        
        // 计算统计数据
        result.setTotalTests(TEST_ITERATIONS);
        result.setSuccessCount(successCount);
        result.setFailCount(failCount);
        result.setSuccessRate((double) successCount / TEST_ITERATIONS * 100);
        
        if (!executionTimes.isEmpty()) {
            result.setAverageTime(executionTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
            result.setMinTime(executionTimes.stream().mapToLong(Long::longValue).min().orElse(0L));
            result.setMaxTime(executionTimes.stream().mapToLong(Long::longValue).max().orElse(0L));
            result.setMedianTime(calculateMedian(executionTimes));
        }
        
        log.info("评分计算性能测试完成: 成功率={}%, 平均耗时={}ms", 
            String.format("%.2f", result.getSuccessRate()), 
            String.format("%.2f", result.getAverageTime()));
        
        return result;
    }

    /**
     * 测试画像生成性能
     */
    private ProfilePerformanceResult testProfileGeneration() {
        ProfilePerformanceResult result = new ProfilePerformanceResult();
        List<Long> executionTimes = new ArrayList<>();
        
        log.info("开始画像生成性能测试，测试{}次", TEST_ITERATIONS / 2); // 画像生成较重，减少测试次数
        
        int successCount = 0;
        int failCount = 0;
        int testCount = TEST_ITERATIONS / 2;
        
        for (int i = 0; i < testCount; i++) {
            try {
                long startTime = System.currentTimeMillis();
                
                ComprehensiveHealthProfile profile = healthProfileService.generateComprehensiveHealthProfile(TEST_USER_ID);
                
                long endTime = System.currentTimeMillis();
                long duration = endTime - startTime;
                executionTimes.add(duration);
                
                if (profile != null) {
                    successCount++;
                } else {
                    failCount++;
                }
                
                if (i % 10 == 0) {
                    log.debug("画像生成测试进度: {}/{}, 当前耗时: {}ms", i + 1, testCount, duration);
                }
                
            } catch (Exception e) {
                failCount++;
                log.debug("画像生成测试失败: iteration={}, error={}", i, e.getMessage());
            }
        }
        
        // 计算统计数据
        result.setTotalTests(testCount);
        result.setSuccessCount(successCount);
        result.setFailCount(failCount);
        result.setSuccessRate((double) successCount / testCount * 100);
        
        if (!executionTimes.isEmpty()) {
            result.setAverageTime(executionTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
            result.setMinTime(executionTimes.stream().mapToLong(Long::longValue).min().orElse(0L));
            result.setMaxTime(executionTimes.stream().mapToLong(Long::longValue).max().orElse(0L));
            result.setMedianTime(calculateMedian(executionTimes));
        }
        
        log.info("画像生成性能测试完成: 成功率={}%, 平均耗时={}ms", 
            String.format("%.2f", result.getSuccessRate()), 
            String.format("%.2f", result.getAverageTime()));
        
        return result;
    }

    /**
     * 测试并发访问性能
     */
    private ConcurrencyPerformanceResult testConcurrentAccess() {
        ConcurrencyPerformanceResult result = new ConcurrencyPerformanceResult();
        
        log.info("开始并发性能测试，并发用户数: {}", CONCURRENT_USERS);
        
        ExecutorService executor = Executors.newFixedThreadPool(CONCURRENT_USERS);
        List<Future<Long>> futures = new ArrayList<>();
        
        long startTime = System.currentTimeMillis();
        
        // 提交并发任务
        for (int i = 0; i < CONCURRENT_USERS; i++) {
            final int taskId = i;
            Future<Long> future = executor.submit(() -> {
                try {
                    long taskStart = System.currentTimeMillis();
                    
                    // 执行健康评分计算
                    healthScoreService.calculateComprehensiveHealthScore(TEST_USER_ID, 30);
                    
                    long taskEnd = System.currentTimeMillis();
                    return taskEnd - taskStart;
                    
                } catch (Exception e) {
                    log.debug("并发任务{}失败: {}", taskId, e.getMessage());
                    return -1L;
                }
            });
            futures.add(future);
        }
        
        // 等待所有任务完成
        List<Long> executionTimes = new ArrayList<>();
        int successCount = 0;
        int failCount = 0;
        
        for (Future<Long> future : futures) {
            try {
                Long duration = future.get(30, TimeUnit.SECONDS);
                if (duration > 0) {
                    executionTimes.add(duration);
                    successCount++;
                } else {
                    failCount++;
                }
            } catch (Exception e) {
                failCount++;
                log.debug("并发任务执行超时或失败: {}", e.getMessage());
            }
        }
        
        long endTime = System.currentTimeMillis();
        long totalDuration = endTime - startTime;
        
        executor.shutdown();
        
        // 计算统计数据
        result.setConcurrentUsers(CONCURRENT_USERS);
        result.setTotalDuration(totalDuration);
        result.setSuccessCount(successCount);
        result.setFailCount(failCount);
        result.setSuccessRate((double) successCount / CONCURRENT_USERS * 100);
        result.setThroughput((double) successCount / (totalDuration / 1000.0)); // QPS
        
        if (!executionTimes.isEmpty()) {
            result.setAverageTime(executionTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
            result.setMinTime(executionTimes.stream().mapToLong(Long::longValue).min().orElse(0L));
            result.setMaxTime(executionTimes.stream().mapToLong(Long::longValue).max().orElse(0L));
        }
        
        log.info("并发性能测试完成: 成功率={}%, 吞吐量={}QPS, 总耗时={}ms", 
            String.format("%.2f", result.getSuccessRate()),
            String.format("%.2f", result.getThroughput()),
            totalDuration);
        
        return result;
    }

    /**
     * 测试缓存性能
     */
    private CachePerformanceResult testCachePerformance() {
        CachePerformanceResult result = new CachePerformanceResult();
        
        log.info("开始缓存性能测试");
        
        // 测试缓存命中率
        int cacheTestCount = 50;
        int cacheHitCount = 0;
        int cacheMissCount = 0;
        
        List<Long> cacheReadTimes = new ArrayList<>();
        List<Long> cacheWriteTimes = new ArrayList<>();
        
        for (int i = 0; i < cacheTestCount; i++) {
            try {
                // 测试缓存写入
                long writeStart = System.currentTimeMillis();
                cacheService.setUserHealthSummary(TEST_USER_ID, "test_data_" + i);
                long writeEnd = System.currentTimeMillis();
                cacheWriteTimes.add(writeEnd - writeStart);
                
                // 测试缓存读取
                long readStart = System.currentTimeMillis();
                String cachedData = cacheService.getUserHealthSummary(TEST_USER_ID);
                long readEnd = System.currentTimeMillis();
                cacheReadTimes.add(readEnd - readStart);
                
                if (cachedData != null) {
                    cacheHitCount++;
                } else {
                    cacheMissCount++;
                }
                
            } catch (Exception e) {
                log.debug("缓存测试失败: iteration={}, error={}", i, e.getMessage());
            }
        }
        
        // 获取缓存统计信息
        CacheStatistics cacheStats = cacheService.getCacheStatistics();
        
        // 计算结果
        result.setTotalCacheTests(cacheTestCount);
        result.setCacheHitCount(cacheHitCount);
        result.setCacheMissCount(cacheMissCount);
        result.setCacheHitRate((double) cacheHitCount / cacheTestCount * 100);
        
        if (!cacheReadTimes.isEmpty()) {
            result.setAverageCacheReadTime(cacheReadTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
        }
        
        if (!cacheWriteTimes.isEmpty()) {
            result.setAverageCacheWriteTime(cacheWriteTimes.stream().mapToLong(Long::longValue).average().orElse(0.0));
        }
        
        result.setCacheStatistics(cacheStats);
        
        log.info("缓存性能测试完成: 命中率={}%, 平均读取耗时={}ms, 平均写入耗时={}ms", 
            String.format("%.2f", result.getCacheHitRate()),
            String.format("%.2f", result.getAverageCacheReadTime()),
            String.format("%.2f", result.getAverageCacheWriteTime()));
        
        return result;
    }

    /**
     * 测试内存使用
     */
    private MemoryUsageResult testMemoryUsage() {
        MemoryUsageResult result = new MemoryUsageResult();
        
        log.info("开始内存使用测试");
        
        Runtime runtime = Runtime.getRuntime();
        
        // 执行GC并获取初始内存状态
        System.gc();
        Thread.yield(); // 让GC有时间执行
        
        long initialMemory = runtime.totalMemory() - runtime.freeMemory();
        result.setInitialMemoryUsage(initialMemory);
        
        // 执行一定数量的操作
        for (int i = 0; i < 20; i++) {
            try {
                healthScoreService.calculateComprehensiveHealthScore(TEST_USER_ID, 30);
            } catch (Exception e) {
                log.debug("内存测试中的操作失败: iteration={}, error={}", i, e.getMessage());
            }
        }
        
        // 获取操作后的内存状态
        long peakMemory = runtime.totalMemory() - runtime.freeMemory();
        result.setPeakMemoryUsage(peakMemory);
        
        // 再次执行GC
        System.gc();
        Thread.yield();
        
        long finalMemory = runtime.totalMemory() - runtime.freeMemory();
        result.setFinalMemoryUsage(finalMemory);
        
        // 计算内存增长
        result.setMemoryGrowth(finalMemory - initialMemory);
        result.setMemoryGrowthPercentage((double) result.getMemoryGrowth() / initialMemory * 100);
        
        log.info("内存使用测试完成: 初始={}MB, 峰值={}MB, 最终={}MB, 增长={}MB ({}%)", 
            bytesToMB(initialMemory), bytesToMB(peakMemory), bytesToMB(finalMemory),
            bytesToMB(result.getMemoryGrowth()), String.format("%.2f", result.getMemoryGrowthPercentage()));
        
        return result;
    }

    /**
     * 打印测试报告摘要
     */
    private void printTestReportSummary(PerformanceTestReport report) {
        log.info("================== 健康系统性能测试报告 ==================");
        log.info("测试时间: {} - {}", 
            report.getStartTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")),
            report.getEndTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")));
        log.info("总耗时: {}ms", report.getTotalDuration());
        log.info("测试结果: {}", report.isSuccess() ? "成功" : "失败");
        
        if (report.getBaselineResult() != null) {
            log.info("基线生成: 成功率={}%, 平均耗时={}ms", 
                String.format("%.1f", report.getBaselineResult().getSuccessRate()),
                String.format("%.1f", report.getBaselineResult().getAverageTime()));
        }
        
        if (report.getScoreResult() != null) {
            log.info("评分计算: 成功率={}%, 平均耗时={}ms", 
                String.format("%.1f", report.getScoreResult().getSuccessRate()),
                String.format("%.1f", report.getScoreResult().getAverageTime()));
        }
        
        if (report.getProfileResult() != null) {
            log.info("画像生成: 成功率={}%, 平均耗时={}ms", 
                String.format("%.1f", report.getProfileResult().getSuccessRate()),
                String.format("%.1f", report.getProfileResult().getAverageTime()));
        }
        
        if (report.getConcurrencyResult() != null) {
            log.info("并发测试: 成功率={}%, 吞吐量={}QPS", 
                String.format("%.1f", report.getConcurrencyResult().getSuccessRate()),
                String.format("%.1f", report.getConcurrencyResult().getThroughput()));
        }
        
        if (report.getCacheResult() != null) {
            log.info("缓存测试: 命中率={}%, 读取耗时={}ms", 
                String.format("%.1f", report.getCacheResult().getCacheHitRate()),
                String.format("%.2f", report.getCacheResult().getAverageCacheReadTime()));
        }
        
        if (report.getMemoryResult() != null) {
            log.info("内存测试: 内存增长={}MB ({}%)", 
                bytesToMB(report.getMemoryResult().getMemoryGrowth()),
                String.format("%.1f", report.getMemoryResult().getMemoryGrowthPercentage()));
        }
        
        log.info("=====================================================");
    }

    // 辅助方法

    private double calculateMedian(List<Long> values) {
        if (values.isEmpty()) return 0.0;
        
        List<Long> sorted = values.stream().sorted().collect(java.util.stream.Collectors.toList());
        int size = sorted.size();
        
        if (size % 2 == 0) {
            return (sorted.get(size/2 - 1) + sorted.get(size/2)) / 2.0;
        } else {
            return sorted.get(size/2);
        }
    }

    private long bytesToMB(long bytes) {
        return bytes / (1024 * 1024);
    }

    // 内部结果类定义

    public static class PerformanceTestReport {
        private LocalDateTime startTime;
        private LocalDateTime endTime;
        private long totalDuration;
        private boolean success;
        private String errorMessage;
        private BaselinePerformanceResult baselineResult;
        private ScorePerformanceResult scoreResult;
        private ProfilePerformanceResult profileResult;
        private ConcurrencyPerformanceResult concurrencyResult;
        private CachePerformanceResult cacheResult;
        private MemoryUsageResult memoryResult;

        // Getters and Setters
        public LocalDateTime getStartTime() { return startTime; }
        public void setStartTime(LocalDateTime startTime) { this.startTime = startTime; }
        
        public LocalDateTime getEndTime() { return endTime; }
        public void setEndTime(LocalDateTime endTime) { this.endTime = endTime; }
        
        public long getTotalDuration() { return totalDuration; }
        public void setTotalDuration(long totalDuration) { this.totalDuration = totalDuration; }
        
        public boolean isSuccess() { return success; }
        public void setSuccess(boolean success) { this.success = success; }
        
        public String getErrorMessage() { return errorMessage; }
        public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
        
        public BaselinePerformanceResult getBaselineResult() { return baselineResult; }
        public void setBaselineResult(BaselinePerformanceResult baselineResult) { this.baselineResult = baselineResult; }
        
        public ScorePerformanceResult getScoreResult() { return scoreResult; }
        public void setScoreResult(ScorePerformanceResult scoreResult) { this.scoreResult = scoreResult; }
        
        public ProfilePerformanceResult getProfileResult() { return profileResult; }
        public void setProfileResult(ProfilePerformanceResult profileResult) { this.profileResult = profileResult; }
        
        public ConcurrencyPerformanceResult getConcurrencyResult() { return concurrencyResult; }
        public void setConcurrencyResult(ConcurrencyPerformanceResult concurrencyResult) { this.concurrencyResult = concurrencyResult; }
        
        public CachePerformanceResult getCacheResult() { return cacheResult; }
        public void setCacheResult(CachePerformanceResult cacheResult) { this.cacheResult = cacheResult; }
        
        public MemoryUsageResult getMemoryResult() { return memoryResult; }
        public void setMemoryResult(MemoryUsageResult memoryResult) { this.memoryResult = memoryResult; }
    }

    public static class BaselinePerformanceResult {
        private int totalTests;
        private int successCount;
        private int failCount;
        private double successRate;
        private double averageTime;
        private long minTime;
        private long maxTime;
        private double medianTime;

        // Getters and Setters
        public int getTotalTests() { return totalTests; }
        public void setTotalTests(int totalTests) { this.totalTests = totalTests; }
        
        public int getSuccessCount() { return successCount; }
        public void setSuccessCount(int successCount) { this.successCount = successCount; }
        
        public int getFailCount() { return failCount; }
        public void setFailCount(int failCount) { this.failCount = failCount; }
        
        public double getSuccessRate() { return successRate; }
        public void setSuccessRate(double successRate) { this.successRate = successRate; }
        
        public double getAverageTime() { return averageTime; }
        public void setAverageTime(double averageTime) { this.averageTime = averageTime; }
        
        public long getMinTime() { return minTime; }
        public void setMinTime(long minTime) { this.minTime = minTime; }
        
        public long getMaxTime() { return maxTime; }
        public void setMaxTime(long maxTime) { this.maxTime = maxTime; }
        
        public double getMedianTime() { return medianTime; }
        public void setMedianTime(double medianTime) { this.medianTime = medianTime; }
    }

    // 其他结果类使用类似的结构...
    public static class ScorePerformanceResult extends BaselinePerformanceResult {}
    public static class ProfilePerformanceResult extends BaselinePerformanceResult {}

    public static class ConcurrencyPerformanceResult extends BaselinePerformanceResult {
        private int concurrentUsers;
        private long totalDuration;
        private double throughput;

        public int getConcurrentUsers() { return concurrentUsers; }
        public void setConcurrentUsers(int concurrentUsers) { this.concurrentUsers = concurrentUsers; }
        
        public long getTotalDuration() { return totalDuration; }
        public void setTotalDuration(long totalDuration) { this.totalDuration = totalDuration; }
        
        public double getThroughput() { return throughput; }
        public void setThroughput(double throughput) { this.throughput = throughput; }
    }

    public static class CachePerformanceResult {
        private int totalCacheTests;
        private int cacheHitCount;
        private int cacheMissCount;
        private double cacheHitRate;
        private double averageCacheReadTime;
        private double averageCacheWriteTime;
        private CacheStatistics cacheStatistics;

        // Getters and Setters
        public int getTotalCacheTests() { return totalCacheTests; }
        public void setTotalCacheTests(int totalCacheTests) { this.totalCacheTests = totalCacheTests; }
        
        public int getCacheHitCount() { return cacheHitCount; }
        public void setCacheHitCount(int cacheHitCount) { this.cacheHitCount = cacheHitCount; }
        
        public int getCacheMissCount() { return cacheMissCount; }
        public void setCacheMissCount(int cacheMissCount) { this.cacheMissCount = cacheMissCount; }
        
        public double getCacheHitRate() { return cacheHitRate; }
        public void setCacheHitRate(double cacheHitRate) { this.cacheHitRate = cacheHitRate; }
        
        public double getAverageCacheReadTime() { return averageCacheReadTime; }
        public void setAverageCacheReadTime(double averageCacheReadTime) { this.averageCacheReadTime = averageCacheReadTime; }
        
        public double getAverageCacheWriteTime() { return averageCacheWriteTime; }
        public void setAverageCacheWriteTime(double averageCacheWriteTime) { this.averageCacheWriteTime = averageCacheWriteTime; }
        
        public CacheStatistics getCacheStatistics() { return cacheStatistics; }
        public void setCacheStatistics(CacheStatistics cacheStatistics) { this.cacheStatistics = cacheStatistics; }
    }

    public static class MemoryUsageResult {
        private long initialMemoryUsage;
        private long peakMemoryUsage;
        private long finalMemoryUsage;
        private long memoryGrowth;
        private double memoryGrowthPercentage;

        // Getters and Setters
        public long getInitialMemoryUsage() { return initialMemoryUsage; }
        public void setInitialMemoryUsage(long initialMemoryUsage) { this.initialMemoryUsage = initialMemoryUsage; }
        
        public long getPeakMemoryUsage() { return peakMemoryUsage; }
        public void setPeakMemoryUsage(long peakMemoryUsage) { this.peakMemoryUsage = peakMemoryUsage; }
        
        public long getFinalMemoryUsage() { return finalMemoryUsage; }
        public void setFinalMemoryUsage(long finalMemoryUsage) { this.finalMemoryUsage = finalMemoryUsage; }
        
        public long getMemoryGrowth() { return memoryGrowth; }
        public void setMemoryGrowth(long memoryGrowth) { this.memoryGrowth = memoryGrowth; }
        
        public double getMemoryGrowthPercentage() { return memoryGrowthPercentage; }
        public void setMemoryGrowthPercentage(double memoryGrowthPercentage) { this.memoryGrowthPercentage = memoryGrowthPercentage; }
    }
}