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

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.entity.TUserHealthDataDaily;
import com.ljwx.modules.health.domain.entity.TUserHealthDataWeekly;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataDailyMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataWeeklyMapper;
import com.ljwx.modules.health.util.HealthDataTableUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 统一健康数据查询服务
 * 封装分表查询、快慢表查询、配置验证等逻辑
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.UnifiedHealthDataQueryService
 * @CreateTime 2025-09-08
 */
@Slf4j
@Service
public class UnifiedHealthDataQueryService {

    @Autowired
    private TUserHealthDataMapper healthDataMapper;
    
    @Autowired
    private TUserHealthDataDailyMapper dailyMapper;
    
    @Autowired
    private TUserHealthDataWeeklyMapper weeklyMapper;
    
    @Autowired
    private HealthDataConfigQueryService configService;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 统一健康数据查询入口
     */
    public Map<String, Object> queryHealthData(UnifiedHealthQueryDTO queryDTO) {
        try {
            log.info("🔍 开始统一健康数据查询: customerId={}, userId={}, 时间范围={} ~ {}", 
                queryDTO.getCustomerId(), queryDTO.getUserId(), 
                queryDTO.getStartDate(), queryDTO.getEndDate());

            // 1. 验证和预处理查询参数
            validateAndPreprocessQuery(queryDTO);

            // 2. 根据查询模式选择查询策略
            return switch (queryDTO.getQueryMode()) {
                case "daily" -> queryDailyData(queryDTO);
                case "weekly" -> queryWeeklyData(queryDTO);
                default -> queryAllData(queryDTO);
            };

        } catch (Exception e) {
            log.error("❌ 统一健康数据查询失败: {}", e.getMessage(), e);
            return Map.of(
                "success", false,
                "error", e.getMessage(),
                "data", Collections.emptyList(),
                "total", 0L
            );
        }
    }

