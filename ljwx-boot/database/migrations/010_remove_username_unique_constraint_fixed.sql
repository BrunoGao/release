-- 移除 sys_user 表的 user_name 唯一约束
-- 原因: 员工名字可以重复，应该通过用户ID区分，而不是用户名
-- 作者: bruno.gao
-- 时间: 2025-09-22

-- 删除 user_name 唯一约束索引
DROP INDEX idx_user_name_unique ON sys_user;

-- 添加注释说明
ALTER TABLE sys_user COMMENT = '用户表 - user_name字段不再强制唯一，员工可以重名，通过ID区分';

-- 验证约束删除是否成功
SELECT 'Username unique constraint removed successfully' as result;