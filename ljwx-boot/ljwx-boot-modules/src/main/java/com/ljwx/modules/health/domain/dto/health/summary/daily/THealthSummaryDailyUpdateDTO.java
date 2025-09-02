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

package com.ljwx.modules.health.domain.dto.health.summary.daily;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;

/**
* 用户每日健康画像汇总表 编辑更新 DTO 对象
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.dto.health.summary.daily.THealthSummaryDailyUpdateDTO
* @CreateTime 2025-05-01 - 21:33:15
*/

@Getter
@Setter
@Schema(name = "THealthSummaryDailyUpdateDTO", description = "用户每日健康画像汇总表 编辑更新 DTO 对象")
public class THealthSummaryDailyUpdateDTO implements Serializable {

    @Schema(description = "ID")
    private Long id;

}