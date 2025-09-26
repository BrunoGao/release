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

package com.ljwx.modules.health.domain.vo.track;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 轨迹点VO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.track.TrackPointVO
 * @CreateTime 2024-01-15 - 11:05:00
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrackPointVO {

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 用户名称
     */
    private String userName;

    /**
     * 经度
     */
    private Double longitude;

    /**
     * 纬度
     */
    private Double latitude;

    /**
     * 海拔(米)
     */
    private Double altitude;

    /**
     * 速度(km/h)
     */
    private Double speed;

    /**
     * 方向角(度)
     */
    private Double bearing;

    /**
     * 定位精度(米)
     */
    private Double accuracy;

    /**
     * 定位类型
     * 1-GPS, 2-WiFi, 3-基站
     */
    private Integer locationType;

    /**
     * 定位类型描述
     */
    private String locationTypeDesc;

    /**
     * 时间戳
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime timestamp;

    /**
     * 设备序列号
     */
    private String deviceSn;

    /**
     * 累计距离(km) - 从起点到当前点的累计距离
     */
    private Double cumulativeDistance;

    /**
     * 与前一点的距离(m)
     */
    private Double segmentDistance;

    /**
     * 与前一点的时间间隔(秒)
     */
    private Integer timeInterval;

    /**
     * 是否停留点
     */
    private Boolean isStayPoint;

    /**
     * 停留时长(分钟) - 如果是停留点
     */
    private Integer stayDuration;

    /**
     * 位置描述 (地址解析结果)
     */
    private String locationDesc;

    /**
     * 上传方式
     */
    private String uploadMethod;

    // ============== 辅助方法 ==============

    /**
     * 获取定位类型描述
     */
    public String getLocationTypeDesc() {
        if (locationType == null) {
            return "未知";
        }
        return switch (locationType) {
            case 1 -> "GPS";
            case 2 -> "WiFi";
            case 3 -> "基站";
            default -> "未知";
        };
    }

    /**
     * 获取精度等级描述
     */
    public String getAccuracyLevel() {
        if (accuracy == null) {
            return "未知";
        }
        if (accuracy <= 5) {
            return "高精度";
        } else if (accuracy <= 20) {
            return "中等精度";
        } else {
            return "低精度";
        }
    }

    /**
     * 是否高精度定位
     */
    public boolean isHighAccuracy() {
        return accuracy != null && accuracy <= 10;
    }

    /**
     * 是否移动状态 (速度 > 1km/h)
     */
    public boolean isMoving() {
        return speed != null && speed > 1.0;
    }
}