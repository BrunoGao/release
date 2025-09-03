package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.OrgStatisticsVO;
import com.ljwx.modules.health.service.*;
import com.ljwx.modules.system.domain.entity.SysOrgUnits;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.domain.entity.SysUserOrg;
import com.ljwx.modules.system.service.ISysOrgUnitsService;
import com.ljwx.modules.system.service.ISysUserOrgService;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@Service
@Slf4j
public class OrgStatisticsServiceImpl implements IOrgStatisticsService {
    
    @Autowired
    private ITDeviceInfoService deviceInfoService;
    
    @Autowired
    private ITAlertInfoService alertService;
    
    @Autowired
    private ITDeviceMessageService messageService;
    
    @Autowired
    private ITUserHealthDataService healthDataService;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private ISysOrgUnitsService sysOrgUnitsService;
    
    @Autowired
    private IDeviceUserMappingService deviceUserMappingService;
    
    @Autowired
    private ITAlertInfoService alertInfoService;
    
    @Autowired
    private ISysUserOrgService sysUserOrgService;
    
    @Override
    public OrgStatisticsVO getOrgStatistics(String orgId) {
        OrgStatisticsVO statistics = new OrgStatisticsVO();
        
        // 1. 获取部门下所有设备
        List<String> deviceSnList = deviceUserMappingService.getDeviceSnListByDepartmentId(orgId);
        
        // 2. 获取并设置告警信息
        statistics.setAlertInfo(getTAlertInfo(deviceSnList));
        
        // 3. 获取并设置设备信息
        statistics.setDeviceInfo(getDeviceInfo(deviceSnList));
        
        // 4. 获取并设置健康数据
        statistics.setHealthData(getHealthData(deviceSnList));
        
        // 5. 获取并设置消息信息
        statistics.setMessageInfo(getMessageInfo(orgId));
        
        // 6. 获取并设置用户信息 - 直接设置 UserInfoVO
        statistics.setUserInfo(queryUserInfoWithOrgId(Long.parseLong(orgId)));
        
        return statistics;
    }
    
    @Override
    public OrgStatisticsVO getOrgStatisticsByCustomerId(String customerId) {
        log.info("🏢 根据customerId获取组织统计信息: {}", customerId);
        
        // 1. 将customerId转换为orgId
        Long orgId = convertCustomerIdToOrgId(customerId);
        if (orgId == null) {
            log.warn("⚠️ 无法根据customerId找到对应的组织ID: {}", customerId);
            return createEmptyStatistics();
        }
        
        log.info("✅ customerId {} -> orgId {}", customerId, orgId);
        
        // 2. 使用转换后的orgId获取统计信息
        return getOrgStatistics(String.valueOf(orgId));
    }
    
    /**
     * 将customerId转换为对应的顶级orgId
     * 支持多级部门管理员登录，次级部门管理员的id只能是orgId而不是customerId
     * @param customerId 客户ID
     * @return 对应的组织ID
     */
    private Long convertCustomerIdToOrgId(String customerId) {
        try {
            Long customerIdLong = Long.parseLong(customerId);
            
            // 查找该customerId下的顶级组织（parent_id = 0）
            LambdaQueryWrapper<SysOrgUnits> query = new LambdaQueryWrapper<SysOrgUnits>()
                .eq(SysOrgUnits::getCustomerId, customerIdLong)
                .eq(SysOrgUnits::getParentId, 0L)
                .eq(SysOrgUnits::getDeleted, 0)
                .eq(SysOrgUnits::getStatus, "1") // 只查询启用的组织
                .orderByAsc(SysOrgUnits::getId) // 如果有多个，取最早创建的
                .last("LIMIT 1");
            
            SysOrgUnits rootOrg = sysOrgUnitsService.getOne(query);
            if (rootOrg != null) {
                log.info("✅ 找到customerId {} 对应的顶级组织: {} ({})", 
                    customerId, rootOrg.getId(), rootOrg.getName());
                return rootOrg.getId();
            } else {
                // 如果没有找到顶级组织，尝试直接使用customerId作为orgId
                log.warn("⚠️ 未找到customerId {} 的顶级组织，尝试直接使用作为orgId", customerId);
                
                // 检查该ID是否存在于组织表中
                SysOrgUnits directOrg = sysOrgUnitsService.getById(customerIdLong);
                if (directOrg != null && !directOrg.getDeleted().equals(1)) {
                    log.info("✅ customerId {} 直接存在于组织表中: {} ({})", 
                        customerId, directOrg.getId(), directOrg.getName());
                    return directOrg.getId();
                }
            }
            
            log.error("❌ 无法找到customerId {} 对应的组织", customerId);
            return null;
            
        } catch (NumberFormatException e) {
            log.error("❌ customerId格式错误: {}", customerId, e);
            return null;
        } catch (Exception e) {
            log.error("❌ 转换customerId到orgId失败: {}", customerId, e);
            return null;
        }
    }
    
