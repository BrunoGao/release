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

package com.ljwx.modules.health.integration;

import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import com.ljwx.modules.health.service.UnifiedMessagePublisher;
import com.ljwx.common.util.RedisUtil;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/**
 * V2消息系统集成测试
 * 验证完整的V2消息处理流程，包括数据库操作、Redis集成、跨平台兼容性
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName MessageV2IntegrationTest
 * @CreateTime 2025-09-10
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
@Slf4j
public class MessageIntegrationTest {
    
    @Autowired
    private ITDeviceMessageService messageService;
    
    @Autowired
    private UnifiedMessagePublisher messagePublisher;
    
    @Autowired
    private RedisUtil redisUtil;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    private TDeviceMessage testMessage;
    private TDeviceMessageDetail testDetail;
    
    @BeforeEach
    void setUp() {
        log.info("开始V2消息系统集成测试初始化");
        
        // 创建测试消息
        testMessage = createTestMessage();
        testDetail = createTestMessageDetail(testMessage.getId());
        
        // 清理Redis测试数据
        clearRedisTestData();
        
        log.info("V2消息系统集成测试初始化完成: messageId={}", testMessage.getId());
    }
    
    @Test
    @DisplayName("完整V2消息处理流程测试")
    void testCompleteV2MessageFlow() throws Exception {
        log.info("开始完整V2消息处理流程测试");
        
        // 1. 保存V2消息到数据库
        TDeviceMessage savedMessage = messageService.save(testMessage);
        assertNotNull(savedMessage.getId());
        log.info("V2消息已保存到数据库: id={}", savedMessage.getId());
        
        // 2. 发布消息创建事件到Redis
        CompletableFuture<Boolean> publishResult = messagePublisher.publishMessageCreated(savedMessage);
        Boolean isPublished = publishResult.get(5, TimeUnit.SECONDS);
        assertTrue(isPublished);
        log.info("V2消息创建事件已发布到Redis");
        
        // 3. 验证Redis缓存
        Thread.sleep(100); // 等待异步操作完成
        String cacheKey = "ljwx:message:cache:" + savedMessage.getId();
        Object cachedMessage = redisUtil.get(cacheKey);
        assertNotNull(cachedMessage);
        log.info("V2消息缓存验证成功");
        
        // 4. 消息分发测试
        List<String> targetDevices = Arrays.asList("DEVICE_001", "DEVICE_002", "DEVICE_003");
        CompletableFuture<Boolean> distributionResult = messagePublisher.publishMessageDistributed(savedMessage, targetDevices);
        Boolean isDistributed = distributionResult.get(5, TimeUnit.SECONDS);
        assertTrue(isDistributed);
        log.info("V2消息分发事件测试完成: targets={}", targetDevices.size());
        
        // 5. 验证消息状态缓存
        Thread.sleep(100);
        String statusKey = "ljwx:message:status:" + savedMessage.getId();
        Object statusData = redisUtil.hGet(statusKey, "status");
        assertEquals("DISTRIBUTED", statusData);
        log.info("V2消息状态缓存验证成功: status={}", statusData);
        
        // 6. 设备队列操作测试
        String testDeviceSn = "TEST_DEVICE_001";
        CompletableFuture<Boolean> queueResult = messagePublisher.pushToDeviceQueue(testDeviceSn, savedMessage, 8);
        Boolean isQueued = queueResult.get(5, TimeUnit.SECONDS);
        assertTrue(isQueued);
        log.info("V2消息队列推送测试完成");
        
        // 7. 队列状态检查
        Map<String, Object> queueStatus = messagePublisher.getDeviceQueueStatus(testDeviceSn);
        assertNotNull(queueStatus);
        assertEquals(testDeviceSn, queueStatus.get("deviceSn"));
        assertTrue((Long) queueStatus.get("queueSize") > 0);
        log.info("V2设备队列状态检查完成: queueSize={}", queueStatus.get("queueSize"));
        
        // 8. 获取队列消息测试
        List<UnifiedMessagePublisher.V2QueuedMessage> queuedMessages = messagePublisher.getQueuedMessages(testDeviceSn, 10);
        assertFalse(queuedMessages.isEmpty());
        assertEquals(savedMessage.getId(), queuedMessages.get(0).getMessageId());
        log.info("V2队列消息获取测试完成: count={}", queuedMessages.size());
        
        // 9. 消息确认测试
        Map<String, Object> ackData = new HashMap<>();
        ackData.put("timestamp", System.currentTimeMillis());
        ackData.put("clientVersion", "2.0.1");
        
        CompletableFuture<Boolean> ackResult = messagePublisher.publishMessageAcknowledged(
            savedMessage.getId(), testDeviceSn, "READ", ackData);
        Boolean isAcknowledged = ackResult.get(5, TimeUnit.SECONDS);
        assertTrue(isAcknowledged);
        log.info("V2消息确认事件测试完成");
        
        // 10. 从队列移除消息
        boolean isRemoved = messagePublisher.removeFromQueue(testDeviceSn, savedMessage.getId());
        assertTrue(isRemoved);
        log.info("V2消息队列移除测试完成");
        
        // 11. 验证最终队列状态
        Map<String, Object> finalQueueStatus = messagePublisher.getDeviceQueueStatus(testDeviceSn);
        assertEquals(0L, finalQueueStatus.get("queueSize"));
        log.info("V2最终队列状态验证完成");
        
        log.info("完整V2消息处理流程测试成功完成！");
    }
    
    @Test
    @DisplayName("V2批量消息处理测试")
    void testV2BatchMessageProcessing() throws Exception {
        log.info("开始V2批量消息处理测试");
        
        // 1. 创建批量测试消息
        List<TDeviceMessage> batchMessages = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            TDeviceMessage message = createTestMessage();
            message.setDeviceSn("BATCH_DEVICE_" + String.format("%03d", i));
            message.setMessageContent("批量测试消息 " + i);
            TDeviceMessage saved = messageService.save(message);
            batchMessages.add(saved);
        }
        log.info("批量测试消息创建完成: count={}", batchMessages.size());
        
        // 2. 准备目标设备映射
        Map<Long, List<String>> targetMap = new HashMap<>();
        for (TDeviceMessage message : batchMessages) {
            List<String> targets = Arrays.asList("TARGET_" + message.getDeviceSn() + "_1", "TARGET_" + message.getDeviceSn() + "_2");
            targetMap.put(message.getId(), targets);
        }
        
        // 3. 批量分发测试
        CompletableFuture<Boolean> batchResult = messagePublisher.publishBatchMessageDistributed(batchMessages, targetMap);
        Boolean isBatchDistributed = batchResult.get(10, TimeUnit.SECONDS);
        assertTrue(isBatchDistributed);
        log.info("V2批量消息分发测试完成");
        
        // 4. 验证各消息状态
        Thread.sleep(200); // 等待异步操作完成
        for (TDeviceMessage message : batchMessages) {
            String statusKey = "ljwx:message:status:" + message.getId();
            Object batchStatus = redisUtil.hGet(statusKey, "status");
            assertEquals("BATCH_DISTRIBUTED", batchStatus);
        }
        log.info("V2批量消息状态验证完成");
        
        log.info("V2批量消息处理测试成功完成！");
    }
    
    @Test
    @DisplayName("V2消息系统性能测试")
    void testV2MessagePerformance() throws Exception {
        log.info("开始V2消息系统性能测试");
        
        int testMessageCount = 100;
        long startTime = System.currentTimeMillis();
        
        // 1. 批量创建和发布消息
        List<CompletableFuture<Boolean>> publishFutures = new ArrayList<>();
        
        for (int i = 1; i <= testMessageCount; i++) {
            TDeviceMessage message = createTestMessage();
            message.setDeviceSn("PERF_DEVICE_" + String.format("%03d", i));
            message.setMessageContent("性能测试消息 " + i);
            
            TDeviceMessage saved = messageService.save(message);
            CompletableFuture<Boolean> future = messagePublisher.publishMessageCreated(saved);
            publishFutures.add(future);
        }
        
        // 2. 等待所有发布完成
        CompletableFuture<Void> allPublished = CompletableFuture.allOf(publishFutures.toArray(new CompletableFuture[0]));
        allPublished.get(30, TimeUnit.SECONDS);
        
        long endTime = System.currentTimeMillis();
        long totalTime = endTime - startTime;
        
        // 3. 性能统计
        double messagesPerSecond = (double) testMessageCount / (totalTime / 1000.0);
        Map<String, Object> stats = messagePublisher.getMessageStats();
        
        log.info("V2消息系统性能测试结果:");
        log.info("- 测试消息数量: {}", testMessageCount);
        log.info("- 总耗时: {}ms", totalTime);
        log.info("- 每秒处理消息数: {:.2f}", messagesPerSecond);
        log.info("- 系统统计: {}", stats);
        
        // 4. 性能断言
        assertTrue(messagesPerSecond > 10, "V2消息系统应能处理每秒10条以上消息");
        assertTrue(totalTime < 30000, "100条消息处理时间应在30秒内完成");
        
        log.info("V2消息系统性能测试成功完成！");
    }
    
    @Test
    @DisplayName("V2消息错误处理和恢复测试")
    void testV2MessageErrorHandling() throws Exception {
        log.info("开始V2消息错误处理和恢复测试");
        
        // 1. 模拟Redis连接异常场景
        try {
            TDeviceMessage message = createTestMessage();
            message.setDeviceSn("ERROR_TEST_DEVICE");
            TDeviceMessage saved = messageService.save(message);
            
            // 模拟错误设备名称
            CompletableFuture<Boolean> result = messagePublisher.pushToDeviceQueue("", saved, 5);
            Boolean isQueued = result.get(5, TimeUnit.SECONDS);
            
            // 即使设备名称错误，系统也应该优雅处理
            log.info("错误场景处理结果: {}", isQueued);
            
        } catch (Exception e) {
            log.info("预期的错误处理: {}", e.getMessage());
        }
        
        // 2. 验证系统统计信息
        Map<String, Object> stats = messagePublisher.getMessageStats();
        assertNotNull(stats);
        log.info("错误处理后系统统计: {}", stats);
        
        // 3. 正常消息处理验证（系统恢复能力）
        TDeviceMessage normalMessage = createTestMessage();
        normalMessage.setDeviceSn("RECOVERY_TEST_DEVICE");
        TDeviceMessage savedNormal = messageService.save(normalMessage);
        
        CompletableFuture<Boolean> normalResult = messagePublisher.publishMessageCreated(savedNormal);
        Boolean isNormalPublished = normalResult.get(5, TimeUnit.SECONDS);
        assertTrue(isNormalPublished);
        
        log.info("V2消息错误处理和恢复测试成功完成！");
    }
    
    private TDeviceMessage createTestMessage() {
        TDeviceMessage message = new TDeviceMessage();
        message.setDeviceSn("TEST_DEVICE_" + System.currentTimeMillis());
        message.setUserId(1001L);
        message.setOrgId(2001L);
        message.setCustomerId(3001L);
        message.setMessageType("HEALTH_ALERT");
        message.setMessageSubtype("HEART_RATE_ABNORMAL");
        message.setMessageContent("测试V2消息内容");
        message.setPriorityLevel(5);
        message.setUrgencyLevel("NORMAL");
        message.setStatus("PENDING");
        message.setCreatedTime(LocalDateTime.now());
        message.setExpireTime(LocalDateTime.now().plusDays(1));
        message.setRetryCount(0);
        message.setMaxRetries(3);
        message.setSourceSystem("ljwx-boot");
        message.setTargetSystem("multi-platform");
        
        // 添加元数据
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("testKey", "testValue");
        metadata.put("timestamp", System.currentTimeMillis());
        message.setMetadata(metadata);
        
        return message;
    }
    
    private TDeviceMessageDetail createTestMessageDetail(Long messageId) {
        TDeviceMessageDetail detail = new TDeviceMessageDetail();
        detail.setMessageId(messageId);
        detail.setDeviceSn("TEST_DEVICE_" + System.currentTimeMillis());
        detail.setDataType("HEART_RATE");
        detail.setDataSubtype("BPM");
        detail.setDataValue("85.5");
        detail.setDataUnit("bpm");
        detail.setThresholdMin(60.0);
        detail.setThresholdMax(100.0);
        detail.setIsAbnormal(false);
        detail.setConfidenceLevel(0.95);
        detail.setCollectedTime(LocalDateTime.now());
        detail.setProcessedTime(LocalDateTime.now());
        detail.setStatus("PROCESSED");
        detail.setSourceDevice("WATCH_V2");
        
        return detail;
    }
    
    private void clearRedisTestData() {
        try {
            // 清理测试相关的Redis键
            Set<String> testKeys = redisTemplate.keys("ljwx:message:*TEST*");
            if (testKeys != null && !testKeys.isEmpty()) {
                redisTemplate.delete(testKeys);
                log.info("清理Redis测试数据: {} 个键", testKeys.size());
            }
        } catch (Exception e) {
            log.warn("清理Redis测试数据时出现异常: {}", e.getMessage());
        }
    }
}