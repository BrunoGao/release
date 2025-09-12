-- 修复健康数据表结构，添加缺失字段
-- 执行时间：2025-09-12

USE test;

-- ============================
-- 1. 修复 t_health_baseline 表 - 添加 is_deleted 字段
-- ============================

ALTER TABLE t_health_baseline 
ADD COLUMN is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除 0-正常 1-删除';

-- 为 is_deleted 字段创建索引
CREATE INDEX idx_health_baseline_deleted ON t_health_baseline(is_deleted);

-- ============================
-- 2. 修复 t_health_score 表 - 添加缺失字段
-- ============================

-- 添加 is_deleted 字段
ALTER TABLE t_health_score 
ADD COLUMN is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除 0-正常 1-删除';

-- 添加 score_level 字段
ALTER TABLE t_health_score 
ADD COLUMN score_level VARCHAR(20) DEFAULT 'fair' COMMENT '评分等级 excellent/good/fair/poor';

-- 添加 raw_value 字段
ALTER TABLE t_health_score 
ADD COLUMN raw_value DECIMAL(10,2) DEFAULT 0.00 COMMENT '原始值';

-- 添加 baseline_value 字段  
ALTER TABLE t_health_score 
ADD COLUMN baseline_value DECIMAL(10,2) DEFAULT 0.00 COMMENT '基线值';

-- 为 is_deleted 字段创建索引
CREATE INDEX idx_health_score_deleted ON t_health_score(is_deleted);

-- ============================
-- 3. 确保 t_health_prediction 表存在且结构正确
-- ============================

CREATE TABLE IF NOT EXISTS t_health_prediction (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL COMMENT '用户ID',
    customer_id BIGINT NOT NULL DEFAULT 0 COMMENT '客户ID',
    device_sn VARCHAR(50) NULL COMMENT '设备序列号',
    org_id BIGINT NULL COMMENT '组织ID',
    prediction_type VARCHAR(50) NULL COMMENT '预测类型 (trend, risk, anomaly)',
    feature_name VARCHAR(50) NULL COMMENT '健康特征名称',
    prediction_date DATE NULL COMMENT '预测日期',
    predicted_value DECIMAL(10,2) NULL COMMENT '预测值',
    confidence_score DECIMAL(5,4) NULL COMMENT '置信度 (0-1)',
    risk_level VARCHAR(20) NULL COMMENT '风险等级 (low, medium, high)',
    model_version VARCHAR(50) NULL COMMENT '预测模型版本',
    accuracy_rate DECIMAL(5,4) NULL COMMENT '预测准确率',
    description TEXT NULL COMMENT '预测描述',
    metadata TEXT NULL COMMENT '预测元数据 (JSON格式)',
    is_valid BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    valid_until TIMESTAMP NULL COMMENT '预测有效期至',
    model_type VARCHAR(50) NULL COMMENT '模型类型',
    prediction_start_date DATE NULL COMMENT '预测开始日期',
    prediction_end_date DATE NULL COMMENT '预测结束日期',
    prediction_horizon_days INT NULL COMMENT '预测周期天数',
    prediction_status VARCHAR(20) DEFAULT 'pending' COMMENT '预测状态 (pending, completed, failed)',
    created_by VARCHAR(50) NULL COMMENT '创建人',
    prediction_details TEXT NULL COMMENT '预测详情 (JSON格式)',
    predicted_values TEXT NULL COMMENT '预测值 (JSON格式)',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康预测表';

-- ============================
-- 4. 创建健康建议表 (如果不存在)
-- ============================

CREATE TABLE IF NOT EXISTS t_health_recommendation (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    customer_id BIGINT NOT NULL DEFAULT 0 COMMENT '客户ID',
    device_sn VARCHAR(50) NULL COMMENT '设备序列号',
    org_id BIGINT NULL COMMENT '组织ID',
    recommendation_type VARCHAR(50) NOT NULL COMMENT '建议类型',
    feature_name VARCHAR(50) NULL COMMENT '相关健康特征',
    title VARCHAR(200) NOT NULL COMMENT '建议标题',
    content TEXT NOT NULL COMMENT '建议内容',
    priority VARCHAR(20) DEFAULT 'medium' COMMENT '优先级 high/medium/low',
    category VARCHAR(50) NULL COMMENT '建议分类',
    target_value DECIMAL(10,2) NULL COMMENT '目标值',
    current_value DECIMAL(10,2) NULL COMMENT '当前值',
    improvement_range VARCHAR(100) NULL COMMENT '改善范围',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态 active/completed/ignored',
    effective_date DATE NULL COMMENT '生效日期',
    expire_date DATE NULL COMMENT '过期日期',
    is_read TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    feedback_score INT NULL COMMENT '反馈评分 1-5',
    feedback_comment TEXT NULL COMMENT '反馈评论',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康建议表';

-- ============================
-- 5. 创建健康档案表 (如果不存在)
-- ============================

CREATE TABLE IF NOT EXISTS t_health_profile (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    customer_id BIGINT NOT NULL DEFAULT 0 COMMENT '客户ID',
    device_sn VARCHAR(50) NULL COMMENT '设备序列号',
    org_id BIGINT NULL COMMENT '组织ID',
    profile_date DATE NOT NULL COMMENT '档案日期',
    overall_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '综合健康评分',
    health_level VARCHAR(20) DEFAULT 'fair' COMMENT '健康等级',
    risk_factors TEXT NULL COMMENT '风险因素 (JSON)',
    health_trends TEXT NULL COMMENT '健康趋势 (JSON)',
    key_metrics TEXT NULL COMMENT '关键指标 (JSON)',
    improvement_areas TEXT NULL COMMENT '改进区域 (JSON)',
    strengths TEXT NULL COMMENT '优势项目 (JSON)',
    recommendations_count INT DEFAULT 0 COMMENT '建议数量',
    alerts_count INT DEFAULT 0 COMMENT '告警数量',
    data_completeness DECIMAL(5,2) DEFAULT 0.00 COMMENT '数据完整度',
    analysis_period_days INT DEFAULT 30 COMMENT '分析周期天数',
    last_update_date DATE NULL COMMENT '最后更新日期',
    summary TEXT NULL COMMENT '档案摘要',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康档案表';

-- ============================
-- 6. 创建必要的索引
-- ============================

-- t_health_prediction 索引
CREATE INDEX idx_health_prediction_user ON t_health_prediction(user_id, customer_id);
CREATE INDEX idx_health_prediction_date ON t_health_prediction(prediction_date);
CREATE INDEX idx_health_prediction_deleted ON t_health_prediction(is_deleted);

-- t_health_recommendation 索引  
CREATE INDEX idx_health_recommendation_user ON t_health_recommendation(user_id, customer_id);
CREATE INDEX idx_health_recommendation_status ON t_health_recommendation(status, is_deleted);
CREATE INDEX idx_health_recommendation_date ON t_health_recommendation(effective_date);

-- t_health_profile 索引
CREATE INDEX idx_health_profile_user ON t_health_profile(user_id, customer_id);
CREATE INDEX idx_health_profile_date ON t_health_profile(profile_date);
CREATE INDEX idx_health_profile_deleted ON t_health_profile(is_deleted);

SELECT 'Health tables schema fix completed successfully!' as status;