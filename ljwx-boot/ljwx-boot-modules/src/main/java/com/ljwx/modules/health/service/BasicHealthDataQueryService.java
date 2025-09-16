/*
 * All Rights Reserved: Copyright [2024] [ljwx (brunoGao@gmail.com)]
 * Open Source Agreement: Apache License, Version 2.0
 */

package com.ljwx.modules.health.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.ljwx.common.api.Result;
import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.modules.health.domain.dto.UnifiedHealthQueryDTO;
import com.ljwx.modules.health.domain.entity.TUserHealthData;
import com.ljwx.modules.health.domain.vo.BasicHealthDataVO;
import com.ljwx.modules.health.repository.mapper.TUserHealthDataMapper;
import com.ljwx.modules.system.service.ISysUserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 基础健康数据查询服务
 * 专注于t_user_health_data表的快字段查询，提供高性能的表格数据展示
 * 不包含daily/weekly慢字段，避免复杂查询影响性能
 * 
 * @author Claude Code
 */
@Slf4j
@Service
public class BasicHealthDataQueryService {

    @Autowired
    private TUserHealthDataMapper healthDataMapper;
    
    @Autowired
    private ISysUserService sysUserService;
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    private static final String CACHE_PREFIX = "health:basic:page:";
    private static final int CACHE_EXPIRE_SECONDS = 300; // 5分钟缓存

    /**
     * 分页查询基础健康数据 - 仅快字段，高性能表格展示
     * 支持历史分表查询，解决跨月查询数据缺失问题
     */
    public Result<Map<String, Object>> getBasicHealthDataPage(UnifiedHealthQueryDTO queryDTO) {
        log.info("🚀 基础健康数据查询: customerId={}, userId={}, page={}, pageSize={}, 时间范围: {} ~ {}", 
                queryDTO.getCustomerId(), queryDTO.getUserId(), queryDTO.getPage(), queryDTO.getPageSize(),
                queryDTO.getStartDate(), queryDTO.getEndDate());
        
        try {
            // 1. 检查缓存
            String cacheKey = buildCacheKey(queryDTO);
            Object cachedResult = redisTemplate.opsForValue().get(cacheKey);
            if (cachedResult != null) {
                log.info("💾 缓存命中: {}", cacheKey);
                return Result.data((Map<String, Object>) cachedResult);
            }
            
            // 2. 查询主表数据
            List<TUserHealthData> mainData = queryMainTableData(queryDTO);
            log.info("📊 主表查询结果: {} 条", mainData.size());
            
            // 3. 查询历史分表数据（解决跨月查询问题）
            List<TUserHealthData> shardedData = queryShardedTableData(queryDTO);
            log.info("📊 分表查询结果: {} 条", shardedData.size());
            
            // 4. 合并数据
            List<TUserHealthData> combinedData = new ArrayList<>();
            combinedData.addAll(mainData);
            combinedData.addAll(shardedData);
            
            // 5. 按时间排序
            combinedData.sort(Comparator.comparing(TUserHealthData::getTimestamp).reversed());
            
            // 6. 应用分页
            long total = combinedData.size();
            int start = (queryDTO.getPage() - 1) * queryDTO.getPageSize();
            int end = Math.min(start + queryDTO.getPageSize(), combinedData.size());
            List<TUserHealthData> pageData = combinedData.subList(start, end);
            
            // 7. 转换为基础VO（仅包含快字段）
            List<BasicHealthDataVO> basicDataList = convertToBasicVO(pageData);
            
            // 8. 构建返回结果
            Map<String, Object> result = buildPageResult(total, basicDataList, queryDTO);
            
            // 9. 缓存结果
            cacheResult(cacheKey, result);
            
            log.info("✅ 基础健康数据查询完成: 总计{}条记录(主表{}+分表{}), 本页{}条记录", 
                    total, mainData.size(), shardedData.size(), basicDataList.size());
            return Result.data(result);
            
        } catch (Exception e) {
            log.error("❌ 基础健康数据查询失败: {}", e.getMessage(), e);
            return Result.failure("查询失败: " + e.getMessage());
        }
    }

    /**
     * 查询主表数据
     */
    private List<TUserHealthData> queryMainTableData(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> wrapper = buildQueryWrapper(queryDTO);
        return healthDataMapper.selectList(wrapper);
    }
    
