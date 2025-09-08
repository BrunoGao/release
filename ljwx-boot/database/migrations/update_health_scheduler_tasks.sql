-- =====================================================
-- 健康定时任务调度器数据库更新脚本
-- 将所有HealthBaselineScoreTasks和HealthRecommendationJob任务
-- 添加到mon_scheduler系统进行统一管理
-- =====================================================

-- 1. 更新现有不完整的任务记录
UPDATE mon_scheduler 
SET 
    job_class_name = 'com.ljwx.modules.health.job.DepartmentHealthAggregationJob',
    description = '部门健康基线聚合任务',
    cron_expression = '0 5 2 * * ?',
    trigger_description = '部门健康基线聚合任务 - 每日02:05执行',
    update_time = NOW()
WHERE job_name = 'DepartmentHealthBaseline';

UPDATE mon_scheduler 
SET 
    job_class_name = 'com.ljwx.modules.health.job.MonthlyDataArchiveJob',
    description = '月度数据归档任务',
    cron_expression = '0 0 0 1 * ?',
    trigger_description = '月度数据归档任务 - 每月1日凌晨执行',
    update_time = NOW()
WHERE job_name = 'MonthlyDataArchive';

UPDATE mon_scheduler 
SET 
    job_class_name = 'com.ljwx.modules.health.job.DepartmentHealthScoreJob',
    description = '部门健康评分生成任务',
    cron_expression = '0 15 2 * * ?',
    trigger_description = '部门健康评分生成任务 - 每日02:15执行',
    update_time = NOW()
WHERE job_name = 'DepartmentHealthScore';

-- 2. 修正现有任务的时间配置和类名（根据HealthBaselineScoreTasks.java）
UPDATE mon_scheduler 
SET 
    job_class_name = 'com.ljwx.modules.health.job.HealthBaselineJob',
    cron_expression = '0 0 2 * * ?',
    trigger_description = '用户健康基线生成任务 - 每日02:00执行',
    update_time = NOW()
WHERE job_name = 'UserHealthBaseline';

UPDATE mon_scheduler 
SET 
    job_class_name = 'com.ljwx.modules.health.job.HealthScoreJob',
    cron_expression = '0 0 4 * * ?',
    trigger_description = '用户健康评分生成任务 - 每日04:00执行',
    update_time = NOW()
WHERE job_name = 'UserHealthScore';

-- 3. 添加缺失的健康定时任务

-- 权重配置验证任务
INSERT INTO mon_scheduler (
    id, create_user, create_time, update_time, customer_id,
    job_name, job_group, job_class_name, description,
    trigger_name, trigger_group, trigger_description,
    cron_expression, trigger_state
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'system', NOW(), NOW(), 0,
    'WeightConfigValidation', 'HealthGroup', 
    'com.ljwx.modules.health.job.WeightValidationJob',
    '权重配置验证任务',
    'WeightConfigValidationTrigger', 'HealthTriggerGroup',
    '权重配置验证任务 - 每日01:00执行',
    '0 0 1 * * ?', 'WAITING'
);

-- 组织健康基线生成任务
INSERT INTO mon_scheduler (
    id, create_user, create_time, update_time, customer_id,
    job_name, job_group, job_class_name, description,
    trigger_name, trigger_group, trigger_description,
    cron_expression, trigger_state
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'system', NOW(), NOW(), 0,
    'OrgHealthBaseline', 'HealthGroup',
    'com.ljwx.modules.health.job.OrgHealthBaselineJob',
    '组织健康基线生成任务',
    'OrgHealthBaselineTrigger', 'HealthTriggerGroup',
    '组织健康基线生成任务 - 每日02:10执行',
    '0 10 2 * * ?', 'WAITING'
);

-- 组织健康评分生成任务
INSERT INTO mon_scheduler (
    id, create_user, create_time, update_time, customer_id,
    job_name, job_group, job_class_name, description,
    trigger_name, trigger_group, trigger_description,
    cron_expression, trigger_state
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'system', NOW(), NOW(), 0,
    'OrgHealthScore', 'HealthGroup',
    'com.ljwx.modules.health.job.OrgHealthScoreJob',
    '组织健康评分生成任务',
    'OrgHealthScoreTrigger', 'HealthTriggerGroup',
    '组织健康评分生成任务 - 每日04:10执行',
    '0 10 4 * * ?', 'WAITING'
);

-- 数据清理任务
INSERT INTO mon_scheduler (
    id, create_user, create_time, update_time, customer_id,
    job_name, job_group, job_class_name, description,
    trigger_name, trigger_group, trigger_description,
    cron_expression, trigger_state
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'system', NOW(), NOW(), 0,
    'HealthDataCleanup', 'HealthGroup',
    'com.ljwx.modules.health.job.HealthDataCleanupJob',
    '健康数据清理任务',
    'HealthDataCleanupTrigger', 'HealthTriggerGroup',
    '健康数据清理任务 - 每日05:00执行',
    '0 0 5 * * ?', 'WAITING'
);

-- 健康建议生成作业（Quartz Job）
INSERT INTO mon_scheduler (
    id, create_user, create_time, update_time, customer_id,
    job_name, job_group, job_class_name, description,
    trigger_name, trigger_group, trigger_description,
    cron_expression, trigger_state
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'system', NOW(), NOW(), 0,
    'HealthRecommendation', 'HealthGroup',
    'com.ljwx.modules.health.job.HealthRecommendationJob',
    '健康建议生成作业',
    'HealthRecommendationTrigger', 'HealthTriggerGroup',
    '健康建议生成作业 - 每日03:00执行',
    '0 0 3 * * ?', 'WAITING'
);

-- 4. 验证查询 - 检查所有健康相关任务
-- SELECT 
--     job_name, job_group, job_class_name, description,
--     cron_expression, trigger_state, create_time
-- FROM mon_scheduler 
-- WHERE job_group = 'HealthGroup'
-- ORDER BY 
--     CASE job_name
--         WHEN 'WeightConfigValidation' THEN 1
--         WHEN 'UserHealthBaseline' THEN 2
--         WHEN 'DepartmentHealthBaseline' THEN 3
--         WHEN 'OrgHealthBaseline' THEN 4
--         WHEN 'DepartmentHealthScore' THEN 5
--         WHEN 'HealthRecommendation' THEN 6
--         WHEN 'UserHealthScore' THEN 7
--         WHEN 'OrgHealthScore' THEN 8
--         WHEN 'HealthDataCleanup' THEN 9
--         WHEN 'MonthlyDataArchive' THEN 10
--         WHEN 'HealthTableArchive' THEN 11
--         ELSE 99
--     END;

-- =====================================================
-- 执行完成后的健康任务时间表：
-- 01:00 - WeightConfigValidation (权重配置验证)
-- 02:00 - UserHealthBaseline (用户健康基线生成)
-- 02:05 - DepartmentHealthBaseline (部门健康基线聚合)
-- 02:10 - OrgHealthBaseline (组织健康基线生成)
-- 02:15 - DepartmentHealthScore (部门健康评分生成)
-- 03:00 - HealthRecommendation (健康建议生成)
-- 04:00 - UserHealthScore (用户健康评分生成)
-- 04:10 - OrgHealthScore (组织健康评分生成)
-- 05:00 - HealthDataCleanup (健康数据清理)
-- 每月1日凌晨 - MonthlyDataArchive + HealthTableArchive (月度分表)
-- =====================================================