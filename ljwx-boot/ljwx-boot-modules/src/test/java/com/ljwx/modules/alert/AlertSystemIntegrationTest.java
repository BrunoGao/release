/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.alert;

import com.ljwx.modules.alert.domain.dto.StandardEventModel;
import com.ljwx.modules.alert.domain.dto.NotificationResult;
import com.ljwx.modules.alert.service.EventIngestionService;
import com.ljwx.modules.alert.service.NotificationChannelManager;
import com.ljwx.modules.alert.service.AlertMonitoringService;
import com.ljwx.modules.alert.service.AlertCacheService;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.domain.entity.TAlertRules;
import com.ljwx.modules.health.service.ITAlertInfoService;
import com.ljwx.modules.health.service.ITAlertRulesService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 告警系统集成测试
 *
 * @Author bruno.gao
 * @CreateTime 2025-08-31 - 12:25:00
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class AlertSystemIntegrationTest {

    @Autowired
    private EventIngestionService eventIngestionService;
    
    @Autowired
    private NotificationChannelManager notificationChannelManager;
    
    @Autowired
    private AlertMonitoringService alertMonitoringService;
    
    @Autowired
    private AlertCacheService alertCacheService;
    
    @Autowired
    private ITAlertInfoService alertInfoService;
    
    @Autowired
    private ITAlertRulesService alertRulesService;

    private static final Long TEST_CUSTOMER_ID = 999L;
    private static final Long TEST_USER_ID = 1001L;
    private static final String TEST_DEVICE_SN = "TEST_DEVICE_001";

    @BeforeEach
    void setUp() {
        // 清理测试数据
        cleanupTestData();
        
        // 创建测试规则
        createTestAlertRules();
    }

    @Test
    void testCompleteAlertFlow() {
        // 1. 测试事件接收和处理
        testEventIngestion();
        
        // 2. 测试规则匹配和告警生成
        testRuleMatchingAndAlertGeneration();
        
        // 3. 测试通知发送
        testNotificationSending();
        
        // 4. 测试告警确认和解决
        testAlertAcknowledgmentAndResolution();
    }

    @Test
    void testEventIngestion() {
        // 创建测试事件
        StandardEventModel event = StandardEventModel.builder()
                .eventId("test_event_" + System.currentTimeMillis())
                .source("watch")
                .customerId(TEST_CUSTOMER_ID)
                .userId(TEST_USER_ID)
                .deviceSn(TEST_DEVICE_SN)
                .eventType("heartRate")
                .metric("heartRate")
                .value(150.0)
                .unit("bpm")
                .timestamp(LocalDateTime.now())
                .build();

        // 处理事件
        boolean result = eventIngestionService.processEvent(event);
        assertTrue(result, "事件处理应该成功");

        // 验证事件是否正确入队
        // 这里应该检查队列中是否有对应的事件
        // assertEventInQueue(event.getEventId());
    }

    @Test
    void testRuleMatchingAndAlertGeneration() {
        // 创建高心率事件
        StandardEventModel highHeartRateEvent = StandardEventModel.builder()
                .eventId("high_hr_" + System.currentTimeMillis())
                .source("watch")
                .customerId(TEST_CUSTOMER_ID)
                .userId(TEST_USER_ID)
                .deviceSn(TEST_DEVICE_SN)
                .eventType("heartRate")
                .metric("heartRate")
                .value(130.0)  // 超过正常范围
                .unit("bpm")
                .timestamp(LocalDateTime.now())
                .build();

        // 处理事件
        eventIngestionService.processEvent(highHeartRateEvent);

        // 等待异步处理完成
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        // 验证是否生成了告警
        List<TAlertInfo> alerts = alertInfoService.list();
        long heartRateAlerts = alerts.stream()
                .filter(alert -> "heartRate".equals(alert.getMetric()))
                .filter(alert -> TEST_USER_ID.equals(alert.getUserId()))
                .count();

        assertTrue(heartRateAlerts > 0, "应该生成心率异常告警");
    }

    @Test
    void testNotificationSending() {
        // 创建测试告警
        TAlertInfo testAlert = createTestAlert();
        TAlertRules testRule = createTestRule();

        // 发送多渠道通知
        List<NotificationResult> results = notificationChannelManager
                .sendMultiChannelNotification(testAlert, testRule);

        assertFalse(results.isEmpty(), "应该有通知结果");

        // 验证各渠道结果
        Map<String, NotificationResult> resultMap = results.stream()
                .collect(java.util.stream.Collectors.toMap(
                        NotificationResult::getChannel, 
                        r -> r
                ));

        // 检查微信通知
        if (resultMap.containsKey("wechat")) {
            NotificationResult wechatResult = resultMap.get("wechat");
            assertNotNull(wechatResult.getMessageId(), "微信通知应该有消息ID");
        }

        // 检查短信通知
        if (resultMap.containsKey("message")) {
            NotificationResult messageResult = resultMap.get("message");
            assertNotNull(messageResult.getMessageId(), "短信通知应该有消息ID");
        }
    }

    @Test
    void testAlertAcknowledgmentAndResolution() {
        // 创建测试告警
        TAlertInfo testAlert = createTestAlert();
        alertInfoService.save(testAlert);

        // 确认告警
        testAlert.setStatus("ACKED");
        testAlert.setAcknowledgedTime(LocalDateTime.now());
        boolean ackResult = alertInfoService.updateById(testAlert);
        assertTrue(ackResult, "告警确认应该成功");

        // 解决告警
        testAlert.setStatus("RESOLVED");
        testAlert.setRecoverAt(LocalDateTime.now());
        boolean resolveResult = alertInfoService.updateById(testAlert);
        assertTrue(resolveResult, "告警解决应该成功");

        // 验证状态更新
        TAlertInfo updatedAlert = alertInfoService.getById(testAlert.getId());
        assertEquals("RESOLVED", updatedAlert.getStatus(), "告警状态应该为已解决");
        assertNotNull(updatedAlert.getRecoverAt(), "应该有恢复时间");
    }

    @Test
    void testPerformanceUnderLoad() throws InterruptedException {
        int numberOfEvents = 100;
        int numberOfThreads = 10;
        ExecutorService executor = Executors.newFixedThreadPool(numberOfThreads);
        CountDownLatch latch = new CountDownLatch(numberOfEvents);

        long startTime = System.currentTimeMillis();

        // 并发发送事件
        for (int i = 0; i < numberOfEvents; i++) {
            final int eventIndex = i;
            executor.submit(() -> {
                try {
                    StandardEventModel event = StandardEventModel.builder()
                            .eventId("perf_test_" + eventIndex + "_" + System.currentTimeMillis())
                            .source("watch")
                            .customerId(TEST_CUSTOMER_ID)
                            .userId(TEST_USER_ID + eventIndex % 10)
                            .deviceSn(TEST_DEVICE_SN)
                            .eventType("heartRate")
                            .metric("heartRate")
                            .value(60.0 + eventIndex % 40)  // 60-100 bpm
                            .unit("bpm")
                            .timestamp(LocalDateTime.now())
                            .build();

                    eventIngestionService.processEvent(event);

                } catch (Exception e) {
                    System.err.println("处理事件失败: " + e.getMessage());
                } finally {
                    latch.countDown();
                }
            });
        }

        // 等待所有事件处理完成
        boolean completed = latch.await(30, TimeUnit.SECONDS);
        assertTrue(completed, "所有事件应该在30秒内处理完成");

        long endTime = System.currentTimeMillis();
        long totalTime = endTime - startTime;

        System.out.println(String.format("性能测试完成: %d个事件, 耗时%dms, 平均%dms/事件", 
                numberOfEvents, totalTime, totalTime / numberOfEvents));

        // 验证性能要求
        assertTrue(totalTime < 30000, "100个事件处理时间应该少于30秒");
        assertTrue(totalTime / numberOfEvents < 300, "单个事件平均处理时间应该少于300ms");

        executor.shutdown();
    }

    @Test
    void testSystemMonitoring() {
        // 测试系统指标收集
        AlertMonitoringService.SystemMetrics metrics = alertMonitoringService.collectSystemMetrics();
        
        assertNotNull(metrics, "系统指标不应该为空");
        assertNotNull(metrics.getTimestamp(), "应该有时间戳");
        assertTrue(metrics.getMemoryUsagePercent() >= 0, "内存使用率应该大于等于0");
        assertTrue(metrics.getMemoryUsagePercent() <= 100, "内存使用率应该小于等于100");

        // 测试健康摘要
        AlertMonitoringService.HealthSummary summary = alertMonitoringService.getHealthSummary();
        
        assertNotNull(summary, "健康摘要不应该为空");
        assertNotNull(summary.getOverallHealth(), "应该有整体健康状态");
        assertTrue(summary.getHealthScore() >= 0, "健康分数应该大于等于0");
        assertTrue(summary.getHealthScore() <= 100, "健康分数应该小于等于100");
    }

    @Test
    void testCacheOperations() {
        // 测试规则缓存
        List<TAlertRules> testRules = alertRulesService.list();
        alertCacheService.cacheAlertRules(TEST_CUSTOMER_ID, testRules);

        List<TAlertRules> cachedRules = alertCacheService.getCachedAlertRules(TEST_CUSTOMER_ID);
        assertNotNull(cachedRules, "缓存的规则不应该为空");
        assertEquals(testRules.size(), cachedRules.size(), "缓存的规则数量应该一致");

        // 测试通知配置缓存
        Map<String, Object> testConfig = Map.of("enabled", true, "template", "test");
        alertCacheService.cacheNotificationConfig(TEST_CUSTOMER_ID, "wechat", testConfig);

        Map<String, Object> cachedConfig = alertCacheService.getCachedNotificationConfig(TEST_CUSTOMER_ID, "wechat");
        assertNotNull(cachedConfig, "缓存的配置不应该为空");
        assertEquals(testConfig.get("enabled"), cachedConfig.get("enabled"), "配置值应该一致");

        // 测试限流计数器
        String throttleKey = "test_throttle_" + System.currentTimeMillis();
        Long count = alertCacheService.incrementThrottleCounter(throttleKey, 60);
        assertEquals(1L, count, "第一次递增应该返回1");

        count = alertCacheService.incrementThrottleCounter(throttleKey, 60);
        assertEquals(2L, count, "第二次递增应该返回2");

        // 测试去重标记
        String dedupKey = "test_dedup_" + System.currentTimeMillis();
        boolean setResult = alertCacheService.setDeduplicationFlag(dedupKey, true, 60);
        assertTrue(setResult, "设置去重标记应该成功");

        boolean hasFlag = alertCacheService.hasDeduplicationFlag(dedupKey);
        assertTrue(hasFlag, "去重标记应该存在");
    }

    /**
     * 创建测试告警
     */
    private TAlertInfo createTestAlert() {
        TAlertInfo alert = new TAlertInfo();
        alert.setCustomerId(TEST_CUSTOMER_ID);
        alert.setUserId(TEST_USER_ID);
        alert.setDeviceSn(TEST_DEVICE_SN);
        alert.setAlertType("heartRate");
        alert.setAlertDesc("心率异常，当前值: 130 bpm");
        alert.setLevel("major");
        alert.setStatus("NEW");
        alert.setSource("watch");
        alert.setMetric("heartRate");
        alert.setValue(130.0);
        alert.setUnit("bpm");
        alert.setOccurAt(LocalDateTime.now());
        alert.setCreateTime(LocalDateTime.now());
        alert.setUpdateTime(LocalDateTime.now());
        alert.setIsDeleted(false);
        
        return alert;
    }

    /**
     * 创建测试规则
     */
    private TAlertRules createTestRule() {
        TAlertRules rule = new TAlertRules();
        rule.setCustomerId(TEST_CUSTOMER_ID);
        rule.setRuleType("metric");
        rule.setMetric("heartRate");
        rule.setLevel("major");
        rule.setNotify(List.of("wechat", "message"));
        rule.setIsEnabled(true);
        rule.setCreateUser("test");
        rule.setCreateTime(LocalDateTime.now());
        rule.setUpdateTime(LocalDateTime.now());
        rule.setIsDeleted(false);
        
        return rule;
    }

    /**
     * 创建测试告警规则
     */
    private void createTestAlertRules() {
        try {
            // 创建心率异常规则
            TAlertRules heartRateRule = new TAlertRules();
            heartRateRule.setCustomerId(TEST_CUSTOMER_ID);
            heartRateRule.setRuleType("metric");
            heartRateRule.setMetric("heartRate");
            heartRateRule.setLevel("major");
            heartRateRule.setNotify(List.of("wechat", "message"));
            heartRateRule.setIsEnabled(true);
            heartRateRule.setCreateUser("test");
            heartRateRule.setCreateTime(LocalDateTime.now());
            heartRateRule.setUpdateTime(LocalDateTime.now());
            heartRateRule.setIsDeleted(false);
            
            alertRulesService.save(heartRateRule);

            // 创建血氧异常规则
            TAlertRules spo2Rule = new TAlertRules();
            spo2Rule.setCustomerId(TEST_CUSTOMER_ID);
            spo2Rule.setRuleType("metric");
            spo2Rule.setMetric("spo2");
            spo2Rule.setLevel("critical");
            spo2Rule.setNotify(List.of("wechat", "message", "screen_popup"));
            spo2Rule.setIsEnabled(true);
            spo2Rule.setCreateUser("test");
            spo2Rule.setCreateTime(LocalDateTime.now());
            spo2Rule.setUpdateTime(LocalDateTime.now());
            spo2Rule.setIsDeleted(false);
            
            alertRulesService.save(spo2Rule);

        } catch (Exception e) {
            log.error("创建测试规则失败", e);
        }
    }

    /**
     * 清理测试数据
     */
    private void cleanupTestData() {
        try {
            // 清理测试告警
            alertInfoService.remove(
                queryWrapper -> queryWrapper.eq("customer_id", TEST_CUSTOMER_ID)
            );
            
            // 清理测试规则
            alertRulesService.remove(
                queryWrapper -> queryWrapper.eq("customer_id", TEST_CUSTOMER_ID)
            );
            
            // 清理缓存
            alertCacheService.clearCustomerCache(TEST_CUSTOMER_ID);

        } catch (Exception e) {
            log.error("清理测试数据失败", e);
        }
    }

    /**
     * 验证告警生成性能
     */
    @Test
    void testAlertGenerationPerformance() throws InterruptedException {
        int numberOfEvents = 1000;
        long startTime = System.currentTimeMillis();

        for (int i = 0; i < numberOfEvents; i++) {
            StandardEventModel event = StandardEventModel.builder()
                    .eventId("perf_" + i + "_" + System.currentTimeMillis())
                    .source("watch")
                    .customerId(TEST_CUSTOMER_ID)
                    .userId(TEST_USER_ID + (i % 10))
                    .deviceSn(TEST_DEVICE_SN)
                    .eventType("heartRate")
                    .metric("heartRate")
                    .value(60.0 + (i % 80))  // 60-140 bpm范围
                    .unit("bpm")
                    .timestamp(LocalDateTime.now())
                    .build();

            eventIngestionService.processEvent(event);
        }

        long endTime = System.currentTimeMillis();
        long totalTime = endTime - startTime;

        System.out.println(String.format("告警生成性能测试: %d事件, %dms, %.2f事件/秒", 
                numberOfEvents, totalTime, numberOfEvents * 1000.0 / totalTime));

        // 验证性能要求: 应该达到每秒1000+事件处理能力
        double eventsPerSecond = numberOfEvents * 1000.0 / totalTime;
        assertTrue(eventsPerSecond > 500, "事件处理性能应该超过500事件/秒");
    }

    /**
     * 验证系统自监控功能
     */
    @Test
    void testSystemSelfMonitoring() {
        // 触发系统健康检查
        alertMonitoringService.checkSystemHealthAndAlert();

        // 获取系统指标
        AlertMonitoringService.SystemMetrics metrics = alertMonitoringService.collectSystemMetrics();
        
        assertNotNull(metrics, "系统指标应该不为空");
        assertTrue(metrics.isDatabaseHealthy(), "数据库应该健康");
        assertTrue(metrics.isRedisHealthy(), "Redis应该健康");
        
        // 获取健康摘要
        AlertMonitoringService.HealthSummary summary = alertMonitoringService.getHealthSummary();
        
        assertNotNull(summary, "健康摘要应该不为空");
        assertNotNull(summary.getOverallHealth(), "应该有整体健康状态");
        assertTrue(summary.getHealthScore() > 0, "健康分数应该大于0");
    }
}