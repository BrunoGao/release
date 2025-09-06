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
@Schema(name = "BaselineGenerateResultVO", description = "基线生成结果 VO 对象")
public class BaselineGenerateResultVO extends BaseVO {
    
    @Schema(description = "生成是否成功")
    private Boolean success;
    
    @Schema(description = "结果消息")
    private String message;
    
    @Schema(description = "生成时间")
    private LocalDateTime timestamp;
}