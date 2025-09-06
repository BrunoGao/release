/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.vo.v1.statistics;

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
@Schema(name = "StatisticsOverviewVO", description = "统计概览 VO 对象")
public class StatisticsOverviewVO extends BaseVO {
    
    @Schema(description = "组织ID")
    private String orgId;
    
    @Schema(description = "总体健康指数")
    private Integer totalHealth;
    
    @Schema(description = "总告警数")
    private Integer totalAlerts;
    
    @Schema(description = "总消息数")
    private Integer totalMessages;
    
    @Schema(description = "在线率")
    private Double onlineRate;
}