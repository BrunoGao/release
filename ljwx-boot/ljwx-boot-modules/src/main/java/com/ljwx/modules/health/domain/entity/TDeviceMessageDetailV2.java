package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import org.springframework.format.annotation.DateTimeFormat;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 消息详情表V2 - 基于userId直接关联
 * 
 * @author ljwx-system
 * @since 2025-08-31
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
@TableName("t_device_message_detail_v2")
@Schema(name = "TDeviceMessageDetailV2", description = "消息详情表V2-基于userId直接关联")
public class TDeviceMessageDetailV2 implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "主键ID")
    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    @Schema(description = "主消息ID", required = true)
    @TableField("message_id")
    private Long messageId;

    @Schema(description = "租户ID（继承）", required = true)
    @TableField("customer_id")
    private Long customerId;

    @Schema(description = "响应用户ID - 主关联字段", required = true)
    @TableField("user_id")
    private Long userId;

    @Schema(description = "响应设备序列号（冗余）")
    @TableField("device_sn")
    private String deviceSn;

    @Schema(description = "响应消息内容")
    @TableField("response_message")
    private String responseMessage;

    @Schema(description = "响应类型", required = true)
    @TableField("response_type")
    @Builder.Default
    private String responseType = "acknowledged";

    @Schema(description = "响应时间")
    @TableField("response_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime responseTime;

    @Schema(description = "传递状态", required = true)
    @TableField("delivery_status")
    @Builder.Default
    private String deliveryStatus = "pending";

    @Schema(description = "传递尝试次数")
    @TableField("delivery_attempt_count")
    @Builder.Default
    private Integer deliveryAttemptCount = 0;

    @Schema(description = "最后传递时间")
    @TableField("last_delivery_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime lastDeliveryTime;

    @Schema(description = "传递错误信息")
    @TableField("delivery_error")
    private String deliveryError;

    @Schema(description = "客户端信息")
    @TableField("client_info")
    private String clientInfo;

    @Schema(description = "响应位置信息")
    @TableField("response_location")
    private String responseLocation;

    @Schema(description = "创建时间")
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime createTime;

    @Schema(description = "更新时间")
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime updateTime;

    @Schema(description = "删除标记")
    @TableField("is_deleted")
    @TableLogic
    @Builder.Default
    private Integer isDeleted = 0;
}