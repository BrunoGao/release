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
import java.util.List;

/**
 * 轨迹统计VO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.vo.track.TrackStatisticsVO
 * @CreateTime 2024-01-15 - 11:10:00
 */

@Data
@NoArgsConstructor
@AllArgsConstructor
public class TrackStatisticsVO {

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 用户名称
     */
    private String userName;

    /**
     * 统计开始时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime startTime;

    /**
     * 统计结束时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime endTime;

    /**
     * 轨迹点总数
     */
    private Integer totalPoints;

    /**
     * 有效轨迹点数 (有经纬度的点)
     */
    private Integer validPoints;

    /**
     * 总距离(km)
     */
    private Double totalDistance;

    /**
     * 运动时长(分钟)
     */
    private Integer totalDuration;

    /**
     * 平均速度(km/h)
     */
    private Double averageSpeed;

    /**
     * 最大速度(km/h)
     */
    private Double maxSpeed;

    /**
     * 最小速度(km/h)
     */
    private Double minSpeed;

    /**
     * 移动时长(分钟) - 速度>1km/h的时长
     */
    private Integer movingDuration;

    /**
     * 停留时长(分钟)
     */
    private Integer stayDuration;

    /**
     * 停留点数量
     */
    private Integer stayPointCount;

    /**
     * 平均定位精度(米)
     */
    private Double averageAccuracy;

    /**
     * 高精度点比例(%)
     */
    private Double highAccuracyRate;

    /**
     * GPS定位点数
     */
    private Integer gpsPoints;

    /**
     * WiFi定位点数
     */
    private Integer wifiPoints;

    /**
     * 基站定位点数
     */
    private Integer cellPoints;

    /**
     * 起始位置
     */
    private TrackPointVO startPoint;

    /**
     * 结束位置
     */
    private TrackPointVO endPoint;

    /**
     * 最北点
     */
    private TrackPointVO northPoint;

    /**
     * 最南点
     */
    private TrackPointVO southPoint;

    /**
     * 最东点
     */
    private TrackPointVO eastPoint;

    /**
     * 最西点
     */
    private TrackPointVO westPoint;

    /**
     * 停留点列表
     */
    private List<StayPointVO> stayPoints;

    /**
     * 轨迹边界框
     */
    private BoundingBoxVO boundingBox;

    // ============== 内部类定义 ==============

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class StayPointVO {
        /**
         * 经度
         */
        private Double longitude;

        /**
         * 纬度
         */
        private Double latitude;

        /**
         * 停留开始时间
         */
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime startTime;

        /**
         * 停留结束时间
         */
        @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
        private LocalDateTime endTime;

        /**
         * 停留时长(分钟)
         */
        private Integer duration;

        /**
         * 停留点数量
         */
        private Integer pointCount;

        /**
         * 位置描述
         */
        private String locationDesc;

        /**
         * 停留半径(米)
         */
        private Double radius;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class BoundingBoxVO {
        /**
         * 最小经度
         */
        private Double minLng;

        /**
         * 最大经度
         */
        private Double maxLng;

        /**
         * 最小纬度
         */
        private Double minLat;

        /**
         * 最大纬度
         */
        private Double maxLat;

        /**
         * 中心点经度
         */
        private Double centerLng;

        /**
         * 中心点纬度
         */
        private Double centerLat;

        /**
         * 跨度经度
         */
        private Double spanLng;

        /**
         * 跨度纬度
         */
        private Double spanLat;
    }

    // ============== 辅助方法 ==============

    /**
     * 获取数据质量评分 (0-100)
     */
    public Double getDataQualityScore() {
        if (totalPoints == null || totalPoints == 0) {
            return 0.0;
        }

        double validRate = (double) validPoints / totalPoints;
        double accuracyScore = highAccuracyRate != null ? highAccuracyRate / 100 : 0.0;
        double gpsRate = gpsPoints != null ? (double) gpsPoints / validPoints : 0.0;

        return (validRate * 0.4 + accuracyScore * 0.4 + gpsRate * 0.2) * 100;
    }

    /**
     * 获取运动强度描述
     */
    public String getActivityLevel() {
        if (averageSpeed == null) {
            return "静止";
        }
        if (averageSpeed < 1) {
            return "静止";
        } else if (averageSpeed < 5) {
            return "步行";
        } else if (averageSpeed < 12) {
            return "跑步";
        } else if (averageSpeed < 25) {
            return "骑行";
        } else {
            return "高速移动";
        }
    }

    /**
     * 获取移动效率 (移动时长/总时长)
     */
    public Double getMovingEfficiency() {
        if (totalDuration == null || totalDuration == 0) {
            return 0.0;
        }
        return movingDuration != null ? (double) movingDuration / totalDuration : 0.0;
    }
}