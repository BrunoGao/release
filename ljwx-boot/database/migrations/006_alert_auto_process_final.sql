-- 告警自动处理功能数据库增强脚本 (最终版)
-- 只添加确实缺失的字段
-- 执行时间：2025-09-11

USE test;

-- ============================
-- 1. t_alert_rules 表增强 - 添加缺失字段
-- ============================

-- 检查缺失的字段：suppress_duration_minutes
ALTER TABLE t_alert_rules ADD COLUMN suppress_duration_minutes INT DEFAULT 60 COMMENT '抑制持续时间(分钟)';

-- ============================
-- 2. t_alert_info 表增强 - 添加所有缺失的自动处理字段
-- ============================

ALTER TABLE t_alert_info ADD COLUMN auto_close_time TIMESTAMP NULL COMMENT '自动关闭时间';
ALTER TABLE t_alert_info ADD COLUMN auto_processed TINYINT(1) DEFAULT 0 COMMENT '是否自动处理';
ALTER TABLE t_alert_info ADD COLUMN auto_process_time TIMESTAMP NULL COMMENT '自动处理时间';
ALTER TABLE t_alert_info ADD COLUMN auto_process_reason TEXT NULL COMMENT '自动处理原因';
ALTER TABLE t_alert_info ADD COLUMN processing_stage ENUM('NEW', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'SUPPRESSED', 'ESCALATED') DEFAULT 'NEW' COMMENT '处理阶段';
ALTER TABLE t_alert_info ADD COLUMN resolution_notes TEXT NULL COMMENT '解决备注';
ALTER TABLE t_alert_info ADD COLUMN suppression_reason TEXT NULL COMMENT '抑制原因';
ALTER TABLE t_alert_info ADD COLUMN suppression_until TIMESTAMP NULL COMMENT '抑制到什么时间';
ALTER TABLE t_alert_info ADD COLUMN acknowledgment_time TIMESTAMP NULL COMMENT '确认时间';
ALTER TABLE t_alert_info ADD COLUMN acknowledgment_user BIGINT NULL COMMENT '确认人(用户ID)';
ALTER TABLE t_alert_info ADD COLUMN priority INT DEFAULT 3 COMMENT '告警优先级 (1-10, 1最高)';

-- ============================
-- 3. 性能优化索引
-- ============================

CREATE INDEX idx_alert_priority_processing ON t_alert_info(priority, processing_stage, auto_processed);
CREATE INDEX idx_auto_processing ON t_alert_info(auto_processed, auto_process_time);
CREATE INDEX idx_device_alert_type ON t_alert_info(device_sn, alert_type, processing_stage);
CREATE INDEX idx_alert_escalation ON t_alert_info(escalation_level, due_time);
CREATE INDEX idx_suppression ON t_alert_info(processing_stage, suppression_until);
CREATE INDEX idx_alert_rules_auto_process ON t_alert_rules(auto_process_enabled, is_enabled);

-- ============================
-- 4. 初始化数据 - 自动处理规则样例 (如果不存在)
-- ============================

INSERT IGNORE INTO t_alert_rules 
(rule_type, physical_sign, severity_level, is_enabled, auto_process_enabled, auto_process_action, auto_process_delay_seconds, suppress_duration_minutes, level, customer_id, rule_category, priority_level, create_time, update_time)
VALUES 
('metric', 'heart_rate', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'blood_oxygen', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'temperature', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW());

SELECT 'Database auto-processing enhancement completed successfully!' as status;