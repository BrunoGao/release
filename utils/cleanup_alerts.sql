-- 清理 t_alert_info 表，只保留每个 alert_type 类型的两条最新记录
-- 使用 test 数据库
USE test;

-- 显示清理前的统计
SELECT '=== 清理前的数据统计 ===' as info;
SELECT alert_type, COUNT(*) as count FROM t_alert_info GROUP BY alert_type ORDER BY alert_type;
SELECT 'Total records before cleanup:' as info, COUNT(*) as total FROM t_alert_info;

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

-- 执行删除操作（删除不在保留列表中的记录）
DELETE FROM t_alert_info 
WHERE id NOT IN (SELECT id FROM temp_keep_alerts);

-- 显示清理后的统计
SELECT '=== 清理后的数据统计 ===' as info;
SELECT alert_type, COUNT(*) as count FROM t_alert_info GROUP BY alert_type ORDER BY alert_type;
SELECT 'Total records after cleanup:' as info, COUNT(*) as total FROM t_alert_info;

-- 显示最终保留的记录
SELECT '=== 最终保留的记录 ===' as info;
SELECT id, alert_type, user_id, device_sn, occur_at FROM t_alert_info ORDER BY alert_type, occur_at DESC;

-- 清理临时表
DROP TEMPORARY TABLE temp_keep_alerts;