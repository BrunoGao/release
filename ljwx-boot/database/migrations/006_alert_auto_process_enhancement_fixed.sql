-- 告警自动处理功能数据库增强脚本 (修复版)
-- 执行时间：2025-09-11
-- 版本：v1.1 - 修复重复字段问题

USE test;

-- ============================
-- 1. t_alert_rules 表增强 - 添加自动处理字段
-- ============================

-- 检查并添加自动处理相关字段
ALTER TABLE t_alert_rules 
ADD COLUMN IF NOT EXISTS auto_process_enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用自动处理',
ADD COLUMN IF NOT EXISTS auto_process_action ENUM('AUTO_RESOLVE', 'AUTO_ACKNOWLEDGE', 'AUTO_ESCALATE', 'AUTO_SUPPRESS') DEFAULT NULL COMMENT '自动处理动作',
ADD COLUMN IF NOT EXISTS auto_process_delay_seconds INT DEFAULT 0 COMMENT '自动处理延迟秒数',
ADD COLUMN IF NOT EXISTS suppress_duration_minutes INT DEFAULT 60 COMMENT '抑制持续时间(分钟)',
ADD COLUMN IF NOT EXISTS auto_resolve_threshold_count INT DEFAULT 1 COMMENT '自动解决阈值计数';

-- ============================
-- 2. t_alert_info 表增强 - 添加自动处理跟踪字段
-- ============================

-- 检查并添加告警处理跟踪字段
ALTER TABLE t_alert_info 
ADD COLUMN IF NOT EXISTS priority INT DEFAULT 3 COMMENT '告警优先级 (1-10, 1最高)',
ADD COLUMN IF NOT EXISTS due_time TIMESTAMP NULL COMMENT '处理截止时间',
ADD COLUMN IF NOT EXISTS escalation_level INT DEFAULT 0 COMMENT '升级级别 (0-无升级, 1-5升级级别)',
ADD COLUMN IF NOT EXISTS auto_close_time TIMESTAMP NULL COMMENT '自动关闭时间',
ADD COLUMN IF NOT EXISTS auto_processed TINYINT(1) DEFAULT 0 COMMENT '是否自动处理',
ADD COLUMN IF NOT EXISTS auto_process_time TIMESTAMP NULL COMMENT '自动处理时间',
ADD COLUMN IF NOT EXISTS auto_process_reason TEXT NULL COMMENT '自动处理原因',
ADD COLUMN IF NOT EXISTS processing_stage ENUM('NEW', 'ACKNOWLEDGED', 'IN_PROGRESS', 'RESOLVED', 'SUPPRESSED', 'ESCALATED') DEFAULT 'NEW' COMMENT '处理阶段',
ADD COLUMN IF NOT EXISTS assigned_to BIGINT NULL COMMENT '分配给谁(用户ID)',
ADD COLUMN IF NOT EXISTS resolution_notes TEXT NULL COMMENT '解决备注',
ADD COLUMN IF NOT EXISTS suppression_reason TEXT NULL COMMENT '抑制原因',
ADD COLUMN IF NOT EXISTS suppression_until TIMESTAMP NULL COMMENT '抑制到什么时间',
ADD COLUMN IF NOT EXISTS acknowledgment_time TIMESTAMP NULL COMMENT '确认时间',
ADD COLUMN IF NOT EXISTS acknowledgment_user BIGINT NULL COMMENT '确认人(用户ID)';

-- ============================
-- 3. 性能优化索引
-- ============================

-- 告警优先级和处理状态索引
CREATE INDEX IF NOT EXISTS idx_alert_priority_processing ON t_alert_info(priority, processing_stage, auto_processed);

-- 自动处理相关索引
CREATE INDEX IF NOT EXISTS idx_auto_processing ON t_alert_info(auto_processed, auto_process_time);

-- 设备告警类型索引
CREATE INDEX IF NOT EXISTS idx_device_alert_type ON t_alert_info(device_sn, alert_type, processing_stage);

-- 告警升级索引
CREATE INDEX IF NOT EXISTS idx_alert_escalation ON t_alert_info(escalation_level, due_time);

-- 告警抑制索引  
CREATE INDEX IF NOT EXISTS idx_suppression ON t_alert_info(processing_stage, suppression_until);

-- 自动处理规则索引
CREATE INDEX IF NOT EXISTS idx_alert_rules_auto_process ON t_alert_rules(auto_process_enabled, is_enabled);

-- ============================
-- 4. 初始化数据 - 自动处理规则样例
-- ============================

-- 插入示例自动处理规则 (minor级别告警自动确认)
INSERT IGNORE INTO t_alert_rules 
(rule_type, physical_sign, severity_level, is_enabled, auto_process_enabled, auto_process_action, auto_process_delay_seconds, suppress_duration_minutes, level, customer_id, rule_category, priority_level, create_time, update_time)
VALUES 
('metric', 'heart_rate', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'blood_oxygen', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'temperature', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW());

-- ============================
-- 5. 验证脚本执行结果
-- ============================

-- 检查t_alert_rules表新增字段
SELECT 't_alert_rules表字段检查:' as info;
SHOW COLUMNS FROM t_alert_rules LIKE '%auto%';

-- 检查t_alert_info表新增字段  
SELECT 't_alert_info表字段检查:' as info;
SHOW COLUMNS FROM t_alert_info LIKE '%auto%';
SHOW COLUMNS FROM t_alert_info LIKE '%process%';
SHOW COLUMNS FROM t_alert_info LIKE '%priority%';

-- 检查索引创建情况
SELECT '索引检查:' as info;
SHOW INDEX FROM t_alert_info WHERE Key_name LIKE 'idx_%';
SHOW INDEX FROM t_alert_rules WHERE Key_name LIKE 'idx_%';

-- 检查初始数据
SELECT '自动处理规则数据:' as info;
SELECT id, rule_type, physical_sign, severity_level, auto_process_enabled, auto_process_action FROM t_alert_rules WHERE auto_process_enabled = 1;

SELECT '数据库增强完成!' as status;