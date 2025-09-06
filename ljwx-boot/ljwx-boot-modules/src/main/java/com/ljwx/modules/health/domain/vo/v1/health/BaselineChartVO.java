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

import java.util.List;

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "BaselineChartVO", description = "基线图表 VO 对象")
public class BaselineChartVO extends BaseVO {
    
    @Schema(description = "图表数据")
    private List<Object> chartData;
    
    @Schema(description = "基线值")
    private Double baselineValue;
    
    @Schema(description = "数据类型")
    private String dataType;
}