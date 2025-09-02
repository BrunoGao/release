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
import com.ljwx.modules.health.domain.vo.MessageResponseDetailVO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageMapper;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import com.ljwx.modules.health.domain.entity.TDeviceMessageV2;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageV2Mapper;
import com.ljwx.modules.health.service.ITDeviceMessageDetailV2Service;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserOrgService;
import com.ljwx.modules.system.service.ISysUserService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

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
    private ITDeviceMessageDetailV2Service deviceMessageDetailService;

    @Autowired
    private ISysUserOrgService sysUserOrgService;

    @Autowired
    private TDeviceMessageV2Mapper messageV2Mapper;

    // #管理员用户缓存 - 避免频繁查询
    private List<String> adminUserIdsCache = null;
    private long lastCacheTime = 0L;
    private static final long CACHE_EXPIRY = 5 * 60 * 1000L; // 5分钟缓存

    @Override
    public IPage<TDeviceMessageVO> listTDeviceMessagePage(PageQuery pageQuery, TDeviceMessageBO tDeviceMessageBO) {
        System.out.println("🚀 使用V2优化查询 - userId: " + tDeviceMessageBO.getUserId() + ", departmentInfo: " + tDeviceMessageBO.getDepartmentInfo());
        
        // 🔥 使用V2表进行优化查询
        LambdaQueryWrapper<TDeviceMessageV2> queryWrapper = new LambdaQueryWrapper<TDeviceMessageV2>()
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getMessageType()), TDeviceMessageV2::getMessageType, tDeviceMessageBO.getMessageType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getSenderType()), TDeviceMessageV2::getSenderType, tDeviceMessageBO.getSenderType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getReceiverType()), TDeviceMessageV2::getReceiverType, tDeviceMessageBO.getReceiverType())
                .eq(ObjectUtils.isNotEmpty(tDeviceMessageBO.getMessageStatus()), TDeviceMessageV2::getMessageStatus, tDeviceMessageBO.getMessageStatus())
                .eq(TDeviceMessageV2::getIsDeleted, 0)
                .orderByDesc(TDeviceMessageV2::getPriorityLevel)
                .orderByDesc(TDeviceMessageV2::getCreateTime);

        if (ObjectUtils.isEmpty(tDeviceMessageBO.getUserId()) || tDeviceMessageBO.getUserId().equals("all")) {
            // 处理按部门查询的逻辑
            System.out.println("📋 执行部门查询逻辑 (V2优化版)");
            handleDepartmentQueryV2(queryWrapper, tDeviceMessageBO.getDepartmentInfo());
        } else {
            // 🔥 处理按用户ID查询的逻辑 - 直接基于userId查询
            System.out.println("👤 执行用户查询逻辑 (V2优化版)");
            handleUserQueryV2(queryWrapper, tDeviceMessageBO.getUserId());
        }

        // 执行分页查询并处理结果
        return processQueryResultsV2(pageQuery, queryWrapper);
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
                new LambdaQueryWrapper<TDeviceMessageDetailV2>()
                    .eq(TDeviceMessageDetailV2::getMessageId, messageId)
                    .eq(TDeviceMessageDetailV2::getDeviceSn, deviceSn)
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
            List<TDeviceMessageDetailV2> messageDetails = deviceMessageDetailService.list(
                new LambdaQueryWrapper<TDeviceMessageDetailV2>()
                    .eq(TDeviceMessageDetailV2::getMessageId, messageId)
            );
        
            // Get the department info from the V2 message
            TDeviceMessageV2 messageV2 = messageV2Mapper.selectById(Long.parseLong(messageId));
            
            List<String> departmentDeviceSns = new ArrayList<>();
            
            if (messageV2 != null && messageV2.getDepartmentId() != null) {
                // 获取部门下所有用户的设备SN
                List<SysUserOrg> userOrgs = sysUserOrgService.list(
                    new LambdaQueryWrapper<SysUserOrg>()
                        .eq(SysUserOrg::getOrgId, messageV2.getDepartmentId())
                        .eq(SysUserOrg::getDeleted, 0)
                );
                
                List<Long> userIds = userOrgs.stream()
                    .map(SysUserOrg::getUserId)
                    .collect(Collectors.toList());
                    
                if (!userIds.isEmpty()) {
                    departmentDeviceSns = sysUserService.list(
                        new LambdaQueryWrapper<SysUser>()
                            .in(SysUser::getId, userIds)
                            .isNotNull(SysUser::getDeviceSn)
                            .eq(SysUser::getDeleted, 0)
                    ).stream()
                    .map(SysUser::getDeviceSn)
                    .filter(Objects::nonNull)
                    .collect(Collectors.toList());
                }
            }
    
            // Create sets for tracking
            Set<String> respondedDeviceSns = messageDetails.stream()
                .map(TDeviceMessageDetailV2::getDeviceSn)
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

    // === V2优化查询方法 ===

    /**
     * 🔥 V2优化：处理用户查询 - 直接基于userId
     */
    private void handleUserQueryV2(LambdaQueryWrapper<TDeviceMessageV2> queryWrapper, String userId) {
        if (StringUtils.hasText(userId)) {
            Long userIdLong = Long.parseLong(userId);
            // 🔥 核心优化：直接基于userId查询，避免复杂关联
            queryWrapper.eq(TDeviceMessageV2::getUserId, userIdLong);
            System.out.println("🚀 V2用户查询 - 直接userId匹配: " + userIdLong);
        }
    }

    /**
     * 🔥 V2优化：处理部门查询 - 基于departmentId
     */
    private void handleDepartmentQueryV2(LambdaQueryWrapper<TDeviceMessageV2> queryWrapper, String departmentInfo) {
        if (ObjectUtils.isNotEmpty(departmentInfo)) {
            Set<Long> allDepartmentIds = new HashSet<>();
            Long deptId = Long.parseLong(departmentInfo);
            
            // 获取当前部门及其所有下属部门
            allDepartmentIds.add(deptId);
            List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(deptId));
            allDepartmentIds.addAll(
                descendants.stream()
                    .map(SysOrgUnits::getId)
                    .collect(Collectors.toSet())
            );

            // 🔥 V2优化：直接基于departmentId查询
            queryWrapper.in(TDeviceMessageV2::getDepartmentId, allDepartmentIds);
            
            System.out.println("🚀 V2部门查询 - departmentIds: " + allDepartmentIds);
        }
    }

    /**
     * 🔥 V2优化：处理查询结果
     */
    private IPage<TDeviceMessageVO> processQueryResultsV2(PageQuery pageQuery, LambdaQueryWrapper<TDeviceMessageV2> queryWrapper) {
        // 执行分页查询
        IPage<TDeviceMessageV2> page = messageV2Mapper.selectPage(pageQuery.buildPage(), queryWrapper);

        // 转换为VO
        IPage<TDeviceMessageVO> voPage = page.convert(message -> {
            TDeviceMessageVO vo = new TDeviceMessageVO();
            // 🔥 V2到V1 VO的转换
            vo.setId(message.getId());
            vo.setDepartmentInfo(String.valueOf(message.getDepartmentId()));
            vo.setUserId(String.valueOf(message.getUserId()));
            vo.setDeviceSn(message.getDeviceSn());
            vo.setMessage(message.getMessage());
            vo.setMessageType(message.getMessageType());
            vo.setSenderType(message.getSenderType());
            vo.setReceiverType(message.getReceiverType());
            vo.setMessageStatus(message.getMessageStatus());
            vo.setSentTime(message.getSentTime());
            vo.setReceivedTime(message.getReceivedTime());
            vo.setCreateUser(message.getCreateUserId() != null ? String.valueOf(message.getCreateUserId()) : null);
            vo.setCreateTime(message.getCreateTime());
            
            // 设置详情信息
            vo.setRespondedDetail(getMessageResponseDetailsV2(
                String.valueOf(message.getId()), 
                String.valueOf(message.getUserId())
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
                try {
                    Long deptId = Long.parseLong(record.getDepartmentInfo());
                    String formattedDeptInfo = deptMap.get(deptId);
                    record.setDepartmentInfo(formattedDeptInfo);
                } catch (NumberFormatException e) {
                    System.out.println("部门ID格式错误: " + record.getDepartmentInfo());
                }
            }
            if (StringUtils.hasText(record.getUserId())) {
                try {
                    Long userId = Long.parseLong(record.getUserId());
                    String formattedUserId = userMap.get(userId);
                    record.setUserId(formattedUserId);
                } catch (NumberFormatException e) {
                    System.out.println("用户ID格式错误: " + record.getUserId());
                }
            }
        });

        return voPage;
    }

    /**
     * 🔥 V2优化：获取消息响应详情
     */
    private MessageResponseDetailVO getMessageResponseDetailsV2(String messageId, String userId) {
        System.out.println("🚀 V2获取消息详情 - messageId: " + messageId + ", userId: " + userId);
        
        if (userId != null && !userId.equals("all") && !userId.equals("") && !userId.equals("null")) {
            // 针对特定用户的逻辑
            try {
                Long userIdLong = Long.parseLong(userId);
                SysUser user = sysUserService.getById(userIdLong);
                System.out.println("user: " + user);
                
                if (user == null) {
                    return new MessageResponseDetailVO(0L, 0, new ArrayList<>());
                }
                
                // 🔥 V2优化：直接基于userId查询详情
                Long messageIdLong = Long.parseLong(messageId);
                TDeviceMessageDetailV2 detail = deviceMessageDetailService.getByMessageAndUser(messageIdLong, userIdLong);
                
                boolean hasResponded = detail != null && "delivered".equals(detail.getDeliveryStatus());
                
                List<MessageResponseDetailVO.NonRespondedUserVO> nonRespondedUsers = new ArrayList<>();
                if (!hasResponded) {
                    // 如果未响应，获取用户信息
                    MessageResponseDetailVO.NonRespondedUserVO userInfo = sysUserService.getByDeviceSn(user.getDeviceSn());
                    if (userInfo != null) {
                        nonRespondedUsers.add(userInfo);
                    }
                }

                return new MessageResponseDetailVO(
                    1L, // 总设备数为1
                    hasResponded ? 1 : 0, // 已响应数
                    nonRespondedUsers // 未响应用户列表
                );
            } catch (NumberFormatException e) {
                System.out.println("ID格式错误 - messageId: " + messageId + ", userId: " + userId);
                return new MessageResponseDetailVO(0L, 0, new ArrayList<>());
            }
        } else {
            // 部门所有用户的统计逻辑
            try {
                Long messageIdLong = Long.parseLong(messageId);
                
                // 🔥 V2优化：直接查询该消息的所有详情记录
                List<TDeviceMessageDetailV2> messageDetails = deviceMessageDetailService.list(
                    new LambdaQueryWrapper<TDeviceMessageDetailV2>()
                        .eq(TDeviceMessageDetailV2::getMessageId, messageIdLong)
                        .eq(TDeviceMessageDetailV2::getIsDeleted, 0)
                );
                
                Set<String> respondedDeviceSns = messageDetails.stream()
                    .filter(detail -> "delivered".equals(detail.getDeliveryStatus()))
                    .map(TDeviceMessageDetailV2::getDeviceSn)
                    .collect(Collectors.toSet());
                
                // 获取该消息对应的所有目标用户
                Set<String> allTargetDeviceSns = messageDetails.stream()
                    .map(TDeviceMessageDetailV2::getDeviceSn)
                    .collect(Collectors.toSet());
                    
                long totalDevices = allTargetDeviceSns.size();
                    
                // 获取未响应用户信息
                List<MessageResponseDetailVO.NonRespondedUserVO> nonRespondedUsers = allTargetDeviceSns.stream()
                    .filter(deviceSn -> !respondedDeviceSns.contains(deviceSn))
                    .map(deviceSn -> {
                        MessageResponseDetailVO.NonRespondedUserVO userInfo = 
                            new MessageResponseDetailVO.NonRespondedUserVO();
                        userInfo = sysUserService.getByDeviceSn(deviceSn);
                        return userInfo;
                    })
                    .filter(userInfo -> userInfo != null && userInfo.getUserName() != null)
                    .collect(Collectors.toList());
                    
                return new MessageResponseDetailVO(
                    totalDevices,
                    respondedDeviceSns.size(),
                    nonRespondedUsers
                );
            } catch (NumberFormatException e) {
                System.out.println("消息ID格式错误: " + messageId);
                return new MessageResponseDetailVO(0L, 0, new ArrayList<>());
            }
        }
    }

    /**
     * 🔥 V2优化：保存消息 - 使用V2表
     */
    public boolean saveMessage(TDeviceMessageBO tDeviceMessageBO) {
        try {
            // 转换BO到V2实体
            TDeviceMessageV2 messageV2 = TDeviceMessageV2.builder()
                .customerId(tDeviceMessageBO.getCustomerId())
                .departmentId(parseDepartmentInfo(tDeviceMessageBO.getDepartmentInfo()))
                .userId(parseUserId(tDeviceMessageBO.getUserId()))
                .deviceSn(tDeviceMessageBO.getDeviceSn())
                .message(tDeviceMessageBO.getMessage())
                .messageType(tDeviceMessageBO.getMessageType())
                .senderType(tDeviceMessageBO.getSenderType())
                .receiverType(tDeviceMessageBO.getReceiverType())
                .messageStatus(tDeviceMessageBO.getMessageStatus())
                .sentTime(tDeviceMessageBO.getSentTime())
                .receivedTime(tDeviceMessageBO.getReceivedTime())
                .createUserId(tDeviceMessageBO.getCreateUserId())
                .build();
            
            // 保存到V2表
            int result = messageV2Mapper.insert(messageV2);
            
            // 如果有用户ID，创建详情记录
            if (messageV2.getUserId() != null) {
                TDeviceMessageDetailV2 detail = TDeviceMessageDetailV2.builder()
                    .messageId(messageV2.getId())
                    .customerId(messageV2.getCustomerId())
                    .userId(messageV2.getUserId())
                    .deviceSn(messageV2.getDeviceSn())
                    .deliveryStatus("pending")
                    .build();
                
                deviceMessageDetailService.save(detail);
            }
            
            System.out.println("🚀 V2消息保存成功 - messageId: " + messageV2.getId());
            return result > 0;
            
        } catch (Exception e) {
            System.err.println("❌ V2消息保存失败: " + e.getMessage());
            return false;
        }
    }

    /**
     * 🔥 V2优化：根据ID获取消息
     */
    public TDeviceMessage getById(Long id) {
        // 从V2表查询
        TDeviceMessageV2 messageV2 = messageV2Mapper.selectById(id);
        if (messageV2 == null) {
            return null;
        }
        
        // 转换V2到V1实体
        TDeviceMessage message = new TDeviceMessage();
        message.setId(messageV2.getId());
        message.setDepartmentInfo(messageV2.getDepartmentId() != null ? String.valueOf(messageV2.getDepartmentId()) : null);
        message.setUserId(messageV2.getUserId() != null ? String.valueOf(messageV2.getUserId()) : null);
        message.setDeviceSn(messageV2.getDeviceSn());
        message.setMessage(messageV2.getMessage());
        message.setMessageType(messageV2.getMessageType());
        message.setSenderType(messageV2.getSenderType());
        message.setReceiverType(messageV2.getReceiverType());
        message.setMessageStatus(messageV2.getMessageStatus());
        message.setSentTime(messageV2.getSentTime());
        message.setReceivedTime(messageV2.getReceivedTime());
        message.setCreateUserId(messageV2.getCreateUserId());
        message.setCreateTime(messageV2.getCreateTime());
        message.setUpdateTime(messageV2.getUpdateTime());
        message.setDeleted(messageV2.getIsDeleted());
        message.setCustomerId(messageV2.getCustomerId());
        
        return message;
    }

    // === 辅助方法 ===
    
    private Long parseDepartmentInfo(String departmentInfo) {
        if (!StringUtils.hasText(departmentInfo)) {
            return 1L; // 默认部门
        }
        try {
            return Long.parseLong(departmentInfo);
        } catch (NumberFormatException e) {
            return 1L; // 默认部门
        }
    }
    
    private Long parseUserId(String userId) {
        if (!StringUtils.hasText(userId) || "null".equals(userId)) {
            return null;
        }
        try {
            return Long.parseLong(userId);
        } catch (NumberFormatException e) {
            return null;
        }
    }

}