/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.utils;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Data;
import lombok.Builder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * LJWX消息系统V2性能测试工具
 * 
 * 功能特性：
 * 1. 多维度性能测试（TPS、延迟、吞吐量、并发）
 * 2. V1/V2系统对比测试
 * 3. 实时性能监控和报告
 * 4. 自动化测试场景生成
 * 5. 详细的性能分析报告
 * 
 * 使用方法：
 * - 开发环境: --spring.profiles.active=dev --ljwx.test.message-performance=true
 * - 测试环境: --spring.profiles.active=test --ljwx.test.message-performance=true
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName MessageSystemPerformanceTest
 * @CreateTime 2025-09-10
 */
@Slf4j
@Component
@Profile({"dev", "test"})
@ConditionalOnProperty(name = "ljwx.test.message-performance", havingValue = "true")
public class MessageSystemPerformanceTest implements CommandLineRunner {

    // ==================== 配置参数 ====================
    private static final String BASE_URL = "http://localhost:8080";
    private static final String V1_API_PREFIX = "/api/v1/messages";
    private static final String V2_API_PREFIX = "/api/v2/messages";
    
    // 测试参数配置
    private static final int WARMUP_REQUESTS = 100;           // 预热请求数
    private static final int CONCURRENT_USERS = 50;           // 并发用户数
    private static final int REQUESTS_PER_USER = 100;         // 每用户请求数
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(30);
    private static final int THREAD_POOL_SIZE = 100;
    
    // HTTP客户端
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final ExecutorService executorService;
    
    // 性能指标收集器
    private final AtomicLong totalRequests = new AtomicLong();
    private final AtomicLong successRequests = new AtomicLong();
    private final AtomicLong failedRequests = new AtomicLong();
    private final List<Long> responseTimes = Collections.synchronizedList(new ArrayList<>());
    private final Map<String, AtomicInteger> errorCodes = new ConcurrentHashMap<>();
    
    public MessageSystemPerformanceTest() {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
        this.objectMapper = new ObjectMapper();
        this.executorService = Executors.newFixedThreadPool(THREAD_POOL_SIZE);
    }

