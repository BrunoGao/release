/*
 * All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
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

package com.ljwx.modules.system.facade.impl;

import cn.dev33.satoken.stp.StpUtil;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.domain.Options;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysPositionBO;
import com.ljwx.modules.system.domain.dto.position.SysPositionAddDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionDeleteDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionSearchDTO;
import com.ljwx.modules.system.domain.dto.position.SysPositionUpdateDTO;
import com.ljwx.modules.system.domain.entity.SysPosition;
import com.ljwx.modules.system.domain.vo.SysPositionVO;
import com.ljwx.modules.system.facade.ISysPositionFacade;
import com.ljwx.modules.system.service.ISysPositionService;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * 岗位管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysPositionFacadeImpl
 * @CreateTime 2024-06-27 - 22:03:29
 */

@Service
@RequiredArgsConstructor
public class SysPositionFacadeImpl implements ISysPositionFacade {

    @NonNull
    private ISysPositionService sysPositionService;
    
    @NonNull
    private ISysUserService sysUserService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public RPage<SysPositionVO> listSysPositionPage(PageQuery pageQuery, SysPositionSearchDTO sysPositionSearchDTO) {
        // 获取当前用户ID
        Long currentUserId = getCurrentUserId();
        
        SysPositionBO sysPositionBO = CglibUtil.convertObj(sysPositionSearchDTO, SysPositionBO::new);
        
        // 根据用户权限过滤数据（基于orgId）
        if (currentUserId != null) {
            if (sysUserService.isAdminUser(currentUserId)) {
                // 管理员：基于部门层级决定权限
                List<Long> userOrgIds = sysUserService.getUserOrgIds(currentUserId);
                
                // 检查是否是顶级部门管理员（用户部门的parent_id为0）
                boolean isTopLevelAdmin = userOrgIds.stream().anyMatch(orgId -> {
                    Long topLevelId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(orgId);
                    return topLevelId != null && topLevelId.equals(orgId);
                });
                
                if (isTopLevelAdmin) {
                    // 顶级部门管理员：可以使用前端传来的orgId参数
                    if (sysPositionSearchDTO.getOrgId() != null) {
                        sysPositionBO.setOrgIds(Arrays.asList(sysPositionSearchDTO.getOrgId()));
                        System.out.println("顶级管理员查询指定orgId: " + sysPositionSearchDTO.getOrgId());
                    } else {
                        // 不设置orgIds，查看所有岗位
                        System.out.println("顶级管理员查询所有岗位");
                    }
                } else {
                    // 下级部门管理员：忽略前端传来的orgId，基于权限过滤
                    Long topLevelDeptId = sysUserService.getUserTopLevelDeptId(currentUserId);
                    if (topLevelDeptId != null) {
                        List<Long> visibleOrgIds = Arrays.asList(0L, topLevelDeptId);
                        sysPositionBO.setOrgIds(visibleOrgIds);
                        System.out.println("下级部门管理员 " + currentUserId + " 可见岗位orgId: " + visibleOrgIds);
                    } else {
                        // 如果找不到顶级部门，只能查看全局岗位
                        sysPositionBO.setOrgIds(Arrays.asList(0L));
                        System.out.println("用户 " + currentUserId + " 只能查看全局岗位");
                    }
                }
            } else {
                // 非管理员用户：根据业务需求处理（暂时不允许查看）
                sysPositionBO.setOrgIds(Arrays.asList(-1L)); // 设置一个不存在的orgId
                System.out.println("非管理员用户 " + currentUserId + " 无权限查看岗位");
            }
        }
        
        IPage<SysPosition> sysPositionIPage = sysPositionService.listSysPositionPage(pageQuery, sysPositionBO);
        return RPage.build(sysPositionIPage, SysPositionVO::new);
    }

