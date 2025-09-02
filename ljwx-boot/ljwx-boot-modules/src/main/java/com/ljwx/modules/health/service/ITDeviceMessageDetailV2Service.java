package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;

import java.util.List;

/**
 * 设备消息详情表V2服务接口 - 基于userId直接关联优化
 *
 * @author ljwx-system
 * @since 2025-08-31
 */
public interface ITDeviceMessageDetailV2Service extends IService<TDeviceMessageDetailV2> {

    /**
     * 根据消息ID和用户ID获取消息详情
     * 
     * @param messageId 消息ID
     * @param userId 用户ID
     * @return 消息详情
     */
    TDeviceMessageDetailV2 getByMessageAndUser(Long messageId, Long userId);

    /**
     * 根据用户ID获取所有消息详情
     * 
     * @param userId 用户ID
     * @param customerId 租户ID
     * @return 消息详情列表
     */
    List<TDeviceMessageDetailV2> getByUserId(Long userId, Long customerId);

    /**
     * 更新消息传递状态
     * 
     * @param messageId 消息ID
     * @param userId 用户ID
     * @param deliveryStatus 传递状态
     * @return 是否成功
     */
    boolean updateDeliveryStatus(Long messageId, Long userId, String deliveryStatus);

    /**
     * 批量更新消息传递状态
     * 
     * @param messageIds 消息ID列表
     * @param userId 用户ID
     * @param deliveryStatus 传递状态
     * @return 更新数量
     */
    int batchUpdateDeliveryStatus(List<Long> messageIds, Long userId, String deliveryStatus);
}