    @Override
    public void run(String... args) throws Exception {
        log.info("🚀 启动LJWX消息系统V2性能测试");
        
        try {
            // 1. 系统预热
            warmupSystem();
            
            // 2. V1系统性能基准测试
            log.info("📊 开始V1系统性能基准测试...");
            PerformanceResult v1Result = performanceTest("V1", V1_API_PREFIX);
            
            // 3. V2系统性能测试
            log.info("📊 开始V2系统性能测试...");
            PerformanceResult v2Result = performanceTest("V2", V2_API_PREFIX);
            
            // 4. 对比分析和报告生成
            generatePerformanceReport(v1Result, v2Result);
            
            // 5. 数据库性能测试
            databasePerformanceTest();
            
            // 6. 压力测试
            stressTest();
            
            log.info("✅ 性能测试完成，详细报告已生成");
            
        } catch (Exception e) {
            log.error("❌ 性能测试执行失败", e);
            throw e;
        } finally {
            executorService.shutdown();
            if (!executorService.awaitTermination(30, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
        }
    }

    /**
     * 系统预热 - 避免冷启动影响测试结果
     */
    private void warmupSystem() throws Exception {
        log.info("🔥 系统预热中... ({} 个请求)", WARMUP_REQUESTS);
        
        List<CompletableFuture<Void>> warmupTasks = IntStream.range(0, WARMUP_REQUESTS)
                .mapToObj(i -> CompletableFuture.runAsync(() -> {
                    try {
                        // 简单的健康检查请求
                        sendRequest("GET", "/actuator/health", null);
                    } catch (Exception e) {
                        // 预热过程中忽略错误
                    }
                }, executorService))
                .collect(Collectors.toList());
        
        CompletableFuture.allOf(warmupTasks.toArray(new CompletableFuture[0])).get();
        
        // 等待系统稳定
        Thread.sleep(5000);
        log.info("✅ 系统预热完成");
    }

    /**
     * 执行性能测试
     */
    private PerformanceResult performanceTest(String version, String apiPrefix) throws Exception {
        log.info("🧪 开始 {} 系统性能测试", version);
        
        // 重置计数器
        resetCounters();
        
        long startTime = System.currentTimeMillis();
        
        // 创建并发测试任务
        List<CompletableFuture<Void>> testTasks = IntStream.range(0, CONCURRENT_USERS)
                .mapToObj(userId -> CompletableFuture.runAsync(() -> {
                    try {
                        executeUserScenario(userId, apiPrefix);
                    } catch (Exception e) {
                        log.error("用户 {} 测试场景执行失败", userId, e);
                    }
                }, executorService))
                .collect(Collectors.toList());
        
        // 等待所有任务完成
        CompletableFuture.allOf(testTasks.toArray(new CompletableFuture[0])).get();
        
        long endTime = System.currentTimeMillis();
        long totalTimeMs = endTime - startTime;
        
        // 构建性能结果
        return buildPerformanceResult(version, totalTimeMs);
    }

    /**
     * 执行单个用户的测试场景
     */
    private void executeUserScenario(int userId, String apiPrefix) throws Exception {
        Random random = new Random();
        
        for (int i = 0; i < REQUESTS_PER_USER; i++) {
            // 随机选择测试场景
            int scenario = random.nextInt(5);
            
            switch (scenario) {
                case 0 -> testCreateMessage(apiPrefix, userId);
                case 1 -> testQueryMessages(apiPrefix, userId);
                case 2 -> testBatchOperations(apiPrefix, userId);
                case 3 -> testMessageStatus(apiPrefix, userId);
                case 4 -> testMessageStatistics(apiPrefix, userId);
            }
            
            // 模拟真实用户行为间隔
            Thread.sleep(random.nextInt(100) + 50);
        }
    }

    /**
     * 测试消息创建
     */
    private void testCreateMessage(String apiPrefix, int userId) throws Exception {
        Map<String, Object> messageData = Map.of(
                "deviceSn", "TEST_DEVICE_" + userId,
                "title", "性能测试消息 " + System.currentTimeMillis(),
                "message", "这是用户 " + userId + " 的性能测试消息内容",
                "messageType", "notification",
                "senderType", "system",
                "receiverType", "device",
                "customerId", 1,
                "urgency", "medium",
                "priority", 3,
                "requireAck", false
        );
        
        sendRequest("POST", apiPrefix, messageData);
    }

    /**
     * 测试消息查询
     */
    private void testQueryMessages(String apiPrefix, int userId) throws Exception {
        String queryParams = "?customerId=1&page=1&pageSize=20&deviceSn=TEST_DEVICE_" + userId;
        sendRequest("GET", apiPrefix + queryParams, null);
    }

    /**
     * 测试批量操作
     */
    private void testBatchOperations(String apiPrefix, int userId) throws Exception {
        List<Map<String, Object>> batchData = IntStream.range(0, 10)
                .mapToObj(i -> Map.of(
                        "deviceSn", "BATCH_DEVICE_" + userId + "_" + i,
                        "title", "批量测试消息 " + i,
                        "message", "批量测试内容 " + i,
                        "messageType", "notification",
                        "senderType", "system",
                        "receiverType", "device",
                        "customerId", 1
                ))
                .collect(Collectors.toList());
        
        sendRequest("POST", apiPrefix + "/batch", batchData);
    }

    /**
     * 测试消息状态更新
     */
    private void testMessageStatus(String apiPrefix, int userId) throws Exception {
        // 假设消息ID为用户ID+1000
        long messageId = userId + 1000L;
        Map<String, Object> statusData = Map.of(
                "messageStatus", "acknowledged",
                "updateTime", LocalDateTime.now().toString()
        );
        
        sendRequest("PUT", apiPrefix + "/" + messageId, statusData);
    }

    /**
     * 测试消息统计
     */
    private void testMessageStatistics(String apiPrefix, int userId) throws Exception {
        String queryParams = "?customerId=1&startDate=2025-09-01&endDate=2025-09-10";
        sendRequest("GET", apiPrefix + "/statistics" + queryParams, null);
    }

    /**
     * 发送HTTP请求并记录性能指标
     */
    private void sendRequest(String method, String endpoint, Object requestBody) throws Exception {
        long requestStart = System.nanoTime();
        totalRequests.incrementAndGet();
        
        try {
            HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                    .uri(URI.create(BASE_URL + endpoint))
                    .timeout(REQUEST_TIMEOUT)
                    .header("Content-Type", "application/json");
            
            if ("POST".equals(method) || "PUT".equals(method)) {
                String jsonBody = requestBody != null ? objectMapper.writeValueAsString(requestBody) : "{}";
                requestBuilder.method(method, HttpRequest.BodyPublishers.ofString(jsonBody));
            } else {
                requestBuilder.GET();
            }
            
            HttpRequest request = requestBuilder.build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            // 记录响应时间
            long responseTime = (System.nanoTime() - requestStart) / 1_000_000; // 转换为毫秒
            responseTimes.add(responseTime);
            
            // 记录成功/失败
            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                successRequests.incrementAndGet();
            } else {
                failedRequests.incrementAndGet();
                errorCodes.computeIfAbsent(String.valueOf(response.statusCode()), k -> new AtomicInteger()).incrementAndGet();
                log.warn("请求失败: {} {}, 状态码: {}, 响应: {}", method, endpoint, response.statusCode(), response.body());
            }
            
        } catch (Exception e) {
            failedRequests.incrementAndGet();
            errorCodes.computeIfAbsent("EXCEPTION", k -> new AtomicInteger()).incrementAndGet();
            
            long responseTime = (System.nanoTime() - requestStart) / 1_000_000;
            responseTimes.add(responseTime); // 即使失败也记录响应时间
            
            throw e;
        }
    }

    /**
     * 构建性能测试结果
     */
    private PerformanceResult buildPerformanceResult(String version, long totalTimeMs) {
        // 计算统计指标
        List<Long> sortedTimes = responseTimes.stream().sorted().collect(Collectors.toList());
        
        double avgResponseTime = responseTimes.stream().mapToLong(Long::longValue).average().orElse(0.0);
        long minResponseTime = sortedTimes.isEmpty() ? 0 : sortedTimes.get(0);
        long maxResponseTime = sortedTimes.isEmpty() ? 0 : sortedTimes.get(sortedTimes.size() - 1);
        long p95ResponseTime = sortedTimes.isEmpty() ? 0 : sortedTimes.get((int) (sortedTimes.size() * 0.95));
        long p99ResponseTime = sortedTimes.isEmpty() ? 0 : sortedTimes.get((int) (sortedTimes.size() * 0.99));
        
        double tps = totalRequests.get() * 1000.0 / totalTimeMs;
        double successRate = totalRequests.get() > 0 ? (successRequests.get() * 100.0 / totalRequests.get()) : 0.0;
        
        return PerformanceResult.builder()
                .version(version)
                .totalRequests(totalRequests.get())
                .successRequests(successRequests.get())
                .failedRequests(failedRequests.get())
                .totalTimeMs(totalTimeMs)
                .tps(tps)
                .successRate(successRate)
                .avgResponseTime(avgResponseTime)
                .minResponseTime(minResponseTime)
                .maxResponseTime(maxResponseTime)
                .p95ResponseTime(p95ResponseTime)
                .p99ResponseTime(p99ResponseTime)
                .errorCodes(new HashMap<>(errorCodes))
                .testTime(LocalDateTime.now())
                .build();
    }

    /**
     * 生成性能对比报告
     */
    private void generatePerformanceReport(PerformanceResult v1Result, PerformanceResult v2Result) {
        StringBuilder report = new StringBuilder();
        
        report.append("\n");
        report.append("═══════════════════════════════════════════════════════════════════\n");
        report.append("                   LJWX消息系统性能对比报告                        \n");
        report.append("═══════════════════════════════════════════════════════════════════\n");
        report.append("测试时间: ").append(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss").format(LocalDateTime.now())).append("\n");
        report.append("并发用户: ").append(CONCURRENT_USERS).append(" 用户\n");
        report.append("总请求数: ").append(CONCURRENT_USERS * REQUESTS_PER_USER).append(" 请求\n");
        report.append("───────────────────────────────────────────────────────────────────\n");
        report.append("\n");
        
        // V1 系统结果
        report.append("📊 V1系统性能指标:\n");
        appendPerformanceMetrics(report, v1Result);
        
        report.append("\n📊 V2系统性能指标:\n");
        appendPerformanceMetrics(report, v2Result);
        
        // 性能提升对比
        report.append("\n🚀 性能提升对比:\n");
        appendPerformanceComparison(report, v1Result, v2Result);
        
        // 错误分析
        report.append("\n❌ 错误统计:\n");
        appendErrorAnalysis(report, v1Result, v2Result);
        
        report.append("\n═══════════════════════════════════════════════════════════════════\n");
        
        log.info(report.toString());
        
        // 保存报告到文件
        saveReportToFile(report.toString());
    }

    /**
     * 追加性能指标到报告
     */
    private void appendPerformanceMetrics(StringBuilder report, PerformanceResult result) {
        report.append(String.format("   TPS:           %.2f 请求/秒\n", result.getTps()));
        report.append(String.format("   成功率:        %.2f%%\n", result.getSuccessRate()));
        report.append(String.format("   平均响应时间:  %.2f ms\n", result.getAvgResponseTime()));
        report.append(String.format("   P95响应时间:   %d ms\n", result.getP95ResponseTime()));
        report.append(String.format("   P99响应时间:   %d ms\n", result.getP99ResponseTime()));
        report.append(String.format("   最大响应时间:  %d ms\n", result.getMaxResponseTime()));
        report.append(String.format("   总执行时间:    %.2f 秒\n", result.getTotalTimeMs() / 1000.0));
    }

    /**
     * 追加性能提升对比
     */
    private void appendPerformanceComparison(StringBuilder report, PerformanceResult v1Result, PerformanceResult v2Result) {
        double tpsImprovement = calculateImprovement(v1Result.getTps(), v2Result.getTps());
        double responseTimeImprovement = calculateImprovement(v1Result.getAvgResponseTime(), v2Result.getAvgResponseTime(), true);
        double p95Improvement = calculateImprovement(v1Result.getP95ResponseTime(), v2Result.getP95ResponseTime(), true);
        
        report.append(String.format("   TPS提升:       %.1f%% (%.2f → %.2f)\n", 
                tpsImprovement, v1Result.getTps(), v2Result.getTps()));
        report.append(String.format("   响应时间优化:  %.1f%% (%.2f ms → %.2f ms)\n", 
                responseTimeImprovement, v1Result.getAvgResponseTime(), v2Result.getAvgResponseTime()));
        report.append(String.format("   P95延迟优化:   %.1f%% (%d ms → %d ms)\n", 
                p95Improvement, v1Result.getP95ResponseTime(), v2Result.getP95ResponseTime()));
        
        // 整体性能评级
        double overallImprovement = (tpsImprovement + responseTimeImprovement + p95Improvement) / 3.0;
        String performanceGrade = getPerformanceGrade(overallImprovement);
        report.append(String.format("   整体性能提升:  %.1f%% (%s)\n", overallImprovement, performanceGrade));
    }

    /**
     * 追加错误分析
     */
    private void appendErrorAnalysis(StringBuilder report, PerformanceResult v1Result, PerformanceResult v2Result) {
        report.append("   V1系统错误: ");
        if (v1Result.getErrorCodes().isEmpty()) {
            report.append("无错误\n");
        } else {
            report.append("\n");
            v1Result.getErrorCodes().forEach((code, count) -> 
                    report.append(String.format("      %s: %d 次\n", code, count.get())));
        }
        
        report.append("   V2系统错误: ");
        if (v2Result.getErrorCodes().isEmpty()) {
            report.append("无错误\n");
        } else {
            report.append("\n");
            v2Result.getErrorCodes().forEach((code, count) -> 
                    report.append(String.format("      %s: %d 次\n", code, count.get())));
        }
    }

    /**
     * 数据库性能测试
     */
    private void databasePerformanceTest() throws Exception {
        log.info("🗃️ 开始数据库性能测试...");
        
        // 测试场景：大批量插入
        testBulkInsert();
        
        // 测试场景：复杂查询
        testComplexQueries();
        
        // 测试场景：并发读写
        testConcurrentReadWrite();
        
        log.info("✅ 数据库性能测试完成");
    }

    /**
     * 测试大批量插入
     */
    private void testBulkInsert() throws Exception {
        log.info("测试批量插入性能 (1000条记录)...");
        
        List<Map<String, Object>> batchData = IntStream.range(0, 1000)
                .mapToObj(i -> Map.of(
                        "deviceSn", "BULK_TEST_" + i,
                        "title", "批量插入测试 " + i,
                        "message", "批量插入测试内容 " + i,
                        "messageType", "notification",
                        "senderType", "system",
                        "receiverType", "device",
                        "customerId", 1
                ))
                .collect(Collectors.toList());
        
        long startTime = System.currentTimeMillis();
        sendRequest("POST", V2_API_PREFIX + "/bulk", batchData);
        long endTime = System.currentTimeMillis();
        
        log.info("批量插入完成: {} ms, TPS: {}", (endTime - startTime), 1000.0 * 1000 / (endTime - startTime));
    }

    /**
     * 测试复杂查询
     */
    private void testComplexQueries() throws Exception {
        log.info("测试复杂查询性能...");
        
        String[] complexQueries = {
                "?customerId=1&messageType=notification&messageStatus=pending&startDate=2025-09-01&endDate=2025-09-10",
                "?deviceSn=TEST_DEVICE_1&urgency=high&priority=5",
                "?orgId=1&senderType=system&receiverType=device&requireAck=true"
        };
        
        for (String query : complexQueries) {
            long startTime = System.currentTimeMillis();
            sendRequest("GET", V2_API_PREFIX + query, null);
            long endTime = System.currentTimeMillis();
            log.info("复杂查询完成: {} ms", (endTime - startTime));
        }
    }

    /**
     * 测试并发读写
     */
    private void testConcurrentReadWrite() throws Exception {
        log.info("测试并发读写性能...");
        
        List<CompletableFuture<Void>> tasks = new ArrayList<>();
        
        // 并发写操作
        for (int i = 0; i < 20; i++) {
            final int index = i;
            tasks.add(CompletableFuture.runAsync(() -> {
                try {
                    testCreateMessage(V2_API_PREFIX, index);
                } catch (Exception e) {
                    log.error("并发写测试失败", e);
                }
            }, executorService));
        }
        
        // 并发读操作
        for (int i = 0; i < 30; i++) {
            final int index = i;
            tasks.add(CompletableFuture.runAsync(() -> {
                try {
                    testQueryMessages(V2_API_PREFIX, index);
                } catch (Exception e) {
                    log.error("并发读测试失败", e);
                }
            }, executorService));
        }
        
        CompletableFuture.allOf(tasks.toArray(new CompletableFuture[0])).get();
        log.info("并发读写测试完成");
    }

    /**
     * 压力测试
     */
    private void stressTest() throws Exception {
        log.info("🔥 开始压力测试 (持续5分钟)...");
        
        long testDuration = 5 * 60 * 1000; // 5分钟
        long startTime = System.currentTimeMillis();
        AtomicInteger stressRequests = new AtomicInteger();
        
        List<CompletableFuture<Void>> stressTasks = IntStream.range(0, 20)
                .mapToObj(i -> CompletableFuture.runAsync(() -> {
                    Random random = new Random();
                    while (System.currentTimeMillis() - startTime < testDuration) {
                        try {
                            testCreateMessage(V2_API_PREFIX, random.nextInt(1000));
                            stressRequests.incrementAndGet();
                            Thread.sleep(100); // 控制请求频率
                        } catch (Exception e) {
                            // 压力测试中忽略个别错误
                        }
                    }
                }, executorService))
                .collect(Collectors.toList());
        
        CompletableFuture.allOf(stressTasks.toArray(new CompletableFuture[0])).get();
        
        long actualDuration = System.currentTimeMillis() - startTime;
        double avgTps = stressRequests.get() * 1000.0 / actualDuration;
        
        log.info("压力测试完成: 总请求 {}, 平均TPS {:.2f}", stressRequests.get(), avgTps);
    }

    /**
     * 重置计数器
     */
    private void resetCounters() {
        totalRequests.set(0);
        successRequests.set(0);
        failedRequests.set(0);
        responseTimes.clear();
        errorCodes.clear();
    }

    /**
     * 计算性能提升百分比
     */
    private double calculateImprovement(double oldValue, double newValue) {
        return calculateImprovement(oldValue, newValue, false);
    }

    private double calculateImprovement(double oldValue, double newValue, boolean lowerIsBetter) {
        if (oldValue == 0) return 0.0;
        
        double improvement = lowerIsBetter ? 
                (oldValue - newValue) / oldValue * 100 : 
                (newValue - oldValue) / oldValue * 100;
        
        return Math.round(improvement * 10) / 10.0;
    }

    /**
     * 获取性能等级
     */
    private String getPerformanceGrade(double improvement) {
        if (improvement >= 50) return "🏆 卓越";
        if (improvement >= 30) return "🥇 优秀";
        if (improvement >= 15) return "🥈 良好";
        if (improvement >= 5) return "🥉 一般";
        return "❌ 需改进";
    }

    /**
     * 保存报告到文件
     */
    private void saveReportToFile(String report) {
        try {
            String fileName = "message-performance-report-" + 
                    DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss").format(LocalDateTime.now()) + ".txt";
            
            java.nio.file.Files.write(
                    java.nio.file.Paths.get(fileName), 
                    report.getBytes(),
                    java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.WRITE
            );
            
            log.info("📝 性能报告已保存到文件: {}", fileName);
        } catch (IOException e) {
            log.error("保存性能报告失败", e);
        }
    }

    /**
     * 性能测试结果数据结构
     */
    @Data
    @Builder
    public static class PerformanceResult {
        private String version;
        private long totalRequests;
        private long successRequests; 
        private long failedRequests;
        private long totalTimeMs;
        private double tps;
        private double successRate;
        private double avgResponseTime;
        private long minResponseTime;
        private long maxResponseTime;
        private long p95ResponseTime;
        private long p99ResponseTime;
        private Map<String, AtomicInteger> errorCodes;
        private LocalDateTime testTime;
    }
}