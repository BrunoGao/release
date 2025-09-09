-- 安全清理 t_alert_info 表，只保留每个 alert_type 类型的两条最新记录
-- 处理外键约束问题
USE test;

-- 显示清理前的统计
SELECT '=== 清理前的数据统计 ===' as info;
SELECT alert_type, COUNT(*) as count FROM t_alert_info GROUP BY alert_type ORDER BY alert_type;
SELECT 'Total records before cleanup:' as info, COUNT(*) as total FROM t_alert_info;

-- 检查是否存在相关外键表
SELECT '=== 检查相关外键约束 ===' as info;
SHOW CREATE TABLE t_alert_info;

-- 创建临时表来标识要保留的记录
CREATE TEMPORARY TABLE temp_keep_alerts AS
SELECT id FROM (
    SELECT id, 
           ROW_NUMBER() OVER (PARTITION BY alert_type ORDER BY occur_at DESC) as rn
    FROM t_alert_info
    WHERE is_deleted = 0
) ranked
WHERE rn <= 2;

-- 显示要保留的记录
SELECT '=== 要保留的记录 ===' as info;
SELECT a.id, a.alert_type, a.user_id, a.device_sn, a.occur_at
FROM t_alert_info a
INNER JOIN temp_keep_alerts t ON a.id = t.id
ORDER BY a.alert_type, a.occur_at DESC;

-- 创建要删除的记录临时表
CREATE TEMPORARY TABLE temp_delete_alerts AS
SELECT id FROM t_alert_info 
WHERE id NOT IN (SELECT id FROM temp_keep_alerts);

-- 显示要删除的记录数量
SELECT '=== 要删除的记录统计 ===' as info;
SELECT COUNT(*) as records_to_delete FROM temp_delete_alerts;

-- 先删除外键表中的相关记录
SELECT '=== 删除外键表中的相关记录 ===' as info;
DELETE FROM t_alert_action_log 
WHERE alert_id IN (SELECT id FROM temp_delete_alerts);

-- 显示删除的外键记录数
SELECT '=== 已删除的外键记录数量 ===' as info, ROW_COUNT() as deleted_foreign_records;

-- 现在安全删除主表记录
DELETE FROM t_alert_info 
WHERE id IN (SELECT id FROM temp_delete_alerts);

-- 显示删除的主表记录数
SELECT '=== 已删除的主表记录数量 ===' as info, ROW_COUNT() as deleted_main_records;

-- 显示清理后的统计
SELECT '=== 清理后的数据统计 ===' as info;
SELECT alert_type, COUNT(*) as count FROM t_alert_info GROUP BY alert_type ORDER BY alert_type;
SELECT 'Total records after cleanup:' as info, COUNT(*) as total FROM t_alert_info;

-- 显示最终保留的记录
SELECT '=== 最终保留的记录 ===' as info;
SELECT id, alert_type, user_id, device_sn, occur_at FROM t_alert_info ORDER BY alert_type, occur_at DESC;

-- 清理临时表
DROP TEMPORARY TABLE temp_keep_alerts;
DROP TEMPORARY TABLE temp_delete_alerts;