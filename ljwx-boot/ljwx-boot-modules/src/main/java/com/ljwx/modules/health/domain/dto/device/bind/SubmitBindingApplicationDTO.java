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

/**
* 提交设备绑定申请 DTO 数据传输类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.dto.device.bind.SubmitBindingApplicationDTO
* @CreateTime 2025-08-23
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "提交设备绑定申请 DTO")
public class SubmitBindingApplicationDTO {

    @Schema(description = "设备序列号", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "设备序列号不能为空")
    private String deviceSn;

    @Schema(description = "手机号码", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "手机号码不能为空")
    private String phoneNumber;

    @Schema(description = "申请用户ID", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "申请用户ID不能为空")
    private String userId;

    @Schema(description = "申请时间戳")
    private String timestamp;
}