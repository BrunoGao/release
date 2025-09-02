package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthBaseline;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;

/**
 * 健康基线Mapper接口
 */
@Mapper
public interface HealthBaselineMapper extends BaseMapper<HealthBaseline> {

    /**
     * 根据用户ID和特征名称查询当前基线
     */
    @Select("SELECT * FROM t_health_baseline WHERE user_id = #{userId} AND feature_name = #{featureName} " +
            "AND is_current = 1 AND is_deleted = 0 ORDER BY baseline_date DESC LIMIT 1")
    HealthBaseline getCurrentBaseline(@Param("userId") Long userId, @Param("featureName") String featureName);

    /**
     * 根据用户ID查询所有当前基线
     */
    @Select("SELECT * FROM t_health_baseline WHERE user_id = #{userId} AND is_current = 1 AND is_deleted = 0")
    List<HealthBaseline> getCurrentBaselines(@Param("userId") Long userId);

    /**
     * 根据基线类型查询基线
     */
    @Select("SELECT * FROM t_health_baseline WHERE baseline_type = #{baselineType} " +
            "AND customer_id = #{customerId} AND is_current = 1 AND is_deleted = 0")
    List<HealthBaseline> getBaselinesByType(@Param("baselineType") String baselineType, @Param("customerId") Long customerId);

    /**
     * 查询群体基线
     */
    @Select("SELECT * FROM t_health_baseline WHERE baseline_type = 'population' " +
            "AND customer_id = #{customerId} AND age_group = #{ageGroup} AND gender = #{gender} " +
            "AND feature_name = #{featureName} AND is_current = 1 AND is_deleted = 0 LIMIT 1")
    HealthBaseline getPopulationBaseline(@Param("customerId") Long customerId, 
                                       @Param("ageGroup") String ageGroup,
                                       @Param("gender") String gender,
                                       @Param("featureName") String featureName);

    /**
     * 批量更新基线状态
     */
    void batchUpdateBaselineStatus(@Param("userIds") List<Long> userIds, @Param("featureName") String featureName);
}