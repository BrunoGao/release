-- 添加 customer_id 字段到 sys_position 表
-- 用于实现租户级岗位隔离

ALTER TABLE sys_position 
ADD COLUMN customer_id BIGINT DEFAULT 0 NOT NULL COMMENT '租户ID (0表示全局岗位，所有租户可见)';

-- 添加索引提升查询性能
CREATE INDEX idx_sys_position_customer_id ON sys_position(customer_id);

-- 创建复合索引
CREATE INDEX idx_sys_position_customer_org ON sys_position(customer_id, org_id);

-- 更新现有数据：将现有岗位设为全局岗位
UPDATE sys_position SET customer_id = 0 WHERE customer_id IS NULL;