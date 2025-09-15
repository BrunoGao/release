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

package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetail;
import com.ljwx.modules.health.domain.enums.DeliveryStatusEnum;

import java.util.List;
import java.util.Map;

/**
 * V2设备消息详情服务接口
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.ITDeviceMessageDetailService
 * @CreateTime 2025-09-10 - 16:20:00
 */
public interface ITDeviceMessageDetailService extends IService<TDeviceMessageDetail> {

    /**
     * 分页查询消息详情 - 兼容BO接口  
     */
    com.baomidou.mybatisplus.core.metadata.IPage<TDeviceMessageDetail> listTDeviceMessageDetailPage(com.ljwx.infrastructure.page.PageQuery pageQuery, com.ljwx.modules.health.domain.bo.TDeviceMessageDetailBO queryBO);

    /**
     * 根据消息ID查询分发详情
     */
    List<TDeviceMessageDetail> getByMessageId(Long messageId);

    /**
     * 根据设备序列号查询分发详情
     */
    List<TDeviceMessageDetail> getByDeviceSn(String deviceSn, Integer limit);

    /**
     * 根据分发ID查询分发详情
     */
    TDeviceMessageDetail getByDistributionId(String distributionId);

    /**
     * 创建消息分发详情
     */
    TDeviceMessageDetail createDistribution(TDeviceMessageDetail detail);

    /**
     * 批量创建消息分发详情
     */
    List<TDeviceMessageDetail> batchCreateDistributions(List<TDeviceMessageDetail> details);

    /**
     * 确认消息分发
     */
    boolean acknowledgeDistribution(String distributionId);

    /**
     * 批量确认消息分发
     */
    boolean batchAcknowledgeDistributions(List<String> distributionIds);

    /**
     * 标记分发失败
     */
    boolean markDistributionFailed(String distributionId, String errorMessage);

    /**
     * 标记分发成功
     */
    boolean markDistributionDelivered(String distributionId);

    /**
     * 更新分发状态
     */
    boolean updateDeliveryStatus(String distributionId, DeliveryStatusEnum status);

    /**
     * 批量更新分发状态
     */
    boolean batchUpdateDeliveryStatus(List<String> distributionIds, DeliveryStatusEnum status);

    /**
     * 重试失败的分发
     */
    boolean retryFailedDistribution(String distributionId);

    /**
     * 批量重试失败的分发
     */
    boolean batchRetryFailedDistributions(List<String> distributionIds);

    /**
     * 获取待确认的分发
     */
    List<TDeviceMessageDetail> getPendingAcknowledgments(Long customerId, Integer limit);

    /**
     * 获取失败的分发
     */
    List<TDeviceMessageDetail> getFailedDistributions(Long customerId, Integer limit);

    /**
     * 获取分发统计信息
     */
    Map<String, Object> getDistributionStats(Long messageId);

    /**
     * 获取设备接收统计
     */
    Map<String, Object> getDeviceReceiveStats(String deviceSn, Integer hours);

    /**
     * 获取渠道响应时间统计
     */
    List<Map<String, Object>> getChannelResponseTimeStats(Long customerId, Integer hours);

    /**
     * 清理过期的分发记录
     */
    boolean cleanupExpiredDistributions(Integer days);

    /**
     * 清理旧的分发数据
     */
    boolean cleanupOldDistributions(Integer days, Integer batchSize);

    /**
     * 计算并更新响应时间
     */
    boolean calculateResponseTime(String distributionId);

    /**
     * 获取分发详情的重试次数
     */
    int getRetryAttempts(String distributionId);

    /**
     * 增加重试次数
     */
    boolean incrementRetryAttempts(String distributionId);

    /**
     * 检查分发是否已过期
     */
    boolean isDistributionExpired(String distributionId);

    /**
     * 获取消息的分发成功率
     */
    Double getDistributionSuccessRate(Long messageId);

    /**
     * 获取设备的分发成功率
     */
    Double getDeviceDistributionSuccessRate(String deviceSn, Integer hours);
}