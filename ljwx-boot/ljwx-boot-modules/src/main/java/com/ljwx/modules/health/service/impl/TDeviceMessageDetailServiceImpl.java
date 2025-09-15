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
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.domain.enums.DeliveryStatusEnum;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageDetailMapper;
import com.ljwx.modules.health.service.ITDeviceMessageDetailService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import jakarta.annotation.Resource;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * V2设备消息详情服务实现类
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceMessageDetailServiceImpl
 * @CreateTime 2025-09-10 - 16:20:00
 */
@Slf4j
@Service
public class TDeviceMessageDetailServiceImpl extends ServiceImpl<TDeviceMessageDetailMapper, TDeviceMessageDetail> 
    implements ITDeviceMessageDetailService {


    @Override
    public List<TDeviceMessageDetail> getByMessageId(Long messageId) {
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getMessageId, messageId);
        return list(wrapper);
    }

    @Override
    public List<TDeviceMessageDetail> getByDeviceSn(String deviceSn, Integer limit) {
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getDeviceSn, deviceSn);
        wrapper.orderByDesc(TDeviceMessageDetail::getCreateTime);
        wrapper.last("LIMIT " + (limit != null ? limit : 50));
        return list(wrapper);
    }

    @Override
    public TDeviceMessageDetail getByDistributionId(String distributionId) {
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getDistributionId, distributionId);
        return getOne(wrapper);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TDeviceMessageDetail createDistribution(TDeviceMessageDetail detail) {
        try {
            detail.generateDistributionId();
            detail.setDeliveryStatus(DeliveryStatusEnum.PENDING);
            detail.setSentTime(LocalDateTime.now());
            
            save(detail);
            
            log.info("创建消息分发详情成功: distributionId={}, messageId={}", 
                detail.getDistributionId(), detail.getMessageId());
            return detail;
        } catch (Exception e) {
            log.error("创建消息分发详情失败: messageId={}", detail.getMessageId(), e);
            throw new RuntimeException("创建消息分发详情失败", e);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<TDeviceMessageDetail> batchCreateDistributions(List<TDeviceMessageDetail> details) {
        try {
            LocalDateTime now = LocalDateTime.now();
            for (TDeviceMessageDetail detail : details) {
                detail.generateDistributionId();
                detail.setDeliveryStatus(DeliveryStatusEnum.PENDING);
                detail.setSentTime(now);
            }
            
            saveBatch(details);
            
            log.info("批量创建消息分发详情成功: count={}", details.size());
            return details;
        } catch (Exception e) {
            log.error("批量创建消息分发详情失败: count={}", details.size(), e);
            throw new RuntimeException("批量创建消息分发详情失败", e);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean acknowledgeDistribution(String distributionId) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.markAsAcknowledged();
            updateById(detail);
            
            log.info("确认消息分发成功: distributionId={}", distributionId);
            return true;
        } catch (Exception e) {
            log.error("确认消息分发失败: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchAcknowledgeDistributions(List<String> distributionIds) {
        try {
            LambdaUpdateWrapper<TDeviceMessageDetail> updateWrapper = new LambdaUpdateWrapper<>();
            updateWrapper.in(TDeviceMessageDetail::getDistributionId, distributionIds)
                         .set(TDeviceMessageDetail::getDeliveryStatus, DeliveryStatusEnum.ACKNOWLEDGED)
                         .set(TDeviceMessageDetail::getAcknowledgeTime, LocalDateTime.now());
            int updated = update(updateWrapper) ? distributionIds.size() : 0;
            
            log.info("批量确认消息分发成功: count={}, updated={}", distributionIds.size(), updated);
            return updated > 0;
        } catch (Exception e) {
            log.error("批量确认消息分发失败: count={}", distributionIds.size(), e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean markDistributionFailed(String distributionId, String errorMessage) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.markAsFailed(errorMessage);
            updateById(detail);
            
            log.info("标记消息分发失败: distributionId={}, error={}", distributionId, errorMessage);
            return true;
        } catch (Exception e) {
            log.error("标记消息分发失败异常: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean markDistributionDelivered(String distributionId) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.markAsDelivered();
            updateById(detail);
            
            log.info("标记消息分发成功: distributionId={}", distributionId);
            return true;
        } catch (Exception e) {
            log.error("标记消息分发成功异常: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateDeliveryStatus(String distributionId, DeliveryStatusEnum status) {
        try {
            LambdaUpdateWrapper<TDeviceMessageDetail> updateWrapper = new LambdaUpdateWrapper<>();
            updateWrapper.eq(TDeviceMessageDetail::getDistributionId, distributionId)
                .set(TDeviceMessageDetail::getDeliveryStatus, status);
            
            boolean updated = update(updateWrapper);
            
            log.info("更新分发状态: distributionId={}, status={}, result={}", distributionId, status, updated);
            return updated;
        } catch (Exception e) {
            log.error("更新分发状态失败: distributionId={}, status={}", distributionId, status, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchUpdateDeliveryStatus(List<String> distributionIds, DeliveryStatusEnum status) {
        try {
            LambdaUpdateWrapper<TDeviceMessageDetail> updateWrapper = new LambdaUpdateWrapper<>();
            updateWrapper.in(TDeviceMessageDetail::getDistributionId, distributionIds)
                         .set(TDeviceMessageDetail::getDeliveryStatus, status);
            int updated = update(updateWrapper) ? distributionIds.size() : 0;
            
            log.info("批量更新分发状态: count={}, status={}, updated={}", 
                distributionIds.size(), status, updated);
            return updated > 0;
        } catch (Exception e) {
            log.error("批量更新分发状态失败: count={}, status={}", distributionIds.size(), status, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean retryFailedDistribution(String distributionId) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.incrementAttempts();
            detail.setDeliveryStatus(DeliveryStatusEnum.PENDING);
            detail.setSentTime(LocalDateTime.now());
            
            updateById(detail);
            
            log.info("重试失败分发: distributionId={}, attempts={}", 
                distributionId, detail.getAttempts());
            return true;
        } catch (Exception e) {
            log.error("重试失败分发异常: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean batchRetryFailedDistributions(List<String> distributionIds) {
        try {
            for (String distributionId : distributionIds) {
                retryFailedDistribution(distributionId);
            }
            
            log.info("批量重试失败分发完成: count={}", distributionIds.size());
            return true;
        } catch (Exception e) {
            log.error("批量重试失败分发异常: count={}", distributionIds.size(), e);
            return false;
        }
    }

    @Override
    public List<TDeviceMessageDetail> getPendingAcknowledgments(Long customerId, Integer limit) {
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(customerId != null, TDeviceMessageDetail::getCustomerId, customerId)
               .eq(TDeviceMessageDetail::getDeliveryStatus, DeliveryStatusEnum.PENDING)
               .orderByDesc(TDeviceMessageDetail::getCreateTime);
        if (limit != null) {
            wrapper.last("LIMIT " + limit);
        }
        return list(wrapper);
    }

    @Override
    public List<TDeviceMessageDetail> getFailedDistributions(Long customerId, Integer limit) {
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(customerId != null, TDeviceMessageDetail::getCustomerId, customerId)
               .eq(TDeviceMessageDetail::getDeliveryStatus, DeliveryStatusEnum.FAILED)
               .orderByDesc(TDeviceMessageDetail::getCreateTime);
        if (limit != null) {
            wrapper.last("LIMIT " + limit);
        }
        return list(wrapper);
    }

    @Override
    public Map<String, Object> getDistributionStats(Long messageId) {
        // Simplified implementation - return basic stats
        Map<String, Object> stats = new java.util.HashMap<>();
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getMessageId, messageId);
        long total = count(wrapper);
        
        wrapper.clear();
        wrapper.eq(TDeviceMessageDetail::getMessageId, messageId)
               .eq(TDeviceMessageDetail::getDeliveryStatus, DeliveryStatusEnum.DELIVERED);
        long delivered = count(wrapper);
        
        stats.put("total", total);
        stats.put("delivered", delivered);
        stats.put("pending", total - delivered);
        
        return stats;
    }

    @Override
    public Map<String, Object> getDeviceReceiveStats(String deviceSn, Integer hours) {
        // Simplified implementation
        Map<String, Object> stats = new java.util.HashMap<>();
        LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessageDetail::getDeviceSn, deviceSn);
        if (hours != null) {
            wrapper.ge(TDeviceMessageDetail::getCreateTime, LocalDateTime.now().minusHours(hours));
        }
        long total = count(wrapper);
        stats.put("total", total);
        return stats;
    }

    @Override
    public List<Map<String, Object>> getChannelResponseTimeStats(Long customerId, Integer hours) {
        // Simplified implementation - return empty list for now
        return new java.util.ArrayList<>();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean cleanupExpiredDistributions(Integer days) {
        try {
            LocalDateTime beforeTime = LocalDateTime.now().minusDays(days);
            LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
            wrapper.lt(TDeviceMessageDetail::getCreateTime, beforeTime)
                   .eq(TDeviceMessageDetail::getDeliveryStatus, DeliveryStatusEnum.EXPIRED);
            long deletedCount = count(wrapper);
            boolean removed = remove(wrapper);
            int deleted = (int) deletedCount;
            
            log.info("清理过期分发记录完成: days={}, deleted={}", days, deleted);
            return deleted > 0;
        } catch (Exception e) {
            log.error("清理过期分发记录失败: days={}", days, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean cleanupOldDistributions(Integer days, Integer batchSize) {
        try {
            LocalDateTime beforeTime = LocalDateTime.now().minusDays(days);
            LambdaQueryWrapper<TDeviceMessageDetail> wrapper = new LambdaQueryWrapper<>();
            wrapper.lt(TDeviceMessageDetail::getCreateTime, beforeTime);
            if (batchSize != null) {
                wrapper.last("LIMIT " + batchSize);
            }
            long deletedCount = count(wrapper);
            boolean removed = remove(wrapper);
            int deleted = (int) deletedCount;
            
            log.info("清理旧分发数据完成: days={}, batchSize={}, deleted={}", 
                days, batchSize, deleted);
            return deleted > 0;
        } catch (Exception e) {
            log.error("清理旧分发数据失败: days={}, batchSize={}", days, batchSize, e);
            return false;
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean calculateResponseTime(String distributionId) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.calculateResponseTime();
            
            if (detail.getResponseTime() != null) {
                LambdaUpdateWrapper<TDeviceMessageDetail> updateWrapper = new LambdaUpdateWrapper<>();
                updateWrapper.eq(TDeviceMessageDetail::getId, detail.getId())
                            .set(TDeviceMessageDetail::getResponseTime, detail.getResponseTime());
                update(updateWrapper);
                log.info("更新响应时间: distributionId={}, responseTime={}s", 
                    distributionId, detail.getResponseTime());
            }
            
            return true;
        } catch (Exception e) {
            log.error("计算响应时间失败: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    public int getRetryAttempts(String distributionId) {
        TDeviceMessageDetail detail = getByDistributionId(distributionId);
        return detail != null ? detail.getAttempts() : 0;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean incrementRetryAttempts(String distributionId) {
        try {
            TDeviceMessageDetail detail = getByDistributionId(distributionId);
            if (detail == null) {
                log.warn("分发详情不存在: distributionId={}", distributionId);
                return false;
            }
            
            detail.incrementAttempts();
            updateById(detail);
            
            log.info("增加重试次数: distributionId={}, attempts={}", 
                distributionId, detail.getAttempts());
            return true;
        } catch (Exception e) {
            log.error("增加重试次数失败: distributionId={}", distributionId, e);
            return false;
        }
    }

    @Override
    public boolean isDistributionExpired(String distributionId) {
        TDeviceMessageDetail detail = getByDistributionId(distributionId);
        if (detail == null) {
            return true;
        }
        
        // 检查是否有过期时间设置，如果没有则不过期
        Object expiryTime = detail.getDeliveryDetail("expiryTime");
        if (expiryTime == null) {
            return false;
        }
        
        if (expiryTime instanceof LocalDateTime) {
            return LocalDateTime.now().isAfter((LocalDateTime) expiryTime);
        }
        
        return false;
    }

    @Override
    public Double getDistributionSuccessRate(Long messageId) {
        try {
            Map<String, Object> stats = getDistributionStats(messageId);
            if (stats == null || stats.isEmpty()) {
                return 0.0;
            }
            
            Long total = (Long) stats.get("total");
            Long successful = (Long) stats.get("successful");
            
            if (total == null || total == 0) {
                return 0.0;
            }
            
            return (successful != null ? successful.doubleValue() : 0.0) / total.doubleValue() * 100.0;
        } catch (Exception e) {
            log.error("获取分发成功率失败: messageId={}", messageId, e);
            return 0.0;
        }
    }

    @Override
    public Double getDeviceDistributionSuccessRate(String deviceSn, Integer hours) {
        try {
            Map<String, Object> stats = getDeviceReceiveStats(deviceSn, hours);
            if (stats == null || stats.isEmpty()) {
                return 0.0;
            }
            
            Long total = (Long) stats.get("total");
            Long successful = (Long) stats.get("successful");
            
            if (total == null || total == 0) {
                return 0.0;
            }
            
            return (successful != null ? successful.doubleValue() : 0.0) / total.doubleValue() * 100.0;
        } catch (Exception e) {
            log.error("获取设备分发成功率失败: deviceSn={}, hours={}", deviceSn, hours, e);
            return 0.0;
        }
    }

    @Override
    public com.baomidou.mybatisplus.core.metadata.IPage<TDeviceMessageDetail> listTDeviceMessageDetailPage(
            com.ljwx.infrastructure.page.PageQuery pageQuery, 
            com.ljwx.modules.health.domain.bo.TDeviceMessageDetailBO queryBO) {
        
        com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<TDeviceMessageDetail> wrapper = 
            new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
        
        if (queryBO != null) {
            wrapper.eq(queryBO.getMessageId() != null, TDeviceMessageDetail::getMessageId, queryBO.getMessageId())
                   .eq(queryBO.getDeviceSn() != null, TDeviceMessageDetail::getDeviceSn, queryBO.getDeviceSn())
                   .eq(queryBO.getCustomerId() != null, TDeviceMessageDetail::getCustomerId, queryBO.getCustomerId())
                   .eq(queryBO.getOrgId() != null, TDeviceMessageDetail::getOrgId, queryBO.getOrgId());
            
            // Set delivery status filter
            if (queryBO.getDeliveryStatus() != null) {
                wrapper.eq(TDeviceMessageDetail::getDeliveryStatus, queryBO.getDeliveryStatus());
            }
        }
        
        wrapper.orderByDesc(TDeviceMessageDetail::getCreateTime);
        
        return page(pageQuery.buildPage(), wrapper);
    }
}