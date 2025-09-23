package com.ljwx.modules.health.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 编译后的条件
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledCondition {
    
    private String physicalSign;
    private String operator; // >, <, >=, <=, ==, !=
    private BigDecimal threshold;
    private Integer durationSeconds;
}