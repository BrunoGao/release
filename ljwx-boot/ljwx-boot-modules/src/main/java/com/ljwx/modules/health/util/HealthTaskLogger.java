package com.ljwx.modules.health.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 健康任务日志记录工具
 * 
 * @Author bruno.gao <gaojunivas@gmail.com>
 * @ProjectName ljwx-boot
 * @ClassName com.ljwx.modules.health.util.HealthTaskLogger
 * @CreateTime 2025-01-26
 */
@Slf4j
@Component
public class HealthTaskLogger {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 记录任务开始
     */
    public Long logTaskStart(String taskName, String taskType, String featureName, LocalDate targetDate) {
        try {
            String sql = """
                INSERT INTO t_health_task_log (
                    task_name, task_type, start_time, status, 
                    feature_name, target_date, create_time
                ) VALUES (?, ?, ?, 'running', ?, ?, ?)
                """;
            
            LocalDateTime now = LocalDateTime.now();
            
            jdbcTemplate.update(sql, 
                taskName, taskType, now, featureName, targetDate, now);
            
            // 获取插入的ID
            String idSql = "SELECT LAST_INSERT_ID()";
            Long logId = jdbcTemplate.queryForObject(idSql, Long.class);
            
            log.info("📝 任务日志记录开始: {} [ID: {}]", taskName, logId);
            return logId;
            
        } catch (Exception e) {
            log.error("❌ 记录任务开始失败: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * 记录任务成功完成
     */
    public void logTaskSuccess(Long logId, int processedCount) {
        if (logId == null) return;
        
        try {
            LocalDateTime now = LocalDateTime.now();
            
            // 计算执行时间
            String getStartTimeSql = "SELECT start_time FROM t_health_task_log WHERE id = ?";
            LocalDateTime startTime = jdbcTemplate.queryForObject(getStartTimeSql, LocalDateTime.class, logId);
            
            long executionTimeMs = 0;
            if (startTime != null) {
                executionTimeMs = java.time.Duration.between(startTime, now).toMillis();
            }
            
            String sql = """
                UPDATE t_health_task_log 
                SET end_time = ?, status = 'success', 
                    processed_count = ?, execution_time_ms = ?
                WHERE id = ?
                """;
            
            jdbcTemplate.update(sql, now, processedCount, executionTimeMs, logId);
            
            log.info("✅ 任务完成记录: [ID: {}] 处理 {} 条记录，耗时 {} ms", 
                logId, processedCount, executionTimeMs);
            
        } catch (Exception e) {
            log.error("❌ 记录任务成功失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 记录任务失败
     */
    public void logTaskFailure(Long logId, String errorMessage) {
        if (logId == null) return;
        
        try {
            LocalDateTime now = LocalDateTime.now();
            
            // 计算执行时间
            String getStartTimeSql = "SELECT start_time FROM t_health_task_log WHERE id = ?";
            LocalDateTime startTime = jdbcTemplate.queryForObject(getStartTimeSql, LocalDateTime.class, logId);
            
            long executionTimeMs = 0;
            if (startTime != null) {
                executionTimeMs = java.time.Duration.between(startTime, now).toMillis();
            }
            
            String sql = """
                UPDATE t_health_task_log 
                SET end_time = ?, status = 'failed', 
                    error_message = ?, execution_time_ms = ?
                WHERE id = ?
                """;
            
            jdbcTemplate.update(sql, now, errorMessage, executionTimeMs, logId);
            
            log.error("❌ 任务失败记录: [ID: {}] 错误: {}, 耗时 {} ms", 
                logId, errorMessage, executionTimeMs);
            
        } catch (Exception e) {
            log.error("❌ 记录任务失败失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 记录简单任务（一次性调用）
     */
    public void logSimpleTask(String taskName, String taskType, 
                             String featureName, LocalDate targetDate, 
                             boolean success, int processedCount, String errorMessage) {
        try {
            LocalDateTime now = LocalDateTime.now();
            
            String sql = """
                INSERT INTO t_health_task_log (
                    task_name, task_type, start_time, end_time, status,
                    processed_count, error_message, feature_name, target_date,
                    execution_time_ms, create_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """;
            
            String status = success ? "success" : "failed";
            
            jdbcTemplate.update(sql, 
                taskName, taskType, now, now, status,
                processedCount, errorMessage, featureName, targetDate, now);
            
            if (success) {
                log.info("✅ 简单任务记录: {} 处理 {} 条记录", taskName, processedCount);
            } else {
                log.error("❌ 简单任务失败记录: {} 错误: {}", taskName, errorMessage);
            }
            
        } catch (Exception e) {
            log.error("❌ 记录简单任务失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 清理过期日志（保留30天）
     */
    public void cleanupOldLogs() {
        try {
            String sql = """
                DELETE FROM t_health_task_log 
                WHERE create_time < DATE_SUB(NOW(), INTERVAL 30 DAY)
                """;
            
            int deletedRows = jdbcTemplate.update(sql);
            
            if (deletedRows > 0) {
                log.info("🧹 清理过期任务日志: {} 条", deletedRows);
            }
            
        } catch (Exception e) {
            log.error("❌ 清理过期日志失败: {}", e.getMessage(), e);
        }
    }
} 