    /**
     * 查询主表和分表数据
     */
    private Map<String, Object> queryAllData(UnifiedHealthQueryDTO queryDTO) {
        List<TUserHealthData> allResults = new ArrayList<>();
        long totalCount = 0L;

        try {
            if (queryDTO.getEnableSharding() && queryDTO.isCrossMonthQuery()) {
                // 跨月查询，使用分表策略
                Map<String, Object> shardingResult = queryWithSharding(queryDTO);
                allResults.addAll((List<TUserHealthData>) shardingResult.get("data"));
                totalCount = (Long) shardingResult.get("total");
                
                log.info("✅ 分表查询完成，结果数量: {}", allResults.size());
            } else {
                // 单月查询，直接查询主表或对应月表
                Map<String, Object> singleResult = querySingleTable(queryDTO);
                allResults.addAll((List<TUserHealthData>) singleResult.get("data"));
                totalCount = (Long) singleResult.get("total");
                
                log.info("✅ 单表查询完成，结果数量: {}", allResults.size());
            }

            // 3. 数据后处理
            List<Map<String, Object>> processedData = postProcessHealthData(allResults, queryDTO);

            return Map.of(
                "success", true,
                "data", processedData,
                "total", totalCount,
                "queryInfo", buildQueryInfo(queryDTO),
                "timestamp", LocalDateTime.now()
            );

        } catch (Exception e) {
            log.error("❌ 查询主表数据失败: {}", e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 查询日汇总表数据
     */
    private Map<String, Object> queryDailyData(UnifiedHealthQueryDTO queryDTO) {
        try {
            LambdaQueryWrapper<TUserHealthDataDaily> query = buildDailyQuery(queryDTO);
            
            if (queryDTO.getLatest()) {
                // 查询最新记录
                query.orderByDesc(TUserHealthDataDaily::getTimestamp).last("LIMIT 1");
                List<TUserHealthDataDaily> result = dailyMapper.selectList(query);
                
                return Map.of(
                    "success", true,
                    "data", processDailyData(result, queryDTO),
                    "total", (long) result.size(),
                    "queryInfo", buildQueryInfo(queryDTO),
                    "queryMode", "daily"
                );
            } else {
                // 分页查询
                IPage<TUserHealthDataDaily> page = new Page<>(queryDTO.getValidPage(), queryDTO.getValidPageSize());
                IPage<TUserHealthDataDaily> result = dailyMapper.selectPage(page, query);
                
                return Map.of(
                    "success", true,
                    "data", processDailyData(result.getRecords(), queryDTO),
                    "total", result.getTotal(),
                    "queryInfo", buildQueryInfo(queryDTO),
                    "queryMode", "daily"
                );
            }

        } catch (Exception e) {
            log.error("❌ 查询日汇总数据失败: {}", e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 查询周汇总表数据
     */
    private Map<String, Object> queryWeeklyData(UnifiedHealthQueryDTO queryDTO) {
        try {
            LambdaQueryWrapper<TUserHealthDataWeekly> query = buildWeeklyQuery(queryDTO);
            
            if (queryDTO.getLatest()) {
                query.orderByDesc(TUserHealthDataWeekly::getTimestamp).last("LIMIT 1");
                List<TUserHealthDataWeekly> result = weeklyMapper.selectList(query);
                
                return Map.of(
                    "success", true,
                    "data", processWeeklyData(result, queryDTO),
                    "total", (long) result.size(),
                    "queryInfo", buildQueryInfo(queryDTO),
                    "queryMode", "weekly"
                );
            } else {
                IPage<TUserHealthDataWeekly> page = new Page<>(queryDTO.getValidPage(), queryDTO.getValidPageSize());
                IPage<TUserHealthDataWeekly> result = weeklyMapper.selectPage(page, query);
                
                return Map.of(
                    "success", true,
                    "data", processWeeklyData(result.getRecords(), queryDTO),
                    "total", result.getTotal(),
                    "queryInfo", buildQueryInfo(queryDTO),
                    "queryMode", "weekly"
                );
            }

        } catch (Exception e) {
            log.error("❌ 查询周汇总数据失败: {}", e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 分表查询策略
     */
    private Map<String, Object> queryWithSharding(UnifiedHealthQueryDTO queryDTO) {
        List<TUserHealthData> allResults = new ArrayList<>();
        long totalCount = 0L;

        // 1. 获取需要查询的分表列表
        List<String> tableNames = HealthDataTableUtil.getTableNames(
            queryDTO.getStartDate(), queryDTO.getEndDate()
        );

        // 2. 逐个查询分表
        for (String tableName : tableNames) {
            try {
                if (isTableExists(tableName)) {
                    log.debug("🔍 查询分表: {}", tableName);
                    List<TUserHealthData> tableResults = queryShardedTable(queryDTO, tableName);
                    allResults.addAll(tableResults);
                    totalCount += tableResults.size();
                } else {
                    log.debug("⚠️ 分表不存在，回退到主表查询: {}", tableName);
                    // 回退到主表查询
                    Map<String, Object> fallbackResult = queryMainTable(queryDTO);
                    allResults.addAll((List<TUserHealthData>) fallbackResult.get("data"));
                    totalCount += (Long) fallbackResult.get("total");
                    break; // 主表查询后停止
                }
            } catch (Exception e) {
                log.warn("⚠️ 查询分表 {} 失败，尝试回退到主表: {}", tableName, e.getMessage());
                // 发生异常时回退到主表查询
                try {
                    Map<String, Object> fallbackResult = queryMainTable(queryDTO);
                    allResults.addAll((List<TUserHealthData>) fallbackResult.get("data"));
                    totalCount += (Long) fallbackResult.get("total");
                    break;
                } catch (Exception fallbackE) {
                    log.error("❌ 回退到主表查询也失败: {}", fallbackE.getMessage());
                }
            }
        }

        // 3. 结果排序和分页
        if (!allResults.isEmpty()) {
            // 排序
            allResults.sort((a, b) -> {
                if ("desc".equalsIgnoreCase(queryDTO.getOrderDirection())) {
                    return b.getTimestamp().compareTo(a.getTimestamp());
                } else {
                    return a.getTimestamp().compareTo(b.getTimestamp());
                }
            });

            // 分页处理
            int offset = queryDTO.getOffset();
            int limit = queryDTO.getValidPageSize();
            int toIndex = Math.min(offset + limit, allResults.size());
            
            if (offset < allResults.size()) {
                allResults = allResults.subList(offset, toIndex);
            } else {
                allResults = Collections.emptyList();
            }
        }

        return Map.of(
            "data", allResults,
            "total", totalCount
        );
    }

    /**
     * 单表查询策略
     */
    private Map<String, Object> querySingleTable(UnifiedHealthQueryDTO queryDTO) {
        // 确定查询的表名
        String tableName = HealthDataTableUtil.getTableName(queryDTO.getStartDate());
        
        // 如果月表存在，查询月表；否则查询主表
        if (isTableExists(tableName)) {
            log.debug("🔍 查询月表: {}", tableName);
            List<TUserHealthData> results = queryShardedTable(queryDTO, tableName);
            return Map.of("data", results, "total", (long) results.size());
        } else {
            log.debug("🔍 月表不存在，查询主表");
            return queryMainTable(queryDTO);
        }
    }

    /**
     * 查询主表
     */
    private Map<String, Object> queryMainTable(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> query = buildMainTableQuery(queryDTO);
        
        if (queryDTO.getLatest()) {
            query.orderByDesc(TUserHealthData::getTimestamp).last("LIMIT 1");
            List<TUserHealthData> result = healthDataMapper.selectList(query);
            return Map.of("data", result, "total", (long) result.size());
        } else {
            IPage<TUserHealthData> page = new Page<>(queryDTO.getValidPage(), queryDTO.getValidPageSize());
            IPage<TUserHealthData> result = healthDataMapper.selectPage(page, query);
            return Map.of("data", result.getRecords(), "total", result.getTotal());
        }
    }

    /**
     * 查询指定分表
     */
    private List<TUserHealthData> queryShardedTable(UnifiedHealthQueryDTO queryDTO, String tableName) {
        try {
            // 使用动态SQL查询分表
            return healthDataMapper.selectFromShardedTable(tableName, buildShardedTableQuery(queryDTO));
        } catch (Exception e) {
            log.error("❌ 查询分表 {} 失败: {}", tableName, e.getMessage(), e);
            return Collections.emptyList();
        }
    }

    /**
     * 构建主表查询条件
     */
    private LambdaQueryWrapper<TUserHealthData> buildMainTableQuery(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> query = new LambdaQueryWrapper<>();
        
        // 基本条件
        if (queryDTO.getCustomerId() != null) {
            query.eq(TUserHealthData::getCustomerId, queryDTO.getCustomerId());
        }
        if (queryDTO.getOrgId() != null) {
            query.eq(TUserHealthData::getOrgId, queryDTO.getOrgId());
        }
        if (queryDTO.getUserId() != null) {
            query.eq(TUserHealthData::getUserId, queryDTO.getUserId());
        }
        if (queryDTO.getDeviceSn() != null) {
            query.eq(TUserHealthData::getDeviceSn, queryDTO.getDeviceSn());
        }

        // 时间范围
        query.ge(TUserHealthData::getTimestamp, queryDTO.getStartDate())
             .le(TUserHealthData::getTimestamp, queryDTO.getEndDate());

        // 过滤条件
        query.ne(TUserHealthData::getUploadMethod, "common_event"); // 过滤特殊数据
        
        // 排序
        if ("desc".equalsIgnoreCase(queryDTO.getOrderDirection())) {
            query.orderByDesc(TUserHealthData::getTimestamp);
        } else {
            query.orderByAsc(TUserHealthData::getTimestamp);
        }

        return query;
    }

    /**
     * 构建分表查询参数
     */
    private Map<String, Object> buildShardedTableQuery(UnifiedHealthQueryDTO queryDTO) {
        Map<String, Object> params = new HashMap<>();
        
        if (queryDTO.getCustomerId() != null) params.put("customerId", queryDTO.getCustomerId());
        if (queryDTO.getOrgId() != null) params.put("orgId", queryDTO.getOrgId());
        if (queryDTO.getUserId() != null) params.put("userId", queryDTO.getUserId());
        if (queryDTO.getDeviceSn() != null) params.put("deviceSn", queryDTO.getDeviceSn());
        
        params.put("startDate", queryDTO.getStartDate());
        params.put("endDate", queryDTO.getEndDate());
        params.put("offset", queryDTO.getOffset());
        params.put("limit", queryDTO.getValidPageSize());
        
        return params;
    }

    /**
     * 构建日汇总表查询条件
     */
    private LambdaQueryWrapper<TUserHealthDataDaily> buildDailyQuery(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthDataDaily> query = new LambdaQueryWrapper<>();
        
        if (queryDTO.getCustomerId() != null) {
            query.eq(TUserHealthDataDaily::getCustomerId, queryDTO.getCustomerId());
        }
        if (queryDTO.getUserId() != null) {
            query.eq(TUserHealthDataDaily::getUserId, queryDTO.getUserId());
        }
        if (queryDTO.getDeviceSn() != null) {
            query.eq(TUserHealthDataDaily::getDeviceSn, queryDTO.getDeviceSn());
        }

        query.ge(TUserHealthDataDaily::getTimestamp, queryDTO.getStartDate())
             .le(TUserHealthDataDaily::getTimestamp, queryDTO.getEndDate());

        if ("desc".equalsIgnoreCase(queryDTO.getOrderDirection())) {
            query.orderByDesc(TUserHealthDataDaily::getTimestamp);
        } else {
            query.orderByAsc(TUserHealthDataDaily::getTimestamp);
        }

        return query;
    }

    /**
     * 构建周汇总表查询条件
     */
    private LambdaQueryWrapper<TUserHealthDataWeekly> buildWeeklyQuery(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthDataWeekly> query = new LambdaQueryWrapper<>();
        
        if (queryDTO.getCustomerId() != null) {
            query.eq(TUserHealthDataWeekly::getCustomerId, queryDTO.getCustomerId());
        }
        if (queryDTO.getUserId() != null) {
            query.eq(TUserHealthDataWeekly::getUserId, queryDTO.getUserId());
        }
        if (queryDTO.getDeviceSn() != null) {
            query.eq(TUserHealthDataWeekly::getDeviceSn, queryDTO.getDeviceSn());
        }

        query.ge(TUserHealthDataWeekly::getTimestamp, queryDTO.getStartDate())
             .le(TUserHealthDataWeekly::getTimestamp, queryDTO.getEndDate());

        if ("desc".equalsIgnoreCase(queryDTO.getOrderDirection())) {
            query.orderByDesc(TUserHealthDataWeekly::getTimestamp);
        } else {
            query.orderByAsc(TUserHealthDataWeekly::getTimestamp);
        }

        return query;
    }

    /**
     * 验证和预处理查询参数
     */
    private void validateAndPreprocessQuery(UnifiedHealthQueryDTO queryDTO) {
        // 1. 验证客户支持的指标
        if (queryDTO.getMetric() != null) {
            if (!configService.isMetricSupported(queryDTO.getCustomerId(), queryDTO.getMetric())) {
                log.warn("⚠️ 指标 {} 不被客户 {} 支持", queryDTO.getMetric(), queryDTO.getCustomerId());
                queryDTO.setMetric(null);
            }
        }

        if (queryDTO.getMetrics() != null && !queryDTO.getMetrics().isEmpty()) {
            List<String> supportedMetrics = configService.filterSupportedMetrics(
                queryDTO.getCustomerId(), queryDTO.getMetrics()
            );
            queryDTO.setMetrics(supportedMetrics);
        }

        // 2. 根据指标自动决定查询模式
        if ("all".equals(queryDTO.getQueryMode())) {
            if (queryDTO.needsFastTableQuery()) {
                queryDTO.setQueryMode("daily");
                log.debug("🔄 自动切换到日汇总表查询模式");
            } else if (queryDTO.needsWeeklyTableQuery()) {
                queryDTO.setQueryMode("weekly");
                log.debug("🔄 自动切换到周汇总表查询模式");
            }
        }

        // 3. 时间范围限制
        if (queryDTO.getQueryDaysSpan() > 90) {
            log.warn("⚠️ 查询时间跨度过大：{}天，限制为90天", queryDTO.getQueryDaysSpan());
            queryDTO.setStartDate(queryDTO.getEndDate().minusDays(90));
        }
    }

    /**
     * 数据后处理
     */
    private List<Map<String, Object>> postProcessHealthData(List<TUserHealthData> rawData, 
                                                            UnifiedHealthQueryDTO queryDTO) {
        return rawData.stream()
            .map(this::convertToMap)
            .collect(Collectors.toList());
    }

    /**
     * 处理日汇总数据
     */
    private List<Map<String, Object>> processDailyData(List<TUserHealthDataDaily> rawData, 
                                                      UnifiedHealthQueryDTO queryDTO) {
        return rawData.stream()
            .map(this::convertDailyToMap)
            .collect(Collectors.toList());
    }

    /**
     * 处理周汇总数据
     */
    private List<Map<String, Object>> processWeeklyData(List<TUserHealthDataWeekly> rawData, 
                                                       UnifiedHealthQueryDTO queryDTO) {
        return rawData.stream()
            .map(this::convertWeeklyToMap)
            .collect(Collectors.toList());
    }

    /**
     * 转换健康数据为Map
     */
    private Map<String, Object> convertToMap(TUserHealthData data) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", data.getId());
        result.put("userId", data.getUserId());
        result.put("deviceSn", data.getDeviceSn());
        result.put("timestamp", data.getTimestamp());
        result.put("heartRate", data.getHeartRate());
        result.put("bloodOxygen", data.getBloodOxygen());
        result.put("temperature", data.getTemperature());
        result.put("pressureHigh", data.getPressureHigh());
        result.put("pressureLow", data.getPressureLow());
        result.put("stress", data.getStress());
        result.put("step", data.getStep());
        result.put("calorie", data.getCalorie());
        result.put("distance", data.getDistance());
        return result;
    }

    /**
     * 转换日汇总数据为Map
     */
    private Map<String, Object> convertDailyToMap(TUserHealthDataDaily data) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", data.getId());
        result.put("userId", data.getUserId());
        result.put("deviceSn", data.getDeviceSn());
        result.put("timestamp", data.getTimestamp());
        result.put("sleepData", data.getSleepData());
        result.put("exerciseDailyData", data.getExerciseDailyData());
        result.put("workoutData", data.getWorkoutData());
        result.put("scientificSleepData", data.getScientificSleepData());
        return result;
    }

    /**
     * 转换周汇总数据为Map
     */
    private Map<String, Object> convertWeeklyToMap(TUserHealthDataWeekly data) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", data.getId());
        result.put("userId", data.getUserId());
        result.put("deviceSn", data.getDeviceSn());
        result.put("timestamp", data.getTimestamp());
        result.put("exerciseWeekData", data.getExerciseWeekData());
        return result;
    }

    /**
     * 构建查询信息
     */
    private Map<String, Object> buildQueryInfo(UnifiedHealthQueryDTO queryDTO) {
        return Map.of(
            "customerId", queryDTO.getCustomerId(),
            "queryMode", queryDTO.getQueryMode(),
            "timeSpan", queryDTO.getQueryDaysSpan(),
            "crossMonth", queryDTO.isCrossMonthQuery(),
            "shardingEnabled", queryDTO.getEnableSharding(),
            "pageInfo", Map.of(
                "page", queryDTO.getValidPage(),
                "pageSize", queryDTO.getValidPageSize()
            )
        );
    }

    /**
     * 检查表是否存在
     */
    private boolean isTableExists(String tableName) {
        try {
            String sql = "SELECT COUNT(*) FROM information_schema.tables " +
                        "WHERE table_schema = DATABASE() AND table_name = ?";
            Integer count = jdbcTemplate.queryForObject(sql, Integer.class, tableName);
            return count != null && count > 0;
        } catch (DataAccessException e) {
            log.warn("⚠️ 检查表 {} 是否存在失败: {}", tableName, e.getMessage());
            return false;
        }
    }
}