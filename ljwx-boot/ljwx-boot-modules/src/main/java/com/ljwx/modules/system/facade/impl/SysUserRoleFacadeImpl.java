package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysUserRoleBO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleAddDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleDeleteDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleSearchDTO;
import com.ljwx.modules.system.domain.dto.user.role.SysUserRoleUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysUserRole;
import com.ljwx.modules.system.domain.vo.SysUserRoleVO;
import com.ljwx.modules.system.facade.ISysUserRoleFacade;
import com.ljwx.modules.system.service.ISysUserRoleService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 用户角色管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysUserRoleFacadeImpl
 * @CreateTime 2023-07-24
 */

@Service
@RequiredArgsConstructor
public class SysUserRoleFacadeImpl implements ISysUserRoleFacade {

    @NonNull
    private ISysUserRoleService sysUserRoleService;

    @Override
    public RPage<SysUserRoleVO> listSysUserRolePage(PageQuery pageQuery, SysUserRoleSearchDTO sysUserRoleSearchDTO) {
        SysUserRoleBO sysUserRoleBO = CglibUtil.convertObj(sysUserRoleSearchDTO, SysUserRoleBO::new);
        IPage<SysUserRole> sysUserRoleIPage = sysUserRoleService.listSysUserRolePage(pageQuery, sysUserRoleBO);
        return RPage.build(sysUserRoleIPage, SysUserRoleVO::new);
    }

    @Override
    public SysUserRoleVO get(Long id) {
        SysUserRole byId = sysUserRoleService.getById(id);
        return CglibUtil.convertObj(byId, SysUserRoleVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysUserRoleAddDTO sysUserRoleAddDTO) {
        SysUserRoleBO sysUserRoleBO = CglibUtil.convertObj(sysUserRoleAddDTO, SysUserRoleBO::new);
        return sysUserRoleService.save(sysUserRoleBO);
    }

    @Override
    @Transactional
    public boolean update(SysUserRoleUpdateDTO sysUserRoleUpdateDTO) {
        SysUserRoleBO sysUserRoleBO = CglibUtil.convertObj(sysUserRoleUpdateDTO, SysUserRoleBO::new);
        return sysUserRoleService.updateById(sysUserRoleBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(SysUserRoleDeleteDTO sysUserRoleDeleteDTO) {
        SysUserRoleBO sysUserRoleBO = CglibUtil.convertObj(sysUserRoleDeleteDTO, SysUserRoleBO::new);
        return sysUserRoleService.removeBatchByIds(sysUserRoleBO.getIds(), true);
    }

}