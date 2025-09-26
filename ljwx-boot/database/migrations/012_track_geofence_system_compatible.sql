-- 运动轨迹与电子围栏系统数据库升级脚本 (MySQL 9.x 兼容版)
-- 创建时间: 2025-01-27
-- 作者: bruno.gao
-- 版本: v1.0.0

SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='';
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

-- =============================================================================
-- 第一部分：扩展 t_user_health_data 表，添加轨迹跟踪字段
-- =============================================================================

-- 1.1 检查并添加轨迹相关字段到现有健康数据表
-- 添加 speed 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND COLUMN_NAME = ''speed''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_user_health_data` ADD COLUMN `speed` DOUBLE DEFAULT NULL COMMENT ''速度(km/h)'' AFTER `distance`', 
    'SELECT ''speed column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 bearing 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND COLUMN_NAME = ''bearing''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_user_health_data` ADD COLUMN `bearing` DOUBLE DEFAULT NULL COMMENT ''方向角(度，0-360)'' AFTER `speed`', 
    'SELECT ''bearing column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 accuracy 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND COLUMN_NAME = ''accuracy''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_user_health_data` ADD COLUMN `accuracy` DOUBLE DEFAULT NULL COMMENT ''定位精度(米)'' AFTER `bearing`', 
    'SELECT ''accuracy column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 location_type 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND COLUMN_NAME = ''location_type''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_user_health_data` ADD COLUMN `location_type` TINYINT DEFAULT NULL COMMENT ''定位类型 1-GPS 2-网络 3-被动'' AFTER `accuracy`', 
    'SELECT ''location_type column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加 geom 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND COLUMN_NAME = ''geom''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_user_health_data` ADD COLUMN `geom` GEOMETRY DEFAULT NULL COMMENT ''空间几何对象'' AFTER `location_type`', 
    'SELECT ''geom column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 1.2 创建空间索引以提高地理查询性能 (如果不存在)
SET @sql = 'SELECT COUNT(*) INTO @idx_exists FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND INDEX_NAME = ''idx_health_data_geom''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@idx_exists = 0, 
    'CREATE SPATIAL INDEX `idx_health_data_geom` ON `t_user_health_data` (`geom`)', 
    'SELECT ''idx_health_data_geom already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 1.3 创建复合索引优化轨迹查询 (如果不存在)
SET @sql = 'SELECT COUNT(*) INTO @idx_exists FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND INDEX_NAME = ''idx_health_data_user_time_location''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@idx_exists = 0, 
    'CREATE INDEX `idx_health_data_user_time_location` ON `t_user_health_data` (`user_name`, `timestamp`, `longitude`, `latitude`)', 
    'SELECT ''idx_health_data_user_time_location already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = 'SELECT COUNT(*) INTO @idx_exists FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_user_health_data'' AND INDEX_NAME = ''idx_health_data_device_time_location''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@idx_exists = 0, 
    'CREATE INDEX `idx_health_data_device_time_location` ON `t_user_health_data` (`device_sn`, `timestamp`, `longitude`, `latitude`)', 
    'SELECT ''idx_health_data_device_time_location already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =============================================================================
-- 第二部分：检查 t_geofence 表是否存在，如果不存在则创建
-- =============================================================================

