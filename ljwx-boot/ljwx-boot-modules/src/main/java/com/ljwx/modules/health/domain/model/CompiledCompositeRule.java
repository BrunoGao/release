package com.ljwx.modules.health.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 编译后的复合规则
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