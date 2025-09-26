package com.ljwx.modules.geofence.domain.dto.alert;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 电子围栏告警查询DTO
 *
 * @author Claude
 */
@Data
public class GeofenceAlertQueryDTO {
    
    /**
     * 告警ID
     */
    private Long id;
    
    /**
     * 围栏ID
     */
    private Long geofenceId;
    
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
     * 告警类型
     * ENTER-进入围栏, EXIT-离开围栏, STAY-停留超时
     */
    private String alertType;
    
    /**
     * 告警状态
     * PENDING-待处理, PROCESSING-处理中, RESOLVED-已解决, IGNORED-已忽略
     */
    private String status;
    
    /**
     * 告警级别
     * LOW-低, MEDIUM-中, HIGH-高
     */
    private String alertLevel;
    
    /**
     * 开始时间
     */
    private LocalDateTime startTime;
    
    /**
     * 结束时间
     */
    private LocalDateTime endTime;
    
    /**
     * 页码
     */
    private Integer page = 1;
    
    /**
     * 页大小
     */
    private Integer pageSize = 20;
    
    /**
     * 限制条数
     */
    private Integer limit = 100;
}