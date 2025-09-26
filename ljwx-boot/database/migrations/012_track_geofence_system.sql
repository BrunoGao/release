-- 运动轨迹与电子围栏系统数据库升级脚本
-- 创建时间: 2025-01-27
-- 作者: bruno.gao
-- 版本: v1.0.0

-- =============================================================================
-- 第一部分：扩展 t_user_health_data 表，添加轨迹跟踪字段
-- =============================================================================

-- 1.1 添加轨迹相关字段到现有健康数据表
ALTER TABLE `t_user_health_data` 
    ADD COLUMN IF NOT EXISTS `speed` DOUBLE DEFAULT NULL COMMENT '速度(km/h)' AFTER `distance`,
    ADD COLUMN IF NOT EXISTS `bearing` DOUBLE DEFAULT NULL COMMENT '方向角(度，0-360)' AFTER `speed`,
    ADD COLUMN IF NOT EXISTS `accuracy` DOUBLE DEFAULT NULL COMMENT '定位精度(米)' AFTER `bearing`,
    ADD COLUMN IF NOT EXISTS `location_type` TINYINT DEFAULT NULL COMMENT '定位类型 1-GPS 2-网络 3-被动' AFTER `accuracy`,
    ADD COLUMN IF NOT EXISTS `geom` GEOMETRY DEFAULT NULL COMMENT '空间几何对象' AFTER `location_type`;

-- 1.2 创建空间索引以提高地理查询性能
CREATE SPATIAL INDEX IF NOT EXISTS `idx_health_data_geom` ON `t_user_health_data` (`geom`);

-- 1.3 创建复合索引优化轨迹查询
CREATE INDEX IF NOT EXISTS `idx_health_data_user_time_location` ON `t_user_health_data` (`user_id`, `timestamp`, `longitude`, `latitude`);
CREATE INDEX IF NOT EXISTS `idx_health_data_device_time_location` ON `t_user_health_data` (`device_sn`, `timestamp`, `longitude`, `latitude`);

-- =============================================================================
-- 第二部分：扩展 t_geofence 表，添加轨迹围栏字段
-- =============================================================================

-- 2.1 添加围栏类型和空间计算字段
ALTER TABLE `t_geofence`
    ADD COLUMN IF NOT EXISTS `fence_type` ENUM('CIRCLE', 'RECTANGLE', 'POLYGON') DEFAULT 'CIRCLE' COMMENT '围栏类型' AFTER `status`,
    ADD COLUMN IF NOT EXISTS `center_lng` DECIMAL(11,8) DEFAULT NULL COMMENT '中心点经度' AFTER `fence_type`,
    ADD COLUMN IF NOT EXISTS `center_lat` DECIMAL(11,8) DEFAULT NULL COMMENT '中心点纬度' AFTER `center_lng`,
    ADD COLUMN IF NOT EXISTS `radius` FLOAT DEFAULT NULL COMMENT '半径(米)-圆形围栏专用' AFTER `center_lat`,
    ADD COLUMN IF NOT EXISTS `geom` GEOMETRY DEFAULT NULL COMMENT '空间几何对象' AFTER `radius`;

-- 2.2 添加告警配置字段
ALTER TABLE `t_geofence`
    ADD COLUMN IF NOT EXISTS `alert_on_enter` TINYINT(1) DEFAULT 1 COMMENT '进入围栏时是否告警' AFTER `geom`,
    ADD COLUMN IF NOT EXISTS `alert_on_exit` TINYINT(1) DEFAULT 1 COMMENT '离开围栏时是否告警' AFTER `alert_on_enter`,
    ADD COLUMN IF NOT EXISTS `alert_on_stay` TINYINT(1) DEFAULT 0 COMMENT '停留超时是否告警' AFTER `alert_on_exit`,
    ADD COLUMN IF NOT EXISTS `stay_duration_minutes` INT DEFAULT 30 COMMENT '停留时长阈值(分钟)' AFTER `alert_on_stay`,
    ADD COLUMN IF NOT EXISTS `alert_level` ENUM('LOW', 'MEDIUM', 'HIGH') DEFAULT 'MEDIUM' COMMENT '告警级别' AFTER `stay_duration_minutes`;

-- 2.3 添加通知配置字段
ALTER TABLE `t_geofence`
    ADD COLUMN IF NOT EXISTS `notify_channels` JSON DEFAULT NULL COMMENT '通知渠道配置' AFTER `alert_level`,
    ADD COLUMN IF NOT EXISTS `notify_template_id` VARCHAR(50) DEFAULT NULL COMMENT '通知模板ID' AFTER `notify_channels`;

