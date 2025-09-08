package com.ljwx.modules.health.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 健康预测模型配置实体类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.entity.HealthPredictionModelConfig
 * @CreateTime 2025-09-08
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_prediction_model_config")
public class HealthPredictionModelConfig implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private Long id;

    /**
     * 客户ID
     */
    @TableField("customer_id")
    private Long customerId;

    /**
     * 模型名称
     */
    @TableField("model_name")
    private String modelName;

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
     * 模型版本
     */
    @TableField("model_version")
    private String modelVersion;

    /**
     * 模型类型 (trend, risk, anomaly)
     */
    @TableField("model_type")
    private String modelType;

    /**
     * 算法类型 (linear_regression, polynomial, neural_network)
     */
    @TableField("algorithm_type")
    private String algorithmType;

    /**
     * 训练数据天数
     */
    @TableField("training_days")
    private Integer trainingDays;

    /**
     * 预测天数
     */
    @TableField("prediction_days")
    private Integer predictionDays;

    /**
     * 最小置信度阈值
     */
    @TableField("min_confidence_threshold")
    private BigDecimal minConfidenceThreshold;

    /**
     * 最大预测误差阈值
     */
    @TableField("max_error_threshold")
    private BigDecimal maxErrorThreshold;

    /**
     * 模型参数 (JSON格式)
     */
    @TableField("model_parameters")
    private String modelParameters;

    /**
     * 特征权重配置 (JSON格式)
     */
    @TableField("feature_weights")
    private String featureWeights;

    /**
     * 风险阈值配置 (JSON格式)
     */
    @TableField("risk_thresholds")
    private String riskThresholds;

    /**
     * 是否启用
     */
    @TableField("enabled")
    private Boolean enabled;

    /**
     * 模型描述
     */
    @TableField("description")
    private String description;

    /**
     * 最后训练时间
     */
    @TableField("last_trained_at")
    private String lastTrainedAt;

    /**
     * 训练数据版本
     */
    @TableField("training_data_version")
    private String trainingDataVersion;
}