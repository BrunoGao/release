-- ===============================================
-- 菜单和权限多租户支持补丁SQL
-- 功能: 为sys_menu和sys_permission表添加多租户支持
-- 版本: v1.0.8
-- 日期: 2025-01-16
-- ===============================================

-- 1. 为sys_menu表添加customer_id字段（如果不存在）
-- ALTER TABLE `sys_menu` ADD COLUMN `customer_id` bigint(20) DEFAULT 0 COMMENT '租户ID(0:全局菜单)' AFTER `status`;

-- 2. 为sys_permission表添加customer_id字段（如果不存在）
-- ALTER TABLE `sys_permission` ADD COLUMN `customer_id` bigint(20) DEFAULT 0 COMMENT '租户ID(0:全局权限)' AFTER `status`;

-- 3. 为现有数据设置默认值（全部设为全局）
-- UPDATE `sys_menu` SET `customer_id` = 0 WHERE `customer_id` IS NULL;
-- UPDATE `sys_permission` SET `customer_id` = 0 WHERE `customer_id` IS NULL;

-- 4. 创建索引提高查询性能
-- CREATE INDEX `idx_sys_menu_customer_id` ON `sys_menu` (`customer_id`);
-- CREATE INDEX `idx_sys_permission_customer_id` ON `sys_permission` (`customer_id`);

-- ===============================================
-- 说明：
-- 1. customer_id = 0 表示全局菜单/权限，所有租户都可以访问
-- 2. customer_id > 0 表示租户专属菜单/权限，只有对应租户可以访问
-- 3. 在应用此补丁前，请备份现有数据库
-- 4. 根据实际需要取消注释相关语句
-- 5. 执行后需要更新相关业务代码以支持多租户查询
-- ===============================================