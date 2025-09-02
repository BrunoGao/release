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
*  VO 展示类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.vo.TDeviceInfoVO
* @CreateTime 2024-12-14 - 21:31:16
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "TDeviceInfoVO", description = " VO 对象")
public class TDeviceInfoVO extends BaseVO {
    private String departmentInfo;

    private String userName;

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

    private Object status;

    private Object wearableStatus;

    private Object chargingStatus;

    private String createUser;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;


}