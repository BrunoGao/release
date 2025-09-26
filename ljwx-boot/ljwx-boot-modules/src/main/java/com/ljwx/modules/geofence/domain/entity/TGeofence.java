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

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ljwx.infrastructure.domain.BaseEntity;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.math.BigDecimal;

/**
*  Entity 实体类
*
* @Author jjgao
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.geofence.domain.entity.TGeofence
* @CreateTime 2025-01-07 - 19:44:06
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_geofence")
public class TGeofence extends BaseEntity {

    /**
     * 电子围栏名称
     */
    private String name;

    /**
     * 围栏区域 (GeoJSON或WKT格式)
     */
    private String area;

    /**
     * 围栏描述
     */
    private String description;

    /**
     * 围栏状态 (active/inactive)
     * @deprecated 使用 isActive 字段替代
     */
    @Deprecated
    private String status;
    
    // ============== 轨迹功能扩展字段 (v1.0.0) ==============
    
    /**
     * 围栏类型
     * CIRCLE-圆形围栏, RECTANGLE-矩形围栏, POLYGON-多边形围栏
     */
    @TableField("fence_type")
    private FenceType fenceType;
    
    /**
     * 中心点经度 (圆形和矩形围栏使用)
     */
    private BigDecimal centerLng;
    
    /**
     * 中心点纬度 (圆形和矩形围栏使用)
     */
    private BigDecimal centerLat;
    
    /**
     * 半径(米) - 圆形围栏专用
     */
    private Float radius;
    
    /**
     * 空间几何对象 (MySQL GEOMETRY类型)
     * 用于高效的地理围栏计算
     */
    private String geom;
    
    // ============== 告警配置字段 ==============
    
    /**
     * 进入围栏时是否告警
     */
    private Boolean alertOnEnter;
    
    /**
     * 离开围栏时是否告警
     */
    private Boolean alertOnExit;
    
    /**
     * 停留超时是否告警
     */
    private Boolean alertOnStay;
    
    /**
     * 停留时长阈值(分钟)
     */
    private Integer stayDurationMinutes;
    
    /**
     * 告警级别
     */
    private AlertLevel alertLevel;
    
    /**
     * 通知渠道配置 (JSON格式)
     * 例: {"wechat": true, "sms": true, "email": false}
     */
    private String notifyChannels;
    
    /**
     * 通知模板ID
     */
    private String notifyTemplateId;
    
    // ============== 多租户支持字段 ==============
    
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
    
    public enum FenceType {
        CIRCLE("圆形"),
        RECTANGLE("矩形"),
        POLYGON("多边形");
        
        private final String description;
        
        FenceType(String description) {
            this.description = description;
        }
        
        public String getDescription() {
            return description;
        }
    }
    
    public enum AlertLevel {
        LOW("低"),
        MEDIUM("中"),
        HIGH("高");
        
        private final String description;
        
        AlertLevel(String description) {
            this.description = description;
        }
        
        public String getDescription() {
            return description;
        }
    }

}