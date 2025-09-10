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

import com.ljwx.common.api.Result;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageAddDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageSearchDTO;
import com.ljwx.modules.health.domain.dto.device.message.TDeviceMessageUpdateDTO;
import com.ljwx.modules.health.domain.vo.TDeviceMessageVO;
import com.ljwx.modules.health.domain.vo.v2.TDeviceMessageV2VO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageCreateV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageQueryV2DTO;
import com.ljwx.modules.health.domain.dto.v2.message.MessageUpdateV2DTO;
import com.ljwx.modules.health.domain.enums.MessageStatusEnum;
import com.ljwx.modules.health.domain.enums.MessageTypeEnum;
import com.ljwx.modules.health.domain.enums.SenderTypeEnum;
import com.ljwx.modules.health.domain.enums.UrgencyEnum;
import com.ljwx.modules.health.service.ITDeviceMessageV2Service;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 消息兼容性控制器 - V1到V2的兼容层
 * 
 * 功能：
 * 1. 保持V1 API接口不变
 * 2. 内部使用V2服务处理
 * 3. 数据格式转换和适配
 * 4. 渐进式迁移支持
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.admin.controller.health.MessageCompatibilityController
 * @CreateTime 2025-09-10 18:00:00
 */
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("t_device_message")
@Tag(name = "设备消息兼容性", description = "V1到V2的兼容性接口")
public class MessageCompatibilityController {

    private final ITDeviceMessageV2Service messageV2Service;

    /**
     * V1分页查询接口 - 兼容原有逻辑
     */
    @GetMapping("/page")
    @Operation(summary = "分页查询消息(V1兼容)", description = "保持V1接口兼容性，内部使用V2处理")
    public Result<RPage<TDeviceMessageVO>> page(
            @Parameter(description = "分页对象") @Valid PageQuery pageQuery,
            @Parameter(description = "查询对象") TDeviceMessageSearchDTO searchDTO) {
        
        log.debug("V1兼容-分页查询: pageQuery={}, searchDTO={}", pageQuery, searchDTO);
        
        // 转换V1查询参数为V2格式
        MessageQueryV2DTO queryV2DTO = convertToV2Query(searchDTO);
        
        // 调用V2服务
        var v2Result = messageV2Service.pageMessages(pageQuery, queryV2DTO);
        
        // 转换V2结果为V1格式
        List<TDeviceMessageVO> v1VOs = v2Result.getRecords().stream()
                .map(this::convertToV1VO)
                .collect(Collectors.toList());
        
        RPage<TDeviceMessageVO> v1Page = new RPage<>(
                v2Result.getCurrent(),
                v2Result.getSize(),
                v1VOs,
                v2Result.getPages(),
                v2Result.getTotal()
        );
        
        return Result.data(v1Page);
    }

    /**
     * V1根据ID获取消息接口
     */
    @GetMapping("/{id}")
    @Operation(summary = "根据ID获取消息(V1兼容)")
    public Result<TDeviceMessageVO> get(@Parameter(description = "ID") @PathVariable("id") Long id) {
        
        log.debug("V1兼容-根据ID获取消息: id={}", id);
        
        TDeviceMessageV2VO v2VO = messageV2Service.getMessageById(id);
        if (v2VO == null) {
            return Result.failure("消息不存在");
        }
        
        TDeviceMessageVO v1VO = convertToV1VO(v2VO);
        return Result.data(v1VO);
    }

    /**
     * V1新增消息接口
     */
    @PostMapping("/")
    @Operation(summary = "新增消息(V1兼容)")
    public Result<Boolean> add(@Parameter(description = "新增对象") @RequestBody TDeviceMessageAddDTO addDTO) {
        
        log.info("V1兼容-新增消息: addDTO={}", addDTO);
        
        // 设置默认时间
        if (addDTO.getSentTime() == null) {
            addDTO.setSentTime(LocalDateTime.now());
        }
        if (addDTO.getReceivedTime() == null) {
            addDTO.setReceivedTime(LocalDateTime.now());
        }
        
        // 转换V1参数为V2格式
        MessageCreateV2DTO createV2DTO = convertToV2Create(addDTO);
        
        // 调用V2服务
        Long messageId = messageV2Service.createMessage(createV2DTO);
        
        return Result.status(messageId != null);
    }

    /**
     * V1更新消息接口
     */
    @PutMapping("/")
    @Operation(summary = "更新消息(V1兼容)")
    public Result<Boolean> update(@Parameter(description = "更新对象") @RequestBody TDeviceMessageUpdateDTO updateDTO) {
        
        log.info("V1兼容-更新消息: updateDTO={}", updateDTO);
        
        // 转换V1参数为V2格式
        MessageUpdateV2DTO updateV2DTO = convertToV2Update(updateDTO);
        
        // 调用V2服务
        boolean success = messageV2Service.updateMessage(updateV2DTO);
        
        return Result.status(success);
    }

