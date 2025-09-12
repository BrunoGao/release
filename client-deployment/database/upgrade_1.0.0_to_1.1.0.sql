-- 数据库升级脚本: 1.0.0 -> 1.1.0
-- 执行时间：2025-09-11
-- 描述：添加告警自动处理功能和性能优化

USE test;

-- ============================
-- 1. 告警规则表增强
-- ============================

-- 添加自动处理相关字段到告警规则表
ALTER TABLE t_alert_rules 
ADD COLUMN IF NOT EXISTS auto_process_enabled TINYINT(1) DEFAULT 0 COMMENT '是否启用自动处理',
ADD COLUMN IF NOT EXISTS auto_process_action ENUM('AUTO_RESOLVE', 'AUTO_ACKNOWLEDGE', 'AUTO_ESCALATE', 'AUTO_SUPPRESS') DEFAULT NULL COMMENT '自动处理动作',
ADD COLUMN IF NOT EXISTS auto_process_delay_seconds INT DEFAULT 0 COMMENT '自动处理延迟秒数',
ADD COLUMN IF NOT EXISTS suppress_duration_minutes INT DEFAULT 60 COMMENT '抑制持续时间(分钟)',
ADD COLUMN IF NOT EXISTS auto_resolve_threshold_count INT DEFAULT 1 COMMENT '自动解决阈值计数';

-- ============================
-- 2. 告警信息表增强
-- ============================

-- 添加告警处理跟踪字段到告警信息表
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

-- 时间范围查询优化索引
CREATE INDEX IF NOT EXISTS idx_alert_time_range ON t_alert_info(create_time, alert_level);

-- 用户告警查询索引
CREATE INDEX IF NOT EXISTS idx_user_alerts ON t_alert_info(user_id, create_time);

-- ============================
-- 4. 权重缓存表 (如果不存在)
-- ============================

CREATE TABLE IF NOT EXISTS t_weight_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    customer_id BIGINT NOT NULL DEFAULT 0 COMMENT '客户ID',
    user_id BIGINT NULL COMMENT '用户ID，NULL表示系统默认权重',
    feature_type VARCHAR(50) NOT NULL COMMENT '健康特征类型',
    weight_value DECIMAL(10,6) NOT NULL COMMENT '权重值',
    risk_multiplier DECIMAL(10,6) DEFAULT 1.0 COMMENT '风险倍数',
    normalized_weight DECIMAL(10,6) NOT NULL COMMENT '归一化权重',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否生效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_weight_cache_user_feature (customer_id, user_id, feature_type),
    INDEX idx_weight_cache_customer (customer_id, is_active),
    INDEX idx_weight_cache_user (user_id, is_active),
    INDEX idx_weight_cache_feature (feature_type, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权重配置缓存表';

-- ============================
-- 5. 初始化默认数据
-- ============================

-- 插入标准权重配置（基于医学重要性）
INSERT IGNORE INTO t_weight_cache (customer_id, user_id, feature_type, weight_value, normalized_weight) VALUES
-- 核心生命体征 (65%)
(0, NULL, 'heart_rate', 0.20, 0.20),      -- 心率: 20%
(0, NULL, 'blood_oxygen', 0.18, 0.18),    -- 血氧: 18%
(0, NULL, 'temperature', 0.15, 0.15),     -- 体温: 15%
(0, NULL, 'pressure_high', 0.06, 0.06),   -- 收缩压: 6%
(0, NULL, 'pressure_low', 0.06, 0.06),    -- 舒张压: 6%

-- 健康状态指标 (20%)
(0, NULL, 'stress', 0.12, 0.12),          -- 压力指数: 12%
(0, NULL, 'sleep', 0.08, 0.08),           -- 睡眠质量: 8%

-- 运动健康指标 (10%)
(0, NULL, 'step', 0.04, 0.04),            -- 步数: 4%
(0, NULL, 'distance', 0.03, 0.03),        -- 距离: 3%
(0, NULL, 'calorie', 0.03, 0.03),         -- 卡路里: 3%

-- 辅助指标 (5%)
(0, NULL, 'ecg', 0.02, 0.02),             -- 心电图: 2%
(0, NULL, 'position', 0.01, 0.01),        -- 位置: 1%
(0, NULL, 'exercise', 0.01, 0.01),        -- 锻炼: 1%
(0, NULL, 'other', 0.01, 0.01);           -- 其他: 1%

-- 插入示例自动处理规则
INSERT IGNORE INTO t_alert_rules 
(rule_type, physical_sign, severity_level, is_enabled, auto_process_enabled, auto_process_action, auto_process_delay_seconds, suppress_duration_minutes, level, customer_id, rule_category, priority_level, create_time, update_time)
VALUES 
('metric', 'heart_rate', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'blood_oxygen', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW()),
('metric', 'temperature', 'minor', 1, 1, 'AUTO_ACKNOWLEDGE', 30, 60, 'minor', 0, 'SINGLE', 3, NOW(), NOW());

-- ============================
-- 6. 数据清理和优化
-- ============================

-- 清理重复的告警规则（如果存在）
DELETE t1 FROM t_alert_rules t1
INNER JOIN t_alert_rules t2 
WHERE t1.id > t2.id 
  AND t1.rule_type = t2.rule_type 
  AND t1.physical_sign = t2.physical_sign 
  AND t1.severity_level = t2.severity_level 
  AND t1.customer_id = t2.customer_id;

-- 更新现有告警的处理阶段
UPDATE t_alert_info 
SET processing_stage = CASE 
    WHEN status = 'resolved' THEN 'RESOLVED'
    WHEN status = 'acknowledged' THEN 'ACKNOWLEDGED' 
    ELSE 'NEW'
END
WHERE processing_stage IS NULL OR processing_stage = 'NEW';

-- 分析表以优化查询性能
ANALYZE TABLE t_alert_rules, t_alert_info, t_weight_cache;

-- 升级完成标记
SELECT '数据库升级到 1.1.0 版本完成！' AS status;