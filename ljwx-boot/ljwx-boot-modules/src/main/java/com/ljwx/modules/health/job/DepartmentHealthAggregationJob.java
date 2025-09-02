package com.ljwx.modules.health.job;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;

/**
 * 部门健康基线聚合作业 - 基于组织闭包表优化
 * 利用sys_org_closure实现高效的层级聚合查询
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.job.DepartmentHealthAggregationJob
 * @CreateTime 2025-08-31
 */
@Slf4j
@Component
public class DepartmentHealthAggregationJob {

    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    private static final String[] HEALTH_FEATURES = {
        "heart_rate", "blood_oxygen", "temperature", "pressure_high", 
        "pressure_low", "stress", "step", "calorie", "distance", "sleep"
    };

    /**
     * 执行部门健康基线聚合 - 利用闭包表快速聚合
     * 由个人health_baseline聚合成部门health_baseline
     */
    @Transactional(rollbackFor = Exception.class)
    public void execute() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始执行部门健康基线聚合，日期: {} (基于组织闭包表)", dateStr);
        
        try {
            // 1. 清理昨日的部门基线数据
            cleanupDepartmentBaselines(dateStr);
            
            // 2. 基于闭包表快速聚合部门基线
            int totalAggregated = 0;
            for (String feature : HEALTH_FEATURES) {
                int aggregatedCount = aggregateDepartmentBaselineForFeature(feature, dateStr);
                totalAggregated += aggregatedCount;
                log.info("✅ 特征 {} 部门基线聚合完成: {} 个部门", feature, aggregatedCount);
            }
            
            log.info("🎉 部门健康基线聚合任务完成，总计: {} 条记录", totalAggregated);
            
        } catch (Exception e) {
            log.error("❌ 部门健康基线聚合失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("部门健康基线聚合失败: " + e.getMessage(), e);
        }
    }

