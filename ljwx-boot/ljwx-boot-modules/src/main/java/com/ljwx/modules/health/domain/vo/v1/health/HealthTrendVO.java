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
@Schema(name = "HealthTrendVO", description = "健康趋势 VO 对象")
public class HealthTrendVO extends BaseVO {
    
    @Schema(description = "日期")
    private LocalDateTime date;
    
    @Schema(description = "数值")
    private Double value;
    
    @Schema(description = "数据类型")
    private String type;
}