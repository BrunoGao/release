package com.ljwx.modules.health.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 健康基线实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_baseline")
public class HealthBaseline implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 设备序列号
     */
    @TableField("device_sn")
    private String deviceSn;

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
     * 健康特征名称
     */
    @TableField("feature_name")
    private String featureName;

    /**
     * 基线日期
     */
    @TableField("baseline_date")
    private LocalDate baselineDate;

    /**
     * 基线类型：personal|population|position
     */
    @TableField("baseline_type")
    private String baselineType;

    /**
     * 年龄组
     */
    @TableField("age_group")
    private String ageGroup;

    /**
     * 性别
     */
    @TableField("gender")
    private String gender;

    /**
     * 职位风险等级
     */
    @TableField("position_risk_level")
    private String positionRiskLevel;

    /**
     * 均值
     */
    @TableField("mean_value")
    private BigDecimal meanValue;

    /**
     * 标准差
     */
    @TableField("std_value")
    private BigDecimal stdValue;

    /**
     * 最小值
     */
    @TableField("min_value")
    private BigDecimal minValue;

    /**
     * 最大值
     */
    @TableField("max_value")
    private BigDecimal maxValue;

    /**
     * 样本数量
     */
    @TableField("sample_count")
    private Integer sampleCount;

    /**
     * 季节调整因子
     */
    @TableField("seasonal_factor")
    private BigDecimal seasonalFactor;

    /**
     * 置信水平
     */
    @TableField("confidence_level")
    private BigDecimal confidenceLevel;

    /**
     * 基线时间
     */
    @TableField("baseline_time")
    private LocalDate baselineTime;

    /**
     * 是否为当前基线
     */
    @TableField("is_current")
    private Integer isCurrent;

    /**
     * 是否删除
     */
    @TableField("is_deleted")
    @TableLogic
    private Integer isDeleted;
}