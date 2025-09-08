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

package com.ljwx.modules.health.service.example;

import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.service.UnifiedHealthDataQueryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 统一健康数据查询使用示例
 * 展示如何在baseline、score、profile等服务中使用统一查询类
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.example.UnifiedHealthQueryExample
 * @CreateTime 2025-09-08
 */
@Slf4j
@Service
public class UnifiedHealthQueryExample {

    @Autowired
    private UnifiedHealthDataQueryService unifiedQueryService;

    /**
     * 示例1：基线生成服务中的数据查询
     * 查询过去90天的健康数据用于生成基线
     */
    public Map<String, Object> queryDataForBaseline(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusDays(90));
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(10000); // 基线计算需要大量数据
        query.setEnableSharding(true); // 启用分表查询
        query.setQueryMode("all"); // 查询所有数据
        
        log.info("🔍 基线生成 - 查询用户 {} 过去90天的健康数据", userId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例2：评分计算服务中的数据查询
     * 查询最近30天的数据用于计算健康评分
     */
    public Map<String, Object> queryDataForScoring(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusDays(30));
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(5000);
        query.setEnableSharding(true);
        query.setQueryMode("all");
        query.setIncludeStats(true); // 包含统计信息
        
        log.info("🔍 健康评分 - 查询用户 {} 最近30天的健康数据", userId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例3：健康画像生成中的数据查询
     * 需要查询多种类型的数据
     */
    public Map<String, Object> queryDataForProfile(Long customerId, Long userId) {
        // 查询主表数据
        UnifiedHealthQueryDTO mainQuery = new UnifiedHealthQueryDTO();
        mainQuery.setCustomerId(customerId);
        mainQuery.setUserId(userId);
        mainQuery.setStartDate(LocalDateTime.now().minusDays(30));
        mainQuery.setEndDate(LocalDateTime.now());
        mainQuery.setQueryMode("all");
        
        // 查询日汇总数据（睡眠、运动等）
        UnifiedHealthQueryDTO dailyQuery = new UnifiedHealthQueryDTO();
        dailyQuery.setCustomerId(customerId);
        dailyQuery.setUserId(userId);
        dailyQuery.setStartDate(LocalDateTime.now().minusDays(30));
        dailyQuery.setEndDate(LocalDateTime.now());
        dailyQuery.setQueryMode("daily");
        dailyQuery.setMetrics(List.of("sleep_data", "exercise_daily_data", "workout_data"));
        
        log.info("🔍 健康画像 - 查询用户 {} 的综合健康数据", userId);
        
        Map<String, Object> mainData = unifiedQueryService.queryHealthData(mainQuery);
        Map<String, Object> dailyData = unifiedQueryService.queryHealthData(dailyQuery);
        
        return Map.of(
            "mainData", mainData,
            "dailyData", dailyData
        );
    }

    /**
     * 示例4：预测分析中的数据查询
     * 查询特定指标的历史趋势数据
     */
    public Map<String, Object> queryDataForPrediction(Long customerId, Long userId, String metric) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setMetric(metric); // 只查询特定指标
        query.setStartDate(LocalDateTime.now().minusDays(180)); // 查询6个月历史数据
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(10000);
        query.setEnableSharding(true);
        query.setOrderBy("timestamp");
        query.setOrderDirection("asc");
        
        log.info("🔍 健康预测 - 查询用户 {} 指标 {} 的历史趋势数据", userId, metric);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例5：实时数据查询
     * 获取用户最新的健康数据
     */
    public Map<String, Object> queryLatestHealthData(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusDays(1)); // 查询最近1天
        query.setEndDate(LocalDateTime.now());
        query.setLatest(true); // 只返回最新记录
        query.setQueryMode("all");
        
        log.info("🔍 实时数据 - 查询用户 {} 的最新健康数据", userId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例6：组织数据聚合查询
     * 查询组织下所有用户的健康数据
     */
    public Map<String, Object> queryOrgHealthData(Long customerId, Long orgId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setOrgId(orgId); // 按组织查询
        query.setStartDate(LocalDateTime.now().minusDays(7));
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(1000);
        query.setEnableSharding(true);
        query.setIncludeStats(true);
        
        log.info("🔍 组织数据 - 查询组织 {} 的健康数据", orgId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例7：跨月数据查询
     * 演示分表查询的自动处理
     */
    public Map<String, Object> queryCrossMonthData(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusMonths(2)); // 跨2个月查询
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(5000);
        query.setEnableSharding(true); // 自动处理分表查询
        
        log.info("🔍 跨月数据 - 查询用户 {} 跨月的健康数据", userId);
        Map<String, Object> result = unifiedQueryService.queryHealthData(query);
        
        // 输出查询信息
        Map<String, Object> queryInfo = (Map<String, Object>) result.get("queryInfo");
        if (queryInfo != null) {
            log.info("📊 查询统计 - 跨月: {}, 分表: {}, 数据量: {}", 
                queryInfo.get("crossMonth"),
                queryInfo.get("shardingEnabled"),
                result.get("total")
            );
        }
        
        return result;
    }

    /**
     * 示例8：快表数据查询
     * 查询睡眠和运动数据（存储在日汇总表中）
     */
    public Map<String, Object> queryFastTableData(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusDays(30));
        query.setEndDate(LocalDateTime.now());
        // 设置需要快表查询的指标，系统会自动切换到daily查询模式
        query.setMetrics(List.of("sleep_data", "exercise_daily_data", "workout_data"));
        query.setPageSize(1000);
        
        log.info("🔍 快表数据 - 查询用户 {} 的睡眠和运动数据", userId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例9：周表数据查询
     * 查询运动周报数据
     */
    public Map<String, Object> queryWeeklyData(Long customerId, Long userId) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setUserId(userId);
        query.setStartDate(LocalDateTime.now().minusDays(84)); // 12周数据
        query.setEndDate(LocalDateTime.now());
        query.setMetric("exercise_week_data"); // 系统会自动切换到weekly查询模式
        query.setPageSize(12);
        
        log.info("🔍 周表数据 - 查询用户 {} 的运动周报数据", userId);
        return unifiedQueryService.queryHealthData(query);
    }

    /**
     * 示例10：设备数据查询
     * 根据设备序列号查询数据
     */
    public Map<String, Object> queryDeviceData(Long customerId, String deviceSn) {
        UnifiedHealthQueryDTO query = new UnifiedHealthQueryDTO();
        query.setCustomerId(customerId);
        query.setDeviceSn(deviceSn); // 按设备查询
        query.setStartDate(LocalDateTime.now().minusDays(7));
        query.setEndDate(LocalDateTime.now());
        query.setPageSize(1000);
        query.setEnableSharding(true);
        
        log.info("🔍 设备数据 - 查询设备 {} 的健康数据", deviceSn);
        return unifiedQueryService.queryHealthData(query);
    }
}