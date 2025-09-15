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

package com.ljwx.modules.health.domain.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * V2消息摘要视图对象
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.v2.MessageSummaryVO
 * @CreateTime 2025-09-10 - 16:10:00
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "V2消息摘要视图对象")
public class MessageSummaryVO {

    @Schema(description = "今日消息总数")
    private Long todayTotal;

    @Schema(description = "今日新增消息数")
    private Long todayNew;

    @Schema(description = "今日发送消息数")
    private Long todaySent;

    @Schema(description = "今日确认消息数")
    private Long todayAcknowledged;

    @Schema(description = "今日失败消息数")
    private Long todayFailed;

    @Schema(description = "本周消息总数")
    private Long weekTotal;

    @Schema(description = "本周新增消息数")
    private Long weekNew;

    @Schema(description = "本月消息总数")
    private Long monthTotal;

    @Schema(description = "本月新增消息数")
    private Long monthNew;

    @Schema(description = "待处理紧急消息数")
    private Long pendingUrgentMessages;

    @Schema(description = "待处理高优先级消息数")
    private Long pendingHighPriorityMessages;

    @Schema(description = "即将过期消息数")
    private Long expiringSoonMessages;

    @Schema(description = "活跃设备数")
    private Long activeDeviceCount;

    @Schema(description = "活跃组织数")
    private Long activeOrgCount;

    @Schema(description = "消息发送成功率")
    private Double overallSuccessRate;

    @Schema(description = "平均响应时间(秒)")
    private Double averageResponseTime;

    @Schema(description = "系统健康状态")
    private String systemHealthStatus;

    @Schema(description = "统计时间")
    private LocalDateTime statisticsTime;
}