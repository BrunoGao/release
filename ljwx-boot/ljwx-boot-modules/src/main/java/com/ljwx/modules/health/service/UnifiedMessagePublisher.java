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
import lombok.Data;
import lombok.Builder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

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
    
    // 消息处理器线程池
    private ExecutorService messageExecutorPool;
    
    // 性能统计
    private final MessageStats messageStats = new MessageStats();
    
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
}