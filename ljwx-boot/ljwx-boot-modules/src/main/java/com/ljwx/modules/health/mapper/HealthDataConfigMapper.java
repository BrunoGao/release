package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthDataConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 健康数据配置Mapper接口
 */
@Mapper
public interface HealthDataConfigMapper extends BaseMapper<HealthDataConfig> {

    /**
     * 根据租户ID查询所有启用的配置
     */
    @Select("SELECT * FROM t_health_data_config WHERE customer_id = #{customerId} " +
            "AND is_enabled = 1 AND is_deleted = 0 ORDER BY metric_name")
    List<HealthDataConfig> getEnabledConfigs(@Param("customerId") Long customerId);

    /**
     * 根据指标名称查询配置
     */
    @Select("SELECT * FROM t_health_data_config WHERE customer_id = #{customerId} " +
            "AND metric_name = #{metricName} AND is_deleted = 0 LIMIT 1")
    HealthDataConfig getConfigByMetric(@Param("customerId") Long customerId, @Param("metricName") String metricName);

    /**
     * 批量查询配置
     */
    List<HealthDataConfig> getConfigsByMetrics(@Param("customerId") Long customerId, @Param("metricNames") List<String> metricNames);
}