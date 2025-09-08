-- 优化健康基线和评分表结构，支持基于userId的层级聚合
-- 创建时间: 2025-09-08
-- 作者: bruno.gao

-- 1. 优化 t_health_baseline 表结构和索引
-- 确保 user_id 字段为非空且有适当的索引支持

ALTER TABLE `t_health_baseline` 
MODIFY COLUMN `user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '用户ID - 优化为主要查询字段';

-- 添加基于 user_id 的复合索引，优化层级聚合查询性能
CREATE INDEX IF NOT EXISTS `idx_baseline_user_feature_date` ON `t_health_baseline` (`user_id`, `feature_name`, `baseline_date`);
CREATE INDEX IF NOT EXISTS `idx_baseline_user_org_feature` ON `t_health_baseline` (`user_id`, `org_id`, `feature_name`);

-- 2. 优化 t_health_score 表结构和索引
ALTER TABLE `t_health_score` 
MODIFY COLUMN `user_id` BIGINT NOT NULL DEFAULT 0 COMMENT '用户ID - 优化为主要查询字段';

-- 添加基于 user_id 的复合索引
CREATE INDEX IF NOT EXISTS `idx_score_user_feature_date` ON `t_health_score` (`user_id`, `feature_name`, `score_date`);
CREATE INDEX IF NOT EXISTS `idx_score_user_org_feature` ON `t_health_score` (`user_id`, `org_id`, `feature_name`);

-- 3. 为组织健康基线表添加租户级别支持的注释
ALTER TABLE `t_org_health_baseline` 
COMMENT = '组织健康基线表 - 支持部门和租户级别的层级聚合，org_id可以是部门ID或customer_id';

ALTER TABLE `t_org_health_score` 
COMMENT = '组织健康评分表 - 支持部门和租户级别的层级聚合，org_id可以是部门ID或customer_id';

-- 4. 添加数据清理存储过程 - 清理无效的基线和评分数据
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS `CleanupInvalidHealthData`()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE cleanup_date DATE;
    DECLARE cleanup_cursor CURSOR FOR 
        SELECT DISTINCT baseline_date 
        FROM t_health_baseline 
        WHERE user_id IS NULL OR user_id = 0
        ORDER BY baseline_date DESC 
        LIMIT 30;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 清理无效的基线数据（没有user_id的记录）
    DELETE FROM t_health_baseline 
    WHERE user_id IS NULL OR user_id = 0;

    -- 清理无效的评分数据
    DELETE FROM t_health_score 
    WHERE user_id IS NULL OR user_id = 0;

    -- 清理孤立的组织基线数据（没有对应用户基线的）
    DELETE FROM t_org_health_baseline 
    WHERE NOT EXISTS (
        SELECT 1 FROM t_health_baseline hb 
        WHERE hb.baseline_date = t_org_health_baseline.baseline_date 
        AND hb.feature_name = t_org_health_baseline.feature_name
        AND hb.user_id IS NOT NULL AND hb.user_id > 0
    );

    -- 清理孤立的组织评分数据
    DELETE FROM t_org_health_score 
    WHERE NOT EXISTS (
        SELECT 1 FROM t_health_score hs 
        WHERE hs.score_date = t_org_health_score.score_date 
        AND hs.feature_name = t_org_health_score.feature_name
        AND hs.user_id IS NOT NULL AND hs.user_id > 0
    );

    COMMIT;

    SELECT CONCAT('✅ 清理完成 - ', NOW()) as message;

END //

DELIMITER ;

-- 5. 创建数据质量检查视图
CREATE OR REPLACE VIEW `v_health_data_quality` AS
SELECT 
    baseline_date,
    feature_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN user_id IS NOT NULL AND user_id > 0 THEN 1 END) as valid_user_records,
    COUNT(CASE WHEN device_sn IS NOT NULL AND device_sn != '' THEN 1 END) as valid_device_records,
    COUNT(CASE WHEN sample_count >= 5 THEN 1 END) as sufficient_sample_records,
    COUNT(CASE WHEN std_value > 0 THEN 1 END) as valid_std_records,
    ROUND(COUNT(CASE WHEN user_id IS NOT NULL AND user_id > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as user_coverage_percent
FROM t_health_baseline 
GROUP BY baseline_date, feature_name
ORDER BY baseline_date DESC, feature_name;

-- 6. 创建层级聚合统计视图
CREATE OR REPLACE VIEW `v_health_hierarchy_stats` AS
SELECT 
    hb.baseline_date,
    hb.feature_name,
    COUNT(DISTINCT hb.user_id) as user_count,
    COUNT(DISTINCT ohb_dept.org_id) as department_count,
    COUNT(DISTINCT ohb_tenant.org_id) as tenant_count,
    AVG(hb.mean_value) as overall_avg_value,
    STD(hb.mean_value) as overall_std_value
FROM t_health_baseline hb
LEFT JOIN t_org_health_baseline ohb_dept ON hb.baseline_date = ohb_dept.baseline_date 
    AND hb.feature_name = ohb_dept.feature_name
    AND ohb_dept.org_id < 10000 -- 假设部门ID小于10000
LEFT JOIN t_org_health_baseline ohb_tenant ON hb.baseline_date = ohb_tenant.baseline_date 
    AND hb.feature_name = ohb_tenant.feature_name
    AND ohb_tenant.org_id >= 10000 -- 假设租户ID大于等于10000
WHERE hb.user_id IS NOT NULL AND hb.user_id > 0
GROUP BY hb.baseline_date, hb.feature_name
ORDER BY hb.baseline_date DESC, hb.feature_name;

-- 7. 添加改进版任务执行日志表
CREATE TABLE IF NOT EXISTS `t_improved_health_task_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
    `task_type` VARCHAR(20) NOT NULL COMMENT '任务类型(user_baseline,dept_baseline,tenant_baseline,user_score,dept_score,tenant_score)',
    `start_time` DATETIME NOT NULL COMMENT '开始时间',
    `end_time` DATETIME COMMENT '结束时间',
    `status` VARCHAR(10) NOT NULL COMMENT '执行状态(running,success,failed)',
    `processed_users` INT DEFAULT 0 COMMENT '处理用户数',
    `processed_departments` INT DEFAULT 0 COMMENT '处理部门数',
    `processed_tenants` INT DEFAULT 0 COMMENT '处理租户数',
    `error_message` TEXT COMMENT '错误信息',
    `feature_name` VARCHAR(20) COMMENT '特征名称',
    `target_date` DATE COMMENT '目标日期',
    `execution_time_ms` BIGINT DEFAULT 0 COMMENT '执行时间(毫秒)',
    `data_quality_score` DECIMAL(5,2) DEFAULT 0.00 COMMENT '数据质量评分',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_improved_task_log_name_time` (`task_name`, `start_time`),
    KEY `idx_improved_task_log_type_date` (`task_type`, `target_date`),
    KEY `idx_improved_task_log_status_time` (`status`, `start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='改进版健康任务执行日志表';

