-- 移除 sys_user 表的 user_name 唯一约束
-- 原因: 员工名字可以重复，应该通过用户ID区分，而不是用户名
-- 作者: bruno.gao
-- 时间: 2025-09-22

-- 检查并删除 user_name 唯一约束
-- 注意：不同数据库可能有不同的约束名称

-- 方法1: 如果约束名为 idx_user_name_unique
ALTER TABLE sys_user DROP INDEX IF EXISTS idx_user_name_unique;

-- 方法2: 如果约束名为 UK_user_name 
ALTER TABLE sys_user DROP INDEX IF EXISTS UK_user_name;

-- 方法3: 如果约束名为 ux_sys_user_user_name
ALTER TABLE sys_user DROP INDEX IF EXISTS ux_sys_user_user_name;

-- 方法4: 通用方法 - 查看所有约束后再删除
-- 可以先运行以下查询查看所有约束：
-- SHOW INDEX FROM sys_user WHERE Column_name = 'user_name';

-- 添加注释说明
ALTER TABLE sys_user COMMENT = '用户表 - user_name字段不再强制唯一，员工可以重名，通过ID区分';

-- 验证约束删除是否成功的查询
-- SELECT * FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
-- WHERE TABLE_NAME = 'sys_user' AND CONSTRAINT_TYPE = 'UNIQUE';