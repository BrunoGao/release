package com.ljwx.modules.system.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysRoleBO;
import com.ljwx.modules.system.domain.entity.SysRole;

import java.util.List;

/**
 * 角色管理 Service 服务接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.ISysRoleService
 * @CreateTime 2023-07-15
 */
public interface ISysRoleService extends IService<SysRole> {
    /**
     * 角色管理 - 分页查询
     *
     * @param pageQuery 分页对象
     * @param sysRoleBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2023-07-15 15:10
     */
    IPage<SysRole> listSysRolePage(PageQuery pageQuery, SysRoleBO sysRoleBO);

    /**
     * 获取所有角色信息
     *
     * @return {@linkplain List} 角色集合
     * @author payne.zhuang
     * @CreateTime 2024-04-07 11:51
     */
    List<SysRoleBO> queryAllRoleList();

    /**
     * 根据用户ID查询角色代码列表
     *
     * @param userId 用户ID
     * @return {@link List<String>} 角色代码列表
     * @author payne.zhuang
     * @CreateTime 2024-04-19 12:26
     */
    List<String> queryRoleCodesWithUserId(Long userId);

    /**
     * 根据用户ID查询角色列表
     *
     * @param userId 用户ID
     * @return {@link List<SysRole>} 角色列表集合
     * @author payne.zhuang
     * @CreateTime 2024-04-19 22:32
     */
    List<SysRoleBO> queryRoleListWithUserId(Long userId);
}
