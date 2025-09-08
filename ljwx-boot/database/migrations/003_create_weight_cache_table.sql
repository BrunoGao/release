-- 权重缓存表 - 用于缓存每日计算的权重结果
CREATE TABLE t_weight_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    customer_id BIGINT NOT NULL COMMENT '租户ID',
    metric_name VARCHAR(50) NOT NULL COMMENT '指标名称',
    base_weight DECIMAL(8,4) NOT NULL COMMENT '基础权重(来自配置)',
    position_risk_multiplier DECIMAL(8,4) DEFAULT 1.0 COMMENT '岗位风险调整系数',
    combined_weight DECIMAL(8,4) NOT NULL COMMENT '综合权重(基础权重×风险系数)',
    normalized_weight DECIMAL(8,4) NOT NULL COMMENT '归一化权重(确保总和为1)',
    position_id BIGINT COMMENT '岗位ID',
    position_risk_level VARCHAR(20) DEFAULT 'normal' COMMENT '岗位风险等级',
    cache_date DATE NOT NULL COMMENT '缓存日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_date (user_id, cache_date),
    INDEX idx_customer_date (customer_id, cache_date),
    INDEX idx_metric_date (metric_name, cache_date),
    UNIQUE KEY uk_user_metric_date (user_id, metric_name, cache_date)
) COMMENT='权重缓存表';