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
 * 健康建议跟踪实体类
 */
@Data
@EqualsAndHashCode(callSuper = false)
@Accessors(chain = true)
@TableName("t_health_recommendation_track")
public class HealthRecommendationTrack implements Serializable {

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
     * 建议ID
     */
    @TableField("recommendation_id")
    private String recommendationId;

    /**
     * 建议类型
     */
    @TableField("recommendation_type")
    private String recommendationType;

    /**
     * 标题
     */
    @TableField("title")
    private String title;

    /**
     * 描述
     */
    @TableField("description")
    private String description;

    /**
     * 推荐动作(JSON)
     */
    @TableField("recommended_actions")
    private String recommendedActions;

    /**
     * 状态
     */
    @TableField("status")
    private String status;

    /**
     * 开始日期
     */
    @TableField("start_date")
    private LocalDate startDate;

    /**
     * 目标完成日期
     */
    @TableField("target_completion_date")
    private LocalDate targetCompletionDate;

    /**
     * 实际完成日期
     */
    @TableField("actual_completion_date")
    private LocalDate actualCompletionDate;

    /**
     * 效果评分
     */
    @TableField("effectiveness_score")
    private BigDecimal effectivenessScore;

    /**
     * 用户反馈
     */
    @TableField("user_feedback")
    private String userFeedback;

    /**
     * 健康改善指标(JSON)
     */
    @TableField("health_improvement_metrics")
    private String healthImprovementMetrics;

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