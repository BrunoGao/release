package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthRecommendationTrack;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 健康建议跟踪Mapper接口
 */
@Mapper
public interface HealthRecommendationTrackMapper extends BaseMapper<HealthRecommendationTrack> {

    /**
     * 查询用户的建议跟踪记录
     */
    @Select("SELECT * FROM t_health_recommendation_track WHERE user_id = #{userId} " +
            "AND status = #{status} AND is_deleted = 0 ORDER BY create_time DESC")
    List<HealthRecommendationTrack> getUserRecommendations(@Param("userId") Long userId, @Param("status") String status);

    /**
     * 查询待完成的建议
     */
    @Select("SELECT * FROM t_health_recommendation_track WHERE user_id = #{userId} " +
            "AND status IN ('pending', 'in_progress') AND is_deleted = 0 " +
            "ORDER BY target_completion_date ASC")
    List<HealthRecommendationTrack> getPendingRecommendations(@Param("userId") Long userId);

    /**
     * 查询建议执行统计
     */
    @Select("SELECT " +
            "recommendation_type, " +
            "COUNT(*) as total_count, " +
            "COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count, " +
            "AVG(effectiveness_score) as avg_effectiveness " +
            "FROM t_health_recommendation_track WHERE customer_id = #{customerId} " +
            "AND start_date >= #{startDate} AND is_deleted = 0 " +
            "GROUP BY recommendation_type")
    List<Map<String, Object>> getRecommendationStats(@Param("customerId") Long customerId, @Param("startDate") LocalDate startDate);

    /**
     * 查询用户建议完成率
     */
    @Select("SELECT " +
            "COUNT(*) as total_recommendations, " +
            "COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_recommendations, " +
            "AVG(effectiveness_score) as avg_effectiveness " +
            "FROM t_health_recommendation_track WHERE user_id = #{userId} AND is_deleted = 0")
    Map<String, Object> getUserRecommendationSummary(@Param("userId") Long userId);
}