-- 迁移脚本：更新t_user_health_data表的org_id和user_id字段
-- 执行日期：2024年
-- 说明：根据device_sn绑定的用户信息更新健康数据表的组织和用户关联

-- 1. 检查当前数据状况
SELECT 
    COUNT(*) as total_records,
    COUNT(user_id) as records_with_user_id,
    COUNT(org_id) as records_with_org_id,
    COUNT(*) - COUNT(user_id) as missing_user_id,
    COUNT(*) - COUNT(org_id) as missing_org_id,
    COUNT(DISTINCT device_sn) as unique_devices
FROM t_user_health_data;

-- 2. 第一步：通过t_device_info表更新user_id和org_id
-- 这是最主要的更新路径，因为设备表通常包含最准确的绑定信息
UPDATE t_user_health_data uhd
JOIN t_device_info di ON uhd.device_sn = di.serial_number
SET uhd.user_id = di.user_id,
    uhd.org_id = di.org_id
WHERE (uhd.user_id IS NULL OR uhd.org_id IS NULL)
  AND di.user_id IS NOT NULL 
  AND di.org_id IS NOT NULL;

-- 3. 第二步：对于仍然缺失的数据，通过sys_user表的device_sn字段匹配
-- 处理user_id为空的记录
UPDATE t_user_health_data uhd
JOIN sys_user su ON uhd.device_sn = su.device_sn
SET uhd.user_id = su.id
WHERE uhd.user_id IS NULL 
  AND su.device_sn IS NOT NULL 
  AND su.device_sn != ''
  AND su.is_deleted = 0;

-- 4. 第三步：通过sys_user_org表更新org_id
-- 对于有user_id但缺少org_id的记录
UPDATE t_user_health_data uhd
JOIN sys_user_org suo ON uhd.user_id = suo.user_id
SET uhd.org_id = suo.org_id
WHERE uhd.org_id IS NULL 
  AND uhd.user_id IS NOT NULL
  AND suo.is_deleted = 0;

-- 5. 第四步：对于仍然缺失org_id的记录，尝试通过device_sn -> sys_user -> sys_user_org路径
UPDATE t_user_health_data uhd
JOIN sys_user su ON uhd.device_sn = su.device_sn
JOIN sys_user_org suo ON su.id = suo.user_id
SET uhd.org_id = suo.org_id,
    uhd.user_id = COALESCE(uhd.user_id, su.id)  -- 如果user_id还是空的话也一并更新
WHERE (uhd.org_id IS NULL OR uhd.user_id IS NULL)
  AND su.device_sn IS NOT NULL 
  AND su.device_sn != ''
  AND su.is_deleted = 0
  AND suo.is_deleted = 0;

-- 6. 创建索引以优化后续查询性能（如果还没有的话）
CREATE INDEX IF NOT EXISTS idx_user_health_data_org_id ON t_user_health_data(org_id);
CREATE INDEX IF NOT EXISTS idx_user_health_data_user_id ON t_user_health_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_health_data_device_sn ON t_user_health_data(device_sn);
CREATE INDEX IF NOT EXISTS idx_user_health_data_org_device ON t_user_health_data(org_id, device_sn);
CREATE INDEX IF NOT EXISTS idx_user_health_data_timestamp ON t_user_health_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_health_data_org_timestamp ON t_user_health_data(org_id, timestamp);

-- 7. 验证更新结果
SELECT 
    '更新后统计' as status,
    COUNT(*) as total_records,
    COUNT(user_id) as records_with_user_id,
    COUNT(org_id) as records_with_org_id,
    COUNT(*) - COUNT(user_id) as missing_user_id,
    COUNT(*) - COUNT(org_id) as missing_org_id,
    COUNT(DISTINCT device_sn) as unique_devices,
    ROUND(COUNT(user_id) * 100.0 / COUNT(*), 2) as user_id_completion_rate,
    ROUND(COUNT(org_id) * 100.0 / COUNT(*), 2) as org_id_completion_rate
FROM t_user_health_data;

-- 8. 查看仍然未匹配的设备（用于排查问题）
SELECT 
    uhd.device_sn,
    COUNT(*) as health_records_count,
    MIN(uhd.timestamp) as first_record,
    MAX(uhd.timestamp) as latest_record,
    CASE 
        WHEN di.serial_number IS NOT NULL THEN '设备表中存在'
        WHEN su.device_sn IS NOT NULL THEN '用户表中存在' 
        ELSE '未找到绑定'
    END as binding_status
FROM t_user_health_data uhd
LEFT JOIN t_device_info di ON uhd.device_sn = di.serial_number
LEFT JOIN sys_user su ON uhd.device_sn = su.device_sn AND su.is_deleted = 0
WHERE uhd.org_id IS NULL OR uhd.user_id IS NULL
GROUP BY uhd.device_sn, binding_status
ORDER BY health_records_count DESC
LIMIT 20;

-- 9. 统计按组织分组的健康数据记录数量（验证org_id字段可用性）
SELECT 
    o.id as org_id,
    o.name as org_name,
    COUNT(uhd.id) as health_records_count,
    COUNT(DISTINCT uhd.device_sn) as unique_devices,
    MIN(uhd.timestamp) as earliest_record,
    MAX(uhd.timestamp) as latest_record
FROM sys_org_units o
LEFT JOIN t_user_health_data uhd ON o.id = uhd.org_id
WHERE o.is_deleted = 0
GROUP BY o.id, o.name
HAVING health_records_count > 0
ORDER BY health_records_count DESC
LIMIT 10; 