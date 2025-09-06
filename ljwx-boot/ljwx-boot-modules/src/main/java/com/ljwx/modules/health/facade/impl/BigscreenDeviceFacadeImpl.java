/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.facade.impl;

import com.ljwx.modules.health.facade.IBigscreenDeviceFacade;
import com.ljwx.modules.health.domain.dto.v1.device.*;
import com.ljwx.modules.health.domain.vo.v1.device.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class BigscreenDeviceFacadeImpl implements IBigscreenDeviceFacade {

    @Override
    public DeviceUserInfoVO getDeviceUserInfo(String deviceSn) {
        log.info("Getting device user info for deviceSn: {}", deviceSn);
        
        return DeviceUserInfoVO.builder()
                .userId("123")
                .userName("测试用户")
                .deviceSn(deviceSn)
                .bindTime(LocalDateTime.now())
                .build();
    }

    @Override
    public DeviceStatusVO getDeviceStatus(String deviceSn) {
        log.info("Getting device status for deviceSn: {}", deviceSn);
        
        return DeviceStatusVO.builder()
                .deviceSn(deviceSn)
                .status("online")
                .batteryLevel(80)
                .lastSync(LocalDateTime.now())
                .build();
    }

    @Override
    public DeviceUserOrganizationVO getDeviceUserOrganization(String deviceSn) {
        log.info("Getting device user organization for deviceSn: {}", deviceSn);
        
        return DeviceUserOrganizationVO.builder()
                .deviceSn(deviceSn)
                .userId("123")
                .orgId("org001")
                .orgName("测试组织")
                .build();
    }

    @Override
    public UserProfileVO getUserProfile(String userId) {
        log.info("Getting user profile for userId: {}", userId);
        
        return UserProfileVO.builder()
                .userId(userId)
                .username("testuser")
                .realName("测试用户")
                .email("test@example.com")
                .build();
    }

    @Override
    public List<UserVO> getUsers(UserQueryDTO query) {
        log.info("Getting users for query: {}", query);
        
        List<UserVO> users = new ArrayList<>();
        users.add(UserVO.builder()
                .userId("123")
                .username("user1")
                .realName("用户1")
                .orgId(query.getOrgId())
                .build());
        
        return users;
    }
}