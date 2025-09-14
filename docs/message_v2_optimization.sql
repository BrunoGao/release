-- ====================================================================
-- 消息系统V2优化 - 基于user_id查询的表结构优化
-- ====================================================================

-- 1. 添加缺失字段到 t_device_message_v2
-- ====================================================================

ALTER TABLE t_device_message_v2 
ADD COLUMN priority_level INTEGER DEFAULT 3 COMMENT '优先级数值1-5' AFTER urgency,
ADD COLUMN channels JSON COMMENT '分发渠道JSON ["message","push","wechat","watch"]' AFTER message_status,
ADD COLUMN require_ack BOOLEAN DEFAULT false COMMENT '是否需要确认' AFTER channels,
ADD COLUMN metadata JSON COMMENT '扩展元数据JSON' AFTER require_ack,
ADD COLUMN target_count INTEGER DEFAULT 0 COMMENT '目标用户总数' AFTER responded_number,
ADD COLUMN version INTEGER DEFAULT 1 COMMENT '乐观锁版本号' AFTER update_user;

-- 2. 添加缺失字段到 t_device_message_detail_v2  
-- ====================================================================

ALTER TABLE t_device_message_detail_v2
ADD COLUMN distribution_id VARCHAR(64) NOT NULL COMMENT '分发唯一ID' AFTER customer_id,
ADD COLUMN device_sn VARCHAR(128) COMMENT '设备序列号' AFTER target_type,
ADD COLUMN user_id VARCHAR(64) COMMENT '用户ID - 主要查询字段' AFTER device_sn,
ADD COLUMN response_duration INTEGER COMMENT '响应耗时(秒)' AFTER acknowledged_time,
ADD COLUMN delivery_details JSON COMMENT '分发详情JSON' AFTER response_data,
ADD COLUMN client_info JSON COMMENT '客户端信息JSON' AFTER delivery_details,
ADD COLUMN location_info JSON COMMENT '位置信息JSON' AFTER client_info,
ADD COLUMN last_retry_time DATETIME COMMENT '最后重试时间' AFTER retry_count;

-- 3. 删除旧的device_sn相关索引，创建基于user_id的优化索引
-- ====================================================================

-- 删除现有的device_sn索引
DROP INDEX idx_user_device ON t_device_message_v2;

-- 创建基于user_id的高性能复合索引
CREATE INDEX idx_customer_user_time ON t_device_message_v2 (customer_id, user_id, create_time DESC, is_deleted);
CREATE INDEX idx_customer_user_status ON t_device_message_v2 (customer_id, user_id, message_status, is_deleted);
CREATE INDEX idx_customer_user_type ON t_device_message_v2 (customer_id, user_id, message_type, is_deleted);
CREATE INDEX idx_user_org_priority ON t_device_message_v2 (user_id, org_id, priority_level, urgency);
CREATE INDEX idx_user_status_time ON t_device_message_v2 (user_id, message_status, create_time DESC);

-- 4. 优化 t_device_message_detail_v2 的索引
-- ====================================================================

-- 添加基于user_id的核心查询索引
CREATE UNIQUE INDEX uk_message_user_target ON t_device_message_detail_v2 (message_id, user_id, target_id);
CREATE INDEX idx_customer_user_status ON t_device_message_detail_v2 (customer_id, user_id, delivery_status);
CREATE INDEX idx_user_channel_time ON t_device_message_detail_v2 (user_id, channel, create_time DESC);
CREATE INDEX idx_user_delivery_status ON t_device_message_detail_v2 (user_id, delivery_status, acknowledged_time);

-- 5. 创建消息生命周期跟踪表
-- ====================================================================

