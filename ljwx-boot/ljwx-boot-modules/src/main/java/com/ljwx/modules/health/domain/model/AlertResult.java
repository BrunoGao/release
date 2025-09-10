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
import java.util.List;
import java.util.Map;

/**
 * 告警结果
 * 
 * @Author jjgao
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertResult {
    
    private Long ruleId;
    private String ruleType;
    private String physicalSign;
    private BigDecimal currentValue;
    private String violationType;
    private BigDecimal thresholdMin;
    private BigDecimal thresholdMax;
    private String severityLevel;
    private String alertMessage;
    private List<String> enabledChannels;
    private String deviceSn;
    private Long customerId;
    private Long userId;
    private Long orgId;
    private String latitude;
    private String longitude;
    private Long timestamp;
    private String evaluationContext;
    
    // 扩展信息
    private Map<String, Object> metadata;
    
    /**
     * 获取优先级数值 (用于排序)
     */
    public int getPriorityValue() {
        if (severityLevel == null) {
            return 3; // 默认中等优先级
        }
        
        switch (severityLevel.toLowerCase()) {
            case "critical":
                return 1;
            case "major":
                return 2;
            case "minor":
                return 3;
            case "info":
                return 4;
            default:
                return 3;
        }
    }
    
    /**
     * 是否为高优先级告警
     */
    public boolean isHighPriority() {
        return getPriorityValue() <= 2;
    }
    
    /**
     * 获取告警描述
     */
    public String getAlertDescription() {
        if (alertMessage != null && !alertMessage.isEmpty()) {
            return alertMessage;
        }
        
        // 生成默认描述
        StringBuilder desc = new StringBuilder();
        desc.append("设备 ").append(deviceSn).append(" ");
        
        if ("SINGLE".equals(ruleType)) {
            desc.append(physicalSign).append(" 异常");
            if (currentValue != null) {
                desc.append("，当前值: ").append(currentValue);
            }
            if (thresholdMin != null && thresholdMax != null) {
                desc.append("，正常范围: ").append(thresholdMin).append("-").append(thresholdMax);
            }
        } else if ("COMPOSITE".equals(ruleType)) {
            desc.append("复合指标异常");
            if (evaluationContext != null) {
                desc.append(" (").append(evaluationContext).append(")");
            }
        } else {
            desc.append("健康指标异常");
        }
        
        return desc.toString();
    }
    
    /**
     * 获取抑制键 (用于重复告警抑制)
     */
    public String getSuppressionKey() {
        return String.format("alert:%s:%s:%s", ruleId, deviceSn, physicalSign);
    }
    
    /**
     * 转换为告警信息实体需要的格式
     */
    public Map<String, Object> toAlertInfoMap() {
        Map<String, Object> map = new java.util.HashMap<>();
        map.put("ruleId", ruleId);
        map.put("alertType", ruleType);
        map.put("deviceSn", deviceSn);
        map.put("alertDesc", getAlertDescription());
        map.put("severityLevel", severityLevel);
        map.put("alertStatus", "pending");
        map.put("alertTimestamp", new java.util.Date(timestamp));
        map.put("userId", userId);
        map.put("orgId", orgId);
        map.put("latitude", latitude);
        map.put("longitude", longitude);
        map.put("customerId", customerId);
        
        if (evaluationContext != null) {
            map.put("evaluationContext", evaluationContext);
        }
        
        return map;
    }
}