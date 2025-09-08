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
 * 健康预测实体类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.entity.HealthPrediction
 * @CreateTime 2025-09-08
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_prediction")
public class HealthPrediction implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 用户ID
     */
    @TableField("user_id")
    private Long userId;

    /**
     * 客户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 设备序列号
     */
    @TableField("device_sn")
    private String deviceSn;

    /**
     * 组织ID
     */
    @TableField("org_id")
    private Long orgId;

    /**
     * 预测类型 (trend, risk, anomaly)
     */
    @TableField("prediction_type")
    private String predictionType;

    /**
     * 健康特征名称
     */
    @TableField("feature_name")
    private String featureName;

    /**
     * 预测日期
     */
    @TableField("prediction_date")
    private LocalDate predictionDate;

    /**
     * 预测值
     */
    @TableField("predicted_value")
    private BigDecimal predictedValue;

    /**
     * 置信度 (0-1)
     */
    @TableField("confidence_score")
    private BigDecimal confidenceScore;

    /**
     * 风险等级 (low, medium, high)
     */
    @TableField("risk_level")
    private String riskLevel;

    /**
     * 预测模型版本
     */
    @TableField("model_version")
    private String modelVersion;

    /**
     * 预测准确率
     */
    @TableField("accuracy_rate")
    private BigDecimal accuracyRate;

    /**
     * 预测描述
     */
    @TableField("description")
    private String description;

    /**
     * 预测元数据 (JSON格式)
     */
    @TableField("metadata")
    private String metadata;

    /**
     * 是否有效
     */
    @TableField("is_valid")
    private Boolean valid;

    /**
     * 预测有效期至
     */
    @TableField("valid_until")
    private LocalDateTime validUntil;

    /**
     * 模型类型
     */
    @TableField("model_type")
    private String modelType;

    /**
     * 预测开始日期
     */
    @TableField("prediction_start_date")
    private LocalDate predictionStartDate;

    /**
     * 预测结束日期
     */
    @TableField("prediction_end_date")
    private LocalDate predictionEndDate;

    /**
     * 预测周期天数
     */
    @TableField("prediction_horizon_days")
    private Integer predictionHorizonDays;

    /**
     * 预测状态 (pending, completed, failed)
     */
    @TableField("prediction_status")
    private String predictionStatus;

    /**
     * 创建人
     */
    @TableField("created_by")
    private String createdBy;

    /**
     * 预测详情 (JSON格式)
     */
    @TableField("prediction_details")
    private String predictionDetails;

    /**
     * 预测值 (JSON格式)
     */
    @TableField("predicted_values")
    private String predictedValues;
}