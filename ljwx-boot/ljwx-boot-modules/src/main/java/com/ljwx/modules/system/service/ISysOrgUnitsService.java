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

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.system.domain.bo.SysOrgUnitsBO;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;

import java.util.List;

/**
 * 组织/部门/子部门管理 Service 服务接口层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.service.ISysOrgUnitsService
 * @CreateTime 2024-07-16 - 16:35:30
 */

public interface ISysOrgUnitsService extends IService<SysOrgUnits> {

    /**
     * 组织/部门/子部门管理 - 分页查询
     *
     * @param pageQuery     分页对象
     * @param sysOrgUnitsBO BO 查询对象
     * @return {@link IPage} 分页结果
     * @author payne.zhuang
     * @CreateTime 2024-07-16 - 16:35:30
     */
    IPage<SysOrgUnits> listSysOrgUnitsPage(PageQuery pageQuery, SysOrgUnitsBO sysOrgUnitsBO);

    /**
     * 查询所有子组织
     *
     * @param parentIds 父id
     * @return {@link List }<{@link SysOrgUnits }> 子组织列表
     * @author payne.zhuang
     * @CreateTime 2024-07-16 - 09:21:02
     */
    List<SysOrgUnits> listAllDescendants(List<Long> parentIds);

    /**
     * 查询组织/部门/子部门列表
     *
     * @param status 状态
     * @return {@link IPage }<{@link SysOrgUnits }> 查询结果
     * @author payne.zhuang
     * @CreateTime 2024-07-11 - 10:39:02
     */
    List<SysOrgUnits> querySysOrgUnitsListWithStatus(String status, Long id);

    /**
     * 查询直接父组织
     *
     * @param id 组织ID
     * @return {@link Long } 直接父组织ID
     * @author bruno.gao
     * @CreateTime 2025-05-10 - 10:39:02
     */
    Long getDirectParent(Long id);

    /**
     * 查询第一个父组织
     *
     * @param id 组织ID 
     * @return {@link Long } 第一个父组织ID
     * @author bruno.gao
     * @CreateTime 2025-05-10 - 10:39:02
     */
    Long getFirstParent(Long id);

    /**
     * 根据部门ID获取顶级部门ID（通用方法）
     * 通过解析 sys_org_units.ancestors 字段，获取最左边第一个非0数字
     * 例如: "0,1955920989166800898,1955921028870082561" -> 1955920989166800898
     * @param orgId 部门ID
     * @return 顶级部门ID，如果已经是顶级部门则返回自身
     * @author bruno.gao
     * @CreateTime 2025-08-18
     */
    Long getTopLevelDeptIdByOrgId(Long orgId);

    /**
     * 根据租户ID查询组织列表
     *
     * @param customerId 租户ID (0表示查询全局组织)
     * @param status 状态
     * @return {@link List }<{@link SysOrgUnits }> 组织列表
     * @author bruno.gao
     * @CreateTime 2025-08-28
     */
    List<SysOrgUnits> listOrgUnitsByCustomerId(Long customerId, String status);

    /**
     * 根据租户ID分页查询组织
     *
     * @param pageQuery 分页对象
     * @param customerId 租户ID
     * @param sysOrgUnitsBO BO 查询对象
     * @return {@link IPage }<{@link SysOrgUnits }> 分页结果
     * @author bruno.gao
     * @CreateTime 2025-08-28
     */
    IPage<SysOrgUnits> listSysOrgUnitsPageByCustomerId(PageQuery pageQuery, Long customerId, SysOrgUnitsBO sysOrgUnitsBO);

    /**
     * 获取组织的租户ID
     *
     * @param orgId 组织ID
     * @return 租户ID
     * @author bruno.gao
     * @CreateTime 2025-08-28
     */
    Long getCustomerIdByOrgId(Long orgId);

}
