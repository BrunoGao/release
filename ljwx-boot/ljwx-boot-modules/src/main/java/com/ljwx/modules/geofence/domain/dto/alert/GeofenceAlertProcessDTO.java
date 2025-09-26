package com.ljwx.modules.geofence.domain.dto.alert;

import lombok.Data;

/**
 * 电子围栏告警处理DTO
 *
 * @author Claude
 */
@Data
public class GeofenceAlertProcessDTO {
    
    /**
     * 告警ID
     */
    private Long id;
    
    /**
     * 处理状态
     * PROCESSING-处理中, RESOLVED-已解决, IGNORED-已忽略
     */
    private String status;
    
    /**
     * 处理说明
     */
    private String processNote;
    
    /**
     * 处理人ID
     */
    private Long processedBy;
    
    /**
     * 处理人姓名
     */
    private String processedByName;
    
    /**
     * 告警ID getter
     */
    public Long getAlertId() {
        return this.id;
    }
    
    /**
     * 新状态 getter
     */
    public String getNewStatus() {
        return this.status;
    }
}