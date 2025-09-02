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

package com.ljwx.modules.customer.domain.dto.health.data.config;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;
import java.math.BigDecimal;
/**
*  编辑更新 DTO 对象
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.customer.domain.dto.health.data.config.THealthDataConfigUpdateDTO
* @CreateTime 2024-12-29 - 15:02:31
*/

@Getter
@Setter
@Schema(name = "THealthDataConfigUpdateDTO", description = " 编辑更新 DTO 对象")
public class THealthDataConfigUpdateDTO implements Serializable {

    @Schema(description = "ID")
    private Long id;
    private Long customerId;
    private String dataType;
    private Integer frequencyInterval;
    private Integer isRealtime;
    private Integer isEnabled;
    private Integer isDefault;
    private String updateUser;
    private BigDecimal weight;
    private BigDecimal warningHigh;
    private BigDecimal warningLow;
    private Integer warningCnt;
}