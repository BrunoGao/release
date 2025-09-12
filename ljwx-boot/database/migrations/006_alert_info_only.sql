-- 告警自动处理功能数据库增强脚本 - 只处理 t_alert_info
-- 执行时间：2025-09-11

USE test;

-- ============================
-- t_alert_info 表增强 - 添加自动处理字段
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
-- 性能优化索引
-- ============================

CREATE INDEX idx_alert_priority_processing ON t_alert_info(priority, processing_stage, auto_processed);
CREATE INDEX idx_auto_processing ON t_alert_info(auto_processed, auto_process_time);
CREATE INDEX idx_device_alert_type ON t_alert_info(device_sn, alert_type, processing_stage);
CREATE INDEX idx_alert_escalation ON t_alert_info(escalation_level, due_time);
CREATE INDEX idx_suppression ON t_alert_info(processing_stage, suppression_until);
CREATE INDEX idx_alert_rules_auto_process ON t_alert_rules(auto_process_enabled, is_enabled);

SELECT 'Database t_alert_info enhancement completed!' as status;