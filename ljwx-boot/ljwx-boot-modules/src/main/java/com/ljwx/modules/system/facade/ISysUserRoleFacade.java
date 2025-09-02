package com.ljwx.modules.system.facade;

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleAddDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleDeleteDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleSearchDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleUpdateDTO;
import com.ljwx.modules.system.domain.vo.SysUserRoleVO;

/**
 * 用户角色管理 门面接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.domain.entity.ISysUserRoleFacade
 * @CreateTime 2023-07-24
 */

public interface ISysUserRoleFacade {

    /**
     * 用户角色管理 - 分页查询
     *
     * @param pageQuery            分页对象
     * @param sysUserRoleSearchDTO 查询对象
     * @return {@link RPage} 查询结果
     * @author payne.zhuang
     * @CreateTime 2023-07-24 15:10
     */
    RPage<SysUserRoleVO> listSysUserRolePage(PageQuery pageQuery, SysUserRoleSearchDTO sysUserRoleSearchDTO);

    /**
     * 根据 ID 获取详情信息
     *
     * @param id 用户角色ID
     * @return {@link SysUserRoleVO} 用户角色 VO 对象
     * @author payne.zhuang
     * @CreateTime 2023-07-24 15:10
     */
    SysUserRoleVO get(Long id);

    /**
     * 新增用户角色
     *
     * @param sysUserRoleAddDTO 新增用户角色 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2023-07-24 15:10
     */
    boolean add(SysUserRoleAddDTO sysUserRoleAddDTO);

    /**
     * 编辑更新用户角色信息
     *
     * @param sysUserRoleUpdateDTO 编辑更新 DTO 对象
     * @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2023-07-24 15:10
     */
    boolean update(SysUserRoleUpdateDTO sysUserRoleUpdateDTO);

    /**
     * 批量删除用户信息
     *
     * @param sysUserRoleDeleteDTO 删除 DTO 对象
     * @return @return {@link Boolean} 结果
     * @author payne.zhuang
     * @CreateTime 2023-07-24 15:10
     */
    boolean batchDelete(SysUserRoleDeleteDTO sysUserRoleDeleteDTO);

}