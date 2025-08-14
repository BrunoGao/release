package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.common.util.StringUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysUserBO;
import com.ljwx.modules.system.domain.bo.SysUserResponsibilitiesBO;
import com.ljwx.modules.system.domain.dto.user.*;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.vo.SysUserResponsibilitiesVO;
import com.ljwx.modules.system.domain.vo.SysUserVO;
import com.ljwx.modules.system.facade.ISysUserFacade;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;

/**
 * 用户管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysUserFacadeImpl
 * @CreateTime 2023/7/6 - 16:06
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysUserFacadeImpl implements ISysUserFacade {

    @NonNull
    private ISysUserService sysUserService;

    @Override
    public RPage<SysUserVO> listSysUserPage(PageQuery pageQuery, SysUserSearchDTO sysUserSearchDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserSearchDTO, SysUserBO::new);
        sysUserBO.setOrgIds(StringUtil.toLongList(sysUserSearchDTO.getOrgIds()));
        IPage<SysUser> sysUserIPage = sysUserService.listSysUserPage(pageQuery, sysUserBO);
        RPage<SysUserVO> result = RPage.build(sysUserIPage, SysUserVO::new);
        // 设置用户类型标识
        result.getRecords().forEach(user -> {
            boolean isAdmin = sysUserService.isAdminUser(user.getId());
            user.setIsAdmin(isAdmin);
            user.setUserType(isAdmin ? "ADMIN" : "EMPLOYEE");
        });
        return result;
    }

    @Override
    public RPage<SysUserVO> listNonAdminUsersPage(PageQuery pageQuery, SysUserSearchDTO sysUserSearchDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserSearchDTO, SysUserBO::new);
        sysUserBO.setOrgIds(StringUtil.toLongList(sysUserSearchDTO.getOrgIds()));
        IPage<SysUser> sysUserIPage = sysUserService.listNonAdminUsersPage(pageQuery, sysUserBO);
        RPage<SysUserVO> result = RPage.build(sysUserIPage, SysUserVO::new);
        // 员工视图：全部为非管理员
        result.getRecords().forEach(user -> {
            user.setIsAdmin(false);
            user.setUserType("EMPLOYEE");
        });
        return result;
    }

    @Override
    public RPage<SysUserVO> listAdminUsersPage(PageQuery pageQuery, SysUserSearchDTO sysUserSearchDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserSearchDTO, SysUserBO::new);
        sysUserBO.setOrgIds(StringUtil.toLongList(sysUserSearchDTO.getOrgIds()));
        IPage<SysUser> sysUserIPage = sysUserService.listAdminUsersPage(pageQuery, sysUserBO);
        RPage<SysUserVO> result = RPage.build(sysUserIPage, SysUserVO::new);
        // 管理员视图：全部为管理员
        result.getRecords().forEach(user -> {
            user.setIsAdmin(true);
            user.setUserType("ADMIN");
        });
        return result;
    }

    @Override
    public SysUserVO get(Long id) {
        SysUser byId = sysUserService.getById(id);
        return CglibUtil.convertObj(byId, SysUserVO::new);
    }

    @Override
    @Transactional
    public boolean addUser(SysUserAddDTO sysUserAddDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserAddDTO, SysUserBO::new);
        return sysUserService.addUser(sysUserBO);
    }

    @Override
    @Transactional
    public boolean updateUser(SysUserUpdateDTO sysUserUpdateDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserUpdateDTO, SysUserBO::new);
        return sysUserService.updateUser(sysUserBO);
    }

    @Override
    @Transactional
    public boolean batchDeleteUser(SysUserDeleteDTO sysUserDeleteDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserDeleteDTO, SysUserBO::new);
        return sysUserService.removeBatchByIds(sysUserBO.getIds());
    }

    @Override
    public List<Map<String, Object>> checkUserDeviceBinding(SysUserDeleteDTO sysUserDeleteDTO) {
        SysUserBO sysUserBO = CglibUtil.convertObj(sysUserDeleteDTO, SysUserBO::new);
        return sysUserService.checkUserDeviceBinding(sysUserBO.getIds());
    }



    @Override
    @Transactional
    public String resetPassword(Long userId) {
        return sysUserService.resetPassword(userId);
    }

    @Override
    public SysUserResponsibilitiesVO queryUserResponsibilitiesWithUserId(Long userId) {
        SysUserResponsibilitiesBO responsibilitiesBO = sysUserService.queryUserResponsibilitiesWithUserId(userId);
        return CglibUtil.convertObj(responsibilitiesBO, SysUserResponsibilitiesVO::new);
    }

    @Override
    @Transactional
    public boolean updateUserResponsibilities(SysUserResponsibilitiesUpdateDTO updateDTO) {
        SysUserResponsibilitiesBO responsibilitiesBO = CglibUtil.convertObj(updateDTO, SysUserResponsibilitiesBO::new);
        return sysUserService.updateUserResponsibilities(responsibilitiesBO);
    }

    @Override
    public List getUnbindDevice(Long customerId) {
        return sysUserService.getUnbindDevice(customerId);
    }

    @Override
    public List getBindDevice(Long customerId) {
        return sysUserService.getBindDevice(customerId);
    }
}
