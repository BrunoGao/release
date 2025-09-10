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

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.entity.TDeviceMessageV2;
import com.ljwx.modules.health.domain.dto.v2.message.MessageCreateV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageQueryV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageUpdateV2DTO;
import com.ljwx.modules.health.domain.vo.v2.MessageStatisticsV2VO;
import com.ljwx.modules.health.domain.vo.v2.MessageSummaryV2VO;
import com.ljwx.modules.health.domain.vo.v2.TDeviceMessageV2VO;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 设备消息V2服务接口 - 高性能版本
 * 
 * 主要特性：
 * 1. 批量操作支持
 * 2. 高性能查询
 * 3. 统计分析功能
 * 4. 缓存策略集成
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.ITDeviceMessageV2Service
 * @CreateTime 2025-09-10 - 16:00:00
 */
public interface ITDeviceMessageV2Service extends IService<TDeviceMessageV2> {

    // ==================== 基础CRUD操作 ====================

    /**
     * 分页查询消息 - 高性能版本
     */
    IPage<TDeviceMessageV2VO> pageMessages(PageQuery pageQuery, MessageQueryV2DTO queryDTO);

    /**
     * 创建消息 - 支持批量分发
     */
    Long createMessage(MessageCreateV2DTO createDTO);

    /**
     * 批量创建消息
     */
    List<Long> batchCreateMessages(List<MessageCreateV2DTO> createDTOs);

    /**
     * 更新消息
     */
    boolean updateMessage(MessageUpdateV2DTO updateDTO);

    /**
     * 根据ID获取消息详情
     */
    TDeviceMessageV2VO getMessageById(Long messageId);

    /**
     * 软删除消息
     */
    boolean deleteMessage(Long messageId);

    /**
     * 批量软删除消息
     */
    boolean batchDeleteMessages(List<Long> messageIds);

    // ==================== 消息分发操作 ====================

    /**
     * 发送消息到指定设备
     */
    boolean sendToDevice(Long messageId, String deviceSn);

    /**
     * 发送消息到指定用户
     */
    boolean sendToUser(Long messageId, String userId);

    /**
     * 发送消息到部门 - 群发
     */
    boolean sendToDepartment(Long messageId, Long orgId);

    /**
     * 发送消息到组织 - 群发
     */
    boolean sendToOrganization(Long messageId, Long customerId);

    /**
     * 批量分发消息
     */
    Map<String, Object> batchDistributeMessage(Long messageId, List<String> targets, String targetType);

    // ==================== 消息状态管理 ====================

    /**
     * 确认消息
     */
    boolean acknowledgeMessage(Long messageId, String targetId, String channel);

    /**
     * 批量确认消息
     */
    boolean batchAcknowledgeMessages(List<Long> messageIds, String targetId);

    /**
     * 标记消息为已送达
     */
    boolean markAsDelivered(Long messageId, String targetId, String channel);

    /**
     * 标记消息为失败
     */
    boolean markAsFailed(Long messageId, String targetId, String channel, String errorMessage);

    /**
     * 重发失败的消息
     */
    boolean retryFailedMessage(Long messageId, String targetId);

    // ==================== 查询操作 ====================

    /**
     * 根据设备获取消息列表
     */
    List<TDeviceMessageV2VO> getMessagesByDevice(String deviceSn, Integer limit);

    /**
     * 根据用户获取消息列表
     */
    List<TDeviceMessageV2VO> getMessagesByUser(String userId, Integer limit);

    /**
     * 获取组织消息列表
     */
    IPage<TDeviceMessageV2VO> getOrganizationMessages(Long customerId, Long orgId, PageQuery pageQuery);

    /**
     * 获取未读消息数量
     */
    Long getUnreadCount(String targetId, String targetType);

    /**
     * 获取过期消息列表
     */
    List<TDeviceMessageV2VO> getExpiredMessages(LocalDateTime before);

    /**
     * 根据消息类型查询
     */
    IPage<TDeviceMessageV2VO> getMessagesByType(String messageType, PageQuery pageQuery);

    // ==================== 统计分析 ====================

    /**
     * 获取消息统计信息
     */
    MessageStatisticsV2VO getMessageStatistics(Long customerId, Long orgId, LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 获取消息汇总信息
     */
    MessageSummaryV2VO getMessageSummary(Long messageId);

    /**
     * 获取渠道分发统计
     */
    Map<String, Object> getChannelStatistics(Long customerId, LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 获取响应时间统计
     */
    Map<String, Object> getResponseTimeStatistics(Long customerId, String messageType, LocalDateTime startTime, LocalDateTime endTime);

    /**
     * 获取消息类型分布
     */
    Map<String, Long> getMessageTypeDistribution(Long customerId, LocalDateTime startTime, LocalDateTime endTime);

    // ==================== 生命周期管理 ====================

    /**
     * 清理过期消息
     */
    int cleanupExpiredMessages(LocalDateTime before);

    /**
     * 清理已完成消息 (保留指定天数)
     */
    int cleanupCompletedMessages(int retentionDays);

    /**
     * 归档历史消息
     */
    int archiveHistoryMessages(LocalDateTime before);

    // ==================== 缓存操作 ====================

    /**
     * 预热消息缓存
     */
    void warmupMessageCache(Long customerId);

    /**
     * 清理消息缓存
     */
    void clearMessageCache(Long messageId);

    /**
     * 刷新统计缓存
     */
    void refreshStatisticsCache(Long customerId);

    // ==================== 高级功能 ====================

    /**
     * 消息去重检查
     */
    boolean isDuplicateMessage(String deviceSn, String messageContent, LocalDateTime withinMinutes);

    /**
     * 获取消息传播路径
     */
    List<Map<String, Object>> getMessagePropagationPath(Long messageId);

    /**
     * 消息性能分析
     */
    Map<String, Object> analyzeMessagePerformance(Long messageId);

    /**
     * 批量导出消息
     */
    List<Map<String, Object>> exportMessages(MessageQueryV2DTO queryDTO);
}