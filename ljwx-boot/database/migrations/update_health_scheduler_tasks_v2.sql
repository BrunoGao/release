-- =====================================================
-- 健康定时任务调度器数据库更新脚本 (适配实际表结构)
-- 将所有HealthBaselineScoreTasks和HealthRecommendationJob任务
-- 添加到mon_scheduler系统进行统一管理
-- =====================================================

-- 1. 更新现有不完整的任务记录 (DepartmentHealthBaseline 已经配置完整，跳过)

-- 更新 DepartmentHealthScore 任务的job_data
UPDATE mon_scheduler 
SET 
    job_data = '[{"key":"jobClass","value":"com.ljwx.modules.health.job.DepartmentHealthScoreJob"},{"key":"description","value":"部门健康评分生成任务"}]',
    update_time = NOW()
WHERE job_name = 'DepartmentHealthScore';

-- 更新 HealthTableArchive 任务配置
UPDATE mon_scheduler 
SET 
    job_data = '[{"key":"jobClass","value":"com.ljwx.modules.health.job.MonthlyDataArchiveJob"},{"key":"description","value":"健康数据按月分表任务"}]',
    trigger_data = '[{"key":"cronExpression","value":"0 0 0 1 * ?"},{"key":"description","value":"每月1日凌晨00:00执行分表任务"}]',
    update_time = NOW()
WHERE job_name = 'HealthTableArchive';

-- 更新 UserHealthBaseline 任务配置
UPDATE mon_scheduler 
SET 
    job_data = '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthBaselineJob"},{"key":"description","value":"用户健康基线生成任务"}]',
    trigger_data = '[{"key":"cronExpression","value":"0 0 2 * * ?"},{"key":"description","value":"每日凌晨02:00执行用户基线生成"}]',
    update_time = NOW()
WHERE job_name = 'UserHealthBaseline';

-- 更新 UserHealthScore 任务配置
UPDATE mon_scheduler 
SET 
    job_data = '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthScoreJob"},{"key":"description","value":"用户健康评分生成任务"}]',
    trigger_data = '[{"key":"cronExpression","value":"0 0 4 * * ?"},{"key":"description","value":"每日凌晨04:00执行用户评分生成"}]',
    update_time = NOW()
WHERE job_name = 'UserHealthScore';

-- 2. 添加缺失的健康定时任务

-- 权重配置验证任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group,
    job_data, trigger_data, 
    create_user, create_user_id, create_time, update_time, is_deleted
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'WeightConfigValidation', 'HealthGroup', 
    'WeightConfigValidationTrigger', 'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.WeightValidationJob"},{"key":"description","value":"权重配置验证任务"}]',
    '[{"key":"cronExpression","value":"0 0 1 * * ?"},{"key":"description","value":"每日凌晨01:00执行权重验证"}]',
    'system', 1, NOW(), NOW(), 0
);

-- 组织健康基线生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group,
    job_data, trigger_data,
    create_user, create_user_id, create_time, update_time, is_deleted
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'OrgHealthBaseline', 'HealthGroup',
    'OrgHealthBaselineTrigger', 'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.OrgHealthBaselineJob"},{"key":"description","value":"组织健康基线生成任务"}]',
    '[{"key":"cronExpression","value":"0 10 2 * * ?"},{"key":"description","value":"每日凌晨02:10执行组织基线生成"}]',
    'system', 1, NOW(), NOW(), 0
);

-- 组织健康评分生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group,
    job_data, trigger_data,
    create_user, create_user_id, create_time, update_time, is_deleted
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'OrgHealthScore', 'HealthGroup',
    'OrgHealthScoreTrigger', 'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.OrgHealthScoreJob"},{"key":"description","value":"组织健康评分生成任务"}]',
    '[{"key":"cronExpression","value":"0 10 4 * * ?"},{"key":"description","value":"每日凌晨04:10执行组织评分生成"}]',
    'system', 1, NOW(), NOW(), 0
);

-- 数据清理任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group,
    job_data, trigger_data,
    create_user, create_user_id, create_time, update_time, is_deleted
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'HealthDataCleanup', 'HealthGroup',
    'HealthDataCleanupTrigger', 'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthDataCleanupJob"},{"key":"description","value":"健康数据清理任务"}]',
    '[{"key":"cronExpression","value":"0 0 5 * * ?"},{"key":"description","value":"每日凌晨05:00执行数据清理"}]',
    'system', 1, NOW(), NOW(), 0
);

-- 健康建议生成作业（Quartz Job）
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group,
    job_data, trigger_data,
    create_user, create_user_id, create_time, update_time, is_deleted
) VALUES (
    UNIX_TIMESTAMP(NOW()) * 1000 + FLOOR(RAND() * 1000),
    'HealthRecommendation', 'HealthGroup',
    'HealthRecommendationTrigger', 'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthRecommendationJob"},{"key":"description","value":"健康建议生成作业"}]',
    '[{"key":"cronExpression","value":"0 0 3 * * ?"},{"key":"description","value":"每日凌晨03:00执行健康建议生成"}]',
    'system', 1, NOW(), NOW(), 0
);

-- 3. 验证查询 - 检查所有健康相关任务
SELECT 
    job_name, 
    job_group,
    JSON_UNQUOTE(JSON_EXTRACT(job_data, '$[0].value')) as job_class,
    JSON_UNQUOTE(JSON_EXTRACT(job_data, '$[1].value')) as description,
    JSON_UNQUOTE(JSON_EXTRACT(trigger_data, '$[0].value')) as cron_expression,
    create_time,
    update_time
FROM mon_scheduler 
WHERE job_group = 'HealthGroup'
ORDER BY 
    CASE job_name
        WHEN 'WeightConfigValidation' THEN 1
        WHEN 'UserHealthBaseline' THEN 2
        WHEN 'DepartmentHealthBaseline' THEN 3
        WHEN 'OrgHealthBaseline' THEN 4
        WHEN 'DepartmentHealthScore' THEN 5
        WHEN 'HealthRecommendation' THEN 6
        WHEN 'UserHealthScore' THEN 7
        WHEN 'OrgHealthScore' THEN 8
        WHEN 'HealthDataCleanup' THEN 9
        WHEN 'MonthlyDataArchive' THEN 10
        WHEN 'HealthTableArchive' THEN 11
        ELSE 99
    END;

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