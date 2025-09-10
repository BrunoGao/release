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
import java.util.Map;

/**
 * 编译后的复杂规则
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledComplexRule {
    private Long ruleId;
    private String expression;
    private Map<String, String> variables;
    private Integer timeWindowSeconds;
    private Integer cooldownSeconds;
    private Integer priorityLevel;
    private String severityLevel;
    private String alertMessage;
    private List<String> enabledChannels;
}