-- 8. 插入示例权重配置数据（如果不存在）
INSERT IGNORE INTO `t_weight_cache` (`user_id`, `metric_name`, `weight_value`, `cache_date`, `create_time`) 
SELECT 
    u.id as user_id,
    'heart_rate' as metric_name,
    0.20 as weight_value,
    CURDATE() as cache_date,
    NOW() as create_time
FROM sys_user u 
WHERE u.is_deleted = 0 AND u.id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM t_weight_cache wc 
    WHERE wc.user_id = u.id AND wc.metric_name = 'heart_rate' AND wc.cache_date = CURDATE()
);

-- 为其他主要健康特征插入默认权重
INSERT IGNORE INTO `t_weight_cache` (`user_id`, `metric_name`, `weight_value`, `cache_date`, `create_time`)
SELECT u.id, 'blood_oxygen', 0.18, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'temperature', 0.15, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'pressure_high', 0.06, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'pressure_low', 0.06, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'stress', 0.12, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'sleep', 0.08, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'step', 0.04, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'calorie', 0.03, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0
UNION ALL
SELECT u.id, 'distance', 0.03, CURDATE(), NOW() FROM sys_user u WHERE u.is_deleted = 0;

-- 9. 创建性能监控表
CREATE TABLE IF NOT EXISTS `t_health_performance_metrics` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `metric_date` DATE NOT NULL COMMENT '指标日期',
    `task_type` VARCHAR(50) NOT NULL COMMENT '任务类型',
    `total_execution_time_ms` BIGINT DEFAULT 0 COMMENT '总执行时间',
    `avg_user_processing_time_ms` DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均用户处理时间',
    `total_users_processed` INT DEFAULT 0 COMMENT '处理用户总数',
    `total_records_generated` INT DEFAULT 0 COMMENT '生成记录总数',
    `memory_usage_mb` DECIMAL(10,2) DEFAULT 0.00 COMMENT '内存使用量',
    `cpu_usage_percent` DECIMAL(5,2) DEFAULT 0.00 COMMENT 'CPU使用率',
    `data_quality_issues` INT DEFAULT 0 COMMENT '数据质量问题数',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_performance_date_task` (`metric_date`, `task_type`),
    KEY `idx_performance_date` (`metric_date`),
    KEY `idx_performance_task` (`task_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康数据处理性能指标表';

-- 完成提示
SELECT '✅ 健康基线和评分系统优化完成 - 支持基于userId的层级聚合！' as message,
       '🔧 已添加优化索引、数据质量检查、清理存储过程和性能监控' as details;