/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0 (the "License").
 */

package com.ljwx.modules.health.facade.impl;

import com.ljwx.modules.health.facade.IBigscreenAlertFacade;
import com.ljwx.modules.health.domain.dto.v1.alert.*;
import com.ljwx.modules.health.domain.vo.v1.alert.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class BigscreenAlertFacadeImpl implements IBigscreenAlertFacade {

    @Override
    public List<UserAlertVO> getUserAlerts(UserAlertQueryDTO query) {
        log.info("Getting user alerts for query: {}", query);
        
        List<UserAlertVO> alerts = new ArrayList<>();
        alerts.add(UserAlertVO.builder()
                .alertId("1")
                .userId(query.getUserId())
                .alertType("heart_rate")
                .message("心率异常")
                .status(query.getStatus())
                .timestamp(LocalDateTime.now())
                .build());
        
        return alerts;
    }

    @Override
    public List<PersonalAlertVO> getPersonalAlerts(PersonalAlertQueryDTO query) {
        log.info("Getting personal alerts for query: {}", query);
        
        List<PersonalAlertVO> alerts = new ArrayList<>();
        alerts.add(PersonalAlertVO.builder()
                .alertId("1")
                .deviceSn(query.getDeviceSn())
                .userId(query.getUserId())
                .alertType("device_offline")
                .message("设备离线")
                .timestamp(LocalDateTime.now())
                .build());
        
        return alerts;
    }

    @Override
    public boolean acknowledgeAlert(AlertAcknowledgeRequestDTO request) {
        log.info("Acknowledging alert for request: {}", request);
        
        // 临时实现 - 返回成功
        return true;
    }

    @Override
    public boolean dealAlert(Long alertId) {
        log.info("Dealing with alert id: {}", alertId);
        
        // 临时实现 - 返回成功
        return true;
    }

    @Override
    public List<UserMessageVO> getUserMessages(UserMessageQueryDTO query) {
        log.info("Getting user messages for query: {}", query);
        
        List<UserMessageVO> messages = new ArrayList<>();
        messages.add(UserMessageVO.builder()
                .messageId("1")
                .userId(query.getUserId())
                .messageType(query.getMessageType())
                .title("系统通知")
                .content("测试消息内容")
                .timestamp(LocalDateTime.now())
                .build());
        
        return messages;
    }
}