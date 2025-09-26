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

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 用户在线状态实体类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.entity.TUserOnlineStatus
 * @CreateTime 2024-01-15 - 10:55:00
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_user_online_status")
public class TUserOnlineStatus extends BaseEntity {

    /**
     * 用户ID (主键)
     */
    @TableId(type = IdType.INPUT)
    private Long userId;

    /**
     * 设备ID
     */
    private String deviceId;

    /**
     * 设备序列号
     */
    private String deviceSn;

    /**
     * 在线状态
     */
    private OnlineStatus onlineStatus;

    /**
     * 最后活跃时间
     */
    private LocalDateTime lastSeenTime;

    /**
     * 离线原因
     */
    private String offlineReason;

    /**
     * 最后定位时间
     */
    private LocalDateTime lastLocationTime;

    /**
     * 最后经度
     */
    private BigDecimal lastLng;

    /**
     * 最后纬度
     */
    private BigDecimal lastLat;

    /**
     * 最后海拔
     */
    private Double lastAltitude;

    /**
     * 最后位置描述
     */
    private String lastLocationDesc;

    /**
     * 最后位置空间对象
     */
    private String lastLocationGeom;

    /**
     * 电池电量(%)
     */
    private Integer batteryLevel;

    /**
     * 信号强度
     */
    private Integer signalStrength;

    /**
     * 心跳间隔(秒)
     */
    private Integer heartbeatInterval;

    /**
     * 上传方式
     */
    private String uploadMethod;

    /**
     * 今日运动距离(km)
     */
    private Double dailyDistance;

    /**
     * 今日步数
     */
    private Integer dailySteps;

    /**
     * 今日卡路里
     */
    private Double dailyCalories;

    /**
     * 最后重置日期
     */
    private LocalDate lastResetDate;

    /**
     * 组织ID
     */
    private Long orgId;

    /**
     * 租户ID (0表示全局数据)
     */
    private Long customerId;

    // ============== 枚举定义 ==============

    public enum OnlineStatus {
        ONLINE("在线"),
        OFFLINE("离线"),
        ABNORMAL("异常");

        private final String description;

        OnlineStatus(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }
}