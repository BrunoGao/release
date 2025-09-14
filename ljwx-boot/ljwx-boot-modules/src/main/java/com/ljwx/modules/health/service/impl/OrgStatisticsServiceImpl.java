package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.ljwx.modules.health.domain.entity.TAlertInfo;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.OrgStatisticsVO;
import com.ljwx.modules.health.service.ITDeviceInfoService;
import com.ljwx.modules.health.service.ITAlertInfoService;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import com.ljwx.modules.health.service.ITUserHealthDataService;
import com.ljwx.modules.health.service.IOrgStatisticsService;
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
    private ITAlertInfoService alertInfoService;
    
    @Autowired
    private ISysUserOrgService sysUserOrgService;
    
    @Override
    public OrgStatisticsVO getOrgStatistics(String orgId) {
        OrgStatisticsVO statistics = new OrgStatisticsVO();
        
        Long orgIdLong = Long.parseLong(orgId);
        
        // 1. 获取并设置用户信息 
        statistics.setUserInfo(queryUserInfoWithOrgId(orgIdLong));
        
        // 2. 获取并设置告警信息 - 直接使用orgId查询
        statistics.setAlertInfo(getTAlertInfo(orgIdLong));
        
        // 3. 获取并设置设备信息 - 直接使用orgId查询
        statistics.setDeviceInfo(getDeviceInfo(orgIdLong));
        
        // 4. 获取并设置健康数据 - 直接使用orgId查询
        statistics.setHealthData(getHealthData(orgIdLong));
        
        // 5. 获取并设置消息信息 - 直接使用orgId查询
        statistics.setMessageInfo(getMessageInfo(orgIdLong));
        
        return statistics;
    }
    
    @Override
    public OrgStatisticsVO getOrgStatisticsByOrgId(String orgId) {
        log.info("🏢 根据orgId获取组织统计信息: {}", orgId);
    
        
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
    
    private OrgStatisticsVO.AlertInfoVO getTAlertInfo(Long orgId) {
        OrgStatisticsVO.AlertInfoVO alertInfo = new OrgStatisticsVO.AlertInfoVO();
        
        log.info("⚠️ 告警查询 - 部门ID: {}", orgId);
        
        // 1. 直接根据orgId查询t_alert_info
        List<TAlertInfo> alerts = alertInfoService.list(new LambdaQueryWrapper<TAlertInfo>()
            .eq(TAlertInfo::getOrgId, orgId) // 直接按orgId查询
            .orderByDesc(TAlertInfo::getCreateTime)); // 按时间倒序
        
        log.info("⚠️ 查询到告警数量: {}", alerts.size());
        
        if (alerts.isEmpty()) {
            log.warn("⚠️ 部门{}下无告警，返回空告警列表", orgId);
            return createEmptyTAlertInfo();
        }
        
        // 2. 获取设备序列号集合，以便查询用户信息
        Set<String> deviceSns = alerts.stream()
            .map(TAlertInfo::getDeviceSn)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        
        // 3. 查询用户信息（直接使用sysUserService）
        final Map<String, String> deviceUserNameMap;
        if (!deviceSns.isEmpty()) {
            List<SysUser> users = sysUserService.list(new LambdaQueryWrapper<SysUser>()
                .in(SysUser::getDeviceSn, deviceSns));
            deviceUserNameMap = users.stream()
                .filter(user -> user.getDeviceSn() != null)
                .collect(Collectors.toMap(
                    SysUser::getDeviceSn,
                    SysUser::getUserName,
                    (k1, k2) -> k1
                ));
        } else {
            deviceUserNameMap = new HashMap<>();
        }
        
        // 4. 统计各类计数 - 在lambda外部进行
        Map<String, Integer> statusCounts = new HashMap<>();
        Map<String, Integer> typeCounts = new HashMap<>(); 
        Map<String, Integer> severityCounts = new HashMap<>();
        
        // 5. 转换告警信息
        List<OrgStatisticsVO.AlertDetailVO> alertVOs = alerts.stream()
            .map(alert -> {
                OrgStatisticsVO.AlertDetailVO vo = new OrgStatisticsVO.AlertDetailVO();
                BeanUtils.copyProperties(alert, vo);
                
                // 添加用户信息
                String userName = deviceUserNameMap.get(alert.getDeviceSn());
                if (userName != null) {
                    vo.setUserName(userName);
                }
                
                return vo;
            })
            .collect(Collectors.toList());
            
        // 6. 统计处理 - 在lambda外部进行
        for (TAlertInfo alert : alerts) {
            String alertStatus = alert.getAlertStatus() != null ? alert.getAlertStatus() : "UNKNOWN";
            String alertType = alert.getAlertType() != null ? alert.getAlertType() : "UNKNOWN";
            String severityLevel = alert.getSeverityLevel() != null ? alert.getSeverityLevel() : "UNKNOWN";
            
            statusCounts.merge(alertStatus, 1, Integer::sum);
            typeCounts.merge(alertType, 1, Integer::sum);
            severityCounts.merge(severityLevel, 1, Integer::sum);
        }
        
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
    
    private OrgStatisticsVO.DeviceInfoVO getDeviceInfo(Long orgId) {
        OrgStatisticsVO.DeviceInfoVO deviceInfo = new OrgStatisticsVO.DeviceInfoVO();

        log.info("📱 设备查询 - 部门ID: {}", orgId);
        
        // 1. 直接根据orgId查询t_device_info
        List<TDeviceInfo> devices = deviceInfoService.list(new LambdaQueryWrapper<TDeviceInfo>()
            .eq(TDeviceInfo::getOrgId, orgId)); // 直接按orgId查询
        
        log.info("📱 查询到设备数量: {}", devices.size());
        
        if (devices.isEmpty()) {
            log.warn("📱 部门{}下无设备，返回空设备列表", orgId);
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
    
    private Map<String, OrgStatisticsVO.HealthDataVO> getHealthData(Long orgId) {
        Map<String, OrgStatisticsVO.HealthDataVO> healthDataMap = new HashMap<>();
        
        log.info("📊 健康数据查询 - 部门ID: {}", orgId);
        
        // 1. 直接根据orgId查询t_user_health_data
        List<TUserHealthData> healthDataList = healthDataService.list(
            new LambdaQueryWrapper<TUserHealthData>()
                .eq(TUserHealthData::getOrgId, orgId) // 直接按orgId查询
                .orderByDesc(TUserHealthData::getCreateTime)
        );
        
        log.info("📊 查询到健康数据数量: {}", healthDataList.size());
        
        if (healthDataList.isEmpty()) {
            log.warn("📊 部门{}下无健康数据，返回空列表", orgId);
            return healthDataMap;
        }
        
        // 2. 按userId分组，只保留最新的数据
        Map<Long, TUserHealthData> latestDataByUser = healthDataList.stream()
            .collect(Collectors.toMap(
                TUserHealthData::getUserId,
                data -> data,
                (existing, replacement) -> existing.getCreateTime().isAfter(replacement.getCreateTime()) ? existing : replacement
            ));
        
        // 3. 转换为 HealthDataVO
        latestDataByUser.forEach((userId, latestData) -> {
            OrgStatisticsVO.HealthDataVO vo = new OrgStatisticsVO.HealthDataVO();
            BeanUtils.copyProperties(latestData, vo);
            healthDataMap.put(String.valueOf(userId), vo); // 使用userId作为key
        });
        
        log.info("📊 最终健康数据数量: {}", healthDataMap.size());
        
        return healthDataMap;
    }
    
    private OrgStatisticsVO.MessageInfoVO getMessageInfo(Long orgId) {
        OrgStatisticsVO.MessageInfoVO messageInfo = new OrgStatisticsVO.MessageInfoVO();
        
        log.info("📨 消息查询 - 部门ID: {}", orgId);
        
        // 1. 直接根据orgId查询t_device_message
        List<TDeviceMessage> messages = messageService.list(
            new LambdaQueryWrapper<TDeviceMessage>()
                .eq(TDeviceMessage::getOrgId, orgId) // 直接按orgId查询
                .orderByDesc(TDeviceMessage::getCreateTime)
        );
        
        log.info("📨 查询到消息数量: {}", messages.size());
        
        if (messages.isEmpty()) {
            log.warn("📨 部门{}下无消息，返回空消息列表", orgId);
            return createEmptyMessageInfo();
        }
        
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