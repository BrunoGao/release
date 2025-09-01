package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.UserHealthData;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 用户健康数据Mapper接口
 */
@Mapper
public interface UserHealthDataMapper extends BaseMapper<UserHealthData> {

    /**
     * 查询用户在指定时间范围内的健康数据
     */
    @Select("SELECT * FROM t_user_health_data WHERE user_id = #{userId} " +
            "AND timestamp BETWEEN #{startTime} AND #{endTime} AND is_deleted = 0 " +
            "ORDER BY timestamp ASC")
    List<UserHealthData> getHealthDataByTimeRange(@Param("userId") Long userId,
                                                 @Param("startTime") LocalDateTime startTime,
                                                 @Param("endTime") LocalDateTime endTime);

    /**
     * 查询用户最新的健康数据
     */
    @Select("SELECT * FROM t_user_health_data WHERE user_id = #{userId} AND is_deleted = 0 " +
            "ORDER BY timestamp DESC LIMIT 1")
    UserHealthData getLatestHealthData(@Param("userId") Long userId);

    /**
     * 按日期分组统计健康数据
     */
    List<Map<String, Object>> getDailyHealthStats(@Param("userId") Long userId,
                                                 @Param("startDate") LocalDate startDate,
                                                 @Param("endDate") LocalDate endDate);

    /**
     * 查询群体健康数据统计
     */
    List<Map<String, Object>> getPopulationHealthStats(@Param("customerId") Long customerId,
                                                      @Param("ageGroup") String ageGroup,
                                                      @Param("gender") String gender,
                                                      @Param("startTime") LocalDateTime startTime,
                                                      @Param("endTime") LocalDateTime endTime);

    /**
     * 查询用户健康数据统计摘要
     */
    @Select("SELECT " +
            "COUNT(*) as total_records, " +
            "AVG(heart_rate) as avg_heart_rate, " +
            "AVG(blood_oxygen) as avg_blood_oxygen, " +
            "AVG(pressure_high) as avg_pressure_high, " +
            "AVG(pressure_low) as avg_pressure_low, " +
            "AVG(temperature) as avg_temperature, " +
            "AVG(stress) as avg_stress, " +
            "AVG(step) as avg_steps, " +
            "AVG(sleep) as avg_sleep " +
            "FROM t_user_health_data WHERE user_id = #{userId} " +
            "AND timestamp >= #{startTime} AND is_deleted = 0")
    Map<String, Object> getUserHealthSummary(@Param("userId") Long userId, @Param("startTime") LocalDateTime startTime);
}