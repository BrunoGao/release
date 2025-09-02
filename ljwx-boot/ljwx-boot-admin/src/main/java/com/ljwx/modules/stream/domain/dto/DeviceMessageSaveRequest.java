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

import java.util.Map;

/**
 * 设备消息保存请求DTO
 * 
 * 兼容ljwx-bigscreen的DeviceMessage保存格式
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DeviceMessageSaveRequest
 * @CreateTime 2024-12-16
 */
@Data
@Schema(description = "设备消息保存请求")
public class DeviceMessageSaveRequest {

    @Schema(description = "消息ID")
    private String messageId;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "客户ID")
    private String customerId;

    @Schema(description = "组织ID")
    private String orgId;

    @Schema(description = "消息类型（TEXT、IMAGE、AUDIO、VIDEO、COMMAND）")
    private String messageType;

    @Schema(description = "消息内容")
    private String messageContent;

    @Schema(description = "消息标题")
    private String messageTitle;

    @Schema(description = "发送者类型（USER、DEVICE、SYSTEM、ADMIN）")
    private String senderType;

    @Schema(description = "发送者ID")
    private String senderId;

    @Schema(description = "接收者类型（USER、DEVICE、GROUP、BROADCAST）")
    private String receiverType;

    @Schema(description = "接收者ID")
    private String receiverId;

    @Schema(description = "消息优先级（1-5）")
    private Integer priority;

    @Schema(description = "消息状态（DRAFT、PENDING、SENT、DELIVERED、READ、FAILED）")
    private String messageStatus;

    @Schema(description = "创建时间戳")
    private Long createTime;

    @Schema(description = "发送时间戳")
    private Long sendTime;

    @Schema(description = "过期时间戳")
    private Long expireTime;

    @Schema(description = "是否需要确认回执")
    private Boolean requireConfirmation;

    @Schema(description = "消息附件信息")
    private Map<String, Object> attachments;

    @Schema(description = "扩展属性")
    private Map<String, Object> extraAttributes;

    @Schema(description = "消息标签")
    private String[] tags;

    @Schema(description = "相关告警ID")
    private String relatedAlertId;

}