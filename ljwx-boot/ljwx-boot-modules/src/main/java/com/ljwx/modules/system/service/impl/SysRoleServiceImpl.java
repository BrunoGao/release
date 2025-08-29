package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.common.exception.BizException;
import com.ljwx.common.pool.StringPools;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysRoleBO;
import com.ljwx.modules.system.domain.entity.SysRole;
import com.ljwx.modules.system.repository.mapper.SysRoleMapper;
import com.ljwx.modules.system.service.ISysRoleService;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.stereotype.Service;

import java.util.Collection;
import java.util.List;

/**
 * 角色管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysRoleServiceImpl
 * @CreateTime 2023-07-15
 */
@Service
public class SysRoleServiceImpl extends ServiceImpl<SysRoleMapper, SysRole> implements ISysRoleService {

    @Override
    public IPage<SysRole> listSysRolePage(PageQuery pageQuery, SysRoleBO sysRoleBO) {
        var queryWrapper = new LambdaQueryWrapper<SysRole>()
                .like(ObjectUtils.isNotEmpty(sysRoleBO.getRoleName()), SysRole::getRoleName, sysRoleBO.getRoleName())
                .like(ObjectUtils.isNotEmpty(sysRoleBO.getRoleCode()), SysRole::getRoleCode, sysRoleBO.getRoleCode())
                .eq(ObjectUtils.isNotEmpty(sysRoleBO.getStatus()), SysRole::getStatus, sysRoleBO.getStatus())
                .eq(ObjectUtils.isNotEmpty(sysRoleBO.getCustomerId()), SysRole::getCustomerId, sysRoleBO.getCustomerId())
                .orderByAsc(SysRole::getSort);
        return baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);
    }

    @Override
    public boolean removeBatchByIds(Collection<?> list) {
        LambdaQueryWrapper<SysRole> queryWrapper = new LambdaQueryWrapper<SysRole>().in(SysRole::getId, list);
        baseMapper.selectList(queryWrapper)
                .stream().filter(sysRole -> StringPools.ADMIN.equalsIgnoreCase(sysRole.getRoleCode())).findFirst()
                .ifPresent(sysRole -> {
                    throw new BizException("系统管理员角色不允许删除");
                });
        return super.removeByIds(list, true);
    }

    @Override
    public List<SysRoleBO> queryAllRoleList(Long customerId) {
        var queryWrapper = new LambdaQueryWrapper<SysRole>()
                .eq(ObjectUtils.isNotEmpty(customerId), SysRole::getCustomerId, customerId)
                .orderByAsc(SysRole::getSort);
        return CglibUtil.convertList(baseMapper.selectList(queryWrapper), SysRoleBO::new);
    }

    @Override
    public List<String> queryRoleCodesWithUserId(Long userId) {
        List<SysRole> sysRoles = baseMapper.queryRoleListWithUserId(userId);
        return sysRoles.stream().map(SysRole::getRoleCode).toList();
    }

    @Override
    public List<SysRoleBO> queryRoleListWithUserId(Long userId) {
        List<SysRole> sysRoles = baseMapper.queryRoleListWithUserId(userId);
        return CglibUtil.convertList(sysRoles, SysRoleBO::new);
    }
}
