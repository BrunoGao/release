/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 * For educational purposes only, commercial use shall comply with the author's copyright information.
 * The author does not guarantee or assume any responsibility for the risks of using software.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ljwx.modules.health.service;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * Health Analytics Service 健康数据分析服务接口
 *
 * @Author jjgao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.HealthAnalyticsService
 * @CreateTime 2025-01-15
 */
public interface HealthAnalyticsService {

    /**
     * 计算健康指标统计信息
     *
     * @param customerId 客户ID
     * @param orgId 组织ID
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @param timeType 时间类型
     * @return 健康指标统计信息
     */
    Map<String, Object> calculateHealthMetrics(Long customerId, String orgId, String userId, 
                                               LocalDateTime startDate, LocalDateTime endDate, String timeType);

    /**
     * 计算健康评分
     *
     * @param customerId 客户ID
     * @param orgId 组织ID
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @return 健康评分信息
     */
    Map<String, Object> calculateHealthScore(Long customerId, String orgId, String userId, 
                                             LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 生成健康建议
     *
     * @param customerId 客户ID
     * @param orgId 组织ID
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @return 健康建议信息
     */
    Map<String, Object> generateHealthRecommendations(Long customerId, String orgId, String userId, 
                                                       LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 分析健康趋势
     *
     * @param customerId 客户ID
     * @param orgId 组织ID
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @param metricType 指标类型
     * @return 健康趋势分析
     */
    Map<String, Object> analyzeHealthTrends(Long customerId, String orgId, String userId, 
                                             LocalDateTime startDate, LocalDateTime endDate, String metricType);

    /**
     * 获取综合健康分析
     *
     * @param customerId 客户ID
     * @param orgId 组织ID
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @param timeType 时间类型
     * @return 综合健康分析
     */
    Map<String, Object> getComprehensiveAnalysis(Long customerId, String orgId, String userId, 
                                                  LocalDateTime startDate, LocalDateTime endDate, String timeType);
}