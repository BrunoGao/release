-- 健康数据性能优化脚本
-- 执行日期：2024年
-- 说明：优化t_user_health_data表查询性能，解决超时问题

-- 1. 检查当前表状态
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT device_sn) as unique_devices,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record,
    AVG(DATEDIFF(NOW(), timestamp)) as avg_days_old
FROM t_user_health_data;

-- 2. 检查现有索引
SHOW INDEX FROM t_user_health_data;

-- 3. 创建性能优化索引（如果不存在）
-- 核心复合索引：设备+时间，支持最新数据查询
CREATE INDEX IF NOT EXISTS idx_device_timestamp ON t_user_health_data(device_sn, timestamp DESC);

-- 时间戳索引：支持时间范围查询
CREATE INDEX IF NOT EXISTS idx_timestamp ON t_user_health_data(timestamp);

-- 组织+时间复合索引：支持按组织查询
CREATE INDEX IF NOT EXISTS idx_org_timestamp ON t_user_health_data(org_id, timestamp DESC);

-- 用户+时间复合索引：支持按用户查询  
CREATE INDEX IF NOT EXISTS idx_user_timestamp ON t_user_health_data(user_id, timestamp DESC);

-- 覆盖索引：设备+时间+关键字段，减少回表
CREATE INDEX IF NOT EXISTS idx_device_time_key_fields ON t_user_health_data(
    device_sn, timestamp DESC, heart_rate, blood_oxygen, temperature, step
);

-- 4. 创建分区（可选，适用于数据量极大的情况）
-- 注意：分区需要谨慎评估，建议先测试索引效果
-- ALTER TABLE t_user_health_data PARTITION BY RANGE (TO_DAYS(timestamp)) (
--     PARTITION p_old VALUES LESS THAN (TO_DAYS('2024-01-01')),
--     PARTITION p_2024_q1 VALUES LESS THAN (TO_DAYS('2024-04-01')),
--     PARTITION p_2024_q2 VALUES LESS THAN (TO_DAYS('2024-07-01')),
--     PARTITION p_2024_q3 VALUES LESS THAN (TO_DAYS('2024-10-01')),
--     PARTITION p_2024_q4 VALUES LESS THAN (TO_DAYS('2025-01-01')),
--     PARTITION p_future VALUES LESS THAN MAXVALUE
-- );

-- 5. 查询性能测试
-- 测试窗口函数查询性能（新的优化查询）
EXPLAIN SELECT * FROM (
    SELECT *, 
           ROW_NUMBER() OVER (PARTITION BY device_sn ORDER BY timestamp DESC) as rn
    FROM t_user_health_data 
    WHERE device_sn IN ('DEVICE_001', 'DEVICE_002', 'DEVICE_003')
      AND timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
) ranked 
WHERE rn = 1
ORDER BY timestamp DESC
LIMIT 200;

-- 6. 清理旧数据（可选，建议谨慎执行）
-- 保留最近30天的数据，删除更老的记录来提升性能
-- DELETE FROM t_user_health_data 
-- WHERE timestamp < DATE_SUB(NOW(), INTERVAL 30 DAY)
-- LIMIT 10000;  -- 分批删除，避免锁表

-- 7. 优化查询建议
-- 使用以下查询模式可以获得最佳性能：

-- 模式1：获取指定设备最新数据（推荐）
-- SELECT * FROM t_user_health_data 
-- WHERE device_sn = 'DEVICE_001' 
-- ORDER BY timestamp DESC 
-- LIMIT 1;

-- 模式2：获取多设备最新数据（已优化）
-- SELECT * FROM (
--     SELECT *, ROW_NUMBER() OVER (PARTITION BY device_sn ORDER BY timestamp DESC) as rn
--     FROM t_user_health_data 
--     WHERE device_sn IN ('DEV1', 'DEV2') AND timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY)
-- ) ranked WHERE rn = 1;

-- 模式3：按组织查询（需要org_id字段已填充）
-- SELECT * FROM t_user_health_data 
-- WHERE org_id = 1 AND timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY)
-- ORDER BY timestamp DESC;

-- 8. 验证索引效果
SELECT 
    table_name,
    index_name,
    column_name,
    cardinality,
    sub_part,
    packed,
    nullable,
    index_type
FROM information_schema.statistics 
WHERE table_schema = DATABASE() 
  AND table_name = 't_user_health_data'
ORDER BY index_name, seq_in_index;

-- 9. 性能监控查询
-- 监控慢查询和表扫描
SELECT 
    'Health Data Performance Check' as check_type,
    COUNT(*) as total_records,
    COUNT(CASE WHEN timestamp > DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as recent_1day,
    COUNT(CASE WHEN timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as recent_7days,
    COUNT(CASE WHEN timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as recent_30days,
    ROUND(AVG(CASE WHEN timestamp > DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) * 100, 2) as recent_percentage
FROM t_user_health_data; 