    /**
     * 清理指定日期的部门基线数据
     */
    private void cleanupDepartmentBaselines(String dateStr) {
        try {
            String deleteSql = "DELETE FROM t_org_health_baseline WHERE baseline_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理旧部门基线数据: {} 条 ({})", deletedRows, dateStr);
            }
        } catch (Exception e) {
            log.error("❌ 清理部门基线数据失败: {}", e.getMessage());
        }
    }

    /**
     * 为单个特征聚合部门基线 - 利用闭包表实现高效层级聚合
     */
    private int aggregateDepartmentBaselineForFeature(String feature, String dateStr) {
        try {
            String aggregationSql = """
                INSERT INTO t_org_health_baseline (
                    org_id, feature_name, baseline_date, mean_value, std_value,
                    min_value, max_value, user_count, sample_count, 
                    create_time, update_time
                )
                SELECT 
                    dept.department_id as org_id,
                    ? as feature_name,
                    ? as baseline_date,
                    AVG(hb.mean_value) as mean_value,
                    COALESCE(STD(hb.mean_value), 0) as std_value,
                    MIN(hb.min_value) as min_value,
                    MAX(hb.max_value) as max_value,
                    COUNT(DISTINCT hb.user_id) as user_count,
                    SUM(hb.sample_count) as sample_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        c.ancestor_id as department_id,
                        uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    JOIN sys_user u ON u.id = uo.user_id
                    WHERE c.depth >= 0
                      AND uo.is_deleted = 0
                      AND u.is_deleted = 0
                      AND u.device_sn IS NOT NULL 
                      AND u.device_sn != ''
                ) dept
                JOIN t_health_baseline hb ON hb.user_id = dept.user_id
                WHERE hb.feature_name = ?
                  AND hb.baseline_date = ?
                  AND hb.mean_value IS NOT NULL
                GROUP BY dept.department_id
                HAVING COUNT(DISTINCT hb.user_id) >= 1
                """;
                
            int aggregatedCount = jdbcTemplate.update(aggregationSql, feature, dateStr, feature, dateStr);
            
            if (aggregatedCount > 0) {
                log.debug("✅ 特征 {} 聚合了 {} 个部门的基线", feature, aggregatedCount);
            }
            
            return aggregatedCount;
            
        } catch (Exception e) {
            log.error("❌ 聚合部门基线失败，特征: {}, 错误: {}", feature, e.getMessage());
            return 0;
        }
    }

    /**
     * 生成部门健康评分 - 基于部门基线数据
     */
    @Transactional(rollbackFor = Exception.class)
    public void generateDepartmentHealthScores() {
        LocalDate yesterday = LocalDate.now().minusDays(1);
        String dateStr = yesterday.toString();
        
        log.info("🔄 开始生成部门健康评分，日期: {} (基于组织闭包表)", dateStr);
        
        try {
            // 清理昨日的部门评分数据
            String deleteSql = "DELETE FROM t_org_health_score WHERE score_date = ?";
            int deletedRows = jdbcTemplate.update(deleteSql, dateStr);
            if (deletedRows > 0) {
                log.info("🧹 清理旧部门评分数据: {} 条", deletedRows);
            }
            
            // 生成部门评分，基于个人评分聚合
            String scoreSql = """
                INSERT INTO t_org_health_score (
                    org_id, feature_name, score_date, mean_score, std_score,
                    min_score, max_score, user_count, create_time, update_time
                )
                SELECT 
                    dept.department_id as org_id,
                    hs.feature_name,
                    hs.score_date,
                    AVG(hs.score_value - COALESCE(hs.penalty_value, 0)) as mean_score,
                    COALESCE(STD(hs.score_value - COALESCE(hs.penalty_value, 0)), 0) as std_score,
                    MIN(hs.score_value - COALESCE(hs.penalty_value, 0)) as min_score,
                    MAX(hs.score_value - COALESCE(hs.penalty_value, 0)) as max_score,
                    COUNT(DISTINCT hs.user_id) as user_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT
                        c.ancestor_id as department_id,
                        uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    JOIN sys_user u ON u.id = uo.user_id
                    WHERE c.depth >= 0
                      AND uo.is_deleted = 0
                      AND u.is_deleted = 0
                      AND u.device_sn IS NOT NULL
                ) dept
                JOIN t_health_score hs ON hs.user_id = dept.user_id
                WHERE hs.score_date = ?
                  AND hs.score_value IS NOT NULL
                GROUP BY dept.department_id, hs.feature_name
                HAVING COUNT(DISTINCT hs.user_id) >= 1
                """;
                
            int scoreCount = jdbcTemplate.update(scoreSql, dateStr);
            log.info("🎉 部门健康评分生成完成，日期: {}, 共 {} 条记录", dateStr, scoreCount);
            
        } catch (Exception e) {
            log.error("❌ 部门健康评分生成失败，日期: {}, 错误: {}", dateStr, e.getMessage(), e);
            throw new RuntimeException("部门健康评分生成失败: " + e.getMessage(), e);
        }
    }

    /**
     * 获取部门健康概览统计 - 演示闭包表查询效率
     */
    public Map<String, Object> getDepartmentHealthOverview(Long departmentId, String date) {
        try {
            // 利用闭包表快速查询部门及其子部门的健康统计
            String overviewSql = """
                SELECT 
                    COUNT(DISTINCT dept_users.user_id) as total_users,
                    COUNT(DISTINCT hb.user_id) as users_with_baseline,
                    COUNT(DISTINCT hs.user_id) as users_with_score,
                    AVG(hb.mean_value) as dept_avg_baseline,
                    AVG(hs.score_value - COALESCE(hs.penalty_value, 0)) as dept_avg_score,
                    COUNT(DISTINCT hb.feature_name) as baseline_features,
                    COUNT(DISTINCT hs.feature_name) as score_features
                FROM (
                    SELECT DISTINCT uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    JOIN sys_user u ON u.id = uo.user_id
                    WHERE c.ancestor_id = ?
                      AND c.depth >= 0
                      AND uo.is_deleted = 0
                      AND u.is_deleted = 0
                      AND u.device_sn IS NOT NULL
                ) dept_users
                LEFT JOIN t_health_baseline hb ON hb.user_id = dept_users.user_id 
                    AND hb.baseline_date = ?
                LEFT JOIN t_health_score hs ON hs.user_id = dept_users.user_id 
                    AND hs.score_date = ?
                """;
            
            List<Map<String, Object>> result = jdbcTemplate.queryForList(overviewSql, 
                departmentId, date, date);
            
            if (!result.isEmpty()) {
                Map<String, Object> overview = result.get(0);
                log.info("📊 部门 {} 健康概览: 总用户 {}, 有基线 {}, 有评分 {}", 
                    departmentId, overview.get("total_users"), 
                    overview.get("users_with_baseline"), overview.get("users_with_score"));
                return overview;
            }
            
            return Map.of("message", "无数据");
            
        } catch (Exception e) {
            log.error("❌ 获取部门健康概览失败: {}", e.getMessage());
            return Map.of("error", e.getMessage());
        }
    }

    /**
     * 级联更新父部门基线 - 当子部门基线更新时
     */
    @Transactional(rollbackFor = Exception.class)
    public void cascadeUpdateParentDepartmentBaselines(Long departmentId, String date) {
        try {
            log.info("🔄 开始级联更新父部门基线，部门: {}, 日期: {}", departmentId, date);
            
            // 利用闭包表查找所有父部门（depth > 0的ancestor）
            String parentDeptSql = """
                SELECT DISTINCT c.ancestor_id as parent_dept_id
                FROM sys_org_closure c
                WHERE c.descendant_id = ?
                  AND c.depth > 0
                ORDER BY c.depth
                """;
            
            List<Map<String, Object>> parentDepts = jdbcTemplate.queryForList(parentDeptSql, departmentId);
            
            for (Map<String, Object> parent : parentDepts) {
                Long parentDeptId = ((Number) parent.get("parent_dept_id")).longValue();
                
                // 为每个父部门重新计算基线
                for (String feature : HEALTH_FEATURES) {
                    updateParentDepartmentBaseline(parentDeptId, feature, date);
                }
                
                log.info("✅ 更新父部门 {} 基线完成", parentDeptId);
            }
            
            log.info("🎉 级联更新完成，影响 {} 个父部门", parentDepts.size());
            
        } catch (Exception e) {
            log.error("❌ 级联更新父部门基线失败: {}", e.getMessage(), e);
            throw new RuntimeException("级联更新失败: " + e.getMessage(), e);
        }
    }

    /**
     * 更新单个父部门的特定特征基线
     */
    private void updateParentDepartmentBaseline(Long parentDeptId, String feature, String date) {
        try {
            // 删除现有的父部门基线记录
            String deleteSql = """
                DELETE FROM t_org_health_baseline 
                WHERE org_id = ? AND feature_name = ? AND baseline_date = ?
                """;
            jdbcTemplate.update(deleteSql, parentDeptId, feature, date);
            
            // 重新计算并插入父部门基线
            String insertSql = """
                INSERT INTO t_org_health_baseline (
                    org_id, feature_name, baseline_date, mean_value, std_value,
                    min_value, max_value, user_count, sample_count, 
                    create_time, update_time
                )
                SELECT 
                    ? as org_id,
                    ? as feature_name,
                    ? as baseline_date,
                    AVG(hb.mean_value) as mean_value,
                    COALESCE(STD(hb.mean_value), 0) as std_value,
                    MIN(hb.min_value) as min_value,
                    MAX(hb.max_value) as max_value,
                    COUNT(DISTINCT hb.user_id) as user_count,
                    SUM(hb.sample_count) as sample_count,
                    NOW() as create_time,
                    NOW() as update_time
                FROM (
                    SELECT DISTINCT uo.user_id
                    FROM sys_org_closure c
                    JOIN sys_user_org uo ON uo.org_id = c.descendant_id
                    JOIN sys_user u ON u.id = uo.user_id
                    WHERE c.ancestor_id = ?
                      AND c.depth >= 0
                      AND uo.is_deleted = 0
                      AND u.is_deleted = 0
                      AND u.device_sn IS NOT NULL
                ) dept_users
                JOIN t_health_baseline hb ON hb.user_id = dept_users.user_id
                WHERE hb.feature_name = ?
                  AND hb.baseline_date = ?
                  AND hb.mean_value IS NOT NULL
                HAVING COUNT(DISTINCT hb.user_id) >= 1
                """;
                
            int result = jdbcTemplate.update(insertSql, 
                parentDeptId, feature, date, parentDeptId, feature, date);
            
            if (result > 0) {
                log.debug("✅ 更新父部门 {} 特征 {} 基线成功", parentDeptId, feature);
            }
            
        } catch (Exception e) {
            log.error("❌ 更新父部门基线失败，部门: {}, 特征: {}, 错误: {}", 
                parentDeptId, feature, e.getMessage());
        }
    }

    /**
     * 获取部门层级健康排名 - 展示闭包表查询能力
     */
    public List<Map<String, Object>> getDepartmentHealthRanking(String feature, String date, Integer limit) {
        try {
            String rankingSql = """
                SELECT 
                    ohb.org_id,
                    ou.name as dept_name,
                    ohb.mean_value,
                    ohb.user_count,
                    ou.level as dept_level,
                    RANK() OVER (ORDER BY ohb.mean_value DESC) as ranking,
                    (SELECT COUNT(DISTINCT c.descendant_id) 
                     FROM sys_org_closure c 
                     WHERE c.ancestor_id = ohb.org_id AND c.depth > 0) as sub_dept_count
                FROM t_org_health_baseline ohb
                JOIN sys_org_units ou ON ou.id = ohb.org_id
                WHERE ohb.feature_name = ?
                  AND ohb.baseline_date = ?
                  AND ou.is_deleted = 0
                ORDER BY ohb.mean_value DESC
                LIMIT ?
                """;
                
            List<Map<String, Object>> rankings = jdbcTemplate.queryForList(rankingSql, 
                feature, date, limit != null ? limit : 20);
                
            log.info("📊 查询部门健康排名: 特征 {}, 日期 {}, 共 {} 个部门", 
                feature, date, rankings.size());
                
            return rankings;
            
        } catch (Exception e) {
            log.error("❌ 查询部门健康排名失败: {}", e.getMessage());
            return List.of(Map.of("error", e.getMessage()));
        }
    }

    /**
     * 手动触发部门聚合任务
     */
    public Map<String, Object> manualExecute(String startDate, String endDate) {
        log.info("🔧 手动触发部门健康基线聚合，时间范围: {} - {}", startDate, endDate);
        
        try {
            LocalDate start = LocalDate.parse(startDate);
            LocalDate end = LocalDate.parse(endDate);
            int processedDays = 0;
            
            while (!start.isAfter(end)) {
                String dateStr = start.toString();
                
                // 执行当日的部门聚合
                int totalAggregated = 0;
                for (String feature : HEALTH_FEATURES) {
                    totalAggregated += aggregateDepartmentBaselineForFeature(feature, dateStr);
                }
                
                if (totalAggregated > 0) {
                    processedDays++;
                    log.info("✅ 日期 {} 部门聚合完成: {} 条记录", dateStr, totalAggregated);
                }
                
                start = start.plusDays(1);
            }
            
            return Map.of(
                "success", true,
                "message", "部门健康基线聚合完成",
                "processedDays", processedDays,
                "startDate", startDate,
                "endDate", endDate
            );
            
        } catch (Exception e) {
            log.error("❌ 手动部门聚合失败: {}", e.getMessage(), e);
            return Map.of(
                "success", false,
                "message", "部门聚合失败: " + e.getMessage(),
                "error", e.getClass().getSimpleName()
            );
        }
    }
}