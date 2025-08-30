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

import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.modules.system.domain.entity.SysOrgClosure;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysOrgManagerCache;
import com.ljwx.modules.system.domain.dto.OrgHierarchyInfo;

import java.util.List;

/**
 * 组织架构闭包表服务接口
 * 提供高效的组织层级查询服务，解决传统ancestor字段性能问题
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.ISysOrgClosureService
 * @CreateTime 2025-08-30 - 16:00:00
 */
public interface ISysOrgClosureService extends IService<SysOrgClosure> {

    /**
     * 查询指定租户的所有顶级组织
     *
     * @param customerId 租户ID
     * @return 顶级组织列表
     */
    List<SysOrgUnits> findTopLevelOrganizations(Long customerId);

    /**
     * 查询指定组织的所有子组织(包含子孙组织)
     *
     * @param ancestorId 祖先组织ID
     * @param customerId 租户ID
     * @return 子组织列表
     */
    List<SysOrgUnits> findAllDescendants(Long ancestorId, Long customerId);

    /**
     * 查询指定组织的直接子组织
     *
     * @param ancestorId 父组织ID
     * @param customerId 租户ID
     * @return 直接子组织列表
     */
    List<SysOrgUnits> findDirectChildren(Long ancestorId, Long customerId);

    /**
     * 查询指定组织的祖先路径
     *
     * @param descendantId 子组织ID
     * @param customerId 租户ID
     * @return 祖先路径列表(从根节点到父节点)
     */
    List<SysOrgUnits> findAncestorPath(Long descendantId, Long customerId);

    /**
     * 查询指定组织的直接父组织
     *
     * @param descendantId 子组织ID
     * @param customerId 租户ID
     * @return 父组织信息
     */
    SysOrgUnits findDirectParent(Long descendantId, Long customerId);

    /**
     * 批量查询多个组织的所有子组织
     *
     * @param ancestorIds 祖先组织ID列表
     * @param customerId 租户ID
     * @return 所有子组织列表
     */
    List<SysOrgUnits> findBatchDescendants(List<Long> ancestorIds, Long customerId);

    /**
     * 查询指定组织的管理员列表
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param roleType 角色类型(manager/supervisor)
     * @return 管理员列表
     */
    List<SysOrgManagerCache> findOrgManagers(Long orgId, Long customerId, String roleType);

    /**
     * 查询指定组织及其所有上级组织的管理员(用于告警升级链)
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @param roleType 角色类型
     * @return 管理员列表(按层级从低到高排序)
     */
    List<SysOrgManagerCache> findEscalationManagers(Long orgId, Long customerId, String roleType);

    /**
     * 查询用户管理的所有组织
     *
     * @param userId 用户ID
     * @param customerId 租户ID
     * @return 管理的组织列表
     */
    List<SysOrgManagerCache> findUserManagedOrgs(Long userId, Long customerId);

    /**
     * 检查组织A是否为组织B的祖先
     *
     * @param ancestorId 祖先组织ID
     * @param descendantId 后代组织ID
     * @param customerId 租户ID
     * @return true表示是祖先关系
     */
    Boolean isAncestor(Long ancestorId, Long descendantId, Long customerId);

    /**
     * 获取组织的层级深度
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return 层级深度
     */
    Integer getOrgDepth(Long orgId, Long customerId);

    /**
     * 添加新组织到闭包表
     *
     * @param orgId 新组织ID
     * @param parentId 父组织ID
     * @param customerId 租户ID
     */
    void addOrgToClosure(Long orgId, Long parentId, Long customerId);

    /**
     * 从闭包表中删除组织
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     */
    void removeOrgFromClosure(Long orgId, Long customerId);

    /**
     * 移动组织到新的父组织下
     *
     * @param orgId 要移动的组织ID
     * @param newParentId 新父组织ID
     * @param customerId 租户ID
     */
    void moveOrgToNewParent(Long orgId, Long newParentId, Long customerId);

    /**
     * 刷新管理员缓存
     *
     * @param orgId 组织ID(null表示刷新所有)
     * @param customerId 租户ID
     */
    void refreshManagerCache(Long orgId, Long customerId);

    /**
     * 验证闭包表数据一致性
     *
     * @param customerId 租户ID
     * @return 不一致的记录列表
     */
    List<String> validateConsistency(Long customerId);

    /**
     * 从现有sys_org_units表重建闭包表
     *
     * @param customerId 租户ID(null表示重建所有租户)
     */
    void rebuildClosureTable(Long customerId);

    // ===================== 告警分发优化相关方法 =====================

    /**
     * 获取告警通知层级信息 - 基于闭包表的高效查询
     * 一次查询获取所有需要通知的人员和组织信息
     *
     * @param orgId 告警发生的组织ID
     * @param customerId 租户ID
     * @return 按层级排序的通知信息列表
     */
    List<OrgHierarchyInfo> getNotificationHierarchy(Long orgId, Long customerId);

    /**
     * 获取批量组织的通知层级信息
     *
     * @param orgIds 组织ID列表
     * @param customerId 租户ID
     * @return 通知信息列表
     */
    List<OrgHierarchyInfo> getBatchNotificationHierarchy(List<Long> orgIds, Long customerId);

    /**
     * 获取用户可接收的告警组织范围
     * 用于告警权限过滤
     *
     * @param userId 用户ID
     * @param customerId 租户ID
     * @return 可接收告警的组织ID列表
     */
    List<Long> getUserAlertScope(Long userId, Long customerId);
}