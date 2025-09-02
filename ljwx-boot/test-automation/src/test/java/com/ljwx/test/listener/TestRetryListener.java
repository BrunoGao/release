package com.ljwx.test.listener;

import lombok.extern.slf4j.Slf4j;
import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

/**
 * 测试重试监听器
 * 为不稳定的网络测试提供重试机制
 */
@Slf4j
public class TestRetryListener implements IRetryAnalyzer {
    
    private static final int MAX_RETRY_COUNT = 2;
    private int currentRetryCount = 0;
    
    @Override
    public boolean retry(ITestResult result) {
        if (currentRetryCount < MAX_RETRY_COUNT) {
            currentRetryCount++;
            
            log.warn("🔄 测试重试 {}/{}: {} - {}", 
                currentRetryCount, 
                MAX_RETRY_COUNT,
                result.getTestClass().getName(),
                result.getMethod().getMethodName());
                
            if (result.getThrowable() != null) {
                log.warn("重试原因: {}", result.getThrowable().getMessage());
            }
            
            // 添加重试间隔
            try {
                Thread.sleep(1000 * currentRetryCount); // 递增等待时间
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                log.warn("重试等待被中断");
            }
            
            return true;
        }
        
        log.error("❌ 测试最终失败，已达到最大重试次数: {} - {}", 
            result.getTestClass().getName(),
            result.getMethod().getMethodName());
            
        return false;
    }
    
    /**
     * 重置重试计数器
     */
    public void resetRetryCount() {
        this.currentRetryCount = 0;
    }
}