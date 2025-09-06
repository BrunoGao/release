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
@Schema(name = "RealtimeStatisticsVO", description = "实时统计 VO 对象")
public class RealtimeStatisticsVO extends BaseVO {
    
    @Schema(description = "组织ID")
    private String orgId;
    
    @Schema(description = "在线数量")
    private Integer onlineCount;
    
    @Schema(description = "总数量")
    private Integer totalCount;
    
    @Schema(description = "新告警数")
    private Integer newAlerts;
    
    @Schema(description = "平均心率")
    private Integer averageHeartRate;
}