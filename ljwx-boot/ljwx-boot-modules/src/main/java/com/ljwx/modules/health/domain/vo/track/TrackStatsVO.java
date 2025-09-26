package com.ljwx.modules.health.domain.vo.track;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 轨迹统计VO
 *
 * @author Claude
 */
@Data
public class TrackStatsVO {
    
    /**
     * 用户ID
     */
    private Long userId;
    
    /**
     * 用户姓名
     */
    private String userName;
    
    /**
     * 组织ID
     */
    private Long orgId;
    
    /**
     * 组织名称
     */
    private String orgName;
    
    /**
     * 统计日期
     */
    private LocalDateTime statsDate;
    
    /**
     * 统计类型描述
     */
    private String statsTypeDesc;
    
    /**
     * 总距离(公里)
     */
    private BigDecimal totalDistance;
    
    /**
     * 总时长(分钟)
     */
    private Integer totalDuration;
    
    /**
     * 平均速度(km/h)
     */
    private BigDecimal avgSpeed;
    
    /**
     * 最高速度(km/h)
     */
    private BigDecimal maxSpeed;
    
    /**
     * 总步数
     */
    private Integer totalSteps;
    
    /**
     * 总消耗卡路里
     */
    private BigDecimal totalCalories;
    
    /**
     * 轨迹点数量
     */
    private Integer trackPointCount;
    
    /**
     * 停留点数量
     */
    private Integer stayPointCount;
    
    /**
     * 运动类型分布
     */
    private List<MovementTypeStats> movementTypeStats;
    
    /**
     * 时间段分布(24小时)
     */
    private List<HourlyStats> hourlyStats;
    
    /**
     * 首次活动时间
     */
    private LocalDateTime firstActivityTime;
    
    /**
     * 最后活动时间
     */
    private LocalDateTime lastActivityTime;
    
    /**
     * 活动天数
     */
    private Integer activeDays;
    
    /**
     * 轨迹详情(可选)
     */
    private List<TrackDetailVO> trackDetails;
    
    /**
     * 运动类型统计
     */
    @Data
    public static class MovementTypeStats {
        private String movementType;
        private String movementTypeDesc;
        private BigDecimal distance;
        private Integer duration;
        private Integer count;
        private BigDecimal percentage;
    }
    
    /**
     * 小时统计
     */
    @Data
    public static class HourlyStats {
        private Integer hour;
        private BigDecimal distance;
        private Integer duration;
        private Integer activityCount;
    }
    
    /**
     * 轨迹详情
     */
    @Data
    public static class TrackDetailVO {
        private LocalDateTime startTime;
        private LocalDateTime endTime;
        private BigDecimal distance;
        private Integer duration;
        private BigDecimal avgSpeed;
        private BigDecimal maxSpeed;
        private String movementType;
        private List<TrackPointVO> trackPoints;
    }
    
    /**
     * 轨迹点
     */
    @Data
    public static class TrackPointVO {
        private BigDecimal longitude;
        private BigDecimal latitude;
        private BigDecimal altitude;
        private BigDecimal speed;
        private BigDecimal bearing;
        private LocalDateTime timestamp;
    }
}