    /**
     * V1批量删除消息接口
     */
    @DeleteMapping("/")
    @Operation(summary = "批量删除消息(V1兼容)")
    public Result<Boolean> batchDelete(@Parameter(description = "删除对象") @RequestBody Map<String, Object> deleteData) {
        
        @SuppressWarnings("unchecked")
        List<Long> ids = (List<Long>) deleteData.get("ids");
        
        log.info("V1兼容-批量删除消息: ids={}", ids);
        
        // 调用V2服务
        boolean success = messageV2Service.batchDeleteMessages(ids);
        
        return Result.status(success);
    }

    // ==================== V1到V2数据转换方法 ====================

    /**
     * 转换V1查询参数为V2格式
     */
    private MessageQueryV2DTO convertToV2Query(TDeviceMessageSearchDTO searchDTO) {
        MessageQueryV2DTO queryV2DTO = new MessageQueryV2DTO();
        
        if (searchDTO != null) {
            BeanUtils.copyProperties(searchDTO, queryV2DTO);
            
            // 转换枚举类型
            if (searchDTO.getMessageType() != null) {
                queryV2DTO.setMessageType(MessageTypeEnum.getByCode(searchDTO.getMessageType()));
            }
            if (searchDTO.getStatus() != null) {
                queryV2DTO.setMessageStatus(MessageStatusEnum.getByCode(searchDTO.getStatus()));
            }
        }
        
        return queryV2DTO;
    }

    /**
     * 转换V1创建参数为V2格式
     */
    private MessageCreateV2DTO convertToV2Create(TDeviceMessageAddDTO addDTO) {
        MessageCreateV2DTO createV2DTO = new MessageCreateV2DTO();
        
        BeanUtils.copyProperties(addDTO, createV2DTO);
        
        // 转换枚举类型
        if (addDTO.getMessageType() != null) {
            createV2DTO.setMessageType(MessageTypeEnum.getByCode(addDTO.getMessageType()));
        }
        if (addDTO.getSenderType() != null) {
            createV2DTO.setSenderType(SenderTypeEnum.getByCode(addDTO.getSenderType()));
        }
        if (addDTO.getMessageStatus() != null) {
            createV2DTO.setMessageStatus(MessageStatusEnum.getByCode(addDTO.getMessageStatus()));
        }
        
        // 设置默认值
        if (createV2DTO.getMessageType() == null) {
            createV2DTO.setMessageType(MessageTypeEnum.NOTIFICATION);
        }
        if (createV2DTO.getSenderType() == null) {
            createV2DTO.setSenderType(SenderTypeEnum.SYSTEM);
        }
        if (createV2DTO.getUrgency() == null) {
            createV2DTO.setUrgency(UrgencyEnum.MEDIUM);
        }
        
        return createV2DTO;
    }

    /**
     * 转换V1更新参数为V2格式
     */
    private MessageUpdateV2DTO convertToV2Update(TDeviceMessageUpdateDTO updateDTO) {
        MessageUpdateV2DTO updateV2DTO = new MessageUpdateV2DTO();
        
        BeanUtils.copyProperties(updateDTO, updateV2DTO);
        
        // 转换枚举类型
        if (updateDTO.getMessageType() != null) {
            updateV2DTO.setMessageType(MessageTypeEnum.getByCode(updateDTO.getMessageType()));
        }
        if (updateDTO.getSenderType() != null) {
            updateV2DTO.setSenderType(SenderTypeEnum.getByCode(updateDTO.getSenderType()));
        }
        if (updateDTO.getMessageStatus() != null) {
            updateV2DTO.setMessageStatus(MessageStatusEnum.getByCode(updateDTO.getMessageStatus()));
        }
        
        return updateV2DTO;
    }

    /**
     * 转换V2结果为V1格式
     */
    private TDeviceMessageVO convertToV1VO(TDeviceMessageV2VO v2VO) {
        TDeviceMessageVO v1VO = new TDeviceMessageVO();
        
        // 复制基本属性
        v1VO.setId(v2VO.getId());
        v1VO.setDeviceSn(v2VO.getDeviceSn());
        v1VO.setTitle(v2VO.getTitle());
        v1VO.setMessage(v2VO.getMessage());
        v1VO.setOrgId(v2VO.getOrgId());
        v1VO.setUserId(v2VO.getUserId());
        v1VO.setCustomerId(v2VO.getCustomerId());
        v1VO.setRespondedNumber(v2VO.getRespondedNumber());
        v1VO.setSentTime(v2VO.getSentTime());
        v1VO.setReceivedTime(v2VO.getReceivedTime());
        v1VO.setCreateTime(v2VO.getCreateTime());
        v1VO.setUpdateTime(v2VO.getUpdateTime());
        
        // 转换枚举为字符串
        if (v2VO.getMessageType() != null) {
            v1VO.setMessageType(v2VO.getMessageType().getCode());
        }
        if (v2VO.getSenderType() != null) {
            v1VO.setSenderType(v2VO.getSenderType().getCode());
        }
        if (v2VO.getReceiverType() != null) {
            v1VO.setReceiverType(v2VO.getReceiverType().getCode());
        }
        if (v2VO.getMessageStatus() != null) {
            v1VO.setMessageStatus(v2VO.getMessageStatus().getCode());
        }
        
        return v1VO;
    }

