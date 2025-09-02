-- ===============================================
-- 租户/部门权限管理补丁SQL
-- 功能: 为admin新增租户权限控制添加数据字典支持
-- 版本: v1.0.7
-- 日期: 2025-01-16
-- ===============================================

-- 1. 添加用户角色类型字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(1001, '用户角色类型', 'user_role_type', '1', 10, '用户角色分类字典', '1', NOW());

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(10001, 1001, 'user_role_type', 'admin', '系统管理员', 'Administrator', 'error', 1, '系统最高权限管理员，可创建租户', '1', NOW()),
(10002, 1001, 'user_role_type', 'tenant_admin', '租户管理员', 'Tenant Admin', 'warning', 2, '租户管理员，可管理租户下所有资源', '1', NOW()),
(10003, 1001, 'user_role_type', 'dept_admin', '部门管理员', 'Department Admin', 'info', 3, '部门管理员，可管理部门下的用户和资源', '1', NOW()),
(10004, 1001, 'user_role_type', 'user', '普通用户', 'Normal User', 'success', 4, '普通用户，只能查看和使用基本功能', '1', NOW());

-- 2. 添加组织类型字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(1002, '组织类型', 'org_type', '1', 11, '组织架构类型字典', '1', NOW());

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(10005, 1002, 'org_type', '1', '租户', 'Tenant', 'primary', 1, '顶级组织，多租户架构的租户', '1', NOW()),
(10006, 1002, 'org_type', '2', '部门', 'Department', 'info', 2, '租户下的部门组织', '1', NOW()),
(10007, 1002, 'org_type', '3', '子部门', 'Sub Department', 'default', 3, '部门下的子部门', '1', NOW());

-- 3. 添加权限等级字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(1003, '权限等级', 'permission_level', '1', 12, '系统权限等级分类', '1', NOW());

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(10008, 1003, 'permission_level', '1', '系统级', 'System Level', 'error', 1, '系统级权限，可操作所有资源', '1', NOW()),
(10009, 1003, 'permission_level', '2', '租户级', 'Tenant Level', 'warning', 2, '租户级权限，可操作租户内资源', '1', NOW()),
(10010, 1003, 'permission_level', '3', '部门级', 'Department Level', 'info', 3, '部门级权限，可操作部门内资源', '1', NOW()),
(10011, 1003, 'permission_level', '4', '个人级', 'Personal Level', 'success', 4, '个人级权限，只能操作个人资源', '1', NOW());

-- 4. 添加操作类型字典
INSERT INTO `sys_dict` (`id`, `name`, `code`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(1004, '操作类型', 'operation_type', '1', 13, '系统操作类型字典', '1', NOW());

INSERT INTO `sys_dict_item` (`id`, `dict_id`, `dict_code`, `value`, `zh_cn`, `en_us`, `type`, `sort`, `description`, `status`, `create_time`) VALUES 
(10012, 1004, 'operation_type', 'create_tenant', '创建租户', 'Create Tenant', 'error', 1, '创建新租户，仅admin可操作', '1', NOW()),
(10013, 1004, 'operation_type', 'create_dept', '创建部门', 'Create Department', 'warning', 2, '在租户下创建部门', '1', NOW()),
(10014, 1004, 'operation_type', 'manage_user', '管理用户', 'Manage User', 'info', 3, '管理用户账号和权限', '1', NOW()),
(10015, 1004, 'operation_type', 'view_data', '查看数据', 'View Data', 'success', 4, '查看业务数据', '1', NOW());

-- 5. 更新现有组织表，增加组织类型字段（如果不存在）
-- 注意：这个操作需要根据实际表结构调整
-- ALTER TABLE `sys_org_units` ADD COLUMN `org_type` varchar(10) DEFAULT '2' COMMENT '组织类型(1:租户,2:部门,3:子部门)' AFTER `level`;

-- 6. 为现有组织数据设置类型（根据level判断）
-- UPDATE `sys_org_units` SET `org_type` = '1' WHERE `level` = 1 AND `parent_id` = 0;
-- UPDATE `sys_org_units` SET `org_type` = '2' WHERE `level` = 2;
-- UPDATE `sys_org_units` SET `org_type` = '3' WHERE `level` >= 3;

-- ===============================================
-- 执行说明：
-- 1. 在应用此补丁前，请备份现有数据库
-- 2. 根据实际sys_dict表的id生成策略调整id值
-- 3. 如需要修改组织表结构，请取消注释相关ALTER和UPDATE语句
-- 4. 执行后重启应用以刷新字典缓存
-- ===============================================