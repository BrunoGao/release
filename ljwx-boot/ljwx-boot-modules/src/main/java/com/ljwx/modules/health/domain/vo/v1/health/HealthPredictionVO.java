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

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "HealthPredictionVO", description = "健康预测 VO 对象")
public class HealthPredictionVO extends BaseVO {
    
    @Schema(description = "预测类型")
    private String type;
    
    @Schema(description = "预测结果")
    private String prediction;
    
    @Schema(description = "置信度")
    private Double confidence;
    
    @Schema(description = "时间范围")
    private String timeFrame;
}