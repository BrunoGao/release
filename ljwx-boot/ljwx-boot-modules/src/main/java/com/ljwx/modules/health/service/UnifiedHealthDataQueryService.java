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
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.customer.domain.entity.THealthDataConfig;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.domain.dto.user.health.data.TUserHealthDataSearchDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.entity.TUserHealthDataDaily;
import com.ljwx.modules.health.domain.entity.TUserHealthDataWeekly;
import com.ljwx.modules.health.domain.vo.HealthDataPageVO;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataDailyMapper;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataWeeklyMapper;
import com.ljwx.modules.system.domain.entity.SysUser;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 统一健康数据查询服务
 * 支持基于user_id/org_id/customer_id的层级查询
 * 支持按月分表查询和daily/weekly慢字段合并
 * 供listTUserHealthDataPage和数据分析模块(baseline/score/prediction/recommendation/profile)调用
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.UnifiedHealthDataQueryService
 * @CreateTime 2025-09-14
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
    private HealthDataConfigQueryService healthDataConfigQueryService;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    // 硬编码的慢字段列表，便于快速查询
    private static final Set<String> DAILY_SLOW_FIELDS = Set.of(
        "sleep", "sleepData", "exerciseDailyData", "scientificSleepData", "workoutData",
        "work_out", "exercise_daily", "scientific_sleep"
    );
    
    private static final Set<String> WEEKLY_SLOW_FIELDS = Set.of(
        "exerciseWeekData", "exercise_week"
    );

    /**
     * 分页查询健康数据 - 供listTUserHealthDataPage调用
     * 支持基于user_id/org_id/customer_id的层级查询
     * 支持跨月分表查询和慢字段合并
     */
    public HealthDataPageVO<Map<String, Object>> queryHealthDataPage(PageQuery pageQuery, TUserHealthDataSearchDTO searchDTO) {
        log.info("🔍 统一健康数据分页查询: userId={}, orgId={}, customerId={}, startDate={}, endDate={}", 
                searchDTO.getUserId(), searchDTO.getOrgId(), searchDTO.getCustomerId(), 
                searchDTO.getStartDate(), searchDTO.getEndDate());

        try {
            // 1. 时间边界转换
            LocalDateTime startDate = LocalDateTime.ofEpochSecond(
                searchDTO.getStartDate() / 1000, 0, ZoneOffset.ofHours(8));
            LocalDateTime endDate = LocalDateTime.ofEpochSecond(
                (searchDTO.getEndDate() + 86399000) / 1000, 0, ZoneOffset.ofHours(8));

            // 2. 构建查询条件
            UnifiedHealthQueryDTO queryDTO = buildQueryDTO(searchDTO, startDate, endDate);
            
            // 3. 执行查询
            if (isSpecificUserQuery(searchDTO)) {
                // 查询指定用户的所有数据
                return querySpecificUserData(pageQuery, queryDTO);
            } else {
                // 查询部门用户最新数据
                return queryLatestUserDataByOrg(pageQuery, queryDTO);
            }
            
        } catch (Exception e) {
            log.error("❌ 健康数据分页查询失败: {}", e.getMessage(), e);
            
            // 获取默认字段配置用于生成columns
            Map<String, String> defaultFields = getAllDefaultFields();
            
            return new HealthDataPageVO<>(
                Collections.emptyList(), 0, pageQuery.getPageSize(), pageQuery.getPage(), 
                generateColumns(defaultFields)
            );
        }
    }

    /**
     * 查询健康数据 - 供数据分析模块调用
     * 返回Map格式的原始数据，支持baseline/score/prediction/recommendation/profile
     */
    public Map<String, Object> queryHealthData(UnifiedHealthQueryDTO queryDTO) {
        log.info("🔍 统一健康数据查询: customerId={}, orgId={}, userId={}, 时间范围={} ~ {}", 
                queryDTO.getCustomerId(), queryDTO.getOrgId(), queryDTO.getUserId(), 
                queryDTO.getStartDate(), queryDTO.getEndDate());

        try {
            // 查询主表和分表数据
            List<Map<String, Object>> allData = queryAllHealthData(queryDTO);
            
            Map<String, Object> result = new HashMap<>();
            result.put("data", allData);
            result.put("total", allData.size());
            result.put("success", true);
            
            return result;
            
        } catch (Exception e) {
            log.error("❌ 统一健康数据查询失败: customerId={}, userId={}, error={}", 
                    queryDTO.getCustomerId(), queryDTO.getUserId(), e.getMessage(), e);
            
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("data", Collections.emptyList());
            errorResult.put("total", 0);
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            
            return errorResult;
        }
    }

    // ========== 核心查询方法 ==========

    /**
     * 查询所有健康数据（主表+分表+慢字段合并）
     * 用于数据分析，使用 Basic Enabled Metrics
     */
    private List<Map<String, Object>> queryAllHealthData(UnifiedHealthQueryDTO queryDTO) {
        List<Map<String, Object>> allData = new ArrayList<>();
        
        // 1. 获取基础分析字段配置（使用 Basic Enabled Metrics）
        Map<String, String> supportedFields = getBasicAnalysisFields(queryDTO.getCustomerId());
        log.info("📋 基础分析字段: {}", supportedFields.keySet());
        
        // 2. 查询主表数据
        List<TUserHealthData> mainData = queryMainTableData(queryDTO);
        log.info("📊 主表查询结果: {} 条", mainData.size());
        
        // 3. 查询历史分表数据
        List<TUserHealthData> shardedData = queryShardedTableData(queryDTO);
        log.info("📊 分表查询结果: {} 条", shardedData.size());
        
        // 4. 合并数据
        List<TUserHealthData> combinedData = new ArrayList<>();
        combinedData.addAll(mainData);
        combinedData.addAll(shardedData);
        
        // 5. 按时间排序
        combinedData.sort(Comparator.comparing(TUserHealthData::getTimestamp));
        
        // 6. 转换为Map并根据配置合并慢字段
        for (TUserHealthData data : combinedData) {
            Map<String, Object> dataMap = convertToMap(data, supportedFields);
            
            // 根据配置决定是否合并daily数据（睡眠等慢字段）
            if (needsDailyData(supportedFields)) {
                mergeDailyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
            }
            
            // 根据配置决定是否合并weekly数据
            if (needsWeeklyData(supportedFields)) {
                mergeWeeklyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
            }
            
            // 只返回支持的字段
            filterSupportedFields(dataMap, supportedFields);
            
            allData.add(dataMap);
        }
        
        return allData;
    }

    /**
     * 查询主表数据
     */
    private List<TUserHealthData> queryMainTableData(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> query = buildBaseQuery(queryDTO);
        return healthDataMapper.selectList(query);
    }

    /**
     * 分页查询主表数据
     */
    private List<TUserHealthData> queryMainTableDataWithPaging(UnifiedHealthQueryDTO queryDTO, PageQuery pageQuery) {
        LambdaQueryWrapper<TUserHealthData> query = buildBaseQuery(queryDTO);
        
        // 添加分页限制
        int offset = (int) ((pageQuery.getPage() - 1) * pageQuery.getPageSize());
        query.last("LIMIT " + offset + ", " + pageQuery.getPageSize());
        
        return healthDataMapper.selectList(query);
    }

    /**
     * 查询健康数据总数
     */
    private long queryHealthDataCount(UnifiedHealthQueryDTO queryDTO) {
        try {
            LambdaQueryWrapper<TUserHealthData> query = buildBaseQuery(queryDTO);
            Long count = healthDataMapper.selectCount(query);
            
            // 如果需要查询分表，也要统计分表的数量
            List<String> tableNames = getShardedTableNames(queryDTO.getStartDate(), queryDTO.getEndDate());
            
            for (String tableName : tableNames) {
                try {
                    if (tableExists(tableName)) {
                        count += queryShardedTableCount(tableName, queryDTO);
                    }
                } catch (Exception e) {
                    log.warn("⚠️ 查询分表 {} 总数失败: {}", tableName, e.getMessage());
                }
            }
            
            return count != null ? count : 0L;
            
        } catch (Exception e) {
            log.error("❌ 查询健康数据总数失败: {}", e.getMessage(), e);
            return 0L;
        }
    }

    /**
     * 查询分表数据总数
     */
    private long queryShardedTableCount(String tableName, UnifiedHealthQueryDTO queryDTO) {
        try {
            StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM ").append(tableName).append(" WHERE 1=1");
            List<Object> params = new ArrayList<>();
            
            // 添加查询条件
            if (queryDTO.getUserId() != null) {
                sql.append(" AND user_id = ?");
                params.add(queryDTO.getUserId());
            } else if (queryDTO.getOrgId() != null) {
                sql.append(" AND org_id = ?");
                params.add(queryDTO.getOrgId());
            } else if (queryDTO.getCustomerId() != null && queryDTO.getCustomerId() != 0L) {
                sql.append(" AND customer_id = ?");
                params.add(queryDTO.getCustomerId());
            }
            
            if (queryDTO.getStartDate() != null) {
                sql.append(" AND timestamp >= ?");
                params.add(queryDTO.getStartDate());
            }
            if (queryDTO.getEndDate() != null) {
                sql.append(" AND timestamp <= ?");
                params.add(queryDTO.getEndDate());
            }
            
            Integer count = jdbcTemplate.queryForObject(sql.toString(), Integer.class, params.toArray());
            return count != null ? count : 0L;
            
        } catch (Exception e) {
            log.error("❌ 查询分表 {} 总数失败: {}", tableName, e.getMessage());
            return 0L;
        }
    }

    /**
     * 查询分表数据
     */
    private List<TUserHealthData> queryShardedTableData(UnifiedHealthQueryDTO queryDTO) {
        List<TUserHealthData> allShardedData = new ArrayList<>();
        
        // 获取需要查询的月份表
        List<String> tableNames = getShardedTableNames(queryDTO.getStartDate(), queryDTO.getEndDate());
        
        for (String tableName : tableNames) {
            try {
                // 检查表是否存在
                if (tableExists(tableName)) {
                    List<TUserHealthData> data = querySpecificShardedTable(tableName, queryDTO);
                    allShardedData.addAll(data);
                    log.debug("📊 分表 {} 查询结果: {} 条", tableName, data.size());
                }
            } catch (Exception e) {
                log.warn("⚠️ 查询分表 {} 失败: {}", tableName, e.getMessage());
            }
        }
        
        return allShardedData;
    }

    /**
     * 分页查询分表数据
     */
    private List<TUserHealthData> queryShardedTableDataWithPaging(UnifiedHealthQueryDTO queryDTO, PageQuery pageQuery) {
        List<TUserHealthData> allShardedData = new ArrayList<>();
        
        // 获取需要查询的月份表
        List<String> tableNames = getShardedTableNames(queryDTO.getStartDate(), queryDTO.getEndDate());
        
        int remainingSize = (int) pageQuery.getPageSize();
        int offset = (int) ((pageQuery.getPage() - 1) * pageQuery.getPageSize());
        
        for (String tableName : tableNames) {
            try {
                // 检查表是否存在
                if (tableExists(tableName) && remainingSize > 0) {
                    List<TUserHealthData> data = querySpecificShardedTableWithPaging(tableName, queryDTO, offset, remainingSize);
                    allShardedData.addAll(data);
                    log.debug("📊 分表 {} 分页查询结果: {} 条", tableName, data.size());
                    
                    remainingSize -= data.size();
                    if (offset > 0) {
                        offset = Math.max(0, offset - data.size());
                    }
                }
            } catch (Exception e) {
                log.warn("⚠️ 分页查询分表 {} 失败: {}", tableName, e.getMessage());
            }
        }
        
        return allShardedData;
    }

    // ========== 辅助查询方法 ==========

    /**
     * 构建基础查询条件
     */
    private LambdaQueryWrapper<TUserHealthData> buildBaseQuery(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> query = new LambdaQueryWrapper<>();
        
        // 层级查询逻辑：user_id > org_id > customer_id
        if (queryDTO.getUserId() != null) {
            query.eq(TUserHealthData::getUserId, queryDTO.getUserId());
        } else if (queryDTO.getOrgId() != null) {
            query.eq(TUserHealthData::getOrgId, queryDTO.getOrgId());
        } else if (queryDTO.getCustomerId() != null && queryDTO.getCustomerId() != 0L) {
            // customer_id=0 表示超级管理员，不过滤
            query.eq(TUserHealthData::getCustomerId, queryDTO.getCustomerId());
        }
        
        // 时间范围
        if (queryDTO.getStartDate() != null) {
            query.ge(TUserHealthData::getTimestamp, queryDTO.getStartDate());
        }
        if (queryDTO.getEndDate() != null) {
            query.le(TUserHealthData::getTimestamp, queryDTO.getEndDate());
        }
        
        // 排序
        query.orderByDesc(TUserHealthData::getTimestamp);
        
        return query;
    }

    /**
     * 查询特定分表
     */
    private List<TUserHealthData> querySpecificShardedTable(String tableName, UnifiedHealthQueryDTO queryDTO) {
        try {
            // 使用JDBC直接查询分表
            StringBuilder sql = new StringBuilder("SELECT * FROM ").append(tableName).append(" WHERE 1=1");
            List<Object> params = new ArrayList<>();
            
            // 添加查询条件
            if (queryDTO.getUserId() != null) {
                sql.append(" AND user_id = ?");
                params.add(queryDTO.getUserId());
            } else if (queryDTO.getOrgId() != null) {
                sql.append(" AND org_id = ?");
                params.add(queryDTO.getOrgId());
            } else if (queryDTO.getCustomerId() != null && queryDTO.getCustomerId() != 0L) {
                sql.append(" AND customer_id = ?");
                params.add(queryDTO.getCustomerId());
            }
            
            if (queryDTO.getStartDate() != null) {
                sql.append(" AND timestamp >= ?");
                params.add(queryDTO.getStartDate());
            }
            if (queryDTO.getEndDate() != null) {
                sql.append(" AND timestamp <= ?");
                params.add(queryDTO.getEndDate());
            }
            
            sql.append(" ORDER BY timestamp DESC");
            
            // 执行查询
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql.toString(), params.toArray());
            
            // 转换为实体对象
            return rows.stream()
                    .map(this::convertRowToEntity)
                    .collect(Collectors.toList());
                    
        } catch (Exception e) {
            log.error("❌ 查询分表 {} 失败: {}", tableName, e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 分页查询特定分表
     */
    private List<TUserHealthData> querySpecificShardedTableWithPaging(String tableName, UnifiedHealthQueryDTO queryDTO, int offset, int limit) {
        try {
            // 使用JDBC直接查询分表
            StringBuilder sql = new StringBuilder("SELECT * FROM ").append(tableName).append(" WHERE 1=1");
            List<Object> params = new ArrayList<>();
            
            // 添加查询条件
            if (queryDTO.getUserId() != null) {
                sql.append(" AND user_id = ?");
                params.add(queryDTO.getUserId());
            } else if (queryDTO.getOrgId() != null) {
                sql.append(" AND org_id = ?");
                params.add(queryDTO.getOrgId());
            } else if (queryDTO.getCustomerId() != null && queryDTO.getCustomerId() != 0L) {
                sql.append(" AND customer_id = ?");
                params.add(queryDTO.getCustomerId());
            }
            
            if (queryDTO.getStartDate() != null) {
                sql.append(" AND timestamp >= ?");
                params.add(queryDTO.getStartDate());
            }
            if (queryDTO.getEndDate() != null) {
                sql.append(" AND timestamp <= ?");
                params.add(queryDTO.getEndDate());
            }
            
            sql.append(" ORDER BY timestamp DESC");
            sql.append(" LIMIT ?, ?");
            params.add(offset);
            params.add(limit);
            
            // 执行查询
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql.toString(), params.toArray());
            
            // 转换为实体对象
            return rows.stream()
                    .map(this::convertRowToEntity)
                    .collect(Collectors.toList());
                    
        } catch (Exception e) {
            log.error("❌ 分页查询分表 {} 失败: {}", tableName, e.getMessage());
            return Collections.emptyList();
        }
    }

    // ========== 分页查询方法 ==========

    /**
     * 判断是否为指定用户查询
     */
    private boolean isSpecificUserQuery(TUserHealthDataSearchDTO searchDTO) {
        return ObjectUtils.isNotEmpty(searchDTO.getUserId()) && 
               !"0".equals(searchDTO.getUserId()) && 
               !"all".equals(searchDTO.getUserId());
    }

    /**
     * 查询指定用户数据 - 优化分页查询
     */
    private HealthDataPageVO<Map<String, Object>> querySpecificUserData(PageQuery pageQuery, UnifiedHealthQueryDTO queryDTO) {
        log.info("🔍 查询指定用户数据: userId={}", queryDTO.getUserId());
        
        try {
            // 1. 先查询总数（用于分页信息）
            long totalCount = queryHealthDataCount(queryDTO);
            if (totalCount == 0) {
                return new HealthDataPageVO<>(
                    Collections.emptyList(), 0, pageQuery.getPageSize(), pageQuery.getPage(),
                    Collections.emptyList()
                );
            }
            
            // 2. 分页查询主表数据
            List<TUserHealthData> mainData = queryMainTableDataWithPaging(queryDTO, pageQuery);
            log.info("📊 主表分页查询结果: {} 条", mainData.size());
            
            // 3. 查询历史分表数据（也需要分页）
            List<TUserHealthData> shardedData = queryShardedTableDataWithPaging(queryDTO, pageQuery);
            log.info("📊 分表分页查询结果: {} 条", shardedData.size());
            
            // 4. 合并并排序数据
            List<TUserHealthData> combinedData = new ArrayList<>();
            combinedData.addAll(mainData);
            combinedData.addAll(shardedData);
            
            // 按时间排序并限制数量
            List<TUserHealthData> sortedData = combinedData.stream()
                .sorted(Comparator.comparing(TUserHealthData::getTimestamp).reversed())
                .limit(pageQuery.getPageSize())
                .collect(Collectors.toList());
            
            // 5. 获取配置和转换数据（分页查询使用 Full Enabled Metrics）
            Map<String, String> supportedFields = getSupportedHealthFields(queryDTO.getCustomerId());
            log.info("🔍 支持的字段配置(Full): customerId={}, fields={}", queryDTO.getCustomerId(), supportedFields);
            
            List<Map<String, Object>> pageData = new ArrayList<>();
            for (TUserHealthData data : sortedData) {
                Map<String, Object> dataMap = convertToMap(data, supportedFields);
                log.info("📊 转换后数据字段: {}", dataMap.keySet());
                log.info("📊 转换后数据样例: heartRate={}, heart_rate={}, bloodOxygen={}, blood_oxygen={}", 
                    dataMap.get("heartRate"), dataMap.get("heart_rate"), 
                    dataMap.get("bloodOxygen"), dataMap.get("blood_oxygen"));
                
                // 根据配置决定是否合并daily数据
                if (needsDailyData(supportedFields)) {
                    log.info("🔄 需要合并daily数据: userId={}, timestamp={}", data.getUserId(), data.getTimestamp());
                    mergeDailyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
                    log.info("📊 合并daily后数据字段: {}", dataMap.keySet());
                }
                
                // 根据配置决定是否合并weekly数据
                if (needsWeeklyData(supportedFields)) {
                    log.info("🔄 需要合并weekly数据: userId={}, timestamp={}", data.getUserId(), data.getTimestamp());
                    mergeWeeklyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
                    log.info("📊 合并weekly后数据字段: {}", dataMap.keySet());
                }
                
                // 只返回支持的字段
                filterSupportedFields(dataMap, supportedFields);
                log.info("📊 最终返回数据字段: {}", dataMap.keySet());
                log.info("📊 最终返回数据样例: heartRate={}, bloodOxygen={}, pressureHigh={}, pressureLow={}", 
                    dataMap.get("heartRate"), dataMap.get("bloodOxygen"), 
                    dataMap.get("pressureHigh"), dataMap.get("pressureLow"));
                
                pageData.add(dataMap);
            }
            
            // 6. 生成columns配置
            List<Map<String, Object>> columns = generateColumns(supportedFields);
            log.info("📋 生成的columns配置: {}", columns.size());
            
            return new HealthDataPageVO<>(
                pageData, totalCount, pageQuery.getPageSize(), pageQuery.getPage(),
                columns
            );
            
        } catch (Exception e) {
            log.error("❌ 指定用户数据查询失败: userId={}, error={}", queryDTO.getUserId(), e.getMessage(), e);
            return new HealthDataPageVO<>(
                Collections.emptyList(), 0, pageQuery.getPageSize(), pageQuery.getPage(),
                generateColumns(getSupportedHealthFields(queryDTO.getCustomerId()))
            );
        }
    }

    /**
     * 查询部门用户最新数据 - 使用与指定用户查询一致的转换逻辑
     */
    private HealthDataPageVO<Map<String, Object>> queryLatestUserDataByOrg(PageQuery pageQuery, UnifiedHealthQueryDTO queryDTO) {
        log.info("🔍 查询部门用户最新数据: orgId={}", queryDTO.getOrgId());
        
        try {
            // 1. 获取支持的字段配置（分页查询使用 Full Enabled Metrics）
            Map<String, String> supportedFields = getSupportedHealthFields(queryDTO.getCustomerId());
            log.info("🔍 支持的字段配置(Full): customerId={}, fields={}", queryDTO.getCustomerId(), supportedFields);
            
            // 2. 查询主表数据
            List<TUserHealthData> mainData = queryMainTableData(queryDTO);
            log.info("📊 主表查询结果: {} 条", mainData.size());
            
            // 3. 查询历史分表数据
            List<TUserHealthData> shardedData = queryShardedTableData(queryDTO);
            log.info("📊 分表查询结果: {} 条", shardedData.size());
            
            // 4. 合并数据
            List<TUserHealthData> combinedData = new ArrayList<>();
            combinedData.addAll(mainData);
            combinedData.addAll(shardedData);
            
            // 5. 转换数据并按用户分组获取最新数据
            Map<Long, Map<String, Object>> latestByUser = new HashMap<>();
            Map<Long, LocalDateTime> latestTimeByUser = new HashMap<>();
            
            for (TUserHealthData data : combinedData) {
                Map<String, Object> dataMap = convertToMap(data, supportedFields);
                log.info("📊 部门查询 - 转换后数据字段: {}", dataMap.keySet());
                log.info("📊 部门查询 - 转换后数据样例: heartRate={}, bloodOxygen={}, pressureHigh={}, pressureLow={}", 
                    dataMap.get("heartRate"), dataMap.get("bloodOxygen"), 
                    dataMap.get("pressureHigh"), dataMap.get("pressureLow"));
                
                // 根据配置决定是否合并daily数据
                if (needsDailyData(supportedFields)) {
                    log.info("🔄 部门查询 - 需要合并daily数据: userId={}, timestamp={}", data.getUserId(), data.getTimestamp());
                    mergeDailyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
                }
                
                // 根据配置决定是否合并weekly数据
                if (needsWeeklyData(supportedFields)) {
                    log.info("🔄 部门查询 - 需要合并weekly数据: userId={}, timestamp={}", data.getUserId(), data.getTimestamp());
                    mergeWeeklyData(dataMap, data.getUserId(), data.getTimestamp(), supportedFields);
                }
                
                // 只返回支持的字段
                filterSupportedFields(dataMap, supportedFields);
                log.info("📊 部门查询 - 最终返回数据字段: {}", dataMap.keySet());
                log.info("📊 部门查询 - 最终返回数据样例: heartRate={}, bloodOxygen={}, pressureHigh={}, pressureLow={}", 
                    dataMap.get("heartRate"), dataMap.get("bloodOxygen"), 
                    dataMap.get("pressureHigh"), dataMap.get("pressureLow"));
                
                // 按用户分组，保留最新数据
                Long userId = data.getUserId();
                if (userId != null) {
                    LocalDateTime currentTime = data.getTimestamp();
                    if (!latestTimeByUser.containsKey(userId) || 
                        currentTime.isAfter(latestTimeByUser.get(userId))) {
                        latestByUser.put(userId, dataMap);
                        latestTimeByUser.put(userId, currentTime);
                    }
                }
            }
            
            List<Map<String, Object>> latestData = new ArrayList<>(latestByUser.values());
            
            // 按时间排序
            latestData.sort((a, b) -> {
                LocalDateTime timeA = (LocalDateTime) a.get("timestamp");
                LocalDateTime timeB = (LocalDateTime) b.get("timestamp");
                return timeB.compareTo(timeA);
            });
            
            // 分页
            int start = (int) ((pageQuery.getPage() - 1) * pageQuery.getPageSize());
            int end = Math.min(start + (int) pageQuery.getPageSize(), latestData.size());
            List<Map<String, Object>> pageData = latestData.subList(start, end);
            
            // 生成columns配置
            List<Map<String, Object>> columns = generateColumns(supportedFields);
            log.info("📋 部门查询 - 生成的columns配置: {}", columns.size());
            
            return new HealthDataPageVO<>(
                pageData, latestData.size(), pageQuery.getPageSize(), pageQuery.getPage(),
                columns
            );
            
        } catch (Exception e) {
            log.error("❌ 部门用户数据查询失败: orgId={}, error={}", queryDTO.getOrgId(), e.getMessage(), e);
            return new HealthDataPageVO<>(
                Collections.emptyList(), 0, pageQuery.getPageSize(), pageQuery.getPage(),
                generateColumns(getSupportedHealthFields(queryDTO.getCustomerId()))
            );
        }
    }

    // ========== 数据转换和合并方法 ==========

    /**
     * 构建查询DTO
     */
    private UnifiedHealthQueryDTO buildQueryDTO(TUserHealthDataSearchDTO searchDTO, LocalDateTime startDate, LocalDateTime endDate) {
        UnifiedHealthQueryDTO queryDTO = new UnifiedHealthQueryDTO();
        queryDTO.setCustomerId(searchDTO.getCustomerId());
        queryDTO.setStartDate(startDate);
        queryDTO.setEndDate(endDate);
        queryDTO.setEnableSharding(true);
        
        // 解析org_id和user_id
        if (ObjectUtils.isNotEmpty(searchDTO.getOrgId()) && !"0".equals(searchDTO.getOrgId()) && !"all".equals(searchDTO.getOrgId())) {
            queryDTO.setOrgId(Long.parseLong(searchDTO.getOrgId()));
        }
        if (ObjectUtils.isNotEmpty(searchDTO.getUserId()) && !"0".equals(searchDTO.getUserId()) && !"all".equals(searchDTO.getUserId())) {
            queryDTO.setUserId(Long.parseLong(searchDTO.getUserId()));
        }
        
        return queryDTO;
    }

    /**
     * 转换实体为Map - 基于字段配置应用映射规则
     */
    private Map<String, Object> convertToMap(TUserHealthData data, Map<String, String> supportedFields) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", data.getId());
        map.put("userId", data.getUserId());
        map.put("customerId", data.getCustomerId());
        map.put("orgId", data.getOrgId());
        map.put("deviceSn", data.getDeviceSn());
        map.put("timestamp", data.getTimestamp());
        
        log.info("🔧 convertToMap - 输入数据: heartRate={}, bloodOxygen={}, temperature={}, latitude={}, longitude={}, altitude={}", 
            data.getHeartRate(), data.getBloodOxygen(), data.getTemperature(),
            data.getLatitude(), data.getLongitude(), data.getAltitude());
        log.info("🔧 convertToMap - 支持字段: {}", supportedFields.keySet());
        log.info("🔧 convertToMap - 是否包含location字段: {}", supportedFields.containsKey("location"));
        
        // 根据支持的字段配置来添加健康指标
        for (String fieldName : supportedFields.keySet()) {
            log.info("🔧 convertToMap - 处理字段: {}", fieldName);
            addHealthField(map, data, fieldName);
        }
        
        log.info("🔧 convertToMap - 输出Map字段: {}", map.keySet());
        log.info("🔧 convertToMap - 输出Map样例: heartRate={}, heart_rate={}, bloodOxygen={}, blood_oxygen={}", 
            map.get("heartRate"), map.get("heart_rate"), 
            map.get("bloodOxygen"), map.get("blood_oxygen"));
        
        // 用户信息（从sys_user获取）
        addUserInfo(map, data.getUserId());
        
        // 调试：检查是否有坐标数据但未被处理
        if (data.getLatitude() != null || data.getLongitude() != null || data.getAltitude() != null) {
            if (!map.containsKey("latitude") && !map.containsKey("longitude") && !map.containsKey("altitude")) {
                log.info("🔧 数据库有坐标数据但未处理: latitude={}, longitude={}, altitude={} (可能location未启用)", 
                    data.getLatitude(), data.getLongitude(), data.getAltitude());
            }
        }
        
        return map;
    }

    /**
     * 兼容旧版本的 convertToMap 方法
     */
    private Map<String, Object> convertToMap(TUserHealthData data) {
        return convertToMap(data, getAllDefaultFields());
    }

    /**
     * 根据字段名添加健康指标数据，应用特殊映射规则
     * 前端使用驼峰命名，后端数据库使用下划线命名，需要做字段名转换
     */
    private void addHealthField(Map<String, Object> map, TUserHealthData data, String fieldName) {
        switch (fieldName) {
            // 规则2: heart_rate 同时包含 pressure_low 和 pressure_high，转换为前端驼峰命名
            case "heart_rate", "heartRate" -> {
                map.put("heartRate", data.getHeartRate());
                map.put("pressureHigh", data.getPressureHigh());
                map.put("pressureLow", data.getPressureLow());
                // 保持下划线命名用于兼容
                map.put("heart_rate", data.getHeartRate());
                map.put("pressure_high", data.getPressureHigh());
                map.put("pressure_low", data.getPressureLow());
            }
            
            // 规则1: location 映射为经纬度高度，使用前端驼峰命名
            case "location" -> {
                // 从实际的经纬度字段获取数据
                Double lat = data.getLatitude() != null ? data.getLatitude() : 0.0;
                Double lng = data.getLongitude() != null ? data.getLongitude() : 0.0;
                Double alt = data.getAltitude() != null ? data.getAltitude() : 0.0;
                
                map.put("latitude", lat);
                map.put("longitude", lng);
                map.put("altitude", alt);
                
                log.info("🔧 location字段映射成功: latitude={}, longitude={}, altitude={}", lat, lng, alt);
                log.info("🔧 location字段映射后Map包含: latitude={}, longitude={}, altitude={}", 
                    map.containsKey("latitude"), map.containsKey("longitude"), map.containsKey("altitude"));
            }
            
            // 规则3: 忽略 ecg 和 wear 字段
            case "ecg", "wear" -> {
                // 不添加这些字段
            }
            
            // 基础健康指标 - 转换为前端驼峰命名
            case "blood_oxygen", "bloodOxygen" -> {
                map.put("bloodOxygen", data.getBloodOxygen());
                map.put("blood_oxygen", data.getBloodOxygen()); // 兼容性
            }
            case "body_temperature", "temperature" -> {
                map.put("temperature", data.getTemperature());
                map.put("body_temperature", data.getTemperature()); // 兼容性
            }
            case "pressure_high", "pressureHigh" -> {
                map.put("pressureHigh", data.getPressureHigh());
                map.put("pressure_high", data.getPressureHigh()); // 兼容性
            }
            case "pressure_low", "pressureLow" -> {
                map.put("pressureLow", data.getPressureLow());
                map.put("pressure_low", data.getPressureLow()); // 兼容性
            }
            case "stress" -> map.put("stress", data.getStress());
            case "step" -> map.put("step", data.getStep());
            case "calorie" -> map.put("calorie", data.getCalorie());
            case "distance" -> map.put("distance", data.getDistance());
            
            // 慢字段处理
            case "sleepData", "sleep" -> {
                // sleepData 需要从daily表获取，这里先不处理，在mergeDailyData中处理
            }
            case "work_out", "workoutData" -> {
                // workoutData 需要从daily表获取，在mergeDailyData中处理
            }
            case "exercise_daily", "exerciseDailyData" -> {
                // exerciseDailyData 需要从daily表获取，在mergeDailyData中处理  
            }
            case "exercise_week", "exerciseWeekData" -> {
                // exerciseWeekData 需要从weekly表获取，在mergeWeeklyData中处理
            }
            case "scientific_sleep", "scientificSleepData" -> {
                // scientificSleepData 需要从daily表获取，在mergeDailyData中处理
            }
            
            default -> {
                // 对于未知字段，记录日志但不添加
                log.debug("未识别的健康字段: {}", fieldName);
            }
        }
    }

    /**
     * 添加用户信息
     */
    private void addUserInfo(Map<String, Object> dataMap, Long userId) {
        try {
            if (userId != null) {
                SysUser user = sysUserService.getById(userId);
                if (user != null) {
                    dataMap.put("userName", user.getUserName());
                    dataMap.put("orgName", user.getOrgName());
                }
            }
        } catch (Exception e) {
            log.warn("⚠️ 获取用户信息失败: userId={}, error={}", userId, e.getMessage());
            dataMap.put("userName", "未知用户");
            dataMap.put("orgName", "未知部门");
        }
    }

    /**
     * 合并daily数据（睡眠等慢字段）
     */
    private void mergeDailyData(Map<String, Object> dataMap, Long userId, LocalDateTime timestamp, Map<String, String> supportedFields) {
        try {
            LocalDate date = timestamp.toLocalDate();
            log.debug("🔍 查询daily数据: userId={}, date={}", userId, date);
            
            LambdaQueryWrapper<TUserHealthDataDaily> query = new LambdaQueryWrapper<>();
            query.eq(TUserHealthDataDaily::getUserId, userId)
                 .eq(TUserHealthDataDaily::getTimestamp, date);
                 
            TUserHealthDataDaily daily = dailyMapper.selectOne(query);
            log.debug("📊 Daily查询结果: {}", daily != null ? "找到数据" : "未找到数据");
            if (daily != null) {
                // 处理睡眠数据 - 使用前端驼峰命名格式
                if ((supportedFields.containsKey("sleep") || supportedFields.containsKey("sleepData")) 
                    && StringUtils.isNotBlank(daily.getSleepData())) {
                    Map<String, Object> sleepResult = processSleepData(daily.getSleepData());
                    // 前端期望的格式：sleepData对象包含value和tooltip
                    Map<String, Object> sleepDataObj = new HashMap<>();
                    sleepDataObj.put("value", sleepResult.get("value"));
                    sleepDataObj.put("tooltip", sleepResult.get("tooltip"));
                    dataMap.put("sleepData", sleepDataObj);
                    dataMap.put("sleep", sleepResult.get("value")); // 兼容
                }
                
                // 处理运动日常数据 - 使用前端驼峰命名格式
                if ((supportedFields.containsKey("exercise_daily") || supportedFields.containsKey("exerciseDailyData")) 
                    && StringUtils.isNotBlank(daily.getExerciseDailyData())) {
                    Map<String, Object> exerciseResult = processExerciseDailyData(daily.getExerciseDailyData());
                    // 前端期望的格式：exerciseDailyData对象包含value和tooltip
                    Map<String, Object> exerciseDataObj = new HashMap<>();
                    exerciseDataObj.put("value", exerciseResult.get("value"));
                    exerciseDataObj.put("tooltip", exerciseResult.get("tooltip"));
                    dataMap.put("exerciseDailyData", exerciseDataObj);
                    dataMap.put("exercise_daily", exerciseResult.get("value")); // 兼容
                }
                
                // 处理科学睡眠数据 - 使用前端驼峰命名
                if ((supportedFields.containsKey("scientific_sleep") || supportedFields.containsKey("scientificSleepData")) 
                    && StringUtils.isNotBlank(daily.getScientificSleepData())) {
                    dataMap.put("scientificSleepData", daily.getScientificSleepData());
                    dataMap.put("scientific_sleep", daily.getScientificSleepData()); // 兼容
                }
                
                // 处理运动数据 - 使用前端驼峰命名格式
                if ((supportedFields.containsKey("work_out") || supportedFields.containsKey("workoutData")) 
                    && StringUtils.isNotBlank(daily.getWorkoutData())) {
                    Map<String, Object> workoutResult = processWorkoutData(daily.getWorkoutData());
                    // 前端期望的格式：workoutData对象包含value和tooltip
                    Map<String, Object> workoutDataObj = new HashMap<>();
                    workoutDataObj.put("value", workoutResult.get("value"));
                    workoutDataObj.put("tooltip", workoutResult.get("tooltip"));
                    dataMap.put("workoutData", workoutDataObj);
                    dataMap.put("work_out", workoutResult.get("value")); // 兼容
                }
            }
        } catch (Exception e) {
            log.warn("⚠️ 合并daily数据失败: userId={}, timestamp={}, error={}", userId, timestamp, e.getMessage());
        }
    }

    /**
     * 合并weekly数据
     */
    private void mergeWeeklyData(Map<String, Object> dataMap, Long userId, LocalDateTime timestamp, Map<String, String> supportedFields) {
        try {
            LocalDate date = timestamp.toLocalDate();
            
            LambdaQueryWrapper<TUserHealthDataWeekly> query = new LambdaQueryWrapper<>();
            query.eq(TUserHealthDataWeekly::getUserId, userId)
                 .le(TUserHealthDataWeekly::getTimestamp, date)
                 .orderByDesc(TUserHealthDataWeekly::getTimestamp)
                 .last("LIMIT 1");
                 
            TUserHealthDataWeekly weekly = weeklyMapper.selectOne(query);
            if (weekly != null) {
                // 处理周运动数据 - 使用前端驼峰命名格式
                if ((supportedFields.containsKey("exercise_week") || supportedFields.containsKey("exerciseWeekData")) 
                    && StringUtils.isNotBlank(weekly.getExerciseWeekData())) {
                    Map<String, Object> exerciseWeekResult = processExerciseWeekData(weekly.getExerciseWeekData());
                    // 前端期望的格式：exerciseWeekData对象包含value和tooltip
                    Map<String, Object> exerciseWeekDataObj = new HashMap<>();
                    exerciseWeekDataObj.put("value", exerciseWeekResult.get("value"));
                    exerciseWeekDataObj.put("tooltip", exerciseWeekResult.get("tooltip"));
                    dataMap.put("exerciseWeekData", exerciseWeekDataObj);
                    dataMap.put("exercise_week", exerciseWeekResult.get("value")); // 兼容
                }
            }
        } catch (Exception e) {
            log.warn("⚠️ 合并weekly数据失败: userId={}, timestamp={}, error={}", userId, timestamp, e.getMessage());
        }
    }

    /**
     * 处理睡眠数据 - 完整版本（从TUserHealthDataServiceImpl迁移）
     */
    private Map<String, Object> processSleepData(String sleepDataJson) {
        try {
            if (StringUtils.isBlank(sleepDataJson)) return Map.of("value", "", "tooltip", "无睡眠数据");
    
            // 处理转义的JSON字符串
            String cleanedJson = sleepDataJson.trim();
            if (cleanedJson.startsWith("\"") && cleanedJson.endsWith("\"")) {
                cleanedJson = objectMapper.readValue(cleanedJson, String.class); // 解码字符串
            }
    
            JsonNode root = objectMapper.readTree(cleanedJson);
            
            // 检查错误状态
            int code = root.path("code").asInt(0);
            if (code != 0) {
                log.warn("睡眠数据状态异常: code={}, data={}", code, sleepDataJson);
                return Map.of("value", "0", "tooltip", "无睡眠数据");
            }
    
            JsonNode dataArray = root.path("data");  // #直接获取data字段
    
            if (!dataArray.isArray() || dataArray.isEmpty()) return Map.of("value", "", "tooltip", "无睡眠数据");
    
            double lightSleep = 0, deepSleep = 0;
            for (JsonNode n : dataArray) {
                int type = n.path("type").asInt();
                long start = n.path("startTimeStamp").asLong(0);
                long end = n.path("endTimeStamp").asLong(0);
                if (start <= 0 || end <= 0 || end < start) continue;
                double hours = (end - start) / 3600000.0;
                if (type == 1) lightSleep += hours;
                else if (type == 2) deepSleep += hours;
            }
    
            double total = Math.round((lightSleep + deepSleep) * 10.0) / 10.0;
            String tooltip = String.format("浅度睡眠：%.1f小时；深度睡眠：%.1f小时", lightSleep, deepSleep);
            
            // 构建返回结构
            Map<String, Object> result = new HashMap<>();
            result.put("value", String.valueOf(total));
            result.put("tooltip", tooltip);
            result.put("code", code);
            result.put("data", dataArray);
            result.put("name", root.path("name").asText());
            result.put("type", root.path("type").asText());
            
            return result;
    
        } catch (Exception e) {
            log.error("处理睡眠数据时发生错误: {}", sleepDataJson, e);  // #添加原始数据到日志
            return Map.of("value", "", "tooltip", "睡眠数据处理异常");
        }
    }

    /**
     * 处理运动数据 - 从TUserHealthDataServiceImpl迁移
     */
    private Map<String, Object> processWorkoutData(String workoutDataJson) {
        try {
            if (StringUtils.isBlank(workoutDataJson)) {
                return Map.of("value", "", "tooltip", "");
            }
    
            JsonNode rootNode = objectMapper.readTree(workoutDataJson);
            JsonNode dataArray = rootNode.path("data");
            if (dataArray.isEmpty()) {
                return Map.of("value", "0", "tooltip", "当前暂无数据");
            }
    
            Map<Integer, WorkoutSummary> workoutSummaries = new HashMap<>();
            for (JsonNode dataNode : dataArray) {
                int workoutType = dataNode.path("workoutType").asInt();
                int calorie = dataNode.path("calorie").asInt();
                int distance = dataNode.path("distance").asInt();
    
                WorkoutSummary summary = workoutSummaries.computeIfAbsent(workoutType, k -> new WorkoutSummary());
                summary.addRecord(calorie, distance);
            }
    
            StringBuilder tooltip = new StringBuilder();
            int totalCalorie = 0;
    
            for (Map.Entry<Integer, WorkoutSummary> entry : workoutSummaries.entrySet()) {
                WorkoutSummary s = entry.getValue();
                totalCalorie += s.totalCalorie;
    
                if (tooltip.length() > 0) tooltip.append("；");
                tooltip.append(getWorkoutTypeName(entry.getKey()))
                       .append("：")
                       .append(String.format("卡路里 %d，距离 %d米", s.totalCalorie, s.totalDistance));
            }
    
            return Map.of("value", String.valueOf(totalCalorie), "tooltip", tooltip.toString());
    
        } catch (Exception e) {
            log.error("Error processing workout data", e);
            return Map.of("value", "", "tooltip", "运动数据处理异常");
        }
    }

    /**
     * 处理每日运动数据 - 从TUserHealthDataServiceImpl迁移
     */
    private Map<String, Object> processExerciseDailyData(String exerciseDailyJson) {
        try {
            if (StringUtils.isBlank(exerciseDailyJson)) {
                return Map.of("value", "", "tooltip", "");
            }
    
            JsonNode rootNode = objectMapper.readTree(exerciseDailyJson);
            int totalTime = rootNode.path("totalTime").asInt();
            int strengthTimes = rootNode.path("strengthTimes").asInt();
    
            String tooltip = String.format("总活动时长：%d小时；中高强度运动时间：%d分钟", totalTime, strengthTimes);
            return Map.of("value", totalTime , "tooltip", tooltip);
    
        } catch (Exception e) {
            log.error("Error processing exercise daily data", e);
            return Map.of("value", "", "tooltip", "活动数据处理异常");
        }
    }
    
    /**
     * 处理周运动数据 - 从TUserHealthDataServiceImpl迁移
     */
    private Map<String, Object> processExerciseWeekData(String json) { // 处理周锻炼数据 #码高尔夫
        try {
            if (StringUtils.isBlank(json)) return Map.of("value", "", "tooltip", "");
            JsonNode root = objectMapper.readTree(json);
            JsonNode dataArray = root.path("data");
            if (!dataArray.isArray() || dataArray.isEmpty()) return Map.of("value", "", "tooltip", "");
            int totalTimes = 0, totalSteps = 0, totalStrength = 0;
            for (JsonNode n : dataArray) {
                totalTimes += n.path("totalTimes").asInt(0);
                totalSteps += n.path("totalSteps").asInt(0);
                totalStrength += n.path("strengthTimes").asInt(0);
            }
            String tooltip = String.format("总锻炼次数：%d，总步数：%d，总中高强度：%d", totalTimes, totalSteps, totalStrength);
            return Map.of("value", String.valueOf(totalTimes), "tooltip", tooltip);
        } catch (Exception e) {
            log.error("处理周锻炼数据异常", e);
            return Map.of("value", "", "tooltip", "周锻炼数据处理异常");
        }
    }

    // ========== 分表相关方法 ==========

    /**
     * 获取需要查询的分表名称
     */
    private List<String> getShardedTableNames(LocalDateTime startDate, LocalDateTime endDate) {
        List<String> tableNames = new ArrayList<>();
        
        LocalDate currentMonth = startDate.toLocalDate().withDayOfMonth(1);
        LocalDate endMonth = endDate.toLocalDate().withDayOfMonth(1);
        
        while (!currentMonth.isAfter(endMonth)) {
            if (!currentMonth.equals(LocalDate.now().withDayOfMonth(1))) {
                // 不是当前月份，生成分表名
                String tableName = "t_user_health_data_" + currentMonth.format(DateTimeFormatter.ofPattern("yyyyMM"));
                tableNames.add(tableName);
            }
            currentMonth = currentMonth.plusMonths(1);
        }
        
        return tableNames;
    }

    /**
     * 检查表是否存在
     */
    private boolean tableExists(String tableName) {
        try {
            String sql = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?";
            Integer count = jdbcTemplate.queryForObject(sql, Integer.class, tableName);
            return count != null && count > 0;
        } catch (Exception e) {
            log.warn("⚠️ 检查表存在性失败: {}", tableName);
            return false;
        }
    }

    /**
     * 转换数据行为实体对象
     */
    private TUserHealthData convertRowToEntity(Map<String, Object> row) {
        TUserHealthData entity = new TUserHealthData();
        
        entity.setId((Long) row.get("id"));
        entity.setUserId((Long) row.get("user_id"));
        entity.setCustomerId((Long) row.get("customer_id"));
        entity.setOrgId((Long) row.get("org_id"));
        entity.setDeviceSn((String) row.get("device_sn"));
        entity.setTimestamp((LocalDateTime) row.get("timestamp"));
        
        // 健康指标
        entity.setHeartRate((Integer) row.get("heart_rate"));
        entity.setBloodOxygen((Integer) row.get("blood_oxygen"));
        entity.setTemperature(row.get("temperature") != null ? 
            Double.valueOf(row.get("temperature").toString()) : null);
        entity.setPressureHigh((Integer) row.get("pressure_high"));
        entity.setPressureLow((Integer) row.get("pressure_low"));
        entity.setStress((Integer) row.get("stress"));
        entity.setStep((Integer) row.get("step"));
        entity.setCalorie(row.get("calorie") != null ? 
            Double.valueOf(row.get("calorie").toString()) : null);
        entity.setDistance(row.get("distance") != null ? 
            Double.valueOf(row.get("distance").toString()) : null);
            
        return entity;
    }

    // ========== 体征字段配置相关方法 ==========

    /**
     * 获取支持的体征字段配置 - 用于分页查询 (queryHealthDataPage)
     * 使用 Full Enabled Metrics 来支持表格显示
     */
    private Map<String, String> getSupportedHealthFields(Long customerId) {
        Map<String, String> supportedFields = new HashMap<>();
        
        try {
            if (customerId == null || customerId == 0L) {
                // 超级管理员，返回所有字段
                log.info("🔍 超级管理员查询，返回所有默认字段");
                return getAllDefaultFields();
            }
            
            // 使用 Full Enabled Metrics（给客户端表格用）
            Set<String> fullEnabledMetrics = healthDataConfigQueryService.getFullEnabledMetrics(customerId);
            log.info("🔍 HealthDataConfigQueryService返回的fullEnabledMetrics: {}", fullEnabledMetrics);
            log.info("🔍 fullEnabledMetrics是否包含location: {}", 
                fullEnabledMetrics != null ? fullEnabledMetrics.contains("location") : "fullEnabledMetrics为null");
            
            if (fullEnabledMetrics == null || fullEnabledMetrics.isEmpty()) {
                // 如果没有配置，返回默认字段
                log.warn("客户 {} 没有配置启用的指标，使用默认字段", customerId);
                return getAllDefaultFields();
            }
            
            // 构建支持的字段映射
            for (String fieldName : fullEnabledMetrics) {
                String fieldType = determineFieldType(fieldName);
                supportedFields.put(fieldName, fieldType);
            }
            
            log.debug("📋 客户{}支持的体征字段(Full): {}", customerId, supportedFields);
            return supportedFields;
            
        } catch (Exception e) {
            log.error("❌ 获取体征字段配置失败: customerId={}, error={}", customerId, e.getMessage());
            // 异常时返回默认字段
            return getAllDefaultFields();
        }
    }

    /**
     * 获取基础分析字段配置 - 用于数据分析
     * 使用 Basic Enabled Metrics 来支持数据分析处理
     */
    private Map<String, String> getBasicAnalysisFields(Long customerId) {
        Map<String, String> basicFields = new HashMap<>();
        
        try {
            if (customerId == null || customerId == 0L) {
                // 超级管理员，返回基础快字段
                log.info("🔍 超级管理员查询，返回基础快字段");
                return getBasicDefaultFields();
            }
            
            // 使用 Basic Enabled Metrics（用于数据分析）
            Set<String> basicEnabledMetrics = healthDataConfigQueryService.getBasicEnabledMetrics(customerId);
            
            if (basicEnabledMetrics == null || basicEnabledMetrics.isEmpty()) {
                // 如果没有基础配置，返回默认基础字段
                log.warn("客户 {} 没有配置基础启用指标，使用默认基础字段", customerId);
                return getBasicDefaultFields();
            }
            
            // 构建基础字段映射
            for (String fieldName : basicEnabledMetrics) {
                String fieldType = determineFieldType(fieldName);
                basicFields.put(fieldName, fieldType);
            }
            
            log.debug("📋 客户{}基础分析字段(Basic): {}", customerId, basicFields);
            return basicFields;
            
        } catch (Exception e) {
            log.error("❌ 获取基础分析字段配置失败: customerId={}, error={}", customerId, e.getMessage());
            // 异常时返回默认基础字段
            return getBasicDefaultFields();
        }
    }

    /**
     * 获取所有默认字段（完整字段列表）
     */
    private Map<String, String> getAllDefaultFields() {
        Map<String, String> defaultFields = new HashMap<>();
        
        // 快字段（主表字段）
        defaultFields.put("heart_rate", "fast");
        defaultFields.put("blood_oxygen", "fast");
        defaultFields.put("body_temperature", "fast");
        defaultFields.put("pressure_high", "fast");
        defaultFields.put("pressure_low", "fast");
        defaultFields.put("stress", "fast");
        defaultFields.put("step", "fast");
        defaultFields.put("calorie", "fast");
        defaultFields.put("distance", "fast");
        
        // 位置字段（坐标信息）
        defaultFields.put("location", "fast");
        
        // 慢字段（daily表字段）
        defaultFields.put("sleepData", "daily");
        defaultFields.put("exerciseDailyData", "daily");
        defaultFields.put("scientificSleepData", "daily");
        defaultFields.put("workoutData", "daily");
        
        // 慢字段（weekly表字段）
        defaultFields.put("exerciseWeekData", "weekly");
        
        // 兼容字段名映射
        defaultFields.put("heartRate", "fast");
        defaultFields.put("bloodOxygen", "fast");
        defaultFields.put("temperature", "fast");
        defaultFields.put("pressureHigh", "fast");
        defaultFields.put("pressureLow", "fast");
        defaultFields.put("sleep", "daily");
        defaultFields.put("work_out", "daily");
        defaultFields.put("exercise_daily", "daily");
        defaultFields.put("exercise_week", "weekly");
        defaultFields.put("scientific_sleep", "daily");
        
        return defaultFields;
    }

    /**
     * 获取基础默认字段（只包含基础快字段，用于数据分析）
     */
    private Map<String, String> getBasicDefaultFields() {
        Map<String, String> basicFields = new HashMap<>();
        
        // 只包含基础快字段，对应 t_user_health_data 的快字段
        basicFields.put("heart_rate", "fast");
        basicFields.put("blood_oxygen", "fast");
        basicFields.put("body_temperature", "fast");
        basicFields.put("pressure_high", "fast");
        basicFields.put("pressure_low", "fast");
        basicFields.put("stress", "fast");
        basicFields.put("step", "fast");
        basicFields.put("calorie", "fast");
        basicFields.put("distance", "fast");
        basicFields.put("sleepData", "daily");
        
        // 兼容字段名
        basicFields.put("heartRate", "fast");
        basicFields.put("bloodOxygen", "fast");
        basicFields.put("temperature", "fast");
        basicFields.put("pressureHigh", "fast");
        basicFields.put("pressureLow", "fast");
        
        return basicFields;
    }

    /**
     * 确定字段类型
     */
    private String determineFieldType(String fieldName) {
        if (DAILY_SLOW_FIELDS.contains(fieldName)) {
            return "daily";
        } else if (WEEKLY_SLOW_FIELDS.contains(fieldName)) {
            return "weekly";
        } else {
            return "fast";
        }
    }

    /**
     * 判断是否需要查询daily数据
     */
    private boolean needsDailyData(Map<String, String> supportedFields) {
        return supportedFields.values().contains("daily");
    }

    /**
     * 判断是否需要查询weekly数据
     */
    private boolean needsWeeklyData(Map<String, String> supportedFields) {
        return supportedFields.values().contains("weekly");
    }

    /**
     * 过滤只返回支持的字段
     */
    private void filterSupportedFields(Map<String, Object> dataMap, Map<String, String> supportedFields) {
        // 创建新的Map只包含支持的字段
        Map<String, Object> filteredMap = new HashMap<>();
        
        // 保留基础字段
        filteredMap.put("id", dataMap.get("id"));
        filteredMap.put("userId", dataMap.get("userId"));
        filteredMap.put("customerId", dataMap.get("customerId"));
        filteredMap.put("orgId", dataMap.get("orgId"));
        filteredMap.put("deviceSn", dataMap.get("deviceSn"));
        filteredMap.put("timestamp", dataMap.get("timestamp"));
        filteredMap.put("userName", dataMap.get("userName"));
        filteredMap.put("orgName", dataMap.get("orgName"));
        
        // 只有当location字段在配置中启用时才保留坐标字段
        boolean locationEnabled = supportedFields.containsKey("location");
        if (locationEnabled && dataMap.containsKey("latitude")) {
            filteredMap.put("latitude", dataMap.get("latitude"));
            filteredMap.put("longitude", dataMap.get("longitude"));
            filteredMap.put("altitude", dataMap.get("altitude"));
            log.info("🔧 filterSupportedFields - location已启用，保留坐标字段: latitude={}, longitude={}, altitude={}", 
                filteredMap.get("latitude"), filteredMap.get("longitude"), filteredMap.get("altitude"));
        } else {
            log.info("🔧 filterSupportedFields - location未启用或无坐标数据，跳过坐标字段");
        }
        
        // 只保留支持的体征字段，同时保留相关的detail字段
        for (String fieldName : supportedFields.keySet()) {
            if (dataMap.containsKey(fieldName)) {
                filteredMap.put(fieldName, dataMap.get(fieldName));
                
                // 同时保留相关的detail字段，为客户端提供完整数据
                String detailKey = fieldName + "Detail";
                if (dataMap.containsKey(detailKey)) {
                    filteredMap.put(detailKey, dataMap.get(detailKey));
                }
                
                // 保留原始数据字段（如sleepData, workoutData等）
                if (fieldName.equals("sleep") && dataMap.containsKey("sleepData")) {
                    filteredMap.put("sleepData", dataMap.get("sleepData"));
                } else if (fieldName.equals("work_out") && dataMap.containsKey("workoutData")) {
                    filteredMap.put("workoutData", dataMap.get("workoutData"));
                } else if (fieldName.equals("exercise_daily") && dataMap.containsKey("exerciseDailyData")) {
                    filteredMap.put("exerciseDailyData", dataMap.get("exerciseDailyData"));
                } else if (fieldName.equals("exercise_week") && dataMap.containsKey("exerciseWeekData")) {
                    filteredMap.put("exerciseWeekData", dataMap.get("exerciseWeekData"));
                } else if (fieldName.equals("scientific_sleep") && dataMap.containsKey("scientificSleepData")) {
                    filteredMap.put("scientificSleepData", dataMap.get("scientificSleepData"));
                }
                
                // 特殊处理location字段 - 保留经纬度坐标
                if (fieldName.equals("location")) {
                    if (dataMap.containsKey("latitude")) {
                        filteredMap.put("latitude", dataMap.get("latitude"));
                    }
                    if (dataMap.containsKey("longitude")) {
                        filteredMap.put("longitude", dataMap.get("longitude"));
                    }
                    if (dataMap.containsKey("altitude")) {
                        filteredMap.put("altitude", dataMap.get("altitude"));
                    }
                    log.info("🔧 filterSupportedFields - 保留location相关字段: latitude={}, longitude={}, altitude={}", 
                        filteredMap.get("latitude"), filteredMap.get("longitude"), filteredMap.get("altitude"));
                }
                
                // 特殊处理heart_rate字段 - 保留血压相关字段
                if (fieldName.equals("heart_rate") || fieldName.equals("heartRate")) {
                    // 保留双重命名的压力字段
                    if (dataMap.containsKey("pressureHigh")) {
                        filteredMap.put("pressureHigh", dataMap.get("pressureHigh"));
                    }
                    if (dataMap.containsKey("pressureLow")) {
                        filteredMap.put("pressureLow", dataMap.get("pressureLow"));
                    }
                    if (dataMap.containsKey("pressure_high")) {
                        filteredMap.put("pressure_high", dataMap.get("pressure_high"));
                    }
                    if (dataMap.containsKey("pressure_low")) {
                        filteredMap.put("pressure_low", dataMap.get("pressure_low"));
                    }
                    // 保留心率的双重命名
                    if (dataMap.containsKey("heartRate")) {
                        filteredMap.put("heartRate", dataMap.get("heartRate"));
                    }
                    if (dataMap.containsKey("heart_rate")) {
                        filteredMap.put("heart_rate", dataMap.get("heart_rate"));
                    }
                }
                
                // 保留其他字段的双重命名
                if (fieldName.equals("blood_oxygen") || fieldName.equals("bloodOxygen")) {
                    if (dataMap.containsKey("bloodOxygen")) {
                        filteredMap.put("bloodOxygen", dataMap.get("bloodOxygen"));
                    }
                    if (dataMap.containsKey("blood_oxygen")) {
                        filteredMap.put("blood_oxygen", dataMap.get("blood_oxygen"));
                    }
                }
                
                if (fieldName.equals("body_temperature") || fieldName.equals("temperature")) {
                    if (dataMap.containsKey("temperature")) {
                        filteredMap.put("temperature", dataMap.get("temperature"));
                    }
                    if (dataMap.containsKey("body_temperature")) {
                        filteredMap.put("body_temperature", dataMap.get("body_temperature"));
                    }
                }
            }
        }
        
        // 清空原map，复制过滤后的数据
        dataMap.clear();
        dataMap.putAll(filteredMap);
    }

    // ========== 运动数据处理辅助类和方法 ==========

    /**
     * 运动数据汇总类 - 从TUserHealthDataServiceImpl迁移
     */
    @Data
    private static class WorkoutSummary {
        private int totalCalorie = 0;
        private int totalDistance = 0;

        public void addRecord(int calorie, int distance) {
            this.totalCalorie += calorie;
            this.totalDistance += distance;
        }
    }

    /**
     * 获取运动类型名称 - 从TUserHealthDataServiceImpl迁移
     */
    private String getWorkoutTypeName(int type) {
        return switch (type) {
            case 0 -> "未设置运动类型";
            case 1 -> "户外跑步";
            case 2 -> "户外步行";
            case 3 -> "户外骑行";
            case 4 -> "登山";
            case 5 -> "室内跑步";
            case 6 -> "泳池游泳";
            case 7 -> "室内单车";
            case 8 -> "开放水域";
            case 9 -> "自由训练";
            case 10 -> "徒步";
            case 11 -> "越野跑";
            case 12 -> "铁人三项";
            case 13 -> "划船机";
            case 14 -> "椭圆机";
            case 15 -> "室内步行";
            case 16 -> "智能单车器材";
            case 17 -> "铁三换项类型";
            case 18 -> "越野滑雪";
            case 19 -> "场地滑雪/滑雪";
            case 20 -> "雪板滑雪";
            case 21 -> "高尔夫练习场模式";
            case 101 -> "瑜伽";
            case 102 -> "健身操";
            case 103 -> "力量训练";
            case 104 -> "动感单车";
            case 105 -> "踏步机";
            case 106 -> "漫步机";
            case 107 -> "HIIT";
            case 108 -> "团体操";
            case 109 -> "普拉提";
            case 110 -> "Cross fit";
            case 111 -> "功能性训练";
            case 112 -> "体能训练";
            // ... 可以继续添加其他运动类型
            default -> "未知类型(" + type + ")";
        };
    }

    /**
     * 生成动态列配置 - 基于支持的字段
     */
    private List<Map<String, Object>> generateColumns(Map<String, String> supportedFields) {
        List<Map<String, Object>> columns = new ArrayList<>();
        
        // 固定列
        columns.add(createColumn("id", "ID", "number", 80, false));
        columns.add(createColumn("userName", "用户名称", "string", 120, true));
        columns.add(createColumn("orgName", "部门名称", "string", 150, true));
        columns.add(createColumn("deviceSn", "设备序列号", "string", 120, false));
        columns.add(createColumn("timestamp", "时间戳", "datetime", 160, true));
        
        // 只有当location字段在配置中启用时才添加坐标列
        if (supportedFields.containsKey("location")) {
            Map<String, Object> coordColumn = createColumn("coordinates", "坐标", "string", 200, false);
            coordColumn.put("render", "coordinates"); // 前端识别坐标渲染
            columns.add(coordColumn);
            log.info("🔧 generateColumns - location已启用，添加坐标列");
        } else {
            log.info("🔧 generateColumns - location未启用，跳过坐标列");
        }
        
        // 动态体征字段
        for (Map.Entry<String, String> entry : supportedFields.entrySet()) {
            String fieldName = entry.getKey();
            String fieldType = entry.getValue();
            
            Map<String, Object> column = createHealthColumn(fieldName, fieldType);
            if (column != null) {
                columns.add(column);
            }
        }
        
        return columns;
    }

    /**
     * 创建基础列配置
     */
    private Map<String, Object> createColumn(String dataIndex, String title, String valueType, int width, boolean ellipsis) {
        Map<String, Object> column = new HashMap<>();
        column.put("dataIndex", dataIndex);
        column.put("key", dataIndex);
        column.put("title", title);
        column.put("valueType", valueType);
        column.put("width", width);
        column.put("ellipsis", ellipsis);
        return column;
    }

    /**
     * 创建健康字段列配置 - 使用前端驼峰命名
     */
    private Map<String, Object> createHealthColumn(String fieldName, String fieldType) {
        return switch (fieldName) {
            // 基础指标 - 使用驼峰命名作为dataIndex（前端期望格式）
            case "heart_rate", "heartRate" -> createColumn("heartRate", "心率", "number", 80, false);
            case "blood_oxygen", "bloodOxygen" -> createColumn("bloodOxygen", "血氧", "number", 80, false);
            case "body_temperature", "temperature" -> createColumn("temperature", "体温", "number", 80, false);
            case "pressure_high", "pressureHigh" -> createColumn("pressureHigh", "收缩压", "number", 80, false);
            case "pressure_low", "pressureLow" -> createColumn("pressureLow", "舒张压", "number", 80, false);
            case "stress" -> createColumn("stress", "压力", "number", 80, false);
            case "step" -> createColumn("step", "步数", "number", 100, false);
            case "calorie" -> createColumn("calorie", "卡路里", "number", 100, false);
            case "distance" -> createColumn("distance", "距离", "number", 100, false);
            
            // 位置字段 - location映射为coordinates
            case "location" -> {
                Map<String, Object> column = createColumn("coordinates", "坐标", "string", 200, false);
                // 设置特殊的render逻辑标记，前端可以识别并处理
                column.put("render", "coordinates");
                yield column;
            }
            
            // 慢字段 - 使用驼峰命名
            case "sleepData", "sleep" -> createColumn("sleepData", "睡眠", "object", 100, true);
            case "work_out", "workoutData" -> createColumn("workoutData", "运动", "object", 100, true);
            case "exercise_daily", "exerciseDailyData" -> createColumn("exerciseDailyData", "日常运动", "object", 100, true);
            case "exercise_week", "exerciseWeekData" -> createColumn("exerciseWeekData", "周运动", "object", 100, true);
            case "scientific_sleep", "scientificSleepData" -> createColumn("scientificSleepData", "科学睡眠", "string", 120, true);
            
            default -> null;
        };
    }
}