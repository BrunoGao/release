-- 管理员排除功能 - 数据库升级脚本
-- 执行日期: 2024-12-20
-- 功能: 在sys_role表中增加is_admin字段，用于标记管理员角色

-- 1. 添加is_admin字段到sys_role表
ALTER TABLE sys_role 
ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为管理员角色（0普通角色，1管理员角色）' AFTER status;

-- 2. 初始化管理员角色数据
-- 将ADMIN和DAdmin角色标记为管理员角色
UPDATE sys_role SET is_admin = 1 WHERE role_code IN ('ADMIN', 'DAdmin');

-- 3. 确保普通角色is_admin为0
UPDATE sys_role SET is_admin = 0 WHERE role_code NOT IN ('ADMIN', 'DAdmin');

-- 4. 验证数据（可选，用于检查）
-- SELECT role_name, role_code, is_admin FROM sys_role ORDER BY is_admin DESC, role_code; 