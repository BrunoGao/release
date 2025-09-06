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
@Schema(name = "OrganizationStatisticsVO", description = "组织统计 VO 对象")
public class OrganizationStatisticsVO extends BaseVO {
    
    @Schema(description = "组织ID")
    private String orgId;
    
    @Schema(description = "总用户数")
    private Integer totalUsers;
    
    @Schema(description = "活跃用户数")
    private Integer activeUsers;
    
    @Schema(description = "总设备数")
    private Integer totalDevices;
    
    @Schema(description = "在线设备数")
    private Integer onlineDevices;
}