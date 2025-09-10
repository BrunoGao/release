-- =====================================
-- 告警规则系统全流程升级数据库脚本
-- 基于现有t_alert_rules表，向下兼容地新增字段
-- =====================================

-- 1. 告警规则表优化 (t_alert_rules)
-- 保持现有字段，新增扩展字段
ALTER TABLE `t_alert_rules` 
ADD COLUMN `rule_category` ENUM('SINGLE', 'COMPOSITE', 'COMPLEX') DEFAULT 'SINGLE' COMMENT '规则类型：单体征/复合/复杂' AFTER `rule_type`,
ADD COLUMN `condition_expression` JSON COMMENT '复合条件表达式' AFTER `dsl`,
ADD COLUMN `time_window_seconds` INT DEFAULT 300 COMMENT '时间窗口(秒)' AFTER `condition_expression`,
ADD COLUMN `cooldown_seconds` INT DEFAULT 600 COMMENT '告警冷却期(秒)' AFTER `time_window_seconds`,
ADD COLUMN `priority_level` INT DEFAULT 3 COMMENT '优先级(1-5，数字越小优先级越高)' AFTER `cooldown_seconds`,
ADD COLUMN `rule_tags` JSON COMMENT '规则标签，便于分类管理' AFTER `priority_level`,
ADD COLUMN `effective_time_start` TIME COMMENT '生效开始时间' AFTER `rule_tags`,
ADD COLUMN `effective_time_end` TIME COMMENT '生效结束时间' AFTER `effective_time_start`,
ADD COLUMN `effective_days` VARCHAR(20) DEFAULT '1,2,3,4,5,6,7' COMMENT '生效星期(1-7)' AFTER `effective_time_end`,
ADD COLUMN `version` BIGINT DEFAULT 1 COMMENT '规则版本号' AFTER `effective_days`,
ADD COLUMN `enabled_channels` JSON COMMENT '启用的通知渠道' AFTER `version`;

-- 添加新的索引
ALTER TABLE `t_alert_rules`
ADD INDEX `idx_customer_category` (`customer_id`, `rule_category`),
ADD INDEX `idx_priority` (`priority_level`),
ADD INDEX `idx_physical_sign_active` (`physical_sign`, `is_enabled`),
ADD INDEX `idx_version` (`version`),
ADD INDEX `idx_effective_time` (`effective_time_start`, `effective_time_end`);

-- 2. 告警记录表增强 (t_alert_info)
ALTER TABLE `t_alert_info`
ADD COLUMN `rule_version` BIGINT COMMENT '规则版本' AFTER `rule_id`,
ADD COLUMN `trigger_conditions` JSON COMMENT '触发条件详情' AFTER `rule_version`,
ADD COLUMN `evaluation_context` JSON COMMENT '评估上下文' AFTER `trigger_conditions`,
ADD COLUMN `suppression_key` VARCHAR(128) COMMENT '抑制键' AFTER `evaluation_context`,
ADD COLUMN `escalation_level` INT DEFAULT 0 COMMENT '升级级别' AFTER `suppression_key`,
ADD COLUMN `ack_required` BOOLEAN DEFAULT FALSE COMMENT '是否需要确认' AFTER `escalation_level`,
ADD COLUMN `auto_resolve` BOOLEAN DEFAULT FALSE COMMENT '是否自动恢复' AFTER `ack_required`;

-- 添加新的索引
ALTER TABLE `t_alert_info`
ADD INDEX `idx_suppression` (`suppression_key`),
ADD INDEX `idx_escalation` (`escalation_level`),
ADD INDEX `idx_rule_version` (`rule_id`, `rule_version`),
ADD INDEX `idx_trigger_time` (`alert_timestamp`);

-- 3. 新增缓存同步表
CREATE TABLE `t_alert_cache_sync` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `customer_id` BIGINT NOT NULL COMMENT '客户ID',
  `cache_key` VARCHAR(255) NOT NULL COMMENT '缓存键名',
  `version` BIGINT NOT NULL DEFAULT 1 COMMENT '缓存版本号',
  `last_sync_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后同步时间',
  `sync_status` ENUM('pending', 'synced', 'failed') DEFAULT 'pending' COMMENT '同步状态',
  `error_message` TEXT COMMENT '错误信息',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_customer_cache` (`customer_id`, `cache_key`),
  INDEX `idx_sync_status` (`sync_status`),
  INDEX `idx_last_sync` (`last_sync_time`),
  INDEX `idx_customer_id` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则缓存同步状态表';

