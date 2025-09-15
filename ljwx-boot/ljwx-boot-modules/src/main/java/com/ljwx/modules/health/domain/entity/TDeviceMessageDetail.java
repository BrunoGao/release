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

package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;
import com.ljwx.infrastructure.domain.BaseEntity;
import com.ljwx.modules.health.domain.enums.DeliveryStatusEnum;
import com.ljwx.modules.health.domain.enums.MessageStatusEnum;
import com.ljwx.modules.health.domain.enums.MessageTypeEnum;
import com.ljwx.modules.health.domain.enums.ReceiverTypeEnum;
import com.ljwx.modules.health.domain.enums.SenderTypeEnum;
import com.ljwx.modules.health.domain.enums.ChannelEnum;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 设备消息详情V2实体类 - 分发记录表
 * 
 * 用于记录每条消息的具体分发情况，支持：
 * 1. 消息分发追踪
 * 2. 确认状态管理
 * 3. 渠道分发记录
 * 4. 响应时间统计
 * 
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.domain.entity.TDeviceMessageDetail
 * @CreateTime 2025-09-10 - 15:45:00
 */
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@TableName(value = "t_device_message_detail", autoResultMap = true)
public class TDeviceMessageDetail extends BaseEntity {

    /**
     * 主键ID
     */
    private Long id;

    /**
     * 关联主消息ID
     */
    @TableField("message_id")
    private Long messageId;

    /**
     * 分发唯一标识ID
     */
    @TableField("distribution_id")
    private String distributionId;

    /**
     * 设备序列号
     */
    @TableField("device_sn")
    private String deviceSn;

    /**
     * 消息内容
     */
    @TableField("message")
    private String message;

    /**
     * 消息类型
     */
    @TableField("message_type")
    private MessageTypeEnum messageType;

    /**
     * 发送者类型
     */
    @TableField("sender_type")
    private SenderTypeEnum senderType;

    /**
     * 接收者类型
     */
    @TableField("receiver_type")
    private ReceiverTypeEnum receiverType;

    /**
     * 消息状态
     */
    @TableField("message_status")
    private MessageStatusEnum messageStatus;

    /**
     * 分发状态
     */
    @TableField("delivery_status")
    private DeliveryStatusEnum deliveryStatus;

    /**
     * 发送时间
     */
    @TableField("sent_time")
    private LocalDateTime sentTime;

    /**
     * 接收时间
     */
    @TableField("received_time")
    private LocalDateTime receivedTime;

    /**
     * 确认时间
     */
    @TableField("acknowledge_time")
    private LocalDateTime acknowledgeTime;

    /**
     * 租户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 组织ID
     */
    @TableField("org_id")
    private Long orgId;

    /**
     * 目标类型
     */
    @TableField("target_type")
    private ReceiverTypeEnum targetType;

    /**
     * 目标ID
     */
    @TableField("target_id")
    private String targetId;

    /**
     * 分发渠道
     */
    @TableField("channel")
    private ChannelEnum channel;

    /**
     * 响应时间(秒)
     */
    @TableField("response_time")
    private Integer responseTime;

    /**
     * 分发详情 - JSON存储
     * 包含：attempts, lastAttemptTime, errorMessage, platform, deviceInfo等
     */
    @TableField(value = "delivery_details", typeHandler = JacksonTypeHandler.class)
    private Map<String, Object> deliveryDetails;

    // ==================== 辅助方法 ====================

    /**
     * 计算响应时间
     */
    public void calculateResponseTime() {
        if (sentTime != null && acknowledgeTime != null) {
            this.responseTime = (int) java.time.Duration.between(sentTime, acknowledgeTime).getSeconds();
        }
    }

    /**
     * 设置分发详情
     */
    public void setDeliveryDetail(String key, Object value) {
        if (deliveryDetails == null) {
            deliveryDetails = new java.util.HashMap<>();
        }
        deliveryDetails.put(key, value);
    }

    /**
     * 获取分发详情
     */
    public Object getDeliveryDetail(String key) {
        return deliveryDetails != null ? deliveryDetails.get(key) : null;
    }

    /**
     * 检查是否已确认
     */
    public boolean isAcknowledged() {
        return deliveryStatus == DeliveryStatusEnum.ACKNOWLEDGED;
    }

    /**
     * 检查是否分发成功
     */
    public boolean isDelivered() {
        return deliveryStatus == DeliveryStatusEnum.DELIVERED || 
               deliveryStatus == DeliveryStatusEnum.ACKNOWLEDGED;
    }

    /**
     * 检查是否分发失败
     */
    public boolean isDeliveryFailed() {
        return deliveryStatus == DeliveryStatusEnum.FAILED || 
               deliveryStatus == DeliveryStatusEnum.EXPIRED;
    }

    /**
     * 更新分发状态为已送达
     */
    public void markAsDelivered() {
        this.deliveryStatus = DeliveryStatusEnum.DELIVERED;
        this.receivedTime = LocalDateTime.now();
    }

    /**
     * 更新分发状态为已确认
     */
    public void markAsAcknowledged() {
        this.deliveryStatus = DeliveryStatusEnum.ACKNOWLEDGED;
        this.acknowledgeTime = LocalDateTime.now();
        calculateResponseTime();
    }

    /**
     * 更新分发状态为失败
     */
    public void markAsFailed(String errorMessage) {
        this.deliveryStatus = DeliveryStatusEnum.FAILED;
        setDeliveryDetail("errorMessage", errorMessage);
        setDeliveryDetail("failedTime", LocalDateTime.now());
    }

    /**
     * 增加重试次数
     */
    public void incrementAttempts() {
        Integer attempts = (Integer) getDeliveryDetail("attempts");
        attempts = (attempts == null) ? 1 : attempts + 1;
        setDeliveryDetail("attempts", attempts);
        setDeliveryDetail("lastAttemptTime", LocalDateTime.now());
    }

    /**
     * 获取重试次数
     */
    public int getAttempts() {
        Integer attempts = (Integer) getDeliveryDetail("attempts");
        return attempts == null ? 0 : attempts;
    }

    /**
     * 生成分发ID
     */
    public void generateDistributionId() {
        if (this.distributionId == null && this.messageId != null) {
            this.distributionId = String.format("DIST_%d_%s_%d", 
                messageId, 
                targetId != null ? targetId : deviceSn,
                System.currentTimeMillis());
        }
    }

    /**
     * 设置设备信息
     */
    public void setDeviceInfo(String phoneModel, String watchModel, String appVersion) {
        if (deliveryDetails == null) {
            deliveryDetails = new java.util.HashMap<>();
        }
        Map<String, String> deviceInfo = new java.util.HashMap<>();
        deviceInfo.put("phoneModel", phoneModel);
        deviceInfo.put("watchModel", watchModel);
        deviceInfo.put("appVersion", appVersion);
        deliveryDetails.put("deviceInfo", deviceInfo);
    }
}