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

package com.ljwx.modules.health.domain.dto.health.baseline;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;

/**
* 用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 查询 DTO 对象
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.dto.health.baseline.THealthBaselineSearchDTO
* @CreateTime 2025-05-04 - 14:13:02
*/

@Getter
@Setter
@Schema(name = "THealthBaselineSearchDTO", description = "用户健康基线表：支持按日/周/月/年记录每个体征的基线统计值 查询 DTO 对象")
public class THealthBaselineSearchDTO implements Serializable {

}