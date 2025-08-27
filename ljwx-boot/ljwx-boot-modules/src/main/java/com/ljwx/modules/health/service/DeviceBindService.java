/*
* All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
* Open Source Agreement: Apache License, Version 2.0
*/

package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.dto.device.bind.BatchApproveBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.CheckDeviceBindingDTO;
import com.ljwx.modules.health.domain.dto.device.bind.SubmitBindingApplicationDTO;
import java.util.Map;

/**
* 设备绑定服务接口
*
* @Author Claude Code
* @ProjectName ljwx-boot
* @ClassName com.ljwx.modules.health.service.DeviceBindService
* @CreateTime 2025-08-23
*/

public interface DeviceBindService {

    /**
     * 检查设备绑定状态
     * @param dto 检查绑定状态参数
     * @return 绑定状态信息
     */
    Map<String, Object> checkDeviceBinding(CheckDeviceBindingDTO dto);

    /**
     * 提交设备绑定申请
     * @param dto 绑定申请参数
     * @return 提交结果
     */
    Map<String, Object> submitBindingApplication(SubmitBindingApplicationDTO dto);

    /**
     * 批量审批绑定申请
     * @param dto 批量审批参数
     * @return 审批结果
     */
    Map<String, Object> batchApprove(BatchApproveBindingDTO dto);

    /**
     * 获取绑定申请列表
     * @param status 申请状态
     * @param pageNum 页码
     * @param pageSize 页大小
     * @return 申请列表
     */
    Map<String, Object> getBindingApplications(String status, Integer pageNum, Integer pageSize);

    /**
     * 获取用户设备绑定状态
     * @param userId 用户ID
     * @return 绑定状态列表
     */
    Map<String, Object> getUserBindings(String userId);
}