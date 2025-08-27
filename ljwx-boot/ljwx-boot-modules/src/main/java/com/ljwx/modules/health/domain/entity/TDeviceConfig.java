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

/**
*  Entity 实体类
*
* @Author brunoGao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.heath.domain.entity.TDeviceConfig
* @CreateTime 2024-10-23 - 22:34:21
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_device_config")
public class TDeviceConfig extends BaseEntity {

    private Integer spo2MeasurePeriod;

    private Integer stressMeasurePeriod;

    private Integer bodyTemperatureMeasurePeriod;

    private Integer heartRateWarningHigh;

    private Integer heartRateWarningLow;

    private Integer spo2Warning;

    private Integer stressWarning;

    private Float bodyTemperatureHighWarning;

    private Float bodyTemperatureLowWarning;

    private String httpUrl;

    private String logo;

    private String uiType;

    private Integer bodyTemperatureWarningCnt;

    private Integer heartWarningCnt;

    private Integer heartRateMeasurePeriod;

    private Integer spo2WarningCnt;

    private Boolean stressMonitoringEnabled;

    private Boolean stepsMonitoringEnabled;

    private Boolean distanceMonitoringEnabled;

    private Boolean calorieMonitoringEnabled;

    private Boolean sleepMonitoringEnabled;

    private Boolean ecgMonitoringEnabled;

    private Boolean locationMonitoringEnabled;

    private Boolean sosEventListenerEnabled;

    private Boolean doubleClickEventListenerEnabled;

    private Boolean temperatureAbnormalListenerEnabled;

    private Boolean heartRateAbnormalListenerEnabled;

    private Boolean stressAbnormalListenerEnabled;

    private Boolean fallEventListenerEnabled;

    private Boolean spo2AbnormalListenerEnabled;

    private Boolean oneClickAlarmListenerEnabled;

    private Boolean wearingStatusListenerEnabled;

}