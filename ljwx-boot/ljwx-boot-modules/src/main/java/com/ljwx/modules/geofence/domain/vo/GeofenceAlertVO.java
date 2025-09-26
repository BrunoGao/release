package com.ljwx.modules.geofence.domain.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 电子围栏告警VO
 *
 * @author Claude
 */
@Data
public class GeofenceAlertVO {
    
    /**
     * 告警ID
     */
    private Long id;
    
    /**
     * 围栏ID
     */
    private Long geofenceId;
    
    /**
     * 围栏名称
     */
    private String geofenceName;
    
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
     * 租户ID
     */
    private Long customerId;
    
    /**
     * 告警类型
     * ENTER-进入围栏, EXIT-离开围栏, STAY-停留超时
     */
    private String alertType;
    
    /**
     * 告警类型描述
     */
    private String alertTypeDesc;
    
    /**
     * 告警状态
     * PENDING-待处理, PROCESSING-处理中, RESOLVED-已解决, IGNORED-已忽略
     */
    private String status;
    
    /**
     * 告警状态描述
     */
    private String statusDesc;
    
    /**
     * 告警级别
     * LOW-低, MEDIUM-中, HIGH-高
     */
    private String alertLevel;
    
    /**
     * 告警级别描述
     */
    private String alertLevelDesc;
    
    /**
     * 经度
     */
    private BigDecimal longitude;
    
    /**
     * 纬度
     */
    private BigDecimal latitude;
    
    /**
     * 告警时间
     */
    private LocalDateTime alertTime;
    
    /**
     * 处理时间
     */
    private LocalDateTime processedTime;
    
    /**
     * 处理人ID
     */
    private Long processedBy;
    
    /**
     * 处理人姓名
     */
    private String processedByName;
    
    /**
     * 处理说明
     */
    private String processNote;
    
    /**
     * 告警消息
     */
    private String message;
    
    /**
     * 创建时间
     */
    private LocalDateTime createTime;
    
    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}