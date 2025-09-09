-- ===============================================================================
-- sys_user表增加org_id和org_name字段的数据库迁移脚本
-- 执行时间：预计2-5分钟（取决于数据量）
-- ===============================================================================

-- 第一步：添加字段到sys_user表
ALTER TABLE sys_user 
ADD COLUMN org_id BIGINT NULL COMMENT '组织ID，直接关联sys_org_info.id',
ADD COLUMN org_name VARCHAR(100) NULL COMMENT '组织名称，冗余字段用于快速查询';

-- 第二步：创建索引以优化查询性能
CREATE INDEX idx_sys_user_org_id ON sys_user(org_id);
CREATE INDEX idx_sys_user_customer_org ON sys_user(customer_id, org_id);
CREATE INDEX idx_sys_user_customer_org_status ON sys_user(customer_id, org_id, status, is_deleted);

-- 第三步：数据迁移 - 从sys_user_org关联表同步数据到sys_user表
-- 注意：这里假设关联表名为sys_user_org和组织表名为sys_org_info
-- 请根据实际表名调整

-- 3.1 迁移策略1：直接从用户-组织关联表迁移（适用于有sys_user_org关联表的情况）
UPDATE sys_user u 
INNER JOIN (
    SELECT 
        uo.user_id,
        uo.org_id,
        COALESCE(o.name, oi.name) as org_name
    FROM sys_user_org uo
    LEFT JOIN sys_org_info o ON uo.org_id = o.id AND o.is_deleted = 0
    LEFT JOIN sys_org_units oi ON uo.org_id = oi.id AND oi.is_deleted = 0
    WHERE uo.is_deleted = 0
) org_data ON u.id = org_data.user_id
SET 
    u.org_id = org_data.org_id,
    u.org_name = org_data.org_name
WHERE u.is_deleted = 0;

-- 3.2 迁移策略2：如果没有关联表，通过其他方式确定用户的组织归属
-- 例如：通过设备信息、部门编码等推导组织关系
-- UPDATE sys_user u 
-- INNER JOIN t_device_info d ON u.device_sn = d.serial_number
-- INNER JOIN sys_org_info o ON d.dept_id = o.id
-- SET u.org_id = o.id, u.org_name = o.name
-- WHERE u.is_deleted = 0 AND d.is_deleted = 0 AND o.is_deleted = 0;

-- 第四步：数据完整性检查
-- 检查迁移结果统计
SELECT 
    COUNT(*) as total_users,
    COUNT(org_id) as users_with_org_id,
    COUNT(org_name) as users_with_org_name,
    ROUND(COUNT(org_id) * 100.0 / COUNT(*), 2) as coverage_percentage
FROM sys_user 
WHERE is_deleted = 0;

-- 检查组织分布
SELECT 
    org_name,
    COUNT(*) as user_count
FROM sys_user 
WHERE is_deleted = 0 AND org_name IS NOT NULL
GROUP BY org_name
ORDER BY user_count DESC;

-- 第五步：清理和优化（可选）
-- 清理空白的组织名称
UPDATE sys_user 
SET org_name = '未分配' 
WHERE is_deleted = 0 AND (org_name IS NULL OR org_name = '');

-- 更新表统计信息以优化查询性能
ANALYZE TABLE sys_user;

-- ===============================================================================
-- 回滚脚本（如果需要撤销更改）
-- ===============================================================================

-- 警告：执行回滚前请确保数据已备份
-- DROP INDEX IF EXISTS idx_sys_user_org_id;
-- DROP INDEX IF EXISTS idx_sys_user_customer_org;
-- DROP INDEX IF EXISTS idx_sys_user_customer_org_status;
-- ALTER TABLE sys_user DROP COLUMN org_id, DROP COLUMN org_name;

-- ===============================================================================
-- 验证脚本
-- ===============================================================================

-- 验证数据一致性：检查用户表的org_name与组织表的name是否一致
SELECT 
    u.id as user_id,
    u.user_name,
    u.org_id,
    u.org_name as user_org_name,
    COALESCE(o.name, oi.name) as actual_org_name,
    CASE 
        WHEN u.org_name = COALESCE(o.name, oi.name) THEN 'MATCH'
        ELSE 'MISMATCH'
    END as status
FROM sys_user u
LEFT JOIN sys_org_info o ON u.org_id = o.id AND o.is_deleted = 0
LEFT JOIN sys_org_units oi ON u.org_id = oi.id AND oi.is_deleted = 0
WHERE u.is_deleted = 0 AND u.org_id IS NOT NULL
HAVING status = 'MISMATCH'
LIMIT 10;

-- 性能测试查询：验证优化效果
-- 优化前的查询（需要JOIN）
EXPLAIN SELECT 
    u.user_name, 
    o.name as org_name
FROM sys_user u
LEFT JOIN sys_user_org uo ON u.id = uo.user_id AND uo.is_deleted = 0
LEFT JOIN sys_org_info o ON uo.org_id = o.id AND o.is_deleted = 0
WHERE u.customer_id = 1939964806110937090 AND u.is_deleted = 0;

-- 优化后的查询（单表查询）
EXPLAIN SELECT 
    u.user_name, 
    u.org_name
FROM sys_user u
WHERE u.customer_id = 1939964806110937090 AND u.is_deleted = 0;