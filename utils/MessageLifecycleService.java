package com.ljwx.modules.health.service.impl;

import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ljwx.common.util.DateUtil;
import com.ljwx.infrastructure.redis.RedisService;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import com.ljwx.modules.health.service.ITDeviceMessageDetailService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 消息生命周期管理服务
 * 负责消息生命周期事件记录、里程碑跟踪、状态分析等功能
 * 
 * @Author brunoGao
 * @CreateTime 2025-09-10
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class MessageLifecycleService {

    private final ITDeviceMessageService messageService;
    private final ITDeviceMessageDetailService messageDetailService;
    private final RedisService redisService;

    private static final String LIFECYCLE_CACHE_PREFIX = "message:lifecycle:";
    private static final String LIFECYCLE_STATS_PREFIX = "message:lifecycle:stats:";

    /**
     * 记录消息生命周期事件
     */
    @Transactional
    public void recordLifecycleEvent(Long messageId, String event, String operator, String platform) {
        try {
            // 获取消息信息
            TDeviceMessage message = messageService.getById(messageId);
            if (message == null) {
                log.warn("消息不存在，无法记录生命周期事件: messageId={}, event={}", messageId, event);
                return;
            }

            // 构建生命周期事件
            JSONObject lifecycleEvent = new JSONObject();
            lifecycleEvent.set("event", event);
            lifecycleEvent.set("timestamp", LocalDateTime.now());
            lifecycleEvent.set("operator", operator);
            lifecycleEvent.set("platform", platform);
            lifecycleEvent.set("messageId", messageId);

            // 存储到Redis缓存
            String cacheKey = LIFECYCLE_CACHE_PREFIX + messageId;
            List<JSONObject> events = getLifecycleEvents(messageId);
            events.add(lifecycleEvent);
            
            redisService.set(cacheKey, JSONUtil.toJsonStr(events), 7 * 24 * 3600); // 7天过期

            // 更新消息状态
            updateMessageStatus(messageId, event);

            // 发布生命周期事件到Redis
            JSONObject eventNotification = new JSONObject();
            eventNotification.set("type", "lifecycle_event");
            eventNotification.set("messageId", messageId);
            eventNotification.set("event", event);
            eventNotification.set("timestamp", LocalDateTime.now());
            
            redisService.publish("message:lifecycle:events", eventNotification.toString());

            log.info("记录消息生命周期事件成功: messageId={}, event={}, operator={}", messageId, event, operator);

        } catch (Exception e) {
            log.error("记录消息生命周期事件失败: messageId={}, event={}", messageId, event, e);
        }
    }

    /**
     * 获取消息生命周期事件列表
     */
    public List<JSONObject> getLifecycleEvents(Long messageId) {
        try {
            String cacheKey = LIFECYCLE_CACHE_PREFIX + messageId;
            String eventsJson = redisService.get(cacheKey);
            
            if (eventsJson != null) {
                return JSONUtil.toList(eventsJson, JSONObject.class);
            }
            
            return new ArrayList<>();
        } catch (Exception e) {
            log.error("获取消息生命周期事件失败: messageId={}", messageId, e);
            return new ArrayList<>();
        }
    }

    /**
     * 获取消息生命周期里程碑
     */
    public JSONObject getLifecycleMilestones(Long messageId) {
        try {
            List<JSONObject> events = getLifecycleEvents(messageId);
            JSONObject milestones = new JSONObject();

            // 按事件类型分组
            Map<String, List<JSONObject>> eventGroups = events.stream()
                .collect(Collectors.groupingBy(event -> event.getStr("event")));

            // 计算关键里程碑
            JSONObject createdEvent = eventGroups.getOrDefault("created", new ArrayList<>())
                .stream().findFirst().orElse(null);
            JSONObject publishedEvent = eventGroups.getOrDefault("published", new ArrayList<>())
                .stream().findFirst().orElse(null);
            
            if (createdEvent != null) {
                milestones.set("created", createdEvent);
                
                if (publishedEvent != null) {
                    LocalDateTime createdTime = createdEvent.get("timestamp", LocalDateTime.class);
                    LocalDateTime publishedTime = publishedEvent.get("timestamp", LocalDateTime.class);
                    long publishDelay = ChronoUnit.SECONDS.between(createdTime, publishedTime);
                    milestones.set("publishDelay", publishDelay);
                    milestones.set("published", publishedEvent);
                }
            }

            // 统计分发状态
            List<JSONObject> deliveryEvents = eventGroups.getOrDefault("delivery_attempt", new ArrayList<>());
            List<JSONObject> ackEvents = eventGroups.getOrDefault("acknowledged", new ArrayList<>());
            
            milestones.set("totalDeliveryAttempts", deliveryEvents.size());
            milestones.set("totalAcknowledgements", ackEvents.size());

            // 计算完成进度
            JSONObject progress = calculateProgress(messageId, events);
            milestones.set("progress", progress);

            return milestones;

        } catch (Exception e) {
            log.error("获取消息生命周期里程碑失败: messageId={}", messageId, e);
            return new JSONObject();
        }
    }

    /**
     * 计算消息完成进度
     */
    private JSONObject calculateProgress(Long messageId, List<JSONObject> events) {
        JSONObject progress = new JSONObject();
        
        try {
            // 获取消息详情统计
            QueryWrapper<TDeviceMessageDetail> wrapper = new QueryWrapper<>();
            wrapper.eq("message_id", messageId);
            List<TDeviceMessageDetail> details = messageDetailService.list(wrapper);

            if (details.isEmpty()) {
                progress.set("totalTargets", 0);
                progress.set("delivered", 0);
                progress.set("acknowledged", 0);
                progress.set("pending", 0);
                progress.set("failed", 0);
                progress.set("completionRate", 0.0);
                return progress;
            }

            int totalTargets = details.size();
            long delivered = details.stream().mapToLong(d -> 
                "delivered".equals(d.getDeliveryStatus()) || "acknowledged".equals(d.getDeliveryStatus()) ? 1 : 0).sum();
            long acknowledged = details.stream().mapToLong(d -> 
                "acknowledged".equals(d.getDeliveryStatus()) ? 1 : 0).sum();
            long pending = details.stream().mapToLong(d -> 
                "pending".equals(d.getDeliveryStatus()) ? 1 : 0).sum();
            long failed = details.stream().mapToLong(d -> 
                "failed".equals(d.getDeliveryStatus()) ? 1 : 0).sum();

            double completionRate = totalTargets > 0 ? (double) acknowledged / totalTargets * 100 : 0.0;

            progress.set("totalTargets", totalTargets);
            progress.set("delivered", delivered);
            progress.set("acknowledged", acknowledged);
            progress.set("pending", pending);
            progress.set("failed", failed);
            progress.set("completionRate", Math.round(completionRate * 100.0) / 100.0);

            // 计算平均响应时间
            OptionalDouble avgResponseTime = details.stream()
                .filter(d -> d.getResponseTime() != null && d.getResponseTime() > 0)
                .mapToDouble(TDeviceMessageDetail::getResponseTime)
                .average();
            
            progress.set("avgResponseTime", avgResponseTime.orElse(0.0));

        } catch (Exception e) {
            log.error("计算消息完成进度失败: messageId={}", messageId, e);
        }

        return progress;
    }

    /**
     * 生成消息生命周期报告
     */
    public JSONObject generateLifecycleReport(Long messageId) {
        try {
            TDeviceMessage message = messageService.getById(messageId);
            if (message == null) {
                throw new RuntimeException("消息不存在: " + messageId);
            }

            JSONObject report = new JSONObject();
            
            // 基本信息
            report.set("messageId", messageId);
            report.set("messageType", message.getMessageType());
            report.set("subType", message.getSubType());
            report.set("title", message.getTitle());
            report.set("priority", message.getPriority());
            report.set("urgency", message.getUrgency());

            // 时间信息
            report.set("createTime", message.getCreateTime());
            report.set("publishTime", message.getSentTime());
            
            // 生命周期事件
            List<JSONObject> events = getLifecycleEvents(messageId);
            report.set("lifecycleEvents", events);
            
            // 里程碑信息
            JSONObject milestones = getLifecycleMilestones(messageId);
            report.set("milestones", milestones);

            // 分发统计
            QueryWrapper<TDeviceMessageDetail> wrapper = new QueryWrapper<>();
            wrapper.eq("message_id", messageId);
            List<TDeviceMessageDetail> details = messageDetailService.list(wrapper);
            
            // 按状态分组统计
            Map<String, Long> statusStats = details.stream()
                .collect(Collectors.groupingBy(
                    d -> d.getDeliveryStatus() != null ? d.getDeliveryStatus() : "unknown",
                    Collectors.counting()
                ));
            report.set("statusStatistics", statusStats);

            // 按渠道分组统计
            Map<String, Long> channelStats = details.stream()
                .collect(Collectors.groupingBy(
                    d -> d.getChannel() != null ? d.getChannel() : "unknown",
                    Collectors.counting()
                ));
            report.set("channelStatistics", channelStats);

            // 性能指标
            JSONObject performance = new JSONObject();
            
            // 总体耗时
            if (message.getCreateTime() != null && message.getSentTime() != null) {
                long totalDuration = ChronoUnit.SECONDS.between(message.getCreateTime(), message.getSentTime());
                performance.set("publishDuration", totalDuration);
            }

            // 响应时间统计
            List<Integer> responseTimes = details.stream()
                .filter(d -> d.getResponseTime() != null && d.getResponseTime() > 0)
                .map(TDeviceMessageDetail::getResponseTime)
                .collect(Collectors.toList());

            if (!responseTimes.isEmpty()) {
                performance.set("minResponseTime", Collections.min(responseTimes));
                performance.set("maxResponseTime", Collections.max(responseTimes));
                performance.set("avgResponseTime", 
                    responseTimes.stream().mapToInt(Integer::intValue).average().orElse(0.0));
            }

            report.set("performance", performance);

            // 异常统计
            long failedCount = details.stream()
                .mapToLong(d -> "failed".equals(d.getDeliveryStatus()) ? 1 : 0)
                .sum();
            
            JSONObject exceptions = new JSONObject();
            exceptions.set("failedDeliveries", failedCount);
            exceptions.set("failureRate", 
                details.size() > 0 ? (double) failedCount / details.size() * 100 : 0.0);
            
            report.set("exceptions", exceptions);

            return report;

        } catch (Exception e) {
            log.error("生成消息生命周期报告失败: messageId={}", messageId, e);
            throw new RuntimeException("生成生命周期报告失败", e);
        }
    }

    /**
     * 获取组织消息生命周期统计
     */
    public JSONObject getOrganizationLifecycleStats(Long orgId, LocalDateTime startTime, LocalDateTime endTime) {
        try {
            JSONObject stats = new JSONObject();
            
            // 获取组织内消息
            QueryWrapper<TDeviceMessage> messageWrapper = new QueryWrapper<>();
            messageWrapper.eq("customer_id", orgId);
            if (startTime != null) {
                messageWrapper.ge("create_time", startTime);
            }
            if (endTime != null) {
                messageWrapper.le("create_time", endTime);
            }
            
            List<TDeviceMessage> messages = messageService.list(messageWrapper);
            
            if (messages.isEmpty()) {
                stats.set("totalMessages", 0);
                stats.set("avgCompletionTime", 0.0);
                stats.set("avgCompletionRate", 0.0);
                return stats;
            }

            // 基础统计
            stats.set("totalMessages", messages.size());
            
            // 按类型分组统计
            Map<String, Long> typeStats = messages.stream()
                .collect(Collectors.groupingBy(
                    m -> m.getMessageType() != null ? m.getMessageType() : "unknown",
                    Collectors.counting()
                ));
            stats.set("messageTypeStats", typeStats);

            // 按紧急程度分组统计
            Map<String, Long> urgencyStats = messages.stream()
                .collect(Collectors.groupingBy(
                    m -> m.getUrgency() != null ? m.getUrgency() : "unknown",
                    Collectors.counting()
                ));
            stats.set("urgencyStats", urgencyStats);

            // 计算平均完成率和完成时间
            List<Double> completionRates = new ArrayList<>();
            List<Long> completionTimes = new ArrayList<>();

            for (TDeviceMessage message : messages) {
                JSONObject progress = calculateProgress(message.getId(), getLifecycleEvents(message.getId()));
                Double completionRate = progress.getDouble("completionRate");
                if (completionRate != null) {
                    completionRates.add(completionRate);
                }
                
                // 计算完成时间（从创建到最后确认的时间）
                if (message.getCreateTime() != null && message.getReceivedTime() != null) {
                    long duration = ChronoUnit.MINUTES.between(message.getCreateTime(), message.getReceivedTime());
                    completionTimes.add(duration);
                }
            }

            double avgCompletionRate = completionRates.stream()
                .mapToDouble(Double::doubleValue)
                .average()
                .orElse(0.0);
            
            double avgCompletionTime = completionTimes.stream()
                .mapToLong(Long::longValue)
                .average()
                .orElse(0.0);

            stats.set("avgCompletionRate", Math.round(avgCompletionRate * 100.0) / 100.0);
            stats.set("avgCompletionTime", Math.round(avgCompletionTime * 100.0) / 100.0); // 分钟

            // 趋势分析（按天统计）
            Map<String, Long> dailyStats = messages.stream()
                .collect(Collectors.groupingBy(
                    m -> DateUtil.format(m.getCreateTime(), "yyyy-MM-dd"),
                    Collectors.counting()
                ));
            stats.set("dailyTrend", dailyStats);

            return stats;

        } catch (Exception e) {
            log.error("获取组织消息生命周期统计失败: orgId={}", orgId, e);
            return new JSONObject();
        }
    }

    /**
     * 更新消息状态
     */
    private void updateMessageStatus(Long messageId, String event) {
        try {
            TDeviceMessage message = messageService.getById(messageId);
            if (message == null) return;

            String newStatus = null;
            switch (event) {
                case "created":
                    newStatus = "created";
                    break;
                case "published":
                    newStatus = "published";
                    break;
                case "delivery_completed":
                    newStatus = "delivered";
                    break;
                case "fully_acknowledged":
                    newStatus = "acknowledged";
                    break;
                case "expired":
                    newStatus = "expired";
                    break;
            }

            if (newStatus != null && !newStatus.equals(message.getMessageStatus())) {
                message.setMessageStatus(newStatus);
                messageService.updateById(message);
                
                log.info("更新消息状态: messageId={}, oldStatus={}, newStatus={}", 
                    messageId, message.getMessageStatus(), newStatus);
            }

        } catch (Exception e) {
            log.error("更新消息状态失败: messageId={}, event={}", messageId, event, e);
        }
    }

    /**
     * 清理过期的生命周期缓存
     */
    public void cleanupExpiredLifecycleCache() {
        try {
            log.info("开始清理过期的消息生命周期缓存...");
            
            // 这里可以添加具体的清理逻辑
            // Redis的TTL会自动处理过期数据，这里主要做统计和日志
            
            log.info("消息生命周期缓存清理完成");
            
        } catch (Exception e) {
            log.error("清理消息生命周期缓存失败", e);
        }
    }
}