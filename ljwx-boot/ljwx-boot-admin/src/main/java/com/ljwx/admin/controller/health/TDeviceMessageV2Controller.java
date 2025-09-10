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

package com.ljwx.admin.controller.health;

import cn.dev33.satoken.annotation.SaCheckPermission;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import com.ljwx.modules.health.domain.dto.v2.message.MessageCreateV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageQueryV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageUpdateV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageAckV2DTO;
import com.ljwx.modules.health.domain.vo.v2.MessageStatisticsV2VO;
import com.ljwx.modules.health.domain.vo.v2.MessageSummaryV2VO;
import com.ljwx.modules.health.domain.vo.v2.TDeviceMessageV2VO;
import com.ljwx.modules.health.service.ITDeviceMessageV2Service;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 设备消息V2控制器 - 高性能API接口
 * 
 * 特性：
 * 1. RESTful API设计
 * 2. 批量操作支持
 * 3. 高性能查询接口
 * 4. 统计分析接口
 * 5. 向下兼容V1接口
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.health.TDeviceMessageV2Controller
 * @CreateTime 2025-09-10 17:45:00
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/messages")
@Tag(name = "设备消息V2", description = "设备消息V2管理接口")
@Validated
public class TDeviceMessageV2Controller {

    private final ITDeviceMessageV2Service messageV2Service;

    // ==================== 基础CRUD接口 ====================

    /**
     * 分页查询消息 - 高性能版本
     */
    @GetMapping
    @SaCheckPermission("message:v2:page")
    @Operation(summary = "分页查询消息", description = "支持多条件查询和排序")
    public Result<RPage<TDeviceMessageV2VO>> pageMessages(
            @Parameter(description = "分页参数") @Valid PageQuery pageQuery,
            @Parameter(description = "查询条件") MessageQueryV2DTO queryDTO) {
        
        log.debug("分页查询消息V2: pageQuery={}, queryDTO={}", pageQuery, queryDTO);
        
        IPage<TDeviceMessageV2VO> result = messageV2Service.pageMessages(pageQuery, queryDTO);
        return Result.data(RPage.build(result));
    }

    /**
     * 根据ID获取消息详情
     */
    @GetMapping("/{messageId}")
    @SaCheckPermission("message:v2:detail")
    @Operation(summary = "获取消息详情", description = "根据消息ID获取详细信息")
    public Result<TDeviceMessageV2VO> getMessageById(
            @Parameter(description = "消息ID") @PathVariable Long messageId) {
        
        log.debug("获取消息详情: messageId={}", messageId);
        
        TDeviceMessageV2VO message = messageV2Service.getMessageById(messageId);
        return message != null ? Result.data(message) : Result.failure("消息不存在");
    }

    /**
     * 创建消息
     */
    @PostMapping
    @SaCheckPermission("message:v2:create")
    @Operation(summary = "创建消息", description = "创建新消息并支持自动分发")
    public Result<Long> createMessage(
            @Parameter(description = "消息创建信息") @RequestBody @Valid MessageCreateV2DTO createDTO) {
        
        log.info("创建消息V2: {}", createDTO);
        
        Long messageId = messageV2Service.createMessage(createDTO);
        return Result.data(messageId);
    }

    /**
     * 批量创建消息
     */
    @PostMapping("/batch")
    @SaCheckPermission("message:v2:batch-create")
    @Operation(summary = "批量创建消息", description = "批量创建多条消息，提升创建效率")
    public Result<List<Long>> batchCreateMessages(
            @Parameter(description = "批量消息创建信息") @RequestBody @Valid List<MessageCreateV2DTO> createDTOs) {
        
        log.info("批量创建消息V2: 数量={}", createDTOs.size());
        
        List<Long> messageIds = messageV2Service.batchCreateMessages(createDTOs);
        return Result.data(messageIds);
    }

