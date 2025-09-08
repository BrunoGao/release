package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthPrediction;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 健康预测 Mapper 接口
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.mapper.HealthPredictionMapper
 * @CreateTime 2025-09-08
 */
@Mapper
public interface HealthPredictionMapper extends BaseMapper<HealthPrediction> {

    /**
     * 根据用户ID和时间范围查询健康预测
     */
    List<HealthPrediction> selectByUserIdAndDateRange(
            @Param("userId") Long userId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);

    /**
     * 根据客户ID和预测类型查询预测记录
     */
    List<HealthPrediction> selectByCustomerIdAndType(
            @Param("customerId") Long customerId,
            @Param("predictionType") String predictionType,
            @Param("limit") Integer limit);

    /**
     * 查询指定用户的最新预测记录
     */
    List<HealthPrediction> selectLatestByUserId(
            @Param("userId") Long userId,
            @Param("limit") Integer limit);

    /**
     * 批量插入预测记录
     */
    int batchInsert(@Param("predictions") List<HealthPrediction> predictions);

    /**
     * 清理过期的预测记录
     */
    int deleteExpiredPredictions(@Param("cutoffDate") LocalDate cutoffDate);

    /**
     * 统计预测准确率
     */
    List<Map<String, Object>> selectAccuracyStatistics(
            @Param("customerId") Long customerId,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);
}