-- 数据库索引优化脚本
-- 针对健康数据上传压力测试的性能优化

USE test;

-- =================================
-- 1. 健康数据表 (t_user_health_data) 索引优化
-- =================================

-- 分析现有索引使用情况
-- 当前表已有较多索引，但需要针对压力测试场景进行优化

-- 1.1 添加用户名查询索引（用于快速定位用户）
-- 压力测试中经常需要根据用户名查询数据
CREATE INDEX idx_user_name ON t_user_health_data(user_name);

-- 1.2 优化设备SN+时间戳的联合索引（设备数据按时间排序）
-- 现有的 idx_device_sn 只包含设备SN，需要加上时间戳提高查询效率
CREATE INDEX idx_device_time_optimized ON t_user_health_data(device_sn, timestamp DESC);

-- 1.3 添加用户ID+时间戳索引（用户健康数据时间序列查询）
CREATE INDEX idx_user_id_time ON t_user_health_data(user_id, timestamp DESC);

-- 1.4 添加创建时间索引（用于数据插入性能监控）
CREATE INDEX idx_create_time ON t_user_health_data(create_time DESC);

-- 1.5 优化批量插入的组合索引（customer_id + create_time）
-- 便于批量操作的快速定位
CREATE INDEX idx_batch_insert_optimized ON t_user_health_data(customer_id, create_time DESC, device_sn);

-- =================================
-- 2. 用户表 (sys_user) 索引优化  
-- =================================

-- 2.1 添加用户名唯一索引（快速用户查找）
-- 压力测试中需要根据用户名快速查找用户信息
CREATE UNIQUE INDEX idx_user_name_unique ON sys_user(user_name);

-- 2.2 优化设备SN索引（一个设备对应一个用户）
-- 现有索引已存在，检查是否需要优化
-- ALTER INDEX idx_sys_user_device_sn RENAME TO idx_device_sn_lookup;

-- 2.3 添加状态+客户ID的联合索引（活跃用户查询）
CREATE INDEX idx_status_customer ON sys_user(status, customer_id, is_deleted);

-- =================================
-- 3. 数据库参数优化
-- =================================

-- 3.1 优化InnoDB缓冲池大小（如果可以修改配置）
-- innodb_buffer_pool_size = 系统内存的70-80%
-- 这需要在MySQL配置文件中设置，这里提供建议值

-- 3.2 优化插入性能相关参数
SET GLOBAL innodb_flush_log_at_trx_commit = 2;  -- 提高插入性能，降低数据安全性
SET GLOBAL sync_binlog = 0;  -- 提高写入性能

-- 3.3 优化查询缓存（MySQL 8.0已移除查询缓存）
-- SET GLOBAL query_cache_size = 268435456;  -- 256MB
-- SET GLOBAL query_cache_type = ON;

-- 3.4 优化连接数
SET GLOBAL max_connections = 1000;  -- 支持更多并发连接
SET GLOBAL thread_cache_size = 50;   -- 线程缓存

-- =================================
-- 4. 表结构优化建议
-- =================================

-- 4.1 分析表空间使用情况
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "DB Size in MB" 
FROM information_schema.tables 
WHERE table_schema="test" AND table_name IN ('t_user_health_data', 'sys_user');

-- 4.2 分析索引使用效率
SELECT 
    TABLE_SCHEMA as `DB`, 
    TABLE_NAME as `Table`,
    INDEX_NAME as `Index`, 
    CARDINALITY,
    ROUND((CARDINALITY/
        (SELECT table_rows FROM information_schema.tables 
         WHERE table_schema = 'test' AND table_name = 't_user_health_data')
    )*100, 2) as `Selectivity %`
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'test' 
  AND TABLE_NAME = 't_user_health_data'
  AND INDEX_NAME != 'PRIMARY'
ORDER BY CARDINALITY DESC;

-- =================================
-- 5. 维护和监控查询
-- =================================

-- 5.1 检查索引使用情况
SHOW INDEX FROM t_user_health_data;
SHOW INDEX FROM sys_user;

-- 5.2 分析慢查询（需要启用慢查询日志）
-- SHOW VARIABLES LIKE 'slow_query_log';
-- SET GLOBAL slow_query_log = 'ON';
-- SET GLOBAL long_query_time = 1;

-- 5.3 检查表状态
SHOW TABLE STATUS LIKE 't_user_health_data';
SHOW TABLE STATUS LIKE 'sys_user';

-- =================================
-- 执行完成提示
-- =================================
SELECT '数据库索引优化完成！请重新运行压力测试验证效果。' as 'OPTIMIZATION_COMPLETE';

-- =================================
-- 回滚脚本（如需要）
-- =================================
/*
-- 如果需要回滚新添加的索引：
DROP INDEX IF EXISTS idx_user_name ON t_user_health_data;
DROP INDEX IF EXISTS idx_device_time_optimized ON t_user_health_data;
DROP INDEX IF EXISTS idx_user_id_time ON t_user_health_data;
DROP INDEX IF EXISTS idx_create_time ON t_user_health_data;
DROP INDEX IF EXISTS idx_batch_insert_optimized ON t_user_health_data;
DROP INDEX IF EXISTS idx_user_name_unique ON sys_user;
DROP INDEX IF EXISTS idx_status_customer ON sys_user;
*/