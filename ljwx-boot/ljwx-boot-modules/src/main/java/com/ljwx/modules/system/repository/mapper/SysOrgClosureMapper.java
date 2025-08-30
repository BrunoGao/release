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
import com.ljwx.modules.system.domain.entity.SysOrgClosure;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 组织架构闭包关系表 Mapper 接口
 * 提供高效的组织层级查询方法
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.repository.mapper.SysOrgClosureMapper
 * @CreateTime 2025-08-30 - 16:00:00
 */

@Mapper
public interface SysOrgClosureMapper extends BaseMapper<SysOrgClosure> {

    /**
     * 查询指定组织的所有子组织(包含子孙组织)
     *
     * @param ancestorId 祖先组织ID
     * @param customerId 租户ID
     * @return 子组织列表
     */
    List<SysOrgUnits> findAllDescendants(@Param("ancestorId") Long ancestorId, 
                                        @Param("customerId") Long customerId);

    /**
     * 查询指定组织的直接子组织
     *
     * @param ancestorId 父组织ID
     * @param customerId 租户ID
     * @return 直接子组织列表
     */
    List<SysOrgUnits> findDirectChildren(@Param("ancestorId") Long ancestorId, 
                                        @Param("customerId") Long customerId);

    /**
     * 查询指定组织的祖先路径
     *
     * @param descendantId 子组织ID
     * @param customerId 租户ID
     * @return 祖先路径列表(从根节点到父节点)
     */
    List<SysOrgUnits> findAncestorPath(@Param("descendantId") Long descendantId, 
                                      @Param("customerId") Long customerId);

    /**
     * 查询指定组织的直接父组织
     *
     * @param descendantId 子组织ID
     * @param customerId 租户ID
     * @return 父组织信息
     */
    SysOrgUnits findDirectParent(@Param("descendantId") Long descendantId, 
                                @Param("customerId") Long customerId);

    /**
     * 批量查询多个组织的所有子组织
     *
     * @param ancestorIds 祖先组织ID列表
     * @param customerId 租户ID
     * @return 所有子组织列表
     */
    List<SysOrgUnits> findBatchDescendants(@Param("ancestorIds") List<Long> ancestorIds, 
                                          @Param("customerId") Long customerId);

    /**
     * 查询租户下的所有顶级组织
     *
     * @param customerId 租户ID
     * @return 顶级组织列表
     */
    List<SysOrgUnits> findTopLevelOrganizations(@Param("customerId") Long customerId);

    /**
     * 检查组织A是否为组织B的祖先
     *
     * @param ancestorId 祖先组织ID
     * @param descendantId 后代组织ID
     * @param customerId 租户ID
     * @return true表示是祖先关系
     */
    Boolean isAncestor(@Param("ancestorId") Long ancestorId, 
                      @Param("descendantId") Long descendantId, 
                      @Param("customerId") Long customerId);

    /**
     * 获取组织的层级深度
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     * @return 层级深度
     */
    Integer getOrgDepth(@Param("orgId") Long orgId, 
                       @Param("customerId") Long customerId);

    /**
     * 删除指定组织的所有闭包关系
     *
     * @param orgId 组织ID
     * @param customerId 租户ID
     */
    void deleteOrgClosure(@Param("orgId") Long orgId, 
                         @Param("customerId") Long customerId);

    /**
     * 为新组织创建闭包关系
     *
     * @param orgId 新组织ID
     * @param parentId 父组织ID
     * @param customerId 租户ID
     */
    void insertOrgClosure(@Param("orgId") Long orgId, 
                         @Param("parentId") Long parentId, 
                         @Param("customerId") Long customerId);
}