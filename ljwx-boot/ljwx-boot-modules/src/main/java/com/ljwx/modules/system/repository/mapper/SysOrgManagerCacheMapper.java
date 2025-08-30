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

package com.ljwx.modules.system.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.system.domain.entity.SysOrgManagerCache;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 组织管理员关系缓存表 Mapper 接口
 * 提供高效的组织管理员查询方法
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.repository.mapper.SysOrgManagerCacheMapper
 * @CreateTime 2025-08-30 - 16:00:00
 */

@Mapper
public interface SysOrgManagerCacheMapper extends BaseMapper<SysOrgManagerCache> {

    /**
     * 查询指定组织的管理员列表
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param roleType 角色类型(manager/supervisor)
     * @return 管理员列表
     */
    List<SysOrgManagerCache> findOrgManagers(@Param("orgId") Long orgId, 
                                            @Param("customerId") Long customerId, 
                                            @Param("roleType") String roleType);

    /**
     * 批量查询多个组织的管理员列表
     *
     * @param orgIds 组织ID列表
     * @param customerId 租户ID
     * @param roleType 角色类型
     * @return 管理员列表
     */
    List<SysOrgManagerCache> findBatchOrgManagers(@Param("orgIds") List<Long> orgIds, 
                                                  @Param("customerId") Long customerId, 
                                                  @Param("roleType") String roleType);

    /**
     * 查询指定组织及其所有上级组织的管理员
     * 用于告警升级链查找
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param roleType 角色类型
     * @return 管理员列表(按层级从低到高排序)
     */
    List<SysOrgManagerCache> findEscalationManagers(@Param("orgId") Long orgId, 
                                                    @Param("customerId") Long customerId, 
                                                    @Param("roleType") String roleType);

    /**
     * 查询用户管理的所有组织
     *
     * @param userId 用户ID
     * @param customerId 租户ID
     * @return 管理的组织列表
     */
    List<SysOrgManagerCache> findUserManagedOrgs(@Param("userId") Long userId, 
                                                 @Param("customerId") Long customerId);

    /**
     * 刷新指定组织的管理员缓存
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     */
    void refreshOrgManagerCache(@Param("orgId") Long orgId, 
                               @Param("customerId") Long customerId);

    /**
     * 删除指定组织的管理员缓存
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     */
    void deleteOrgManagerCache(@Param("orgId") Long orgId, 
                              @Param("customerId") Long customerId);
}