    /**
     * 创建空的统计信息
     */
    private OrgStatisticsVO createEmptyStatistics() {
        OrgStatisticsVO statistics = new OrgStatisticsVO();
        statistics.setAlertInfo(createEmptyTAlertInfo());
        statistics.setDeviceInfo(createEmptyDeviceInfo());
        statistics.setHealthData(new HashMap<>());
        statistics.setMessageInfo(createEmptyMessageInfo());
        statistics.setUserInfo(createEmptyUserInfo());
        return statistics;
    }
    
    private OrgStatisticsVO.AlertInfoVO getTAlertInfo(List<String> deviceSnList ) {
        OrgStatisticsVO.AlertInfoVO alertInfo = new OrgStatisticsVO.AlertInfoVO();
        
        // 🔧 修复: 检查设备列表是否为空,避免SQL语法错误
        if (deviceSnList == null || deviceSnList.isEmpty()) {
            log.warn("告警查询设备序列号列表为空,返回默认告警信息");
            return createEmptyTAlertInfo();
        }
        
        // 🔧 修复: 过滤无效的设备序列号
        List<String> validDeviceSnList = deviceSnList.stream()
            .filter(Objects::nonNull)
            .filter(sn -> !sn.trim().isEmpty())
            .distinct()
            .collect(Collectors.toList());
        
        if (validDeviceSnList.isEmpty()) {
            log.warn("告警查询过滤后设备序列号列表为空,返回默认告警信息");
            return createEmptyTAlertInfo();
        }
        
        // 3. 查询告警信息 - 使用过滤后的安全设备列表
        LambdaQueryWrapper<TAlertInfo> queryWrapper = new LambdaQueryWrapper<TAlertInfo>()
            .in(TAlertInfo::getDeviceSn, validDeviceSnList)
            .orderByDesc(TAlertInfo::getCreateTime); // 按时间倒序
            
        List<TAlertInfo> alerts = alertInfoService.list(queryWrapper);
        
        // 4. 统计各类计数
        Map<String, Integer> statusCounts = new HashMap<>();
        Map<String, Integer> typeCounts = new HashMap<>();
        Map<String, Integer> severityCounts = new HashMap<>();
        
        // 5. 获取设备用户信息映射
        Set<String> deviceSns = alerts.stream()
            .map(TAlertInfo::getDeviceSn)
            .collect(Collectors.toSet());
        Map<String, IDeviceUserMappingService.UserInfo> deviceUserMap = 
            deviceUserMappingService.getDeviceUserInfo(deviceSns);
        
        // 6. 转换并统计告警信息
        List<OrgStatisticsVO.AlertDetailVO> alertVOs = alerts.stream()
            .map(alert -> {
                OrgStatisticsVO.AlertDetailVO vo = new OrgStatisticsVO.AlertDetailVO();
                BeanUtils.copyProperties(alert, vo);
                
                // 添加用户信息
                IDeviceUserMappingService.UserInfo userInfo = deviceUserMap.get(alert.getDeviceSn());
                if (userInfo != null) {
                    vo.setUserName(userInfo.getUserName());
                }
                
                // 统计 - 处理null值,避免JSON序列化错误
                String alertStatus = alert.getAlertStatus() != null ? alert.getAlertStatus() : "UNKNOWN";
                String alertType = alert.getAlertType() != null ? alert.getAlertType() : "UNKNOWN";  
                String severityLevel = alert.getSeverityLevel() != null ? alert.getSeverityLevel() : "UNKNOWN";
                
                statusCounts.merge(alertStatus, 1, Integer::sum);
                typeCounts.merge(alertType, 1, Integer::sum);
                severityCounts.merge(severityLevel, 1, Integer::sum);
                
                return vo;
            })
            .collect(Collectors.toList());
        
        // 7. 设置统计结果
        alertInfo.setAlerts(alertVOs);
        alertInfo.setAlertStatusCounts(statusCounts);
        alertInfo.setAlertTypeCounts(typeCounts);
        alertInfo.setSeverityLevelCounts(severityCounts);
        alertInfo.setTotalAlerts(alerts.size());
        alertInfo.setUniqueAlertTypes(typeCounts.size());
        
        return alertInfo;
    }
    
