-- =============================================
-- 健康预测数据表结构设计
-- 支持LSTM/ARIMA时间序列预测结果存储
-- Author: Bruno Gao <gaojunivas@gmail.com>
-- Date: 2025-01-26
-- =============================================

-- 1. 健康预测主表
CREATE TABLE IF NOT EXISTS `t_health_prediction` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '预测记录ID',
  `user_id` BIGINT(20) NOT NULL COMMENT '用户ID',
  `customer_id` BIGINT(20) NOT NULL COMMENT '租户ID',
  `device_sn` VARCHAR(50) NULL COMMENT '设备序列号',
  
  -- 预测基本信息
  `prediction_type` VARCHAR(50) NOT NULL COMMENT '预测类型：health_trend|risk_assessment|intervention_effect|deterioration_warning|recovery_timeline',
  `feature_name` VARCHAR(50) NOT NULL COMMENT '预测的健康特征：heart_rate|blood_oxygen|temperature|pressure_high|pressure_low|stress|step|calorie|distance|sleep',
  `model_type` VARCHAR(30) NOT NULL COMMENT '预测模型类型：LSTM|ARIMA|LINEAR_REGRESSION|RANDOM_FOREST',
  `model_version` VARCHAR(20) NOT NULL DEFAULT 'v1.0' COMMENT '模型版本号',
  
  -- 时间相关字段
  `prediction_date` DATE NOT NULL COMMENT '预测生成日期',
  `prediction_start_date` DATE NOT NULL COMMENT '预测开始日期',
  `prediction_end_date` DATE NOT NULL COMMENT '预测结束日期',
  `prediction_horizon_days` INT NOT NULL DEFAULT 30 COMMENT '预测时间跨度（天）',
  
  -- 预测结果
  `predicted_value` DECIMAL(10,4) NULL COMMENT '预测数值（单一值预测）',
  `predicted_values` JSON NULL COMMENT '预测数值序列（时间序列预测）',
  `confidence_score` DECIMAL(5,4) NOT NULL DEFAULT 0.7500 COMMENT '置信度评分 0-1',
  `prediction_accuracy` DECIMAL(5,4) NULL COMMENT '预测准确性（回测验证结果）',
  
  -- 预测详情
  `prediction_details` JSON NULL COMMENT '详细预测信息：趋势方向、变化幅度、关键影响因子',
  `contributing_factors` JSON NULL COMMENT '影响因子权重分析',
  `risk_indicators` JSON NULL COMMENT '风险指标和预警阈值',
  `intervention_recommendations` JSON NULL COMMENT '干预建议',
  
  -- 模型相关
  `training_data_period` VARCHAR(50) NULL COMMENT '训练数据时间段',
  `training_sample_count` INT NULL COMMENT '训练样本数量',
  `model_parameters` JSON NULL COMMENT '模型参数配置',
  `feature_importance` JSON NULL COMMENT '特征重要性分析',
  
  -- 验证和监控
  `validation_metrics` JSON NULL COMMENT '模型验证指标：MAE、RMSE、MAPE等',
  `prediction_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '预测状态：pending|completed|validated|expired|failed',
  `actual_outcome` DECIMAL(10,4) NULL COMMENT '实际结果（用于模型效果评估）',
  `prediction_error` DECIMAL(10,4) NULL COMMENT '预测误差',
  
  -- 审计字段
  `created_by` VARCHAR(50) NULL COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` VARCHAR(50) NULL COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-未删除，1-已删除',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_prediction_type` (`user_id`, `prediction_type`, `prediction_date`),
  KEY `idx_customer_feature` (`customer_id`, `feature_name`, `prediction_date`),
  KEY `idx_prediction_date_status` (`prediction_date`, `prediction_status`),
  KEY `idx_device_sn` (`device_sn`),
  KEY `idx_model_type_version` (`model_type`, `model_version`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康预测数据表';

-- 2. 预测模型配置表
CREATE TABLE IF NOT EXISTS `t_health_prediction_model_config` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `customer_id` BIGINT(20) NOT NULL COMMENT '租户ID',
  `model_name` VARCHAR(100) NOT NULL COMMENT '模型名称',
  `model_type` VARCHAR(30) NOT NULL COMMENT '模型类型：LSTM|ARIMA|LINEAR_REGRESSION|RANDOM_FOREST',
  `feature_name` VARCHAR(50) NOT NULL COMMENT '适用的健康特征',
  `model_version` VARCHAR(20) NOT NULL DEFAULT 'v1.0' COMMENT '模型版本',
  
  -- 模型配置参数
  `model_config` JSON NOT NULL COMMENT '模型配置参数JSON',
  `training_config` JSON NOT NULL COMMENT '训练配置参数JSON',
  `hyperparameters` JSON NULL COMMENT '超参数配置',
  
  -- 模型性能指标
  `performance_metrics` JSON NULL COMMENT '模型性能指标',
  `validation_results` JSON NULL COMMENT '验证结果',
  `benchmark_scores` JSON NULL COMMENT '基准测试分数',
  
  -- 使用控制
  `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：0-禁用，1-启用',
  `min_training_samples` INT NOT NULL DEFAULT 100 COMMENT '最少训练样本数',
  `max_prediction_horizon` INT NOT NULL DEFAULT 90 COMMENT '最大预测时间跨度（天）',
  `update_frequency_hours` INT NOT NULL DEFAULT 24 COMMENT '模型更新频率（小时）',
  
  -- 审计字段
  `created_by` VARCHAR(50) NULL COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` VARCHAR(50) NULL COMMENT '更新者', 
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否删除：0-未删除，1-已删除',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_customer_model_feature_version` (`customer_id`, `model_type`, `feature_name`, `model_version`),
  KEY `idx_model_type_enabled` (`model_type`, `is_enabled`),
  KEY `idx_feature_name` (`feature_name`),
  KEY `idx_is_deleted` (`is_deleted`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康预测模型配置表';

-- 3. 预测任务执行日志表  
CREATE TABLE IF NOT EXISTS `t_health_prediction_task_log` (
  `id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT '任务日志ID',
  `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
  `execution_date` DATE NOT NULL COMMENT '执行日期',
  `start_time` DATETIME NOT NULL COMMENT '开始时间',
  `end_time` DATETIME NULL COMMENT '结束时间',
  `duration_seconds` INT NULL COMMENT '执行时长（秒）',
  
  -- 执行结果
  `task_status` VARCHAR(20) NOT NULL COMMENT '任务状态：running|completed|failed|cancelled',
  `processed_users` INT NOT NULL DEFAULT 0 COMMENT '处理用户数量',
  `generated_predictions` INT NOT NULL DEFAULT 0 COMMENT '生成预测数量',
  `failed_predictions` INT NOT NULL DEFAULT 0 COMMENT '失败预测数量',
  
  -- 详细信息
  `execution_details` JSON NULL COMMENT '执行详情',
  `error_message` TEXT NULL COMMENT '错误信息',
  `performance_stats` JSON NULL COMMENT '性能统计',
  
  -- 审计字段
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_task_execution_date` (`task_name`, `execution_date`),
  KEY `idx_task_status` (`task_status`),
  KEY `idx_execution_date` (`execution_date`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康预测任务执行日志表';

-- 4. 插入默认的预测模型配置
INSERT INTO `t_health_prediction_model_config` 
(`customer_id`, `model_name`, `model_type`, `feature_name`, `model_version`, 
 `model_config`, `training_config`, `is_enabled`, `created_by`) 
VALUES 
-- LSTM模型配置 - 适用于心率预测
(1, 'Heart Rate LSTM Predictor', 'LSTM', 'heart_rate', 'v1.0',
 JSON_OBJECT(
   'sequence_length', 30,
   'lstm_units', 50, 
   'dropout_rate', 0.2,
   'epochs', 100,
   'batch_size', 32
 ),
 JSON_OBJECT(
   'train_test_split', 0.8,
   'validation_split', 0.2,
   'early_stopping_patience', 10
 ),
 1, 'system'),

-- ARIMA模型配置 - 适用于血氧预测  
(1, 'Blood Oxygen ARIMA Predictor', 'ARIMA', 'blood_oxygen', 'v1.0',
 JSON_OBJECT(
   'order_p', 2,
   'order_d', 1, 
   'order_q', 2,
   'seasonal_P', 1,
   'seasonal_D', 1,
   'seasonal_Q', 1,
   'seasonal_period', 7
 ),
 JSON_OBJECT(
   'auto_arima', true,
   'information_criterion', 'aic',
   'max_p', 5,
   'max_d', 2,
   'max_q', 5
 ),
 1, 'system'),

-- Linear Regression模型配置 - 适用于体温预测
(1, 'Temperature Linear Predictor', 'LINEAR_REGRESSION', 'temperature', 'v1.0', 
 JSON_OBJECT(
   'fit_intercept', true,
   'normalize', false,
   'polynomial_degree', 2
 ),
 JSON_OBJECT(
   'cross_validation_folds', 5,
   'regularization_alpha', 0.1
 ),
 1, 'system');

-- 5. 创建相关索引优化
-- 为主表创建分区（按月分区，提高查询性能）
-- ALTER TABLE t_health_prediction PARTITION BY RANGE (YEAR(prediction_date)*100 + MONTH(prediction_date))
-- (
--   PARTITION p202501 VALUES LESS THAN (202502),
--   PARTITION p202502 VALUES LESS THAN (202503),
--   PARTITION p202503 VALUES LESS THAN (202504),
--   PARTITION p202504 VALUES LESS THAN (202505),
--   PARTITION p202505 VALUES LESS THAN (202506),
--   PARTITION p202506 VALUES LESS THAN (202507),
--   PARTITION p_future VALUES LESS THAN MAXVALUE
-- );

-- 6. 创建视图简化常用查询
CREATE OR REPLACE VIEW `v_latest_health_predictions` AS
SELECT 
  hp.user_id,
  hp.customer_id,
  hp.prediction_type,
  hp.feature_name,
  hp.predicted_value,
  hp.confidence_score,
  hp.prediction_date,
  hp.prediction_end_date,
  hp.prediction_status,
  ui.user_name,
  ui.phone
FROM t_health_prediction hp
LEFT JOIN t_user_info ui ON hp.user_id = ui.id
WHERE hp.is_deleted = 0 
AND hp.prediction_status IN ('completed', 'validated')
AND hp.prediction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY hp.user_id, hp.feature_name, hp.prediction_date DESC;

-- 7. 创建存储过程 - 获取用户预测摘要
DELIMITER $$

CREATE PROCEDURE `GetUserHealthPredictionSummary`(
  IN p_user_id BIGINT,
  IN p_customer_id BIGINT,
  IN p_days_back INT DEFAULT 30
)
BEGIN
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  
  SELECT 
    feature_name,
    prediction_type,
    AVG(confidence_score) as avg_confidence,
    MAX(prediction_date) as latest_prediction_date,
    COUNT(*) as prediction_count,
    AVG(prediction_accuracy) as avg_accuracy
  FROM t_health_prediction
  WHERE user_id = p_user_id
    AND customer_id = p_customer_id
    AND is_deleted = 0
    AND prediction_date >= DATE_SUB(CURDATE(), INTERVAL p_days_back DAY)
    AND prediction_status IN ('completed', 'validated')
  GROUP BY feature_name, prediction_type
  ORDER BY latest_prediction_date DESC, avg_confidence DESC;
END$$

DELIMITER ;

-- 8. 权限设置
-- GRANT SELECT, INSERT, UPDATE ON t_health_prediction TO 'ljwx_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON t_health_prediction_model_config TO 'ljwx_app'@'%';
-- GRANT SELECT, INSERT, UPDATE ON t_health_prediction_task_log TO 'ljwx_app'@'%';

-- 执行完成后的验证查询
SELECT 'Health Prediction Tables Created Successfully' as status;
SELECT TABLE_NAME, ENGINE, TABLE_ROWS, TABLE_COMMENT 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME LIKE 't_health_prediction%';