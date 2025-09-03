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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

/**
*  Entity 实体类
*
* @Author brunoGao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.TDeviceMessage
* @CreateTime 2024-10-24 - 13:07:24
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_message")
public class TDeviceMessage extends BaseEntity {

    private Long id;

    private Long orgId;

    private String userId;

    /**
     * 租户ID，继承自设备所属租户
     */
    private Long customerId;

    private String deviceSn;

    private String message;

    private String messageType;

    private String senderType;

    private String receiverType;

    private Integer respondedNumber;

    private String messageStatus;

    private LocalDateTime sentTime;

    private LocalDateTime receivedTime;

}