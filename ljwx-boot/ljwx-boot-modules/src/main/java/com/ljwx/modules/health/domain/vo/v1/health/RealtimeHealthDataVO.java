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
@Schema(name = "RealtimeHealthDataVO", description = "实时健康数据 VO 对象")
public class RealtimeHealthDataVO extends BaseVO {
    
    @Schema(description = "心率")
    private Integer heartRate;
    
    @Schema(description = "血压")
    private String bloodPressure;
    
    @Schema(description = "体温")
    private Double temperature;
    
    @Schema(description = "血氧水平")
    private Integer oxygenLevel;
    
    @Schema(description = "数据时间")
    private LocalDateTime timestamp;
}