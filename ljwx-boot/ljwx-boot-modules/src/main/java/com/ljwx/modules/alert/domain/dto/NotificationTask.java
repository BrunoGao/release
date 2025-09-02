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

package com.ljwx.modules.alert.domain.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 通知任务DTO
 *
 * @Author bruno.gao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.alert.domain.dto.NotificationTask
 * @CreateTime 2024-08-30 - 17:10:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationTask {

    private String taskId;
    private Long alertId;
    private Long recipientId;
    private String recipientType;
    private Integer priority;
    private List<String> channels;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime deliveryDeadline;
    
    private long escalationDelay;
    private String alertType;
    private String alertDesc;
    private String severityLevel;
    private String deviceSn;
    private String userName;
    private String userPhone;
    private String userEmail;
    private String orgName;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;
    
    private String status;
    private int retryCount;
    private Map<String, Object> metadata;
    
    public enum Status {
        PENDING, PROCESSING, DELIVERED, FAILED, EXPIRED
    }
    
    public enum RecipientType {
        MANAGER, MEMBER, ADMIN
    }
    
    public enum Channel {
        SMS, EMAIL, WECHAT_WORK, WECHAT_OFFICIAL, PUSH
    }
}