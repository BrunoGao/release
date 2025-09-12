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

package com.ljwx.modules.system.service;

import com.ljwx.modules.system.domain.enums.AdminLevel;
import com.ljwx.modules.system.domain.enums.UserType;

import java.util.List;

/**
 * 用户类型同步服务接口
 * 
 * <p>负责维护 user_type 和 admin_level 冗余字段的数据一致性</p>
 * <p>在角色、组织关系变更时自动同步更新用户类型信息</p>
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.IUserTypeSyncService
 * @CreateTime 2025-09-12 - 16:35:30
 */
public interface IUserTypeSyncService {

    /**
     * 根据用户角色计算用户类型
     *
     * @param userId 用户ID
     * @param roleIds 角色ID列表
     * @return 用户类型
     */
    UserType calculateUserTypeFromRoles(Long userId, List<Long> roleIds);

    /**
     * 根据用户角色计算管理级别
     *
     * @param userId 用户ID
     * @param roleIds 角色ID列表
     * @return 管理级别
     */
    AdminLevel calculateAdminLevelFromRoles(Long userId, List<Long> roleIds);

    /**
     * 同步更新单个用户的类型信息（基于角色）
     *
     * @param userId 用户ID
     * @return 是否更新成功
     */
    boolean syncUserTypeFromRoles(Long userId);

    /**
     * 同步更新单个用户的类型信息（基于角色和组织）
     *
     * @param userId 用户ID
     * @param roleIds 角色ID列表
     * @return 是否更新成功
     */
    boolean syncUserTypeFromRoles(Long userId, List<Long> roleIds);

    /**
     * 批量同步用户类型信息
     *
     * @param userIds 用户ID列表
     * @return 成功同步的用户数量
     */
    int batchSyncUserTypes(List<Long> userIds);

    /**
     * 重新计算用户的管理级别（基于组织关系变更）
     *
     * @param userId 用户ID
     * @return 是否更新成功
     */
    boolean recalculateUserAdminLevel(Long userId);

    /**
     * 检查数据一致性
     * 
     * @return 不一致的用户ID列表
     */
    List<Long> findInconsistentUsers();

    /**
     * 修复数据不一致的用户
     *
     * @param userIds 需要修复的用户ID列表
     * @return 成功修复的用户数量
     */
    int fixInconsistentUsers(List<Long> userIds);

    /**
     * 全量同步所有用户的类型信息（维护任务）
     *
     * @return 同步的用户数量
     */
    int syncAllUserTypes();
}