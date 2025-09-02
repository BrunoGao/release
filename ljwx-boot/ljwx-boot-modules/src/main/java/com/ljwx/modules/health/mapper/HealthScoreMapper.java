package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthScore;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 健康评分Mapper接口
 */
@Mapper
public interface HealthScoreMapper extends BaseMapper<HealthScore> {

    /**
     * 查询用户最新的健康评分
     */
    @Select("SELECT * FROM t_health_score WHERE user_id = #{userId} AND feature_name = #{featureName} " +
            "AND is_deleted = 0 ORDER BY score_date DESC LIMIT 1")
    HealthScore getLatestScore(@Param("userId") Long userId, @Param("featureName") String featureName);

    /**
     * 查询用户在指定日期的所有评分
     */
    @Select("SELECT * FROM t_health_score WHERE user_id = #{userId} AND score_date = #{scoreDate} " +
            "AND is_deleted = 0 ORDER BY feature_name")
    List<HealthScore> getUserScoresByDate(@Param("userId") Long userId, @Param("scoreDate") LocalDate scoreDate);

    /**
     * 查询用户评分趋势
     */
    @Select("SELECT * FROM t_health_score WHERE user_id = #{userId} AND feature_name = #{featureName} " +
            "AND score_date BETWEEN #{startDate} AND #{endDate} AND is_deleted = 0 " +
            "ORDER BY score_date ASC")
    List<HealthScore> getScoreTrends(@Param("userId") Long userId, 
                                   @Param("featureName") String featureName,
                                   @Param("startDate") LocalDate startDate, 
                                   @Param("endDate") LocalDate endDate);

    /**
     * 查询用户评分统计
     */
    @Select("SELECT " +
            "feature_name, " +
            "AVG(score_value) as avg_score, " +
            "MAX(score_value) as max_score, " +
            "MIN(score_value) as min_score, " +
            "COUNT(*) as record_count " +
            "FROM t_health_score WHERE user_id = #{userId} " +
            "AND score_date >= #{startDate} AND is_deleted = 0 " +
            "GROUP BY feature_name")
    List<Map<String, Object>> getUserScoreStats(@Param("userId") Long userId, @Param("startDate") LocalDate startDate);

    /**
     * 查询群体评分分布
     */
    List<Map<String, Object>> getPopulationScoreDistribution(@Param("customerId") Long customerId,
                                                            @Param("featureName") String featureName,
                                                            @Param("scoreDate") LocalDate scoreDate);
}