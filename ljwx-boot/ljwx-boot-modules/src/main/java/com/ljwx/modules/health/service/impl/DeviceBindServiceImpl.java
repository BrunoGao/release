/*
* All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
* Open Source Agreement: Apache License, Version 2.0
*/

package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ljwx.modules.health.domain.dto.device.bind.BatchApproveBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.CheckDeviceBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.SubmitBindingApplicationDTO;
import com.ljwx.modules.health.domain.entity.TDeviceBindRequest;
import com.ljwx.modules.health.domain.entity.TDeviceInfo;
import com.ljwx.modules.health.domain.entity.TDeviceUser;
import com.ljwx.modules.health.repository.mapper.TDeviceBindRequestMapper;
import com.ljwx.modules.health.repository.mapper.TDeviceInfoMapper;
import com.ljwx.modules.health.repository.mapper.TDeviceUserMapper;
import com.ljwx.modules.health.service.DeviceBindService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;

/**
* 设备绑定服务实现类
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.service.impl.DeviceBindServiceImpl
* @CreateTime 2025-08-23
*/

@Slf4j
@Service
@RequiredArgsConstructor
public class DeviceBindServiceImpl implements DeviceBindService {

    private final TDeviceBindRequestMapper deviceBindRequestMapper;
    private final TDeviceInfoMapper deviceInfoMapper;
    private final TDeviceUserMapper deviceUserMapper;

    @Override
    public Map<String, Object> checkDeviceBinding(CheckDeviceBindingDTO dto) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("检查设备绑定状态 - 设备序列号: {}, 手机号: {}", dto.getSerialNumber(), dto.getPhoneNumber());
            
            // 1. 查询设备信息
            QueryWrapper<TDeviceInfo> deviceQuery = new QueryWrapper<>();
            deviceQuery.eq("device_sn", dto.getSerialNumber())
                       .eq("is_deleted", 0);
            TDeviceInfo deviceInfo = deviceInfoMapper.selectOne(deviceQuery);
            
            if (deviceInfo == null) {
                result.put("success", false);
                result.put("error", "设备不存在");
                result.put("exists", false);
                return result;
            }
            
            // 2. 检查是否已绑定
            QueryWrapper<TDeviceUser> userQuery = new QueryWrapper<>();
            userQuery.eq("device_sn", dto.getSerialNumber())
                     .eq("status", "BIND")
                     .eq("is_deleted", 0);
            TDeviceUser deviceUser = deviceUserMapper.selectOne(userQuery);
            
            if (deviceUser != null) {
                result.put("success", true);
                result.put("exists", true);
                result.put("bound", true);
                result.put("user_id", deviceUser.getUserId());
                log.info("设备已绑定给用户: {}", deviceUser.getUserId());
                return result;
            }
            
            // 3. 检查是否有待审批申请
            QueryWrapper<TDeviceBindRequest> requestQuery = new QueryWrapper<>();
            requestQuery.eq("device_sn", dto.getSerialNumber())
                        .eq("status", "PENDING")
                        .eq("is_deleted", 0);
            TDeviceBindRequest pendingRequest = deviceBindRequestMapper.selectOne(requestQuery);
            
            result.put("success", true);
            result.put("exists", pendingRequest != null);
            result.put("bound", false);
            result.put("pending", pendingRequest != null);
            
