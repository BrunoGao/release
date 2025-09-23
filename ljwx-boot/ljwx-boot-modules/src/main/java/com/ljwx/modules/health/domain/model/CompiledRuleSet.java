package com.ljwx.modules.health.domain.model;

import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

/**
 * 编译后的规则集合
 */
@Data
@NoArgsConstructor
public class CompiledRuleSet {
    
    private List<CompiledSingleRule> singleRules = new ArrayList<>();
    private List<CompiledCompositeRule> compositeRules = new ArrayList<>(); 
    private List<CompiledComplexRule> complexRules = new ArrayList<>();
    
    public void addSingleRule(CompiledSingleRule rule) {
        singleRules.add(rule);
    }
    
    public void addCompositeRule(CompiledCompositeRule rule) {
        compositeRules.add(rule);
    }
    
    public void addComplexRule(CompiledComplexRule rule) {
        complexRules.add(rule);
    }
}