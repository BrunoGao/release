package com.ljwx.modules.health.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 用户健康数据实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_user_health_data")
public class UserHealthData implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 用户ID
     */
    @TableField("user_id")
    private Long userId;

    /**
     * 设备序列号
     */
    @TableField("device_sn")
    private String deviceSn;

    /**
     * 租户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 数据时间戳
     */
    @TableField("timestamp")
    private LocalDateTime timestamp;

    /**
     * 心率
     */
    @TableField("heart_rate")
    private Integer heartRate;

    /**
     * 血氧
     */
    @TableField("blood_oxygen")
    private Integer bloodOxygen;

    /**
     * 高压
     */
    @TableField("pressure_high")
    private Integer pressureHigh;

    /**
     * 低压
     */
    @TableField("pressure_low")
    private Integer pressureLow;

    /**
     * 体温
     */
    @TableField("temperature")
    private BigDecimal temperature;

    /**
     * 压力值
     */
    @TableField("stress")
    private Integer stress;

    /**
     * 步数
     */
    @TableField("step")
    private Integer step;

    /**
     * 睡眠时间(分钟)
     */
    @TableField("sleep")
    private Integer sleep;

    /**
     * 距离
     */
    @TableField("distance")
    private BigDecimal distance;

    /**
     * 卡路里
     */
    @TableField("calorie")
    private BigDecimal calorie;

    /**
     * 创建时间
     */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    /**
     * 是否删除
     */
    @TableField("is_deleted")
    @TableLogic
    private Integer isDeleted;
}