package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysRolePermissionBO;
import com.ljwx.modules.system.domain.dto.role.permission.SysRolePermissionAddDTO;
import com.ljwx.modules.system.domain.dto.role.permission.SysRolePermissionDeleteDTO;
import com.ljwx.modules.system.domain.dto.role.permission.SysRolePermissionSearchDTO;
import com.ljwx.modules.system.domain.dto.role.permission.SysRolePermissionUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysRolePermission;
import com.ljwx.modules.system.domain.vo.SysRolePermissionVO;
import com.ljwx.modules.system.facade.ISysRolePermissionFacade;
import com.ljwx.modules.system.service.ISysRolePermissionService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 角色权限管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysRolePermissionFacadeImpl
 * @CreateTime 2023-08-05
 */

@Service
@RequiredArgsConstructor
public class SysRolePermissionFacadeImpl implements ISysRolePermissionFacade {

    @NonNull
    private ISysRolePermissionService sysRolePermissionService;

    @Override
    public RPage<SysRolePermissionVO> listSysRolePermissionPage(PageQuery pageQuery, SysRolePermissionSearchDTO sysRolePermissionSearchDTO) {
        SysRolePermissionBO sysRolePermissionBO = CglibUtil.convertObj(sysRolePermissionSearchDTO, SysRolePermissionBO::new);
        IPage<SysRolePermission> sysRolePermissionIPage = sysRolePermissionService.listSysRolePermissionPage(pageQuery, sysRolePermissionBO);
        return RPage.build(sysRolePermissionIPage, SysRolePermissionVO::new);
    }

    @Override
    public SysRolePermissionVO get(Long id) {
        SysRolePermission byId = sysRolePermissionService.getById(id);
        return CglibUtil.convertObj(byId, SysRolePermissionVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysRolePermissionAddDTO sysRolePermissionAddDTO) {
        SysRolePermissionBO sysRolePermissionBO = CglibUtil.convertObj(sysRolePermissionAddDTO, SysRolePermissionBO::new);
        return sysRolePermissionService.add(sysRolePermissionBO);
    }

    @Override
    @Transactional
    public boolean update(SysRolePermissionUpdateDTO sysRolePermissionUpdateDTO) {
        SysRolePermissionBO sysRolePermissionBO = CglibUtil.convertObj(sysRolePermissionUpdateDTO, SysRolePermissionBO::new);
        return sysRolePermissionService.updateById(sysRolePermissionBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(SysRolePermissionDeleteDTO sysRolePermissionDeleteDTO) {
        SysRolePermissionBO sysRolePermissionBO = CglibUtil.convertObj(sysRolePermissionDeleteDTO, SysRolePermissionBO::new);
        return sysRolePermissionService.removeBatchByIds(sysRolePermissionBO.getIds(), true);
    }

    @Override
    public List<Long> queryPermissionIdsWithRoleId(Long roleId) {
        return sysRolePermissionService.queryPermissionIdsWithRoleId(roleId);
    }

    @Override
    @Transactional
    public boolean addPermissionForRoleId(Long roleId, List<Long> permissionIds) {
        return sysRolePermissionService.addPermissionForRoleId(roleId, permissionIds);
    }
}