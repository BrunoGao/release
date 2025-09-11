package com.ljwx.modules.health.domain.vo;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 告警规则统计信息VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertRuleStatsVO {

    /**
     * 总规则数
     */
    private Long totalRules;

    /**
     * 启用的规则数
     */
    private Long enabledRules;

    /**
     * 禁用的规则数
     */
    private Long disabledRules;

    /**
     * 启用自动处理的规则数
     */
    private Long autoProcessEnabledRules;

    /**
     * 按规则类型分组统计
     */
    private Map<String, Long> ruleTypeStats;

    /**
     * 按严重程度分组统计
     */
    private Map<String, Long> severityLevelStats;

    /**
     * 按生理指标分组统计
     */
    private Map<String, Long> physicalSignStats;

    /**
     * 按规则分类分组统计
     */
    private Map<String, Long> ruleCategoryStats;

    /**
     * 按客户分组统计
     */
    private Map<String, Long> customerStats;

    /**
     * 按优先级分组统计
     */
    private Map<String, Long> priorityLevelStats;

    /**
     * 最近24小时触发次数
     */
    private Long triggeredIn24Hours;

    /**
     * 最近7天触发次数
     */
    private Long triggeredIn7Days;

    /**
     * 最近30天触发次数
     */
    private Long triggeredIn30Days;

    /**
     * 平均处理时间（秒）
     */
    private Double avgProcessingTimeSeconds;

    /**
     * 自动处理成功率
     */
    private Double autoProcessSuccessRate;

    /**
     * 最活跃的规则（最近触发最多的前5个）
     */
    private Map<String, Object> mostActiveRules;

    /**
     * 统计时间
     */
    private LocalDateTime statsTime;

    /**
     * 数据更新时间
     */
    private LocalDateTime lastUpdated;
}