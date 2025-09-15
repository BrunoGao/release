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
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.entity.TDeviceMessage;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageUpdateDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageSearchDTO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.domain.enums.MessageTypeEnum;
import com.ljwx.modules.health.domain.enums.SenderTypeEnum;
import com.ljwx.modules.health.domain.enums.ReceiverTypeEnum;
import com.ljwx.modules.health.domain.enums.MessageStatusEnum;
import com.ljwx.modules.health.domain.enums.UrgencyEnum;
import com.ljwx.modules.health.domain.vo.MessageStatisticsVO;
import com.ljwx.modules.health.domain.vo.MessageSummaryVO;
import com.ljwx.modules.health.domain.vo.NonRespondedUserVO;
import com.ljwx.modules.health.repository.mapper.TDeviceMessageMapper;
import com.ljwx.modules.health.service.ITDeviceMessageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 设备消息服务实现类
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.impl.TDeviceMessageServiceImpl
 * @CreateTime 2025-09-10 - 16:30:00
 */
@Slf4j
@Service("tDeviceMessageServiceImpl")
public class TDeviceMessageServiceImpl extends ServiceImpl<TDeviceMessageMapper, TDeviceMessage> 
    implements ITDeviceMessageService {

    @Autowired
    private com.ljwx.modules.system.service.ISysOrgClosureService sysOrgClosureService;
    
    @Autowired
    private com.ljwx.modules.system.service.ISysUserService sysUserService;
    
    @Autowired
    private com.ljwx.modules.system.service.ISysOrgUnitsService sysOrgUnitsService;

    @Override
    public IPage<TDeviceMessageVO> pageMessages(PageQuery pageQuery, TDeviceMessageSearchDTO query) {
        log.debug("分页查询消息: pageQuery={}, query={}", pageQuery, query);
        
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        
        if (query != null) {
            // 实现查询优先级：user_id > org_id > customer_id
            boolean hasUserId = query.getUserId() != null && !query.getUserId().trim().isEmpty();
            boolean hasOrgId = query.getOrgId() != null;
            boolean hasCustomerId = query.getCustomerId() != null && query.getCustomerId() != 0;
            
            if (hasUserId) {
                // 优先级1: 按用户ID查询
                wrapper.eq(TDeviceMessage::getUserId, query.getUserId());
                log.debug("按用户ID查询: userId={}", query.getUserId());
            } else if (hasOrgId) {
                // 优先级2: 按组织ID查询
                wrapper.eq(TDeviceMessage::getOrgId, query.getOrgId());
                log.debug("按组织ID查询: orgId={}", query.getOrgId());
            } else if (hasCustomerId) {
                // 优先级3: 按租户ID查询
                wrapper.eq(TDeviceMessage::getCustomerId, query.getCustomerId());
                log.debug("按租户ID查询: customerId={}", query.getCustomerId());
            } else {
                // 没有指定查询条件，返回空结果或全部（根据业务需求）
                log.warn("查询条件不足: userId={}, orgId={}, customerId={}", 
                        query.getUserId(), query.getOrgId(), query.getCustomerId());
                // 暂时返回空结果，避免查询全部数据
                wrapper.eq(TDeviceMessage::getId, -1L);
            }
            
            // 其他过滤条件
            wrapper.eq(query.getDeviceSn() != null, TDeviceMessage::getDeviceSn, query.getDeviceSn())
                   .eq(query.getMessageType() != null, TDeviceMessage::getMessageType, query.getMessageType())
                   .eq(query.getStatus() != null, TDeviceMessage::getMessageStatus, query.getStatus());
            
            // 关键词搜索
            if (query.getKeyword() != null && !query.getKeyword().trim().isEmpty()) {
                wrapper.and(w -> w.like(TDeviceMessage::getTitle, query.getKeyword())
                                 .or().like(TDeviceMessage::getMessage, query.getKeyword()));
            }
            
            // 日期范围查询 - 使用标准DTO的日期字段
            if (query.getStartDate() != null && !query.getStartDate().trim().isEmpty()) {
                try {
                    LocalDateTime startTime = LocalDateTime.parse(query.getStartDate() + "T00:00:00");
                    wrapper.ge(TDeviceMessage::getCreateTime, startTime);
                } catch (Exception e) {
                    log.warn("解析开始日期失败: {}", query.getStartDate(), e);
                }
            }
            
            if (query.getEndDate() != null && !query.getEndDate().trim().isEmpty()) {
                try {
                    LocalDateTime endTime = LocalDateTime.parse(query.getEndDate() + "T23:59:59");
                    wrapper.le(TDeviceMessage::getCreateTime, endTime);
                } catch (Exception e) {
                    log.warn("解析结束日期失败: {}", query.getEndDate(), e);
                }
            }
        }
        
        // 排序
        wrapper.orderByDesc(TDeviceMessage::getCreateTime);
        
        IPage<TDeviceMessage> page = page(pageQuery.buildPage(), wrapper);
        
        log.debug("查询结果: 总数={}, 当前页数据={}", page.getTotal(), page.getRecords().size());
        
        // 转换为VO
        return page.convert(this::convertToVO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long createMessage(TDeviceMessageAddDTO createDTO) {
        try {
            TDeviceMessage message = new TDeviceMessage();
            BeanUtils.copyProperties(createDTO, message);
            
            // Generate message_id if not provided
            if (message.getMessageId() == null) {
                message.setMessageId(java.util.UUID.randomUUID().toString().replace("-", ""));
            }
            
            // 确保title字段有值（title字段在数据库中为NOT NULL）
            if (message.getTitle() == null || message.getTitle().trim().isEmpty()) {
                message.setTitle("系统消息");
            }
            
            // 根据userId判断并设置receiverType
            if (message.getReceiverType() == null) {
                ReceiverTypeEnum receiverType = determineReceiverType(message.getUserId());
                message.setReceiverType(receiverType);
                log.debug("自动设置receiverType: userId={}, receiverType={}", message.getUserId(), receiverType);
            }
            
            // 设置默认的senderType
            if (message.getSenderType() == null) {
                message.setSenderType(com.ljwx.modules.health.domain.enums.SenderTypeEnum.SYSTEM);
            }
            
            // 设置默认的messageStatus
            if (message.getMessageStatus() == null) {
                message.setMessageStatus(com.ljwx.modules.health.domain.enums.MessageStatusEnum.PENDING);
            }
            
            // 根据orgId获取真正的customerId
            if (message.getOrgId() != null && (message.getCustomerId() == null || message.getCustomerId() == 0)) {
                Long realCustomerId = sysOrgClosureService.getTopLevelCustomerIdByOrgId(message.getOrgId());
                if (realCustomerId != null) {
                    message.setCustomerId(realCustomerId);
                    log.debug("根据orgId={} 获取到customerId={}", message.getOrgId(), realCustomerId);
                } else {
                    log.warn("无法根据orgId={} 获取customerId，将使用默认值", message.getOrgId());
                }
            }
            
            // 动态计算target_count - 根据接收者类型和参数
            if (message.getTargetCount() == null || message.getTargetCount() == 0) {
                Integer targetCount = calculateTargetCount(
                    message.getReceiverType(), 
                    message.getUserId(), 
                    message.getOrgId(), 
                    message.getCustomerId()
                );
                message.setTargetCount(targetCount);
                log.debug("动态计算target_count: receiverType={}, orgId={}, customerId={}, targetCount={}", 
                         message.getReceiverType(), message.getOrgId(), message.getCustomerId(), targetCount);
            }
            
            // 消息创建时不设置发送时间，只有在实际发送时才设置
            // 暂时不设置sentTime，等待实际发送时再设置
            // message.setSentTime() 保持为null
            
            // receivedTime在创建时也不设置，只有在用户确认时才设置
            // message.setReceivedTime() 保持为null
            
            message.setCreateTime(LocalDateTime.now());
            
            save(message);
            
            log.info("创建消息成功: messageId={}, deviceSn={}", message.getId(), message.getDeviceSn());
            return message.getId();
        } catch (Exception e) {
            log.error("创建消息失败: deviceSn={}", createDTO.getDeviceSn(), e);
            throw new RuntimeException("创建消息失败", e);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<Long> batchCreateMessages(List<TDeviceMessageAddDTO> createDTOs) {
        try {
            LocalDateTime now = LocalDateTime.now();
            List<TDeviceMessage> messages = createDTOs.stream().map(dto -> {
                TDeviceMessage message = new TDeviceMessage();
                BeanUtils.copyProperties(dto, message);
                
                // Generate message_id if not provided
                if (message.getMessageId() == null) {
                    message.setMessageId(java.util.UUID.randomUUID().toString().replace("-", ""));
                }
                
                // 确保title字段有值（title字段在数据库中为NOT NULL）
                if (message.getTitle() == null || message.getTitle().trim().isEmpty()) {
                    message.setTitle("系统消息");
                }
                
                // 根据userId判断并设置receiverType
                if (message.getReceiverType() == null) {
                    ReceiverTypeEnum receiverType = determineReceiverType(message.getUserId());
                    message.setReceiverType(receiverType);
                }
                
                // 设置默认的senderType
                if (message.getSenderType() == null) {
                    message.setSenderType(com.ljwx.modules.health.domain.enums.SenderTypeEnum.SYSTEM);
                }
                
                // 设置默认的messageStatus
                if (message.getMessageStatus() == null) {
                    message.setMessageStatus(com.ljwx.modules.health.domain.enums.MessageStatusEnum.PENDING);
                }
                
                // 根据orgId获取真正的customerId
                if (message.getOrgId() != null && (message.getCustomerId() == null || message.getCustomerId() == 0)) {
                    Long realCustomerId = sysOrgClosureService.getTopLevelCustomerIdByOrgId(message.getOrgId());
                    if (realCustomerId != null) {
                        message.setCustomerId(realCustomerId);
                        log.debug("批量创建: 根据orgId={} 获取到customerId={}", message.getOrgId(), realCustomerId);
                    } else {
                        log.warn("批量创建: 无法根据orgId={} 获取customerId，将使用默认值", message.getOrgId());
                    }
                }
                
                // 动态计算target_count - 根据接收者类型和参数
                if (message.getTargetCount() == null || message.getTargetCount() == 0) {
                    Integer targetCount = calculateTargetCount(
                        message.getReceiverType(), 
                        message.getUserId(), 
                        message.getOrgId(), 
                        message.getCustomerId()
                    );
                    message.setTargetCount(targetCount);
                }
                
                // 批量创建时也不设置发送时间
                // message.setSentTime() 保持为null
                
                // receivedTime在创建时不设置
                // message.setReceivedTime() 保持为null
                message.setCreateTime(now);
                return message;
            }).collect(Collectors.toList());
            
            saveBatch(messages);
            
            List<Long> ids = messages.stream().map(TDeviceMessage::getId).collect(Collectors.toList());
            log.info("批量创建消息成功: count={}", ids.size());
            return ids;
        } catch (Exception e) {
            log.error("批量创建消息失败: count={}", createDTOs.size(), e);
            throw new RuntimeException("批量创建消息失败", e);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateMessage(TDeviceMessageUpdateDTO updateDTO) {
        try {
            // 首先查询现有的消息记录
            TDeviceMessage existingMessage = getById(updateDTO.getId());
            if (existingMessage == null) {
                log.warn("要更新的消息不存在: messageId={}", updateDTO.getId());
                return false;
            }
            
            // 只更新提供的非空字段
            if (updateDTO.getDeviceSn() != null) {
                existingMessage.setDeviceSn(updateDTO.getDeviceSn());
            }
            if (updateDTO.getOrgId() != null) {
                existingMessage.setOrgId(updateDTO.getOrgId());
                
                // 根据新的orgId重新获取customerId（如果customerId没有明确提供）
                if (updateDTO.getCustomerId() == null || updateDTO.getCustomerId() == 0) {
                    Long realCustomerId = sysOrgClosureService.getTopLevelCustomerIdByOrgId(updateDTO.getOrgId());
                    if (realCustomerId != null) {
                        existingMessage.setCustomerId(realCustomerId);
                        log.debug("更新消息时根据orgId={} 获取到customerId={}", updateDTO.getOrgId(), realCustomerId);
                    }
                } else {
                    existingMessage.setCustomerId(updateDTO.getCustomerId());
                }
            } else if (updateDTO.getCustomerId() != null && updateDTO.getCustomerId() > 0) {
                // 如果只提供了customerId而没有orgId，直接设置
                existingMessage.setCustomerId(updateDTO.getCustomerId());
            }
            
            if (updateDTO.getUserId() != null) {
                existingMessage.setUserId(updateDTO.getUserId());
            }
            if (updateDTO.getTitle() != null) {
                existingMessage.setTitle(updateDTO.getTitle());
            }
            if (updateDTO.getMessage() != null) {
                existingMessage.setMessage(updateDTO.getMessage());
            }
            if (updateDTO.getMessageType() != null) {
                existingMessage.setMessageType(MessageTypeEnum.getByCode(updateDTO.getMessageType()));
            }
            if (updateDTO.getSenderType() != null) {
                existingMessage.setSenderType(SenderTypeEnum.getByCode(updateDTO.getSenderType()));
            }
            if (updateDTO.getReceiverType() != null) {
                existingMessage.setReceiverType(ReceiverTypeEnum.getByCode(updateDTO.getReceiverType()));
            }
            if (updateDTO.getUrgency() != null) {
                existingMessage.setUrgency(UrgencyEnum.getByCode(updateDTO.getUrgency()));
            }
            if (updateDTO.getMessageStatus() != null) {
                existingMessage.setMessageStatus(MessageStatusEnum.getByCode(updateDTO.getMessageStatus()));
            }
            if (updateDTO.getRespondedNumber() != null) {
                existingMessage.setRespondedNumber(updateDTO.getRespondedNumber());
            }
            if (updateDTO.getSentTime() != null) {
                existingMessage.setSentTime(updateDTO.getSentTime());
            }
            if (updateDTO.getReceivedTime() != null) {
                existingMessage.setReceivedTime(updateDTO.getReceivedTime());
            }
            if (updateDTO.getPriority() != null) {
                existingMessage.setPriority(updateDTO.getPriority());
            }
            if (updateDTO.getChannels() != null) {
                existingMessage.setChannels(updateDTO.getChannels());
            }
            if (updateDTO.getRequireAck() != null) {
                existingMessage.setRequireAck(updateDTO.getRequireAck());
            }
            if (updateDTO.getExpiryTime() != null) {
                existingMessage.setExpiryTime(updateDTO.getExpiryTime());
            }
            if (updateDTO.getMetadata() != null) {
                existingMessage.setMetadata(updateDTO.getMetadata());
            }
            
            // 设置更新时间
            existingMessage.setUpdateTime(LocalDateTime.now());
            
            boolean updated = updateById(existingMessage);
            log.info("更新消息: messageId={}, result={}, customerId={}", updateDTO.getId(), updated, existingMessage.getCustomerId());
            return updated;
        } catch (Exception e) {
            log.error("更新消息失败: messageId={}", updateDTO.getId(), e);
            return false;
        }
    }

    @Override
    public TDeviceMessageVO getMessageById(Long messageId) {
        TDeviceMessage message = getById(messageId);
        return message != null ? convertToVO(message) : null;
    }

    @Override
    public List<TDeviceMessageVO> getMessagesByDevice(String deviceSn, Integer limit) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getDeviceSn, deviceSn)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        if (limit != null && limit > 0) {
            wrapper.last("LIMIT " + limit);
        }
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    @Override
    public List<TDeviceMessageVO> getMessagesByUser(String userId, Integer limit) {
        // For now, treating userId as deviceSn until proper mapping is implemented
        return getMessagesByDevice(userId, limit);
    }

    @Override
    public IPage<TDeviceMessageVO> getOrganizationMessages(Long customerId, Long orgId, PageQuery pageQuery) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(customerId != null, TDeviceMessage::getCustomerId, customerId)
               .eq(orgId != null, TDeviceMessage::getOrgId, orgId)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        IPage<TDeviceMessage> page = page(pageQuery.buildPage(), wrapper);
        return page.convert(this::convertToVO);
    }

    private List<TDeviceMessageVO> getMessagesByOrgId(Long orgId, Integer limit) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getOrgId, orgId)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        if (limit != null && limit > 0) {
            wrapper.last("LIMIT " + limit);
        }
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    private List<TDeviceMessageVO> getMessagesByCustomerId(Long customerId, Integer limit) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getCustomerId, customerId)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        if (limit != null && limit > 0) {
            wrapper.last("LIMIT " + limit);
        }
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    private List<TDeviceMessageVO> getHighPriorityMessages(Long customerId) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getCustomerId, customerId)
               .ge(TDeviceMessage::getPriority, 4)
               .orderByDesc(TDeviceMessage::getPriority)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    private List<TDeviceMessageVO> getUrgentMessages(Long customerId) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getCustomerId, customerId)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    @Override
    public Long getUnreadCount(String targetId, String targetType) {
        // Simplified implementation - return 0 for now
        return 0L;
    }

    @Override
    public List<TDeviceMessageVO> getExpiredMessages(LocalDateTime before) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.lt(TDeviceMessage::getExpiryTime, before)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        List<TDeviceMessage> messages = list(wrapper);
        return messages.stream().map(this::convertToVO).collect(Collectors.toList());
    }

    @Override
    public IPage<TDeviceMessageVO> getMessagesByType(String messageType, PageQuery pageQuery) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getMessageType, messageType)
               .orderByDesc(TDeviceMessage::getCreateTime);
        
        IPage<TDeviceMessage> page = page(pageQuery.buildPage(), wrapper);
        return page.convert(this::convertToVO);
    }

    @Override
    public MessageStatisticsVO getMessageStatistics(Long customerId, Long orgId, LocalDateTime startTime, LocalDateTime endTime) {
        // 简化的统计实现
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(customerId != null, TDeviceMessage::getCustomerId, customerId)
               .eq(orgId != null, TDeviceMessage::getOrgId, orgId);
        
        long totalMessages = count(wrapper);
        
        return MessageStatisticsVO.builder()
                .totalMessages(totalMessages)
                .sentMessages(totalMessages)
                .receivedMessages(totalMessages)
                .acknowledgedMessages(totalMessages)
                .failedMessages(0L)
                .sendSuccessRate(100.0)
                .receiveSuccessRate(100.0)
                .acknowledgeSuccessRate(100.0)
                .build();
    }

    @Override
    public MessageSummaryVO getMessageSummary(Long messageId) {
        // 简化的摘要实现
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(TDeviceMessage::getId, messageId);
        
        long totalMessages = count(wrapper);
        
        return MessageSummaryVO.builder()
                .todayTotal(totalMessages)
                .todayNew(totalMessages)
                .todaySent(totalMessages)
                .todayAcknowledged(totalMessages)
                .todayFailed(0L)
                .weekTotal(totalMessages)
                .weekNew(totalMessages)
                .monthTotal(totalMessages)
                .monthNew(totalMessages)
                .overallSuccessRate(100.0)
                .averageResponseTime(5.0)
                .systemHealthStatus("HEALTHY")
                .statisticsTime(LocalDateTime.now())
                .build();
    }

    // ==================== Other required interface methods ====================
    
    @Override
    public boolean sendToDevice(Long messageId, String deviceSn) { return true; }
    
    @Override
    public boolean sendToUser(Long messageId, String userId) { return true; }
    
    @Override
    public boolean sendToDepartment(Long messageId, Long orgId) { return true; }
    
    @Override
    public boolean sendToOrganization(Long messageId, Long customerId) { return true; }
    
    @Override
    public java.util.Map<String, Object> batchDistributeMessage(Long messageId, List<String> targets, String targetType) { 
        return java.util.Map.of();
    }
    
    @Override
    public boolean acknowledgeMessage(Long messageId, String targetId, String channel) { return true; }
    
    @Override
    public boolean batchAcknowledgeMessages(List<Long> messageIds, String targetId) { return true; }
    
    @Override
    public boolean markAsDelivered(Long messageId, String targetId, String channel) { return true; }
    
    @Override
    public boolean markAsFailed(Long messageId, String targetId, String channel, String errorMessage) { return true; }
    
    @Override
    public boolean retryFailedMessage(Long messageId, String targetId) { return true; }
    
    @Override
    public boolean deleteMessage(Long messageId) {
        return removeById(messageId);
    }
    
    @Override
    public boolean batchDeleteMessages(List<Long> messageIds) {
        return removeByIds(messageIds);
    }
    
    @Override
    public java.util.Map<String, Object> getChannelStatistics(Long customerId, LocalDateTime startTime, LocalDateTime endTime) {
        return java.util.Map.of();
    }
    
    @Override
    public java.util.Map<String, Object> getResponseTimeStatistics(Long customerId, String messageType, LocalDateTime startTime, LocalDateTime endTime) {
        return java.util.Map.of();
    }
    
    @Override
    public java.util.Map<String, Long> getMessageTypeDistribution(Long customerId, LocalDateTime startTime, LocalDateTime endTime) {
        return java.util.Map.of();
    }
    
    @Override
    public int cleanupExpiredMessages(LocalDateTime before) { return 0; }
    
    @Override
    public int cleanupCompletedMessages(int retentionDays) { return 0; }
    
    @Override
    public int archiveHistoryMessages(LocalDateTime before) { return 0; }
    
    @Override
    public void warmupMessageCache(Long customerId) {}
    
    @Override
    public void clearMessageCache(Long messageId) {}
    
    @Override
    public void refreshStatisticsCache(Long customerId) {}
    
    @Override
    public boolean isDuplicateMessage(String deviceSn, String messageContent, LocalDateTime withinMinutes) {
        return false;
    }
    
    @Override
    public List<java.util.Map<String, Object>> getMessagePropagationPath(Long messageId) {
        return List.of();
    }
    
    @Override
    public java.util.Map<String, Object> analyzeMessagePerformance(Long messageId) {
        return java.util.Map.of();
    }
    
    @Override
    public List<java.util.Map<String, Object>> exportMessages(TDeviceMessageSearchDTO queryDTO) {
        return List.of();
    }

    @Override
    public IPage<TDeviceMessageVO> listTDeviceMessagePage(PageQuery pageQuery, com.ljwx.modules.health.domain.bo.TDeviceMessageBO queryBO) {
        LambdaQueryWrapper<TDeviceMessage> wrapper = new LambdaQueryWrapper<>();
        
        if (queryBO != null) {
            wrapper.eq(queryBO.getDeviceSn() != null, TDeviceMessage::getDeviceSn, queryBO.getDeviceSn())
                   .eq(queryBO.getOrgId() != null, TDeviceMessage::getOrgId, queryBO.getOrgId())
                   .eq(queryBO.getCustomerId() != null, TDeviceMessage::getCustomerId, queryBO.getCustomerId());
            
            // Set enum filters directly
            if (queryBO.getMessageType() != null) {
                wrapper.eq(TDeviceMessage::getMessageType, queryBO.getMessageType());
            }
            if (queryBO.getMessageStatus() != null) {
                wrapper.eq(TDeviceMessage::getMessageStatus, queryBO.getMessageStatus());
            }
        }
        
        wrapper.orderByDesc(TDeviceMessage::getCreateTime);
        
        IPage<TDeviceMessage> page = page(pageQuery.buildPage(), wrapper);
        
        // Convert to VO
        return page.convert(this::convertToVO);
    }

    /**
     * 根据userId判断接收者类型
     */
    private ReceiverTypeEnum determineReceiverType(String userId) {
        if (userId == null || userId.trim().isEmpty() || 
            "全部".equals(userId.trim()) || "all".equalsIgnoreCase(userId.trim())) {
            // 用户ID为空或"全部"/"all"时，认为是群组消息
            return ReceiverTypeEnum.GROUP;
        } else {
            // 有具体用户ID时，认为是个人消息
            return ReceiverTypeEnum.USER;
        }
    }

    /**
     * 根据接收者类型和参数动态计算目标数量
     */
    private Integer calculateTargetCount(ReceiverTypeEnum receiverType, String userId, Long orgId, Long customerId) {
        if (receiverType == null) {
            return 1;
        }
        
        try {
            switch (receiverType) {
                case USER:
                case DEVICE:
                    // 个人/设备消息：目标数量为1
                    log.debug("个人/设备消息，target_count=1");
                    return 1;
                    
                case GROUP:
                    // 群组消息：根据orgId查询用户数量
                    if (orgId != null) {
                        Long userCount = getUserCountByOrgId(orgId);
                        log.debug("群组消息，orgId={}, target_count={}", orgId, userCount);
                        return userCount.intValue();
                    }
                    log.debug("群组消息但orgId为空，target_count=1");
                    return 1;
                    
                case BROADCAST:
                    // 广播消息：根据customerId查询所有用户数量
                    if (customerId != null) {
                        Long userCount = getUserCountByCustomerId(customerId);
                        log.debug("广播消息，customerId={}, target_count={}", customerId, userCount);
                        return userCount.intValue();
                    }
                    log.debug("广播消息但customerId为空，target_count=1");
                    return 1;
                    
                default:
                    log.debug("未知接收者类型：{}，target_count=1", receiverType);
                    return 1;
            }
        } catch (Exception e) {
            log.error("计算target_count失败，使用默认值1: receiverType={}, userId={}, orgId={}, customerId={}", 
                      receiverType, userId, orgId, customerId, e);
            return 1;
        }
    }
    
    /**
     * 根据组织ID查询用户数量
     */
    private Long getUserCountByOrgId(Long orgId) {
        try {
            // 使用系统用户服务查询组织下的用户数量
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.ljwx.modules.system.domain.entity.SysUser> wrapper = 
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
            wrapper.eq(com.ljwx.modules.system.domain.entity.SysUser::getOrgId, orgId)
                   .eq(com.ljwx.modules.system.domain.entity.SysUser::getStatus, 1); // 只统计启用用户
            
            Long count = sysUserService.count(wrapper);
            return count > 0 ? count : 1L; // 至少返回1
        } catch (Exception e) {
            log.error("查询组织用户数量失败，orgId={}", orgId, e);
            return 1L;
        }
    }
    
    /**
     * 根据租户ID查询用户数量
     */
    private Long getUserCountByCustomerId(Long customerId) {
        try {
            // 使用系统用户服务查询租户下的用户数量
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.ljwx.modules.system.domain.entity.SysUser> wrapper = 
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
            wrapper.eq(com.ljwx.modules.system.domain.entity.SysUser::getCustomerId, customerId)
                   .eq(com.ljwx.modules.system.domain.entity.SysUser::getStatus, 1); // 只统计启用用户
            
            Long count = sysUserService.count(wrapper);
            return count > 0 ? count : 1L; // 至少返回1
        } catch (Exception e) {
            log.error("查询租户用户数量失败，customerId={}", customerId, e);
            return 1L;
        }
    }
    
    /**
     * 根据用户ID查询用户名
     */
    private String getUserNameById(String userId) {
        try {
            if (userId == null || userId.trim().isEmpty()) {
                return "";
            }
            
            // 查询用户信息
            com.ljwx.modules.system.domain.entity.SysUser user = sysUserService.getById(userId);
            if (user != null && user.getUserName() != null) {
                return user.getUserName();
            }
            
            // 如果查询失败，返回空字符串
            return "";
        } catch (Exception e) {
            log.warn("查询用户名失败，userId={}", userId, e);
            return "";
        }
    }
    
    /**
     * 根据用户ID查询组织名（优先通过sys_user表查询）
     */
    private String getOrgNameByUserId(String userId) {
        try {
            if (userId == null || userId.trim().isEmpty()) {
                return "";
            }
            
            // 查询用户信息，获取orgName
            com.ljwx.modules.system.domain.entity.SysUser user = sysUserService.getById(userId);
            if (user != null && user.getOrgName() != null) {
                return user.getOrgName();
            }
            
            return "";
        } catch (Exception e) {
            log.warn("通过用户ID查询组织名失败，userId={}", userId, e);
            return "";
        }
    }
    
    /**
     * 根据组织ID查询组织名（通过sys_org_units表）
     */
    private String getOrgNameById(Long orgId) {
        try {
            if (orgId == null) {
                return "";
            }
            
            // 先尝试通过组织下的任一用户查询orgName
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.ljwx.modules.system.domain.entity.SysUser> userWrapper = 
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
            userWrapper.eq(com.ljwx.modules.system.domain.entity.SysUser::getOrgId, orgId)
                       .eq(com.ljwx.modules.system.domain.entity.SysUser::getStatus, 1)
                       .last("LIMIT 1");
            
            com.ljwx.modules.system.domain.entity.SysUser user = sysUserService.getOne(userWrapper);
            if (user != null && user.getOrgName() != null && !user.getOrgName().trim().isEmpty()) {
                return user.getOrgName();
            }
            
            // 如果通过用户查询不到，直接查询sys_org_units表
            return getOrgNameFromOrgUnits(orgId);
            
        } catch (Exception e) {
            log.warn("查询组织名失败，orgId={}", orgId, e);
            return "";
        }
    }
    
    /**
     * 从sys_org_units表查询组织名
     */
    private String getOrgNameFromOrgUnits(Long orgId) {
        try {
            if (orgId == null) {
                return "";
            }
            
            // 通过SysOrgUnitsService查询组织信息
            com.ljwx.modules.system.domain.entity.SysOrgUnits orgUnits = sysOrgUnitsService.getById(orgId);
            if (orgUnits != null && orgUnits.getName() != null && !orgUnits.getName().trim().isEmpty()) {
                log.debug("从sys_org_units查询到组织名，orgId={}, orgName={}", orgId, orgUnits.getName());
                return orgUnits.getName();
            }
            
            log.debug("从sys_org_units未查询到组织信息，orgId={}", orgId);
            return "";
            
        } catch (Exception e) {
            log.warn("从sys_org_units查询组织名失败，orgId={}", orgId, e);
            return "";
        }
    }

    /**
     * 转换为VO对象
     */
    private TDeviceMessageVO convertToVO(TDeviceMessage message) {
        TDeviceMessageVO vo = new TDeviceMessageVO();
        BeanUtils.copyProperties(message, vo);
        
        // 设置枚举字段的String值（用于前端显示）
        if (message.getMessageType() != null) {
            vo.setMessageType(message.getMessageType().getCode());
            vo.setMessageTypeName(message.getMessageType().getDisplayName());
        }
        if (message.getSenderType() != null) {
            vo.setSenderType(message.getSenderType().getCode());
            vo.setSenderTypeName(message.getSenderType().getDisplayName());
        } else {
            vo.setSenderType("SYSTEM");
            vo.setSenderTypeName("系统");
        }
        if (message.getReceiverType() != null) {
            vo.setReceiverType(message.getReceiverType().getCode());
            vo.setReceiverTypeName(message.getReceiverType().getDisplayName());
        }
        if (message.getUrgency() != null) {
            vo.setUrgencyName(message.getUrgency().getDisplayName());
        }
        if (message.getMessageStatus() != null) {
            vo.setMessageStatus(message.getMessageStatus().getCode());
            vo.setMessageStatusName(message.getMessageStatus().getDisplayName());
        } else {
            vo.setMessageStatus("PENDING");
            vo.setMessageStatusName("待处理");
        }
        
        // 设置是否过期
        vo.setExpired(message.isExpired());
        
        // 设置targetCount (从实体字段获取)
        vo.setTargetCount(message.getTargetCount() != null ? message.getTargetCount() : 1);
        
        // 根据receiverType设置userName和orgName显示逻辑
        if (message.getReceiverType() == ReceiverTypeEnum.USER) {
            // USER类型：显示userName和orgName（优先通过userId查询）
            if (message.getUserId() != null && !message.getUserId().trim().isEmpty()) {
                String userName = getUserNameById(message.getUserId());
                vo.setUserName(userName);
                
                // 优先通过userId查询orgName
                String orgName = getOrgNameByUserId(message.getUserId());
                if (orgName == null || orgName.trim().isEmpty()) {
                    // 如果通过userId查不到，再通过orgId查询
                    orgName = getOrgNameById(message.getOrgId());
                }
                vo.setOrgName(orgName);
            } else {
                // 没有userId，直接通过orgId查询
                String orgName = getOrgNameById(message.getOrgId());
                vo.setOrgName(orgName);
            }
        } else if (message.getReceiverType() == ReceiverTypeEnum.GROUP) {
            // GROUP类型：只显示orgName，userName为空
            vo.setUserName(""); // 群组消息不显示用户名
            if (message.getOrgId() != null) {
                String orgName = getOrgNameById(message.getOrgId());
                vo.setOrgName(orgName);
            }
        } else {
            // 其他类型：统一处理
            if (message.getUserId() != null && !message.getUserId().trim().isEmpty()) {
                String userName = getUserNameById(message.getUserId());
                vo.setUserName(userName);
                
                // 优先通过userId查询orgName
                String orgName = getOrgNameByUserId(message.getUserId());
                if (orgName == null || orgName.trim().isEmpty()) {
                    orgName = getOrgNameById(message.getOrgId());
                }
                vo.setOrgName(orgName);
            } else if (message.getOrgId() != null) {
                String orgName = getOrgNameById(message.getOrgId());
                vo.setOrgName(orgName);
            }
        }
        
        // 设置respondedDetail（未响应用户列表）
        com.ljwx.modules.health.domain.vo.MessageResponseDetailVO respondedDetail = buildRespondedDetail(message);
        log.info("🔥 convertToVO: messageId={}, respondedDetail={}", message.getId(), respondedDetail);
        vo.setRespondedDetail(respondedDetail);
        
        // 添加JSON序列化测试
        try {
            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            String json = mapper.writeValueAsString(respondedDetail);
            log.info("🔥 JSON序列化测试: {}", json);
        } catch (Exception e) {
            log.error("JSON序列化失败: {}", e.getMessage());
        }
        
        return vo;
    }
    
    /**
     * 构建响应详情信息（完整实现）
     * 根据消息类型和实际确认情况构建未响应用户列表
     */
    private com.ljwx.modules.health.domain.vo.MessageResponseDetailVO buildRespondedDetail(TDeviceMessage message) {
        try {
            com.ljwx.modules.health.domain.vo.MessageResponseDetailVO detail = 
                new com.ljwx.modules.health.domain.vo.MessageResponseDetailVO();
            
            log.debug("构建响应详情: messageId={}, receiverType={}, userId={}, orgId={}", 
                     message.getId(), message.getReceiverType(), message.getUserId(), message.getOrgId());
            
            if (message.getReceiverType() == ReceiverTypeEnum.USER) {
                // 个人消息处理
                buildUserMessageDetail(message, detail);
            } else if (message.getReceiverType() == ReceiverTypeEnum.GROUP) {
                // 群组消息处理
                buildGroupMessageDetail(message, detail);
            } else {
                // 其他类型（DEVICE, BROADCAST等）
                buildOtherMessageDetail(message, detail);
            }
            
            log.debug("响应详情构建完成: totalUsers={}, respondedCount={}, nonRespondedCount={}", 
                     detail.getTotalUsersWithDevices(), detail.getRespondedCount(), 
                     detail.getNonRespondedUsers() != null ? detail.getNonRespondedUsers().size() : 0);
            
            return detail;
        } catch (Exception e) {
            log.error("构建响应详情失败，messageId={}", message.getId(), e);
            return createEmptyDetail();
        }
    }
    
    /**
     * 处理个人消息的响应详情
     */
    private void buildUserMessageDetail(TDeviceMessage message, 
                                        com.ljwx.modules.health.domain.vo.MessageResponseDetailVO detail) {
        if (message.getUserId() == null || message.getUserId().trim().isEmpty()) {
            log.warn("个人消息但userId为空: messageId={}", message.getId());
            detail.setTotalUsersWithDevices(1L);
            detail.setRespondedCount(0);
            detail.setNonRespondedUsers(new ArrayList<>());
            return;
        }
        
        // 设置基本数据
        detail.setTotalUsersWithDevices(1L);
        
        // 查询用户确认状态
        boolean isAcknowledged = checkUserAcknowledgement(message.getId(), message.getUserId());
        detail.setRespondedCount(isAcknowledged ? 1 : 0);
        
        // 如果未确认，添加到未响应列表
        if (!isAcknowledged) {
            List<NonRespondedUserVO> nonRespondedUsers = new ArrayList<>();
            
            NonRespondedUserVO userVO = createNonRespondedUserVO(message.getUserId(), message.getDeviceSn());
            
            if (userVO != null) {
                nonRespondedUsers.add(userVO);
            }
            
            detail.setNonRespondedUsers(nonRespondedUsers);
        } else {
            detail.setNonRespondedUsers(new ArrayList<>());
        }
    }
    
    /**
     * 处理群组消息的响应详情
     */
    private void buildGroupMessageDetail(TDeviceMessage message, 
                                         com.ljwx.modules.health.domain.vo.MessageResponseDetailVO detail) {
        if (message.getOrgId() == null) {
            log.warn("群组消息但orgId为空: messageId={}", message.getId());
            detail.setTotalUsersWithDevices(0L);
            detail.setRespondedCount(0);
            detail.setNonRespondedUsers(new ArrayList<>());
            return;
        }
        
        // 查询组织下所有启用用户
        List<com.ljwx.modules.system.domain.entity.SysUser> allUsers = getActiveUsersByOrgId(message.getOrgId());
        detail.setTotalUsersWithDevices(Long.valueOf(allUsers.size()));
        
        // 查询已确认的用户
        List<String> acknowledgedUserIds = getAcknowledgedUserIds(message.getId());
        detail.setRespondedCount(acknowledgedUserIds.size());
        
        // 构建未响应用户列表
        List<NonRespondedUserVO> nonRespondedUsers = new ArrayList<>();
        
        for (com.ljwx.modules.system.domain.entity.SysUser user : allUsers) {
            String userId = String.valueOf(user.getId());
            if (!acknowledgedUserIds.contains(userId)) {
                // 用户未确认，添加到未响应列表
                NonRespondedUserVO userVO = createNonRespondedUserVOFromSysUser(user);
                
                if (userVO != null) {
                    nonRespondedUsers.add(userVO);
                }
            }
        }
        
        detail.setNonRespondedUsers(nonRespondedUsers);
        
        log.debug("群组消息详情: messageId={}, orgId={}, totalUsers={}, acknowledgedUsers={}, nonRespondedUsers={}", 
                 message.getId(), message.getOrgId(), allUsers.size(), acknowledgedUserIds.size(), nonRespondedUsers.size());
    }
    
    /**
     * 处理其他类型消息的响应详情
     */
    private void buildOtherMessageDetail(TDeviceMessage message, 
                                        com.ljwx.modules.health.domain.vo.MessageResponseDetailVO detail) {
        // 对于DEVICE、BROADCAST等类型，使用targetCount作为总数
        Integer targetCount = message.getTargetCount() != null ? message.getTargetCount() : 1;
        Integer respondedNumber = message.getRespondedNumber() != null ? message.getRespondedNumber() : 0;
        
        detail.setTotalUsersWithDevices(Long.valueOf(targetCount));
        detail.setRespondedCount(respondedNumber);
        
        // 对于非用户类型消息，不显示具体的未响应用户列表
        detail.setNonRespondedUsers(new ArrayList<>());
        
        log.debug("其他类型消息详情: messageId={}, receiverType={}, targetCount={}, respondedNumber={}", 
                 message.getId(), message.getReceiverType(), targetCount, respondedNumber);
    }
    
    /**
     * 检查用户是否已确认消息
     */
    private boolean checkUserAcknowledgement(Long messageId, String userId) {
        try {
            // 首先检查表是否存在
            Long tableExists = getBaseMapper().checkDetailTableExists();
            if (tableExists == null || tableExists == 0) {
                log.warn("t_device_message_detail表不存在，返回未确认状态");
                return false;
            }
            
            // 查询t_device_message_detail表中的确认记录
            Long count = getBaseMapper().checkUserAcknowledgement(messageId, userId);
            
            boolean acknowledged = count != null && count > 0;
            log.debug("用户确认状态查询: messageId={}, userId={}, acknowledged={}", messageId, userId, acknowledged);
            
            return acknowledged;
        } catch (Exception e) {
            log.error("查询用户确认状态失败: messageId={}, userId={}", messageId, userId, e);
            return false;
        }
    }
    
    /**
     * 查询组织下所有启用用户
     */
    private List<com.ljwx.modules.system.domain.entity.SysUser> getActiveUsersByOrgId(Long orgId) {
        try {
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<com.ljwx.modules.system.domain.entity.SysUser> wrapper = 
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>();
            wrapper.eq(com.ljwx.modules.system.domain.entity.SysUser::getOrgId, orgId)
                   .eq(com.ljwx.modules.system.domain.entity.SysUser::getStatus, 1)
                   .orderByAsc(com.ljwx.modules.system.domain.entity.SysUser::getUserName);
            
            List<com.ljwx.modules.system.domain.entity.SysUser> users = sysUserService.list(wrapper);
            log.debug("查询组织用户: orgId={}, userCount={}", orgId, users.size());
            
            return users;
        } catch (Exception e) {
            log.error("查询组织用户失败: orgId={}", orgId, e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 查询已确认消息的用户ID列表
     */
    private List<String> getAcknowledgedUserIds(Long messageId) {
        try {
            // 首先检查表是否存在
            Long tableExists = getBaseMapper().checkDetailTableExists();
            if (tableExists == null || tableExists == 0) {
                log.warn("t_device_message_detail表不存在，返回空的已确认用户列表");
                return new ArrayList<>();
            }
            
            // 查询t_device_message_detail表中已确认的用户
            List<String> acknowledgedUserIds = getBaseMapper().getAcknowledgedUserIds(messageId);
            
            if (acknowledgedUserIds == null) {
                acknowledgedUserIds = new ArrayList<>();
            }
            
            log.debug("查询已确认用户: messageId={}, acknowledgedCount={}", messageId, acknowledgedUserIds.size());
            
            return acknowledgedUserIds;
        } catch (Exception e) {
            log.error("查询已确认用户失败: messageId={}", messageId, e);
            return new ArrayList<>();
        }
    }
    
    /**
     * 根据用户ID创建未响应用户VO
     */
    private NonRespondedUserVO createNonRespondedUserVO(String userId, String deviceSn) {
        try {
            com.ljwx.modules.system.domain.entity.SysUser user = sysUserService.getById(userId);
            if (user != null) {
                return createNonRespondedUserVOFromSysUser(user, deviceSn);
            } else {
                log.warn("未找到用户: userId={}", userId);
                return null;
            }
        } catch (Exception e) {
            log.error("创建用户VO失败: userId={}", userId, e);
            return null;
        }
    }
    
    /**
     * 根据SysUser实体创建未响应用户VO
     */
    private NonRespondedUserVO createNonRespondedUserVOFromSysUser(com.ljwx.modules.system.domain.entity.SysUser user) {
        return createNonRespondedUserVOFromSysUser(user, "");
    }
    
    /**
     * 根据SysUser实体创建未响应用户VO（带设备信息）
     */
    private NonRespondedUserVO createNonRespondedUserVOFromSysUser(com.ljwx.modules.system.domain.entity.SysUser user, String deviceSn) {
        try {
            NonRespondedUserVO userVO = new NonRespondedUserVO();
            
            // 设置用户名
            userVO.setUserName(user.getUserName() != null && !user.getUserName().trim().isEmpty() 
                              ? user.getUserName() : "用户_" + user.getId());
            
            // 设置部门名称（优先使用orgName，如果为空则查询orgId）
            String departmentName = "";
            if (user.getOrgName() != null && !user.getOrgName().trim().isEmpty()) {
                departmentName = user.getOrgName();
            } else if (user.getOrgId() != null) {
                departmentName = getOrgNameById(user.getOrgId());
            }
            userVO.setDepartmentName(departmentName);
            
            // 设置设备信息
            userVO.setDeviceSn(deviceSn != null ? deviceSn : "");
            
            return userVO;
        } catch (Exception e) {
            log.error("创建用户VO失败: userId={}", user.getId(), e);
            return null;
        }
    }
    
    /**
     * 创建空的响应详情对象
     */
    private com.ljwx.modules.health.domain.vo.MessageResponseDetailVO createEmptyDetail() {
        com.ljwx.modules.health.domain.vo.MessageResponseDetailVO detail = 
            new com.ljwx.modules.health.domain.vo.MessageResponseDetailVO();
        detail.setTotalUsersWithDevices(0L);
        detail.setRespondedCount(0);
        detail.setNonRespondedUsers(new ArrayList<>());
        return detail;
    }
}