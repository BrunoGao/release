-- 健康数据处理定时任务优化SQL脚本
-- 删除旧的分散任务，添加新的统一任务

-- 1. 删除重复和过时的定时任务
DELETE FROM mon_scheduler WHERE job_name IN (
    'HealthTableArchive',           -- 与 MonthlyDataArchive 重复
    'UserHealthBaseline',          -- 替换为统一任务
    'DepartmentHealthBaseline',    -- 替换为统一任务
    'OrgHealthBaseline',           -- 替换为统一任务
    'UserHealthScore',             -- 替换为统一任务
    'DepartmentHealthScore',       -- 替换为统一任务
    'OrgHealthScore',              -- 替换为统一任务
    'HealthRecommendation'         -- 替换为统一任务
);

-- 2. 添加统一健康数据处理任务 (每日凌晨02:00执行)
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'UnifiedHealthProcessing',
    'HealthGroup',
    'UnifiedHealthProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.UnifiedHealthProcessingJob"},{"key":"description","value":"统一健康数据处理任务（基线→评分→建议）"}]',
    '[{"key":"cronExpression","value":"0 0 2 * * ?"},{"key":"description","value":"每日凌晨02:00执行统一健康数据处理"}]',
    'system',
    1,
    NOW()
);

-- 3. 添加分步骤健康数据处理任务（用于手动或独立执行）

-- 健康基线生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'HealthBaselineProcessing',
    'HealthGroup',
    'HealthBaselineProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthBaselineProcessingJob"},{"key":"description","value":"健康基线生成任务"}]',
    '[{"key":"cronExpression","value":"0 0 0 1 1 ? 2099"},{"key":"description","value":"健康基线生成任务（手动执行）"}]',
    'system',
    1,
    NOW()
);

-- 健康评分生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'HealthScoreProcessing',
    'HealthGroup',
    'HealthScoreProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthScoreProcessingJob"},{"key":"description","value":"健康评分生成任务"}]',
    '[{"key":"cronExpression","value":"0 0 0 1 1 ? 2099"},{"key":"description","value":"健康评分生成任务（手动执行）"}]',
    'system',
    1,
    NOW()
);

-- 健康预测生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'HealthPredictionProcessing',
    'HealthGroup',
    'HealthPredictionProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthPredictionProcessingJob"},{"key":"description","value":"健康预测生成任务"}]',
    '[{"key":"cronExpression","value":"0 0 0 1 1 ? 2099"},{"key":"description","value":"健康预测生成任务（手动执行）"}]',
    'system',
    1,
    NOW()
);

-- 健康建议生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'HealthRecommendationProcessing',
    'HealthGroup',
    'HealthRecommendationProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthRecommendationProcessingJob"},{"key":"description","value":"健康建议生成任务"}]',
    '[{"key":"cronExpression","value":"0 0 0 1 1 ? 2099"},{"key":"description","value":"健康建议生成任务（手动执行）"}]',
    'system',
    1,
    NOW()
);

-- 健康档案生成任务
INSERT INTO mon_scheduler (
    id, job_name, job_group, trigger_name, trigger_group, 
    job_data, trigger_data, create_user, create_user_id, create_time
) VALUES (
    UNIX_TIMESTAMP() * 1000 + FLOOR(RAND() * 1000000),
    'HealthProfileProcessing',
    'HealthGroup',
    'HealthProfileProcessingTrigger',
    'HealthTriggerGroup',
    '[{"key":"jobClass","value":"com.ljwx.modules.health.job.HealthProfileProcessingJob"},{"key":"description","value":"健康档案生成任务"}]',
    '[{"key":"cronExpression","value":"0 0 0 1 1 ? 2099"},{"key":"description","value":"健康档案生成任务（手动执行）"}]',
    'system',
    1,
    NOW()
);

-- 保留必要的任务：
-- WeightConfigValidation (权重配置验证) - 01:00
-- MonthlyDataArchive (月度数据归档) - 每月1日00:00  
-- HealthDataCleanup (数据清理) - 05:00

-- 查看优化后的任务列表
SELECT 
    job_name,
    job_group,
    JSON_EXTRACT(job_data, '$[1].value') as description,
    JSON_EXTRACT(trigger_data, '$[0].value') as cron_expression,
    create_time
FROM mon_scheduler 
WHERE job_group = 'HealthGroup'
ORDER BY 
    CASE 
        WHEN JSON_EXTRACT(trigger_data, '$[0].value') = '0 0 1 * * ?' THEN 1   -- 01:00
        WHEN JSON_EXTRACT(trigger_data, '$[0].value') = '0 0 2 * * ?' THEN 2   -- 02:00  
        WHEN JSON_EXTRACT(trigger_data, '$[0].value') = '0 0 5 * * ?' THEN 3   -- 05:00
        WHEN JSON_EXTRACT(trigger_data, '$[0].value') = '0 0 0 1 * ?' THEN 4   -- 每月1日
        ELSE 5
    END,
    job_name;