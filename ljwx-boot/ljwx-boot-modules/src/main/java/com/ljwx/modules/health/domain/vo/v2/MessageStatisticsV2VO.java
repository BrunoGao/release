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

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

/**
 * V2消息统计视图对象
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.v2.MessageStatisticsV2VO
 * @CreateTime 2025-09-10 - 16:10:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "V2消息统计视图对象")
public class MessageStatisticsV2VO {

    @Schema(description = "总消息数")
    private Long totalMessages;

    @Schema(description = "已发送消息数")
    private Long sentMessages;

    @Schema(description = "已接收消息数")
    private Long receivedMessages;

    @Schema(description = "已确认消息数")
    private Long acknowledgedMessages;

    @Schema(description = "失败消息数")
    private Long failedMessages;

    @Schema(description = "过期消息数")
    private Long expiredMessages;

    @Schema(description = "待处理消息数")
    private Long pendingMessages;

    @Schema(description = "发送成功率")
    private Double sendSuccessRate;

    @Schema(description = "接收成功率")
    private Double receiveSuccessRate;

    @Schema(description = "确认成功率")
    private Double acknowledgeSuccessRate;

    @Schema(description = "平均响应时间(秒)")
    private Double averageResponseTime;

    @Schema(description = "按消息类型统计")
    private Map<String, Long> messageTypeStats;

    @Schema(description = "按发送者类型统计")
    private Map<String, Long> senderTypeStats;

    @Schema(description = "按接收者类型统计")
    private Map<String, Long> receiverTypeStats;

    @Schema(description = "按紧急程度统计")
    private Map<String, Long> urgencyStats;

    @Schema(description = "按消息状态统计")
    private Map<String, Long> messageStatusStats;

    @Schema(description = "按分发渠道统计")
    private Map<String, Long> channelStats;

    @Schema(description = "按组织统计")
    private Map<String, Long> orgStats;

    @Schema(description = "按设备统计")
    private Map<String, Long> deviceStats;

    @Schema(description = "每日统计")
    private Map<String, Long> dailyStats;

    @Schema(description = "每小时统计")
    private Map<String, Long> hourlyStats;

    // V1兼容性方法
    public Long getDeliveredCount() {
        return this.receivedMessages;
    }

    public Long getAcknowledgedCount() {
        return this.acknowledgedMessages;
    }

    public Long getFailedCount() {
        return this.failedMessages;
    }

    public Double getDeliveryRate() {
        return this.receiveSuccessRate;
    }

    public Double getAcknowledgmentRate() {
        return this.acknowledgeSuccessRate;
    }
}