    private OrgStatisticsVO.AlertInfoVO createEmptyTAlertInfo() {
        OrgStatisticsVO.AlertInfoVO emptyInfo = new OrgStatisticsVO.AlertInfoVO();
        emptyInfo.setAlerts(new ArrayList<>());
        emptyInfo.setAlertStatusCounts(new HashMap<>());
        emptyInfo.setAlertTypeCounts(new HashMap<>());
        emptyInfo.setSeverityLevelCounts(new HashMap<>());
        emptyInfo.setTotalAlerts(0);
        emptyInfo.setUniqueAlertTypes(0);
        return emptyInfo;
    }
    
    private OrgStatisticsVO.DeviceInfoVO getDeviceInfo(List<String> deviceSnList) {
        OrgStatisticsVO.DeviceInfoVO deviceInfo = new OrgStatisticsVO.DeviceInfoVO();

        // 🔧 修复: 检查设备列表是否为空,避免SQL语法错误
        if (deviceSnList == null || deviceSnList.isEmpty()) {
            log.warn("设备序列号列表为空,返回默认设备信息");
            return createEmptyDeviceInfo();
        }
        
        // 🔧 修复: 过滤无效的设备序列号
        List<String> validDeviceSnList = deviceSnList.stream()
            .filter(Objects::nonNull)
            .filter(sn -> !sn.trim().isEmpty())
            .distinct()
            .collect(Collectors.toList());
        
        if (validDeviceSnList.isEmpty()) {
            log.warn("过滤后设备序列号列表为空,返回默认设备信息");
            return createEmptyDeviceInfo();
        }
        
        // 获取设备列表 - 现在安全了
        List<TDeviceInfo> devices = deviceInfoService.list(new LambdaQueryWrapper<TDeviceInfo>()
            .in(TDeviceInfo::getSerialNumber, validDeviceSnList));
        
        if (devices.isEmpty()) {
            return createEmptyDeviceInfo();
        }
        
        // 统计各类计数
        Map<String, Integer> chargingCounts = new HashMap<>();
        Map<String, Integer> osCounts = new HashMap<>();
        Map<String, Integer> statusCounts = new HashMap<>();
        Map<String, Integer> wearableCounts = new HashMap<>();
        
        // 转换并统计设备信息
        List<OrgStatisticsVO.DeviceDetailVO> deviceVOs = devices.stream()
            .map(device -> {
                OrgStatisticsVO.DeviceDetailVO vo = new OrgStatisticsVO.DeviceDetailVO();
                vo.setChargingStatus(device.getChargingStatus());
                vo.setSerialNumber(device.getSerialNumber());
                vo.setStatus(device.getStatus());
                vo.setSystemSoftwareVersion(device.getSystemSoftwareVersion());
                vo.setWearableStatus(device.getWearableStatus());
                
                // 统计 - 处理null值,避免JSON序列化错误
                String chargingStatus = device.getChargingStatus() != null ? device.getChargingStatus() : "UNKNOWN";
                String systemVersion = device.getSystemSoftwareVersion() != null ? device.getSystemSoftwareVersion() : "UNKNOWN";
                String status = device.getStatus() != null ? device.getStatus() : "UNKNOWN";
                String wearableStatus = device.getWearableStatus() != null ? device.getWearableStatus() : "UNKNOWN";
                
                chargingCounts.merge(chargingStatus, 1, Integer::sum);
                osCounts.merge(systemVersion, 1, Integer::sum);
                statusCounts.merge(status, 1, Integer::sum);
                wearableCounts.merge(wearableStatus, 1, Integer::sum);
                
                return vo;
            })
            .collect(Collectors.toList());
        
        deviceInfo.setDevices(deviceVOs);
        deviceInfo.setDeviceChargingCounts(chargingCounts);
        deviceInfo.setDeviceOsCounts(osCounts);
        deviceInfo.setDeviceStatusCounts(statusCounts);
        deviceInfo.setDeviceWearableCounts(wearableCounts);
        deviceInfo.setSuccess(true);
        deviceInfo.setTotalDevices(devices.size());
        
        return deviceInfo;
    }
    
