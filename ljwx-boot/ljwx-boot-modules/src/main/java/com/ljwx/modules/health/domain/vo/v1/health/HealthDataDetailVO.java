/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.vo.v1.health;

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
@Schema(name = "HealthDataDetailVO", description = "健康数据详情 VO 对象")
public class HealthDataDetailVO extends BaseVO {
    
    @Schema(description = "健康数据ID")
    private String dataId;
    
    @Schema(description = "用户ID")
    private String userId;
    
    @Schema(description = "设备序列号")
    private String deviceSn;
    
    @Schema(description = "健康数据内容")
    private String data;
    
    @Schema(description = "数据时间")
    private LocalDateTime timestamp;
}