            if (pendingRequest != null) {
                log.info("设备有待审批申请: {}", pendingRequest.getId());
            } else {
                log.info("设备未绑定且无待审批申请");
            }
            
        } catch (Exception e) {
            log.error("检查设备绑定状态失败", e);
            result.put("success", false);
            result.put("error", "查询失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    @Transactional
    public Map<String, Object> submitBindingApplication(SubmitBindingApplicationDTO dto) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("提交设备绑定申请 - 设备序列号: {}, 用户ID: {}, 手机号: {}", 
                    dto.getDeviceSn(), dto.getUserId(), dto.getPhoneNumber());
            
            // 1. 检查是否已有待审批申请
            QueryWrapper<TDeviceBindRequest> existingQuery = new QueryWrapper<>();
            existingQuery.eq("device_sn", dto.getDeviceSn())
                        .eq("status", "PENDING")
                        .eq("is_deleted", 0);
            TDeviceBindRequest existing = deviceBindRequestMapper.selectOne(existingQuery);
            
            if (existing != null) {
                result.put("success", false);
                result.put("error", "已有待审批申请，请等待处理");
                return result;
            }
            
            // 2. 创建新申请
            TDeviceBindRequest request = TDeviceBindRequest.builder()
                    .deviceSn(dto.getDeviceSn())
                    .userId(dto.getUserId())
                    .phoneNumber(dto.getPhoneNumber())
                    .applyTime(LocalDateTime.now())
                    .status("PENDING")
                    .isDeleted(0)
                    .build();
            
            int insertResult = deviceBindRequestMapper.insert(request);
            
            if (insertResult > 0) {
                result.put("success", true);
                result.put("message", "申请提交成功");
                result.put("request_id", request.getId());
                log.info("绑定申请提交成功，申请ID: {}", request.getId());
            } else {
                result.put("success", false);
                result.put("error", "提交申请失败");
            }
            
        } catch (Exception e) {
            log.error("提交设备绑定申请失败", e);
            result.put("success", false);
            result.put("error", "提交失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    @Transactional
    public Map<String, Object> batchApprove(BatchApproveBindingDTO dto) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("批量审批绑定申请 - 操作: {}, 申请数量: {}", dto.getAction(), dto.getIds().size());
            
            List<String> successIds = new ArrayList<>();
            List<String> failedIds = new ArrayList<>();
            
            for (String requestId : dto.getIds()) {
                try {
                    // 查询申请记录
                    TDeviceBindRequest request = deviceBindRequestMapper.selectById(requestId);
                    if (request == null || !"PENDING".equals(request.getStatus())) {
                        failedIds.add(requestId);
                        continue;
                    }
                    
                    // 更新申请状态
                    request.setStatus(dto.getAction());
                    request.setApproveTime(LocalDateTime.now());
                    request.setApproverId(dto.getApproverId());
                    request.setComment(dto.getComment());
                    
                    deviceBindRequestMapper.updateById(request);
                    
                    // 如果是通过，创建绑定关系
                    if ("APPROVED".equals(dto.getAction())) {
                        TDeviceUser deviceUser = TDeviceUser.builder()
                                .deviceSn(request.getDeviceSn())
                                .userId(request.getUserId())
                                .userName(request.getUserName())
                                .operateTime(LocalDateTime.now())
                                .status("BIND")
                                .isDeleted(0)
                                .build();
                        
                        deviceUserMapper.insert(deviceUser);
                        log.info("创建设备绑定关系 - 设备: {}, 用户: {}", request.getDeviceSn(), request.getUserId());
                    }
                    
                    successIds.add(requestId);
                    
                } catch (Exception e) {
                    log.error("处理申请失败，申请ID: {}", requestId, e);
                    failedIds.add(requestId);
                }
            }
            
            result.put("success", true);
            result.put("message", String.format("处理完成 - 成功: %d, 失败: %d", 
                    successIds.size(), failedIds.size()));
            result.put("success_ids", successIds);
            result.put("failed_ids", failedIds);
            
            log.info("批量审批完成 - 成功: {}, 失败: {}", successIds.size(), failedIds.size());
            
        } catch (Exception e) {
            log.error("批量审批绑定申请失败", e);
            result.put("success", false);
            result.put("error", "批量审批失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getBindingApplications(String status, Integer pageNum, Integer pageSize) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            Page<TDeviceBindRequest> page = new Page<>(
                    pageNum != null ? pageNum : 1, 
                    pageSize != null ? pageSize : 10
            );
            
            QueryWrapper<TDeviceBindRequest> query = new QueryWrapper<>();
            query.eq("is_deleted", 0);
            if (status != null && !status.isEmpty()) {
                query.eq("status", status);
            }
            query.orderByDesc("apply_time");
            
            IPage<TDeviceBindRequest> pageResult = deviceBindRequestMapper.selectPage(page, query);
            
            result.put("success", true);
            result.put("data", Map.of(
                    "items", pageResult.getRecords(),
                    "total", pageResult.getTotal(),
                    "page", pageResult.getCurrent(),
                    "size", pageResult.getSize(),
                    "pages", pageResult.getPages()
            ));
            
            log.info("获取绑定申请列表 - 状态: {}, 总数: {}", status, pageResult.getTotal());
            
        } catch (Exception e) {
            log.error("获取绑定申请列表失败", e);
            result.put("success", false);
            result.put("error", "获取申请列表失败: " + e.getMessage());
        }
        
        return result;
    }

    @Override
    public Map<String, Object> getUserBindings(String userId) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            QueryWrapper<TDeviceUser> query = new QueryWrapper<>();
            query.eq("user_id", userId)
                 .eq("status", "BIND")
                 .eq("is_deleted", 0);
            
            List<TDeviceUser> bindings = deviceUserMapper.selectList(query);
            
            result.put("success", true);
            result.put("data", bindings);
            
            log.info("获取用户绑定设备列表 - 用户ID: {}, 绑定数量: {}", userId, bindings.size());
            
        } catch (Exception e) {
            log.error("获取用户绑定设备失败", e);
            result.put("success", false);
            result.put("error", "获取绑定设备失败: " + e.getMessage());
        }
        
        return result;
    }
}