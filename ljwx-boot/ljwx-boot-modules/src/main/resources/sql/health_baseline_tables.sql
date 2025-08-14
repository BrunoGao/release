-- 健康基线和评分系统数据库表结构
-- 创建时间: 2025-01-26
-- 作者: bruno.gao

-- 1. 用户健康基线表
CREATE TABLE IF NOT EXISTS `t_health_baseline` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `device_sn` VARCHAR(50) NOT NULL COMMENT '设备序列号',
    `user_id` BIGINT DEFAULT 0 COMMENT '用户ID',
    `org_id` VARCHAR(20) DEFAULT '1' COMMENT '组织ID',
    `feature_name` VARCHAR(20) NOT NULL COMMENT '特征名称(heart_rate,blood_oxygen等)',
    `baseline_date` DATE NOT NULL COMMENT '基线日期',
    `mean_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均值',
    `std_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '标准差',
    `min_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '最小值',
    `max_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '最大值',
    `sample_count` INT DEFAULT 0 COMMENT '样本数量',
    `is_current` TINYINT DEFAULT 1 COMMENT '是否当前有效(1是0否)',
    `baseline_time` DATE COMMENT '基线生成时间',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_baseline_device_feature_date` (`device_sn`, `feature_name`, `baseline_date`),
    KEY `idx_baseline_org_feature_date` (`org_id`, `feature_name`, `baseline_date`),
    KEY `idx_baseline_date_feature` (`baseline_date`, `feature_name`),
    KEY `idx_baseline_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户健康基线表';

-- 2. 组织健康基线表
CREATE TABLE IF NOT EXISTS `t_org_health_baseline` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `org_id` VARCHAR(20) NOT NULL COMMENT '组织ID',
    `feature_name` VARCHAR(20) NOT NULL COMMENT '特征名称',
    `baseline_date` DATE NOT NULL COMMENT '基线日期',
    `mean_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均值',
    `std_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '标准差',
    `min_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '最小值',
    `max_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '最大值',
    `user_count` INT DEFAULT 0 COMMENT '用户数量',
    `sample_count` INT DEFAULT 0 COMMENT '样本总数',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_org_baseline_org_feature_date` (`org_id`, `feature_name`, `baseline_date`),
    KEY `idx_org_baseline_date_feature` (`baseline_date`, `feature_name`),
    KEY `idx_org_baseline_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织健康基线表';

-- 3. 用户健康评分表
CREATE TABLE IF NOT EXISTS `t_health_score` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `device_sn` VARCHAR(50) NOT NULL COMMENT '设备序列号',
    `user_id` BIGINT DEFAULT 0 COMMENT '用户ID',
    `org_id` VARCHAR(20) DEFAULT '1' COMMENT '组织ID',
    `feature_name` VARCHAR(20) NOT NULL COMMENT '特征名称',
    `avg_value` DECIMAL(10,2) DEFAULT 0.00 COMMENT '当日平均值',
    `z_score` DECIMAL(10,4) DEFAULT 0.0000 COMMENT 'Z分数',
    `score_value` DECIMAL(5,2) DEFAULT 0.00 COMMENT '评分值(0-100)',
    `penalty_value` DECIMAL(5,2) DEFAULT 0.00 COMMENT '惩罚分值',
    `baseline_time` DATE COMMENT '基线时间',
    `score_date` DATE NOT NULL COMMENT '评分日期',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_score_device_feature_date` (`device_sn`, `feature_name`, `score_date`),
    KEY `idx_score_org_feature_date` (`org_id`, `feature_name`, `score_date`),
    KEY `idx_score_date_feature` (`score_date`, `feature_name`),
    KEY `idx_score_value` (`score_value`),
    KEY `idx_score_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户健康评分表';