-- 2.1 创建 t_geofence 表 (如果不存在)
CREATE TABLE IF NOT EXISTS `t_geofence` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(100) NOT NULL COMMENT '电子围栏名称',
    `area` TEXT COMMENT '围栏区域 (GeoJSON或WKT格式)',
    `description` VARCHAR(500) COMMENT '围栏描述',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '围栏状态 (active/inactive)',
    `fence_type` ENUM('CIRCLE', 'RECTANGLE', 'POLYGON') DEFAULT 'CIRCLE' COMMENT '围栏类型',
    `center_lng` DECIMAL(11,8) DEFAULT NULL COMMENT '中心点经度',
    `center_lat` DECIMAL(11,8) DEFAULT NULL COMMENT '中心点纬度',
    `radius` FLOAT DEFAULT NULL COMMENT '半径(米)-圆形围栏专用',
    `geom` GEOMETRY DEFAULT NULL COMMENT '空间几何对象',
    `alert_on_enter` TINYINT(1) DEFAULT 1 COMMENT '进入围栏时是否告警',
    `alert_on_exit` TINYINT(1) DEFAULT 1 COMMENT '离开围栏时是否告警',
    `alert_on_stay` TINYINT(1) DEFAULT 0 COMMENT '停留超时是否告警',
    `stay_duration_minutes` INT DEFAULT 30 COMMENT '停留时长阈值(分钟)',
    `alert_level` ENUM('LOW', 'MEDIUM', 'HIGH') DEFAULT 'MEDIUM' COMMENT '告警级别',
    `notify_channels` JSON DEFAULT NULL COMMENT '通知渠道配置',
    `notify_template_id` VARCHAR(50) DEFAULT NULL COMMENT '通知模板ID',
    `org_id` BIGINT DEFAULT NULL COMMENT '组织ID',
    `customer_id` BIGINT DEFAULT 0 COMMENT '租户ID',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    `created_by` VARCHAR(50) DEFAULT NULL COMMENT '创建人',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_geofence_customer_active` (`customer_id`, `is_active`),
    KEY `idx_geofence_org_active` (`org_id`, `is_active`),
    KEY `idx_geofence_center_location` (`center_lng`, `center_lat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='电子围栏表';

-- 2.2 为现有的t_geofence表添加新字段 (如果字段不存在)
-- 检查每个字段是否存在，不存在则添加

-- fence_type 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''fence_type''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `fence_type` ENUM(''CIRCLE'', ''RECTANGLE'', ''POLYGON'') DEFAULT ''CIRCLE'' COMMENT ''围栏类型'' AFTER `status`', 
    'SELECT ''fence_type column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- center_lng 字段  
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''center_lng''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `center_lng` DECIMAL(11,8) DEFAULT NULL COMMENT ''中心点经度'' AFTER `fence_type`', 
    'SELECT ''center_lng column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- center_lat 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''center_lat''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `center_lat` DECIMAL(11,8) DEFAULT NULL COMMENT ''中心点纬度'' AFTER `center_lng`', 
    'SELECT ''center_lat column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- radius 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''radius''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `radius` FLOAT DEFAULT NULL COMMENT ''半径(米)-圆形围栏专用'' AFTER `center_lat`', 
    'SELECT ''radius column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- geom 字段 (围栏几何对象)
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''geom''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `geom` GEOMETRY DEFAULT NULL COMMENT ''空间几何对象'' AFTER `radius`', 
    'SELECT ''geom column already exists in t_geofence'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加告警配置字段
-- alert_on_enter 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''alert_on_enter''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `alert_on_enter` TINYINT(1) DEFAULT 1 COMMENT ''进入围栏时是否告警''', 
    'SELECT ''alert_on_enter column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- alert_on_exit 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''alert_on_exit''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `alert_on_exit` TINYINT(1) DEFAULT 1 COMMENT ''离开围栏时是否告警''', 
    'SELECT ''alert_on_exit column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- alert_on_stay 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''alert_on_stay''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `alert_on_stay` TINYINT(1) DEFAULT 0 COMMENT ''停留超时是否告警''', 
    'SELECT ''alert_on_stay column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- stay_duration_minutes 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''stay_duration_minutes''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `stay_duration_minutes` INT DEFAULT 30 COMMENT ''停留时长阈值(分钟)''', 
    'SELECT ''stay_duration_minutes column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- alert_level 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''alert_level''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `alert_level` ENUM(''LOW'', ''MEDIUM'', ''HIGH'') DEFAULT ''MEDIUM'' COMMENT ''告警级别''', 
    'SELECT ''alert_level column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 添加多租户支持字段
-- customer_id 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''customer_id''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `customer_id` BIGINT DEFAULT 0 COMMENT ''租户ID''', 
    'SELECT ''customer_id column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- is_active 字段
SET @sql = 'SELECT COUNT(*) INTO @col_exists FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND COLUMN_NAME = ''is_active''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@col_exists = 0, 
    'ALTER TABLE `t_geofence` ADD COLUMN `is_active` TINYINT(1) DEFAULT 1 COMMENT ''是否启用''', 
    'SELECT ''is_active column already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.3 创建围栏空间索引 (如果不存在)
