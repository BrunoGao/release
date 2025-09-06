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
@Schema(name = "HealthScoreVO", description = "健康评分 VO 对象")
public class HealthScoreVO extends BaseVO {
    
    @Schema(description = "综合评分")
    private Integer score;
    
    @Schema(description = "健康等级")
    private String level;
    
    @Schema(description = "评分描述")
    private String description;
    
    @Schema(description = "评分时间")
    private LocalDateTime timestamp;
}