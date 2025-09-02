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

package com.ljwx.modules.alert.service.tracking;

import com.ljwx.modules.alert.domain.dto.AnalyzedAlert;
import com.ljwx.modules.alert.domain.dto.NotificationTask;
import com.ljwx.infrastructure.util.RedisUtil;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 投递跟踪器
 * 负责记录和跟踪通知投递状态
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.service.tracking.DeliveryTracker
 * @CreateTime 2024-08-30 - 17:45:00
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeliveryTracker {

    private final ObjectMapper objectMapper;
    
    private static final String TRACKING_PREFIX = "alert_tracking:";
    private static final int TRACKING_EXPIRE_DAYS = 7; // 跟踪信息保留7天

    /**
     * 记录分发信息
     */
    public void recordDistribution(String distributionId, 
                                 AnalyzedAlert alert, 
                                 List<NotificationTask> tasks) {
        try {
            Map<String, Object> trackingInfo = new HashMap<>();
            trackingInfo.put("distributionId", distributionId);
            trackingInfo.put("alertId", alert.getAlertId());
            trackingInfo.put("alertType", alert.getAlertType());
            trackingInfo.put("severityLevel", alert.getSeverityLevel());
            trackingInfo.put("totalRecipients", tasks.size());
            trackingInfo.put("createdAt", LocalDateTime.now().toString());
            trackingInfo.put("status", "DISTRIBUTED");
            
            Map<String, Object> taskSummary = new HashMap<>();
            for (NotificationTask task : tasks) {
                taskSummary.put(task.getTaskId(), Map.of(
                        "recipientId", task.getRecipientId(),
                        "channels", task.getChannels(),
                        "priority", task.getPriority(),
                        "status", task.getStatus()
                ));
            }
            trackingInfo.put("tasks", taskSummary);
            
            String trackingKey = TRACKING_PREFIX + distributionId;
            String trackingJson = objectMapper.writeValueAsString(trackingInfo);
            
            // 设置7天过期时间
            RedisUtil.set(trackingKey, trackingJson, TRACKING_EXPIRE_DAYS * 24 * 60 * 60);
            
            log.info("记录分发跟踪信息: distributionId={}, taskCount={}", 
                    distributionId, tasks.size());
            
        } catch (Exception e) {
            log.error("记录分发跟踪信息失败: distributionId={}", distributionId, e);
        }
    }

    /**
     * 获取跟踪信息
     */
    public Map<String, Object> getTrackingInfo(String distributionId) {
        try {
            String trackingKey = TRACKING_PREFIX + distributionId;
            String trackingJson = (String) RedisUtil.get(trackingKey);
            
            if (trackingJson != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> trackingInfo = objectMapper.readValue(
                        trackingJson, Map.class);
                return trackingInfo;
            }
            
            return null;
        } catch (Exception e) {
            log.error("获取跟踪信息失败: distributionId={}", distributionId, e);
            return null;
        }
    }
}