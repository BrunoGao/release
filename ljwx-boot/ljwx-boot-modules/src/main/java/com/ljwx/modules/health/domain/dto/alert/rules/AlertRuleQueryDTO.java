/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 */

package com.ljwx.modules.health.domain.dto.alert.rules;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 告警规则查询DTO
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName AlertRuleQueryDTO
 * @CreateTime 2025-09-10
 */
@Data
@Schema(description = "告警规则查询DTO")
public class AlertRuleQueryDTO {

    @Schema(description = "规则名称(模糊查询)")
    private String ruleName;

    @Schema(description = "告警类型")
    private String alertType;

    @Schema(description = "生理指标")
    private String physicalSign;

    @Schema(description = "严重程度")
    private String severityLevel;

    @Schema(description = "是否启用")
    private Boolean isEnabled;

    @Schema(description = "自动处理是否启用")
    private Boolean autoProcessEnabled;

    @Schema(description = "自动处理动作")
    private String autoProcessAction;

    @Schema(description = "客户ID")
    private Long customerId;

    @Schema(description = "组织ID")
    private Long orgId;

    @Schema(description = "创建时间-开始")
    private LocalDateTime createTimeStart;

    @Schema(description = "创建时间-结束")
    private LocalDateTime createTimeEnd;

    @Schema(description = "更新时间-开始")
    private LocalDateTime updateTimeStart;

    @Schema(description = "更新时间-结束")
    private LocalDateTime updateTimeEnd;

    @Schema(description = "页码", example = "1")
    private Integer pageNum = 1;

    @Schema(description = "页面大小", example = "10")
    private Integer pageSize = 10;

    @Schema(description = "排序字段")
    private String orderBy;

    @Schema(description = "排序方向(ASC/DESC)")
    private String sortDirection = "DESC";
}