    // ==================== 兼容性扩展接口 ====================

    /**
     * 获取消息统计 - V1兼容格式
     */
    @GetMapping("/statistics")
    @Operation(summary = "获取消息统计(V1兼容)")
    public Result<Map<String, Object>> getStatistics(
            @Parameter(description = "设备序列号") @RequestParam(required = false) String deviceSn,
            @Parameter(description = "用户ID") @RequestParam(required = false) String userId) {
        
        log.debug("V1兼容-获取消息统计: deviceSn={}, userId={}", deviceSn, userId);
        
        // 获取V2统计数据
        var v2Stats = messageV2Service.getMessageStatistics(null, null, null, null);
        
        // 转换为V1格式
        Map<String, Object> v1Stats = new HashMap<>();
        if (v2Stats != null) {
            v1Stats.put("totalMessages", v2Stats.getTotalMessages());
            v1Stats.put("deliveredCount", v2Stats.getDeliveredCount());
            v1Stats.put("acknowledgedCount", v2Stats.getAcknowledgedCount());
            v1Stats.put("failedCount", v2Stats.getFailedCount());
            v1Stats.put("deliveryRate", v2Stats.getDeliveryRate());
            v1Stats.put("acknowledgmentRate", v2Stats.getAcknowledgmentRate());
        }
        
        return Result.data(v1Stats);
    }

    /**
     * 确认消息 - V1兼容接口
     */
    @PostMapping("/{messageId}/acknowledge")
    @Operation(summary = "确认消息(V1兼容)")
    public Result<Boolean> acknowledgeMessageV1(
            @Parameter(description = "消息ID") @PathVariable Long messageId,
            @Parameter(description = "设备序列号") @RequestParam String deviceSn) {
        
        log.info("V1兼容-确认消息: messageId={}, deviceSn={}", messageId, deviceSn);
        
        // 调用V2服务
        boolean success = messageV2Service.acknowledgeMessage(messageId, deviceSn, "message");
        
        return Result.status(success);
    }

    /**
     * 获取设备未读消息数量 - V1兼容
     */
    @GetMapping("/unread-count/{deviceSn}")
    @Operation(summary = "获取未读数量(V1兼容)")
    public Result<Long> getUnreadCountV1(@Parameter(description = "设备序列号") @PathVariable String deviceSn) {
        
        log.debug("V1兼容-获取未读数量: deviceSn={}", deviceSn);
        
        // 调用V2服务
        Long count = messageV2Service.getUnreadCount(deviceSn, "device");
        
        return Result.data(count);
    }

    /**
     * 根据设备获取消息列表 - V1兼容
     */
    @GetMapping("/device/{deviceSn}/messages")
    @Operation(summary = "获取设备消息列表(V1兼容)")
    public Result<List<TDeviceMessageVO>> getDeviceMessagesV1(
            @Parameter(description = "设备序列号") @PathVariable String deviceSn,
            @Parameter(description = "限制数量") @RequestParam(defaultValue = "50") Integer limit) {
        
        log.debug("V1兼容-获取设备消息: deviceSn={}, limit={}", deviceSn, limit);
        
        // 调用V2服务
        List<TDeviceMessageV2VO> v2Messages = messageV2Service.getMessagesByDevice(deviceSn, limit);
        
        // 转换为V1格式
        List<TDeviceMessageVO> v1Messages = v2Messages.stream()
                .map(this::convertToV1VO)
                .collect(Collectors.toList());
        
        return Result.data(v1Messages);
    }

    // ==================== 健康检查接口 ====================

    /**
     * V1兼容性健康检查
     */
    @GetMapping("/health-check")
    @Operation(summary = "兼容性健康检查", description = "检查V1到V2的兼容性状态")
    public Result<Map<String, Object>> healthCheck() {
        
        Map<String, Object> status = new HashMap<>();
        status.put("v1_compatible", true);
        status.put("v2_service_available", true);
        status.put("timestamp", System.currentTimeMillis());
        status.put("version", "V2-Compatible");
        
        try {
            // 尝试调用V2服务检查可用性
            messageV2Service.getMessageStatistics(1L, null, null, null);
            status.put("v2_service_status", "OK");
        } catch (Exception e) {
            status.put("v2_service_status", "ERROR");
            status.put("v2_service_error", e.getMessage());
            log.error("V2服务健康检查失败", e);
        }
        
        return Result.data(status);
    }

    /**
     * 获取API版本信息
     */
    @GetMapping("/version")
    @Operation(summary = "获取API版本信息")
    public Result<Map<String, Object>> getVersion() {
        
        Map<String, Object> version = new HashMap<>();
        version.put("api_version", "V1-Compatible");
        version.put("backend_version", "V2");
        version.put("compatible_mode", true);
        version.put("migration_status", "ACTIVE");
        version.put("deprecation_notice", "V1 API将在未来版本中弃用，建议迁移到V2 API");
        
        return Result.data(version);
    }
}