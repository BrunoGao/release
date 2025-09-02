package com.ljwx.modules.health.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageDetailV2Mapper;
import com.ljwx.modules.health.service.ITDeviceMessageDetailV2Service;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 设备消息详情表V2服务实现 - 基于userId直接关联优化
 *
 * @author ljwx-system
 * @since 2025-08-31
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TDeviceMessageDetailV2ServiceImpl extends ServiceImpl<TDeviceMessageDetailV2Mapper, TDeviceMessageDetailV2> 
        implements ITDeviceMessageDetailV2Service {

    @Override
    public TDeviceMessageDetailV2 getByMessageAndUser(Long messageId, Long userId) {
        return getOne(new LambdaQueryWrapper<TDeviceMessageDetailV2>()
            .eq(TDeviceMessageDetailV2::getMessageId, messageId)
            .eq(TDeviceMessageDetailV2::getUserId, userId)
            .eq(TDeviceMessageDetailV2::getIsDeleted, 0));
    }

    @Override
    public List<TDeviceMessageDetailV2> getByUserId(Long userId, Long customerId) {
        return list(new LambdaQueryWrapper<TDeviceMessageDetailV2>()
            .eq(TDeviceMessageDetailV2::getUserId, userId)
            .eq(TDeviceMessageDetailV2::getCustomerId, customerId)
            .eq(TDeviceMessageDetailV2::getIsDeleted, 0)
            .orderByDesc(TDeviceMessageDetailV2::getCreateTime));
    }

    @Override
    @Transactional
    public boolean updateDeliveryStatus(Long messageId, Long userId, String deliveryStatus) {
        return update(new LambdaUpdateWrapper<TDeviceMessageDetailV2>()
            .set(TDeviceMessageDetailV2::getDeliveryStatus, deliveryStatus)
            .set(TDeviceMessageDetailV2::getLastDeliveryTime, LocalDateTime.now())
            .set(TDeviceMessageDetailV2::getUpdateTime, LocalDateTime.now())
            .eq(TDeviceMessageDetailV2::getMessageId, messageId)
            .eq(TDeviceMessageDetailV2::getUserId, userId));
    }

    @Override
    @Transactional
    public int batchUpdateDeliveryStatus(List<Long> messageIds, Long userId, String deliveryStatus) {
        if (messageIds == null || messageIds.isEmpty()) {
            return 0;
        }
        
        LambdaUpdateWrapper<TDeviceMessageDetailV2> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.set(TDeviceMessageDetailV2::getDeliveryStatus, deliveryStatus)
                    .set(TDeviceMessageDetailV2::getLastDeliveryTime, LocalDateTime.now())
                    .set(TDeviceMessageDetailV2::getUpdateTime, LocalDateTime.now())
                    .in(TDeviceMessageDetailV2::getMessageId, messageIds)
                    .eq(TDeviceMessageDetailV2::getUserId, userId);
        
        return getBaseMapper().update(null, updateWrapper);
    }
}