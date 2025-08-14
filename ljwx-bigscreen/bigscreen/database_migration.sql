-- 设备信息表优化迁移脚本
-- 为t_device_info表添加user_id和org_id字段以提高查询性能

-- 1. 添加user_id字段（绑定用户ID）
ALTER TABLE t_device_info 
ADD COLUMN user_id BIGINT NULL COMMENT '绑定用户ID' AFTER customer_id;

-- 2. 添加org_id字段（直属部门ID）
ALTER TABLE t_device_info 
ADD COLUMN org_id BIGINT NULL COMMENT '直属部门ID' AFTER user_id;

-- 3. 为新字段创建索引以提高查询性能
CREATE INDEX idx_device_user_id ON t_device_info(user_id);
CREATE INDEX idx_device_org_id ON t_device_info(org_id);
CREATE INDEX idx_device_user_org ON t_device_info(user_id, org_id);

-- 4. 为历史表添加索引优化
CREATE INDEX idx_history_sn_timestamp ON t_device_info_history(serial_number, timestamp);
CREATE INDEX idx_history_battery_level ON t_device_info_history(battery_level);
CREATE INDEX idx_history_charging_status ON t_device_info_history(charging_status);

-- 5. 更新现有数据，填充user_id和org_id字段
UPDATE t_device_info d 
SET 
    user_id = (
        SELECT u.id 
        FROM sys_user u 
        WHERE u.device_sn = d.serial_number 
        AND u.is_deleted = 0 
        LIMIT 1
    ),
    org_id = (
        SELECT uo.org_id 
        FROM sys_user u 
        JOIN sys_user_org uo ON u.id = uo.user_id 
        WHERE u.device_sn = d.serial_number 
        AND u.is_deleted = 0 
        AND uo.is_deleted = 0 
        LIMIT 1
    )
WHERE d.serial_number IS NOT NULL; 