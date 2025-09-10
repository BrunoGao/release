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

package com.ljwx.modules.health.domain.dto.v2.message;

import com.ljwx.modules.health.domain.enums.MessageStatusEnum;
import com.ljwx.modules.health.domain.enums.MessageTypeEnum;
import com.ljwx.modules.health.domain.enums.ReceiverTypeEnum;
import com.ljwx.modules.health.domain.enums.SenderTypeEnum;
import com.ljwx.modules.health.domain.enums.UrgencyEnum;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * V2消息查询DTO
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.v2.message.MessageQueryV2DTO
 * @CreateTime 2025-09-10 - 16:00:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "V2消息查询DTO")
public class MessageQueryV2DTO {

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "消息关键词")
    private String keyword;

    @Schema(description = "组织ID")
    private Long orgId;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "租户ID")
    private Long customerId;

    @Schema(description = "消息类型")
    private MessageTypeEnum messageType;

    @Schema(description = "消息类型列表")
    private List<MessageTypeEnum> messageTypes;

    @Schema(description = "发送者类型")
    private SenderTypeEnum senderType;

    @Schema(description = "接收者类型")
    private ReceiverTypeEnum receiverType;

    @Schema(description = "紧急程度")
    private UrgencyEnum urgency;

    @Schema(description = "消息状态")
    private MessageStatusEnum messageStatus;

    @Schema(description = "消息状态列表")
    private List<MessageStatusEnum> messageStatuses;

    @Schema(description = "优先级最小值")
    private Integer minPriority;

    @Schema(description = "优先级最大值")
    private Integer maxPriority;

    @Schema(description = "是否需要确认")
    private Boolean requireAck;

    @Schema(description = "开始发送时间")
    private LocalDateTime startSentTime;

    @Schema(description = "结束发送时间")
    private LocalDateTime endSentTime;

    @Schema(description = "开始接收时间")
    private LocalDateTime startReceivedTime;

    @Schema(description = "结束接收时间")
    private LocalDateTime endReceivedTime;

    @Schema(description = "开始创建时间")
    private LocalDateTime startCreateTime;

    @Schema(description = "结束创建时间")
    private LocalDateTime endCreateTime;

    @Schema(description = "分发渠道")
    private String channel;

    @Schema(description = "是否已过期")
    private Boolean expired;

    @Schema(description = "页码", example = "1")
    private Integer pageNum = 1;

    @Schema(description = "每页大小", example = "10")
    private Integer pageSize = 10;

    @Schema(description = "排序字段", example = "createTime")
    private String sortBy = "createTime";

    @Schema(description = "排序方式", example = "desc")
    private String sortOrder = "desc";
}