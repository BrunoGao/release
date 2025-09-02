package com.ljwx.modules.health.domain.dto.user.health.data;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(name = "ThresholdDTO", description = "健康数据阈值参数")
public class ThresholdDTO {
    
    @Schema(description = "数据类型")
    private String dataType;
    
    @Schema(description = "最小阈值")
    private Double minThreshold;
    
    @Schema(description = "最大阈值")
    private Double maxThreshold;
} 