    private OrgStatisticsVO.DeviceInfoVO createEmptyDeviceInfo() {
        OrgStatisticsVO.DeviceInfoVO emptyInfo = new OrgStatisticsVO.DeviceInfoVO();
        emptyInfo.setDevices(new ArrayList<>());
        emptyInfo.setDeviceChargingCounts(new HashMap<>());
        emptyInfo.setDeviceOsCounts(new HashMap<>());
        emptyInfo.setDeviceStatusCounts(new HashMap<>());
        emptyInfo.setDeviceWearableCounts(new HashMap<>());
        emptyInfo.setSuccess(true);
        emptyInfo.setTotalDevices(0);
        return emptyInfo;
    }
    
    private Map<String, OrgStatisticsVO.HealthDataVO> getHealthData(List<String> deviceSnList) {
        Map<String, OrgStatisticsVO.HealthDataVO> healthDataMap = new HashMap<>();
        
        if (deviceSnList.isEmpty()) {
            return healthDataMap;
        }
        
        deviceSnList.forEach(deviceSn -> {
            // 获取最新健康数据
            TUserHealthData latestData = healthDataService.getOne(
                new LambdaQueryWrapper<TUserHealthData>()
                    .eq(TUserHealthData::getDeviceSn, deviceSn)
                    .orderByDesc(TUserHealthData::getCreateTime)
                    .last("LIMIT 1")
            );
            
            OrgStatisticsVO.HealthDataVO vo = new OrgStatisticsVO.HealthDataVO();
            if (latestData != null) {
                BeanUtils.copyProperties(latestData, vo);
            }
            healthDataMap.put(deviceSn, vo);
        });
        
        return healthDataMap;
    }
    
