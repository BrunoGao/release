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

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
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
* @ClassName com.ljwx.modules.health.domain.entity.TAlertActionLog
* @CreateTime 2024-10-27 - 21:37:48
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_alert_action_log")
public class TAlertActionLog extends BaseEntity {
    
    // 排除BaseEntity的id字段
    @TableField(exist = false)
    private Long id;
    
    /**
     * 用户ID
     */
    @TableField(exist = false)
    private String userName;

    /**
     * 部门信息
     */
    @TableField(exist = false)
    private String departmentInfo;

    @TableId // 指定logId为主键
    private Long logId;

    private Long alertId;

    /**
     * 租户ID，继承自告警所属租户
     */
    private Long customerId;

    private String action;

    private LocalDateTime actionTimestamp;

    private String actionUser;

    private Long actionUserId;

    private String details;

    private String result;

}