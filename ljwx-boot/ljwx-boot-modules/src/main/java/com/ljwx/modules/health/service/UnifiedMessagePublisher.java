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

package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.model.AlertResult;
import com.ljwx.modules.health.domain.entity.TDeviceMessageV2;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;
import com.ljwx.infrastructure.util.RedisUtil;
import lombok.Data;
import lombok.Builder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

/**
 * 统一消息发布器
 * 支持多渠道消息分发和智能路由
 * 
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName UnifiedMessagePublisher
 * @CreateTime 2025-09-10
 */
@Service
@Slf4j
public class UnifiedMessagePublisher {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // RedisUtil使用静态方法，不需要注入
    
    @Autowired
    private ObjectMapper objectMapper;
    
    // 消息处理器线程池
    private ExecutorService messageExecutorPool;
    
    // 性能统计
    private final MessageStats messageStats = new MessageStats();
    
    // Redis 消息主题
    private static final String REDIS_TOPIC_MESSAGE_CREATED = "ljwx:message:created";
    private static final String REDIS_TOPIC_MESSAGE_DISTRIBUTED = "ljwx:message:distributed";
    private static final String REDIS_TOPIC_MESSAGE_ACKNOWLEDGED = "ljwx:message:acknowledged";
    private static final String REDIS_TOPIC_MESSAGE_BATCH = "ljwx:message:batch";
    
    // Redis 键前缀
    private static final String REDIS_KEY_MESSAGE_CACHE = "ljwx:message:cache:";
    private static final String REDIS_KEY_MESSAGE_STATUS = "ljwx:message:status:";
    private static final String REDIS_KEY_MESSAGE_QUEUE = "ljwx:message:queue:";
    
    @PostConstruct
    public void init() {
        // 初始化线程池
        messageExecutorPool = new ThreadPoolExecutor(
            4, 16, 60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(5000),
            r -> {
                Thread t = new Thread(r, "message-publisher-" + r.hashCode());
                t.setDaemon(true);
                return t;
            }
        );
        
        log.info("统一消息发布器已初始化，线程池大小: {}", ((ThreadPoolExecutor) messageExecutorPool).getCorePoolSize());
    }
    
