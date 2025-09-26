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
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

/**
*  Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.entity.TUserHealthData
* @CreateTime 2024-12-16 - 19:56:12
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_user_health_data")
public class TUserHealthData extends BaseEntity {

    private Long orgId;

    private Long userId;

    /**
     * 租户ID，0表示全局数据，其他值表示特定租户
     */
    private Long customerId;

    /**
     * 用户ID
     */
    @TableField(exist = false)
    private String userName;

    private Integer heartRate;

    private Integer pressureHigh;

    private Integer pressureLow;

    private Integer bloodOxygen;

    private Double temperature;

    private Integer step;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "Asia/Shanghai")
    private LocalDateTime timestamp;


    private Double latitude;

    private Double longitude;

    private Double altitude;

    private String deviceSn;

    private Double distance;

    private Double calorie;

    // #已迁移到分表：sleepData, exerciseDailyData, scientificSleepData, workoutData -> t_user_health_data_daily
    // #已迁移到分表：exerciseWeekData -> t_user_health_data_weekly

    private Integer stress;

    /**
     * 上传方式：wifi、bluetooth、common_event
     */
    private String uploadMethod;
    
    // ============== 轨迹功能新增字段 (v1.0.0) ==============
    
    /**
     * 速度(km/h)
     */
    private Double speed;
    
    /**
     * 方向角(度，0-360)
     * 0度表示正北，90度表示正东，180度表示正南，270度表示正西
     */
    private Double bearing;
    
    /**
     * 定位精度(米)
     */
    private Double accuracy;
    
    /**
     * 定位类型
     * 1-GPS定位, 2-WiFi定位, 3-基站定位
     */
    private Integer locationType;
    
    /**
     * 空间几何对象 (MySQL POINT类型)
     * 用于地理围栏计算和空间查询，由 longitude + latitude 自动生成
     * 注意: 此字段由数据库触发器维护，不需要手动设置
     */
    @TableField("geom")
    private String geom;

}