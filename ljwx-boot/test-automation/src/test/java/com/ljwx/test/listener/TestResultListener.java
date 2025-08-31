package com.ljwx.test.listener;

import lombok.extern.slf4j.Slf4j;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 测试结果监听器
 * 提供详细的测试执行日志和报告
 */
@Slf4j
public class TestResultListener implements ITestListener {
    
    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private int totalTests = 0;
    private int passedTests = 0;
    private int failedTests = 0;
    private int skippedTests = 0;
    
    @Override
    public void onTestStart(ITestResult result) {
        totalTests++;
        log.info("🚀 开始执行测试: {} - {}", 
            result.getTestClass().getName(), 
            result.getMethod().getMethodName());
    }
    
    @Override
    public void onTestSuccess(ITestResult result) {
        passedTests++;
        long duration = result.getEndMillis() - result.getStartMillis();
        log.info("✅ 测试通过: {} - {} (耗时: {}ms)", 
            result.getTestClass().getName(),
            result.getMethod().getMethodName(),
            duration);
    }
    
    @Override
    public void onTestFailure(ITestResult result) {
        failedTests++;
        long duration = result.getEndMillis() - result.getStartMillis();
        log.error("❌ 测试失败: {} - {} (耗时: {}ms)", 
            result.getTestClass().getName(),
            result.getMethod().getMethodName(),
            duration);
        
        // 记录失败详情
        if (result.getThrowable() != null) {
            log.error("失败原因: {}", result.getThrowable().getMessage());
            log.debug("失败堆栈:", result.getThrowable());
        }
    }
    
    @Override
    public void onTestSkipped(ITestResult result) {
        skippedTests++;
        log.warn("⏭️ 测试跳过: {} - {}", 
            result.getTestClass().getName(),
            result.getMethod().getMethodName());
        
        if (result.getThrowable() != null) {
            log.warn("跳过原因: {}", result.getThrowable().getMessage());
        }
    }
    
    /**
     * 生成测试摘要报告
     */
    public void generateSummaryReport() {
        log.info("\n" +
            "========================================\n" +
            "           测试执行摘要报告              \n" +
            "========================================\n" +
            "执行时间: {}\n" +
            "总测试数: {}\n" +
            "通过数量: {} ({}%)\n" +
            "失败数量: {} ({}%)\n" +
            "跳过数量: {} ({}%)\n" +
            "========================================",
            LocalDateTime.now().format(FORMATTER),
            totalTests,
            passedTests, calculatePercentage(passedTests, totalTests),
            failedTests, calculatePercentage(failedTests, totalTests),
            skippedTests, calculatePercentage(skippedTests, totalTests)
        );
    }
    
    private double calculatePercentage(int count, int total) {
        return total > 0 ? (double) count / total * 100 : 0;
    }
    
    public TestSummary getTestSummary() {
        return new TestSummary(totalTests, passedTests, failedTests, skippedTests);
    }
    
    /**
     * 测试摘要数据类
     */
    public static class TestSummary {
        public final int total;
        public final int passed;
        public final int failed;
        public final int skipped;
        public final double passRate;
        
        public TestSummary(int total, int passed, int failed, int skipped) {
            this.total = total;
            this.passed = passed;
            this.failed = failed;
            this.skipped = skipped;
            this.passRate = total > 0 ? (double) passed / total * 100 : 0;
        }
        
        @Override
        public String toString() {
            return String.format("总数:%d, 通过:%d, 失败:%d, 跳过:%d, 通过率:%.1f%%",
                total, passed, failed, skipped, passRate);
        }
    }
}