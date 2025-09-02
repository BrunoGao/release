package com.ljwx.test.data;

import lombok.extern.slf4j.Slf4j;
import org.testng.annotations.Test;

/**
 * 测试数据清理测试类
 * 用于单独执行测试数据清理操作
 */
@Slf4j
public class TestDataCleanupTest {
    
    @Test(description = "清理所有测试数据")
    public void cleanupAllTestData() throws Exception {
        log.info("开始执行测试数据清理...");
        
        TestDataManager dataManager = new TestDataManager();
        try {
            dataManager.cleanupTestData();
            log.info("✅ 测试数据清理完成");
            
        } catch (Exception e) {
            log.error("❌ 测试数据清理失败", e);
            throw new RuntimeException("测试数据清理失败", e);
        }
    }
}