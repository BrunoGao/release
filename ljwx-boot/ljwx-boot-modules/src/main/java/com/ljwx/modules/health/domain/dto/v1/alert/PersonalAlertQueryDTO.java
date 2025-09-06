/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.dto.v1.alert;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import java.io.Serializable;

@Getter
@Setter
@Builder
@Schema(name = "PersonalAlertQueryDTO", description = "个人告警查询 DTO 对象")
public class PersonalAlertQueryDTO implements Serializable {
    
    @Schema(description = "设备序列号")
    private String deviceSn;
    
    @Schema(description = "用户ID")
    private String userId;
}