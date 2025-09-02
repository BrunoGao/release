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

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
* 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.THealthBaselineVO
* @CreateTime 2025-05-04 - 14:13:02
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "THealthBaselineVO", description = "用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 VO 对象")
public class THealthBaselineVO extends BaseVO {

    @Schema(description = "基线记录主键")
    private Long baselineId;

    private String deviceSn;

    @Schema(description = "用户ID，关联用户表")
    private Long userId;

    private String timePeriod;

    private String featureName;

    @Schema(description = "基线周期类型")
    private Object periodType;

    private Float meanValue;

    @Schema(description = "基线周期开始日期")
    private LocalDate periodStart;

    private Float stdValue;

    @Schema(description = "基线周期结束日期")
    private LocalDate periodEnd;

    private Float minValue;

    private Float maxValue;

    private LocalDateTime timestamp;

    @Schema(description = "是否当前有效基线(1=是,0=否)")
    private Integer current;

    @Schema(description = "创建人")
    private String createUser;

    @Schema(description = "记录创建时间")
    private LocalDateTime createTime;

}