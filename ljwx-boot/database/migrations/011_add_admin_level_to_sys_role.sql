-- Migration: 为 sys_role 表添加 admin_level 字段
-- Author: 系统更新
-- Date: 2025-09-22
-- Description: 新增 admin_level 字段来区分不同级别的管理员角色

-- 添加 admin_level 字段
ALTER TABLE `sys_role` ADD COLUMN `admin_level` tinyint(1) NOT NULL DEFAULT '2' COMMENT '管理员级别（0:超级管理员，1:租户管理员，2:部门管理员）' AFTER `is_admin`;

-- 更新现有数据：根据角色名称设置合理的 admin_level 值
UPDATE `sys_role` SET `admin_level` = 0 WHERE `role_code` = 'super_admin' OR `role_name` LIKE '%超级管理员%';
UPDATE `sys_role` SET `admin_level` = 1 WHERE `role_code` = 'tenant_admin' OR `role_name` LIKE '%租户管理员%' OR `role_name` LIKE '%客户管理员%';
UPDATE `sys_role` SET `admin_level` = 2 WHERE `is_admin` = 1 AND `admin_level` NOT IN (0, 1);

-- 添加索引以提高查询性能
CREATE INDEX `idx_sys_role_admin_level` ON `sys_role` (`is_admin`, `admin_level`);

-- 记录迁移完成
INSERT INTO `sys_migration_log` (`migration_name`, `executed_at`, `status`) 
VALUES ('011_add_admin_level_to_sys_role', NOW(), 'SUCCESS')
ON DUPLICATE KEY UPDATE `executed_at` = NOW(), `status` = 'SUCCESS';