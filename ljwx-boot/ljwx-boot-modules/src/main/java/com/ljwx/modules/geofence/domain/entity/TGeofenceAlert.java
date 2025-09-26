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

package com.ljwx.modules.geofence.domain.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 围栏告警记录实体类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.domain.entity.TGeofenceAlert
 * @CreateTime 2024-01-15 - 10:50:00
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_geofence_alert")
public class TGeofenceAlert extends BaseEntity {

    /**
     * 告警ID (业务主键)
     */
    private String alertId;

    /**
     * 围栏ID
     */
    private Long fenceId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 设备ID
     */
    private String deviceId;

    /**
     * 告警类型
     */
    private AlertType alertType;

    /**
     * 告警级别
     */
    private TGeofence.AlertLevel alertLevel;

    /**
     * 告警开始时间
     */
    private LocalDateTime startTime;

    /**
     * 告警结束时间
     */
    private LocalDateTime endTime;

    /**
     * 持续时长(分钟)
     */
    private Integer durationMinutes;

    /**
     * 告警位置经度
     */
    private BigDecimal locationLng;

    /**
     * 告警位置纬度
     */
    private BigDecimal locationLat;

    /**
     * 位置描述
     */
    private String locationDesc;

    /**
     * 告警位置空间对象
     */
    private String locationGeom;

    /**
     * 处理状态
     */
    private AlertStatus alertStatus;

    /**
     * 处理人ID
     */
    private Long handlerId;

    /**
     * 处理时间
     */
    private LocalDateTime handleTime;

    /**
     * 处理备注
     */
    private String handleNote;

    /**
     * 处理结果
     */
    private String handleResult;

    /**
     * 通知状态记录 (JSON格式)
     * 例: {"wechat": {"sent": true, "time": "2024-01-15T10:30:00"}, "sms": {"sent": false, "error": "..."}}
     */
    private String notifyStatus;

    /**
     * 通知重试次数
     */
    private Integer notifyRetryCount;

    /**
     * 通知成功时间
     */
    private LocalDateTime notifySuccessTime;

    /**
     * 组织ID
     */
    private Long orgId;

    /**
     * 租户ID (0表示全局数据)
     */
    private Long customerId;

    // ============== 枚举定义 ==============

    public enum AlertType {
        ENTER("进入围栏"),
        EXIT("离开围栏"),
        STAY_TIMEOUT("停留超时");

        private final String description;

        AlertType(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }

    public enum AlertStatus {
        PENDING("待处理"),
        PROCESSING("处理中"),
        RESOLVED("已解决"),
        IGNORED("已忽略");

        private final String description;

        AlertStatus(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }
}