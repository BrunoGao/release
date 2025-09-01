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

package com.ljwx.modules.stream.service.impl;

import com.ljwx.common.api.Result;
import com.ljwx.modules.stream.domain.dto.DeviceMessageSaveRequest;
import com.ljwx.modules.stream.domain.dto.DeviceMessageSendRequest;
import com.ljwx.modules.stream.service.IDeviceMessageService;
import com.ljwx.modules.message.service.IDeviceMessageV2Service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.time.Instant;
import java.time.ZoneId;
import java.util.*;

/**
 * 设备消息处理服务实现
 * 
 * 兼容ljwx-bigscreen的DeviceMessage相关接口，提供设备消息的保存、发送、接收功能
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName DeviceMessageServiceImpl
 * @CreateTime 2024-12-16
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DeviceMessageServiceImpl implements IDeviceMessageService {

    private final IDeviceMessageV2Service deviceMessageV2Service;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> saveMessage(DeviceMessageSaveRequest request) {
        
        log.info("💬 设备消息保存开始: messageId={}, deviceSn={}", request.getMessageId(), request.getDeviceSn());
        log.info("💬 消息详情: {}", request);
        
        try {
            // 基础验证
            if (!StringUtils.hasText(request.getDeviceSn()) && !StringUtils.hasText(request.getUserId())) {
                log.warn("⚠️ 设备SN和用户ID都为空，无法保存消息");
                return Result.failure("设备SN或用户ID至少需要提供一个");
            }
            
            if (!StringUtils.hasText(request.getMessageContent())) {
                log.warn("⚠️ 消息内容为空，无法保存");
                return Result.failure("消息内容不能为空");
            }
            
            // 构建消息数据
            Map<String, Object> messageData = buildMessageData(request);
            
            // 保存消息到数据库
            Long messageId = deviceMessageV2Service.saveMessage(messageData);
            
            if (messageId != null && messageId > 0) {
                log.info("✅ 设备消息保存成功: messageId={}", messageId);
                
                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("messageId", messageId);
                result.put("message", "设备消息保存成功");
                result.put("savedAt", System.currentTimeMillis());
                
                return Result.data(result);
                
            } else {
                log.error("❌ 设备消息保存失败");
                return Result.failure("设备消息保存失败");
            }
            
        } catch (Exception e) {
            log.error("❌ 设备消息保存异常: {}", e.getMessage(), e);
            return Result.failure("设备消息保存失败: " + e.getMessage());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> sendMessage(DeviceMessageSendRequest request) {
        
        log.info("📤 设备消息发送开始: targetDeviceSn={}, messageType={}", request.getTargetDeviceSn(), request.getMessageType());
        log.info("📤 发送详情: {}", request);
        
        try {
            // 基础验证
            if (!StringUtils.hasText(request.getTargetDeviceSn()) && 
                !StringUtils.hasText(request.getTargetUserId()) && 
                (request.getTargetDevices() == null || request.getTargetDevices().isEmpty()) && 
                (request.getTargetUsers() == null || request.getTargetUsers().isEmpty())) {
                
                log.warn("⚠️ 未指定发送目标，无法发送消息");
                return Result.failure("必须指定发送目标（设备SN、用户ID或批量目标）");
            }
            
            if (!StringUtils.hasText(request.getMessageContent())) {
                log.warn("⚠️ 消息内容为空，无法发送");
                return Result.failure("消息内容不能为空");
            }
            
            Map<String, Object> result = new HashMap<>();
            
            // 处理单个目标发送
            if (StringUtils.hasText(request.getTargetDeviceSn()) || StringUtils.hasText(request.getTargetUserId())) {
                Map<String, Object> singleResult = sendSingleMessage(request);
                result.putAll(singleResult);
                result.put("sendType", "single");
                
            } else {
                // 处理批量发送
                Map<String, Object> batchResult = sendBatchMessages(request);
                result.putAll(batchResult);
                result.put("sendType", "batch");
            }
            
            log.info("✅ 设备消息发送完成: {}", result);
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("❌ 设备消息发送异常: {}", e.getMessage(), e);
            return Result.failure("设备消息发送失败: " + e.getMessage());
        }
    }

    @Override
    public Result<Map<String, Object>> receiveMessages(String deviceSn) {
        
        log.info("📥 设备消息接收开始: deviceSn={}", deviceSn);
        
        try {
            if (!StringUtils.hasText(deviceSn)) {
                log.warn("⚠️ 设备SN为空，无法获取消息");
                return Result.failure("设备SN不能为空");
            }
            
            // 获取设备消息列表
            List<Map<String, Object>> messages = deviceMessageV2Service.getMessagesByDeviceSn(deviceSn);
            
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("deviceSn", deviceSn);
            result.put("messageCount", messages != null ? messages.size() : 0);
            result.put("messages", messages != null ? messages : new ArrayList<>());
            result.put("retrievedAt", System.currentTimeMillis());
            
            log.info("✅ 设备消息接收完成: deviceSn={}, 消息数量={}", deviceSn, result.get("messageCount"));
            
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("❌ 设备消息接收异常: {}", e.getMessage(), e);
            return Result.failure("设备消息接收失败: " + e.getMessage());
        }
    }

    /**
     * 构建消息数据
     */
    private Map<String, Object> buildMessageData(DeviceMessageSaveRequest request) {
        Map<String, Object> messageData = new HashMap<>();
        
        messageData.put("messageId", request.getMessageId());
        messageData.put("deviceSn", request.getDeviceSn());
        messageData.put("userId", request.getUserId());
        messageData.put("customerId", request.getCustomerId());
        messageData.put("orgId", request.getOrgId());
        messageData.put("messageType", request.getMessageType() != null ? request.getMessageType() : "TEXT");
        messageData.put("messageContent", request.getMessageContent());
        messageData.put("messageTitle", request.getMessageTitle());
        messageData.put("senderType", request.getSenderType() != null ? request.getSenderType() : "SYSTEM");
        messageData.put("senderId", request.getSenderId());
        messageData.put("receiverType", request.getReceiverType() != null ? request.getReceiverType() : "DEVICE");
        messageData.put("receiverId", request.getReceiverId());
        messageData.put("priority", request.getPriority() != null ? request.getPriority() : 3);
        messageData.put("messageStatus", request.getMessageStatus() != null ? request.getMessageStatus() : "PENDING");
        messageData.put("requireConfirmation", request.getRequireConfirmation() != null ? request.getRequireConfirmation() : false);
        messageData.put("relatedAlertId", request.getRelatedAlertId());
        
        // 时间处理
        if (request.getCreateTime() != null) {
            LocalDateTime createTime = Instant.ofEpochMilli(request.getCreateTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            messageData.put("createTime", createTime);
        } else {
            messageData.put("createTime", LocalDateTime.now());
        }
        
        if (request.getSendTime() != null) {
            LocalDateTime sendTime = Instant.ofEpochMilli(request.getSendTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            messageData.put("sendTime", sendTime);
        }
        
        if (request.getExpireTime() != null) {
            LocalDateTime expireTime = Instant.ofEpochMilli(request.getExpireTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            messageData.put("expireTime", expireTime);
        }
        
        // 扩展属性
        if (request.getAttachments() != null) {
            messageData.put("attachments", request.getAttachments());
        }
        
        if (request.getExtraAttributes() != null) {
            messageData.put("extraAttributes", request.getExtraAttributes());
        }
        
        if (request.getTags() != null) {
            messageData.put("tags", Arrays.asList(request.getTags()));
        }
        
        return messageData;
    }

    /**
     * 发送单个消息
     */
    private Map<String, Object> sendSingleMessage(DeviceMessageSendRequest request) {
        try {
            // 构建发送数据
            Map<String, Object> sendData = buildSendData(request);
            
            // 调用消息发送服务
            boolean sent = deviceMessageV2Service.sendMessage(sendData);
            
            Map<String, Object> result = new HashMap<>();
            result.put("success", sent);
            result.put("target", StringUtils.hasText(request.getTargetDeviceSn()) ? request.getTargetDeviceSn() : request.getTargetUserId());
            result.put("messageType", request.getMessageType());
            result.put("sentCount", sent ? 1 : 0);
            result.put("failedCount", sent ? 0 : 1);
            result.put("message", sent ? "消息发送成功" : "消息发送失败");
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 单个消息发送异常: {}", e.getMessage());
            Map<String, Object> result = new HashMap<>();
            result.put("success", false);
            result.put("error", e.getMessage());
            return result;
        }
    }

    /**
     * 发送批量消息
     */
    private Map<String, Object> sendBatchMessages(DeviceMessageSendRequest request) {
        int sentCount = 0;
        int failedCount = 0;
        List<Map<String, Object>> results = new ArrayList<>();
        
        try {
            // 处理批量设备
            if (request.getTargetDevices() != null) {
                for (String deviceSn : request.getTargetDevices()) {
                    DeviceMessageSendRequest singleRequest = createSingleRequest(request, deviceSn, null);
                    Map<String, Object> singleResult = sendSingleMessage(singleRequest);
                    results.add(singleResult);
                    
                    if ((Boolean) singleResult.get("success")) {
                        sentCount++;
                    } else {
                        failedCount++;
                    }
                }
            }
            
            // 处理批量用户
            if (request.getTargetUsers() != null) {
                for (String userId : request.getTargetUsers()) {
                    DeviceMessageSendRequest singleRequest = createSingleRequest(request, null, userId);
                    Map<String, Object> singleResult = sendSingleMessage(singleRequest);
                    results.add(singleResult);
                    
                    if ((Boolean) singleResult.get("success")) {
                        sentCount++;
                    } else {
                        failedCount++;
                    }
                }
            }
            
            Map<String, Object> batchResult = new HashMap<>();
            batchResult.put("success", true);
            batchResult.put("totalCount", sentCount + failedCount);
            batchResult.put("sentCount", sentCount);
            batchResult.put("failedCount", failedCount);
            batchResult.put("message", String.format("批量消息发送完成: 成功%d, 失败%d", sentCount, failedCount));
            batchResult.put("results", results);
            
            return batchResult;
            
        } catch (Exception e) {
            log.error("❌ 批量消息发送异常: {}", e.getMessage());
            Map<String, Object> result = new HashMap<>();
            result.put("success", false);
            result.put("error", e.getMessage());
            return result;
        }
    }

    /**
     * 构建发送数据
     */
    private Map<String, Object> buildSendData(DeviceMessageSendRequest request) {
        Map<String, Object> sendData = new HashMap<>();
        
        sendData.put("targetDeviceSn", request.getTargetDeviceSn());
        sendData.put("targetUserId", request.getTargetUserId());
        sendData.put("targetOrgId", request.getTargetOrgId());
        sendData.put("messageType", request.getMessageType());
        sendData.put("messageContent", request.getMessageContent());
        sendData.put("messageTitle", request.getMessageTitle());
        sendData.put("senderId", request.getSenderId());
        sendData.put("senderType", request.getSenderType());
        sendData.put("priority", request.getPriority());
        sendData.put("immediate", request.getImmediate());
        sendData.put("requireDeliveryReceipt", request.getRequireDeliveryReceipt());
        sendData.put("requireReadReceipt", request.getRequireReadReceipt());
        sendData.put("retryCount", request.getRetryCount());
        sendData.put("sendChannels", request.getSendChannels());
        sendData.put("templateId", request.getTemplateId());
        sendData.put("templateParams", request.getTemplateParams());
        sendData.put("attachments", request.getAttachments());
        sendData.put("extraAttributes", request.getExtraAttributes());
        sendData.put("customerId", request.getCustomerId());
        
        if (request.getTags() != null) {
            sendData.put("tags", Arrays.asList(request.getTags()));
        }
        
        // 时间处理
        if (request.getScheduledTime() != null) {
            LocalDateTime scheduledTime = Instant.ofEpochMilli(request.getScheduledTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            sendData.put("scheduledTime", scheduledTime);
        }
        
        if (request.getExpireTime() != null) {
            LocalDateTime expireTime = Instant.ofEpochMilli(request.getExpireTime())
                    .atZone(ZoneId.systemDefault())
                    .toLocalDateTime();
            sendData.put("expireTime", expireTime);
        }
        
        return sendData;
    }

    /**
     * 为批量发送创建单个请求
     */
    private DeviceMessageSendRequest createSingleRequest(DeviceMessageSendRequest batchRequest, String deviceSn, String userId) {
        DeviceMessageSendRequest singleRequest = new DeviceMessageSendRequest();
        
        // 复制基础属性
        singleRequest.setMessageType(batchRequest.getMessageType());
        singleRequest.setMessageContent(batchRequest.getMessageContent());
        singleRequest.setMessageTitle(batchRequest.getMessageTitle());
        singleRequest.setSenderId(batchRequest.getSenderId());
        singleRequest.setSenderType(batchRequest.getSenderType());
        singleRequest.setPriority(batchRequest.getPriority());
        singleRequest.setImmediate(batchRequest.getImmediate());
        singleRequest.setScheduledTime(batchRequest.getScheduledTime());
        singleRequest.setExpireTime(batchRequest.getExpireTime());
        singleRequest.setRequireDeliveryReceipt(batchRequest.getRequireDeliveryReceipt());
        singleRequest.setRequireReadReceipt(batchRequest.getRequireReadReceipt());
        singleRequest.setRetryCount(batchRequest.getRetryCount());
        singleRequest.setSendChannels(batchRequest.getSendChannels());
        singleRequest.setTemplateId(batchRequest.getTemplateId());
        singleRequest.setTemplateParams(batchRequest.getTemplateParams());
        singleRequest.setAttachments(batchRequest.getAttachments());
        singleRequest.setExtraAttributes(batchRequest.getExtraAttributes());
        singleRequest.setTags(batchRequest.getTags());
        singleRequest.setCustomerId(batchRequest.getCustomerId());
        
        // 设置特定目标
        singleRequest.setTargetDeviceSn(deviceSn);
        singleRequest.setTargetUserId(userId);
        
        return singleRequest;
    }

}