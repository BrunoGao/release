-- 慢SQL优化 - 数据库索引优化脚本
-- 执行前请备份数据库

-- ===== 健康数据表优化 =====
-- 1. 优化时间范围查询: WHERE created_at > "2025-01-01" ORDER BY id DESC
CREATE INDEX idx_health_create_time_id ON t_user_health_data (create_time DESC, id DESC);
CREATE INDEX idx_health_timestamp ON t_user_health_data (timestamp DESC);

-- 2. 优化心率查询: WHERE heart_rate > 100 ORDER BY created_at DESC  
CREATE INDEX idx_health_heart_rate_time ON t_user_health_data (heart_rate, create_time DESC);

-- 3. 优化设备查询
CREATE INDEX idx_health_device_time ON t_user_health_data (device_sn, timestamp DESC);
CREATE INDEX idx_health_device_create ON t_user_health_data (device_sn, create_time DESC);

-- 4. 优化删除标记查询
CREATE INDEX idx_health_deleted_time ON t_user_health_data (is_deleted, create_time DESC);

-- ===== 用户表优化 =====
-- 5. 优化用户设备关联查询
CREATE INDEX idx_user_device_sn ON sys_user (device_sn);
CREATE INDEX idx_user_deleted_create ON sys_user (is_deleted, create_time);

-- ===== 告警表优化 =====  
-- 6. 优化告警批量更新: WHERE severity = "high" AND created_at < NOW() - INTERVAL 1 DAY
CREATE INDEX idx_alert_severity_time_status ON t_alert_info (severity_level, create_time, alert_status);
CREATE INDEX idx_alert_status_time ON t_alert_info (alert_status, create_time);

-- ===== 设备表优化 =====
-- 7. 优化设备统计查询: WHERE status = "active" AND created_at > "2024-01-01"
CREATE INDEX idx_device_status_time ON t_device_info (status, create_time);
CREATE INDEX idx_device_deleted_time ON t_device_info (is_deleted, create_time);
CREATE INDEX idx_device_charging_status ON t_device_info (charging_status);
CREATE INDEX idx_device_wearable_status ON t_device_info (wearable_status);

-- ===== 复合索引优化 =====
-- 8. 健康数据多维度查询
CREATE INDEX idx_health_multi ON t_user_health_data (device_sn, heart_rate, create_time DESC);
CREATE INDEX idx_health_vital_signs ON t_user_health_data (heart_rate, blood_oxygen, temperature, timestamp);

-- 9. 告警多维度查询
CREATE INDEX idx_alert_multi ON t_alert_info (device_sn, severity_level, alert_status, create_time);

-- ===== 分区表优化(可选) =====
-- 10. 健康数据按月分区(大数据量时使用)
-- ALTER TABLE t_user_health_data PARTITION BY RANGE (YEAR(create_time)*100 + MONTH(create_time)) (
--     PARTITION p202501 VALUES LESS THAN (202502),
--     PARTITION p202502 VALUES LESS THAN (202503),
--     PARTITION p202503 VALUES LESS THAN (202504),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
-- );

-- ===== 查询优化建议 =====
-- 11. 分析表统计信息
ANALYZE TABLE t_user_health_data;
ANALYZE TABLE sys_user;
ANALYZE TABLE t_alert_info;
ANALYZE TABLE t_device_info;

-- 12. 检查索引使用情况
-- EXPLAIN SELECT * FROM t_user_health_data WHERE create_time > '2025-01-01' ORDER BY id DESC LIMIT 1000;
-- EXPLAIN SELECT h.*, u.real_name FROM t_user_health_data h LEFT JOIN sys_user u ON h.device_sn = u.device_sn WHERE h.heart_rate > 100 ORDER BY h.create_time DESC;

-- ===== 清理无用索引 =====
-- 13. 删除重复或无用索引(根据实际情况调整)
-- DROP INDEX idx_old_index_name ON t_user_health_data;

-- ===== 性能监控 =====
-- 14. 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1; -- 记录超过1秒的查询
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- 15. 查看索引大小
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    ROUND(STAT_VALUE * @@innodb_page_size / 1024 / 1024, 2) AS 'Size(MB)'
FROM information_schema.INNODB_SYS_TABLESTATS 
WHERE TABLE_NAME LIKE '%user_health_data%';

COMMIT; 