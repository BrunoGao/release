/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.domain.vo.analytics;

import lombok.Data;
import java.util.Map;

/**
 * 统计摘要数据
 * 提供健康数据分析的总体统计和关键指标摘要
 * 
 * @author Claude Code
 */
@Data
public class StatisticsSummary {
    
    /**
     * 总记录数
     */
    private Integer totalRecords;
    
    /**
     * 有效数据百分比
     */
    private Double validDataPercentage;
    
    /**
     * 分析周期
     */
    private String analysisPeriod;
    
    /**
     * 关键指标
     */
    private Map<String, Object> keyMetrics;
    
    /**
     * 健康评分 (0-100)
     */
    private Double healthScore;
    
    /**
     * 趋势分析
     */
    private Map<String, String> trends;
    
    /**
     * 异常指标数量
     */
    private Integer abnormalMetricsCount;
    
    /**
     * 建议数量
     */
    private Integer recommendationsCount;
    
    /**
     * 数据质量等级
     */
    private String dataQualityGrade; // "A", "B", "C", "D"
    
    /**
     * 分析可信度 (0-100)
     */
    private Double confidenceLevel;
}