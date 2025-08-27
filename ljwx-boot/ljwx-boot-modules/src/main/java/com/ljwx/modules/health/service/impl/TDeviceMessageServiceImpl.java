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
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.ObjectUtils;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.bo.TDeviceMessageBO;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageMapper;
import com.ljwx.modules.health.service.ITDeviceMessageDetailService;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserOrgService;
import com.ljwx.modules.system.service.ISysUserService;
import com.ljwx.modules.health.service.IDeviceUserMappingService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.*;
import java.util.stream.Collectors;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;

/**
 *  Service 服务接口实现层
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceMessageServiceImpl
 * @CreateTime 2024-10-24 - 13:07:24
 */

@Service
public class TDeviceMessageServiceImpl extends ServiceImpl<TDeviceMessageMapper, TDeviceMessage> implements ITDeviceMessageService {

    @Autowired
    private ISysUserService sysUserService;

    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;

    @Autowired
    private ITDeviceMessageDetailService deviceMessageDetailService;

    @Autowired
    private IDeviceUserMappingService deviceUserMappingService;

    @Autowired
    private ISysUserOrgService sysUserOrgService;

    // #管理员用户缓存 - 避免频繁查询
    private List<String> adminUserIdsCache = null;
    private long lastCacheTime = 0L;
    private static final long CACHE_EXPIRY = 5 * 60 * 1000L; // 5分钟缓存

