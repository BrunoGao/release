-- 管理员用户查询优化 - 添加用户类型和管理级别字段
-- Migration: 008_add_user_type_admin_level
-- Date: 2025-09-12
-- Description: 添加user_type和admin_level冗余字段以优化管理员查询性能

-- 1. 添加用户类型字段
ALTER TABLE sys_user ADD COLUMN user_type TINYINT DEFAULT 0 COMMENT '用户类型: 0=普通用户, 1=部门管理员, 2=租户管理员, 3=超级管理员';

-- 2. 添加管理级别字段  
ALTER TABLE sys_user ADD COLUMN admin_level TINYINT DEFAULT 0 COMMENT '管理级别: 0=非管理员, 1=部门级, 2=租户级, 3=系统级';

-- 3. 创建相关索引优化查询性能
ALTER TABLE sys_user ADD INDEX idx_user_type (user_type) COMMENT '用户类型索引';
ALTER TABLE sys_user ADD INDEX idx_admin_level (admin_level) COMMENT '管理级别索引';
ALTER TABLE sys_user ADD INDEX idx_org_admin (org_id, admin_level) COMMENT '组织管理员复合索引';
ALTER TABLE sys_user ADD INDEX idx_customer_admin (customer_id, admin_level) COMMENT '租户管理员复合索引';

-- 4. 初始化现有用户的类型数据
UPDATE sys_user su 
SET user_type = CASE 
    WHEN su.user_name = 'admin' THEN 3  -- 超级管理员
    WHEN EXISTS (
        SELECT 1 FROM sys_user_role sur 
        JOIN sys_role sr ON sur.role_id = sr.id 
        WHERE sur.user_id = su.id AND sr.is_admin = 1 AND sur.deleted = 0 AND sr.deleted = 0
    ) THEN CASE
        WHEN EXISTS (
            SELECT 1 FROM sys_user_org suo
            JOIN sys_org_units sou ON suo.org_id = sou.id
            WHERE suo.user_id = su.id AND (sou.parent_id IS NULL OR sou.parent_id IN (0, 1))
              AND suo.deleted = 0 AND sou.is_deleted = 0
        ) THEN 2  -- 租户管理员
        ELSE 1    -- 部门管理员
    END
    ELSE 0        -- 普通用户
END,
admin_level = CASE 
    WHEN su.user_name = 'admin' THEN 3  -- 系统级
    WHEN EXISTS (
        SELECT 1 FROM sys_user_role sur 
        JOIN sys_role sr ON sur.role_id = sr.id 
        WHERE sur.user_id = su.id AND sr.is_admin = 1 AND sur.deleted = 0 AND sr.deleted = 0
    ) THEN CASE
        WHEN EXISTS (
            SELECT 1 FROM sys_user_org suo
            JOIN sys_org_units sou ON suo.org_id = sou.id
            WHERE suo.user_id = su.id AND (sou.parent_id IS NULL OR sou.parent_id IN (0, 1))
              AND suo.deleted = 0 AND sou.is_deleted = 0
        ) THEN 2  -- 租户级
        ELSE 1    -- 部门级
    END
    ELSE 0        -- 非管理员
END
WHERE su.deleted = 0;

-- 5. 验证数据初始化结果
SELECT 
    user_type,
    admin_level,
    COUNT(*) as user_count,
    GROUP_CONCAT(user_name SEPARATOR ', ') as sample_users
FROM sys_user 
WHERE deleted = 0
GROUP BY user_type, admin_level
ORDER BY user_type, admin_level;