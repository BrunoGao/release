-- 数据库索引优化脚本（安全版本）
-- 先检查索引是否存在，避免重复创建错误

USE test;

-- =================================
-- 1. 安全创建索引的存储过程
-- =================================

DELIMITER $$

-- 创建安全添加索引的存储过程
CREATE PROCEDURE AddIndexIfNotExists(
    IN table_name VARCHAR(64),
    IN index_name VARCHAR(64), 
    IN column_definition TEXT
)
BEGIN
    DECLARE index_exists INT DEFAULT 0;
    
    -- 检查索引是否存在
    SELECT COUNT(1) INTO index_exists
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = table_name 
      AND INDEX_NAME = index_name;
      
    -- 如果索引不存在则创建
    IF index_exists = 0 THEN
        SET @sql = CONCAT('CREATE INDEX ', index_name, ' ON ', table_name, '(', column_definition, ')');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
        SELECT CONCAT('创建索引: ', index_name) as result;
    ELSE
        SELECT CONCAT('索引已存在: ', index_name) as result;
    END IF;
END$$

DELIMITER ;

-- =================================
-- 2. 执行索引优化
-- =================================

-- 2.1 健康数据表索引优化
CALL AddIndexIfNotExists('t_user_health_data', 'idx_device_time_optimized', 'device_sn, timestamp DESC');
CALL AddIndexIfNotExists('t_user_health_data', 'idx_create_time', 'create_time DESC');
CALL AddIndexIfNotExists('t_user_health_data', 'idx_batch_insert_optimized', 'customer_id, create_time DESC, device_sn');

-- 2.2 用户表索引优化
CALL AddIndexIfNotExists('sys_user', 'idx_status_customer', 'status, customer_id, is_deleted');

-- =================================
-- 3. 数据库参数优化（安全设置）
-- =================================

-- 检查当前设置
SELECT @@innodb_flush_log_at_trx_commit as current_flush_log_at_trx_commit;
SELECT @@sync_binlog as current_sync_binlog;
SELECT @@max_connections as current_max_connections;
SELECT @@thread_cache_size as current_thread_cache_size;

-- 临时优化插入性能（测试期间）
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
SET GLOBAL sync_binlog = 0;
SET GLOBAL max_connections = 1000;
SET GLOBAL thread_cache_size = 50;

-- =================================
-- 4. 检查优化结果
-- =================================

-- 4.1 显示所有新创建的索引
SELECT 
    TABLE_NAME as '表名',
    INDEX_NAME as '索引名', 
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as '索引字段',
    CARDINALITY as '基数',
    INDEX_TYPE as '索引类型'
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'test' 
  AND TABLE_NAME IN ('t_user_health_data', 'sys_user')
  AND INDEX_NAME IN (
    'idx_device_time_optimized', 
    'idx_create_time', 
    'idx_batch_insert_optimized',
    'idx_status_customer'
  )
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;

-- 4.2 显示表空间使用情况
SELECT 
    table_name as '表名',
    table_rows as '行数',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "大小(MB)",
    ROUND((index_length / 1024 / 1024), 2) AS "索引大小(MB)",
    ROUND((data_length / 1024 / 1024), 2) AS "数据大小(MB)"
FROM information_schema.tables 
WHERE table_schema='test' 
  AND table_name IN ('t_user_health_data', 'sys_user')
ORDER BY (data_length + index_length) DESC;

-- =================================
-- 5. 清理存储过程
-- =================================
DROP PROCEDURE IF EXISTS AddIndexIfNotExists;

-- =================================
-- 完成提示
-- =================================
SELECT '数据库索引优化完成！新索引已安全创建。' as 'OPTIMIZATION_COMPLETE',
       '请重新运行压力测试验证优化效果。' as 'NEXT_STEP';