SET @sql = 'SELECT COUNT(*) INTO @idx_exists FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ''t_geofence'' AND INDEX_NAME = ''idx_geofence_geom''';
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @sql = IF(@idx_exists = 0, 
    'CREATE SPATIAL INDEX `idx_geofence_geom` ON `t_geofence` (`geom`)', 
    'SELECT ''idx_geofence_geom already exists'' as message');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =============================================================================
-- 第三部分：创建围栏告警记录表
-- =============================================================================

-- 3.1 创建围栏告警表 (如果不存在)
CREATE TABLE IF NOT EXISTS `t_geofence_alert` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `alert_id` VARCHAR(50) NOT NULL COMMENT '告警ID(UUID)',
    `fence_id` BIGINT NOT NULL COMMENT '围栏ID',
    `fence_name` VARCHAR(100) NOT NULL COMMENT '围栏名称',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `device_sn` VARCHAR(50) NOT NULL COMMENT '设备序列号',
    `event_type` ENUM('ENTER', 'EXIT', 'STAY_TIMEOUT') NOT NULL COMMENT '事件类型',
    `event_time` DATETIME NOT NULL COMMENT '事件发生时间',
    `location_lng` DECIMAL(11,8) NOT NULL COMMENT '事件位置经度',
    `location_lat` DECIMAL(11,8) NOT NULL COMMENT '事件位置纬度',
    `alert_level` ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL COMMENT '告警级别',
    `alert_status` ENUM('PENDING', 'PROCESSING', 'PROCESSED', 'IGNORED') DEFAULT 'PENDING' COMMENT '告警状态',
    `process_time` DATETIME DEFAULT NULL COMMENT '处理时间',
    `processed_by` VARCHAR(50) DEFAULT NULL COMMENT '处理人',
    `process_note` TEXT DEFAULT NULL COMMENT '处理备注',
    `notification_status` JSON DEFAULT NULL COMMENT '通知状态',
    `customer_id` BIGINT DEFAULT 0 COMMENT '租户ID',
    `org_id` BIGINT DEFAULT NULL COMMENT '组织ID',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_alert_id` (`alert_id`),
    KEY `idx_alert_fence_user` (`fence_id`, `user_id`),
    KEY `idx_alert_event_time` (`event_time`),
    KEY `idx_alert_status_level` (`alert_status`, `alert_level`),
    KEY `idx_alert_customer_org` (`customer_id`, `org_id`),
    KEY `idx_alert_device_time` (`device_sn`, `event_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='围栏告警记录表';

-- =============================================================================
-- 第四部分：创建围栏用户绑定表
-- =============================================================================

-- 4.1 创建围栏绑定表 (如果不存在)
CREATE TABLE IF NOT EXISTS `t_geofence_bind` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `fence_id` BIGINT NOT NULL COMMENT '围栏ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `bind_type` ENUM('MONITOR', 'EXCLUDE') DEFAULT 'MONITOR' COMMENT '绑定类型 MONITOR-监控 EXCLUDE-排除',
    `bind_status` TINYINT(1) DEFAULT 1 COMMENT '绑定状态 1-启用 0-停用',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `effective_time` TIME DEFAULT NULL COMMENT '生效时间',
    `expiry_time` TIME DEFAULT NULL COMMENT '失效时间',
    `effective_days` VARCHAR(20) DEFAULT NULL COMMENT '生效星期 1,2,3,4,5,6,7',
    `customer_id` BIGINT DEFAULT 0 COMMENT '租户ID',
    `org_id` BIGINT DEFAULT NULL COMMENT '组织ID',
    `created_by` VARCHAR(50) DEFAULT NULL COMMENT '创建人',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_fence_user_bind` (`fence_id`, `user_id`),
    KEY `idx_bind_customer_org` (`customer_id`, `org_id`),
    KEY `idx_bind_user_status` (`user_id`, `bind_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='围栏用户绑定表';

