package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.baomidou.mybatisplus.extension.toolkit.Db;
import com.google.common.collect.Sets;
import com.ljwx.common.util.CollectionUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysUserRoleBO;
import com.ljwx.modules.system.domain.entity.SysUserRole;
import com.ljwx.modules.system.repository.mapper.SysUserRoleMapper;
import com.ljwx.common.pool.StringPools;
import com.ljwx.modules.system.domain.entity.SysRole;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.enums.AdminLevel;
import com.ljwx.modules.system.domain.enums.UserType;
import com.ljwx.modules.system.service.ISysRoleService;
import com.ljwx.modules.system.service.ISysUserRoleService;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 用户角色管理 Service 服务接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.SysUserRoleServiceImpl
 * @CreateTime 2023-07-24
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SysUserRoleServiceImpl extends ServiceImpl<SysUserRoleMapper, SysUserRole> implements ISysUserRoleService {

    @NonNull
    private ISysRoleService sysRoleService;
    
    @NonNull
    @Lazy
    private ISysUserService sysUserService;

    @Override
    public IPage<SysUserRole> listSysUserRolePage(PageQuery pageQuery, SysUserRoleBO sysUserRoleBO) {
        return baseMapper.selectPage(pageQuery.buildPage(), new LambdaQueryWrapper<>());
    }

    @Override
    public List<Long> queryRoleIdsWithUserId(Long userId) {
        List<SysUserRole> sysUserRoleList = baseMapper.listUserRoleByUserId(userId);
        return sysUserRoleList.stream().map(SysUserRole::getRoleId).toList();
    }

    @Override
    public List<String> queryRoleCodesWithUserId(Long userId) {
        return sysRoleService.queryRoleCodesWithUserId(userId);
    }

    @Override
    public boolean updateUserRole(Long userId, List<Long> roleIds) {
        List<Long> originUserRoleIds = queryRoleIdsWithUserId(userId);
        // 处理数据
        Set<Long> roleIdSet = Sets.newHashSet(roleIds);
        // 处理结果
        AtomicBoolean saveResult = new AtomicBoolean(true);
        CollectionUtil.handleDifference(
                Sets.newHashSet(originUserRoleIds),
                roleIdSet,
                // 处理增加和删除的数据
                (addRoleIdSet, removeRoleIdSet) -> {
                    // 如有删除，则进行删除数据
                    if (!CollectionUtils.isEmpty(removeRoleIdSet)) {
                        LambdaQueryWrapper<SysUserRole> removeQueryWrapper = new LambdaQueryWrapper<SysUserRole>()
                                .eq(SysUserRole::getUserId, userId)
                                .in(SysUserRole::getRoleId, removeRoleIdSet);
                        baseMapper.delete(removeQueryWrapper);
                    }
                    // 进行新增数据
                    if (!CollectionUtils.isEmpty(addRoleIdSet)) {
                        List<SysUserRole> sysUserRoleList = addRoleIdSet.stream()
                                .map(roleId -> new SysUserRole(userId, roleId))
                                .toList();
                        saveResult.set(Db.saveBatch(sysUserRoleList));
                    }
                }
        );
        
        // 同步更新用户类型信息到 sys_user 表
        if (saveResult.get()) {
            try {
                syncUserTypeToSysUser(userId, roleIds);
                log.info("✅ 角色更新后同步用户类型成功: userId={}, roleIds={}", userId, roleIds);
            } catch (Exception e) {
                log.error("❌ 角色更新后同步用户类型失败: userId={}, roleIds={}, error={}", userId, roleIds, e.getMessage(), e);
            }
        }
        
        return saveResult.get();
    }

    /**
     * 同步用户类型信息到 sys_user 表
     */
    @Transactional
    private void syncUserTypeToSysUser(Long userId, List<Long> roleIds) {
        if (userId == null || roleIds == null) {
            return;
        }

        // 获取用户信息
        SysUser user = sysUserService.getById(userId);
        if (user == null) {
            return;
        }

        // 计算用户类型和管理级别
        UserType userType = calculateUserType(user, roleIds);
        AdminLevel adminLevel = calculateAdminLevel(userType);

        // 更新用户类型字段
        SysUser updateUser = new SysUser();
        updateUser.setId(userId);
        updateUser.setUserType(userType.getCode());
        updateUser.setAdminLevel(adminLevel.getCode());

        boolean updated = sysUserService.updateById(updateUser);
        if (updated) {
            log.debug("🔄 用户类型同步成功: userId={}, userType={}, adminLevel={}", 
                    userId, userType.getDescription(), adminLevel.getDescription());
        }
    }

    /**
     * 根据角色计算用户类型
     */
    private UserType calculateUserType(SysUser user, List<Long> roleIds) {
        // 检查是否为超级管理员（admin用户）
        if (StringPools.ADMIN.equalsIgnoreCase(user.getUserName())) {
            return UserType.SUPER_ADMIN;
        }

        // 如果没有角色，返回普通用户
        if (roleIds.isEmpty()) {
            return UserType.NORMAL;
        }

        // 查询角色信息，检查是否有管理员角色
        List<SysRole> roles = sysRoleService.listByIds(roleIds);
        boolean hasAdminRole = roles.stream()
                .anyMatch(role -> role.getIsAdmin() != null && role.getIsAdmin() == 1);

        if (!hasAdminRole) {
            return UserType.NORMAL;
        }

        // 根据组织关系判断管理级别
        // 简化逻辑：有管理角色的用户默认为部门管理员，如果是顶级组织则为租户管理员
        return isInTopLevelOrg(user) ? UserType.TENANT_ADMIN : UserType.DEPT_ADMIN;
    }

    /**
     * 根据用户类型计算管理级别
     */
    private AdminLevel calculateAdminLevel(UserType userType) {
        switch (userType) {
            case SUPER_ADMIN:
                return AdminLevel.SYSTEM_LEVEL;
            case TENANT_ADMIN:
                return AdminLevel.TENANT_LEVEL;
            case DEPT_ADMIN:
                return AdminLevel.DEPT_LEVEL;
            default:
                return AdminLevel.NONE;
        }
    }

    /**
     * 检查用户是否在顶级组织
     */
    private boolean isInTopLevelOrg(SysUser user) {
        // 简化判断：如果用户的组织ID为空或者是顶级组织（parentId为null、0、1），则认为是顶级组织
        Long orgId = user.getOrgId();
        if (orgId == null) {
            return false;
        }
        
        // 这里可以根据实际的组织结构进行更复杂的判断
        // 暂时简化为：orgId <= 10 的认为是顶级组织
        return orgId <= 10L;
    }
}
