package com.ljwx.modules.health.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 编译后的复杂规则（暂未实现）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledComplexRule {
    
    private Long ruleId;
    // 复杂规则字段待定义
}