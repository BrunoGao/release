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
 * 设备消息发送请求DTO
 * 
 * 兼容ljwx-bigscreen的DeviceMessage发送格式
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DeviceMessageSendRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "设备消息发送请求")
public class DeviceMessageSendRequest {

    @Schema(description = "目标设备序列号")
    private String targetDeviceSn;

    @Schema(description = "目标用户ID")
    private String targetUserId;

    @Schema(description = "目标组织ID")
    private String targetOrgId;

    @Schema(description = "消息类型（TEXT、IMAGE、AUDIO、VIDEO、COMMAND、NOTIFICATION）")
    private String messageType;

    @Schema(description = "消息内容")
    private String messageContent;

    @Schema(description = "消息标题")
    private String messageTitle;

    @Schema(description = "发送者ID")
    private String senderId;

    @Schema(description = "发送者类型（USER、DEVICE、SYSTEM、ADMIN）")
    private String senderType;

    @Schema(description = "消息优先级（1-5，数字越小优先级越高）")
    private Integer priority;

    @Schema(description = "是否立即发送")
    private Boolean immediate;

    @Schema(description = "定时发送时间戳")
    private Long scheduledTime;

    @Schema(description = "消息过期时间戳")
    private Long expireTime;

    @Schema(description = "是否需要送达回执")
    private Boolean requireDeliveryReceipt;

    @Schema(description = "是否需要阅读回执")
    private Boolean requireReadReceipt;

    @Schema(description = "重试次数")
    private Integer retryCount;

    @Schema(description = "发送渠道（DEVICE、WEBSOCKET、PUSH、SMS、EMAIL）")
    private List<String> sendChannels;

    @Schema(description = "目标设备列表（批量发送）")
    private List<String> targetDevices;

    @Schema(description = "目标用户列表（批量发送）")
    private List<String> targetUsers;

    @Schema(description = "消息模板ID")
    private String templateId;

    @Schema(description = "模板参数")
    private Map<String, Object> templateParams;

    @Schema(description = "附件信息")
    private Map<String, Object> attachments;

    @Schema(description = "扩展属性")
    private Map<String, Object> extraAttributes;

    @Schema(description = "消息标签")
    private String[] tags;

    @Schema(description = "客户ID")
    private String customerId;

}