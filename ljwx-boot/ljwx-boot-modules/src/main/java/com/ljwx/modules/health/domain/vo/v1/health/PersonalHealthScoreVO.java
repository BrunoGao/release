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
@Schema(name = "PersonalHealthScoreVO", description = "个人健康评分 VO 对象")
public class PersonalHealthScoreVO extends BaseVO {
    
    @Schema(description = "总体评分")
    private Integer overallScore;
    
    @Schema(description = "心率评分")
    private Integer heartScore;
    
    @Schema(description = "睡眠评分")
    private Integer sleepScore;
    
    @Schema(description = "活动评分")
    private Integer activityScore;
    
    @Schema(description = "评分时间")
    private LocalDateTime timestamp;
}