-- 2.4 添加多租户支持字段
ALTER TABLE `t_geofence`
    ADD COLUMN IF NOT EXISTS `org_id` BIGINT DEFAULT NULL COMMENT '组织ID' AFTER `notify_template_id`,
    ADD COLUMN IF NOT EXISTS `customer_id` BIGINT DEFAULT 0 COMMENT '租户ID' AFTER `org_id`,
    ADD COLUMN IF NOT EXISTS `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否启用' AFTER `customer_id`,
    ADD COLUMN IF NOT EXISTS `created_by` VARCHAR(50) DEFAULT NULL COMMENT '创建人' AFTER `is_active`;

-- 2.5 创建围栏空间索引
CREATE SPATIAL INDEX IF NOT EXISTS `idx_geofence_geom` ON `t_geofence` (`geom`);

-- 2.6 创建围栏查询索引
CREATE INDEX IF NOT EXISTS `idx_geofence_customer_active` ON `t_geofence` (`customer_id`, `is_active`);
CREATE INDEX IF NOT EXISTS `idx_geofence_org_active` ON `t_geofence` (`org_id`, `is_active`);
CREATE INDEX IF NOT EXISTS `idx_geofence_center_location` ON `t_geofence` (`center_lng`, `center_lat`);

-- =============================================================================
-- 第三部分：创建围栏告警记录表
-- =============================================================================

-- 3.1 创建围栏告警表
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
    KEY `idx_alert_device_time` (`device_sn`, `event_time`),
    FOREIGN KEY (`fence_id`) REFERENCES `t_geofence` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='围栏告警记录表';

-- =============================================================================
-- 第四部分：创建围栏用户绑定表
-- =============================================================================

-- 4.1 创建围栏绑定表
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
    KEY `idx_bind_user_status` (`user_id`, `bind_status`),
    FOREIGN KEY (`fence_id`) REFERENCES `t_geofence` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='围栏用户绑定表';

-- =============================================================================
-- 第五部分：创建用户在线状态表
-- =============================================================================

-- 5.1 创建用户在线状态表
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

-- 6.1 为现有围栏数据设置默认值
UPDATE `t_geofence` SET 
    `fence_type` = 'CIRCLE',
    `alert_on_enter` = 1,
    `alert_on_exit` = 1,
    `alert_on_stay` = 0,
    `stay_duration_minutes` = 30,
    `alert_level` = 'MEDIUM',
    `is_active` = 1,
    `customer_id` = 0
WHERE `fence_type` IS NULL;

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
-- 第八部分：创建视图（可选）
-- =============================================================================

-- 8.1 创建轨迹查询视图
CREATE OR REPLACE VIEW `v_user_track_points` AS
SELECT 
    t.id,
    t.user_id,
    t.device_sn,
    t.timestamp,
    t.longitude,
    t.latitude,
    t.altitude,
    t.speed,
    t.bearing,
    t.accuracy,
    t.location_type,
    t.step,
    t.distance,
    t.calorie,
    t.customer_id,
    t.org_id,
    ST_AsText(t.geom) AS geom_wkt
FROM t_user_health_data t
WHERE t.longitude IS NOT NULL 
  AND t.latitude IS NOT NULL
  AND t.longitude BETWEEN -180 AND 180
  AND t.latitude BETWEEN -90 AND 90;

-- 8.2 创建活跃围栏视图
CREATE OR REPLACE VIEW `v_active_geofences` AS
SELECT 
    g.id,
    g.name,
    g.area,
    g.description,
    g.fence_type,
    g.center_lng,
    g.center_lat,
    g.radius,
    g.alert_on_enter,
    g.alert_on_exit,
    g.alert_on_stay,
    g.stay_duration_minutes,
    g.alert_level,
    g.customer_id,
    g.org_id,
    g.created_by,
    g.create_time,
    ST_AsText(g.geom) AS geom_wkt
FROM t_geofence g
WHERE g.is_active = 1;

-- =============================================================================
-- 第九部分：权限和触发器（可选）
-- =============================================================================

-- 9.1 创建围栏几何更新触发器
DELIMITER //
CREATE TRIGGER IF NOT EXISTS `tr_geofence_geom_update`
BEFORE UPDATE ON `t_geofence`
FOR EACH ROW
BEGIN
    -- 当中心点坐标或半径变化时，自动更新几何对象
    IF NEW.fence_type = 'CIRCLE' AND NEW.center_lng IS NOT NULL AND NEW.center_lat IS NOT NULL AND NEW.radius IS NOT NULL THEN
        SET NEW.geom = ST_GeomFromText(CONCAT('POINT(', NEW.center_lng, ' ', NEW.center_lat, ')'));
    END IF;
END//

-- 9.2 创建轨迹点几何更新触发器
CREATE TRIGGER IF NOT EXISTS `tr_health_data_geom_update`
BEFORE INSERT ON `t_user_health_data`
FOR EACH ROW
BEGIN
    -- 当插入轨迹点时，自动创建几何对象
    IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL THEN
        SET NEW.geom = ST_GeomFromText(CONCAT('POINT(', NEW.longitude, ' ', NEW.latitude, ')'));
    END IF;
END//

CREATE TRIGGER IF NOT EXISTS `tr_health_data_geom_update_on_update`
BEFORE UPDATE ON `t_user_health_data`
FOR EACH ROW
BEGIN
    -- 当更新轨迹点时，自动更新几何对象
    IF NEW.longitude IS NOT NULL AND NEW.latitude IS NOT NULL AND (OLD.longitude != NEW.longitude OR OLD.latitude != NEW.latitude) THEN
        SET NEW.geom = ST_GeomFromText(CONCAT('POINT(', NEW.longitude, ' ', NEW.latitude, ')'));
    END IF;
END//
DELIMITER ;

-- =============================================================================
-- 完成提示
-- =============================================================================
SELECT '🚀 运动轨迹与电子围栏系统升级完成！' AS message, 
       '✅ 轨迹字段已添加到健康数据表' AS track_extension,
       '✅ 围栏表已扩展告警和多租户功能' AS geofence_extension,
       '✅ 创建了告警记录表和绑定表' AS new_tables,
       '✅ 空间索引和触发器已创建' AS spatial_optimization,
       NOW() AS completion_time;