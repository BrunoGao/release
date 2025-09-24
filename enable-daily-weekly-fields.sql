-- 启用所有 Daily/Weekly 数据字段配置
-- 修复 Daily, weekly 数据查询问题

USE ljwx;

-- 查看当前配置状态
SELECT 'BEFORE UPDATE:' as status;
SELECT data_type, is_enabled, customer_id, is_deleted 
FROM t_health_data_config 
WHERE data_type IN ('sleepData', 'sleep', 'exerciseDailyData', 'exercise_daily', 
                    'workoutData', 'work_out', 'scientificSleepData', 'scientific_sleep', 
                    'exerciseWeekData', 'exercise_week')
ORDER BY customer_id, data_type;

-- 启用所有 Daily/Weekly 字段（如果存在的话）
UPDATE t_health_data_config 
SET is_enabled = 1, 
    update_time = NOW()
WHERE data_type IN ('sleepData', 'sleep', 'exerciseDailyData', 'exercise_daily', 
                    'workoutData', 'work_out', 'scientificSleepData', 'scientific_sleep', 
                    'exerciseWeekData', 'exercise_week')
  AND is_deleted = 0;

-- 为不存在的字段添加基础配置（如果需要的话）
-- 先查看当前存在的客户ID
SELECT 'Adding missing configurations for customers:' as status;

-- 为每个客户添加缺失的Daily/Weekly配置字段
INSERT INTO t_health_data_config (customer_id, data_type, is_enabled, create_time, update_time, is_deleted, weight, warning_low, warning_high)
SELECT DISTINCT 
    customer_id,
    field_name as data_type,
    1 as is_enabled,
    NOW() as create_time,
    NOW() as update_time,
    0 as is_deleted,
    0.05 as weight,  -- 默认权重
    0 as warning_low,
    1000 as warning_high
FROM (
    SELECT DISTINCT customer_id FROM t_health_data_config WHERE is_deleted = 0
) customers
CROSS JOIN (
    SELECT 'sleep' as field_name
    UNION SELECT 'exerciseDailyData' as field_name
    UNION SELECT 'exercise_daily' as field_name
    UNION SELECT 'workoutData' as field_name
    UNION SELECT 'work_out' as field_name
    UNION SELECT 'scientificSleepData' as field_name
    UNION SELECT 'scientific_sleep' as field_name
    UNION SELECT 'exerciseWeekData' as field_name
    UNION SELECT 'exercise_week' as field_name
) fields
WHERE NOT EXISTS (
    SELECT 1 FROM t_health_data_config thdc 
    WHERE thdc.customer_id = customers.customer_id 
      AND thdc.data_type = fields.field_name
      AND thdc.is_deleted = 0
);

-- 查看更新后的配置状态
SELECT 'AFTER UPDATE:' as status;
SELECT data_type, is_enabled, customer_id, is_deleted 
FROM t_health_data_config 
WHERE data_type IN ('sleepData', 'sleep', 'exerciseDailyData', 'exercise_daily', 
                    'workoutData', 'work_out', 'scientificSleepData', 'scientific_sleep', 
                    'exerciseWeekData', 'exercise_week')
ORDER BY customer_id, data_type;

SELECT 'Configuration update completed' as status;