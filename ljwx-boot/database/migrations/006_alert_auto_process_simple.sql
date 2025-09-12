-- 告警自动处理功能数据库增强脚本 (简化版)
-- 执行时间：2025-09-11

USE test;

-- ============================
-- 1. t_alert_rules 表增强 - 添加自动处理字段
-- ============================

ALTER TABLE t_alert_rules ADD COLUMN auto_process_enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用自动处理';
ALTER TABLE t_alert_rules ADD COLUMN auto_process_action ENUM('AUTO_RESOLVE', 'AUTO_ACKNOWLEDGE', 'AUTO_ESCALATE', 'AUTO_SUPPRESS') DEFAULT NULL COMMENT '自动处理动作';
ALTER TABLE t_alert_rules ADD COLUMN auto_process_delay_seconds INT DEFAULT 0 COMMENT '自动处理延迟秒数';
ALTER TABLE t_alert_rules ADD COLUMN suppress_duration_minutes INT DEFAULT 60 COMMENT '抑制持续时间(分钟)';
ALTER TABLE t_alert_rules ADD COLUMN auto_resolve_threshold_count INT DEFAULT 1 COMMENT '自动解决阈值计数';

-- ============================
-- 2. t_alert_info 表增强 - 添加自动处理跟踪字段
-- ============================

ALTER TABLE t_alert_info ADD COLUMN due_time TIMESTAMP NULL COMMENT '处理截止时间';
ALTER TABLE t_alert_info ADD COLUMN escalation_level INT DEFAULT 0 COMMENT '升级级别 (0-无升级, 1-5升级级别)';
ALTER TABLE t_alert_info ADD COLUMN auto_close_time TIMESTAMP NULL COMMENT '自动关闭时间';
ALTER TABLE t_alert_info ADD COLUMN auto_processed TINYINT(1) DEFAULT 0 COMMENT '是否自动处理';
ALTER TABLE t_alert_info ADD COLUMN auto_process_time TIMESTAMP NULL COMMENT '自动处理时间';
ALTER TABLE t_alert_info ADD COLUMN auto_process_reason TEXT NULL COMMENT '自动处理原因';
ALTER TABLE t_alert_info ADD COLUMN processing_stage ENUM('NEW', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'SUPPRESSED', 'ESCALATED') DEFAULT 'NEW' COMMENT '处理阶段';
ALTER TABLE t_alert_info ADD COLUMN assigned_to BIGINT NULL COMMENT '分配给谁(用户ID)';
ALTER TABLE t_alert_info ADD COLUMN resolution_notes TEXT NULL COMMENT '解决备注';
ALTER TABLE t_alert_info ADD COLUMN suppression_reason TEXT NULL COMMENT '抑制原因';
ALTER TABLE t_alert_info ADD COLUMN suppression_until TIMESTAMP NULL COMMENT '抑制到什么时间';
ALTER TABLE t_alert_info ADD COLUMN acknowledgment_time TIMESTAMP NULL COMMENT '确认时间';
ALTER TABLE t_alert_info ADD COLUMN acknowledgment_user BIGINT NULL COMMENT '确认人(用户ID)';

-- ============================
-- 3. 性能优化索引
-- ============================

CREATE INDEX idx_alert_priority_processing ON t_alert_info(alert_level, processing_stage, auto_processed);
CREATE INDEX idx_auto_processing ON t_alert_info(auto_processed, auto_process_time);
CREATE INDEX idx_device_alert_type ON t_alert_info(device_sn, alert_type, processing_stage);
CREATE INDEX idx_alert_escalation ON t_alert_info(escalation_level, due_time);
CREATE INDEX idx_suppression ON t_alert_info(processing_stage, suppression_until);
CREATE INDEX idx_alert_rules_auto_process ON t_alert_rules(auto_process_enabled, is_enabled);

-- ============================
-- 4. 初始化数据 - 自动处理规则样例
-- ============================

INSERT INTO t_alert_rules 
(rule_type, physical_sign, severity_level, is_enabled, auto_process_enabled, auto_process_action, auto_process_delay_seconds, suppress_duration_minutes, level, customer_id, rule_category, priority_level, create_time, update_time)
VALUES 
('metric', 'heart_rate', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'blood_oxygen', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'temperature', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW());

SELECT 'Database enhancement completed!' as status;