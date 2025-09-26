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

package com.ljwx.modules.health.domain.dto.track;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 轨迹查询DTO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.dto.track.TrackQueryDTO
 * @CreateTime 2024-01-15 - 11:00:00
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrackQueryDTO {

    /**
     * 用户ID (单用户查询)
     */
    private Long userId;

    /**
     * 用户ID列表 (多用户查询)
     */
    private String userIds;

    /**
     * 组织ID
     */
    private Long orgId;

    /**
     * 租户ID
     */
    private Long customerId;

    /**
     * 开始时间
     */
    private LocalDateTime startDate;

    /**
     * 结束时间
     */
    private LocalDateTime endDate;

    /**
     * 分页页码
     */
    private Integer page = 1;

    /**
     * 分页大小
     */
    private Integer pageSize = 100;

    /**
     * 是否启用轨迹抽稀
     */
    private Boolean simplify = false;

    /**
     * 抽稀容差(米) - Douglas-Peucker算法参数
     */
    private Double tolerance = 10.0;

    /**
     * 最大点数限制
     */
    private Integer maxPoints = 1000;

    /**
     * 最小速度过滤(km/h) - 过滤静止点
     */
    private Double minSpeed = 0.0;

    /**
     * 最大速度过滤(km/h) - 过滤异常点
     */
    private Double maxSpeed = 200.0;

    /**
     * 定位精度过滤(米) - 过滤低精度点
     */
    private Double maxAccuracy = 50.0;

    /**
     * 定位类型过滤
     * 1-GPS, 2-WiFi, 3-基站, 多个用逗号分隔
     */
    private String locationTypes = "1,2,3";

    /**
     * 是否包含停留点分析
     */
    private Boolean includeStayPoints = false;

    /**
     * 停留点检测距离阈值(米)
     */
    private Double stayDistanceThreshold = 100.0;

    /**
     * 停留点检测时间阈值(分钟)
     */
    private Integer stayTimeThreshold = 5;

    /**
     * 是否只返回有效位置数据 (经纬度不为空)
     */
    private Boolean validLocationOnly = true;

    /**
     * 排序字段 (timestamp, distance, speed)
     */
    private String orderBy = "timestamp";

    /**
     * 排序方向 (ASC, DESC)
     */
    private String orderDirection = "ASC";
    
    /**
     * 设备序列号
     */
    private String deviceSn;
    
    /**
     * 简化容差
     */
    private double simplifyTolerance = 10.0;
    
    /**
     * 排序方向
     */
    private String sortDirection = "ASC";
}