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

package com.ljwx.modules.health.domain.vo.v2;

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
import java.util.Map;

/**
 * V2消息视图对象
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.v2.TDeviceMessageV2VO
 * @CreateTime 2025-09-10 - 16:10:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "V2消息视图对象")
public class TDeviceMessageV2VO {

    @Schema(description = "消息ID")
    private Long id;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "消息标题")
    private String title;

    @Schema(description = "消息内容")
    private String message;

    @Schema(description = "组织ID")
    private Long orgId;

    @Schema(description = "组织名称")
    private String orgName;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "用户名称")
    private String userName;

    @Schema(description = "租户ID")
    private Long customerId;

    @Schema(description = "租户名称")
    private String customerName;

    @Schema(description = "消息类型")
    private MessageTypeEnum messageType;

    @Schema(description = "消息类型名称")
    private String messageTypeName;

    @Schema(description = "发送者类型")
    private SenderTypeEnum senderType;

    @Schema(description = "发送者类型名称")
    private String senderTypeName;

    @Schema(description = "接收者类型")
    private ReceiverTypeEnum receiverType;

    @Schema(description = "接收者类型名称")
    private String receiverTypeName;

    @Schema(description = "紧急程度")
    private UrgencyEnum urgency;

    @Schema(description = "紧急程度名称")
    private String urgencyName;

    @Schema(description = "消息状态")
    private MessageStatusEnum messageStatus;

    @Schema(description = "消息状态名称")
    private String messageStatusName;

    @Schema(description = "响应数量")
    private Integer respondedNumber;

    @Schema(description = "发送时间")
    private LocalDateTime sentTime;

    @Schema(description = "接收时间")
    private LocalDateTime receivedTime;

    @Schema(description = "优先级")
    private Integer priority;

    @Schema(description = "分发渠道列表")
    private List<String> channels;

    @Schema(description = "是否需要确认")
    private Boolean requireAck;

    @Schema(description = "过期时间")
    private LocalDateTime expiryTime;

    @Schema(description = "是否已过期")
    private Boolean expired;

    @Schema(description = "元数据")
    private Map<String, Object> metadata;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    private LocalDateTime updateTime;

    @Schema(description = "创建人")
    private String createBy;

    @Schema(description = "更新人")
    private String updateBy;

    @Schema(description = "分发详情数量")
    private Long distributionCount;

    @Schema(description = "已确认分发数量")
    private Long acknowledgedCount;

    @Schema(description = "分发成功率")
    private Double distributionSuccessRate;
}