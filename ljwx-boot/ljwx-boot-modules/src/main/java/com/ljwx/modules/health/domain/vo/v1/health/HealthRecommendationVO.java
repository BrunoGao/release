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
@Schema(name = "HealthRecommendationVO", description = "健康建议 VO 对象")
public class HealthRecommendationVO extends BaseVO {
    
    @Schema(description = "建议类型")
    private String type;
    
    @Schema(description = "建议标题")
    private String title;
    
    @Schema(description = "建议描述")
    private String description;
    
    @Schema(description = "优先级")
    private String priority;
}