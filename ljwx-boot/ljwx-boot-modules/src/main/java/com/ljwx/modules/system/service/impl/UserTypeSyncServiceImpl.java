/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.system.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.common.pool.StringPools;
import com.ljwx.modules.system.domain.entity.*;
import com.ljwx.modules.system.domain.enums.AdminLevel;
import com.ljwx.modules.system.domain.enums.UserType;
import com.ljwx.modules.system.service.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * 用户类型同步服务实现
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.impl.UserTypeSyncServiceImpl
 * @CreateTime 2025-09-12 - 16:35:30
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class UserTypeSyncServiceImpl implements IUserTypeSyncService {

    private final ISysUserService sysUserService;
    private final ISysRoleService sysRoleService;
    private final ISysUserRoleService sysUserRoleService;
    private final ISysUserOrgService sysUserOrgService;
    private final ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public UserType calculateUserTypeFromRoles(Long userId, List<Long> roleIds) {
        if (userId == null || roleIds == null || roleIds.isEmpty()) {
            return UserType.NORMAL;
        }

        // 检查是否为超级管理员（admin用户）
        SysUser user = sysUserService.getById(userId);
        if (user != null && StringPools.ADMIN.equalsIgnoreCase(user.getUserName())) {
            return UserType.SUPER_ADMIN;
        }

        // 查询角色信息
        List<SysRole> roles = sysRoleService.listByIds(roleIds);
        boolean hasAdminRole = roles.stream()
                .anyMatch(role -> role.getIsAdmin() != null && role.getIsAdmin() == 1);

        if (!hasAdminRole) {
            return UserType.NORMAL;
        }

        // 根据组织关系判断管理级别
        return calculateUserTypeFromOrg(userId);
    }

    @Override
    public AdminLevel calculateAdminLevelFromRoles(Long userId, List<Long> roleIds) {
        UserType userType = calculateUserTypeFromRoles(userId, roleIds);
        
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

    @Override
    @Transactional
    public boolean syncUserTypeFromRoles(Long userId) {
        if (userId == null) {
            return false;
        }

        // 获取用户当前角色
        List<Long> roleIds = sysUserRoleService.list(new LambdaQueryWrapper<SysUserRole>()
                .eq(SysUserRole::getUserId, userId)
                .eq(SysUserRole::getDeleted, false))
                .stream()
                .map(SysUserRole::getRoleId)
                .collect(Collectors.toList());

        return syncUserTypeFromRoles(userId, roleIds);
    }

    @Override
    @Transactional
    public boolean syncUserTypeFromRoles(Long userId, List<Long> roleIds) {
        try {
            UserType userType = calculateUserTypeFromRoles(userId, roleIds);
            AdminLevel adminLevel = calculateAdminLevelFromRoles(userId, roleIds);

            // 更新用户类型字段
            SysUser updateUser = new SysUser();
            updateUser.setId(userId);
            updateUser.setUserType(userType.getCode());
            updateUser.setAdminLevel(adminLevel.getCode());

            boolean result = sysUserService.updateById(updateUser);
            
            if (result) {
                log.info("✅ 用户类型同步成功: userId={}, userType={}, adminLevel={}", 
                        userId, userType.getDescription(), adminLevel.getDescription());
            } else {
                log.error("❌ 用户类型同步失败: userId={}", userId);
            }
            
            return result;
        } catch (Exception e) {
            log.error("❌ 用户类型同步异常: userId={}, error={}", userId, e.getMessage(), e);
            return false;
        }
    }

    @Override
    @Transactional
    public int batchSyncUserTypes(List<Long> userIds) {
        if (userIds == null || userIds.isEmpty()) {
            return 0;
        }

        int successCount = 0;
        for (Long userId : userIds) {
            if (syncUserTypeFromRoles(userId)) {
                successCount++;
            }
        }

        log.info("📊 批量用户类型同步完成: 总数={}, 成功={}, 失败={}", 
                userIds.size(), successCount, userIds.size() - successCount);
        return successCount;
    }

    @Override
    @Transactional
    public boolean recalculateUserAdminLevel(Long userId) {
        try {
            SysUser user = sysUserService.getById(userId);
            if (user == null) {
                return false;
            }

            // 如果不是管理员，无需重新计算
            if (user.getUserType() == null || user.getUserType().equals(UserType.NORMAL.getCode())) {
                return true;
            }

            // 重新计算管理级别
            UserType newUserType = calculateUserTypeFromOrg(userId);
            AdminLevel newAdminLevel = AdminLevel.fromCode(newUserType.getCode());

            // 更新管理级别
            if (!Objects.equals(newUserType.getCode(), user.getUserType()) || 
                !Objects.equals(newAdminLevel.getCode(), user.getAdminLevel())) {
                
                SysUser updateUser = new SysUser();
                updateUser.setId(userId);
                updateUser.setUserType(newUserType.getCode());
                updateUser.setAdminLevel(newAdminLevel.getCode());

                boolean result = sysUserService.updateById(updateUser);
                
                if (result) {
                    log.info("🔄 用户管理级别重新计算成功: userId={}, userType={}->{}, adminLevel={}->{}", 
                            userId, UserType.fromCode(user.getUserType()).getDescription(), newUserType.getDescription(),
                            AdminLevel.fromCode(user.getAdminLevel()).getDescription(), newAdminLevel.getDescription());
                }
                
                return result;
            }

            return true;
        } catch (Exception e) {
            log.error("❌ 重新计算用户管理级别异常: userId={}, error={}", userId, e.getMessage(), e);
            return false;
        }
    }

    @Override
    public List<Long> findInconsistentUsers() {
        log.info("🔍 开始检查用户类型数据一致性");
        
        // 这里可以实现具体的一致性检查逻辑
        // 例如：检查用户的角色与用户类型是否匹配
        List<Long> inconsistentUserIds = new ArrayList<>();
        
        // 查询所有用户，检查数据一致性
        List<SysUser> allUsers = sysUserService.list(new LambdaQueryWrapper<SysUser>()
                .eq(SysUser::getDeleted, false));
        
        for (SysUser user : allUsers) {
            try {
                // 基于角色重新计算用户类型
                List<Long> roleIds = sysUserRoleService.list(new LambdaQueryWrapper<SysUserRole>()
                        .eq(SysUserRole::getUserId, user.getId())
                        .eq(SysUserRole::getDeleted, false))
                        .stream()
                        .map(SysUserRole::getRoleId)
                        .collect(Collectors.toList());
                
                UserType expectedType = calculateUserTypeFromRoles(user.getId(), roleIds);
                AdminLevel expectedLevel = calculateAdminLevelFromRoles(user.getId(), roleIds);
                
                // 检查是否一致
                boolean typeInconsistent = user.getUserType() == null || 
                        !user.getUserType().equals(expectedType.getCode());
                boolean levelInconsistent = user.getAdminLevel() == null || 
                        !user.getAdminLevel().equals(expectedLevel.getCode());
                
                if (typeInconsistent || levelInconsistent) {
                    inconsistentUserIds.add(user.getId());
                    log.debug("⚠️ 发现数据不一致用户: userId={}, 期望类型={}, 实际类型={}, 期望级别={}, 实际级别={}", 
                            user.getId(), expectedType.getDescription(), 
                            UserType.fromCodeNullable(user.getUserType()) != null ? 
                                UserType.fromCode(user.getUserType()).getDescription() : "null",
                            expectedLevel.getDescription(),
                            AdminLevel.fromCodeNullable(user.getAdminLevel()) != null ? 
                                AdminLevel.fromCode(user.getAdminLevel()).getDescription() : "null");
                }
            } catch (Exception e) {
                log.error("❌ 检查用户{}一致性时发生异常: {}", user.getId(), e.getMessage(), e);
                inconsistentUserIds.add(user.getId());
            }
        }
        
        log.info("📊 用户类型一致性检查完成: 总用户数={}, 不一致用户数={}", allUsers.size(), inconsistentUserIds.size());
        return inconsistentUserIds;
    }

    @Override
    @Transactional
    public int fixInconsistentUsers(List<Long> userIds) {
        log.info("🔧 开始修复不一致用户数据: 用户数量={}", userIds != null ? userIds.size() : 0);
        
        if (userIds == null || userIds.isEmpty()) {
            return 0;
        }
        
        return batchSyncUserTypes(userIds);
    }

    @Override
    @Transactional
    public int syncAllUserTypes() {
        log.info("🔄 开始全量同步用户类型信息");
        
        List<SysUser> allUsers = sysUserService.list(new LambdaQueryWrapper<SysUser>()
                .eq(SysUser::getDeleted, false));
        
        List<Long> userIds = allUsers.stream()
                .map(SysUser::getId)
                .collect(Collectors.toList());
        
        int syncCount = batchSyncUserTypes(userIds);
        
        log.info("✅ 全量用户类型同步完成: 总用户数={}, 同步成功数={}", allUsers.size(), syncCount);
        return syncCount;
    }

    /**
     * 定时任务：每日凌晨检查并修复数据一致性
     */
    @Scheduled(cron = "0 0 2 * * ?") // 每日凌晨2点执行
    public void scheduledSyncTask() {
        try {
            log.info("🕐 开始执行定时用户类型同步任务");
            
            // 检查数据一致性
            List<Long> inconsistentUsers = findInconsistentUsers();
            
            // 修复不一致的数据
            if (!inconsistentUsers.isEmpty()) {
                int fixedCount = fixInconsistentUsers(inconsistentUsers);
                log.info("✅ 定时同步任务完成，修复{}个不一致记录", fixedCount);
            } else {
                log.info("✅ 定时同步任务完成，数据一致性良好");
            }
        } catch (Exception e) {
            log.error("❌ 定时用户类型同步任务执行异常", e);
        }
    }

    /**
     * 根据组织关系计算用户类型
     */
    private UserType calculateUserTypeFromOrg(Long userId) {
        // 获取用户所在的组织
        List<SysUserOrg> userOrgs = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
                .eq(SysUserOrg::getUserId, userId)
                .eq(SysUserOrg::getDeleted, false));

        if (userOrgs.isEmpty()) {
            return UserType.DEPT_ADMIN; // 默认为部门管理员
        }

        // 检查是否在顶级部门（租户级）
        boolean isInTopLevelOrg = userOrgs.stream().anyMatch(userOrg -> {
            SysOrgUnits org = sysOrgUnitsService.getById(userOrg.getOrgId());
            return org != null && isTopLevelOrg(org.getParentId());
        });

        return isInTopLevelOrg ? UserType.TENANT_ADMIN : UserType.DEPT_ADMIN;
    }

    /**
     * 判断是否是顶级组织
     */
    private boolean isTopLevelOrg(Long parentId) {
        return parentId == null || parentId == 0L || parentId == 1L;
    }
}