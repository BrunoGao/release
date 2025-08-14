/*
* All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.geofence.domain.vo;

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

/**
*  VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.geofence.domain.vo.TGeofenceVO
* @CreateTime 2025-01-07 - 19:44:06
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TGeofenceVO", description = " VO 对象")
public class TGeofenceVO extends BaseVO {

    @Schema(description = "电子围栏名称")
    private String name;

    @Schema(description = "围栏区域")
    private String area;

    @Schema(description = "围栏描述")
    private String description;

    @Schema(description = "围栏状态")
    private String status;

    @Schema(description = "创建用户")
    private String createUser;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}