/*
* All Rights Reserved: Copyright [2024] [Zhuang Pan (brunoGao@gmail.com)]
* Open Source Agreement: Apache License, Version 2.0
*/

package com.ljwx.admin.controller.health;

import com.ljwx.modules.health.domain.dto.device.bind.BatchApproveBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.CheckDeviceBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.SubmitBindingApplicationDTO;
import com.ljwx.modules.health.service.DeviceBindService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.Map;

/**
* 设备绑定管理 REST 控制器
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.admin.controller.health.DeviceBindController
* @CreateTime 2025-08-23
*/

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/device")
@Tag(name = "设备绑定管理", description = "设备绑定申请与审批管理接口")
public class DeviceBindController {

    private final DeviceBindService deviceBindService;

    @PostMapping("/check_binding")
    @Operation(summary = "检查设备绑定状态", description = "检查指定设备是否已绑定或有待审批申请")
    public Map<String, Object> checkDeviceBinding(@Valid @RequestBody CheckDeviceBindingDTO dto) {
        log.info("接收到检查设备绑定状态请求: {}", dto);
        return deviceBindService.checkDeviceBinding(dto);
    }

    @PostMapping("/binding_application")
    @Operation(summary = "提交设备绑定申请", description = "用户提交设备绑定申请")
    public Map<String, Object> submitBindingApplication(@Valid @RequestBody SubmitBindingApplicationDTO dto) {
        log.info("接收到提交设备绑定申请请求: {}", dto);
        return deviceBindService.submitBindingApplication(dto);
    }

    @PostMapping("/batch_approve")
    @Operation(summary = "批量审批绑定申请", description = "管理员批量审批设备绑定申请")
    public Map<String, Object> batchApprove(@Valid @RequestBody BatchApproveBindingDTO dto) {
        log.info("接收到批量审批绑定申请请求: {}", dto);
        return deviceBindService.batchApprove(dto);
    }

    @GetMapping("/applications")
    @Operation(summary = "获取绑定申请列表", description = "分页获取设备绑定申请列表")
    public Map<String, Object> getBindingApplications(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        log.info("获取绑定申请列表 - 状态: {}, 页码: {}, 大小: {}", status, pageNum, pageSize);
        return deviceBindService.getBindingApplications(status, pageNum, pageSize);
    }

    @GetMapping("/user_bindings")
    @Operation(summary = "获取用户设备绑定列表", description = "获取指定用户的设备绑定状态")
    public Map<String, Object> getUserBindings(@RequestParam String userId) {
        log.info("获取用户设备绑定列表 - 用户ID: {}", userId);
        return deviceBindService.getUserBindings(userId);
    }
}