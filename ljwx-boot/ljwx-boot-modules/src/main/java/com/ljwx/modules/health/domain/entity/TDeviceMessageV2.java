package com.ljwx.modules.health.domain.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import org.springframework.format.annotation.DateTimeFormat;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备消息表V2 - 基于userId直接关联
 * 
 * @author ljwx-system
 * @since 2025-08-31
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = false)
@TableName("t_device_message_v2")
@Schema(name = "TDeviceMessageV2", description = "设备消息表V2-基于userId直接关联")
public class TDeviceMessageV2 implements Serializable {

    private static final long serialVersionUID = 1L;

    @Schema(description = "主键ID")
    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    @Schema(description = "租户ID", required = true)
    @TableField("customer_id")
    private Long customerId;

    @Schema(description = "部门ID", required = true)
    @TableField("department_id")
    private Long departmentId;

    @Schema(description = "用户ID - 主要关联字段", required = true)
    @TableField("user_id")
    private Long userId;

    @Schema(description = "设备序列号 - 冗余字段，仅用于设备管理")
    @TableField("device_sn")
    private String deviceSn;

    @Schema(description = "消息内容", required = true)
    @TableField("message")
    private String message;

    @Schema(description = "消息类型", required = true)
    @TableField("message_type")
    private String messageType;

    @Schema(description = "发送者类型", required = true)
    @TableField("sender_type")
    private String senderType;

    @Schema(description = "接收者类型", required = true)
    @TableField("receiver_type")
    private String receiverType;

    @Schema(description = "优先级(1-5)", required = true)
    @TableField("priority_level")
    @Builder.Default
    private Integer priorityLevel = 3;

    @Schema(description = "消息状态", required = true)
    @TableField("message_status")
    @Builder.Default
    private String messageStatus = "pending";

    @Schema(description = "发送时间")
    @TableField("sent_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime sentTime;

    @Schema(description = "接收时间")
    @TableField("received_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime receivedTime;

    @Schema(description = "确认时间")
    @TableField("acknowledged_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime acknowledgedTime;

    @Schema(description = "过期时间")
    @TableField("expired_time")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private LocalDateTime expiredTime;

    @Schema(description = "目标用户数（单发=1，群发>1）")
    @TableField("target_user_count")
    @Builder.Default
    private Integer targetUserCount = 1;

    @Schema(description = "已确认用户数")
    @TableField("acknowledged_count")
    @Builder.Default
    private Integer acknowledgedCount = 0;

    @Schema(description = "创建用户ID")
    @TableField("create_user_id")
    private Long createUserId;

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

    @Schema(description = "乐观锁版本号")
    @TableField("version")
    @Version
    @Builder.Default
    private Integer version = 1;
}