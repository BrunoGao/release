-- 数据库重复插入问题解决方案 - 迁移脚本
-- 执行前请备份数据库

-- 1. 检查并删除重复记录（可选，谨慎执行）
-- DELETE t1 FROM t_user_health_data t1
-- INNER JOIN t_user_health_data t2 
-- WHERE t1.id > t2.id 
-- AND t1.device_sn = t2.device_sn 
-- AND t1.timestamp = t2.timestamp;

-- 2. 添加唯一约束（防止重复插入）
ALTER TABLE t_user_health_data 
ADD CONSTRAINT uk_device_timestamp 
UNIQUE (device_sn, timestamp);

-- 3. 添加性能优化索引
CREATE INDEX idx_device_timestamp ON t_user_health_data (device_sn, timestamp);
CREATE INDEX idx_timestamp ON t_user_health_data (timestamp);
CREATE INDEX idx_device_sn ON t_user_health_data (device_sn);

-- 4. 验证约束和索引
SHOW INDEX FROM t_user_health_data;
SHOW CREATE TABLE t_user_health_data;

-- 5. 测试重复插入（应该失败）
-- INSERT INTO t_user_health_data (device_sn, timestamp, heart_rate) 
-- VALUES ('TEST001', '2024-01-01 12:00:00', 80);
-- INSERT INTO t_user_health_data (device_sn, timestamp, heart_rate) 
-- VALUES ('TEST001', '2024-01-01 12:00:00', 85); -- 这条应该失败

COMMIT; 