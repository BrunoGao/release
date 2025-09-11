/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.modules.health.domain.dto.alert.rules;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;
import java.math.BigDecimal;

/**
 * 告警规则更新DTO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertRuleUpdateDTO
 * @CreateTime 2025-09-10
 */
@Data
@Schema(description = "告警规则更新DTO")
public class AlertRuleUpdateDTO {

    @NotNull(message = "规则ID不能为空")
    @Schema(description = "规则ID", required = true)
    private Long id;

    @Schema(description = "生理指标")
    private String physicalSign;

    @Schema(description = "阈值最小值")
    private BigDecimal thresholdMin;

    @Schema(description = "阈值最大值")
    private BigDecimal thresholdMax;

    @Schema(description = "严重程度(critical/major/minor/info)")
    private String severityLevel;

    @Schema(description = "告警描述")
    private String alertDesc;

    @Schema(description = "是否启用")
    private Boolean isEnabled;

    @Schema(description = "自动处理是否启用")
    private Boolean autoProcessEnabled;

    @Schema(description = "自动处理动作(AUTO_RESOLVE/AUTO_ACKNOWLEDGE/AUTO_ESCALATE/AUTO_SUPPRESS)")
    private String autoProcessAction;

    @Min(value = 0, message = "延迟秒数不能小于0")
    @Max(value = 86400, message = "延迟秒数不能超过86400秒(24小时)")
    @Schema(description = "自动处理延迟秒数", example = "30")
    private Integer autoProcessDelaySeconds;

    @Min(value = 1, message = "自动解决阈值不能小于1")
    @Max(value = 100, message = "自动解决阈值不能超过100")
    @Schema(description = "自动解决阈值计数", example = "3")
    private Integer autoResolveThresholdCount;

    @Min(value = 1, message = "抑制时长不能小于1分钟")
    @Max(value = 1440, message = "抑制时长不能超过1440分钟(24小时)")
    @Schema(description = "抑制持续时间(分钟)", example = "60")
    private Integer suppressDurationMinutes;

    @Schema(description = "时间窗口(秒)")
    private Integer timeWindowSeconds;

    @Schema(description = "告警类型")
    private String alertType;

    @Schema(description = "事件类型")
    private String eventType;

    @Schema(description = "规则备注")
    private String remark;
}