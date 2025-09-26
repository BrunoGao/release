package com.ljwx.modules.health.domain.dto.track;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 轨迹统计查询DTO
 *
 * @author Claude
 */
@Data
public class TrackStatsDTO {
    
    /**
     * 用户ID
     */
    private Long userId;
    
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
    private LocalDateTime startTime;
    
    /**
     * 结束时间
     */
    private LocalDateTime endTime;
    
    /**
     * 统计类型
     * DAILY-日统计, WEEKLY-周统计, MONTHLY-月统计
     */
    private String statsType;
    
    /**
     * 是否包含轨迹详情
     */
    private Boolean includeTrackDetails = false;
    
    /**
     * 页码
     */
    private Integer page = 1;
    
    /**
     * 页大小
     */
    private Integer pageSize = 20;
    
    /**
     * 设备序列号
     */
    private String deviceSn;
}