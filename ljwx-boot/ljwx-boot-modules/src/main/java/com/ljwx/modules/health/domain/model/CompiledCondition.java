/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.model;

import lombok.Data;
import lombok.Builder;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

/**
 * 编译后的条件
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
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