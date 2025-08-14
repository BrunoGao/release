-- 企业级系统事件告警方案数据库表结构 - 修复版本
-- 创建时间: 2024年
-- 修复MySQL语法兼容性问题

USE `lj-06`;

-- 1. 微信告警配置表(租户维度)
CREATE TABLE IF NOT EXISTS `t_wechat_alarm_config` (
  `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  `tenant_id` BIGINT NOT NULL COMMENT '租户ID',
  `type` VARCHAR(20) NOT NULL COMMENT '微信类型: enterprise(企业微信)/official(公众号)',
  `corp_id` VARCHAR(100) DEFAULT NULL COMMENT '企业微信企业ID',
  `agent_id` VARCHAR(50) DEFAULT NULL COMMENT '企业微信应用AgentID',
  `secret` VARCHAR(100) DEFAULT NULL COMMENT '企业微信应用Secret',
  `appid` VARCHAR(100) DEFAULT NULL COMMENT '微信公众号AppID',
  `appsecret` VARCHAR(100) DEFAULT NULL COMMENT '微信公众号AppSecret',
  `template_id` VARCHAR(100) DEFAULT NULL COMMENT '微信模板消息ID',
  `enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用告警',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_tenant_type` (`tenant_id`, `type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微信告警配置表(支持企业微信和公众号)';

-- 2. 系统事件规则表
CREATE TABLE IF NOT EXISTS `t_system_event_rule` (
  `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  `event_type` VARCHAR(100) NOT NULL COMMENT '完整事件类型(如com.tdtech.ohos.health.action.SOS_EVENT)',
  `rule_type` VARCHAR(50) NOT NULL COMMENT '规则类型(简化,如SOS_EVENT)',
  `severity_level` VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT '告警级别:critical/high/medium/low',
  `alert_message` VARCHAR(500) NOT NULL COMMENT '告警消息模板',
  `is_emergency` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否紧急事件(触发微信推送)',
  `notification_type` VARCHAR(20) NOT NULL DEFAULT 'message' COMMENT '通知类型:wechat/message/both',
  `retry_count` INT NOT NULL DEFAULT 3 COMMENT '失败重试次数',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用规则',
  `tenant_id` BIGINT NOT NULL DEFAULT 1 COMMENT '租户ID',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_rule_tenant` (`rule_type`, `tenant_id`),
  INDEX `idx_event_type` (`event_type`),
  INDEX `idx_is_emergency` (`is_emergency`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统事件规则配置表';

-- 3. 事件告警队列表
CREATE TABLE IF NOT EXISTS `t_event_alarm_queue` (
  `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
  `event_type` VARCHAR(100) NOT NULL COMMENT '事件类型',
  `device_sn` VARCHAR(50) NOT NULL COMMENT '设备序列号',
  `event_value` VARCHAR(500) DEFAULT NULL COMMENT '事件值',
  `event_data` JSON DEFAULT NULL COMMENT '完整事件数据(JSON格式)',
  `processing_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '处理状态:pending/processing/completed/failed',
  `retry_count` INT NOT NULL DEFAULT 0 COMMENT '已重试次数',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `process_time` DATETIME DEFAULT NULL COMMENT '开始处理时间',
  `complete_time` DATETIME DEFAULT NULL COMMENT '完成时间',
  INDEX `idx_status_time` (`processing_status`, `create_time`),
  INDEX `idx_device_time` (`device_sn`, `create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='事件告警处理队列';

-- 4. 检查并扩展t_alert_info表字段
-- 先检查字段是否存在，再添加
SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND COLUMN_NAME='user_id') = 0,
  'ALTER TABLE `t_alert_info` ADD COLUMN `user_id` BIGINT DEFAULT NULL COMMENT ''用户ID'' AFTER `health_id`',
  'SELECT ''user_id字段已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND COLUMN_NAME='org_id') = 0,
  'ALTER TABLE `t_alert_info` ADD COLUMN `org_id` BIGINT DEFAULT NULL COMMENT ''组织ID'' AFTER `user_id`',
  'SELECT ''org_id字段已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND COLUMN_NAME='tenant_id') = 0,
  'ALTER TABLE `t_alert_info` ADD COLUMN `tenant_id` BIGINT DEFAULT 1 COMMENT ''租户ID'' AFTER `org_id`',
  'SELECT ''tenant_id字段已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 5. 检查并扩展t_alert_action_log表字段
SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_action_log' AND COLUMN_NAME='notification_type') = 0,
  'ALTER TABLE `t_alert_action_log` ADD COLUMN `notification_type` VARCHAR(20) DEFAULT NULL COMMENT ''通知类型:wechat/message/both'' AFTER `result`',
  'SELECT ''notification_type字段已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_action_log' AND COLUMN_NAME='retry_attempt') = 0,
  'ALTER TABLE `t_alert_action_log` ADD COLUMN `retry_attempt` INT DEFAULT 0 COMMENT ''重试次数'' AFTER `notification_type`',
  'SELECT ''retry_attempt字段已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 6. 初始化默认系统事件规则数据
INSERT IGNORE INTO `t_system_event_rule` (`event_type`, `rule_type`, `severity_level`, `alert_message`, `is_emergency`, `notification_type`, `tenant_id`) VALUES 
-- 紧急事件(微信实时告警)
('com.tdtech.ohos.health.action.SOS_EVENT', 'SOS_EVENT', 'critical', 'SOS紧急求助信号', 1, 'both', 1),
('com.tdtech.ohos.health.action.FALLDOWN_EVENT', 'FALLDOWN_EVENT', 'critical', '检测到跌倒事件', 1, 'both', 1),
('com.tdtech.ohos.action.ONE_KEY_ALARM', 'ONE_KEY_ALARM', 'critical', '一键报警触发', 1, 'both', 1),

-- 严重事件(平台消息推送)
('com.tdtech.ohos.action.WEAR_STATUS_CHANGED', 'WEAR_STATUS_CHANGED', 'high', '设备佩戴状态变化', 0, 'message', 1),
('com.tdtech.ohos.health.action.STRESS_HIGH_ALERT', 'STRESS_HIGH_ALERT', 'high', '压力水平过高告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.SPO2_LOW_ALERT', 'SPO2_LOW_ALERT', 'high', '血氧浓度过低告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.HEARTRATE_HIGH_ALERT', 'HEARTRATE_HIGH_ALERT', 'high', '心率过高告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.HEARTRATE_LOW_ALERT', 'HEARTRATE_LOW_ALERT', 'high', '心率过低告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.TEMPERATURE_HIGH_ALERT', 'TEMPERATURE_HIGH_ALERT', 'high', '体温过高告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.TEMPERATURE_LOW_ALERT', 'TEMPERATURE_LOW_ALERT', 'high', '体温过低告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.PRESSURE_HIGH_ALERT', 'PRESSURE_HIGH_ALERT', 'high', '血压过高告警', 0, 'message', 1),
('com.tdtech.ohos.health.action.PRESSURE_LOW_ALERT', 'PRESSURE_LOW_ALERT', 'high', '血压过低告警', 0, 'message', 1),

-- 系统事件(消息通知)
('com.tdtech.ohos.action.CALL_STATE', 'CALL_STATE', 'medium', '通话状态变化', 0, 'message', 1),
('com.tdtech.ohos.action.BOOT_COMPLETED', 'BOOT_COMPLETED', 'medium', '设备启动完成', 0, 'message', 1),
('com.tdtech.ohos.action.UI_SETTINGS_CHANGED', 'UI_SETTINGS_CHANGED', 'low', 'UI设置变更', 0, 'message', 1),
('com.tdtech.ohos.action.FUN_DOUBLE_CLICK', 'FUN_DOUBLE_CLICK', 'low', '功能键双击', 0, 'message', 1);

-- 7. 初始化默认微信告警配置(租户ID=1)
INSERT IGNORE INTO `t_wechat_alarm_config` (`tenant_id`, `type`, `enabled`) VALUES
(1, 'enterprise', 1),
(1, 'official', 1);

-- 8. 创建视图：事件告警统计
DROP VIEW IF EXISTS `v_event_alarm_stats`;
CREATE VIEW `v_event_alarm_stats` AS
SELECT 
  DATE(create_time) as stat_date,
  processing_status,
  COUNT(*) as event_count,
  COUNT(DISTINCT device_sn) as device_count
FROM t_event_alarm_queue 
GROUP BY DATE(create_time), processing_status;

-- 9. 创建视图：告警规则使用统计  
DROP VIEW IF EXISTS `v_alert_rule_usage`;
CREATE VIEW `v_alert_rule_usage` AS
SELECT 
  r.rule_type,
  r.severity_level,
  r.is_emergency,
  COUNT(a.id) as alert_count,
  COUNT(DISTINCT a.device_sn) as device_count,
  AVG(CASE WHEN a.alert_status = 'responded' THEN 1 ELSE 0 END) as response_rate
FROM t_system_event_rule r
LEFT JOIN t_alert_info a ON r.rule_type = a.alert_type
WHERE r.is_active = 1
GROUP BY r.id, r.rule_type, r.severity_level, r.is_emergency;

-- 10. 添加索引优化(检查是否存在再创建)
SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND INDEX_NAME='idx_alert_info_health_user') = 0,
  'CREATE INDEX `idx_alert_info_health_user` ON `t_alert_info` (`health_id`, `user_id`)',
  'SELECT ''索引idx_alert_info_health_user已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_alert_info' AND INDEX_NAME='idx_alert_info_tenant_status') = 0,
  'CREATE INDEX `idx_alert_info_tenant_status` ON `t_alert_info` (`tenant_id`, `alert_status`)',
  'SELECT ''索引idx_alert_info_tenant_status已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = (SELECT IF(
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
   WHERE TABLE_SCHEMA='lj-06' AND TABLE_NAME='t_device_message' AND INDEX_NAME='idx_device_message_health') = 0,
  'CREATE INDEX `idx_device_message_health` ON `t_device_message` (`device_sn`, `create_time`)',
  'SELECT ''索引idx_device_message_health已存在'' as message'
));
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 完成提示
SELECT '🎉 企业级系统事件告警方案数据库表结构创建完成!' as message; 
