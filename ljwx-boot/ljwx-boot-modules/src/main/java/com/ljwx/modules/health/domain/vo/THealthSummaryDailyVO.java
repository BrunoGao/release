/*
* All Rights Reserved: Copyright [2024] [ljwx (paynezhuang@gmail.com)]
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

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
* 用户每日健康画像汇总表 VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.THealthSummaryDailyVO
* @CreateTime 2025-05-01 - 21:33:15
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "THealthSummaryDailyVO", description = "用户每日健康画像汇总表 VO 对象")
public class THealthSummaryDailyVO extends BaseVO {

    private Long orgId;

    @Schema(description = "用户ID，关联用户表")
    private Long userId;

    @Schema(description = "健康数据所属日期")
    private LocalDate date;

    @Schema(description = "平均心率")
    private Integer avgHeartRate;

    @Schema(description = "最高心率")
    private Integer maxHeartRate;

    @Schema(description = "最低心率")
    private Integer minHeartRate;

    @Schema(description = "平均收缩压")
    private Integer avgPressureHigh;

    @Schema(description = "平均舒张压")
    private Integer avgPressureLow;

    @Schema(description = "最低血氧")
    private Integer minBloodOxygen;

    @Schema(description = "平均血氧")
    private Integer avgBloodOxygen;

    @Schema(description = "最高体温")
    private BigDecimal maxTemperature;

    @Schema(description = "平均体温")
    private BigDecimal avgTemperature;

    @Schema(description = "平均压力指数")
    private Integer avgStress;

    @Schema(description = "总步数")
    private Integer totalStep;

    @Schema(description = "总运动距离（米）")
    private Float totalDistance;

    @Schema(description = "总消耗卡路里")
    private Float totalCalorie;

    @Schema(description = "总睡眠时长（分钟）")
    private Integer sleepDuration;

    @Schema(description = "深睡时长（分钟）")
    private Integer deepSleepDuration;

    @Schema(description = "睡眠评分（从scientific_sleep_data提取）")
    private Integer sleepScore;

    @Schema(description = "当天告警次数")
    private Integer alertCount;

    @Schema(description = "当天触发的告警类型")
    private Object alertTypes;

    @Schema(description = "心率得分")
    private Integer scoreHeartRate;

    @Schema(description = "血氧得分")
    private Integer scoreBloodOxygen;

    @Schema(description = "体温得分")
    private Integer scoreTemperature;

    @Schema(description = "压力得分")
    private Integer scorePressure;

    @Schema(description = "睡眠得分")
    private Integer scoreSleep;

    @Schema(description = "步数得分")
    private Integer scoreStep;

    @Schema(description = "里程得分")
    private Integer scoreDistance;

    @Schema(description = "卡路里得分")
    private Integer scoreCalorie;

    @Schema(description = "健康总分（加权平均）")
    private BigDecimal healthScore;

    @Schema(description = "健康等级，如A/B/C/D")
    private String healthLevel;

    @Schema(description = "创建人名称")
    private String createUser;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}