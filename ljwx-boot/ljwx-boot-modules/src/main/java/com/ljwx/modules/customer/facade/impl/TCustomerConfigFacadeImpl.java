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

package com.ljwx.modules.customer.facade.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.util.CglibUtil;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.customer.domain.bo.TCustomerConfigBO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigAddDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigDeleteDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigSearchDTO;
import com.ljwx.modules.customer.domain.dto.config.TCustomerConfigUpdateDTO;
import com.ljwx.modules.customer.domain.entity.TCustomerConfig;
import com.ljwx.modules.customer.domain.vo.TCustomerConfigVO;
import com.ljwx.modules.customer.facade.ITCustomerConfigFacade;
import com.ljwx.modules.customer.service.ITCustomerConfigService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.event.SysOrgUnitsChangeEvent;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.domain.dto.org.units.DepartmentDeletePreCheckDTO;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import java.util.*;
import java.util.stream.Collectors;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 *  门面接口实现层
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName  com.ljwx.modules.customer.facade.impl.TCustomerConfigFacadeImpl
 * @CreateTime 2024-12-29 - 15:33:30
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class TCustomerConfigFacadeImpl implements ITCustomerConfigFacade {

    @NonNull
    private ITCustomerConfigService tCustomerConfigService;
    
    @NonNull
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @NonNull
    private ISysUserService sysUserService;
    
    @NonNull
    private ITDeviceInfoService deviceInfoService;
    
    @NonNull
    private ApplicationEventPublisher eventPublisher;

    @Override
    public RPage<TCustomerConfigVO> listTCustomerConfigPage(PageQuery pageQuery, TCustomerConfigSearchDTO tCustomerConfigSearchDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigSearchDTO, TCustomerConfigBO::new);
        IPage<TCustomerConfig> tCustomerConfigIPage = tCustomerConfigService.listTCustomerConfigPage(pageQuery, tCustomerConfigBO);
        return RPage.build(tCustomerConfigIPage, TCustomerConfigVO::new);
    }

    @Override
    public TCustomerConfigVO get(Long id) {
        TCustomerConfig byId = tCustomerConfigService.getById(id);
        return CglibUtil.convertObj(byId, TCustomerConfigVO::new);
    }

    @Override
    @Transactional
    public boolean add(TCustomerConfigAddDTO tCustomerConfigAddDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigAddDTO, TCustomerConfigBO::new);
        
        // 处理字段映射：supportLicense -> isSupportLicense
        if (tCustomerConfigAddDTO.getSupportLicense() != null) {
            tCustomerConfigBO.setIsSupportLicense(tCustomerConfigAddDTO.getSupportLicense());
        }
        
        boolean result = tCustomerConfigService.save(tCustomerConfigBO);
        
        if (result && tCustomerConfigBO.getId() != null) {
            // 同步到 sys_org_units 表
            syncToSysOrgUnits(tCustomerConfigBO.getId(), tCustomerConfigBO.getCustomerName(), "CREATE");
        }
        
        return result;
    }

    @Override
    @Transactional
    public boolean update(TCustomerConfigUpdateDTO tCustomerConfigUpdateDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigUpdateDTO, TCustomerConfigBO::new);
        
        // DTO中已经是isSupportLicense字段，无需特殊映射
        
        boolean result = tCustomerConfigService.updateById(tCustomerConfigBO);
        
        if (result && tCustomerConfigBO.getId() != null) {
            // 同步到 sys_org_units 表
            syncToSysOrgUnits(tCustomerConfigBO.getId(), tCustomerConfigBO.getCustomerName(), "UPDATE");
        }
        
        return result;
    }

    @Override
    @Transactional
    public boolean batchDelete(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        TCustomerConfigBO tCustomerConfigBO = CglibUtil.convertObj(tCustomerConfigDeleteDTO, TCustomerConfigBO::new);
        
        // 在删除前先同步到 sys_org_units
        if (tCustomerConfigBO.getIds() != null) {
            for (Long id : tCustomerConfigBO.getIds()) {
                syncToSysOrgUnits(id, null, "DELETE");
            }
        }
        
        return tCustomerConfigService.removeBatchByIds(tCustomerConfigBO.getIds(), true);
    }
    
    /**
     * 同步租户配置到 sys_org_units 表，仅在CREATE操作时发布事件
     */
    private void syncToSysOrgUnits(Long customerId, String customerName, String operationType) {
        try {
            log.info("同步租户配置到sys_org_units: customerId={}, customerName={}, operation={}", 
                    customerId, customerName, operationType);
            
            SysOrgUnits orgUnit = null;
            boolean shouldPublishEvent = false;
            
            if ("DELETE".equals(operationType)) {
                // 删除操作：标记为删除
                orgUnit = sysOrgUnitsService.getById(customerId);
                if (orgUnit != null) {
                    orgUnit.setIsDeleted(1);
                    sysOrgUnitsService.updateById(orgUnit);
                } else {
                    // 创建一个删除标记的组织单元
                    orgUnit = SysOrgUnits.builder()
                        .id(customerId)
                        .parentId(0L)
                        .name("已删除租户")
                        .code("deleted_" + customerId)
                        .level(1)
                        .ancestors("0")
                        .description("已删除的租户")
                        .sort(999)
                        .status("0")
                        .isDeleted(1)
                        .customerId(customerId)
                        .build();
                }
                shouldPublishEvent = true; // 删除操作需要发布事件
            } else if ("CREATE".equals(operationType)) {
                // 新增操作
                orgUnit = sysOrgUnitsService.getById(customerId);
                if (orgUnit == null) {
                    // 创建新的组织单元（顶级租户）
                    orgUnit = SysOrgUnits.builder()
                        .id(customerId)
                        .parentId(0L) // 顶级租户的父ID为0
                        .name(customerName)
                        .code("tenant_" + customerId)
                        .level(1) // 顶级租户为第一级
                        .ancestors("0") // 祖先路径为"0"
                        .description("租户: " + customerName)
                        .sort(1)
                        .status("1") // 启用状态
                        .isDeleted(0)
                        .customerId(customerId)
                        .build();
                    sysOrgUnitsService.save(orgUnit);
                    shouldPublishEvent = true; // 新增操作需要发布事件
                }
            } else if ("UPDATE".equals(operationType)) {
                // 更新操作：只同步到sys_org_units，不触发OrgUnitsChangeListener
                orgUnit = sysOrgUnitsService.getById(customerId);
                if (orgUnit != null && customerName != null && !customerName.equals(orgUnit.getName())) {
                    // 更新组织单元名称
                    orgUnit.setName(customerName);
                    orgUnit.setDescription("租户: " + customerName);
                    orgUnit.setIsDeleted(0); // 确保不是删除状态
                    sysOrgUnitsService.updateById(orgUnit);
                }
                // UPDATE操作不发布事件，避免触发OrgUnitsChangeListener
                log.info("租户信息更新完成，未发布事件避免触发监听器: customerId={}", customerId);
                return;
            }
            
            // 仅在需要时发布组织变更事件
            if (shouldPublishEvent && orgUnit != null) {
                SysOrgUnitsChangeEvent event = new SysOrgUnitsChangeEvent(this, orgUnit, operationType);
                eventPublisher.publishEvent(event);
                log.info("成功发布组织变更事件: customerId={}, operation={}", customerId, operationType);
            }
            
        } catch (Exception e) {
            log.error("同步租户配置到sys_org_units失败: customerId={}, operation={}", customerId, operationType, e);
            // 不抛出异常，避免影响主业务流程
        }
    }

    @Override
    public DepartmentDeletePreCheckDTO tenantDeletePreCheck(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        log.info("🔍 开始检查租户删除影响，租户IDs: {}", tCustomerConfigDeleteDTO.getIds());
        
        List<Long> tenantIds = tCustomerConfigDeleteDTO.getIds();
        
        // 获取所有要删除的租户下的组织单元（包括租户本身和子部门）
        List<SysOrgUnits> allDepartmentsToDelete = new ArrayList<>();
        for (Long tenantId : tenantIds) {
            // 获取租户本身
            SysOrgUnits tenant = sysOrgUnitsService.getById(tenantId);
            if (tenant != null) {
                allDepartmentsToDelete.add(tenant);
            }
            
            // 获取租户下的所有子部门
            List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(List.of(tenantId));
            allDepartmentsToDelete.addAll(descendants);
        }
        
        List<Long> allOrgIds = allDepartmentsToDelete.stream().map(SysOrgUnits::getId).collect(Collectors.toList());
        
        // 获取受影响的用户
        List<SysUser> affectedUsers = getUsersInDepartments(allOrgIds);
        
        // 获取需要释放的设备
        List<TDeviceInfo> devicesToRelease = getDevicesInDepartments(affectedUsers);
        
        // 构建检查结果
        return buildTenantPreCheckResult(allDepartmentsToDelete, affectedUsers, devicesToRelease);
    }

    @Override
    @Transactional
    public boolean tenantCascadeDelete(TCustomerConfigDeleteDTO tCustomerConfigDeleteDTO) {
        log.info("🗑️ 开始级联删除租户，租户IDs: {}", tCustomerConfigDeleteDTO.getIds());
        
        try {
            List<Long> tenantIds = tCustomerConfigDeleteDTO.getIds();
            
            // 获取所有要删除的租户下的组织单元（包括租户本身和子部门）
            List<SysOrgUnits> allDepartmentsToDelete = new ArrayList<>();
            for (Long tenantId : tenantIds) {
                // 获取租户本身
                SysOrgUnits tenant = sysOrgUnitsService.getById(tenantId);
                if (tenant != null) {
                    allDepartmentsToDelete.add(tenant);
                }
                
                // 获取租户下的所有子部门
                List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(List.of(tenantId));
                allDepartmentsToDelete.addAll(descendants);
            }
            
            List<Long> allOrgIds = allDepartmentsToDelete.stream().map(SysOrgUnits::getId).collect(Collectors.toList());
            
            // 获取受影响的用户
            List<SysUser> affectedUsers = getUsersInDepartments(allOrgIds);
            List<Long> userIds = affectedUsers.stream().map(SysUser::getId).collect(Collectors.toList());
            
            log.info("📊 租户级联删除统计: 租户{}个, 部门{}个, 用户{}个", 
                    tenantIds.size(), allOrgIds.size(), userIds.size());
            
            // 1. 删除用户（会自动释放设备）
            if (!userIds.isEmpty()) {
                boolean userDeleted = sysUserService.forceRemoveBatchByIds(userIds, true);
                if (!userDeleted) {
                    throw new RuntimeException("删除用户失败");
                }
                log.info("✅ 已删除{}个用户并自动释放绑定设备", userIds.size());
            }
            
            // 2. 删除所有组织单元（包括租户和子部门）
            if (!allOrgIds.isEmpty()) {
                boolean orgDeleted = sysOrgUnitsService.removeBatchByIds(allOrgIds, true);
                if (!orgDeleted) {
                    throw new RuntimeException("删除组织单元失败");
                }
                log.info("✅ 已删除{}个组织单元（含租户和部门）", allOrgIds.size());
            }
            
            // 3. 删除租户配置记录
            boolean configDeleted = tCustomerConfigService.removeBatchByIds(tenantIds, true);
            if (!configDeleted) {
                throw new RuntimeException("删除租户配置失败");
            }
            log.info("✅ 已删除{}个租户配置记录", tenantIds.size());
            
            return true;
            
        } catch (Exception e) {
            log.error("❌ 租户级联删除失败: {}", e.getMessage(), e);
            throw new RuntimeException("租户级联删除失败: " + e.getMessage());
        }
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
     * 构建租户删除预检查结果
     */
    private DepartmentDeletePreCheckDTO buildTenantPreCheckResult(
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
        
        // 获取租户数量（level=1的组织）
        int tenantCount = Math.toIntExact(departments.stream()
            .filter(dept -> dept.getLevel() != null && dept.getLevel() == 1)
            .count());
        
        String warningMessage = String.format(
            "此操作将删除 %d 个租户、%d 个部门、%d 个用户，并释放 %d 个设备。其中 %d 个用户绑定了设备。",
            tenantCount, departments.size() - tenantCount, users.size(), devices.size(), usersWithDevices
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