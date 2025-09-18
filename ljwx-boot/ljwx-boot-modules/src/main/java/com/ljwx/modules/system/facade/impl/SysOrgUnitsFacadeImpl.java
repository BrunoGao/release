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

package com.ljwx.modules.system.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.pool.StringPools;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.system.domain.bo.SysOrgUnitsBO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsAddDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsDeleteDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsSearchDTO;
import com.ljwx.modules.system.domain.dto.org.units.SysOrgUnitsUpdateDTO;
import com.ljwx.modules.system.domain.dto.org.units.DepartmentDeletePreCheckDTO;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.vo.SysOrgUnitsTreeVO;
import com.ljwx.modules.system.domain.vo.SysOrgUnitsVO;
import com.ljwx.modules.system.facade.ISysOrgUnitsFacade;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.stream.Collectors;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.extern.slf4j.Slf4j;

/**
 * 组织/部门/子部门管理 门面接口实现层
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.system.facade.impl.SysOrgUnitsFacadeImpl
 * @CreateTime 2024-07-16 - 16:35:30
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class SysOrgUnitsFacadeImpl implements ISysOrgUnitsFacade {

    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @NonNull
    private ISysUserService sysUserService;
    
    @NonNull
    private ITDeviceInfoService deviceInfoService;

    /**
     * 初始化组织单位子单位
     *
     * @param parentId    父id
     * @param orgUnitsMap 所有单位数据 Map 结构
     * @return {@link List }<{@link SysOrgUnitsTreeVO }> 子组织集合
     * @author payne.zhuang
     * @CreateTime 2024-07-16 - 22:03:21
     */
    private static List<SysOrgUnitsTreeVO> initOrgUnitsChild(Long parentId, Map<Long, List<SysOrgUnits>> orgUnitsMap) {
        // 获取子单位
        List<SysOrgUnits> childOrgUnits = orgUnitsMap.get(parentId);
        if (CollectionUtils.isEmpty(childOrgUnits)) {
            return Collections.emptyList();
        }
        // 递归初始化子单位
        return childOrgUnits.stream()
                .map(unit -> {
                    SysOrgUnitsTreeVO orgUnitsTreeVO = CglibUtil.convertObj(unit, SysOrgUnitsTreeVO::new);
                    orgUnitsTreeVO.setChildren(initOrgUnitsChild(unit.getId(), orgUnitsMap));
                    return orgUnitsTreeVO;
                })
                .sorted(Comparator.comparing(SysOrgUnitsTreeVO::getSort))
                .toList();
    }


    @Override
    public RPage<SysOrgUnitsTreeVO> listSysOrgUnitsPage(PageQuery pageQuery, SysOrgUnitsSearchDTO sysOrgUnitsSearchDTO) {
        SysOrgUnitsBO sysOrgUnitsBO = CglibUtil.convertObj(sysOrgUnitsSearchDTO, SysOrgUnitsBO::new);
        
        // 如果传入了customerId，说明要按租户过滤，返回租户下属的部门（不包含租户本身）
        if (sysOrgUnitsSearchDTO.getCustomerId() != null) {
            System.out.println("🔍 SysOrgUnitsFacadeImpl - 根据customerId过滤: " + sysOrgUnitsSearchDTO.getCustomerId());
            
            // 查询租户下的所有部门
            List<SysOrgUnits> allOrgUnits = sysOrgUnitsService.querySysOrgUnitsListWithStatus(StringPools.ONE, sysOrgUnitsSearchDTO.getCustomerId());
            
            // 过滤掉租户节点本身，只保留下属部门
            List<SysOrgUnits> departmentsOnly = allOrgUnits.stream()
                    .filter(unit -> !unit.getId().equals(sysOrgUnitsSearchDTO.getCustomerId()))
                    .collect(Collectors.toList());
            
            // 如果没有下属部门，返回空结果
            if (departmentsOnly.isEmpty()) {
                return new RPage<>(pageQuery.getPage(), pageQuery.getPageSize(), List.of(), 0, 0);
            }
            
            // 找出顶级部门（parentId 等于 customerId 的部门）
            List<SysOrgUnits> topDepartments = departmentsOnly.stream()
                    .filter(unit -> unit.getParentId().equals(sysOrgUnitsSearchDTO.getCustomerId()))
                    .sorted(Comparator.comparing(SysOrgUnits::getSort))
                    .collect(Collectors.toList());
            
            // 按 parentId 分组，用于构建子部门
            Map<Long, List<SysOrgUnits>> orgUnitsMap = departmentsOnly.stream()
                    .collect(Collectors.groupingBy(SysOrgUnits::getParentId));
            
            // 构建树形结构
            List<SysOrgUnitsTreeVO> topDepartmentTreeVOList = topDepartments.stream()
                    .map(unit -> {
                        SysOrgUnitsTreeVO orgUnitsTreeVO = CglibUtil.convertObj(unit, SysOrgUnitsTreeVO::new);
                        orgUnitsTreeVO.setChildren(initOrgUnitsChild(unit.getId(), orgUnitsMap));
                        return orgUnitsTreeVO;
                    }).collect(Collectors.toList());
            
            // 构建分页结果
            RPage<SysOrgUnitsTreeVO> result = new RPage<>(
                pageQuery.getPage(), 
                pageQuery.getPageSize(), 
                topDepartmentTreeVOList,
                topDepartmentTreeVOList.isEmpty() ? 0 : 1,
                topDepartmentTreeVOList.size()
            );
            
            System.out.println("🏢 返回部门管理页面结果，不包含租户节点，部门数量: " + topDepartmentTreeVOList.size());
            return result;
        }
        
        // 原有逻辑：查询租户或全部组织
        IPage<SysOrgUnits> sysOrgUnitsIPage = sysOrgUnitsService.listSysOrgUnitsPage(pageQuery, sysOrgUnitsBO);
        List<SysOrgUnits> topOrgUnits = sysOrgUnitsIPage.getRecords();
        if (topOrgUnits.isEmpty()) {
            return RPage.build(sysOrgUnitsIPage, SysOrgUnitsTreeVO::new);
        }
        // 查询所有数据
        List<Long> topLevelIds = topOrgUnits.stream().map(SysOrgUnits::getId).toList();
        List<SysOrgUnits> allOrgUnits = sysOrgUnitsService.listAllDescendants(topLevelIds);
        // 按 parentId 分组
        Map<Long, List<SysOrgUnits>> orgUnitsMap = allOrgUnits.stream()
                .collect(Collectors.groupingBy(SysOrgUnits::getParentId));
        // 初始化顶级单位的子单位
        List<SysOrgUnitsTreeVO> topOrgUnitsTreeVOList = topOrgUnits.stream()
                .map(unit -> {
                    SysOrgUnitsTreeVO orgUnitsTreeVO = CglibUtil.convertObj(unit, SysOrgUnitsTreeVO::new);
                    orgUnitsTreeVO.setChildren(initOrgUnitsChild(unit.getId(), orgUnitsMap));
                    return orgUnitsTreeVO;
                }).toList();

        RPage<SysOrgUnitsTreeVO> build = RPage.build(sysOrgUnitsIPage, SysOrgUnitsTreeVO::new);
        build.setRecords(topOrgUnitsTreeVOList);
        return build;
    }

    @Override
    public SysOrgUnitsVO get(Long id) {
        SysOrgUnits byId = sysOrgUnitsService.getById(id);
        return CglibUtil.convertObj(byId, SysOrgUnitsVO::new);
    }

    @Override
    @Transactional
    public boolean add(SysOrgUnitsAddDTO sysOrgUnitsAddDTO) {
        SysOrgUnitsBO sysOrgUnitsBO = CglibUtil.convertObj(sysOrgUnitsAddDTO, SysOrgUnitsBO::new);
        return sysOrgUnitsService.save(sysOrgUnitsBO);
    }

    @Override
    @Transactional
    public boolean update(SysOrgUnitsUpdateDTO sysOrgUnitsUpdateDTO) {
        SysOrgUnitsBO sysOrgUnitsBO = CglibUtil.convertObj(sysOrgUnitsUpdateDTO, SysOrgUnitsBO::new);
        return sysOrgUnitsService.updateById(sysOrgUnitsBO);
    }

    @Override
    @Transactional
    public boolean batchDelete(SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        SysOrgUnitsBO sysOrgUnitsBO = CglibUtil.convertObj(sysOrgUnitsDeleteDTO, SysOrgUnitsBO::new);
        return sysOrgUnitsService.removeBatchByIds(sysOrgUnitsBO.getIds(), true);
    }

    

    @Override
    public List<SysOrgUnitsTreeVO> queryAllOrgUnitsListConvertToTree(Long id) {
        // 查询所有数据
        List<SysOrgUnits> allOrgUnits = sysOrgUnitsService.querySysOrgUnitsListWithStatus(StringPools.ONE, id);
        System.out.println("allOrgUnits: " + allOrgUnits);
        // 按 parentId 分组
        Map<Long, List<SysOrgUnits>> orgUnitsMap = allOrgUnits.stream()
                .collect(Collectors.groupingBy(SysOrgUnits::getParentId));
        System.out.println("orgUnitsMap: " + orgUnitsMap);
        Long directParent = sysOrgUnitsService.getDirectParent(id);
        // 组装对应结构
        List<SysOrgUnitsTreeVO> result = initOrgUnitsChild(directParent, orgUnitsMap);  
        System.out.println("queryAllOrgUnitsListConvertToTree:result: " + result);
        return result;
    }
    
    @Override
    public List<SysOrgUnitsTreeVO> queryTenantDepartmentsTree(Long tenantId) {
        // 查询租户下的所有数据
        List<SysOrgUnits> allOrgUnits = sysOrgUnitsService.querySysOrgUnitsListWithStatus(StringPools.ONE, tenantId);
        System.out.println("🏢 queryTenantDepartmentsTree - tenantId: " + tenantId);
        System.out.println("🏢 查询到的所有组织单位: " + allOrgUnits);
        
        // 按 parentId 分组
        Map<Long, List<SysOrgUnits>> orgUnitsMap = allOrgUnits.stream()
                .collect(Collectors.groupingBy(SysOrgUnits::getParentId));
        
        // 直接返回租户下属的部门，不包含租户节点本身
        List<SysOrgUnitsTreeVO> result = initOrgUnitsChild(tenantId, orgUnitsMap);
        System.out.println("🏢 返回的部门树结构: " + result);
        return result;
    }

    @Override
    public DepartmentDeletePreCheckDTO deletePreCheck(SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        log.info("🔍 开始检查部门删除影响，部门IDs: {}", sysOrgUnitsDeleteDTO.getIds());
        
        // 获取所有要删除的部门（包括子部门）
        List<SysOrgUnits> allDepartmentsToDelete = getAllDepartmentsToDelete(sysOrgUnitsDeleteDTO.getIds());
        List<Long> allOrgIds = allDepartmentsToDelete.stream().map(SysOrgUnits::getId).collect(Collectors.toList());
        
        // 获取受影响的用户
        List<SysUser> affectedUsers = getUsersInDepartments(allOrgIds);
        
        // 获取需要释放的设备
        List<TDeviceInfo> devicesToRelease = getDevicesInDepartments(affectedUsers);
        
        // 构建检查结果
        return buildPreCheckResult(allDepartmentsToDelete, affectedUsers, devicesToRelease);
    }

    @Override
    @Transactional
    public boolean cascadeDelete(SysOrgUnitsDeleteDTO sysOrgUnitsDeleteDTO) {
        log.info("🗑️ 开始级联删除部门，部门IDs: {}", sysOrgUnitsDeleteDTO.getIds());
        
        try {
            // 获取所有要删除的部门（包括子部门）
            List<SysOrgUnits> allDepartmentsToDelete = getAllDepartmentsToDelete(sysOrgUnitsDeleteDTO.getIds());
            List<Long> allOrgIds = allDepartmentsToDelete.stream().map(SysOrgUnits::getId).collect(Collectors.toList());
            
            // 获取受影响的用户
            List<SysUser> affectedUsers = getUsersInDepartments(allOrgIds);
            List<Long> userIds = affectedUsers.stream().map(SysUser::getId).collect(Collectors.toList());
            
            log.info("📊 级联删除统计: 部门{}个, 用户{}个", allOrgIds.size(), userIds.size());
            
            // 1. 删除用户（会自动释放设备）
            if (!userIds.isEmpty()) {
                boolean userDeleted = sysUserService.forceRemoveBatchByIds(userIds, true);
                if (!userDeleted) {
                    throw new RuntimeException("删除用户失败");
                }
                log.info("✅ 已删除{}个用户并自动释放绑定设备", userIds.size());
            }
            
            // 2. 删除部门
            boolean departmentDeleted = sysOrgUnitsService.removeBatchByIds(allOrgIds, true);
            if (!departmentDeleted) {
                throw new RuntimeException("删除部门失败");
            }
            log.info("✅ 已删除{}个部门", allOrgIds.size());
            
            return true;
            
        } catch (Exception e) {
            log.error("❌ 级联删除失败: {}", e.getMessage(), e);
            throw new RuntimeException("级联删除失败: " + e.getMessage());
        }
    }

    /**
     * 获取所有需要删除的部门（包括子部门）
     */
    private List<SysOrgUnits> getAllDepartmentsToDelete(List<Long> orgIds) {
        List<SysOrgUnits> result = new ArrayList<>();
        
        for (Long orgId : orgIds) {
            // 获取当前部门
            SysOrgUnits org = sysOrgUnitsService.getById(orgId);
            if (org != null) {
                result.add(org);
            }
            
            // 获取所有子部门
            List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(List.of(orgId));
            result.addAll(descendants);
        }
        
        return result;
    }

    /**
     * 获取部门下的所有用户（直接利用sys_user.org_id字段）
     */
    private List<SysUser> getUsersInDepartments(List<Long> orgIds) {
        if (orgIds.isEmpty()) {
            return new ArrayList<>();
        }
        
        // 直接使用sys_user.org_id IN查询，高效且简单
        LambdaQueryWrapper<SysUser> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.in(SysUser::getOrgId, orgIds)
                   .eq(SysUser::getStatus, "1"); // 只查询启用用户
        
        return sysUserService.list(queryWrapper);
    }

    /**
     * 获取用户绑定的设备
     */
    private List<TDeviceInfo> getDevicesInDepartments(List<SysUser> users) {
        List<TDeviceInfo> devices = new ArrayList<>();
        
        for (SysUser user : users) {
            if (user.getDeviceSn() != null && !user.getDeviceSn().trim().isEmpty() 
                && !"-".equals(user.getDeviceSn().trim())) {
                TDeviceInfo device = deviceInfoService.getOne(new LambdaQueryWrapper<TDeviceInfo>()
                    .eq(TDeviceInfo::getSerialNumber, user.getDeviceSn()));
                if (device != null) {
                    devices.add(device);
                }
            }
        }
        
        return devices;
    }

    /**
     * 构建预检查结果
     */
    private DepartmentDeletePreCheckDTO buildPreCheckResult(
            List<SysOrgUnits> departments, 
            List<SysUser> users, 
            List<TDeviceInfo> devices) {
        
        // 构建部门信息
        List<DepartmentDeletePreCheckDTO.DepartmentInfo> departmentInfos = departments.stream()
            .map(dept -> DepartmentDeletePreCheckDTO.DepartmentInfo.builder()
                .orgId(dept.getId())
                .orgName(dept.getName())
                .level(dept.getLevel())
                .userCount(Math.toIntExact(users.stream()
                    .filter(user -> dept.getId().equals(user.getOrgId()))
                    .count()))
                .deviceCount(Math.toIntExact(devices.stream()
                    .filter(device -> users.stream()
                        .anyMatch(user -> dept.getId().equals(user.getOrgId()) 
                            && device.getSerialNumber().equals(user.getDeviceSn())))
                    .count()))
                .build())
            .collect(Collectors.toList());
        
        // 构建用户信息
        List<DepartmentDeletePreCheckDTO.UserInfo> userInfos = users.stream()
            .map(user -> DepartmentDeletePreCheckDTO.UserInfo.builder()
                .userId(user.getId())
                .userName(user.getUserName())
                .realName(user.getRealName())
                .orgName(user.getOrgName())
                .deviceSn(user.getDeviceSn())
                .hasDevice(user.getDeviceSn() != null && !user.getDeviceSn().trim().isEmpty() 
                    && !"-".equals(user.getDeviceSn().trim()))
                .build())
            .collect(Collectors.toList());
        
        // 构建设备信息
        List<DepartmentDeletePreCheckDTO.DeviceInfo> deviceInfos = devices.stream()
            .map(device -> {
                SysUser boundUser = users.stream()
                    .filter(user -> device.getSerialNumber().equals(user.getDeviceSn()))
                    .findFirst()
                    .orElse(null);
                return DepartmentDeletePreCheckDTO.DeviceInfo.builder()
                    .deviceSn(device.getSerialNumber())
                    .deviceType(device.getModel()) // 使用model字段作为设备类型
                    .boundUserId(boundUser != null ? boundUser.getId() : null)
                    .boundUserName(boundUser != null ? boundUser.getRealName() : null)
                    .orgName(boundUser != null ? boundUser.getOrgName() : null)
                    .build();
            })
            .collect(Collectors.toList());
        
        // 构建汇总信息
        int usersWithDevices = Math.toIntExact(userInfos.stream()
            .filter(DepartmentDeletePreCheckDTO.UserInfo::getHasDevice)
            .count());
        
        String warningMessage = String.format(
            "此操作将删除 %d 个部门、%d 个用户，并释放 %d 个设备。其中 %d 个用户绑定了设备。",
            departments.size(), users.size(), devices.size(), usersWithDevices
        );
        
        DepartmentDeletePreCheckDTO.SummaryInfo summary = DepartmentDeletePreCheckDTO.SummaryInfo.builder()
            .totalDepartments(departments.size())
            .totalUsers(users.size())
            .totalDevices(devices.size())
            .usersWithDevices(usersWithDevices)
            .warningMessage(warningMessage)
            .build();
        
        return DepartmentDeletePreCheckDTO.builder()
            .canSafeDelete(users.isEmpty() && devices.isEmpty())
            .departmentsToDelete(departmentInfos)
            .usersToDelete(userInfos)
            .devicesToRelease(deviceInfos)
            .summary(summary)
            .build();
    }

}