-- =============================================================================
-- 第五部分：创建用户在线状态表
-- =============================================================================

-- 5.1 创建用户在线状态表 (如果不存在)
CREATE TABLE IF NOT EXISTS `t_user_online_status` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `device_sn` VARCHAR(50) NOT NULL COMMENT '设备序列号',
    `online_status` TINYINT(1) DEFAULT 0 COMMENT '在线状态 1-在线 0-离线',
    `last_location_lng` DECIMAL(11,8) DEFAULT NULL COMMENT '最后位置经度',
    `last_location_lat` DECIMAL(11,8) DEFAULT NULL COMMENT '最后位置纬度',
    `last_location_time` DATETIME DEFAULT NULL COMMENT '最后定位时间',
    `last_heartbeat_time` DATETIME DEFAULT NULL COMMENT '最后心跳时间',
    `connection_type` ENUM('GPS', 'NETWORK', 'PASSIVE') DEFAULT NULL COMMENT '连接类型',
    `battery_level` TINYINT DEFAULT NULL COMMENT '电池电量',
    `signal_strength` TINYINT DEFAULT NULL COMMENT '信号强度',
    `customer_id` BIGINT DEFAULT 0 COMMENT '租户ID',
    `org_id` BIGINT DEFAULT NULL COMMENT '组织ID',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_device_online` (`user_id`, `device_sn`),
    KEY `idx_online_status_time` (`online_status`, `last_heartbeat_time`),
    KEY `idx_online_customer_org` (`customer_id`, `org_id`),
    KEY `idx_online_location_time` (`last_location_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户在线状态表';

-- =============================================================================
-- 第六部分：更新现有围栏数据兼容性处理
-- =============================================================================

-- 6.1 为现有围栏数据设置默认值 (如果表存在且有数据)
UPDATE `t_geofence` SET 
    `fence_type` = COALESCE(`fence_type`, 'CIRCLE'),
    `alert_on_enter` = COALESCE(`alert_on_enter`, 1),
    `alert_on_exit` = COALESCE(`alert_on_exit`, 1),
    `alert_on_stay` = COALESCE(`alert_on_stay`, 0),
    `stay_duration_minutes` = COALESCE(`stay_duration_minutes`, 30),
    `alert_level` = COALESCE(`alert_level`, 'MEDIUM'),
    `is_active` = COALESCE(`is_active`, 1),
    `customer_id` = COALESCE(`customer_id`, 0)
WHERE `id` > 0;

-- =============================================================================
-- 第七部分：插入演示数据（可选）
-- =============================================================================

-- 7.1 插入演示围栏数据
INSERT IGNORE INTO `t_geofence` (
    `name`, `area`, `description`, `fence_type`, `center_lng`, `center_lat`, `radius`,
    `alert_on_enter`, `alert_on_exit`, `alert_level`, `customer_id`, `is_active`
) VALUES
('公司总部', 'CIRCLE(116.397128 39.916527)', '北京公司总部围栏', 'CIRCLE', 116.397128, 39.916527, 200.0, 1, 1, 'MEDIUM', 0, 1),
('生产车间', 'CIRCLE(116.398000 39.917000)', '生产车间安全围栏', 'CIRCLE', 116.398000, 39.917000, 100.0, 1, 1, 'HIGH', 0, 1),
('员工宿舍区', 'CIRCLE(116.396000 39.916000)', '员工宿舍区域', 'CIRCLE', 116.396000, 39.916000, 300.0, 1, 1, 'LOW', 0, 1);

-- =============================================================================
-- 恢复设置
-- =============================================================================
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET SQL_MODE=@OLD_SQL_MODE;

-- 完成提示
SELECT '🚀 运动轨迹与电子围栏系统升级完成！' AS message, 
       '✅ 轨迹字段已添加到健康数据表' AS track_extension,
       '✅ 围栏表已扩展告警和多租户功能' AS geofence_extension,
       '✅ 创建了告警记录表和绑定表' AS new_tables,
       '✅ 空间索引已创建' AS spatial_optimization,
       NOW() AS completion_time;