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
import java.util.Map;
import java.util.HashMap;

/**
 * 健康数据事件
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthDataEvent {
    
    private Long customerId;
    private String deviceSn;
    private Long userId;
    private Long orgId;
    private String latitude;
    private String longitude;
    private Long timestamp;
    
    // 健康数据值映射
    @Builder.Default
    private Map<String, Object> healthData = new HashMap<>();
    
    // 扩展属性
    @Builder.Default
    private Map<String, Object> extraProperties = new HashMap<>();
    
    /**
     * 获取指定生理指标的值
     */
    public Object getValue(String physicalSign) {
        return healthData.get(physicalSign);
    }
    
    /**
     * 设置生理指标值
     */
    public void setValue(String physicalSign, Object value) {
        if (healthData == null) {
            healthData = new HashMap<>();
        }
        healthData.put(physicalSign, value);
    }
    
    /**
     * 获取BigDecimal类型的值
     */
    public BigDecimal getBigDecimalValue(String physicalSign) {
        Object value = getValue(physicalSign);
        if (value == null) {
            return null;
        }
        
        if (value instanceof BigDecimal) {
            return (BigDecimal) value;
        }
        
        try {
            return new BigDecimal(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }
    
    /**
     * 获取扩展属性
     */
    public Object getExtraProperty(String key) {
        return extraProperties.get(key);
    }
    
    /**
     * 设置扩展属性
     */
    public void setExtraProperty(String key, Object value) {
        if (extraProperties == null) {
            extraProperties = new HashMap<>();
        }
        extraProperties.put(key, value);
    }
    
    /**
     * 检查是否包含指定的生理指标
     */
    public boolean hasValue(String physicalSign) {
        return healthData != null && healthData.containsKey(physicalSign);
    }
    
    /**
     * 获取所有生理指标名称
     */
    public java.util.Set<String> getPhysicalSigns() {
        return healthData != null ? healthData.keySet() : java.util.Collections.emptySet();
    }
}