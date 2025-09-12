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
import com.ljwx.modules.system.service.ISysRoleService;
import com.ljwx.modules.system.service.ISysUserRoleService;
import com.ljwx.modules.system.service.IUserTypeSyncService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
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
    private IUserTypeSyncService userTypeSyncService;

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
        
        // 同步更新用户类型信息（角色变更影响用户类型和管理级别）
        if (saveResult.get()) {
            try {
                userTypeSyncService.syncUserTypeFromRoles(userId, roleIds);
                log.info("✅ 角色更新后同步用户类型成功: userId={}, roleIds={}", userId, roleIds);
            } catch (Exception e) {
                log.error("❌ 角色更新后同步用户类型失败: userId={}, roleIds={}, error={}", userId, roleIds, e.getMessage(), e);
            }
        }
        
        return saveResult.get();
    }
}
