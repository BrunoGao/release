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

package com.ljwx.modules.alert.service.queue;

import com.ljwx.modules.alert.domain.dto.NotificationTask;
import com.ljwx.infrastructure.util.RedisUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * 智能优先级消息队列
 * 基于Redis实现的高性能告警通知队列系统
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.queue.PriorityMessageQueue
 * @CreateTime 2024-08-30 - 17:00:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PriorityMessageQueue {

    private final ObjectMapper objectMapper;
    
    private static final int PRIORITY_LEVELS = 10;
    private static final String QUEUE_PREFIX = "notification_queue:priority_";
    private static final String DEDUP_PREFIX = "notification_dedup:";
    private static final String STATS_PREFIX = "notification_stats:";
    
    private final Map<String, Long> dedupCache = new ConcurrentHashMap<>();

    /**
     * 批量入队通知任务
     */
    public int enqueueBatch(List<NotificationTask> notificationTasks) {
        if (notificationTasks == null || notificationTasks.isEmpty()) {
            return 0;
        }
        
        log.info("开始批量入队通知任务: size={}", notificationTasks.size());
        long startTime = System.currentTimeMillis();
        
        List<NotificationTask> processedTasks = new ArrayList<>();
        int duplicateCount = 0;
        
        for (NotificationTask task : notificationTasks) {
            try {
                // 消息去重检查
                if (isDuplicate(task)) {
                    duplicateCount++;
                    log.debug("检测到重复消息: alertId={}, recipientId={}", 
                            task.getAlertId(), task.getRecipientId());
                    continue;
                }
                
                // 消息优化
                NotificationTask optimizedTask = optimizeTask(task);
                processedTasks.add(optimizedTask);
                
                // 按优先级入队
                String queueKey = QUEUE_PREFIX + task.getPriority();
                String taskJson = objectMapper.writeValueAsString(optimizedTask);
                
                RedisUtil.lSet(queueKey, taskJson);
                
                // 更新去重缓存
                updateDedupCache(task);
                
            } catch (Exception e) {
                log.error("处理通知任务时出错: alertId={}, recipientId={}", 
                        task.getAlertId(), task.getRecipientId(), e);
            }
        }
        
        // 更新统计信息
        updateQueueStats(processedTasks.size(), duplicateCount);
        
        long processingTime = System.currentTimeMillis() - startTime;
        log.info("批量入队完成: 总数={}, 处理={}, 重复={}, 耗时={}ms", 
                notificationTasks.size(), processedTasks.size(), duplicateCount, processingTime);
        
        return processedTasks.size();
    }

    /**
     * 批量出队处理
     */
    public List<NotificationTask> dequeueBatch(int batchSize) {
        if (batchSize <= 0) {
            batchSize = 50;
        }
        
        List<NotificationTask> tasks = new ArrayList<>();
        
        // 按优先级顺序处理
        for (int priority = 1; priority <= PRIORITY_LEVELS; priority++) {
            String queueKey = QUEUE_PREFIX + priority;
            
            int remaining = batchSize - tasks.size();
            if (remaining <= 0) {
                break;
            }
            
            // 批量获取任务
            List<Object> taskJsons = RedisUtil.lGet(queueKey, 0, remaining - 1);
            
            if (!taskJsons.isEmpty()) {
                // 从队列中移除已取出的任务
                for (int i = 0; i < taskJsons.size(); i++) {
                    RedisUtil.lRemove(queueKey, 1, taskJsons.get(i));
                }
                
                // 反序列化任务
                for (Object taskJson : taskJsons) {
                    try {
                        NotificationTask task = objectMapper.readValue(
                                taskJson.toString(), NotificationTask.class);
                        tasks.add(task);
                    } catch (Exception e) {
                        log.error("反序列化通知任务失败: {}", taskJson, e);
                    }
                }
                
                log.debug("从优先级{}队列出队{}个任务", priority, taskJsons.size());
            }
        }
        
        if (!tasks.isEmpty()) {
            log.info("批量出队完成: size={}", tasks.size());
        }
        
        return tasks;
    }

    /**
     * 获取队列状态统计
     */
    public Map<String, Object> getQueueStats() {
        Map<String, Object> stats = new HashMap<>();
        Map<Integer, Long> queueLengths = new HashMap<>();
        long totalLength = 0;
        
        // 统计各优先级队列长度
        for (int priority = 1; priority <= PRIORITY_LEVELS; priority++) {
            String queueKey = QUEUE_PREFIX + priority;
            Long length = RedisUtil.lGetSize(queueKey);
            queueLengths.put(priority, length);
            totalLength += length;
        }
        
        stats.put("queueLengths", queueLengths);
        stats.put("totalLength", totalLength);
        stats.put("priorityLevels", PRIORITY_LEVELS);
        
        // 从Redis获取处理统计
        Object processedCount = RedisUtil.get(STATS_PREFIX + "processed_count");
        Object duplicateCount = RedisUtil.get(STATS_PREFIX + "duplicate_count");
        
        stats.put("processedCount", processedCount != null ? processedCount : 0);
        stats.put("duplicateCount", duplicateCount != null ? duplicateCount : 0);
        
        return stats;
    }

    /**
     * 清理过期的去重缓存
     */
    public void cleanExpiredDedupCache() {
        try {
            Set<String> expiredKeys = RedisUtil.getKeysByPrefix(DEDUP_PREFIX + "*");
            List<String> toDelete = new ArrayList<>();
            
            for (String key : expiredKeys) {
                Long ttl = RedisUtil.getExpire(key);
                if (ttl != null && ttl <= 0) {
                    toDelete.add(key);
                }
            }
            
            if (!toDelete.isEmpty()) {
                RedisUtil.del(toDelete);
                log.info("清理过期去重缓存: count={}", toDelete.size());
            }
            
        } catch (Exception e) {
            log.error("清理去重缓存失败", e);
        }
    }

    /**
     * 检查消息是否重复
     */
    private boolean isDuplicate(NotificationTask task) {
        String dedupKey = DEDUP_PREFIX + task.getAlertId() + ":" + task.getRecipientId();
        return RedisUtil.exists(dedupKey);
    }

    /**
     * 更新去重缓存
     */
    private void updateDedupCache(NotificationTask task) {
        String dedupKey = DEDUP_PREFIX + task.getAlertId() + ":" + task.getRecipientId();
        // 设置15分钟过期，防止短时间内重复通知
        RedisUtil.set(dedupKey, "1", 15 * 60);
    }

    /**
     * 优化通知任务
     */
    private NotificationTask optimizeTask(NotificationTask task) {
        // 这里可以进行消息压缩、格式优化等处理
        // 目前返回原任务
        return task;
    }

    /**
     * 更新队列统计
     */
    private void updateQueueStats(int processedCount, int duplicateCount) {
        try {
            if (processedCount > 0) {
                RedisUtil.incr(STATS_PREFIX + "processed_count", processedCount);
            }
            if (duplicateCount > 0) {
                RedisUtil.incr(STATS_PREFIX + "duplicate_count", duplicateCount);
            }
        } catch (Exception e) {
            log.error("更新队列统计失败", e);
        }
    }
}