-- 4. 新增告警规则性能统计表
CREATE TABLE `t_alert_rule_performance` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `rule_id` BIGINT NOT NULL COMMENT '规则ID',
  `customer_id` BIGINT NOT NULL COMMENT '客户ID',
  `execution_count` BIGINT DEFAULT 0 COMMENT '执行次数',
  `success_count` BIGINT DEFAULT 0 COMMENT '成功次数',
  `failure_count` BIGINT DEFAULT 0 COMMENT '失败次数',
  `avg_execution_time` DECIMAL(10,3) DEFAULT 0 COMMENT '平均执行时间(ms)',
  `max_execution_time` DECIMAL(10,3) DEFAULT 0 COMMENT '最大执行时间(ms)',
  `last_execution_time` DATETIME COMMENT '最后执行时间',
  `alert_generated_count` BIGINT DEFAULT 0 COMMENT '生成告警数量',
  `performance_score` DECIMAL(5,2) DEFAULT 100.00 COMMENT '性能评分(0-100)',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_rule_customer` (`rule_id`, `customer_id`),
  INDEX `idx_rule_id` (`rule_id`),
  INDEX `idx_customer_id` (`customer_id`),
  INDEX `idx_performance_score` (`performance_score`),
  INDEX `idx_last_execution` (`last_execution_time`),
  FOREIGN KEY (`rule_id`) REFERENCES `t_alert_rules`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则性能统计表';

-- 5. 新增告警抑制记录表
CREATE TABLE `t_alert_suppression` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `suppression_key` VARCHAR(128) NOT NULL COMMENT '抑制键',
  `rule_id` BIGINT NOT NULL COMMENT '规则ID',
  `device_sn` VARCHAR(100) COMMENT '设备序列号',
  `customer_id` BIGINT NOT NULL COMMENT '客户ID',
  `suppression_start` DATETIME NOT NULL COMMENT '抑制开始时间',
  `suppression_end` DATETIME COMMENT '抑制结束时间',
  `suppressed_count` INT DEFAULT 1 COMMENT '被抑制告警数量',
  `last_suppressed_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后抑制时间',
  `status` ENUM('active', 'expired', 'cancelled') DEFAULT 'active' COMMENT '抑制状态',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_suppression_key` (`suppression_key`),
  INDEX `idx_rule_device` (`rule_id`, `device_sn`),
  INDEX `idx_customer_status` (`customer_id`, `status`),
  INDEX `idx_suppression_time` (`suppression_start`, `suppression_end`),
  FOREIGN KEY (`rule_id`) REFERENCES `t_alert_rules`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警抑制记录表';

-- 6. 数据迁移和默认值设置
-- 将现有rule_type映射到新的rule_category
UPDATE `t_alert_rules` 
SET `rule_category` = CASE 
  WHEN `rule_type` = 'metric' THEN 'SINGLE'
  WHEN `rule_type` = 'custom' THEN 'COMPLEX'
  ELSE 'SINGLE'
END 
WHERE `rule_category` IS NULL;

-- 设置默认的enabled_channels
UPDATE `t_alert_rules` 
SET `enabled_channels` = JSON_ARRAY(
  CASE 
    WHEN `notification_type` = 'wechat' THEN 'wechat'
    WHEN `notification_type` = 'message' THEN 'message'
    WHEN `notification_type` = 'both' THEN 'wechat'
    ELSE 'message'
  END,
  CASE 
    WHEN `notification_type` = 'both' THEN 'message'
    ELSE NULL
  END
)
WHERE `enabled_channels` IS NULL;

-- 清理enabled_channels中的NULL值
UPDATE `t_alert_rules` 
SET `enabled_channels` = JSON_REMOVE(`enabled_channels`, JSON_UNQUOTE(JSON_SEARCH(`enabled_channels`, 'one', NULL)))
WHERE JSON_SEARCH(`enabled_channels`, 'one', NULL) IS NOT NULL;

-- 设置默认优先级：根据severity_level映射
UPDATE `t_alert_rules` 
SET `priority_level` = CASE 
  WHEN `level` = 'critical' THEN 1
  WHEN `level` = 'major' THEN 2
  WHEN `level` = 'minor' THEN 3
  WHEN `level` = 'info' THEN 4
  ELSE 3
END 
WHERE `priority_level` IS NULL;

-- 7. 创建视图便于查询
CREATE VIEW `v_alert_rules_enhanced` AS
SELECT 
  ar.id,
  ar.rule_type,
  ar.rule_category,
  ar.physical_sign,
  ar.threshold_min,
  ar.threshold_max,
  ar.condition_expression,
  ar.time_window_seconds,
  ar.cooldown_seconds,
  ar.priority_level,
  ar.rule_tags,
  ar.effective_time_start,
  ar.effective_time_end,
  ar.effective_days,
  ar.alert_message,
  ar.level as severity_level,
  ar.enabled_channels,
  ar.is_enabled,
  ar.customer_id,
  ar.version,
  ar.create_time,
  ar.update_time,
  -- 性能统计
  COALESCE(arp.execution_count, 0) as execution_count,
  COALESCE(arp.success_count, 0) as success_count,
  COALESCE(arp.avg_execution_time, 0) as avg_execution_time,
  COALESCE(arp.alert_generated_count, 0) as alert_generated_count,
  COALESCE(arp.performance_score, 100.00) as performance_score,
  arp.last_execution_time
FROM `t_alert_rules` ar
LEFT JOIN `t_alert_rule_performance` arp ON ar.id = arp.rule_id AND ar.customer_id = arp.customer_id
WHERE ar.is_deleted = 0;

-- 8. 创建触发器维护version字段
DELIMITER $$
CREATE TRIGGER `tr_alert_rules_version_update` 
BEFORE UPDATE ON `t_alert_rules`
FOR EACH ROW 
BEGIN
  -- 当关键字段发生变化时，增加版本号
  IF (NEW.rule_category != OLD.rule_category OR
      NEW.physical_sign != OLD.physical_sign OR
      NEW.threshold_min != OLD.threshold_min OR
      NEW.threshold_max != OLD.threshold_max OR
      NEW.condition_expression != OLD.condition_expression OR
      NEW.time_window_seconds != OLD.time_window_seconds OR
      NEW.cooldown_seconds != OLD.cooldown_seconds OR
      NEW.priority_level != OLD.priority_level OR
      NEW.effective_time_start != OLD.effective_time_start OR
      NEW.effective_time_end != OLD.effective_time_end OR
      NEW.effective_days != OLD.effective_days OR
      NEW.enabled_channels != OLD.enabled_channels OR
      NEW.is_enabled != OLD.is_enabled OR
      NEW.alert_message != OLD.alert_message) THEN
    SET NEW.version = OLD.version + 1;
  END IF;
END$$
DELIMITER ;

-- 9. 初始化缓存同步表
INSERT INTO `t_alert_cache_sync` (`customer_id`, `cache_key`, `version`, `sync_status`)
SELECT DISTINCT 
  customer_id, 
  CONCAT('alert_rules_', customer_id),
  1,
  'pending'
FROM `t_alert_rules` 
WHERE customer_id IS NOT NULL AND customer_id > 0
ON DUPLICATE KEY UPDATE version = 1;

-- 10. 创建索引优化查询性能
-- 复合索引用于常见查询场景
CREATE INDEX `idx_rules_category_enabled_customer` ON `t_alert_rules` (`rule_category`, `is_enabled`, `customer_id`);
CREATE INDEX `idx_rules_priority_category` ON `t_alert_rules` (`priority_level`, `rule_category`);
CREATE INDEX `idx_alert_info_timestamp_rule` ON `t_alert_info` (`alert_timestamp`, `rule_id`);

-- 11. 添加约束确保数据完整性
-- 确保复合规则必须有condition_expression
ALTER TABLE `t_alert_rules` 
ADD CONSTRAINT `chk_composite_condition` 
CHECK (
  (rule_category != 'COMPOSITE') OR 
  (rule_category = 'COMPOSITE' AND condition_expression IS NOT NULL)
);

-- 确保优先级在有效范围内
ALTER TABLE `t_alert_rules` 
ADD CONSTRAINT `chk_priority_range` 
CHECK (priority_level >= 1 AND priority_level <= 5);

-- 确保时间窗口和冷却期为正数
ALTER TABLE `t_alert_rules` 
ADD CONSTRAINT `chk_time_positive` 
CHECK (time_window_seconds > 0 AND cooldown_seconds >= 0);

-- 12. 创建存储过程用于缓存管理
DELIMITER $$
CREATE PROCEDURE `sp_refresh_alert_cache`(IN p_customer_id BIGINT)
BEGIN
  DECLARE v_version BIGINT DEFAULT 1;
  
  -- 获取当前版本号
  SELECT COALESCE(MAX(version), 0) + 1 INTO v_version
  FROM `t_alert_cache_sync` 
  WHERE customer_id = p_customer_id AND cache_key = CONCAT('alert_rules_', p_customer_id);
  
  -- 更新同步状态
  INSERT INTO `t_alert_cache_sync` 
    (customer_id, cache_key, version, sync_status, last_sync_time)
  VALUES 
    (p_customer_id, CONCAT('alert_rules_', p_customer_id), v_version, 'pending', NOW())
  ON DUPLICATE KEY UPDATE
    version = v_version,
    sync_status = 'pending',
    last_sync_time = NOW(),
    error_message = NULL;
  
  -- 返回版本信息
  SELECT p_customer_id as customer_id, v_version as version, 'pending' as status;
END$$
DELIMITER ;

-- 验证升级完成
SELECT 
  'Alert Rules Schema Upgrade Completed' as message,
  COUNT(*) as total_rules,
  COUNT(CASE WHEN rule_category = 'SINGLE' THEN 1 END) as single_rules,
  COUNT(CASE WHEN rule_category = 'COMPOSITE' THEN 1 END) as composite_rules,
  COUNT(CASE WHEN rule_category = 'COMPLEX' THEN 1 END) as complex_rules
FROM t_alert_rules 
WHERE is_deleted = 0;

-- 显示新增的表
SHOW TABLES LIKE '%alert%';

-- 显示表结构变化
DESCRIBE t_alert_rules;