    /**
     * 构建查询条件
     */
    private LambdaQueryWrapper<TUserHealthData> buildQueryWrapper(UnifiedHealthQueryDTO queryDTO) {
        LambdaQueryWrapper<TUserHealthData> wrapper = new LambdaQueryWrapper<>();
        
        // 客户ID过滤 - 当customerId为0时查询所有数据，否则按指定客户过滤
        if (queryDTO.getCustomerId() != null && queryDTO.getCustomerId() != 0L) {
            wrapper.eq(TUserHealthData::getCustomerId, queryDTO.getCustomerId());
        }
        // customerId为0时不添加过滤条件，返回所有客户的数据
        
        // 用户ID过滤
        if (queryDTO.getUserId() != null) {
            wrapper.eq(TUserHealthData::getUserId, queryDTO.getUserId());
        }
        
        // 组织ID过滤
        if (queryDTO.getOrgId() != null) {
            wrapper.eq(TUserHealthData::getOrgId, queryDTO.getOrgId());
        }
        
        // 设备序列号过滤
        if (queryDTO.getDeviceSn() != null) {
            wrapper.eq(TUserHealthData::getDeviceSn, queryDTO.getDeviceSn());
        }
        
        // 时间范围过滤
        if (queryDTO.getStartDate() != null) {
            wrapper.ge(TUserHealthData::getTimestamp, queryDTO.getStartDate());
        }
        if (queryDTO.getEndDate() != null) {
            wrapper.le(TUserHealthData::getTimestamp, queryDTO.getEndDate());
        }
        
        // 按时间降序排列
        wrapper.orderByDesc(TUserHealthData::getTimestamp);
        
        return wrapper;
    }

    /**
     * 转换为基础VO对象（仅包含快字段）
     */
    private List<BasicHealthDataVO> convertToBasicVO(List<TUserHealthData> healthDataList) {
        if (healthDataList == null || healthDataList.isEmpty()) {
            return new ArrayList<>();
        }
        
        return healthDataList.stream().map(this::convertSingleToBasicVO).collect(Collectors.toList());
    }

    /**
     * 转换单个实体为基础VO
     */
    private BasicHealthDataVO convertSingleToBasicVO(TUserHealthData data) {
        BasicHealthDataVO vo = new BasicHealthDataVO();
        
        // 基础信息
        vo.setId(data.getId());
        vo.setUserId(data.getUserId() != null ? data.getUserId().toString() : null);
        vo.setCustomerId(data.getCustomerId());
        vo.setOrgId(data.getOrgId());
        vo.setDeviceSn(data.getDeviceSn());
        vo.setTimestamp(data.getTimestamp());
        
        // 添加用户信息
        try {
            if (data.getUserId() != null) {
                var user = sysUserService.getById(data.getUserId());
                if (user != null) {
                    vo.setUserName(user.getUserName());
                    vo.setOrgName(user.getOrgName());
                } else {
                    vo.setUserName("未知用户");
                    vo.setOrgName("未知部门");
                }
            } else {
                vo.setUserName("未知用户");
                vo.setOrgName("未知部门");
            }
        } catch (Exception e) {
            log.warn("获取用户信息失败: userId={}", data.getUserId());
            vo.setUserName("未知用户");
            vo.setOrgName("未知部门");
        }
        
        // 基础生理指标（快字段）
        vo.setHeartRate(data.getHeartRate());
        vo.setBloodOxygen(data.getBloodOxygen());
        vo.setTemperature(data.getTemperature());
        vo.setPressureHigh(data.getPressureHigh());
        vo.setPressureLow(data.getPressureLow());
        vo.setStress(data.getStress());
        vo.setStep(data.getStep());
        vo.setCalorie(data.getCalorie());
        vo.setDistance(data.getDistance());
        
        // 位置信息
        vo.setLatitude(data.getLatitude());
        vo.setLongitude(data.getLongitude());
        vo.setAltitude(data.getAltitude());
        
        return vo;
    }

    /**
     * 构建分页返回结果 - 支持自定义总数（用于分表查询）
     */
    private Map<String, Object> buildPageResult(long total, 
                                               List<BasicHealthDataVO> basicDataList, 
                                               UnifiedHealthQueryDTO queryDTO) {
        Map<String, Object> result = new HashMap<>();
        result.put("total", total);
        result.put("pages", (int) Math.ceil((double) total / queryDTO.getPageSize()));
        result.put("records", basicDataList);
        result.put("pageSize", queryDTO.getPageSize());
        result.put("page", queryDTO.getPage());
        
        // 构建基础列定义（仅快字段）
        result.put("columns", buildBasicColumns());
        
        return result;
    }

