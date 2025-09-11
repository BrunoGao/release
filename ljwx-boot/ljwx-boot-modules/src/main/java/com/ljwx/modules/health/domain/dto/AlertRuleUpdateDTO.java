package com.ljwx.modules.health.domain.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.math.BigDecimal;

/**
 * 告警规则更新DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertRuleUpdateDTO {

    /**
     * 规则ID
     */
    private Long id;

    /**
     * 规则类型
     */
    private String ruleType;

    /**
     * 生理指标
     */
    private String physicalSign;

    /**
     * 阈值最小值
     */
    private BigDecimal thresholdMin;

    /**
     * 阈值最大值
     */
    private BigDecimal thresholdMax;

    /**
     * 偏差百分比
     */
    private BigDecimal deviationPercentage;

    /**
     * 趋势持续时间
     */
    private Integer trendDuration;

    /**
     * 参数配置
     */
    private String parameters;

    /**
     * 触发条件
     */
    private String triggerCondition;

    /**
     * 告警消息
     */
    private String alertMessage;

    /**
     * 严重程度
     */
    private String severityLevel;

    /**
     * 通知类型
     */
    private String notificationType;

    /**
     * 客户ID
     */
    private Long customerId;

    /**
     * 规则分类
     */
    private String ruleCategory;

    /**
     * 条件表达式
     */
    private Object conditionExpression;

    /**
     * 时间窗口（秒）
     */
    private Integer timeWindowSeconds;

    /**
     * 冷却时间（秒）
     */
    private Integer cooldownSeconds;

    /**
     * 优先级
     */
    private Integer priorityLevel;

    /**
     * 规则标签
     */
    private Object ruleTags;

    /**
     * 生效时间开始
     */
    private java.sql.Time effectiveTimeStart;

    /**
     * 生效时间结束
     */
    private java.sql.Time effectiveTimeEnd;

    /**
     * 生效日期
     */
    private String effectiveDays;

    /**
     * 启用的通知渠道
     */
    private Object enabledChannels;

    /**
     * 是否启用
     */
    private Boolean isEnabled;

    /**
     * 是否启用自动处理
     */
    private Boolean autoProcessEnabled;

    /**
     * 自动处理动作
     */
    private String autoProcessAction;

    /**
     * 自动处理延迟时间（秒）
     */
    private Integer autoProcessDelaySeconds;

    /**
     * 抑制持续时间（分钟）
     */
    private Integer suppressDurationMinutes;

    /**
     * 自动解决阈值计数
     */
    private Integer autoResolveThresholdCount;
}