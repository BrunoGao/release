package com.ljwx.modules.system.domain.vo;

import com.ljwx.infrastructure.domain.BaseVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.io.Serial;

/**
 * 角色管理 VO 展示类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.entity.SysRole
 * @CreateTime 2023-07-15
 */
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "SysRoleVO", description = "角色管理 VO 对象")
public class SysRoleVO extends BaseVO {

    @Serial
    private static final long serialVersionUID = 5617979161002086574L;

    @Schema(description = "父主键")
    private Long parentId;

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

    @Schema(description = "管理员级别(0:超级管理员,1:租户管理员,2:部门管理员)")
    private Integer adminLevel;

    @Schema(description = "租户ID")
    private Long customerId;
}