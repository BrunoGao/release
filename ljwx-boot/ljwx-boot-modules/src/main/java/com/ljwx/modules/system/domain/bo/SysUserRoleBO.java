package com.ljwx.modules.system.domain.bo;

import com.ljwx.modules.system.domain.entity.SysUserRole;
import lombok.Data;

import java.io.Serial;
import java.util.List;

/**
 * 用户角色管理 BO 业务处理对象
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.bo.SysUserRoleBO
 * @CreateTime 2023-07-24
 */
@Data
public class SysUserRoleBO extends SysUserRole {

    @Serial
    private static final long serialVersionUID = -5554870308593158543L;

    /**
     * Ids
     */
    private List<Long> ids;

}