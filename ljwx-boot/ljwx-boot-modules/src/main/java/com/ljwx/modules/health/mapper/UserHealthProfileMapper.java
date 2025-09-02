package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.UserHealthProfile;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 用户健康画像Mapper接口
 */
@Mapper
public interface UserHealthProfileMapper extends BaseMapper<UserHealthProfile> {

    /**
     * 查询用户最新的健康画像
     */
    @Select("SELECT * FROM t_user_health_profile WHERE user_id = #{userId} AND is_deleted = 0 " +
            "ORDER BY profile_date DESC LIMIT 1")
    UserHealthProfile getLatestProfile(@Param("userId") Long userId);

    /**
     * 查询指定日期的用户健康画像
     */
    @Select("SELECT * FROM t_user_health_profile WHERE user_id = #{userId} AND profile_date = #{profileDate} " +
            "AND is_deleted = 0 LIMIT 1")
    UserHealthProfile getProfileByDate(@Param("userId") Long userId, @Param("profileDate") LocalDate profileDate);

    /**
     * 查询用户画像历史
     */
    @Select("SELECT * FROM t_user_health_profile WHERE user_id = #{userId} " +
            "AND profile_date BETWEEN #{startDate} AND #{endDate} AND is_deleted = 0 " +
            "ORDER BY profile_date DESC")
    List<UserHealthProfile> getProfileHistory(@Param("userId") Long userId,
                                             @Param("startDate") LocalDate startDate,
                                             @Param("endDate") LocalDate endDate);

    /**
     * 查询健康等级分布统计
     */
    @Select("SELECT health_level, COUNT(*) as count FROM t_user_health_profile " +
            "WHERE customer_id = #{customerId} AND profile_date = #{profileDate} AND is_deleted = 0 " +
            "GROUP BY health_level")
    List<Map<String, Object>> getHealthLevelDistribution(@Param("customerId") Long customerId, 
                                                         @Param("profileDate") LocalDate profileDate);

    /**
     * 查询风险等级分布统计
     */
    @Select("SELECT current_risk_level, COUNT(*) as count FROM t_user_health_profile " +
            "WHERE customer_id = #{customerId} AND profile_date = #{profileDate} AND is_deleted = 0 " +
            "GROUP BY current_risk_level")
    List<Map<String, Object>> getRiskLevelDistribution(@Param("customerId") Long customerId, 
                                                       @Param("profileDate") LocalDate profileDate);
}