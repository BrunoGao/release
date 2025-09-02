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
* 检查设备绑定状态 DTO 数据传输类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.domain.dto.device.bind.CheckDeviceBindingDTO
* @CreateTime 2025-08-23
*/

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "检查设备绑定状态 DTO")
public class CheckDeviceBindingDTO {

    @Schema(description = "设备序列号", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "设备序列号不能为空")
    private String serialNumber;

    @Schema(description = "手机号码", requiredMode = Schema.RequiredMode.REQUIRED)
    @NotBlank(message = "手机号码不能为空")
    private String phoneNumber;
}