    @Override
    public SysPositionVO get(Long id) {
        SysPosition byId = sysPositionService.getById(id);
        return CglibUtil.convertObj(byId, SysPositionVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysPositionAddDTO sysPositionAddDTO) {
        SysPositionBO sysPositionBO = CglibUtil.convertObj(sysPositionAddDTO, SysPositionBO::new);
        System.out.println("sysPositionBO: " + sysPositionBO.getOrgId());
        
        // orgId 逻辑：
        // - admin 用户: orgId=0 创建全局岗位，其他值创建对应部门岗位
        // - 租户管理员: orgId=自己的部门ID，创建本部门岗位
        // 注意：前端传来的 orgId 就是正确的值，无需额外处理
        
        return sysPositionService.save(sysPositionBO);
    }

    @Override
    @Transactional
    public boolean update(SysPositionUpdateDTO sysPositionUpdateDTO) {
        SysPositionBO sysPositionBO = CglibUtil.convertObj(sysPositionUpdateDTO, SysPositionBO::new);
        System.out.println("sysPositionBO: " + sysPositionBO.getOrgId());
        return sysPositionService.updateById(sysPositionBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(SysPositionDeleteDTO sysPositionDeleteDTO) {
        SysPositionBO sysPositionBO = CglibUtil.convertObj(sysPositionDeleteDTO, SysPositionBO::new);
        return sysPositionService.removeBatchByIds(sysPositionBO.getIds(), true);
    }

    @Override
    public List<Options<Long>> queryAllPositionListConvertOptions(Long orgId) {
        System.out.println("queryAllPositionListConvertOptions.orgId: " + orgId);
        
        Long currentUserId = getCurrentUserId();
        List<SysPositionBO> allRole;
        
        if (currentUserId != null && sysUserService.isAdminUser(currentUserId)) {
            // 管理员：基于部门层级决定权限
            List<Long> userOrgIds = sysUserService.getUserOrgIds(currentUserId);
            
            // 检查是否是顶级部门管理员
            boolean isTopLevelAdmin = userOrgIds.stream().anyMatch(userOrgId -> {
                Long topLevelId = sysOrgUnitsService.getTopLevelDeptIdByOrgId(userOrgId);
                return topLevelId != null && topLevelId.equals(userOrgId);
            });
            
            if (isTopLevelAdmin) {
                // 顶级部门管理员：根据传入的orgId决定
                if (orgId != null) {
                    if (orgId == 0L) {
                        allRole = sysPositionService.queryAllPositionList(); // 查询所有岗位
                    } else {
                        allRole = sysPositionService.queryAllPositionList(orgId); // 按orgId过滤
                    }
                } else {
                    allRole = sysPositionService.queryAllPositionList(); // 查询所有岗位
                }
                System.out.println("顶级管理员查询岗位选项，orgId: " + orgId);
            } else {
                // 下级部门管理员：忽略传入的orgId，基于权限过滤
                Long topLevelDeptId = sysUserService.getUserTopLevelDeptId(currentUserId);
                if (topLevelDeptId != null) {
                    // 查询全局岗位 + 顶级部门岗位
                    List<SysPositionBO> globalPositions = sysPositionService.queryAllPositionList(0L);
                    List<SysPositionBO> deptPositions = sysPositionService.queryAllPositionList(topLevelDeptId);
                    allRole = new ArrayList<>(globalPositions);
                    allRole.addAll(deptPositions);
                    System.out.println("下级部门管理员 " + currentUserId + " 查询岗位选项，顶级部门ID: " + topLevelDeptId);
                } else {
                    allRole = sysPositionService.queryAllPositionList(0L); // 只能查看全局岗位
                    System.out.println("用户 " + currentUserId + " 只能查看全局岗位选项");
                }
            }
        } else {
            // 非管理员用户：无权限查看
            allRole = new ArrayList<>();
            System.out.println("非管理员用户 " + currentUserId + " 无权限查看岗位选项");
        }
            
        return allRole.stream()
                .map(item -> Options.<Long>builder()
                        .label(item.getName())
                        .value(item.getId())
                        .build())
                .toList();
    }

    /**
     * 获取当前登录用户ID
     */
    private Long getCurrentUserId() {
        try {
            return Long.parseLong(StpUtil.getLoginIdAsString());
        } catch (Exception e) {
            return null;
        }
    }

}