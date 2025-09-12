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

import com.ljwx.infrastructure.page.PageQuery;
import com.ljwx.infrastructure.page.RPage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 统一健康数据查询服务 - 为所有健康功能提供统一的数据访问接口
 *
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.service.HealthDataService
 * @CreateTime 2025-09-11
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class HealthDataService {

    private final JdbcTemplate jdbcTemplate;

    /**
     * 获取健康基线分页数据
     */
    public RPage<Map<String, Object>> getHealthBaselinePage(PageQuery pageQuery, Long customerId) {
        log.info("获取健康基线分页数据 - page: {}, size: {}, customerId: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT b.*, u.real_name, u.user_name, u.org_id, u.org_name ");
        sql.append("FROM t_health_baseline b ");
        sql.append("LEFT JOIN sys_user u ON b.user_id = u.id ");
        sql.append("WHERE (b.is_deleted = 0 OR b.is_deleted IS NULL)");
        
        return executeHealthQuery(sql, pageQuery, customerId, "b.customer_id", this::convertBaselineRecord);
    }
    
    /**
     * 根据ID获取健康基线详情
     */
    public Map<String, Object> getHealthBaselineById(Long id) {
        log.info("获取健康基线详情 - id: {}", id);
        
        String sql = "SELECT b.*, u.real_name, u.user_name, u.org_id, u.org_name " +
                    "FROM t_health_baseline b " +
                    "LEFT JOIN sys_user u ON b.user_id = u.id " +
                    "WHERE b.id = ?";
        
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql, id);
        if (records.isEmpty()) {
            return null;
        }
        
        return convertBaselineRecord(records.get(0));
    }

    /**
     * 获取健康评分分页数据
     */
    public RPage<Map<String, Object>> getHealthScorePage(PageQuery pageQuery, Long customerId) {
        log.info("获取健康评分分页数据 - page: {}, size: {}, customerId: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT s.*, u.real_name, u.user_name, u.org_id, u.org_name ");
        sql.append("FROM t_health_score s ");
        sql.append("LEFT JOIN sys_user u ON s.user_id = u.id ");
        sql.append("WHERE (s.is_deleted = 0 OR s.is_deleted IS NULL)");
        
        return executeHealthQuery(sql, pageQuery, customerId, "s.customer_id", this::convertScoreRecord);
    }

    /**
     * 根据ID获取健康评分详情
     */
    public Map<String, Object> getHealthScoreById(Long id) {
        log.info("获取健康评分详情 - id: {}", id);
        
        String sql = "SELECT s.*, u.real_name, u.user_name, u.org_id, u.org_name " +
                    "FROM t_health_score s " +
                    "LEFT JOIN sys_user u ON s.user_id = u.id " +
                    "WHERE s.id = ?";
        
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql, id);
        if (records.isEmpty()) {
            return null;
        }
        
        return convertScoreRecord(records.get(0));
    }
    
    /**
     * 获取健康预测分页数据
     */
    public RPage<Map<String, Object>> getHealthPredictionPage(PageQuery pageQuery, Long customerId) {
        log.info("获取健康预测分页数据 - page: {}, size: {}, customerId: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT p.*, u.real_name, u.user_name, u.org_id, u.org_name ");
        sql.append("FROM t_health_prediction p ");
        sql.append("LEFT JOIN sys_user u ON p.user_id = u.id ");
        sql.append("WHERE (p.is_deleted = 0 OR p.is_deleted IS NULL)");
        
        return executeHealthQuery(sql, pageQuery, customerId, "p.customer_id", this::convertPredictionRecord);
    }

    /**
     * 根据ID获取健康预测详情
     */
    public Map<String, Object> getHealthPredictionById(Long id) {
        log.info("获取健康预测详情 - id: {}", id);
        
        String sql = "SELECT p.*, u.real_name, u.user_name, u.org_id, u.org_name " +
                    "FROM t_health_prediction p " +
                    "LEFT JOIN sys_user u ON p.user_id = u.id " +
                    "WHERE p.id = ?";
        
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql, id);
        if (records.isEmpty()) {
            return null;
        }
        
        return convertPredictionRecord(records.get(0));
    }
    
    /**
     * 获取健康建议分页数据
     */
    public RPage<Map<String, Object>> getHealthRecommendationPage(PageQuery pageQuery, Long customerId) {
        log.info("获取健康建议分页数据 - page: {}, size: {}, customerId: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT r.*, u.real_name, u.user_name, u.org_id, u.org_name ");
        sql.append("FROM t_health_recommendation_track r ");
        sql.append("LEFT JOIN sys_user u ON r.user_id = u.id ");
        sql.append("WHERE (r.is_deleted = 0 OR r.is_deleted IS NULL)");
        
        return executeHealthQuery(sql, pageQuery, customerId, "r.customer_id", this::convertRecommendationRecord);
    }

    /**
     * 根据ID获取健康建议详情
     */
    public Map<String, Object> getHealthRecommendationById(Long id) {
        log.info("获取健康建议详情 - id: {}", id);
        
        String sql = "SELECT r.*, u.real_name, u.user_name, u.org_id, u.org_name " +
                    "FROM t_health_recommendation_track r " +
                    "LEFT JOIN sys_user u ON r.user_id = u.id " +
                    "WHERE r.id = ?";
        
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql, id);
        if (records.isEmpty()) {
            return null;
        }
        
        return convertRecommendationRecord(records.get(0));
    }
    
    /**
     * 获取健康档案分页数据
     */
    public RPage<Map<String, Object>> getHealthProfilePage(PageQuery pageQuery, Long customerId) {
        log.info("获取健康档案分页数据 - page: {}, size: {}, customerId: {}", 
                pageQuery.getPage(), pageQuery.getPageSize(), customerId);
        
        StringBuilder sql = new StringBuilder();
        sql.append("SELECT p.*, u.real_name, u.user_name, u.org_id, u.org_name ");
        sql.append("FROM t_health_profile p ");
        sql.append("LEFT JOIN sys_user u ON p.user_id = u.id ");
        sql.append("WHERE (p.is_deleted = 0 OR p.is_deleted IS NULL)");
        
        return executeHealthQuery(sql, pageQuery, customerId, "p.customer_id", this::convertProfileRecord);
    }

    /**
     * 根据ID获取健康档案详情
     */
    public Map<String, Object> getHealthProfileById(Long id) {
        log.info("获取健康档案详情 - id: {}", id);
        
        String sql = "SELECT p.*, u.real_name, u.user_name, u.org_id, u.org_name " +
                    "FROM t_health_profile p " +
                    "LEFT JOIN sys_user u ON p.user_id = u.id " +
                    "WHERE p.id = ?";
        
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql, id);
        if (records.isEmpty()) {
            return null;
        }
        
        return convertProfileRecord(records.get(0));
    }
    
    /**
     * 统一的健康数据查询执行方法
     */
    private RPage<Map<String, Object>> executeHealthQuery(StringBuilder sql, PageQuery pageQuery, 
                                                          Long customerId, String customerIdField,
                                                          Function<Map<String, Object>, Map<String, Object>> converter) {
        List<Object> params = new ArrayList<>();
        if (customerId != null) {
            sql.append(" AND ").append(customerIdField).append(" = ?");
            params.add(customerId);
        }
        sql.append(" ORDER BY create_time DESC");
        
        // 计算总数
        String countSql = "SELECT COUNT(*) FROM (" + sql.toString() + ") t";
        Long total = jdbcTemplate.queryForObject(countSql, params.toArray(), Long.class);
        
        // 添加分页
        long offset = (pageQuery.getPage() - 1) * pageQuery.getPageSize();
        sql.append(" LIMIT ").append(pageQuery.getPageSize()).append(" OFFSET ").append(offset);
        
        // 执行查询
        List<Map<String, Object>> records = jdbcTemplate.queryForList(sql.toString(), params.toArray());
        
        // 转换数据格式
        List<Map<String, Object>> convertedRecords = records.stream()
                .map(converter)
                .collect(Collectors.toList());
        
        // 计算总页数
        long totalPages = (total + pageQuery.getPageSize() - 1) / pageQuery.getPageSize();
        
        return new RPage<>(pageQuery.getPage(), pageQuery.getPageSize(), convertedRecords, totalPages, total);
    }
    
    /**
     * 转换健康基线数据记录
     */
    private Map<String, Object> convertBaselineRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", record.get("id"));
        result.put("userId", record.get("user_id"));
        result.put("deviceSn", record.get("device_sn"));
        result.put("customerId", record.get("customer_id"));
        result.put("featureName", getFeatureDisplayName((String) record.get("feature_name")));
        result.put("baselineDate", record.get("baseline_date"));
        result.put("meanValue", record.get("mean_value"));
        result.put("stdValue", record.get("std_value"));
        result.put("minValue", record.get("min_value"));
        result.put("maxValue", record.get("max_value"));
        result.put("sampleCount", record.get("sample_count"));
        result.put("current", record.get("is_current"));
        result.put("baselineTime", record.get("baseline_time"));
        result.put("createTime", record.get("create_time"));
        
        addUserOrgInfo(result, record);
        return result;
    }
    
    /**
     * 转换健康评分数据记录
     */
    private Map<String, Object> convertScoreRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", record.get("id"));
        result.put("userId", record.get("user_id"));
        result.put("customerId", record.get("customer_id"));
        result.put("scoreDate", record.get("score_date"));
        result.put("overallScore", record.get("overall_score"));
        result.put("heartRateScore", record.get("heart_rate_score"));
        result.put("bloodOxygenScore", record.get("blood_oxygen_score"));
        result.put("temperatureScore", record.get("temperature_score"));
        result.put("bloodPressureScore", record.get("blood_pressure_score"));
        result.put("stressScore", record.get("stress_score"));
        result.put("sleepScore", record.get("sleep_score"));
        result.put("activityScore", record.get("activity_score"));
        result.put("createTime", record.get("create_time"));
        
        addUserOrgInfo(result, record);
        return result;
    }
    
    /**
     * 转换健康预测数据记录
     */
    private Map<String, Object> convertPredictionRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", record.get("id"));
        result.put("userId", record.get("user_id"));
        result.put("customerId", record.get("customer_id"));
        result.put("predictionType", record.get("prediction_type"));
        result.put("featureName", getFeatureDisplayName((String) record.get("feature_name")));
        result.put("predictedValue", record.get("predicted_value"));
        result.put("confidence", record.get("confidence"));
        result.put("predictionDate", record.get("prediction_date"));
        result.put("validUntil", record.get("valid_until"));
        result.put("createTime", record.get("create_time"));
        
        addUserOrgInfo(result, record);
        return result;
    }
    
    /**
     * 转换健康建议数据记录
     */
    private Map<String, Object> convertRecommendationRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", record.get("id"));
        result.put("userId", record.get("user_id"));
        result.put("customerId", record.get("customer_id"));
        result.put("recommendationType", record.get("recommendation_type"));
        result.put("title", record.get("title"));
        result.put("content", record.get("content"));
        result.put("priority", record.get("priority"));
        result.put("status", record.get("status"));
        result.put("effectiveDate", record.get("effective_date"));
        result.put("expiryDate", record.get("expiry_date"));
        result.put("createTime", record.get("create_time"));
        
        addUserOrgInfo(result, record);
        return result;
    }
    
    /**
     * 转换健康档案数据记录
     */
    private Map<String, Object> convertProfileRecord(Map<String, Object> record) {
        Map<String, Object> result = new HashMap<>();
        result.put("id", record.get("id"));
        result.put("userId", record.get("user_id"));
        result.put("customerId", record.get("customer_id"));
        result.put("profileData", record.get("profile_data"));
        result.put("lastUpdated", record.get("last_updated"));
        result.put("createTime", record.get("create_time"));
        
        addUserOrgInfo(result, record);
        return result;
    }
    
    /**
     * 添加用户和组织信息到结果中
     */
    private void addUserOrgInfo(Map<String, Object> result, Map<String, Object> record) {
        String realName = (String) record.get("real_name");
        String userName = (String) record.get("user_name");
        result.put("userName", realName != null ? realName : (userName != null ? userName : "未知用户"));
        result.put("orgName", record.get("org_name") != null ? record.get("org_name") : "未知部门");
        result.put("orgId", record.get("org_id"));
    }
    
    /**
     * 获取特征显示名称
     */
    private String getFeatureDisplayName(String featureName) {
        if (featureName == null) return "未知";
        switch (featureName) {
            case "heart_rate": return "心率";
            case "blood_oxygen": return "血氧";
            case "temperature": return "体温";
            case "blood_pressure": return "血压";
            case "pressure_high": return "收缩压";
            case "pressure_low": return "舒张压";
            case "step": return "步数";
            case "sleep": return "睡眠";
            case "stress": return "压力";
            case "calorie": return "卡路里";
            case "distance": return "距离";
            default: return featureName;
        }
    }
}