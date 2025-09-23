package com.ljwx.modules.health.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

/**
 * 编译后的单体征规则
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledSingleRule {
    
    private Long ruleId;
    private String physicalSign;
    private BigDecimal thresholdMin;
    private BigDecimal thresholdMax;
    private Integer trendDuration;
    private Integer timeWindowSeconds;
    private Integer cooldownSeconds;
    private Integer priorityLevel;
    private String severityLevel;
    private String alertMessage;
    private List<String> enabledChannels;
}