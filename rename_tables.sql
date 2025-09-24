-- 重命名健康数据慢字段表
-- 避免与真正的daily/weekly统计表混淆

-- 重命名日报慢字段表（存储睡眠、运动等JSON数据）
RENAME TABLE t_user_health_data_daily TO t_health_data_slow_daily;

-- 重命名周报慢字段表（存储周运动JSON数据）  
RENAME TABLE t_user_health_data_weekly TO t_health_data_slow_weekly;

-- 验证重命名结果
SELECT 'Tables renamed successfully' as status;
SHOW TABLES LIKE '%health_data_slow%';