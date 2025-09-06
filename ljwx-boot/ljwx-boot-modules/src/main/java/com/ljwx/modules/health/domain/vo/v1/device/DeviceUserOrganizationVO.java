/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.domain.vo.v1.device;

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "DeviceUserOrganizationVO", description = "设备用户组织 VO 对象")
public class DeviceUserOrganizationVO extends BaseVO {
    
    @Schema(description = "设备序列号")
    private String deviceSn;
    
    @Schema(description = "用户ID")
    private String userId;
    
    @Schema(description = "组织ID")
    private String orgId;
    
    @Schema(description = "组织名称")
    private String orgName;
}