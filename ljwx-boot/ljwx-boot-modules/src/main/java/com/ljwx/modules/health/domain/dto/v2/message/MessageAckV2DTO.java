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

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 消息确认V2 DTO
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.v2.message.MessageAckV2DTO
 * @CreateTime 2025-09-10 - 17:00:00
 */
@Data
@Schema(description = "消息确认V2DTO")
public class MessageAckV2DTO implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 消息ID
     */
    @Schema(description = "消息ID", example = "123456")
    @NotNull(message = "消息ID不能为空")
    private Long messageId;

    /**
     * 目标ID (设备序列号或用户ID)
     */
    @Schema(description = "目标ID", example = "DEVICE001 或 USER001")
    @NotNull(message = "目标ID不能为空")
    private String targetId;

    /**
     * 确认渠道
     */
    @Schema(description = "确认渠道", example = "message", allowableValues = {"message", "push", "wechat", "watch"})
    private String channel;

    /**
     * 确认时间
     */
    @Schema(description = "确认时间")
    private LocalDateTime ackTime;

    /**
     * 确认备注
     */
    @Schema(description = "确认备注", example = "用户已阅读消息")
    private String remark;
}