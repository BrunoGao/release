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

package com.ljwx.modules.alert.service.notification;

import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import com.ljwx.modules.alert.domain.dto.PriorityInfo;
import com.ljwx.modules.alert.domain.dto.NotificationTask;
import com.ljwx.modules.alert.domain.dto.DistributionResult;
import com.ljwx.modules.alert.service.queue.PriorityMessageQueue;
import com.ljwx.modules.alert.service.channel.NotificationChannelManager;
import com.ljwx.modules.alert.service.tracking.DeliveryTracker;
import com.ljwx.modules.system.domain.dto.OrgHierarchyInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Async;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 统一通知分发中心
 * 负责告警消息的智能分发和处理
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.notification.NotificationHub
 * @CreateTime 2024-08-30 - 17:20:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationHub {

    private final PriorityMessageQueue messageQueue;
    private final NotificationChannelManager channelManager;
    private final DeliveryTracker deliveryTracker;

    /**
     * 统一告警分发
     */
    public DistributionResult distributeAlert(AnalyzedAlert alert, 
                                            List<OrgHierarchyInfo> orgHierarchy, 
                                            PriorityInfo priorityInfo) {
        
        log.info("开始告警分发: alertId={}, recipientCount={}", 
                alert.getAlertId(), orgHierarchy.size());
        
        long startTime = System.currentTimeMillis();
        String distributionId = generateDistributionId();
        
        try {
            // 1. 创建分发计划
            DistributionPlan distributionPlan = createDistributionPlan(
                    alert, orgHierarchy, priorityInfo);
            
            // 2. 生成通知任务
            List<NotificationTask> notificationTasks = generateNotificationTasks(
                    alert, distributionPlan);
            
            // 3. 批量入队
            int enqueuedCount = messageQueue.enqueueBatch(notificationTasks);
            
            // 4. 异步处理通知
            processNotificationsAsync(notificationTasks);
            
            // 5. 记录分发跟踪信息
            deliveryTracker.recordDistribution(distributionId, alert, notificationTasks);
            
            long processingTime = System.currentTimeMillis() - startTime;
            
            DistributionResult result = DistributionResult.builder()
                    .distributionId(distributionId)
                    .totalRecipients(enqueuedCount)
                    .estimatedDeliveryTime(calculateEstimatedDelivery(distributionPlan))
                    .trackingUrl("/api/alerts/" + alert.getAlertId() + "/tracking")
                    .build();
            
            log.info("告警分发完成: distributionId={}, recipients={}, time={}ms", 
                    distributionId, enqueuedCount, processingTime);
            
            return result;
            
        } catch (Exception e) {
            log.error("告警分发失败: alertId={}", alert.getAlertId(), e);
            throw new RuntimeException("告警分发失败: " + e.getMessage(), e);
        }
    }

    /**
     * 创建分发计划
     */
    private DistributionPlan createDistributionPlan(AnalyzedAlert alert, 
                                                  List<OrgHierarchyInfo> orgHierarchy, 
                                                  PriorityInfo priorityInfo) {
        
        Map<Integer, List<OrgHierarchyInfo>> recipientsByLevel = orgHierarchy.stream()
                .collect(Collectors.groupingBy(OrgHierarchyInfo::getDepth));
        
        Map<Integer, Long> escalationDelays = new HashMap<>();
        
        for (Integer level : recipientsByLevel.keySet()) {
            escalationDelays.put(level, calculateEscalationDelay(level, priorityInfo.getPriority()));
        }
        
        return DistributionPlan.builder()
                .id(generateDistributionId())
                .recipientsByLevel(recipientsByLevel)
                .escalationDelays(escalationDelays)
                .estimatedDelivery(calculateTotalEstimatedDelivery(recipientsByLevel))
                .build();
    }

    /**
     * 生成通知任务
     */
    private List<NotificationTask> generateNotificationTasks(AnalyzedAlert alert, 
                                                           DistributionPlan plan) {
        
        List<NotificationTask> tasks = new ArrayList<>();
        
        for (Map.Entry<Integer, List<OrgHierarchyInfo>> entry : plan.getRecipientsByLevel().entrySet()) {
            Integer level = entry.getKey();
            List<OrgHierarchyInfo> recipients = entry.getValue();
            Long escalationDelay = plan.getEscalationDelays().get(level);
            
            for (OrgHierarchyInfo recipient : recipients) {
                NotificationTask task = NotificationTask.builder()
                        .taskId(UUID.randomUUID().toString())
                        .alertId(alert.getAlertId())
                        .recipientId(recipient.getUserId())
                        .recipientType(determineRecipientType(recipient))
                        .priority(calculateTaskPriority(alert, level))
                        .channels(selectChannels(alert, recipient))
                        .deliveryDeadline(LocalDateTime.now().plusMinutes(escalationDelay))
                        .escalationDelay(escalationDelay)
                        .alertType(alert.getAlertType())
                        .alertDesc(alert.getAlertDesc())
                        .severityLevel(alert.getSeverityLevel())
                        .deviceSn(alert.getDeviceSn())
                        .userName(recipient.getUserName())
                        .userPhone(recipient.getPhone())
                        .userEmail(recipient.getEmail())
                        .orgName(recipient.getOrgName())
                        .createdAt(LocalDateTime.now())
                        .status(NotificationTask.Status.PENDING.name())
                        .retryCount(0)
                        .metadata(createTaskMetadata(alert, recipient, level))
                        .build();
                
                tasks.add(task);
            }
        }
        
        return tasks;
    }

    /**
     * 异步处理通知
     */
    @Async("alertNotificationExecutor")
    public void processNotificationsAsync(List<NotificationTask> tasks) {
        log.info("开始异步处理通知任务: count={}", tasks.size());
        
        // 这里将启动异步处理逻辑
        // 实际的通知发送由独立的消费者处理
        channelManager.scheduleNotifications(tasks);
    }

    private String generateDistributionId() {
        return "DIST_" + System.currentTimeMillis() + "_" + 
               UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    private long calculateEscalationDelay(Integer level, Integer priority) {
        // 根据层级和优先级计算升级延迟时间
        int baseDelay = switch (priority) {
            case 1, 2 -> 5;   // 紧急：5分钟
            case 3, 4 -> 15;  // 重要：15分钟
            case 5, 6 -> 30;  // 普通：30分钟
            default -> 60;    // 低优先级：60分钟
        };
        
        return baseDelay + (level * 5); // 每层级增加5分钟
    }

    private long calculateEstimatedDelivery(DistributionPlan plan) {
        return plan.getRecipientsByLevel().values().stream()
                .mapToLong(List::size)
                .sum() * 2; // 预计每个接收者2秒处理时间
    }

    private long calculateTotalEstimatedDelivery(Map<Integer, List<OrgHierarchyInfo>> recipientsByLevel) {
        return recipientsByLevel.values().stream()
                .mapToLong(List::size)
                .sum() * 2;
    }

    private String determineRecipientType(OrgHierarchyInfo recipient) {
        return "1".equals(recipient.getPrincipal()) ? 
               NotificationTask.RecipientType.MANAGER.name() : 
               NotificationTask.RecipientType.MEMBER.name();
    }

    private Integer calculateTaskPriority(AnalyzedAlert alert, Integer level) {
        // 根据告警优先级和组织层级计算任务优先级
        int alertPriority = switch (alert.getSeverityLevel()) {
            case "CRITICAL" -> 1;
            case "HIGH" -> 2;
            case "MEDIUM" -> 3;
            case "LOW" -> 4;
            default -> 5;
        };
        
        return Math.max(1, alertPriority - level); // 层级越高，优先级越高
    }

    private List<String> selectChannels(AnalyzedAlert alert, OrgHierarchyInfo recipient) {
        List<String> channels = new ArrayList<>();
        
        // 根据告警严重级别和接收者信息选择通知渠道
        switch (alert.getSeverityLevel()) {
            case "CRITICAL":
                channels.addAll(List.of("SMS", "WECHAT_WORK", "EMAIL"));
                break;
            case "HIGH":
                channels.addAll(List.of("WECHAT_WORK", "EMAIL"));
                break;
            default:
                channels.add("EMAIL");
                break;
        }
        
        return channels;
    }

    private Map<String, Object> createTaskMetadata(AnalyzedAlert alert, 
                                                 OrgHierarchyInfo recipient, 
                                                 Integer level) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("orgLevel", level);
        metadata.put("orgDepth", recipient.getDepth());
        metadata.put("confidenceScore", alert.getConfidenceScore());
        metadata.put("autoProcessable", alert.isAutoProcessable());
        return metadata;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    private static class DistributionPlan {
        private String id;
        private Map<Integer, List<OrgHierarchyInfo>> recipientsByLevel;
        private Map<Integer, Long> escalationDelays;
        private long estimatedDelivery;
    }
}