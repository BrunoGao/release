package com.ljwx.modules.health.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 健康评分实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_score")
public class HealthScore implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 用户ID
     */
    @TableField("user_id")
    private Long userId;

    /**
     * 租户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 设备序列号
     */
    @TableField("device_sn")
    private String deviceSn;

    /**
     * 特征名称
     */
    @TableField("feature_name")
    private String featureName;

    /**
     * 评分日期
     */
    @TableField("score_date")
    private LocalDate scoreDate;

    /**
     * 评分值
     */
    @TableField("score_value")
    private BigDecimal scoreValue;

    /**
     * 评分等级
     */
    @TableField("score_level")
    private String scoreLevel;

    /**
     * 原始值
     */
    @TableField("raw_value")
    private BigDecimal rawValue;

    /**
     * 基线值
     */
    @TableField("baseline_value")
    private BigDecimal baselineValue;

    /**
     * Z-Score
     */
    @TableField("z_score")
    private BigDecimal zScore;

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