-- 4. 组织健康评分表
CREATE TABLE IF NOT EXISTS `t_org_health_score` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `org_id` VARCHAR(20) NOT NULL COMMENT '组织ID',
    `feature_name` VARCHAR(20) NOT NULL COMMENT '特征名称',
    `score_date` DATE NOT NULL COMMENT '评分日期',
    `mean_score` DECIMAL(5,2) DEFAULT 0.00 COMMENT '平均评分',
    `std_score` DECIMAL(5,2) DEFAULT 0.00 COMMENT '评分标准差',
    `min_score` DECIMAL(5,2) DEFAULT 0.00 COMMENT '最低评分',
    `max_score` DECIMAL(5,2) DEFAULT 0.00 COMMENT '最高评分',
    `user_count` INT DEFAULT 0 COMMENT '参与评分用户数',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_org_score_org_feature_date` (`org_id`, `feature_name`, `score_date`),
    KEY `idx_org_score_date_feature` (`score_date`, `feature_name`),
    KEY `idx_org_score_mean` (`mean_score`),
    KEY `idx_org_score_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织健康评分表';

-- 5. 健康任务执行日志表
CREATE TABLE IF NOT EXISTS `t_health_task_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `task_name` VARCHAR(50) NOT NULL COMMENT '任务名称',
    `task_type` VARCHAR(20) NOT NULL COMMENT '任务类型(baseline,score,archive)',
    `start_time` DATETIME NOT NULL COMMENT '开始时间',
    `end_time` DATETIME COMMENT '结束时间',
    `status` VARCHAR(10) NOT NULL COMMENT '执行状态(running,success,failed)',
    `processed_count` INT DEFAULT 0 COMMENT '处理记录数',
    `error_message` TEXT COMMENT '错误信息',
    `feature_name` VARCHAR(20) COMMENT '特征名称',
    `target_date` DATE COMMENT '目标日期',
    `execution_time_ms` BIGINT DEFAULT 0 COMMENT '执行时间(毫秒)',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_task_log_name_time` (`task_name`, `start_time`),
    KEY `idx_task_log_status_time` (`status`, `start_time`),
    KEY `idx_task_log_type_date` (`task_type`, `target_date`),
    KEY `idx_task_log_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康任务执行日志表';

-- 6. 添加sleep字段到健康数据表（如果不存在）
ALTER TABLE `t_user_health_data` 
ADD COLUMN IF NOT EXISTS `sleep` DOUBLE DEFAULT NULL COMMENT '睡眠时长(小时)' 
AFTER `stress`;

-- 创建必要的索引优化查询性能
CREATE INDEX IF NOT EXISTS `idx_health_data_device_time` ON `t_user_health_data` (`device_sn`, `timestamp`);
CREATE INDEX IF NOT EXISTS `idx_health_data_org_time` ON `t_user_health_data` (`org_id`, `timestamp`);
CREATE INDEX IF NOT EXISTS `idx_health_data_create_time` ON `t_user_health_data` (`create_time`);

-- 插入健康特征配置数据
INSERT IGNORE INTO `t_health_baseline` (`device_sn`, `feature_name`, `baseline_date`, `mean_value`, `std_value`, `min_value`, `max_value`, `sample_count`, `is_current`, `baseline_time`) VALUES
('SYSTEM_DEFAULT', 'heart_rate', '2025-01-01', 75.0, 15.0, 60.0, 100.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'blood_oxygen', '2025-01-01', 97.0, 3.0, 95.0, 100.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'temperature', '2025-01-01', 36.5, 0.5, 36.0, 37.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'pressure_high', '2025-01-01', 120.0, 20.0, 90.0, 140.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'pressure_low', '2025-01-01', 80.0, 15.0, 60.0, 90.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'stress', '2025-01-01', 50.0, 20.0, 20.0, 80.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'sleep', '2025-01-01', 7.5, 1.5, 6.0, 9.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'step', '2025-01-01', 8000.0, 3000.0, 3000.0, 15000.0, 1000, 1, '2025-01-01'),
('SYSTEM_DEFAULT', 'calorie', '2025-01-01', 300.0, 150.0, 100.0, 600.0, 1000, 1, '2025-01-01');

-- 完成提示
SELECT '✅ 健康基线和评分系统表结构创建完成！' as message; 