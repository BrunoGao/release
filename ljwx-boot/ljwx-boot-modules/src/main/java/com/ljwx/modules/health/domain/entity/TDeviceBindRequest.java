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
* 设备绑定申请表 Entity 实体类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.TDeviceBindRequest
* @CreateTime 2025-08-23
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_bind_request")
public class TDeviceBindRequest extends BaseEntity {

    /**
    * 设备序列号
    */
    private String deviceSn;

    /**
    * 申请用户ID
    */
    private String userId;

    /**
     * 租户ID，继承自申请用户的租户信息
     */
    private Long customerId;

    /**
    * 申请用户姓名
    */
    private String userName;

    /**
    * 手机号码
    */
    private String phoneNumber;

    /**
    * 组织ID
    */
    private String orgId;

    /**
    * 申请时间
    */
    private LocalDateTime applyTime;

    /**
    * 审批时间
    */
    private LocalDateTime approveTime;

    /**
    * 审批人ID
    */
    private String approverId;

    /**
    * 审批人姓名
    */
    private String approverName;

    /**
    * 申请状态 (PENDING:待审批, APPROVED:已通过, REJECTED:已拒绝)
    */
    private String status;

    /**
    * 审批备注
    */
    private String comment;

    /**
    * 是否删除 (0:未删除, 1:已删除)
    */
    private Integer isDeleted;
}