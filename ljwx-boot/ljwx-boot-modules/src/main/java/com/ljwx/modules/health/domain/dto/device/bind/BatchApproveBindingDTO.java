/*
* All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
* Open Source Agreement: Apache License, Version 2.0
*/

package com.ljwx.modules.health.domain.dto.device.bind;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

/**
* 批量审批设备绑定申请 DTO 数据传输类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.dto.device.bind.BatchApproveBindingDTO
* @CreateTime 2025-08-23
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "批量审批设备绑定申请 DTO")
public class BatchApproveBindingDTO {

    @Schema(description = "申请ID列表", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotEmpty(message = "申请ID列表不能为空")
    private List<String> ids;

    @Schema(description = "审批操作 (APPROVED:通过, REJECTED:拒绝)", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "审批操作不能为空")
    private String action;

    @Schema(description = "审批人ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "审批人ID不能为空")
    private String approverId;

    @Schema(description = "审批备注")
    private String comment;
}