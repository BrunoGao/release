package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysPermissionBO;
import com.ljwx.modules.system.domain.dto.permission.SysPermissionAddDTO;
import com.ljwx.modules.system.domain.dto.permission.SysPermissionDeleteDTO;
import com.ljwx.modules.system.domain.dto.permission.SysPermissionSearchDTO;
import com.ljwx.modules.system.domain.dto.permission.SysPermissionUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysPermission;
import com.ljwx.modules.system.domain.vo.SysPermissionVO;
import com.ljwx.modules.system.facade.ISysPermissionFacade;
import com.ljwx.modules.system.service.ISysPermissionService;
import com.ljwx.modules.system.service.ISysRolePermissionService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 权限管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysPermissionFacadeImpl
 * @CreateTime 2023-08-05
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class SysPermissionFacadeImpl implements ISysPermissionFacade {

    @NonNull
    private ISysPermissionService sysPermissionService;

    @NonNull
    private ISysRolePermissionService sysRolePermissionService;

    @Override
    public RPage<SysPermissionVO> listSysPermissionPage(PageQuery pageQuery, SysPermissionSearchDTO sysPermissionSearchDTO) {
        SysPermissionBO sysPermissionBO = CglibUtil.convertObj(sysPermissionSearchDTO, SysPermissionBO::new);
        IPage<SysPermission> sysPermissionIPage = sysPermissionService.listSysPermissionPage(pageQuery, sysPermissionBO);
        return RPage.build(sysPermissionIPage, SysPermissionVO::new);
    }

    @Override
    public SysPermissionVO get(Long id) {
        SysPermission byId = sysPermissionService.getById(id);
        return CglibUtil.convertObj(byId, SysPermissionVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysPermissionAddDTO sysPermissionAddDTO) {
        SysPermissionBO sysPermissionBO = CglibUtil.convertObj(sysPermissionAddDTO, SysPermissionBO::new);
        return sysPermissionService.add(sysPermissionBO);
    }

    @Override
    @Transactional
    public boolean update(SysPermissionUpdateDTO sysPermissionUpdateDTO) {
        SysPermissionBO sysPermissionBO = CglibUtil.convertObj(sysPermissionUpdateDTO, SysPermissionBO::new);
        boolean update = sysPermissionService.updateById(sysPermissionBO);
        sysRolePermissionService.deleteRolePermissionCacheWithRoleId(sysPermissionBO.getId());
        return update;
    }

    @Override
    @Transactional
    public boolean batchDelete(SysPermissionDeleteDTO sysPermissionDeleteDTO) {
        SysPermissionBO sysPermissionBO = CglibUtil.convertObj(sysPermissionDeleteDTO, SysPermissionBO::new);
        boolean batchByIds = sysPermissionService.removeBatchByIds(sysPermissionBO.getIds(), true);
        sysRolePermissionService.deleteRolePermissionCacheWithRoleId(sysPermissionBO.getId());
        return batchByIds;
    }
}