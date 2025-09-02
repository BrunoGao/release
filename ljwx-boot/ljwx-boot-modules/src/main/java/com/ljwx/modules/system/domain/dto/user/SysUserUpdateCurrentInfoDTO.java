package com.ljwx.modules.system.domain.dto.user;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;

/**
 * 用户管理 - 当前用户更新个人信息 DTO 对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.dto.user.SysUserUpdateCurrentInfoDTO
 * @CreateTime 2024/1/26 - 14:54
 */
@Getter
@Setter
public class SysUserUpdateCurrentInfoDTO implements Serializable {
    @Serial
    private static final long serialVersionUID = 2935137173366166569L;

    @Schema(description = "ID")
    private Long id;

    @Schema(description = "昵称")
    private String nickName;

    @Schema(description = "真名")
    private String realName;

    @Schema(description = "头像")
    private String avatar;

    @Schema(description = "邮箱")
    private String email;

    @Schema(description = "手机")
    private String phone;

    @Schema(description = "性别 0保密 1男 2女")
    private String gender;

    @Schema(description = "是否启用(0:禁用,1:启用)")
    private String status;

    @Schema(description = "设备序列号")
    private String deviceSn;

    @Schema(description = "工龄")
    private Integer currentWorkingYears;

    @Schema(description = "客户ID")
    private Long customerId;
}
