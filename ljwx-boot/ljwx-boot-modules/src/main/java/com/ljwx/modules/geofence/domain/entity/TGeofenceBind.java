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

import java.time.LocalTime;

/**
 * 围栏绑定关系实体类
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.geofence.domain.entity.TGeofenceBind
 * @CreateTime 2024-01-15 - 10:45:00
 */

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_geofence_bind")
public class TGeofenceBind extends BaseEntity {

    /**
     * 绑定ID (业务主键)
     */
    private String bindId;

    /**
     * 围栏ID
     */
    private Long fenceId;

    /**
     * 绑定目标类型
     */
    private TargetType targetType;

    /**
     * 目标ID (用户ID/设备ID/车辆ID)
     */
    private Long targetId;

    /**
     * 绑定规则配置 (JSON格式)
     */
    private String bindRule;

    /**
     * 是否仅工作时间生效
     */
    private Boolean workTimeOnly;

    /**
     * 生效星期 (1-7, 逗号分隔)
     * 例: "1,2,3,4,5" 表示周一到周五
     */
    private String effectiveWeekdays;

    /**
     * 生效开始时间
     */
    private LocalTime effectiveStartTime;

    /**
     * 生效结束时间
     */
    private LocalTime effectiveEndTime;

    /**
     * 组织ID
     */
    private Long orgId;

    /**
     * 租户ID (0表示全局数据)
     */
    private Long customerId;

    /**
     * 是否启用
     */
    private Boolean isActive;

    /**
     * 创建人
     */
    private String createdBy;

    // ============== 枚举定义 ==============

    public enum TargetType {
        USER("用户"),
        DEVICE("设备"),
        VEHICLE("车辆");

        private final String description;

        TargetType(String description) {
            this.description = description;
        }

        public String getDescription() {
            return description;
        }
    }
}