    @Override
    public IPage<TDeviceMessageVO> listTDeviceMessagePage(PageQuery pageQuery, TDeviceMessageBO tDeviceMessageBO) {
        // 构建基础查询条件
        LambdaQueryWrapper<TDeviceMessage> queryWrapper = new LambdaQueryWrapper<TDeviceMessage>()
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getMessageType()), TDeviceMessage::getMessageType, tDeviceMessageBO.getMessageType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getSenderType()), TDeviceMessage::getSenderType, tDeviceMessageBO.getSenderType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getReceiverType()), TDeviceMessage::getReceiverType, tDeviceMessageBO.getReceiverType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getMessageStatus()), TDeviceMessage::getMessageStatus, tDeviceMessageBO.getMessageStatus())
                .orderByDesc(TDeviceMessage::getSentTime);
        System.out.println("🔍 设备消息查询 - userId: " + tDeviceMessageBO.getUserId() + ", departmentInfo: " + tDeviceMessageBO.getDepartmentInfo());

        if (ObjectUtils.isEmpty(tDeviceMessageBO.getUserId()) || tDeviceMessageBO.getUserId().equals("all")) {
            // 处理按部门查询的逻辑 - 将自动排除管理员私人消息
            System.out.println("📋 执行部门查询逻辑 (将排除管理员私人消息)");
            handleDepartmentQuery(queryWrapper, tDeviceMessageBO.getDepartmentInfo());
        } else {
            // 处理按用户ID查询的逻辑
            System.out.println("👤 执行用户查询逻辑");
            handleUserQuery(queryWrapper, tDeviceMessageBO.getUserId());
        }

        // 执行分页查询并处理结果
        return processQueryResults(pageQuery, queryWrapper);
    }

    private void handleDepartmentQuery(LambdaQueryWrapper<TDeviceMessage> queryWrapper, String departmentInfo) {
        if (ObjectUtils.isNotEmpty(departmentInfo)) {
            Set<String> allDepartmentIds = new HashSet<>();
            Long deptId = Long.parseLong(departmentInfo);
            
            // 获取当前部门及其所有下属部门
            allDepartmentIds.add(departmentInfo);
            List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(deptId));
            allDepartmentIds.addAll(
                descendants.stream()
                    .map(unit -> String.valueOf(unit.getId()))
                    .collect(Collectors.toSet())
            );

            // 🔧 部门查询时排除管理员私人消息 #管理员过滤优化
            queryWrapper.and(wrapper -> {
                wrapper.in(TDeviceMessage::getDepartmentInfo, allDepartmentIds)
                      .and(w -> w.isNull(TDeviceMessage::getUserId) // 部门公告（userId为空）
                               .or(subW -> subW.isNotNull(TDeviceMessage::getUserId)
                                              .notIn(TDeviceMessage::getUserId, getAdminUserIds()))); // 排除管理员用户ID
            });
            
            System.out.println("🔍 部门查询 - departmentIds: " + allDepartmentIds + ", 排除管理员: " + getAdminUserIds());
        }
    }
    
    /**
     * 获取所有管理员用户ID列表（带缓存）
     * @return 管理员用户ID列表
     */
    private List<String> getAdminUserIds() {
        long currentTime = System.currentTimeMillis();
        
        // 检查缓存是否有效
        if (adminUserIdsCache != null && (currentTime - lastCacheTime) < CACHE_EXPIRY) {
            return adminUserIdsCache;
        }
        
        try {
            // 🚀 优化: 直接SQL查询管理员用户，避免多次数据库访问
            List<String> adminUserIds = sysUserService.list(new LambdaQueryWrapper<SysUser>()
                .exists("SELECT 1 FROM sys_user_role ur " +
                       "JOIN sys_role r ON ur.role_id = r.id " +
                       "WHERE ur.user_id = sys_user.id " +
                       "AND r.is_admin = 1 " +
                       "AND ur.is_deleted = 0 " +
                       "AND r.is_deleted = 0"))
                .stream()
                .map(user -> String.valueOf(user.getId()))
                .collect(Collectors.toList());
                
            // 更新缓存
            adminUserIdsCache = adminUserIds;
            lastCacheTime = currentTime;
                
            System.out.println("📊 管理员用户列表更新: " + adminUserIds + " (缓存时间: " + new java.util.Date(currentTime) + ")");
            return adminUserIds;
        } catch (Exception e) {
            System.err.println("❌ 获取管理员用户列表失败: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    private void handleUserQuery(LambdaQueryWrapper<TDeviceMessage> queryWrapper, String userId) {
        if (StringUtils.hasText(userId)) {
            Long userIdLong = Long.parseLong(userId);
            // 1. 查询用户所属部门信息
            SysUserOrg userOrg = sysUserOrgService.getOne(
                new LambdaQueryWrapper<SysUserOrg>()
                    .eq(SysUserOrg::getUserId, userIdLong)
            );

            if (userOrg != null) {
                // 2. 获取部门的ancestors
                SysOrgUnits orgUnit = sysOrgUnitsService.getById(userOrg.getOrgId());
                if (orgUnit != null && StringUtils.hasText(orgUnit.getAncestors())) {
                    // 3. 处理ancestors，去掉开头的0
                    List<String> ancestorIds = Arrays.stream(orgUnit.getAncestors().split(","))
                        .filter(id -> !"0".equals(id))
                        .collect(Collectors.toList());

                    // 4. 构建查询条件：合并两种查询
                    queryWrapper.and(wrapper -> {
                        // 直接匹配userId的消息
                        wrapper.or()
                              .eq(TDeviceMessage::getUserId, userIdLong);

                        // 匹配上级部门且userId为空的消息
                        if (!ancestorIds.isEmpty()) {
                            wrapper.or(w -> {
                                w.in(TDeviceMessage::getDepartmentInfo, ancestorIds)
                                 .isNull(TDeviceMessage::getUserId);
                            });
                        }
                    });
                }
            }
        }
    }

    private IPage<TDeviceMessageVO> processQueryResults(PageQuery pageQuery, LambdaQueryWrapper<TDeviceMessage> queryWrapper) {
        // 执行分页查询
        IPage<TDeviceMessage> page = baseMapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 转换为VO
        IPage<TDeviceMessageVO> voPage = page.convert(message -> {
            TDeviceMessageVO vo = new TDeviceMessageVO();
            BeanUtils.copyProperties(message, vo);
            vo.setRespondedDetail(getMessageResponseDetails(
                String.valueOf(message.getId()), 
                vo.getUserId()
            ));
            return vo;
        });

        // 批量获取名称映射
        Map<Long, String> deptMap = sysOrgUnitsService.list().stream()
            .collect(Collectors.toMap(SysOrgUnits::getId, SysOrgUnits::getName, (k1, k2) -> k1));
        Map<Long, String> userMap = sysUserService.list().stream()
            .collect(Collectors.toMap(SysUser::getId, SysUser::getUserName, (k1, k2) -> k1));

        // 转换ID为名称
        voPage.getRecords().forEach(record -> {
            if (StringUtils.hasText(record.getDepartmentInfo())) {
                String formattedDeptInfo = deptMap.get(Long.parseLong(record.getDepartmentInfo()));
                record.setDepartmentInfo(formattedDeptInfo);
            }
            if (StringUtils.hasText(record.getUserId())) {
                String formattedUserId = userMap.get(Long.parseLong(record.getUserId()));
                record.setUserId(formattedUserId);
            }
        });

        return voPage;
    }

    private MessageResponseDetailVO getMessageResponseDetails(String messageId, String userId) {

        System.out.println("messageId: " + messageId);
        System.out.println("userId: " + userId);
        if (userId != null && !userId.equals("all") && !userId.equals("") && !userId.equals("null")) {
            // 针对特定用户的逻辑
            SysUser user = sysUserService.getById(userId);
            System.out.println("user: " + user);
            if (user == null) {
                return new MessageResponseDetailVO(0L, 0, new ArrayList<>());
            }
            String deviceSn = user.getDeviceSn();
            
            // 检查是否有响应记录
            boolean hasResponded = deviceMessageDetailService.count(
                new LambdaQueryWrapper<TDeviceMessageDetail>()
                    .eq(TDeviceMessageDetail::getMessageId, messageId)
                    .eq(TDeviceMessageDetail::getDeviceSn, deviceSn)
            ) > 0;

            List<MessageResponseDetailVO.NonRespondedUserVO> nonRespondedUsers = new ArrayList<>();
            if (!hasResponded) {
                // 如果未响应，获取用户信息
                MessageResponseDetailVO.NonRespondedUserVO userInfo = sysUserService.getByDeviceSn(deviceSn);
                if (userInfo != null) {
                    nonRespondedUsers.add(userInfo);
                }
            }

            return new MessageResponseDetailVO(
                1L, // 总设备数为1
                hasResponded ? 1 : 0, // 已响应数
                nonRespondedUsers // 未响应用户列表
            );
        } else {
            // Get all device details for this message
            List<TDeviceMessageDetail> messageDetails = deviceMessageDetailService.list(
                new LambdaQueryWrapper<TDeviceMessageDetail>()
                    .eq(TDeviceMessageDetail::getMessageId, messageId)
            );
        
            // Get the department info from the original message
            TDeviceMessage message = this.getById(messageId);
            
            List<String> departmentDeviceSns;
        
                // Original logic for all users in department
            String departmentId = message.getDepartmentInfo();
            departmentDeviceSns = deviceUserMappingService.getDeviceSnListByDepartmentId(departmentId);
    
            // Create sets for tracking
            Set<String> respondedDeviceSns = messageDetails.stream()
                .map(TDeviceMessageDetail::getDeviceSn)
                .collect(Collectors.toSet());
                
            // Count total devices
            long totalDevices = departmentDeviceSns.size();
                
            // Get non-responded devices and their user info
            List<MessageResponseDetailVO.NonRespondedUserVO> nonRespondedUsers = departmentDeviceSns.stream()
                .filter(deviceSn -> !respondedDeviceSns.contains(deviceSn))
                .map(deviceSn -> {
                    MessageResponseDetailVO.NonRespondedUserVO userInfo = 
                        new MessageResponseDetailVO.NonRespondedUserVO();
                    // Get user info by device SN
                    userInfo= sysUserService.getByDeviceSn(deviceSn);
                    return userInfo;
                })
                .filter(userInfo -> userInfo.getUserName() != null)
                .collect(Collectors.toList());
                
            return new MessageResponseDetailVO(
                totalDevices,
                respondedDeviceSns.size(),
                nonRespondedUsers
            );
        }
    }

}