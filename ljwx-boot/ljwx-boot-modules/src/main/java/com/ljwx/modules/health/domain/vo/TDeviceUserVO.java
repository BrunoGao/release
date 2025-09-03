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

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

/**
* 设备与用户关联表 VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.TDeviceUserVO
* @CreateTime 2025-01-03 - 15:12:29
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TDeviceUserVO", description = "设备与用户关联表 VO 对象")
public class TDeviceUserVO extends BaseVO {
    /**
     * 组织ID
     */
    private Long orgId;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "用户ID")
    private String userId;

    @Schema(description = "用户名")
    private String userName;

    @Schema(description = "操作时间")
    private LocalDateTime operateTime;

    @Schema(description = "绑定状态 (BIND:绑定, UNBIND:解绑)")
    private Object status;

    @Schema(description = "创建用户")
    private String createUser;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}