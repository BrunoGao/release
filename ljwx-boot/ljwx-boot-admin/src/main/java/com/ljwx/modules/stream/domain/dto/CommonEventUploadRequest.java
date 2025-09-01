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

package com.ljwx.modules.stream.domain.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 通用事件上传请求DTO
 * 
 * 兼容ljwx-bigscreen的事件格式，用于处理SOS、跌倒检测等紧急事件
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName CommonEventUploadRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "通用事件上传请求")
public class CommonEventUploadRequest {

    @Schema(description = "事件ID")
    private String eventId;

    @Schema(description = "事件类型（SOS、FALL、ABNORMAL_HEART_RATE等）")
    private String eventType;

    @Schema(description = "事件级别（INFO、WARNING、CRITICAL、EMERGENCY）")
    private String eventLevel;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "客户ID")
    private String customerId;

    @Schema(description = "组织ID")
    private String orgId;

    @Schema(description = "事件发生时间戳")
    private Long eventTime;

    @Schema(description = "事件描述")
    private String eventDescription;

    @Schema(description = "事件位置信息")
    private Map<String, Object> location;

    @Schema(description = "相关的健康数据")
    private Map<String, Object> healthData;

    @Schema(description = "事件详细信息")
    private Map<String, Object> eventDetails;

    @Schema(description = "触发条件")
    private Map<String, Object> triggerConditions;

    @Schema(description = "事件状态（PENDING、PROCESSING、RESOLVED、CLOSED）")
    private String eventStatus;

    @Schema(description = "优先级（1-5，数字越小优先级越高）")
    private Integer priority;

    @Schema(description = "是否需要立即通知")
    private Boolean immediateNotification;

    @Schema(description = "通知方式列表")
    private List<String> notificationMethods;

    @Schema(description = "相关联系人")
    private List<String> relatedContacts;

    @Schema(description = "处理超时时间（分钟）")
    private Integer timeoutMinutes;

    @Schema(description = "扩展数据")
    private Map<String, Object> extraData;

    @Schema(description = "事件来源")
    private String eventSource;

    @Schema(description = "批量事件列表")
    private List<CommonEventUploadRequest> batchEvents;

}