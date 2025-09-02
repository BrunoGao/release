package com.ljwx.modules.system.domain.dto.role;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;

/**
 * 角色管理 编辑更新 DTO 对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.dto.SysRoleUpdateDTO
 * @CreateTime 2023-07-23
 */
@Getter
@Setter
@Schema(name = "SysRoleUpdateDTO", description = "角色管理 编辑更新 DTO 对象")
public class SysRoleUpdateDTO implements Serializable {

    @Serial
    private static final long serialVersionUID = -7489005408436078733L;

    @Schema(description = "ID")
    private Long id;

    @Schema(description = "角色名称")
    private String roleName;

    @Schema(description = "角色编码")
    private String roleCode;

    @Schema(description = "描述")
    private String description;

    @Schema(description = "排序")
    private Integer sort;

    @Schema(description = "是否启用(0:禁用,1:启用)")
    private String status;

    @Schema(description = "是否为管理员角色(0:普通角色,1:管理员角色)")
    private Integer isAdmin;
}