    @PreDestroy
    public void destroy() {
        if (messageExecutorPool != null && !messageExecutorPool.isShutdown()) {
            messageExecutorPool.shutdown();
            try {
                if (!messageExecutorPool.awaitTermination(10, TimeUnit.SECONDS)) {
                    messageExecutorPool.shutdownNow();
                }
            } catch (InterruptedException e) {
                messageExecutorPool.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
        log.info("统一消息发布器已关闭");
    }
    
    /**
     * 统一消息发布入口
     */
    public CompletableFuture<PublishResult> publishAlert(AlertMessage alertMessage) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                return publishAlertSync(alertMessage);
            } catch (Exception e) {
                log.error("异步消息发布失败", e);
                return PublishResult.failed("异步发布失败: " + e.getMessage());
            }
        }, messageExecutorPool);
    }
    
    /**
     * 同步消息发布
     */
    public PublishResult publishAlertSync(AlertMessage alertMessage) {
        if (alertMessage == null) {
            return PublishResult.failed("消息为空");
        }
        
        long startTime = System.currentTimeMillis();
        String messageId = generateMessageId();
        
        try {
            // 1. 消息预处理
            UnifiedMessage unifiedMessage = buildUnifiedMessage(alertMessage, messageId);
            
            // 2. 渠道路由
            List<NotificationChannel> channels = routeChannels(alertMessage);
            
            if (channels.isEmpty()) {
                log.warn("未配置消息通知渠道: messageId={}", messageId);
                return PublishResult.failed("未配置通知渠道");
            }
            
            // 3. 并行发送
            List<CompletableFuture<NotificationResult>> futures = channels.stream()
                .map(channel -> CompletableFuture.supplyAsync(() -> 
                    sendToChannel(unifiedMessage, channel), messageExecutorPool))
                .collect(Collectors.toList());
            
            // 4. 等待结果并汇总
            try {
                List<NotificationResult> results = futures.stream()
                    .map(future -> {
                        try {
                            return future.get(30, TimeUnit.SECONDS); // 30秒超时
                        } catch (Exception e) {
                            log.error("消息发送超时: messageId={}", messageId, e);
                            return NotificationResult.failed("发送超时");
                        }
                    })
                    .collect(Collectors.toList());
                
                // 5. 记录结果
                PublishResult result = aggregateResults(messageId, results);
                long processingTime = System.currentTimeMillis() - startTime;
                
                logResults(alertMessage, result, processingTime);
                messageStats.recordPublish(processingTime, result.isSuccess());
                
                return result;
                
            } catch (Exception e) {
                log.error("消息结果汇总失败: messageId={}", messageId, e);
                return PublishResult.failed("结果汇总失败: " + e.getMessage());
            }
            
        } catch (Exception e) {
            log.error("消息发布失败: messageId={}", messageId, e);
            messageStats.recordFailure();
            return PublishResult.failed("消息发布失败: " + e.getMessage());
        }
    }
    
    /**
     * 构建统一消息模型
     */
    private UnifiedMessage buildUnifiedMessage(AlertMessage alertMessage, String messageId) {
        return UnifiedMessage.builder()
            .messageId(messageId)
            .messageType("alert")
            .subType(alertMessage.getAlertType())
            .title(buildTitle(alertMessage))
            .content(buildContent(alertMessage))
            .priority(mapPriority(alertMessage.getSeverityLevel()))
            .urgency(mapUrgency(alertMessage.getSeverityLevel()))
            .sender(buildSender())
            .target(buildTarget(alertMessage))
            .delivery(buildDelivery(alertMessage))
            .metadata(buildMetadata(alertMessage))
            .timestamp(System.currentTimeMillis())
            .build();
    }
    
    /**
     * 构建消息标题
     */
    private String buildTitle(AlertMessage alertMessage) {
        String severityText = getSeverityText(alertMessage.getSeverityLevel());
        String deviceSn = alertMessage.getDeviceSn();
        
        if (deviceSn != null && deviceSn.length() > 6) {
            deviceSn = deviceSn.substring(deviceSn.length() - 6); // 只显示后6位
        }
        
        return String.format("【%s告警】设备 %s 异常", severityText, deviceSn);
    }
    
    /**
     * 构建消息内容
     */
    private String buildContent(AlertMessage alertMessage) {
        StringBuilder content = new StringBuilder();
        content.append("设备序列号: ").append(alertMessage.getDeviceSn()).append("\n");
        content.append("告警时间: ").append(LocalDateTime.now()).append("\n");
        content.append("告警级别: ").append(getSeverityText(alertMessage.getSeverityLevel())).append("\n");
        
        if (alertMessage.getAlertDesc() != null && !alertMessage.getAlertDesc().isEmpty()) {
            content.append("告警描述: ").append(alertMessage.getAlertDesc()).append("\n");
        }
        
        if (alertMessage.getPhysicalSign() != null) {
            content.append("异常指标: ").append(getPhysicalSignText(alertMessage.getPhysicalSign())).append("\n");
        }
        
        if (alertMessage.getCurrentValue() != null) {
            content.append("当前值: ").append(alertMessage.getCurrentValue()).append("\n");
        }
        
        if (alertMessage.getThresholdMin() != null || alertMessage.getThresholdMax() != null) {
            content.append("正常范围: ");
            if (alertMessage.getThresholdMin() != null && alertMessage.getThresholdMax() != null) {
                content.append(alertMessage.getThresholdMin()).append(" - ").append(alertMessage.getThresholdMax());
            } else if (alertMessage.getThresholdMin() != null) {
                content.append("≥ ").append(alertMessage.getThresholdMin());
            } else {
                content.append("≤ ").append(alertMessage.getThresholdMax());
            }
            content.append("\n");
        }
        
        content.append("\n请及时关注设备状态并采取必要措施。");
        
        return content.toString();
    }
    
    /**
     * 映射优先级
     */
    private MessagePriority mapPriority(String severityLevel) {
        if (severityLevel == null) return MessagePriority.NORMAL;
        
        switch (severityLevel.toLowerCase()) {
            case "critical":
                return MessagePriority.URGENT;
            case "major":
                return MessagePriority.HIGH;
            case "minor":
                return MessagePriority.NORMAL;
            case "info":
                return MessagePriority.LOW;
            default:
                return MessagePriority.NORMAL;
        }
    }
    
    /**
     * 映射紧急程度
     */
    private MessageUrgency mapUrgency(String severityLevel) {
        if (severityLevel == null) return MessageUrgency.NORMAL;
        
        switch (severityLevel.toLowerCase()) {
            case "critical":
                return MessageUrgency.IMMEDIATE;
            case "major":
                return MessageUrgency.HIGH;
            case "minor":
                return MessageUrgency.NORMAL;
            case "info":
                return MessageUrgency.LOW;
            default:
                return MessageUrgency.NORMAL;
        }
    }
    
    /**
     * 构建发送者信息
     */
    private MessageSender buildSender() {
        return MessageSender.builder()
            .senderId("system")
            .senderName("健康监护系统")
            .senderType("system")
            .build();
    }
    
    /**
     * 构建目标信息
     */
    private MessageTarget buildTarget(AlertMessage alertMessage) {
        return MessageTarget.builder()
            .customerId(alertMessage.getCustomerId())
            .userId(alertMessage.getUserId())
            .orgId(alertMessage.getOrgId())
            .deviceSn(alertMessage.getDeviceSn())
            .build();
    }
    
    /**
     * 构建投递信息
     */
    private MessageDelivery buildDelivery(AlertMessage alertMessage) {
        return MessageDelivery.builder()
            .channels(alertMessage.getEnabledChannels())
            .retryCount(0)
            .maxRetries(3)
            .retryInterval(5000L) // 5秒重试间隔
            .expireTime(System.currentTimeMillis() + 24 * 60 * 60 * 1000L) // 24小时过期
            .build();
    }
    
    /**
     * 构建元数据
     */
    private Map<String, Object> buildMetadata(AlertMessage alertMessage) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("ruleId", alertMessage.getRuleId());
        metadata.put("alertType", alertMessage.getAlertType());
        metadata.put("physicalSign", alertMessage.getPhysicalSign());
        metadata.put("severityLevel", alertMessage.getSeverityLevel());
        metadata.put("source", "alert-engine");
        metadata.put("version", "1.0");
        return metadata;
    }
    
    /**
     * 渠道智能路由
     */
    private List<NotificationChannel> routeChannels(AlertMessage alertMessage) {
        List<NotificationChannel> channels = new ArrayList<>();
        
        String severity = alertMessage.getSeverityLevel();
        List<String> enabledChannels = alertMessage.getEnabledChannels();
        
        if (enabledChannels == null || enabledChannels.isEmpty()) {
            enabledChannels = Arrays.asList("message"); // 默认内部消息
        }
        
        // 基于配置的渠道
        for (String channelName : enabledChannels) {
            NotificationChannel channel = parseChannel(channelName);
            if (channel != null) {
                channels.add(channel);
            }
        }
        
        // Critical级别强制WebSocket推送
        if ("critical".equalsIgnoreCase(severity)) {
            if (!channels.contains(NotificationChannel.WEBSOCKET)) {
                channels.add(NotificationChannel.WEBSOCKET);
            }
        }
        
        return channels;
    }
    
    /**
     * 解析渠道名称
     */
    private NotificationChannel parseChannel(String channelName) {
        if (channelName == null) return null;
        
        switch (channelName.toLowerCase()) {
            case "wechat":
                return NotificationChannel.WECHAT;
            case "message":
                return NotificationChannel.INTERNAL_MESSAGE;
            case "sms":
                return NotificationChannel.SMS;
            case "email":
                return NotificationChannel.EMAIL;
            case "webhook":
                return NotificationChannel.WEBHOOK;
            case "websocket":
                return NotificationChannel.WEBSOCKET;
            default:
                log.warn("未知的通知渠道: {}", channelName);
                return null;
        }
    }
    
    /**
     * 发送到指定渠道
     */
    private NotificationResult sendToChannel(UnifiedMessage message, NotificationChannel channel) {
        try {
            switch (channel) {
                case WECHAT:
                    return sendWechatMessage(message);
                case SMS:
                    return sendSmsMessage(message);
                case EMAIL:
                    return sendEmailMessage(message);
                case WEBSOCKET:
                    return sendWebSocketMessage(message);
                case WEBHOOK:
                    return sendWebhookMessage(message);
                case INTERNAL_MESSAGE:
                    return sendInternalMessage(message);
                default:
                    return NotificationResult.failed("未知渠道: " + channel);
            }
        } catch (Exception e) {
            log.error("发送消息失败: channel={}, messageId={}", channel, message.getMessageId(), e);
            return NotificationResult.failed("发送异常: " + e.getMessage());
        }
    }
    
    /**
     * 发送微信消息
     */
    private NotificationResult sendWechatMessage(UnifiedMessage message) {
        // TODO: 实现微信消息发送逻辑
        log.debug("发送微信消息: messageId={}", message.getMessageId());
        
        try {
            // 模拟发送延迟
            Thread.sleep(100);
            return NotificationResult.success("微信消息发送成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("微信消息发送中断");
        }
    }
    
    /**
     * 发送短信消息
     */
    private NotificationResult sendSmsMessage(UnifiedMessage message) {
        // TODO: 实现短信发送逻辑
        log.debug("发送短信消息: messageId={}", message.getMessageId());
        
        try {
            Thread.sleep(200);
            return NotificationResult.success("短信发送成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("短信发送中断");
        }
    }
    
    /**
     * 发送邮件消息
     */
    private NotificationResult sendEmailMessage(UnifiedMessage message) {
        // TODO: 实现邮件发送逻辑
        log.debug("发送邮件消息: messageId={}", message.getMessageId());
        
        try {
            Thread.sleep(300);
            return NotificationResult.success("邮件发送成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("邮件发送中断");
        }
    }
    
    /**
     * 发送WebSocket消息
     */
    private NotificationResult sendWebSocketMessage(UnifiedMessage message) {
        // TODO: 实现WebSocket推送逻辑
        log.debug("发送WebSocket消息: messageId={}", message.getMessageId());
        
        try {
            Thread.sleep(50);
            return NotificationResult.success("WebSocket推送成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("WebSocket推送中断");
        }
    }
    
    /**
     * 发送Webhook消息
     */
    private NotificationResult sendWebhookMessage(UnifiedMessage message) {
        // TODO: 实现Webhook发送逻辑
        log.debug("发送Webhook消息: messageId={}", message.getMessageId());
        
        try {
            Thread.sleep(150);
            return NotificationResult.success("Webhook发送成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("Webhook发送中断");
        }
    }
    
    /**
     * 发送内部消息
     */
    private NotificationResult sendInternalMessage(UnifiedMessage message) {
        // TODO: 实现内部消息存储逻辑
        log.debug("保存内部消息: messageId={}", message.getMessageId());
        
        try {
            // 模拟数据库操作
            Thread.sleep(20);
            return NotificationResult.success("内部消息保存成功");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return NotificationResult.failed("内部消息保存中断");
        }
    }
    
    /**
     * 汇总发送结果
     */
    private PublishResult aggregateResults(String messageId, List<NotificationResult> results) {
        if (results.isEmpty()) {
            return PublishResult.failed("无发送结果");
        }
        
        int successCount = 0;
        int failureCount = 0;
        List<String> failureReasons = new ArrayList<>();
        
        for (NotificationResult result : results) {
            if (result.isSuccess()) {
                successCount++;
            } else {
                failureCount++;
                if (result.getErrorMessage() != null) {
                    failureReasons.add(result.getErrorMessage());
                }
            }
        }
        
        boolean overallSuccess = successCount > 0; // 至少有一个成功就算成功
        
        return PublishResult.builder()
            .messageId(messageId)
            .success(overallSuccess)
            .totalChannels(results.size())
            .successChannels(successCount)
            .failureChannels(failureCount)
            .failureReasons(failureReasons)
            .message(overallSuccess ? "消息发布成功" : "消息发布失败")
            .timestamp(System.currentTimeMillis())
            .build();
    }
    
    /**
     * 记录结果日志
     */
    private void logResults(AlertMessage alertMessage, PublishResult result, long processingTime) {
        if (result.isSuccess()) {
            log.info("消息发布成功: messageId={}, deviceSn={}, channels={}/{}, time={}ms", 
                result.getMessageId(), alertMessage.getDeviceSn(), 
                result.getSuccessChannels(), result.getTotalChannels(), processingTime);
        } else {
            log.warn("消息发布部分失败: messageId={}, deviceSn={}, success={}/{}, failures={}, time={}ms", 
                result.getMessageId(), alertMessage.getDeviceSn(),
                result.getSuccessChannels(), result.getTotalChannels(),
                String.join(", ", result.getFailureReasons()), processingTime);
        }
    }
    
    /**
     * 获取严重程度文本
     */
    private String getSeverityText(String severityLevel) {
        if (severityLevel == null) return "一般";
        
        switch (severityLevel.toLowerCase()) {
            case "critical":
                return "紧急";
            case "major":
                return "重要";
            case "minor":
                return "一般";
            case "info":
                return "信息";
            default:
                return "一般";
        }
    }
    
    /**
     * 获取生理指标文本
     */
    private String getPhysicalSignText(String physicalSign) {
        if (physicalSign == null) return "";
        
        switch (physicalSign.toLowerCase()) {
            case "heart_rate":
                return "心率";
            case "blood_oxygen":
                return "血氧";
            case "temperature":
                return "体温";
            case "pressure_high":
                return "收缩压";
            case "pressure_low":
                return "舒张压";
            case "step":
                return "步数";
            case "calorie":
                return "卡路里";
            case "distance":
                return "距离";
            case "stress":
                return "压力指数";
            default:
                return physicalSign;
        }
    }
    
    /**
     * 生成消息ID
     */
    private String generateMessageId() {
        return "msg_" + System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8);
    }
    
    /**
     * 获取消息统计信息
     */
    public Map<String, Object> getMessageStats() {
        return messageStats.getStats();
    }
    
    // ==================== V2 消息系统 Redis 集成方法 ====================
    
    /**
     * 发布 V2 消息创建事件到 Redis 消息总线
     */
    @Async
    public CompletableFuture<Boolean> publishMessageCreated(TDeviceMessageV2 message) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                V2MessageEvent event = V2MessageEvent.builder()
                    .eventType("MESSAGE_CREATED")
                    .messageId(message.getId())
                    .deviceSn(message.getDeviceSn())
                    .userId(message.getUserId())
                    .orgId(message.getOrgId())
                    .messageType(message.getMessageType().name())
                    .timestamp(System.currentTimeMillis())
                    .payload(message)
                    .build();
                
                redisTemplate.convertAndSend(REDIS_TOPIC_MESSAGE_CREATED, event);
                
                // 缓存消息到Redis，TTL 24小时
                String cacheKey = REDIS_KEY_MESSAGE_CACHE + message.getId();
                RedisUtil.set(cacheKey, message, 24 * 60 * 60);
                
                log.debug("V2消息创建事件已发布到Redis: messageId={}, deviceSn={}", 
                    message.getId(), message.getDeviceSn());
                return true;
                
            } catch (Exception e) {
                log.error("发布V2消息创建事件失败: messageId={}", message.getId(), e);
                return false;
            }
        }, messageExecutorPool);
    }
    
    /**
     * 发布 V2 消息分发事件到 Redis 消息总线
     */
    @Async
    public CompletableFuture<Boolean> publishMessageDistributed(TDeviceMessageV2 message, List<String> targetDevices) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                V2MessageDistributionEvent event = V2MessageDistributionEvent.builder()
                    .eventType("MESSAGE_DISTRIBUTED")
                    .messageId(message.getId())
                    .deviceSn(message.getDeviceSn())
                    .targetDevices(targetDevices)
                    .distributionTime(System.currentTimeMillis())
                    .build();
                
                redisTemplate.convertAndSend(REDIS_TOPIC_MESSAGE_DISTRIBUTED, event);
                
                // 更新消息状态缓存
                String statusKey = REDIS_KEY_MESSAGE_STATUS + message.getId();
                Map<String, Object> status = new HashMap<>();
                status.put("status", "DISTRIBUTED");
                status.put("targetCount", targetDevices.size());
                status.put("distributionTime", System.currentTimeMillis());
                RedisUtil.set(statusKey, status, 24 * 60 * 60);
                
                log.debug("V2消息分发事件已发布到Redis: messageId={}, targets={}", 
                    message.getId(), targetDevices.size());
                return true;
                
            } catch (Exception e) {
                log.error("发布V2消息分发事件失败: messageId={}", message.getId(), e);
                return false;
            }
        }, messageExecutorPool);
    }
    
    /**
     * 发布 V2 批量消息分发事件到 Redis 消息总线
     */
    @Async
    public CompletableFuture<Boolean> publishBatchMessageDistributed(List<TDeviceMessageV2> messages, 
                                                                    Map<Long, List<String>> targetMap) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                V2BatchMessageEvent event = V2BatchMessageEvent.builder()
                    .eventType("BATCH_MESSAGE_DISTRIBUTED")
                    .messageIds(messages.stream().map(TDeviceMessageV2::getId).collect(Collectors.toList()))
                    .batchSize(messages.size())
                    .totalTargets(targetMap.values().stream().mapToInt(List::size).sum())
                    .distributionTime(System.currentTimeMillis())
                    .targetMap(targetMap)
                    .build();
                
                redisTemplate.convertAndSend(REDIS_TOPIC_MESSAGE_BATCH, event);
                
                // 批量更新消息状态
                messages.parallelStream().forEach(message -> {
                    String statusKey = REDIS_KEY_MESSAGE_STATUS + message.getId();
                    Map<String, Object> status = new HashMap<>();
                    status.put("status", "BATCH_DISTRIBUTED");
                    status.put("batchId", event.getBatchId());
                    status.put("distributionTime", System.currentTimeMillis());
                    RedisUtil.set(statusKey, status, 24 * 60 * 60);
                });
                
                log.info("V2批量消息分发事件已发布到Redis: batchSize={}, totalTargets={}", 
                    messages.size(), event.getTotalTargets());
                return true;
                
            } catch (Exception e) {
                log.error("发布V2批量消息分发事件失败: batchSize={}", messages.size(), e);
                return false;
            }
        }, messageExecutorPool);
    }
    
    /**
     * 发布 V2 消息确认事件到 Redis 消息总线
     */
    @Async
    public CompletableFuture<Boolean> publishMessageAcknowledged(Long messageId, String deviceSn, 
                                                                String ackType, Map<String, Object> ackData) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                V2MessageAckEvent event = V2MessageAckEvent.builder()
                    .eventType("MESSAGE_ACKNOWLEDGED")
                    .messageId(messageId)
                    .deviceSn(deviceSn)
                    .ackType(ackType)
                    .ackTime(System.currentTimeMillis())
                    .ackData(ackData)
                    .build();
                
                redisTemplate.convertAndSend(REDIS_TOPIC_MESSAGE_ACKNOWLEDGED, event);
                
                // 更新确认状态
                String statusKey = REDIS_KEY_MESSAGE_STATUS + messageId;
                Map<String, Object> ackStatus = new HashMap<>();
                ackStatus.put("ackStatus", ackType);
                ackStatus.put("ackTime", System.currentTimeMillis());
                ackStatus.put("ackDevice", deviceSn);
                RedisUtil.set(statusKey, ackStatus, 24 * 60 * 60);
                
                log.debug("V2消息确认事件已发布到Redis: messageId={}, deviceSn={}, ackType={}", 
                    messageId, deviceSn, ackType);
                return true;
                
            } catch (Exception e) {
                log.error("发布V2消息确认事件失败: messageId={}, deviceSn={}", messageId, deviceSn, e);
                return false;
            }
        }, messageExecutorPool);
    }
    
    /**
     * 将 V2 消息推送到设备队列
     */
    @Async
    public CompletableFuture<Boolean> pushToDeviceQueue(String deviceSn, TDeviceMessageV2 message, Integer priority) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String queueKey = REDIS_KEY_MESSAGE_QUEUE + deviceSn;
                
                V2QueuedMessage queuedMessage = V2QueuedMessage.builder()
                    .messageId(message.getId())
                    .messageType(message.getMessageType().name())
                    .priority(priority != null ? priority : 5)
                    .queueTime(System.currentTimeMillis())
                    .expireTime(System.currentTimeMillis() + 24 * 60 * 60 * 1000L) // 24小时过期
                    .message(message)
                    .build();
                
                // 使用有序集合存储，以优先级为分数
                double score = priority != null ? priority : 5.0;
                redisTemplate.opsForZSet().add(queueKey, queuedMessage, score);
                redisTemplate.expire(queueKey, 24, TimeUnit.HOURS);
                
                log.debug("V2消息已推送到设备队列: deviceSn={}, messageId={}, priority={}", 
                    deviceSn, message.getId(), priority);
                return true;
                
            } catch (Exception e) {
                log.error("推送V2消息到设备队列失败: deviceSn={}, messageId={}", deviceSn, message.getId(), e);
                return false;
            }
        }, messageExecutorPool);
    }
    
    /**
     * 从设备队列获取待发送消息 (高优先级优先)
     */
    public List<V2QueuedMessage> getQueuedMessages(String deviceSn, int limit) {
        try {
            String queueKey = REDIS_KEY_MESSAGE_QUEUE + deviceSn;
            
            // 获取高优先级消息 (按分数倒序，分数越高优先级越高)
            Set<Object> messages = redisTemplate.opsForZSet().reverseRange(queueKey, 0, limit - 1);
            
            return messages.stream()
                .map(obj -> {
                    try {
                        if (obj instanceof V2QueuedMessage) {
                            return (V2QueuedMessage) obj;
                        } else {
                            return objectMapper.readValue(obj.toString(), V2QueuedMessage.class);
                        }
                    } catch (Exception e) {
                        log.error("解析队列消息失败", e);
                        return null;
                    }
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("获取设备队列消息失败: deviceSn={}", deviceSn, e);
            return Collections.emptyList();
        }
    }
    
    /**
     * 从设备队列移除已处理的消息
     */
    public boolean removeFromQueue(String deviceSn, Long messageId) {
        try {
            String queueKey = REDIS_KEY_MESSAGE_QUEUE + deviceSn;
            
            // 查找并移除指定消息ID的队列项
            Set<Object> allMessages = redisTemplate.opsForZSet().range(queueKey, 0, -1);
            
            for (Object obj : allMessages) {
                try {
                    V2QueuedMessage queuedMessage = (obj instanceof V2QueuedMessage) 
                        ? (V2QueuedMessage) obj
                        : objectMapper.readValue(obj.toString(), V2QueuedMessage.class);
                        
                    if (messageId.equals(queuedMessage.getMessageId())) {
                        redisTemplate.opsForZSet().remove(queueKey, obj);
                        log.debug("已从设备队列移除消息: deviceSn={}, messageId={}", deviceSn, messageId);
                        return true;
                    }
                } catch (Exception e) {
                    log.warn("解析队列消息时出错，跳过: {}", obj, e);
                }
            }
            
            return false;
            
        } catch (Exception e) {
            log.error("从设备队列移除消息失败: deviceSn={}, messageId={}", deviceSn, messageId, e);
            return false;
        }
    }
    
    /**
     * 获取设备队列状态
     */
    public Map<String, Object> getDeviceQueueStatus(String deviceSn) {
        try {
            String queueKey = REDIS_KEY_MESSAGE_QUEUE + deviceSn;
            
            Long queueSize = redisTemplate.opsForZSet().count(queueKey, Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY);
            Long highPriorityCount = redisTemplate.opsForZSet().count(queueKey, 8.0, Double.POSITIVE_INFINITY);
            Long ttl = redisTemplate.getExpire(queueKey);
            
            Map<String, Object> status = new HashMap<>();
            status.put("deviceSn", deviceSn);
            status.put("queueSize", queueSize != null ? queueSize : 0);
            status.put("highPriorityCount", highPriorityCount != null ? highPriorityCount : 0);
            status.put("ttlSeconds", ttl != null ? ttl : -1);
            status.put("lastUpdateTime", System.currentTimeMillis());
            
            return status;
            
        } catch (Exception e) {
            log.error("获取设备队列状态失败: deviceSn={}", deviceSn, e);
            Map<String, Object> errorStatus = new HashMap<>();
            errorStatus.put("deviceSn", deviceSn);
            errorStatus.put("error", "获取队列状态失败: " + e.getMessage());
            return errorStatus;
        }
    }
    
    // 内部类和枚举定义
    
    public enum NotificationChannel {
        WECHAT, SMS, EMAIL, WEBSOCKET, WEBHOOK, INTERNAL_MESSAGE
    }
    
    public enum MessagePriority {
        LOW, NORMAL, HIGH, URGENT
    }
    
    public enum MessageUrgency {
        LOW, NORMAL, HIGH, IMMEDIATE
    }
    
    @Data
    @Builder
    public static class AlertMessage {
        private Long ruleId;
        private String alertType;
        private String deviceSn;
        private String alertDesc;
        private String severityLevel;
        private String physicalSign;
        private Object currentValue;
        private Object thresholdMin;
        private Object thresholdMax;
        private Long customerId;
        private Long userId;
        private Long orgId;
        private List<String> enabledChannels;
    }
    
    @Data
    @Builder
    public static class UnifiedMessage {
        private String messageId;
        private String messageType;
        private String subType;
        private String title;
        private String content;
        private MessagePriority priority;
        private MessageUrgency urgency;
        private MessageSender sender;
        private MessageTarget target;
        private MessageDelivery delivery;
        private Map<String, Object> metadata;
        private Long timestamp;
    }
    
    @Data
    @Builder
    public static class MessageSender {
        private String senderId;
        private String senderName;
        private String senderType;
    }
    
    @Data
    @Builder
    public static class MessageTarget {
        private Long customerId;
        private Long userId;
        private Long orgId;
        private String deviceSn;
    }
    
    @Data
    @Builder
    public static class MessageDelivery {
        private List<String> channels;
        private Integer retryCount;
        private Integer maxRetries;
        private Long retryInterval;
        private Long expireTime;
    }
    
    @Data
    @Builder
    public static class NotificationResult {
        private boolean success;
        private String message;
        private String errorMessage;
        private Long timestamp;
        
        public static NotificationResult success(String message) {
            return NotificationResult.builder()
                .success(true)
                .message(message)
                .timestamp(System.currentTimeMillis())
                .build();
        }
        
        public static NotificationResult failed(String errorMessage) {
            return NotificationResult.builder()
                .success(false)
                .errorMessage(errorMessage)
                .timestamp(System.currentTimeMillis())
                .build();
        }
    }
    
    @Data
    @Builder
    public static class PublishResult {
        private String messageId;
        private boolean success;
        private String message;
        private Integer totalChannels;
        private Integer successChannels;
        private Integer failureChannels;
        private List<String> failureReasons;
        private Long timestamp;
        
        public static PublishResult failed(String message) {
            return PublishResult.builder()
                .success(false)
                .message(message)
                .timestamp(System.currentTimeMillis())
                .build();
        }
    }
    
    /**
     * 消息统计
     */
    private static class MessageStats {
        private volatile long publishCount = 0;
        private volatile long successCount = 0;
        private volatile long failureCount = 0;
        private volatile long totalProcessingTime = 0;
        
        public void recordPublish(long processingTime, boolean success) {
            publishCount++;
            totalProcessingTime += processingTime;
            
            if (success) {
                successCount++;
            } else {
                failureCount++;
            }
        }
        
        public void recordFailure() {
            failureCount++;
        }
        
        public Map<String, Object> getStats() {
            Map<String, Object> stats = new HashMap<>();
            stats.put("publishCount", publishCount);
            stats.put("successCount", successCount);
            stats.put("failureCount", failureCount);
            stats.put("successRate", publishCount > 0 ? (double) successCount / publishCount * 100 : 0);
            stats.put("avgProcessingTime", publishCount > 0 ? (double) totalProcessingTime / publishCount : 0);
            return stats;
        }
    }
    
    // ==================== V2 消息事件类定义 ====================
    
    /**
     * V2 消息事件基类
     */
    @Data
    @Builder
    public static class V2MessageEvent {
        private String eventType;
        private Long messageId;
        private String deviceSn;
        private String userId;
        private Long orgId;
        private String messageType;
        private Long timestamp;
        private TDeviceMessageV2 payload;
    }
    
    /**
     * V2 消息分发事件
     */
    @Data
    @Builder
    public static class V2MessageDistributionEvent {
        private String eventType;
        private Long messageId;
        private String deviceSn;
        private List<String> targetDevices;
        private Long distributionTime;
    }
    
    /**
     * V2 批量消息分发事件
     */
    @Data
    @Builder
    public static class V2BatchMessageEvent {
        private String eventType;
        private String batchId;
        private List<Long> messageIds;
        private Integer batchSize;
        private Integer totalTargets;
        private Long distributionTime;
        private Map<Long, List<String>> targetMap;
        
        @Builder.Default
        private String batchIdDefault = generateBatchId();
        
        private static String generateBatchId() {
            return "batch_" + System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8);
        }
        
        public String getBatchId() {
            return batchId != null ? batchId : batchIdDefault;
        }
    }
    
    /**
     * V2 消息确认事件
     */
    @Data
    @Builder
    public static class V2MessageAckEvent {
        private String eventType;
        private Long messageId;
        private String deviceSn;
        private String ackType;
        private Long ackTime;
        private Map<String, Object> ackData;
    }
    
    /**
     * V2 队列消息
     */
    @Data
    @Builder
    public static class V2QueuedMessage {
        private Long messageId;
        private String messageType;
        private Integer priority;
        private Long queueTime;
        private Long expireTime;
        private TDeviceMessageV2 message;
    }
}