    private OrgStatisticsVO.MessageInfoVO getMessageInfo(String orgId) {
        OrgStatisticsVO.MessageInfoVO messageInfo = new OrgStatisticsVO.MessageInfoVO();
        
        // 🔧 修复：使用设备序列号过滤，排除管理员消息 #管理员消息过滤
        List<String> deviceSnList = deviceUserMappingService.getDeviceSnListByDepartmentId(orgId);
        log.info("📨 消息查询 - 部门ID: {}, 获取到设备数量: {}", orgId, deviceSnList.size());
        
        if (deviceSnList.isEmpty()) {
            log.warn("📨 部门{}下无设备，返回空消息列表", orgId);
            return createEmptyMessageInfo();
        }
        
        // 过滤无效设备序列号
        List<String> validDeviceSnList = deviceSnList.stream()
            .filter(Objects::nonNull)
            .filter(sn -> !sn.trim().isEmpty())
            .filter(sn -> !"-".equals(sn.trim())) // 过滤无效设备号
            .distinct()
            .collect(Collectors.toList());
            
        if (validDeviceSnList.isEmpty()) {
            log.warn("📨 部门{}下无有效设备，返回空消息列表", orgId);
            return createEmptyMessageInfo();
        }
        
        log.info("📨 有效设备列表: {}", validDeviceSnList);
        
        // 🔥 关键修复：按设备序列号查询消息，自动排除管理员设备消息
        List<TDeviceMessage> messages = messageService.list(
            new LambdaQueryWrapper<TDeviceMessage>()
                .in(TDeviceMessage::getDeviceSn, validDeviceSnList) // 改为按设备序列号查询
                .orderByDesc(TDeviceMessage::getCreateTime)
        );
        
        log.info("📨 查询到消息数量: {}", messages.size());
        
        // 统计各类计数
        Map<String, Integer> statusCounts = new HashMap<>();
        Map<String, Integer> typeCounts = new HashMap<>();
        
        // 转换并统计消息信息
        List<OrgStatisticsVO.MessageDetailVO> messageVOs = messages.stream()
            .map(message -> {
                OrgStatisticsVO.MessageDetailVO vo = new OrgStatisticsVO.MessageDetailVO();
                vo.setDeviceSn(message.getDeviceSn());
                vo.setId(message.getId());
                vo.setMessage(message.getMessage());
                vo.setMessageStatus(message.getMessageStatus());
                vo.setMessageType(message.getMessageType());
                vo.setReceivedTime(message.getReceivedTime());
                vo.setSentTime(message.getSentTime());
                
                // 统计 - 处理null值,避免JSON序列化错误
                String messageStatus = message.getMessageStatus() != null ? message.getMessageStatus() : "UNKNOWN";
                String messageType = message.getMessageType() != null ? message.getMessageType() : "UNKNOWN";
                
                statusCounts.merge(messageStatus, 1, Integer::sum);
                typeCounts.merge(messageType, 1, Integer::sum);
                
                return vo;
            })
            .collect(Collectors.toList());
        
        messageInfo.setMessages(messageVOs);
        messageInfo.setMessageStatusCounts(statusCounts);
        messageInfo.setMessageTypeCounts(typeCounts);
        messageInfo.setSuccess(true);
        messageInfo.setTotalMessages(messages.size());
        messageInfo.setUniqueMessageTypes(typeCounts.size());
        
        return messageInfo;
    }
    
    private OrgStatisticsVO.MessageInfoVO createEmptyMessageInfo() {
        OrgStatisticsVO.MessageInfoVO emptyInfo = new OrgStatisticsVO.MessageInfoVO();
        emptyInfo.setMessages(new ArrayList<>());
        emptyInfo.setMessageStatusCounts(new HashMap<>());
        emptyInfo.setMessageTypeCounts(new HashMap<>());
        emptyInfo.setSuccess(true);
        emptyInfo.setTotalMessages(0);
        emptyInfo.setUniqueMessageTypes(0);
        return emptyInfo;
    }

    public OrgStatisticsVO.UserInfoVO queryUserInfoWithOrgId(Long orgId) {
        OrgStatisticsVO.UserInfoVO userInfo = new OrgStatisticsVO.UserInfoVO();
        
        // 1. 获取所有子部门ID
        List<SysOrgUnits> descendants = sysOrgUnitsService.listAllDescendants(Collections.singletonList(orgId));
        List<Long> orgIds = new ArrayList<>();
        orgIds.add(orgId);
        orgIds.addAll(descendants.stream()
            .map(SysOrgUnits::getId)
            .collect(Collectors.toList()));

        // 2. 从sys_user_org获取所有用户ID
        List<Long> userIds = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .in(SysUserOrg::getOrgId, orgIds))
            .stream()
            .map(SysUserOrg::getUserId)
            .distinct()
            .collect(Collectors.toList());

