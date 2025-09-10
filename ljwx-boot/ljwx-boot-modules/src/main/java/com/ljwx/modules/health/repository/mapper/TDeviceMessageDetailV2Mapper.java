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

package com.ljwx.modules.health.repository.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.domain.entity.TDeviceMessageDetailV2;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * V2设备消息详情Mapper接口
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.repository.mapper.TDeviceMessageDetailV2Mapper
 * @CreateTime 2025-09-10 - 16:15:00
 */
@Mapper
public interface TDeviceMessageDetailV2Mapper extends BaseMapper<TDeviceMessageDetailV2> {

    /**
     * 根据消息ID查询分发详情
     */
    List<TDeviceMessageDetailV2> selectByMessageId(@Param("messageId") Long messageId);

    /**
     * 根据设备序列号查询分发详情
     */
    List<TDeviceMessageDetailV2> selectByDeviceSn(@Param("deviceSn") String deviceSn, @Param("limit") Integer limit);

    /**
     * 根据分发ID查询分发详情
     */
    TDeviceMessageDetailV2 selectByDistributionId(@Param("distributionId") String distributionId);

    /**
     * 查询待确认的分发
     */
    List<TDeviceMessageDetailV2> selectPendingAcknowledgments(@Param("customerId") Long customerId, @Param("limit") Integer limit);

    /**
     * 查询失败的分发
     */
    List<TDeviceMessageDetailV2> selectFailedDistributions(@Param("customerId") Long customerId, @Param("limit") Integer limit);

    /**
     * 批量插入分发详情
     */
    int batchInsert(@Param("list") List<TDeviceMessageDetailV2> list);

    /**
     * 批量更新分发状态
     */
    int batchUpdateDeliveryStatus(@Param("distributionIds") List<String> distributionIds, @Param("status") String status);

    /**
     * 统计分发情况按状态
     */
    List<Map<String, Object>> countByDeliveryStatus(@Param("messageId") Long messageId);

    /**
     * 统计分发情况按渠道
     */
    List<Map<String, Object>> countByChannel(@Param("customerId") Long customerId, @Param("orgId") Long orgId);

    /**
     * 获取消息的分发统计
     */
    Map<String, Object> getDistributionStats(@Param("messageId") Long messageId);

    /**
     * 获取设备的接收统计
     */
    Map<String, Object> getDeviceReceiveStats(@Param("deviceSn") String deviceSn, @Param("hours") Integer hours);

    /**
     * 获取渠道响应时间统计
     */
    List<Map<String, Object>> getChannelResponseTimeStats(@Param("customerId") Long customerId, @Param("hours") Integer hours);

    /**
     * 删除过期的分发记录
     */
    int deleteExpiredDistributions(@Param("beforeTime") LocalDateTime beforeTime);

    /**
     * 清理旧的分发数据
     */
    int cleanupOldDistributions(@Param("beforeTime") LocalDateTime beforeTime, @Param("batchSize") Integer batchSize);

    /**
     * 更新响应时间
     */
    int updateResponseTime(@Param("id") Long id, @Param("responseTime") Integer responseTime);

    /**
     * 重置失败的分发状态
     */
    int resetFailedDistributions(@Param("ids") List<Long> ids);
}