package com.ljwx.modules.health.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ljwx.modules.health.entity.HealthPredictionModelConfig;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Map;

/**
 * 健康预测模型配置 Mapper 接口
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.mapper.HealthPredictionModelConfigMapper
 * @CreateTime 2025-09-08
 */
@Mapper
public interface HealthPredictionModelConfigMapper extends BaseMapper<HealthPredictionModelConfig> {

    /**
     * 根据客户ID和预测类型查询模型配置
     */
    List<HealthPredictionModelConfig> selectByCustomerIdAndType(
            @Param("customerId") Long customerId,
            @Param("predictionType") String predictionType);

    /**
     * 根据特征名称和客户ID查询模型配置
     */
    HealthPredictionModelConfig selectByFeatureAndCustomer(
            @Param("featureName") String featureName,
            @Param("customerId") Long customerId);

    /**
     * 查询启用的模型配置
     */
    List<HealthPredictionModelConfig> selectEnabledConfigs(
            @Param("customerId") Long customerId);

    /**
     * 根据算法类型查询模型配置
     */
    List<HealthPredictionModelConfig> selectByAlgorithmType(
            @Param("algorithmType") String algorithmType);

    /**
     * 更新模型最后训练时间
     */
    int updateLastTrainedTime(
            @Param("id") Long id,
            @Param("lastTrainedAt") String lastTrainedAt,
            @Param("trainingDataVersion") String trainingDataVersion);

    /**
     * 根据条件查询模型配置
     */
    List<HealthPredictionModelConfig> selectByCondition(Map<String, Object> condition);
}