        if (userIds.isEmpty()) {
            return createEmptyUserInfo();
        }

        // 3. 获取用户信息（排除管理员）
        List<SysUser> allUsers = sysUserService.list(new LambdaQueryWrapper<SysUser>()
            .in(SysUser::getId, userIds));
        
        // 3.1 过滤掉管理员用户
        List<SysUser> users = allUsers.stream()
            .filter(user -> !sysUserService.isAdminUser(user.getId()))
            .collect(Collectors.toList());

        // 4. 创建部门ID到名称的映射
        Map<Long, String> orgNameMap = sysOrgUnitsService.listByIds(orgIds)
            .stream()
            .collect(Collectors.toMap(
                SysOrgUnits::getId,
                SysOrgUnits::getName,
                (k1, k2) -> k1
            ));

        // 5. 获取用户所属部门信息
        Map<Long, Long> userOrgMap = sysUserOrgService.list(new LambdaQueryWrapper<SysUserOrg>()
            .in(SysUserOrg::getUserId, userIds))
            .stream()
            .collect(Collectors.toMap(
                SysUserOrg::getUserId,
                SysUserOrg::getOrgId,
                (k1, k2) -> k1
            ));

        // 6. 统计信息
        Map<String, Integer> deviceBindCounts = new HashMap<>();
        Map<String, Integer> userStatusCounts = new HashMap<>();

        // 7. 转换为UserDetailVO
        List<OrgStatisticsVO.UserDetailVO> userDetails = users.stream()
            .map(user -> {
                OrgStatisticsVO.UserDetailVO vo = new OrgStatisticsVO.UserDetailVO();
                vo.setUserId(user.getId());
                vo.setUserName(user.getUserName());
                vo.setPhone(user.getPhone());
                vo.setDeviceSn(user.getDeviceSn());
                vo.setStatus(user.getStatus());
                vo.setBindStatus(StringUtils.hasText(user.getDeviceSn()) ? "BOUND" : "UNBOUND");
                
                // 设置部门信息
                Long userOrgId = userOrgMap.get(user.getId());
                if (userOrgId != null) {
                    vo.setOrgId(userOrgId);
                    vo.setOrgName(orgNameMap.get(userOrgId));
                }
                
                // 统计 - 处理null值,避免JSON序列化错误
                String bindStatus = vo.getBindStatus() != null ? vo.getBindStatus() : "UNKNOWN";
                String userStatus = vo.getStatus() != null ? vo.getStatus() : "UNKNOWN";
                
                deviceBindCounts.merge(bindStatus, 1, Integer::sum);
                userStatusCounts.merge(userStatus, 1, Integer::sum);
                
                return vo;
            })
            .collect(Collectors.toList());

        // 8. 设置返回结果
        userInfo.setUsers(userDetails);
        userInfo.setDeviceBindCounts(deviceBindCounts);
        userInfo.setUserStatusCounts(userStatusCounts);
        userInfo.setTotalUsers(userDetails.size());
        userInfo.setSuccess(true);
        
        return userInfo;
    }


    private OrgStatisticsVO.UserInfoVO createEmptyUserInfo() {
        OrgStatisticsVO.UserInfoVO emptyInfo = new OrgStatisticsVO.UserInfoVO();
        emptyInfo.setUsers(new ArrayList<>());
        emptyInfo.setDeviceBindCounts(new HashMap<>());
        emptyInfo.setUserStatusCounts(new HashMap<>());
        emptyInfo.setTotalUsers(0);
        emptyInfo.setSuccess(true);
        return emptyInfo;
    }


} 