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
@Schema(name = "DepartmentVO", description = "部门 VO 对象")
public class DepartmentVO extends BaseVO {
    
    @Schema(description = "部门ID")
    private String departmentId;
    
    @Schema(description = "部门名称")
    private String name;
    
    @Schema(description = "组织ID")
    private String orgId;
    
    @Schema(description = "用户数量")
    private Integer userCount;
}