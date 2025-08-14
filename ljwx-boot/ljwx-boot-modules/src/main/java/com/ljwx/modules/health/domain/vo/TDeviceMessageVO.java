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

package com.ljwx.modules.health.domain.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
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
* @Author brunoGao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.TDeviceMessageVO
* @CreateTime 2024-10-24 - 13:07:24
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TDeviceMessageVO", description = " VO 对象")
public class TDeviceMessageVO extends BaseVO {

    private Long id;

    private String departmentInfo;

    private String userId;

    private String userName;
    private String departmentName;

    private String deviceSn;

    private String message;

    private String messageType;

    private String senderType;

    private String receiverType;

    private Integer respondedNumber;

    private MessageResponseDetailVO respondedDetail;

    private String messageStatus;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
    private LocalDateTime sentTime;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
    private LocalDateTime receivedTime;

    private String createUser;

    private LocalDateTime createTime;

}