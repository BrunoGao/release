package com.ljwx.modules.health.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 健康数据配置实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_data_config")
public class HealthDataConfig implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 租户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 指标名称
     */
    @TableField("metric_name")
    private String metricName;

    /**
     * 指标权重
     */
    @TableField("weight")
    private BigDecimal weight;

    /**
     * 目标值
     */
    @TableField("target_value")
    private BigDecimal targetValue;

    /**
     * 最小阈值
     */
    @TableField("min_threshold")
    private BigDecimal minThreshold;

    /**
     * 最大阈值
     */
    @TableField("max_threshold")
    private BigDecimal maxThreshold;

    /**
     * 单位
     */
    @TableField("unit")
    private String unit;

    /**
     * 是否启用
     */
    @TableField("is_enabled")
    private Integer isEnabled;

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