    /**
     * 更新消息
     */
    @PutMapping("/{messageId}")
    @SaCheckPermission("message:v2:update")
    @Operation(summary = "更新消息", description = "更新消息信息")
    public Result<Boolean> updateMessage(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "消息更新信息") @RequestBody @Valid MessageUpdateV2DTO updateDTO) {
        
        log.info("更新消息V2: messageId={}, updateDTO={}", messageId, updateDTO);
        
        updateDTO.setId(messageId);
        boolean success = messageV2Service.updateMessage(updateDTO);
        return Result.status(success);
    }

    /**
     * 删除消息
     */
    @DeleteMapping("/{messageId}")
    @SaCheckPermission("message:v2:delete")
    @Operation(summary = "删除消息", description = "软删除指定消息")
    public Result<Boolean> deleteMessage(
            @Parameter(description = "消息ID") @PathVariable Long messageId) {
        
        log.info("删除消息V2: messageId={}", messageId);
        
        boolean success = messageV2Service.deleteMessage(messageId);
        return Result.status(success);
    }

    /**
     * 批量删除消息
     */
    @DeleteMapping("/batch")
    @SaCheckPermission("message:v2:batch-delete")
    @Operation(summary = "批量删除消息", description = "批量软删除多条消息")
    public Result<Boolean> batchDeleteMessages(
            @Parameter(description = "消息ID列表") @RequestBody List<Long> messageIds) {
        
        log.info("批量删除消息V2: messageIds={}", messageIds);
        
        boolean success = messageV2Service.batchDeleteMessages(messageIds);
        return Result.status(success);
    }

    // ==================== 消息分发接口 ====================

    /**
     * 发送消息到设备
     */
    @PostMapping("/{messageId}/send-to-device")
    @SaCheckPermission("message:v2:send")
    @Operation(summary = "发送消息到设备", description = "将消息发送到指定设备")
    public Result<Boolean> sendToDevice(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "设备序列号") @RequestParam String deviceSn) {
        
        log.info("发送消息到设备: messageId={}, deviceSn={}", messageId, deviceSn);
        
        boolean success = messageV2Service.sendToDevice(messageId, deviceSn);
        return Result.status(success);
    }

    /**
     * 发送消息到用户
     */
    @PostMapping("/{messageId}/send-to-user")
    @SaCheckPermission("message:v2:send")
    @Operation(summary = "发送消息到用户", description = "将消息发送到指定用户的所有设备")
    public Result<Boolean> sendToUser(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "用户ID") @RequestParam String userId) {
        
        log.info("发送消息到用户: messageId={}, userId={}", messageId, userId);
        
        boolean success = messageV2Service.sendToUser(messageId, userId);
        return Result.status(success);
    }

    /**
     * 发送消息到部门
     */
    @PostMapping("/{messageId}/send-to-department")
    @SaCheckPermission("message:v2:send")
    @Operation(summary = "发送消息到部门", description = "将消息群发到指定部门")
    public Result<Boolean> sendToDepartment(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "部门ID") @RequestParam Long orgId) {
        
        log.info("发送消息到部门: messageId={}, orgId={}", messageId, orgId);
        
        boolean success = messageV2Service.sendToDepartment(messageId, orgId);
        return Result.status(success);
    }

    /**
     * 批量分发消息
     */
    @PostMapping("/{messageId}/batch-distribute")
    @SaCheckPermission("message:v2:send")
    @Operation(summary = "批量分发消息", description = "将消息批量分发到多个目标")
    public Result<Map<String, Object>> batchDistributeMessage(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "目标列表") @RequestBody List<String> targets,
            @Parameter(description = "目标类型") @RequestParam String targetType) {
        
        log.info("批量分发消息: messageId={}, targetType={}, targets数量={}", messageId, targetType, targets.size());
        
        Map<String, Object> result = messageV2Service.batchDistributeMessage(messageId, targets, targetType);
        return Result.data(result);
    }

    // ==================== 消息状态管理接口 ====================

    /**
     * 确认消息
     */
    @PostMapping("/{messageId}/acknowledge")
    @SaCheckPermission("message:v2:ack")
    @Operation(summary = "确认消息", description = "确认指定消息")
    public Result<Boolean> acknowledgeMessage(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "确认请求信息") @RequestBody @Valid MessageAckV2DTO ackDTO) {
        
        log.info("确认消息: messageId={}, ackDTO={}", messageId, ackDTO);
        
        boolean success = messageV2Service.acknowledgeMessage(messageId, ackDTO.getTargetId(), ackDTO.getChannel());
        return Result.status(success);
    }

    /**
     * 批量确认消息
     */
    @PostMapping("/batch-acknowledge")
    @SaCheckPermission("message:v2:batch-ack")
    @Operation(summary = "批量确认消息", description = "批量确认多条消息")
    public Result<Boolean> batchAcknowledgeMessages(
            @Parameter(description = "批量确认请求") @RequestBody Map<String, Object> requestData) {
        
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> requests = (List<Map<String, Object>>) requestData.get("requests");
        
        log.info("批量确认消息: 数量={}", requests.size());
        
        for (Map<String, Object> request : requests) {
            Integer messageId = (Integer) request.get("message_id");
            String targetId = (String) request.get("target_id");
            String channel = (String) request.get("channel");
            
            if (messageId != null && targetId != null) {
                messageV2Service.acknowledgeMessage(messageId.longValue(), targetId, channel);
            }
        }
        
        return Result.success("批量确认完成");
    }

    /**
     * 标记消息为已送达
     */
    @PostMapping("/{messageId}/mark-delivered")
    @SaCheckPermission("message:v2:status")
    @Operation(summary = "标记已送达", description = "标记消息为已送达状态")
    public Result<Boolean> markAsDelivered(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "目标ID") @RequestParam String targetId,
            @Parameter(description = "渠道") @RequestParam(required = false) String channel) {
        
        log.info("标记消息已送达: messageId={}, targetId={}, channel={}", messageId, targetId, channel);
        
        boolean success = messageV2Service.markAsDelivered(messageId, targetId, channel);
        return Result.status(success);
    }

    /**
     * 重发失败的消息
     */
    @PostMapping("/{messageId}/retry")
    @SaCheckPermission("message:v2:retry")
    @Operation(summary = "重发失败消息", description = "重发失败或过期的消息")
    public Result<Boolean> retryFailedMessage(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "目标ID") @RequestParam String targetId) {
        
        log.info("重发失败消息: messageId={}, targetId={}", messageId, targetId);
        
        boolean success = messageV2Service.retryFailedMessage(messageId, targetId);
        return Result.status(success);
    }

    // ==================== 查询接口 ====================

    /**
     * 根据设备获取消息列表
     */
    @GetMapping("/device/{deviceSn}")
    @SaCheckPermission("message:v2:query")
    @Operation(summary = "获取设备消息", description = "获取指定设备的消息列表")
    public Result<List<TDeviceMessageV2VO>> getMessagesByDevice(
            @Parameter(description = "设备序列号") @PathVariable String deviceSn,
            @Parameter(description = "限制数量") @RequestParam(defaultValue = "50") Integer limit) {
        
        log.debug("获取设备消息: deviceSn={}, limit={}", deviceSn, limit);
        
        List<TDeviceMessageV2VO> messages = messageV2Service.getMessagesByDevice(deviceSn, limit);
        return Result.data(messages);
    }

    /**
     * 根据用户获取消息列表
     */
    @GetMapping("/user/{userId}")
    @SaCheckPermission("message:v2:query")
    @Operation(summary = "获取用户消息", description = "获取指定用户的消息列表")
    public Result<List<TDeviceMessageV2VO>> getMessagesByUser(
            @Parameter(description = "用户ID") @PathVariable String userId,
            @Parameter(description = "限制数量") @RequestParam(defaultValue = "50") Integer limit) {
        
        log.debug("获取用户消息: userId={}, limit={}", userId, limit);
        
        List<TDeviceMessageV2VO> messages = messageV2Service.getMessagesByUser(userId, limit);
        return Result.data(messages);
    }

    /**
     * 获取组织消息列表
     */
    @GetMapping("/organization/{customerId}")
    @SaCheckPermission("message:v2:query")
    @Operation(summary = "获取组织消息", description = "获取指定组织的消息列表")
    public Result<RPage<TDeviceMessageV2VO>> getOrganizationMessages(
            @Parameter(description = "租户ID") @PathVariable Long customerId,
            @Parameter(description = "组织ID") @RequestParam(required = false) Long orgId,
            @Parameter(description = "分页参数") @Valid PageQuery pageQuery) {
        
        log.debug("获取组织消息: customerId={}, orgId={}", customerId, orgId);
        
        IPage<TDeviceMessageV2VO> result = messageV2Service.getOrganizationMessages(customerId, orgId, pageQuery);
        return Result.data(RPage.build(result));
    }

    /**
     * 获取未读消息数量
     */
    @GetMapping("/unread-count")
    @SaCheckPermission("message:v2:query")
    @Operation(summary = "获取未读数量", description = "获取指定目标的未读消息数量")
    public Result<Long> getUnreadCount(
            @Parameter(description = "目标ID") @RequestParam String targetId,
            @Parameter(description = "目标类型") @RequestParam String targetType) {
        
        Long count = messageV2Service.getUnreadCount(targetId, targetType);
        return Result.data(count);
    }

    // ==================== 统计分析接口 ====================

    /**
     * 获取消息统计信息
     */
    @GetMapping("/statistics")
    @SaCheckPermission("message:v2:stats")
    @Operation(summary = "获取消息统计", description = "获取消息统计信息")
    public Result<MessageStatisticsV2VO> getMessageStatistics(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId,
            @Parameter(description = "组织ID") @RequestParam(required = false) Long orgId,
            @Parameter(description = "开始时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        
        log.debug("获取消息统计: customerId={}, orgId={}, 时间范围: {} - {}", 
                 customerId, orgId, startTime, endTime);
        
        MessageStatisticsV2VO statistics = messageV2Service.getMessageStatistics(customerId, orgId, startTime, endTime);
        return Result.data(statistics);
    }

    /**
     * 获取消息汇总信息
     */
    @GetMapping("/{messageId}/summary")
    @SaCheckPermission("message:v2:stats")
    @Operation(summary = "获取消息汇总", description = "获取指定消息的汇总统计信息")
    public Result<MessageSummaryV2VO> getMessageSummary(
            @Parameter(description = "消息ID") @PathVariable Long messageId) {
        
        log.debug("获取消息汇总: messageId={}", messageId);
        
        MessageSummaryV2VO summary = messageV2Service.getMessageSummary(messageId);
        return Result.data(summary);
    }

    /**
     * 获取渠道分发统计
     */
    @GetMapping("/channel-statistics")
    @SaCheckPermission("message:v2:stats")
    @Operation(summary = "获取渠道统计", description = "获取各渠道的分发统计信息")
    public Result<Map<String, Object>> getChannelStatistics(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId,
            @Parameter(description = "开始时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        
        Map<String, Object> statistics = messageV2Service.getChannelStatistics(customerId, startTime, endTime);
        return Result.data(statistics);
    }

    /**
     * 获取响应时间统计
     */
    @GetMapping("/response-time-statistics")
    @SaCheckPermission("message:v2:stats")
    @Operation(summary = "获取响应时间统计", description = "获取消息响应时间统计信息")
    public Result<Map<String, Object>> getResponseTimeStatistics(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId,
            @Parameter(description = "消息类型") @RequestParam(required = false) String messageType,
            @Parameter(description = "开始时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        
        Map<String, Object> statistics = messageV2Service.getResponseTimeStatistics(
                customerId, messageType, startTime, endTime);
        return Result.data(statistics);
    }

    /**
     * 获取消息类型分布
     */
    @GetMapping("/type-distribution")
    @SaCheckPermission("message:v2:stats")
    @Operation(summary = "获取消息类型分布", description = "获取消息类型分布统计")
    public Result<Map<String, Long>> getMessageTypeDistribution(
            @Parameter(description = "租户ID") @RequestParam(required = false) Long customerId,
            @Parameter(description = "开始时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime startTime,
            @Parameter(description = "结束时间") @RequestParam(required = false) 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime endTime) {
        
        Map<String, Long> distribution = messageV2Service.getMessageTypeDistribution(customerId, startTime, endTime);
        return Result.data(distribution);
    }

    // ==================== 管理接口 ====================

    /**
     * 清理过期消息
     */
    @DeleteMapping("/cleanup/expired")
    @SaCheckPermission("message:v2:manage")
    @Operation(summary = "清理过期消息", description = "清理指定时间之前的过期消息")
    public Result<Integer> cleanupExpiredMessages(
            @Parameter(description = "截止时间") @RequestParam 
            @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss") LocalDateTime before) {
        
        log.info("清理过期消息: before={}", before);
        
        int count = messageV2Service.cleanupExpiredMessages(before);
        return Result.data(count);
    }

    /**
     * 清理已完成消息
     */
    @DeleteMapping("/cleanup/completed")
    @SaCheckPermission("message:v2:manage")
    @Operation(summary = "清理已完成消息", description = "清理指定天数之前的已完成消息")
    public Result<Integer> cleanupCompletedMessages(
            @Parameter(description = "保留天数") @RequestParam(defaultValue = "30") int retentionDays) {
        
        log.info("清理已完成消息: retentionDays={}", retentionDays);
        
        int count = messageV2Service.cleanupCompletedMessages(retentionDays);
        return Result.data(count);
    }

    /**
     * 预热消息缓存
     */
    @PostMapping("/cache/warmup")
    @SaCheckPermission("message:v2:manage")
    @Operation(summary = "预热消息缓存", description = "预热指定租户的消息缓存")
    public Result<Void> warmupMessageCache(
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        log.info("预热消息缓存: customerId={}", customerId);
        
        messageV2Service.warmupMessageCache(customerId);
        return Result.success("缓存预热完成");
    }

    /**
     * 刷新统计缓存
     */
    @PostMapping("/cache/refresh-statistics")
    @SaCheckPermission("message:v2:manage")
    @Operation(summary = "刷新统计缓存", description = "刷新指定租户的统计缓存")
    public Result<Void> refreshStatisticsCache(
            @Parameter(description = "租户ID") @RequestParam Long customerId) {
        
        log.info("刷新统计缓存: customerId={}", customerId);
        
        messageV2Service.refreshStatisticsCache(customerId);
        return Result.success("统计缓存刷新完成");
    }

    /**
     * 批量导出消息
     */
    @PostMapping("/export")
    @SaCheckPermission("message:v2:export")
    @Operation(summary = "批量导出消息", description = "根据查询条件批量导出消息")
    public Result<List<Map<String, Object>>> exportMessages(
            @Parameter(description = "查询条件") @RequestBody MessageQueryV2DTO queryDTO) {
        
        log.info("批量导出消息: queryDTO={}", queryDTO);
        
        List<Map<String, Object>> messages = messageV2Service.exportMessages(queryDTO);
        return Result.data(messages);
    }
}