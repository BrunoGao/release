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

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserOrgService;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.ObjectUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Device User Mapping Service 服务接口实现层
 *
 * @deprecated 此服务已废弃，请直接使用 ISysUserService 和相关服务
 *             迁移指南:
 *             - 使用 ISysUserService.getUsersByOrgId() 替代 getDeviceSnListByDepartmentId()
 *             - 使用 ISysUserService + ISysOrgUnitsService 替代 getDeviceUserInfo()
 *             - 直接使用 userId 查询，不再依赖 deviceSn 映射
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @CreateTime 2024-03-20 - 10:00:00
 */
@Deprecated
@Service
@Slf4j
public class DeviceUserMappingServiceImpl implements IDeviceUserMappingService {

    @Autowired
    private ISysUserService sysUserService;

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;

    @Autowired
    private ISysUserOrgService sysUserOrgService;

    @Override
    @Deprecated
    public List<String> getDeviceSnList(String userId, String departmentId) {
        log.info("🔍 过滤参数 - userId: {}, departmentId: {}", userId, departmentId);
        
        if (ObjectUtils.isNotEmpty(userId) && !"all".equals(userId)) {
            try {
                Long userIdLong = Long.parseLong(userId); // #支持长整型用户ID
                SysUser user = sysUserService.getById(userIdLong);
                
                if (user != null && user.getDeviceSn() != null) {
                    log.info("✅ 找到用户设备: userId={}, deviceSn={}", userId, user.getDeviceSn());
                    return Collections.singletonList(user.getDeviceSn());
                }
                log.warn("⚠️ 用户无设备绑定: userId={}", userId);
                return Collections.emptyList();
            } catch (NumberFormatException e) {
                log.warn("❌ 用户ID格式错误: {}", userId);
                return Collections.emptyList();
            }
        } else if (departmentId != null && !departmentId.isEmpty()) {
            return getDeviceSnListByDepartmentId(departmentId);
        }
        log.warn("⚠️ 未提供有效过滤条件");
        return Collections.emptyList();
    }

    /**
     * 根据部门ID获取所有关联的设备序列号 - 优化版本
     * @param departmentId 部门ID
     * @return 设备序列号列表
     */
    @Deprecated
    public List<String> getDeviceSnListByDepartmentId(String departmentId) {
        if (departmentId == null || departmentId.isEmpty()) return Collections.emptyList();
        
        Long deptId;
        try {
            deptId = Long.parseLong(departmentId); // #确保长整型转换支持大数值
        } catch (NumberFormatException e) {
            log.warn("❌ 部门ID格式错误: {}", departmentId);
            return Collections.emptyList();
        }
        
        try {
            log.info("🔍 查询部门设备列表: deptId={}", deptId);
            // 获取组织的customerId
            SysOrgUnits org = sysOrgUnitsService.getById(deptId);
            Long customerId = (org != null) ? org.getCustomerId() : null;
            
            List<SysUser> users = sysUserService.getUsersByOrgId(deptId, customerId);
            log.info("📊 找到用户数量: {}", users.size());
            
            if (users.isEmpty()) {
                log.warn("⚠️ 部门 {} 下没有找到任何用户", deptId);
            } else {
                log.info("👥 部门用户详情:");
                users.forEach(user -> 
                    log.info("  用户ID: {}, 姓名: {}, 设备SN: {}", 
                        user.getId(), user.getUserName(), user.getDeviceSn())
                );
            }
            
            if (users.isEmpty()) return Collections.emptyList();
            
            List<String> deviceSnList = users.stream()
                .filter(u -> u.getDeviceSn() != null && !u.getDeviceSn().trim().isEmpty())
                .map(SysUser::getDeviceSn)
                .limit(1000) // #限制最大1000个设备
                .collect(Collectors.toList());
            
            log.info("✅ 获取到设备序列号数量: {}, 列表: {}", deviceSnList.size(), deviceSnList);
            return deviceSnList;
        } catch (Exception e) {
            log.error("❌ 查询部门设备列表失败: deptId={}", deptId, e);
            return Collections.emptyList();
        }
    }

    @Override
    @Deprecated
    public Map<String, UserInfo> getDeviceUserInfo(Set<String> deviceSns) {
        Map<String, UserInfo> deviceUserMap = new HashMap<>();
        if (deviceSns == null || deviceSns.isEmpty()) {
            return deviceUserMap;
        }

        try {
            // 批量查询用户信息
            List<SysUser> users = sysUserService.list(new LambdaQueryWrapper<SysUser>()
                .in(SysUser::getDeviceSn, deviceSns));

            // 获取所有用户ID
            List<Long> userIds = users.stream()
                .map(SysUser::getId)
                .collect(Collectors.toList());

            // 批量查询用户组织关系
            Map<Long, List<SysUserOrg>> userOrgMap = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
                .in(SysUserOrg::getUserId, userIds))
                .stream()
                .collect(Collectors.groupingBy(SysUserOrg::getUserId));

            // 获取所有组织ID
            Set<Long> orgIds = userOrgMap.values().stream()
                .flatMap(List::stream)
                .map(SysUserOrg::getOrgId)
                .collect(Collectors.toSet());

            // 批量查询组织信息
            Map<Long, SysOrgUnits> orgMap = sysOrgUnitsService.listByIds(orgIds)
                .stream()
                .collect(Collectors.toMap(SysOrgUnits::getId, org -> org));

            // 组装用户和部门信息
            for (SysUser user : users) {
                if (user.getDeviceSn() != null) {
                    UserInfo userInfo = new UserInfo();
                    userInfo.setUserName(user.getUserName());
                    
                    // 获取用户的部门信息
                    List<SysUserOrg> userOrgs = userOrgMap.getOrDefault(user.getId(), Collections.emptyList());
                    if (!userOrgs.isEmpty()) {
                        String deptNames = userOrgs.stream()
                            .map(userOrg -> {
                                SysOrgUnits org = orgMap.get(userOrg.getOrgId());
                                return org != null ? org.getName() : "";
                            })
                            .filter(name -> !name.isEmpty())
                            .collect(Collectors.joining(", "));
                        userInfo.setDepartmentName(deptNames);
                    }
                    
                    deviceUserMap.put(user.getDeviceSn(), userInfo);
                }
            }
        } catch (Exception e) {
            log.error("Error getting device user info: ", e);
        }

        return deviceUserMap;
    }

    @Override
    @Deprecated
    public Map<String, UserInfo> getUserInfoMap(List<String> deviceSnList) {
        return getDeviceUserInfo(new HashSet<>(deviceSnList));
    }
} 