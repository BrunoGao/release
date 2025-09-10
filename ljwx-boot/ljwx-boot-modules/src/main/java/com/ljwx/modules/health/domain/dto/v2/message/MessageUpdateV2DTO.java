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

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * V2消息更新DTO
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.v2.message.MessageUpdateV2DTO
 * @CreateTime 2025-09-10 - 16:00:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "V2消息更新DTO")
public class MessageUpdateV2DTO {

    @Schema(description = "消息ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotNull(message = "消息ID不能为空")
    private Long id;

    @Schema(description = "消息标题")
    @Size(max = 200, message = "消息标题长度不能超过200个字符")
    private String title;

    @Schema(description = "消息内容")
    @Size(max = 2000, message = "消息内容长度不能超过2000个字符")
    private String message;

    @Schema(description = "消息类型")
    private MessageTypeEnum messageType;

    @Schema(description = "发送者类型")
    private SenderTypeEnum senderType;

    @Schema(description = "接收者类型")
    private ReceiverTypeEnum receiverType;

    @Schema(description = "紧急程度")
    private UrgencyEnum urgency;

    @Schema(description = "消息状态")
    private MessageStatusEnum messageStatus;

    @Schema(description = "响应数量")
    private Integer respondedNumber;

    @Schema(description = "发送时间")
    private LocalDateTime sentTime;

    @Schema(description = "接收时间")
    private LocalDateTime receivedTime;

    @Schema(description = "优先级(1-5)")
    private Integer priority;

    @Schema(description = "分发渠道列表")
    private List<String> channels;

    @Schema(description = "是否需要确认")
    private Boolean requireAck;

    @Schema(description = "过期时间")
    private LocalDateTime expiryTime;

    @Schema(description = "元数据")
    private Map<String, Object> metadata;
}