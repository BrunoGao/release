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

package com.ljwx.modules.health.facade;

import com.ljwx.modules.health.domain.dto.v1.health.*;
import com.ljwx.modules.health.domain.vo.v1.health.*;

import java.util.List;

/**
 * Bigscreen Health Facade Interface - 大屏健康数据门面接口
 *
 * @Author brunoGao
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.facade.IBigscreenHealthFacade
 * @CreateTime 2025-01-01 - 10:00:00
 */
public interface IBigscreenHealthFacade {

    /**
     * 获取健康综合评分
     */
    HealthScoreVO getComprehensiveHealthScore(HealthScoreQueryDTO query);

    /**
     * 获取基线数据图表
     */
    BaselineChartVO getBaselineChart(BaselineChartQueryDTO query);

    /**
     * 生成基线数据
     */
    BaselineGenerateResultVO generateBaseline(BaselineGenerateRequestDTO request);

    /**
     * 根据ID获取健康数据
     */
    HealthDataDetailVO getHealthDataById(String id);

    /**
     * 获取实时健康数据
     */
    RealtimeHealthDataVO getRealtimeHealthData(RealtimeHealthQueryDTO query);

    /**
     * 获取健康趋势数据
     */
    List<HealthTrendVO> getHealthTrends(HealthTrendQueryDTO query);

    /**
     * 获取个人健康评分
     */
    PersonalHealthScoreVO getPersonalHealthScores(PersonalHealthScoreQueryDTO query);

    /**
     * 获取健康建议
     */
    List<HealthRecommendationVO> getHealthRecommendations(String userId);

    /**
     * 获取健康预测
     */
    List<HealthPredictionVO> getHealthPredictions(String userId);
}