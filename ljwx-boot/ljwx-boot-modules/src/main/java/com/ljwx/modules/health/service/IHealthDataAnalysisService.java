package com.ljwx.modules.health.service;

import com.ljwx.modules.health.domain.dto.user.health.data.HealthDataAnalysisDTO;
import com.ljwx.modules.health.domain.vo.HealthDataAnalysisVO;

public interface IHealthDataAnalysisService {
    
    /**
     * 分析健康数据
     *
     * @param analysisDTO 分析参数
     * @return 分析结果
     */
    HealthDataAnalysisVO analyzeHealthData(HealthDataAnalysisDTO analysisDTO);
} 