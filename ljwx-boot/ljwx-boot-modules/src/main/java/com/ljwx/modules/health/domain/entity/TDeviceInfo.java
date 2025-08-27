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
import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;

import io.swagger.v3.oas.models.security.SecurityScheme.In;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;

/**
*  Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.TDeviceInfo
* @CreateTime 2024-12-14 - 21:31:16
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_info")
public class TDeviceInfo extends BaseEntity {
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

    private String systemSoftwareVersion;

    private String wifiAddress;

    private String bluetoothAddress;

    private String ipAddress;

    private String networkAccessMode;

    private String serialNumber;

    private String deviceName;

    private String imei;

    private LocalDateTime createdAt;

    private Integer batteryLevel;

    private Integer voltage;

    private LocalDateTime timestamp;

    private String model;

    private String status;

    private String wearableStatus;

    private String chargingStatus;

    private LocalDateTime updateTime;

    @JsonFormat(shape = JsonFormat.Shape.STRING) // 防止前端精度丢失
    private Long orgId; // 组织ID

    @JsonFormat(shape = JsonFormat.Shape.STRING) // 防止前端精度丢失
    private Long userId; // 用户ID

}