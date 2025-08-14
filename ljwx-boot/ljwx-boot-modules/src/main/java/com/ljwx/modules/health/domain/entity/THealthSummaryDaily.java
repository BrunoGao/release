/*
* All Rights Reserved: Copyright [2024] [Zhuang Pan (paynezhuang@gmail.com)]
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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
* 用户每日健康画像汇总表 Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.THealthSummaryDaily
* @CreateTime 2025-05-01 - 21:33:15
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_health_summary_daily")
public class THealthSummaryDaily extends BaseEntity {

    private Long orgId;

    /**
    * 用户ID，关联用户表
    */
    private Long userId;

    /**
    * 健康数据所属日期
    */
    private LocalDate date;

    /**
    * 平均心率
    */
    private Integer avgHeartRate;

    /**
    * 最高心率
    */
    private Integer maxHeartRate;

    /**
    * 最低心率
    */
    private Integer minHeartRate;

    /**
    * 平均收缩压
    */
    private Integer avgPressureHigh;

    /**
    * 平均舒张压
    */
    private Integer avgPressureLow;

    /**
    * 最低血氧
    */
    private Integer minBloodOxygen;

    /**
    * 平均血氧
    */
    private Integer avgBloodOxygen;

    /**
    * 最高体温
    */
    private BigDecimal maxTemperature;

    /**
    * 平均体温
    */
    private BigDecimal avgTemperature;

    /**
    * 平均压力指数
    */
    private Integer avgStress;

    /**
    * 总步数
    */
    private Integer totalStep;

    /**
    * 总运动距离（米）
    */
    private Float totalDistance;

    /**
    * 总消耗卡路里
    */
    private Float totalCalorie;

    /**
    * 总睡眠时长（分钟）
    */
    private Integer sleepDuration;

    /**
    * 深睡时长（分钟）
    */
    private Integer deepSleepDuration;

    /**
    * 睡眠评分（从scientific_sleep_data提取）
    */
    private Integer sleepScore;

    /**
    * 当天告警次数
    */
    private Integer alertCount;

    /**
    * 当天触发的告警类型，如["高心率", "低血氧"]
    */
    private String alertTypes;

    /**
    * 心率得分
    */
    private Integer scoreHeartRate;

    /**
    * 血氧得分
    */
    private Integer scoreBloodOxygen;

    /**
    * 体温得分
    */
    private Integer scoreTemperature;

    /**
    * 压力得分
    */
    private Integer scorePressure;

    /**
    * 睡眠得分
    */
    private Integer scoreSleep;

    /**
    * 步数得分
    */
    private Integer scoreStep;

    /**
    * 里程得分
    */
    private Integer scoreDistance;

    /**
    * 卡路里得分
    */
    private Integer scoreCalorie;

    /**
    * 健康总分（加权平均）
    */
    private BigDecimal healthScore;

    /**
    * 健康等级，如A/B/C/D
    */
    private String healthLevel;

}