    /**
     * 构建基础列定义（仅快字段）
     */
    private List<Map<String, Object>> buildBasicColumns() {
        List<Map<String, Object>> columns = new ArrayList<>();
        
        // 基础信息列
        columns.add(Map.of("dataIndex", "id", "title", "ID", "valueType", "number", "width", 80, "key", "id"));
        columns.add(Map.of("dataIndex", "userName", "title", "用户名称", "valueType", "string", "width", 120, "key", "userName"));
        columns.add(Map.of("dataIndex", "orgName", "title", "部门名称", "valueType", "string", "width", 150, "key", "orgName"));
        columns.add(Map.of("dataIndex", "deviceSn", "title", "设备序列号", "valueType", "string", "width", 120, "key", "deviceSn"));
        columns.add(Map.of("dataIndex", "timestamp", "title", "时间戳", "valueType", "datetime", "width", 160, "key", "timestamp"));
        
        // 生理指标列
        columns.add(Map.of("dataIndex", "heartRate", "title", "心率", "valueType", "number", "width", 80, "key", "heartRate"));
        columns.add(Map.of("dataIndex", "bloodOxygen", "title", "血氧", "valueType", "number", "width", 80, "key", "bloodOxygen"));
        columns.add(Map.of("dataIndex", "pressureHigh", "title", "收缩压", "valueType", "number", "width", 80, "key", "pressureHigh"));
        columns.add(Map.of("dataIndex", "pressureLow", "title", "舒张压", "valueType", "number", "width", 80, "key", "pressureLow"));
        columns.add(Map.of("dataIndex", "temperature", "title", "体温", "valueType", "number", "width", 80, "key", "temperature"));
        columns.add(Map.of("dataIndex", "stress", "title", "压力", "valueType", "number", "width", 80, "key", "stress"));
        
        // 活动指标列
        columns.add(Map.of("dataIndex", "step", "title", "步数", "valueType", "number", "width", 100, "key", "step"));
        columns.add(Map.of("dataIndex", "calorie", "title", "卡路里", "valueType", "number", "width", 100, "key", "calorie"));
        columns.add(Map.of("dataIndex", "distance", "title", "距离", "valueType", "number", "width", 100, "key", "distance"));
        
        // 位置信息列
        Map<String, Object> coordColumn = new HashMap<>();
        coordColumn.put("dataIndex", "coordinates");
        coordColumn.put("title", "坐标");
        coordColumn.put("valueType", "string");
        coordColumn.put("width", 200);
        coordColumn.put("key", "coordinates");
        coordColumn.put("render", "coordinates");
        columns.add(coordColumn);
        
        return columns;
    }

    /**
     * 构建缓存key
     */
    private String buildCacheKey(UnifiedHealthQueryDTO queryDTO) {
        return CACHE_PREFIX + 
               (queryDTO.getCustomerId() != null ? queryDTO.getCustomerId() : 0L) + ":" +
               (queryDTO.getUserId() != null ? queryDTO.getUserId() : "all") + ":" +
               (queryDTO.getOrgId() != null ? queryDTO.getOrgId() : "all") + ":" +
               (queryDTO.getStartDate() != null ? queryDTO.getStartDate().toString() : "nostart") + ":" +
               (queryDTO.getEndDate() != null ? queryDTO.getEndDate().toString() : "noend") + ":" +
               queryDTO.getPage() + ":" + 
               queryDTO.getPageSize();
    }

    /**
     * 缓存查询结果
     */
    private void cacheResult(String cacheKey, Map<String, Object> result) {
        try {
            redisTemplate.opsForValue().set(cacheKey, result, CACHE_EXPIRE_SECONDS, TimeUnit.SECONDS);
            log.debug("💾 查询结果已缓存: {}, TTL: {}秒", cacheKey, CACHE_EXPIRE_SECONDS);
        } catch (Exception e) {
            log.warn("⚠️ 缓存设置失败: {}", e.getMessage());
        }
    }
    
    // ========== 分表查询方法（从UnifiedHealthDataQueryService迁移） ==========
    
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
     * 获取需要查询的分表名称
     */
    private List<String> getShardedTableNames(LocalDateTime startDate, LocalDateTime endDate) {
        List<String> tableNames = new ArrayList<>();
        
        if (startDate == null || endDate == null) {
            return tableNames;
        }
        
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
            
        // 位置信息
        entity.setLatitude(row.get("latitude") != null ? 
            Double.valueOf(row.get("latitude").toString()) : null);
        entity.setLongitude(row.get("longitude") != null ? 
            Double.valueOf(row.get("longitude").toString()) : null);
        entity.setAltitude(row.get("altitude") != null ? 
            Double.valueOf(row.get("altitude").toString()) : null);
            
        return entity;
    }
}