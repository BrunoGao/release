/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.model;

import lombok.Data;
import lombok.Builder;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 编译后的复合规则
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledCompositeRule {
    private Long ruleId;
    private List<CompiledCondition> conditions;
    private String logicalOperator; // AND, OR
    private Integer timeWindowSeconds;
    private Integer cooldownSeconds;
    private Integer priorityLevel;
    private String severityLevel;
    private String alertMessage;
    private List<String> enabledChannels;
}