/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.vo.v1.alert;

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "UserAlertVO", description = "用户告警 VO 对象")
public class UserAlertVO extends BaseVO {
    
    @Schema(description = "告警ID")
    private String alertId;
    
    @Schema(description = "用户ID")
    private String userId;
    
    @Schema(description = "告警类型")
    private String alertType;
    
    @Schema(description = "告警消息")
    private String message;
    
    @Schema(description = "告警状态")
    private String status;
    
    @Schema(description = "告警时间")
    private LocalDateTime timestamp;
}