/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.dto.v1.alert;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.NotNull;
import java.io.Serializable;

@Getter
@Setter
@Builder
@Schema(name = "AlertAcknowledgeRequestDTO", description = "告警确认请求 DTO 对象")
public class AlertAcknowledgeRequestDTO implements Serializable {
    
    @NotNull(message = "告警ID不能为空")
    @Schema(description = "告警ID", required = true)
    private Long alertId;
    
    @Schema(description = "确认说明")
    private String acknowledgmentNote;
}