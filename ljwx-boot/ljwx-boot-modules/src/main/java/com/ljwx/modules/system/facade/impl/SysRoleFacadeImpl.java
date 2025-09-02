package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.domain.Options;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysRoleBO;
import com.ljwx.modules.system.domain.dto.role.SysRoleAddDTO;
import com.ljwx.modules.system.domain.dto.role.SysRoleDeleteDTO;
import com.ljwx.modules.system.domain.dto.role.SysRoleSearchDTO;
import com.ljwx.modules.system.domain.dto.role.SysRoleUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysRole;
import com.ljwx.modules.system.domain.vo.SysRoleVO;
import com.ljwx.modules.system.facade.ISysRoleFacade;
import com.ljwx.modules.system.service.ISysRoleService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 角色管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysRoleFacadeImpl
 * @CreateTime 2023-07-23
 */

@Service
@RequiredArgsConstructor
public class SysRoleFacadeImpl implements ISysRoleFacade {

    @NonNull
    private ISysRoleService sysRoleService;

    @Override
    public RPage<SysRoleVO> listSysRolePage(PageQuery pageQuery, SysRoleSearchDTO sysRoleSearchDTO) {
        SysRoleBO sysRoleBO = CglibUtil.convertObj(sysRoleSearchDTO, SysRoleBO::new);
        IPage<SysRole> sysRoleIPage = sysRoleService.listSysRolePage(pageQuery, sysRoleBO);
        return RPage.build(sysRoleIPage, SysRoleVO::new);
    }

    @Override
    public SysRoleVO get(Long id) {
        SysRole byId = sysRoleService.getById(id);
        return CglibUtil.convertObj(byId, SysRoleVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysRoleAddDTO sysRoleAddDTO) {
        SysRoleBO sysRoleBO = CglibUtil.convertObj(sysRoleAddDTO, SysRoleBO::new);
        return sysRoleService.save(sysRoleBO);
    }

    @Override
    @Transactional
    public boolean update(SysRoleUpdateDTO sysRoleUpdateDTO) {
        SysRoleBO sysRoleBO = CglibUtil.convertObj(sysRoleUpdateDTO, SysRoleBO::new);
        return sysRoleService.updateById(sysRoleBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(SysRoleDeleteDTO sysRoleDeleteDTO) {
        SysRoleBO sysRoleBO = CglibUtil.convertObj(sysRoleDeleteDTO, SysRoleBO::new);
        return sysRoleService.removeBatchByIds(sysRoleBO.getIds());
    }

    @Override
    public List<Options<Long>> queryAllRoleListConvertOptions(Long customerId) {
        List<SysRoleBO> allRole = sysRoleService.queryAllRoleList(customerId);
        return allRole.stream()
                .map(item -> Options.<Long>builder()
                        .label(item.getRoleName())
                        .value(item.getId())
                        .build())
                .toList();
    }
}