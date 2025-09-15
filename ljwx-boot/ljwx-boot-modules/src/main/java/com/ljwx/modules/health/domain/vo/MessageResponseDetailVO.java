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
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.List;

/**
 * 消息响应详情 VO 对象
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.MessageResponseDetailVO
 * @CreateTime 2025-09-15 - 21:00:00
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "MessageResponseDetailVO", description = "消息响应详情 VO 对象")
public class MessageResponseDetailVO implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "设备用户总数")
    private Long totalUsersWithDevices;

    @Schema(description = "已响应数量")
    private Integer respondedCount;

    @Schema(description = "未响应用户列表")
    private List<NonRespondedUserVO> nonRespondedUsers;
}
