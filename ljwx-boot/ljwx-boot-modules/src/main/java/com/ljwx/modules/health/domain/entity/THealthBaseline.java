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

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
* 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.THealthBaseline
* @CreateTime 2025-05-04 - 14:13:02
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_health_baseline")
public class THealthBaseline extends BaseEntity {

    /**
    * 基线记录主键
    */
    private Long baselineId;

    /**
    * 用户ID，关联用户表
    */
    private Long userId;

    /**
    * 设备序列号
    */
    private String deviceSn;

    /**
    * 基线周期类型
    */
    private String periodType;

    /**
    * 基线周期开始日期
    */
    private LocalDate periodStart;

    /**
    * 基线周期结束日期
    */
    private LocalDate periodEnd;

    /**
    * 体征名称，如 heart_rate/blood_oxygen
    */
    private String featureName;

    /**
    * 该期平均值
    */
    private BigDecimal meanValue;

    /**
    * 该期标准差
    */
    private BigDecimal stdValue;

    /**
    * 该期最小值
    */
    private BigDecimal minValue;

    /**
    * 该期最大值
    */
    private BigDecimal maxValue;

    /**
    * 是否当前有效基线(1=是,0=否)
    */
    @TableField("is_current")
    private Boolean rrent;

}