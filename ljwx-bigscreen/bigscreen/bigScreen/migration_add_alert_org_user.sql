-- 迁移脚本：为t_alert_info表添加org_id和user_id字段
-- 执行日期：2024年
-- 说明：增强告警系统，支持组织和用户关联

-- 1. 添加新字段
ALTER TABLE t_alert_info 
ADD COLUMN org_id BIGINT NULL COMMENT '组织ID',
ADD COLUMN user_id BIGINT NULL COMMENT '用户ID';

-- 2. 添加索引以提升查询性能
CREATE INDEX idx_alert_info_org_id ON t_alert_info(org_id);
CREATE INDEX idx_alert_info_user_id ON t_alert_info(user_id);
CREATE INDEX idx_alert_info_device_sn ON t_alert_info(device_sn);
CREATE INDEX idx_alert_info_org_device ON t_alert_info(org_id, device_sn);

-- 3. 批量更新现有数据的org_id和user_id
-- 通过device_sn关联t_device_info表获取user_id和org_id
UPDATE t_alert_info ai
JOIN t_device_info di ON ai.device_sn = di.serial_number
SET ai.user_id = di.user_id,
    ai.org_id = di.org_id
WHERE ai.org_id IS NULL OR ai.user_id IS NULL;

-- 4. 对于没有在t_device_info中找到的设备，尝试通过sys_user表的device_sn字段匹配
UPDATE t_alert_info ai
JOIN sys_user su ON ai.device_sn = su.device_sn
JOIN sys_user_org suo ON su.id = suo.user_id
SET ai.user_id = su.id,
    ai.org_id = suo.org_id
WHERE ai.org_id IS NULL OR ai.user_id IS NULL;

-- 5. 验证更新结果的查询语句
SELECT 
    COUNT(*) as total_alerts,
    COUNT(org_id) as alerts_with_org_id,
    COUNT(user_id) as alerts_with_user_id,
    COUNT(*) - COUNT(org_id) as alerts_missing_org_id,
    COUNT(*) - COUNT(user_id) as alerts_missing_user_id
FROM t_alert_info;

-- 6. 查看未匹配的设备（可选，用于排查问题）
SELECT DISTINCT ai.device_sn, COUNT(*) as alert_count
FROM t_alert_info ai
WHERE ai.org_id IS NULL OR ai.user_id IS NULL
GROUP BY ai.device_sn
ORDER BY alert_count DESC
LIMIT 20;

-- 7. 回滚脚本（如需要）
-- ALTER TABLE t_alert_info DROP COLUMN org_id;
-- ALTER TABLE t_alert_info DROP COLUMN user_id;
-- DROP INDEX idx_alert_info_org_id;
-- DROP INDEX idx_alert_info_user_id;
-- DROP INDEX idx_alert_info_device_sn;
-- DROP INDEX idx_alert_info_org_device; 