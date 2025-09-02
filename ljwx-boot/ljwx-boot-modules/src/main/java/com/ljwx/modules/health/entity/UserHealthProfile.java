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
 * 用户健康画像实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_user_health_profile")
public class UserHealthProfile implements Serializable {

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
     * 画像日期
     */
    @TableField("profile_date")
    private LocalDate profileDate;

    /**
     * 综合健康评分
     */
    @TableField("overall_health_score")
    private BigDecimal overallHealthScore;

    /**
     * 健康等级
     */
    @TableField("health_level")
    private String healthLevel;

    /**
     * 生理指标评分
     */
    @TableField("physiological_score")
    private BigDecimal physiologicalScore;

    /**
     * 行为模式评分
     */
    @TableField("behavioral_score")
    private BigDecimal behavioralScore;

    /**
     * 风险因子评分
     */
    @TableField("risk_factor_score")
    private BigDecimal riskFactorScore;

    /**
     * 心血管评分
     */
    @TableField("cardiovascular_score")
    private BigDecimal cardiovascularScore;

    /**
     * 呼吸系统评分
     */
    @TableField("respiratory_score")
    private BigDecimal respiratoryScore;

    /**
     * 代谢功能评分
     */
    @TableField("metabolic_score")
    private BigDecimal metabolicScore;

    /**
     * 心理健康评分
     */
    @TableField("psychological_score")
    private BigDecimal psychologicalScore;

    /**
     * 运动一致性评分
     */
    @TableField("activity_consistency_score")
    private BigDecimal activityConsistencyScore;

    /**
     * 睡眠质量评分
     */
    @TableField("sleep_quality_score")
    private BigDecimal sleepQualityScore;

    /**
     * 健康参与度评分
     */
    @TableField("health_engagement_score")
    private BigDecimal healthEngagementScore;

    /**
     * 当前风险等级
     */
    @TableField("current_risk_level")
    private String currentRiskLevel;

    /**
     * 预测风险评分
     */
    @TableField("predicted_risk_score")
    private BigDecimal predictedRiskScore;

    /**
     * 详细分析数据(JSON)
     */
    @TableField("detailed_analysis")
    private String detailedAnalysis;

    /**
     * 趋势分析数据(JSON)
     */
    @TableField("trend_analysis")
    private String trendAnalysis;

    /**
     * 个性化建议(JSON)
     */
    @TableField("recommendations")
    private String recommendations;

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

    /**
     * 版本号
     */
    @TableField("version")
    private Integer version;
}