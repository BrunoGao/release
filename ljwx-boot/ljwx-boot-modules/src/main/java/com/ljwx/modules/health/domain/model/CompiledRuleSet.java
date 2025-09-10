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
import java.util.ArrayList;
import java.util.List;

/**
 * 编译后的规则集合
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CompiledRuleSet {
    
    @Builder.Default
    private List<CompiledSingleRule> singleRules = new ArrayList<>();
    
    @Builder.Default
    private List<CompiledCompositeRule> compositeRules = new ArrayList<>();
    
    @Builder.Default
    private List<CompiledComplexRule> complexRules = new ArrayList<>();
    
    /**
     * 添加单体征规则
     */
    public void addSingleRule(CompiledSingleRule rule) {
        if (singleRules == null) {
            singleRules = new ArrayList<>();
        }
        singleRules.add(rule);
    }
    
    /**
     * 添加复合规则
     */
    public void addCompositeRule(CompiledCompositeRule rule) {
        if (compositeRules == null) {
            compositeRules = new ArrayList<>();
        }
        compositeRules.add(rule);
    }
    
    /**
     * 添加复杂规则
     */
    public void addComplexRule(CompiledComplexRule rule) {
        if (complexRules == null) {
            complexRules = new ArrayList<>();
        }
        complexRules.add(rule);
    }
    
    /**
     * 获取规则总数
     */
    public int getTotalRuleCount() {
        return (singleRules != null ? singleRules.size() : 0) +
               (compositeRules != null ? compositeRules.size() : 0) +
               (complexRules != null ? complexRules.size() : 0);
    }
    
    /**
     * 是否为空
     */
    public boolean isEmpty() {
        return getTotalRuleCount() == 0;
    }
}
