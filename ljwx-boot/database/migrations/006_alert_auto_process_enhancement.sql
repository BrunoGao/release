-- 灵境万象告警系统自动处理功能数据库升级脚本
-- 执行时间：阶段一 数据库架构升级
-- 说明：为现有告警表添加自动处理相关字段

USE ljwx;

-- =====================================
-- 1. t_alert_info表结构增强
-- =====================================
ALTER TABLE t_alert_info
ADD COLUMN priority TINYINT DEFAULT 5 COMMENT '优先级(1-10, 1最高)',
ADD COLUMN due_time DATETIME COMMENT '处理截止时间',
ADD COLUMN escalation_level TINYINT DEFAULT 0 COMMENT '升级级别(0-3)',
ADD COLUMN auto_close_time DATETIME COMMENT '自动关闭时间',
ADD COLUMN trigger_conditions JSON COMMENT '触发条件详情',
ADD COLUMN evaluation_context JSON COMMENT '评估上下文',
ADD COLUMN suppression_key VARCHAR(128) COMMENT '抑制键',
ADD COLUMN ack_required BOOLEAN DEFAULT FALSE COMMENT '是否需要确认',
ADD COLUMN auto_resolve BOOLEAN DEFAULT FALSE COMMENT '是否自动恢复',
ADD COLUMN auto_processed BOOLEAN DEFAULT FALSE COMMENT '是否自动处理',
ADD COLUMN auto_process_rule_id BIGINT COMMENT '自动处理规则ID',
ADD COLUMN auto_process_time DATETIME COMMENT '自动处理时间',
ADD COLUMN auto_process_reason VARCHAR(500) COMMENT '自动处理原因',
ADD COLUMN processing_stage ENUM('PENDING', 'EVALUATING', 'AUTO_PROCESSING', 'MANUAL_REVIEW', 'RESOLVED', 'CLOSED') DEFAULT 'PENDING' COMMENT '处理阶段';

-- =====================================
-- 2. t_alert_rules表结构完善
-- =====================================
ALTER TABLE t_alert_rules 
ADD COLUMN auto_process_enabled BOOLEAN DEFAULT FALSE COMMENT '启用自动处理',
ADD COLUMN auto_process_action ENUM('AUTO_RESOLVE', 'AUTO_ACKNOWLEDGE', 'AUTO_ESCALATE', 'AUTO_SUPPRESS') COMMENT '自动处理动作',
ADD COLUMN auto_process_delay_seconds INT DEFAULT 0 COMMENT '自动处理延迟秒数',
ADD COLUMN auto_resolve_threshold_count INT DEFAULT 1 COMMENT '自动恢复阈值次数',
ADD COLUMN suppress_duration_minutes INT DEFAULT 60 COMMENT '抑制持续时间(分钟)';

-- =====================================
-- 3. 性能优化索引
-- =====================================

-- 告警优先级和处理状态索引
CREATE INDEX idx_alert_priority_processing ON t_alert_info(customer_id, priority, alert_status, due_time);

-- 告警升级索引
CREATE INDEX idx_alert_escalation ON t_alert_info(customer_id, escalation_level, alert_timestamp);

-- 告警抑制索引
CREATE INDEX idx_suppression ON t_alert_info(suppression_key);

-- 自动处理索引
CREATE INDEX idx_auto_processing ON t_alert_info(customer_id, processing_stage, auto_processed);

-- 自动处理时间索引
CREATE INDEX idx_auto_process_time ON t_alert_info(auto_process_time);

-- 设备和告警类型组合索引（用于查询同类告警）
CREATE INDEX idx_device_alert_type ON t_alert_info(device_sn, alert_type, alert_timestamp);

-- 用户和告警状态索引
CREATE INDEX idx_user_alert_status ON t_alert_info(user_id, alert_status, alert_timestamp);

-- 告警规则自动处理索引
CREATE INDEX idx_rules_auto_process ON t_alert_rules(customer_id, auto_process_enabled, is_enabled);

-- =====================================
-- 4. 数据初始化
-- =====================================

-- 为现有告警设置默认优先级（基于严重程度）
UPDATE t_alert_info SET 
    priority = CASE 
        WHEN severity_level = 'critical' THEN 1
        WHEN severity_level = 'major' THEN 3
        WHEN severity_level = 'minor' THEN 5
        WHEN severity_level = 'info' THEN 7
        ELSE 5
    END
WHERE priority IS NULL;

-- 为现有告警设置处理阶段
UPDATE t_alert_info SET 
    processing_stage = CASE 
        WHEN alert_status = 'resolved' THEN 'RESOLVED'
        WHEN alert_status = 'closed' THEN 'CLOSED'
        WHEN alert_status = 'acknowledged' THEN 'MANUAL_REVIEW'
        ELSE 'PENDING'
    END
WHERE processing_stage IS NULL;

-- =====================================
-- 5. 创建示例自动处理规则
-- =====================================

-- 设备离线自动确认规则
UPDATE t_alert_rules SET 
    auto_process_enabled = TRUE,
    auto_process_action = 'AUTO_ACKNOWLEDGE',
    auto_process_delay_seconds = 30,
    suppress_duration_minutes = 120
WHERE alert_type = 'device_offline' AND severity_level IN ('minor', 'info');

-- 电量不足自动抑制规则  
UPDATE t_alert_rules SET 
    auto_process_enabled = TRUE,
    auto_process_action = 'AUTO_SUPPRESS',
    auto_process_delay_seconds = 0,
    suppress_duration_minutes = 60
WHERE alert_type = 'battery_low' AND severity_level = 'info';

-- 心率异常轻微告警自动解决规则
UPDATE t_alert_rules SET 
    auto_process_enabled = TRUE,
    auto_process_action = 'AUTO_RESOLVE',
    auto_process_delay_seconds = 60,
    auto_resolve_threshold_count = 3
WHERE alert_type = 'heart_rate_abnormal' AND severity_level = 'minor';

-- =====================================
-- 6. 验证脚本
-- =====================================

-- 验证表结构
SELECT 
    TABLE_NAME,
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'ljwx' 
    AND TABLE_NAME IN ('t_alert_info', 't_alert_rules')
    AND COLUMN_NAME LIKE '%auto%'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 验证索引
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLUMNS
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'ljwx' 
    AND TABLE_NAME IN ('t_alert_info', 't_alert_rules')
    AND INDEX_NAME LIKE 'idx_%'
GROUP BY TABLE_NAME, INDEX_NAME;

-- 验证自动处理规则配置
SELECT 
    id,
    alert_type,
    severity_level,
    auto_process_enabled,
    auto_process_action,
    auto_process_delay_seconds,
    suppress_duration_minutes
FROM t_alert_rules 
WHERE auto_process_enabled = TRUE;

-- 验证数据更新结果
SELECT 
    processing_stage,
    COUNT(*) as count
FROM t_alert_info 
GROUP BY processing_stage;

SELECT 
    priority,
    COUNT(*) as count
FROM t_alert_info 
GROUP BY priority 
ORDER BY priority;

-- =====================================
-- 完成提示
-- =====================================
SELECT '数据库架构升级完成！' AS status,
       'PHASE_1_COMPLETED' AS phase,
       NOW() AS completion_time;