CREATE TABLE IF NOT EXISTS t_message_lifecycle_v2 (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    message_id BIGINT NOT NULL COMMENT '消息ID',
    customer_id BIGINT NOT NULL COMMENT '租户ID',
    user_id VARCHAR(64) COMMENT '操作用户ID',
    event_type ENUM('created','published','distributed','delivered','acknowledged','failed','expired','cancelled') NOT NULL COMMENT '事件类型',
    event_data JSON COMMENT '事件数据JSON',
    operator_id VARCHAR(64) COMMENT '操作者ID',
    operator_type ENUM('system','user','admin','device') NOT NULL COMMENT '操作者类型',
    platform_source ENUM('ljwx-admin','ljwx-bigscreen','ljwx-boot','ljwx-phone','ljwx-watch') NOT NULL COMMENT '平台来源',
    event_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '事件时间',
    duration_ms INTEGER COMMENT '事件耗时(毫秒)',
    
    PRIMARY KEY (id),
    KEY idx_message_event_time (message_id, event_time),
    KEY idx_customer_user_event (customer_id, user_id, event_type, event_time),
    KEY idx_platform_time (platform_source, event_time),
    
    CONSTRAINT fk_lifecycle_message FOREIGN KEY (message_id) REFERENCES t_device_message_v2(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息生命周期跟踪表V2';

-- 6. 基于user_id的常用查询视图
-- ====================================================================

CREATE OR REPLACE VIEW v_user_messages_summary AS
SELECT 
    m.user_id,
    m.customer_id,
    m.org_id,
    COUNT(*) as total_messages,
    SUM(CASE WHEN m.message_status = 'PENDING' THEN 1 ELSE 0 END) as pending_count,
    SUM(CASE WHEN m.message_status = 'DELIVERED' THEN 1 ELSE 0 END) as delivered_count,
    SUM(CASE WHEN m.message_status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as acknowledged_count,
    SUM(CASE WHEN m.message_status = 'FAILED' THEN 1 ELSE 0 END) as failed_count,
    SUM(CASE WHEN m.message_status = 'EXPIRED' THEN 1 ELSE 0 END) as expired_count,
    
    -- 按优先级统计
    SUM(CASE WHEN m.priority_level = 5 THEN 1 ELSE 0 END) as critical_count,
    SUM(CASE WHEN m.priority_level = 4 THEN 1 ELSE 0 END) as high_count,
    SUM(CASE WHEN m.priority_level = 3 THEN 1 ELSE 0 END) as medium_count,
    SUM(CASE WHEN m.priority_level <= 2 THEN 1 ELSE 0 END) as low_count,
    
    -- 按紧急程度统计
    SUM(CASE WHEN m.urgency = 'CRITICAL' THEN 1 ELSE 0 END) as urgent_critical,
    SUM(CASE WHEN m.urgency = 'HIGH' THEN 1 ELSE 0 END) as urgent_high,
    SUM(CASE WHEN m.urgency = 'MEDIUM' THEN 1 ELSE 0 END) as urgent_medium,
    SUM(CASE WHEN m.urgency = 'LOW' THEN 1 ELSE 0 END) as urgent_low,
    
    -- 时间统计
    MAX(m.create_time) as latest_message_time,
    MIN(m.create_time) as earliest_message_time,
    
    -- 完成率计算
    ROUND(
        SUM(CASE WHEN m.message_status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) as completion_rate
    
FROM t_device_message_v2 m
WHERE m.is_deleted = 0 
  AND m.user_id IS NOT NULL
GROUP BY m.user_id, m.customer_id, m.org_id;

-- 7. 用户消息详情视图（用于快速查询确认状态）
-- ====================================================================

CREATE OR REPLACE VIEW v_user_message_details AS
SELECT 
    m.id as message_id,
    m.user_id,
    m.customer_id,
    m.org_id,
    m.title,
    m.message,
    m.message_type,
    m.urgency,
    m.priority_level,
    m.message_status,
    m.create_time,
    m.sent_time,
    m.acknowledged_time,
    m.target_count,
    m.responded_number,
    
    -- 详情统计
    COUNT(d.id) as total_targets,
    SUM(CASE WHEN d.delivery_status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as acknowledged_targets,
    SUM(CASE WHEN d.delivery_status = 'DELIVERED' THEN 1 ELSE 0 END) as delivered_targets,
    SUM(CASE WHEN d.delivery_status = 'PENDING' THEN 1 ELSE 0 END) as pending_targets,
    SUM(CASE WHEN d.delivery_status = 'FAILED' THEN 1 ELSE 0 END) as failed_targets,
    
    -- 平均响应时间
    AVG(d.response_duration) as avg_response_time,
    
    -- 完成率
    ROUND(
        SUM(CASE WHEN d.delivery_status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) * 100.0 / COUNT(d.id), 
        2
    ) as completion_rate

FROM t_device_message_v2 m
LEFT JOIN t_device_message_detail_v2 d ON m.id = d.message_id AND d.is_deleted = 0
WHERE m.is_deleted = 0 
  AND m.user_id IS NOT NULL
GROUP BY m.id, m.user_id, m.customer_id, m.org_id, m.title, m.message, 
         m.message_type, m.urgency, m.priority_level, m.message_status, 
         m.create_time, m.sent_time, m.acknowledged_time, m.target_count, m.responded_number;

-- 8. 性能优化建议的存储过程
-- ====================================================================

DELIMITER $$

CREATE PROCEDURE GetUserMessages(
    IN p_user_id VARCHAR(64),
    IN p_customer_id BIGINT,
    IN p_message_status VARCHAR(50),
    IN p_page_size INT DEFAULT 20,
    IN p_page_offset INT DEFAULT 0
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    -- 利用索引：idx_customer_user_status
    SELECT 
        m.id,
        m.message_id,
        m.title,
        m.message,
        m.message_type,
        m.urgency,
        m.priority_level,
        m.message_status,
        m.create_time,
        m.sent_time,
        m.acknowledged_time,
        m.target_count,
        m.responded_number,
        m.channels,
        m.require_ack,
        m.metadata
    FROM t_device_message_v2 m
    WHERE m.customer_id = p_customer_id
      AND m.user_id = p_user_id
      AND (p_message_status IS NULL OR m.message_status = p_message_status)
      AND m.is_deleted = 0
    ORDER BY m.priority_level DESC, m.create_time DESC
    LIMIT p_page_size OFFSET p_page_offset;
    
END$$

CREATE PROCEDURE GetUserMessageAcknowledgments(
    IN p_user_id VARCHAR(64),
    IN p_message_id BIGINT,
    IN p_customer_id BIGINT
)
BEGIN
    -- 利用索引：idx_customer_user_status
    SELECT 
        d.id,
        d.target_id,
        d.target_type,
        d.channel,
        d.delivery_status,
        d.sent_time,
        d.delivered_time,
        d.acknowledged_time,
        d.response_duration,
        d.failure_reason,
        d.retry_count,
        d.delivery_details,
        d.client_info
    FROM t_device_message_detail_v2 d
    WHERE d.customer_id = p_customer_id
      AND d.user_id = p_user_id
      AND (p_message_id IS NULL OR d.message_id = p_message_id)
      AND d.is_deleted = 0
    ORDER BY d.acknowledged_time DESC, d.create_time DESC;
    
END$$

DELIMITER ;

-- 9. 数据迁移脚本（如果需要从旧版本迁移）
-- ====================================================================

-- 更新现有记录的分发ID
UPDATE t_device_message_detail_v2 
SET distribution_id = CONCAT('dist_', message_id, '_', target_id, '_', UNIX_TIMESTAMP(create_time))
WHERE distribution_id IS NULL OR distribution_id = '';

-- 更新优先级数值（从枚举转换）
UPDATE t_device_message_v2 
SET priority_level = CASE 
    WHEN urgency = 'CRITICAL' THEN 5
    WHEN urgency = 'HIGH' THEN 4  
    WHEN urgency = 'MEDIUM' THEN 3
    WHEN urgency = 'LOW' THEN 2
    ELSE 3
END
WHERE priority_level IS NULL;

-- 初始化默认渠道
UPDATE t_device_message_v2 
SET channels = JSON_ARRAY('DEVICE')
WHERE channels IS NULL;

-- 10. 验证和测试查询
-- ====================================================================

-- 测试基于user_id的查询性能
EXPLAIN SELECT * FROM t_device_message_v2 
WHERE customer_id = 1 AND user_id = 'user123' AND message_status = 'PENDING' 
ORDER BY create_time DESC LIMIT 10;

-- 测试用户消息详情查询
EXPLAIN SELECT * FROM v_user_message_details 
WHERE user_id = 'user123' AND customer_id = 1 
ORDER BY create_time DESC LIMIT 10;

-- 测试消息确认状态查询  
EXPLAIN SELECT * FROM t_device_message_detail_v2
WHERE customer_id = 1 AND user_id = 'user123' AND delivery_status = 'ACKNOWLEDGED'
ORDER BY acknowledged_time DESC;

-- ====================================================================
-- 执行完成后的验证脚本
-- ====================================================================

-- 检查新增字段
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE, 
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'test' 
  AND TABLE_NAME IN ('t_device_message_v2', 't_device_message_detail_v2')
  AND COLUMN_NAME IN ('priority_level', 'channels', 'require_ack', 'metadata', 'target_count', 'version',
                      'distribution_id', 'device_sn', 'user_id', 'response_duration', 'delivery_details',
                      'client_info', 'location_info', 'last_retry_time')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 检查新增索引
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS,
    NON_UNIQUE,
    INDEX_TYPE
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'test' 
  AND TABLE_NAME IN ('t_device_message_v2', 't_device_message_detail_v2')
  AND INDEX_NAME LIKE 'idx_%user%'
GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE, INDEX_TYPE
ORDER BY TABLE_NAME, INDEX_NAME;

-- ====================================================================
-- 使用说明
-- ====================================================================

/*
核心优化点：

1. 索引优化：
   - 所有查询索引都以user_id为核心
   - 复合索引顺序：customer_id -> user_id -> 其他条件
   - 支持按用户快速查询消息和确认状态

2. 查询模式：
   - 主查询：按user_id获取用户消息列表
   - 详情查询：按user_id + message_id获取确认详情
   - 统计查询：按user_id获取消息统计和完成率

3. 性能提升：
   - 所有user_id相关查询都能使用索引
   - 视图预计算常用统计指标
   - 存储过程封装高频查询逻辑

4. 数据完整性：
   - 外键约束保证数据一致性
   - 唯一索引防止重复分发记录
   - 枚举类型确保状态值规范
*/