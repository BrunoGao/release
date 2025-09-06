/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.vo.v1.device;

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
@Schema(name = "DeviceStatusVO", description = "设备状态 VO 对象")
public class DeviceStatusVO extends BaseVO {
    
    @Schema(description = "设备序列号")
    private String deviceSn;
    
    @Schema(description = "设备状态")
    private String status;
    
    @Schema(description = "电池电量")
    private Integer batteryLevel;
    
    @Schema(description = "最后同步时间")
    private LocalDateTime lastSync;
}