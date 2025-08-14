package com.ljwx.modules.health.controller;

import com.ljwx.modules.health.task.HealthBaselineScoreTasks;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 健康任务控制器
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.controller.HealthTaskController
 * @CreateTime 2025-01-26
 */
@Slf4j
@Tag(name = "健康任务管理", description = "健康数据基线和评分任务管理接口")
@RestController
@RequestMapping("/api/health/task")
public class HealthTaskController {

    @Autowired
    private HealthBaselineScoreTasks healthBaselineScoreTasks;
    
    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 手动触发按月分表
     */
    @Operation(summary = "手动触发按月分表", description = "立即执行健康数据按月分表归档")
    @PostMapping("/archive")
    public Map<String, Object> manualArchive() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("🔧 手动触发按月分表任务");
            healthBaselineScoreTasks.archiveAndResetUserHealthTable();
            
            result.put("success", true);
            result.put("message", "按月分表任务执行成功");
            result.put("timestamp", System.currentTimeMillis());
            
        } catch (Exception e) {
            log.error("❌ 手动分表任务失败: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("message", "分表任务失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return result;
    }

    /**
     * 手动触发基线生成
     */
    @Operation(summary = "手动触发基线生成", description = "手动生成指定时间范围的健康基线数据")
    @PostMapping("/baseline/manual")
    public Map<String, Object> manualGenerateBaseline(
            @RequestParam String startDate,
            @RequestParam String endDate) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            healthBaselineScoreTasks.manualGenerateBaseline(startDate, endDate);
            result.put("success", true);
            result.put("message", "基线生成任务已完成");
            result.put("startDate", startDate);
            result.put("endDate", endDate);
            
        } catch (Exception e) {
            log.error("手动基线生成失败", e);
            result.put("success", false);
            result.put("error", e.getMessage());
        }
        
        return result;
    }

    /**
     * 手动触发今日基线和评分
     */
    @Operation(summary = "手动触发今日基线和评分", description = "立即执行昨日数据的基线生成和评分计算")
    @PostMapping("/daily")
    public Map<String, Object> manualDailyTasks() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("🔧 手动触发今日基线和评分任务");
            
            // 依次执行任务
            healthBaselineScoreTasks.generateUserHealthBaseline();
            Thread.sleep(2000); // 等待2秒
            
            healthBaselineScoreTasks.generateOrgHealthBaseline();
            Thread.sleep(2000);
            
            healthBaselineScoreTasks.generateHealthScore();
            Thread.sleep(2000);
            
            healthBaselineScoreTasks.generateOrgHealthScore();
            
            result.put("success", true);
            result.put("message", "今日基线和评分任务执行成功");
            result.put("tasks", new String[]{"用户基线", "组织基线", "用户评分", "组织评分"});
            result.put("timestamp", System.currentTimeMillis());
            
        } catch (Exception e) {
            log.error("❌ 手动今日任务失败: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("message", "今日任务失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return result;
    }

    /**
     * 手动触发数据清理
     */
    @Operation(summary = "手动触发数据清理", description = "清理过期的基线和评分数据")
    @PostMapping("/cleanup")
    public Map<String, Object> manualCleanup() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            log.info("🔧 手动触发数据清理任务");
            healthBaselineScoreTasks.cleanupOldData();
            
            result.put("success", true);
            result.put("message", "数据清理任务执行成功");
            result.put("timestamp", System.currentTimeMillis());
            
        } catch (Exception e) {
            log.error("❌ 手动数据清理失败: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("message", "数据清理失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return result;
    }

    /**
     * 查询任务执行状态
     */
    @Operation(summary = "查询任务执行状态", description = "获取最近的任务执行日志")
    @GetMapping("/status")
    public Map<String, Object> getTaskStatus(
            @Parameter(description = "查询条数", example = "10") 
            @RequestParam(defaultValue = "10") int limit) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 查询最近的任务日志
            String sql = """
                SELECT task_name, task_type, start_time, end_time, status, 
                       processed_count, feature_name, target_date, execution_time_ms
                FROM t_health_task_log 
                ORDER BY start_time DESC 
                LIMIT ?
                """;
            
            List<Map<String, Object>> logs = jdbcTemplate.queryForList(sql, limit);
            
            // 查询基线和评分数据统计
            Map<String, Object> statistics = getHealthStatistics();
            
            result.put("success", true);
            result.put("recentLogs", logs);
            result.put("statistics", statistics);
            result.put("timestamp", System.currentTimeMillis());
            
        } catch (Exception e) {
            log.error("❌ 查询任务状态失败: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("message", "查询状态失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return result;
    }

    /**
     * 查询健康数据统计信息
     */
    @Operation(summary = "查询健康数据统计", description = "获取基线和评分数据的统计信息")
    @GetMapping("/statistics")
    public Map<String, Object> getHealthStatistics() {
        Map<String, Object> statistics = new HashMap<>();
        
        try {
            // 基线数据统计
            String baselineSql = """
                SELECT feature_name, COUNT(*) as count, 
                       MAX(baseline_date) as latest_date,
                       COUNT(DISTINCT device_sn) as device_count
                FROM t_health_baseline 
                WHERE baseline_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY feature_name
                """;
            List<Map<String, Object>> baselineStats = jdbcTemplate.queryForList(baselineSql);
            
            // 评分数据统计
            String scoreSql = """
                SELECT feature_name, COUNT(*) as count,
                       MAX(score_date) as latest_date,
                       AVG(score_value) as avg_score,
                       COUNT(DISTINCT device_sn) as device_count
                FROM t_health_score 
                WHERE score_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY feature_name
                """;
            List<Map<String, Object>> scoreStats = jdbcTemplate.queryForList(scoreSql);
            
            // 归档表统计
            String archiveSql = """
                SELECT COUNT(*) as archive_table_count
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name LIKE 't_user_health_data_%'
                AND table_name != 't_user_health_data'
                """;
            Integer archiveCount = jdbcTemplate.queryForObject(archiveSql, Integer.class);
            
            statistics.put("baselineStats", baselineStats);
            statistics.put("scoreStats", scoreStats);
            statistics.put("archiveTableCount", archiveCount != null ? archiveCount : 0);
            
        } catch (Exception e) {
            log.error("❌ 查询统计信息失败: {}", e.getMessage(), e);
            statistics.put("error", e.getMessage());
        }
        
        return statistics;
    }

    /**
     * 查询分表信息
     */
    @Operation(summary = "查询分表信息", description = "获取健康数据分表的详细信息")
    @GetMapping("/tables")
    public Map<String, Object> getTableInfo() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 查询所有健康数据表
            String tableSql = """
                SELECT table_name, table_comment, create_time, table_rows,
                       ROUND((data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND (table_name = 't_user_health_data' OR table_name LIKE 't_user_health_data_%')
                ORDER BY table_name
                """;
            
            List<Map<String, Object>> tables = jdbcTemplate.queryForList(tableSql);
            
            // 计算总记录数和大小
            long totalRows = 0;
            double totalSizeMb = 0;
            
            for (Map<String, Object> table : tables) {
                Object rows = table.get("table_rows");
                Object size = table.get("size_mb");
                
                if (rows != null) {
                    totalRows += ((Number) rows).longValue();
                }
                if (size != null) {
                    totalSizeMb += ((Number) size).doubleValue();
                }
            }
            
            result.put("success", true);
            result.put("tables", tables);
            result.put("summary", Map.of(
                "totalTables", tables.size(),
                "totalRows", totalRows,
                "totalSizeMb", Math.round(totalSizeMb * 100.0) / 100.0
            ));
            result.put("timestamp", System.currentTimeMillis());
            
        } catch (Exception e) {
            log.error("❌ 查询分表信息失败: {}", e.getMessage(), e);
            result.put("success", false);
            result.put("message", "查询分表信息失败: " + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return result;
    }

    @Operation(summary = "手动触发评分生成", description = "手动生成指定时间范围的健康评分数据")
    @PostMapping("/score/manual")
    public Map<String, Object> manualGenerateScore(
            @RequestParam String startDate,
            @RequestParam String endDate) {
        Map<String, Object> result = new HashMap<>();
        
        try {
            healthBaselineScoreTasks.manualGenerateScore(startDate, endDate);
            result.put("success", true);
            result.put("message", "评分生成任务已完成");
            result.put("startDate", startDate);
            result.put("endDate", endDate);
            
        } catch (Exception e) {
            log.error("手动评分生成失败", e);
            result.put("success", false);
            result.put("error", e.getMessage());
        }
        
        return result;
    }
    
    @Operation(summary = "补充生成最近2个月数据", description = "一键补充生成最近2个月的健康基线和评分数据")
    @PostMapping("/generate-recent")
    public Map<String, Object> generateRecentData() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            healthBaselineScoreTasks.generateRecentBaselinesAndScores();
            result.put("success", true);
            result.put("message", "最近2个月健康基线和评分数据补充生成完成");
            result.put("generatedPeriod", "最近2个月");
            
        } catch (Exception e) {
            log.error("补充生成最近2个月数据失败", e);
            result.put("success", false);
            result.put("error", e.getMessage());
        }
        
        return result;
    }
} 