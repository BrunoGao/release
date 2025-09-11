package com.ljwx.modules.health.domain.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;

/**
 * 告警规则查询DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AlertRuleQueryDTO {

    /**
     * 规则类型
     */
    private String ruleType;

    /**
     * 生理指标
     */
    private String physicalSign;

    /**
     * 严重程度
     */
    private String severityLevel;

    /**
     * 是否启用
     */
    private Boolean isEnabled;

    /**
     * 客户ID
     */
    private Long customerId;

    /**
     * 规则分类
     */
    private String ruleCategory;

    /**
     * 优先级范围 - 最小值
     */
    private Integer priorityLevelMin;

    /**
     * 优先级范围 - 最大值
     */
    private Integer priorityLevelMax;

    /**
     * 创建时间范围 - 开始
     */
    private LocalDateTime createTimeStart;

    /**
     * 创建时间范围 - 结束
     */
    private LocalDateTime createTimeEnd;

    /**
     * 是否启用自动处理
     */
    private Boolean autoProcessEnabled;

    /**
     * 关键词搜索（规则名称、描述等）
     */
    private String keyword;

    /**
     * 页码
     */
    private Integer pageNum = 1;

    /**
     * 页大小
     */
    private Integer pageSize = 10;
}