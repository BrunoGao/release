/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.modules.health.domain.vo.alert;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 告警规则统计VO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertRuleStatsVO
 * @CreateTime 2025-09-10
 */
@Data
@Builder
@Schema(description = "告警规则统计VO")
public class AlertRuleStatsVO {

    @Schema(description = "总规则数")
    private Long totalRules;

    @Schema(description = "启用规则数")
    private Long enabledRules;

    @Schema(description = "自动处理启用规则数")
    private Long autoProcessEnabledRules;

    @Schema(description = "禁用规则数")
    private Long disabledRules;

    @Schema(description = "自动处理覆盖率(%)")
    private Double autoProcessCoverageRate;

    @Schema(description = "按动作类型统计")
    private Map<String, Long> actionStats;

    @Schema(description = "按严重程度统计")
    private Map<String, Long> severityStats;

    @Schema(description = "按告警类型统计")
    private Map<String, Long> alertTypeStats;

    @Schema(description = "按生理指标统计")
    private Map<String, Long> physicalSignStats;

    @Schema(description = "最近24小时自动处理次数")
    private Long recentAutoProcessCount;

    @Schema(description = "最近24小时自动处理成功率(%)")
    private Double recentAutoProcessSuccessRate;

    @Schema(description = "平均处理延迟时间(秒)")
    private Double averageProcessDelaySeconds;

    @Schema(description = "统计时间")
    private LocalDateTime statsTime;

    @Schema(description = "数据更新时间")
    private LocalDateTime lastUpdateTime;

    public Long getDisabledRules() {
        if (disabledRules != null) {
            return disabledRules;
        }
        return totalRules != null && enabledRules != null ? totalRules - enabledRules : 0L;
    }

    public Double getAutoProcessCoverageRate() {
        if (autoProcessCoverageRate != null) {
            return autoProcessCoverageRate;
        }
        if (totalRules != null && totalRules > 0 && autoProcessEnabledRules != null) {
            return (double) autoProcessEnabledRules / totalRules * 100;
        }
        return 0.0;
    }
}