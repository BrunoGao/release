-- ============================================================================
-- 运动轨迹 & 电子围栏系统 - 数据库升级脚本
-- 版本: v1.0.0  
-- 日期: 2024-01-15
-- 说明: 基于现有 t_user_health_data 和 t_geofence 表进行向下兼容扩展
-- 重要: 所有健康数据查询必须通过 UnifiedHealthDataQueryService.queryHealthData 方法
-- ============================================================================

-- 设置事务隔离级别和字符集
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
SET NAMES utf8mb4;

-- ============================================================================
-- 1. 轨迹数据表扩展 (基于现有 t_user_health_data)
-- ============================================================================

-- 检查表是否存在
SELECT 'Starting t_user_health_data table extension...' as status;

-- 为现有健康数据表添加轨迹专用字段
ALTER TABLE t_user_health_data 
ADD COLUMN IF NOT EXISTS speed DOUBLE COMMENT '速度(km/h)' AFTER distance,
ADD COLUMN IF NOT EXISTS bearing DOUBLE COMMENT '方向角(度,0-360)' AFTER speed,
ADD COLUMN IF NOT EXISTS accuracy DOUBLE COMMENT '定位精度(米)' AFTER bearing,
ADD COLUMN IF NOT EXISTS location_type TINYINT DEFAULT 1 COMMENT '定位类型:1-GPS,2-WiFi,3-基站' AFTER accuracy,
ADD COLUMN IF NOT EXISTS geom POINT SRID 4326 COMMENT '空间几何对象' AFTER location_type;

-- 创建空间索引 (提升地理查询性能)
ALTER TABLE t_user_health_data 
ADD SPATIAL INDEX IF NOT EXISTS idx_geom (geom);

-- 创建轨迹查询专用复合索引
ALTER TABLE t_user_health_data 
ADD INDEX IF NOT EXISTS idx_user_timestamp_location (user_id, timestamp, latitude, longitude),
ADD INDEX IF NOT EXISTS idx_customer_timestamp (customer_id, timestamp),
ADD INDEX IF NOT EXISTS idx_org_timestamp (org_id, timestamp);

-- 更新现有数据的空间几何对象 (为已有位置数据生成geom字段)
UPDATE t_user_health_data 
SET geom = ST_GeomFromText(CONCAT('POINT(', longitude, ' ', latitude, ')'), 4326)
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL 
  AND geom IS NULL;

SELECT 'Completed t_user_health_data extension' as status;

-- ============================================================================
-- 2. 围栏表扩展 (基于现有 t_geofence)
-- ============================================================================

SELECT 'Starting t_geofence table extension...' as status;

-- 扩展围栏表 - 添加告警和类型支持
ALTER TABLE t_geofence
ADD COLUMN IF NOT EXISTS fence_type ENUM('CIRCLE','RECTANGLE','POLYGON') DEFAULT 'POLYGON' COMMENT '围栏类型' AFTER area,
ADD COLUMN IF NOT EXISTS center_lng DECIMAL(10,7) COMMENT '中心点经度' AFTER fence_type,
ADD COLUMN IF NOT EXISTS center_lat DECIMAL(10,7) COMMENT '中心点纬度' AFTER center_lng,
ADD COLUMN IF NOT EXISTS radius FLOAT COMMENT '半径(米,圆形围栏用)' AFTER center_lat,
ADD COLUMN IF NOT EXISTS geom GEOMETRY SRID 4326 COMMENT '空间几何对象' AFTER radius,

-- 告警配置相关字段
ADD COLUMN IF NOT EXISTS alert_on_enter BOOLEAN DEFAULT TRUE COMMENT '进入告警' AFTER geom,
ADD COLUMN IF NOT EXISTS alert_on_exit BOOLEAN DEFAULT TRUE COMMENT '离开告警' AFTER alert_on_enter,
ADD COLUMN IF NOT EXISTS alert_on_stay BOOLEAN DEFAULT FALSE COMMENT '停留告警' AFTER alert_on_exit,
ADD COLUMN IF NOT EXISTS stay_duration_minutes INT DEFAULT 30 COMMENT '停留时长阈值(分钟)' AFTER alert_on_stay,
ADD COLUMN IF NOT EXISTS alert_level ENUM('LOW','MEDIUM','HIGH') DEFAULT 'MEDIUM' COMMENT '告警级别' AFTER stay_duration_minutes,

-- 通知配置
ADD COLUMN IF NOT EXISTS notify_channels JSON COMMENT '通知渠道配置' AFTER alert_level,
ADD COLUMN IF NOT EXISTS notify_template_id VARCHAR(32) COMMENT '通知模板ID' AFTER notify_channels,

-- 多租户支持
ADD COLUMN IF NOT EXISTS org_id BIGINT COMMENT '组织ID' AFTER notify_template_id,
ADD COLUMN IF NOT EXISTS customer_id BIGINT DEFAULT 0 COMMENT '租户ID,0表示全局数据' AFTER org_id,

-- 状态控制
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用' AFTER customer_id,
ADD COLUMN IF NOT EXISTS created_by VARCHAR(32) COMMENT '创建人' AFTER is_active;

-- 创建围栏空间索引
ALTER TABLE t_geofence 
ADD SPATIAL INDEX IF NOT EXISTS idx_geom (geom),
ADD INDEX IF NOT EXISTS idx_customer_org (customer_id, org_id),
ADD INDEX IF NOT EXISTS idx_active_type (is_active, fence_type);

SELECT 'Completed t_geofence extension' as status;

-- ============================================================================
-- 3. 围栏绑定关系表 (全新)
-- ============================================================================

CREATE TABLE IF NOT EXISTS t_geofence_bind (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bind_id VARCHAR(32) NOT NULL COMMENT '绑定ID',
    fence_id BIGINT NOT NULL COMMENT '围栏ID',
    target_type ENUM('USER','DEVICE','VEHICLE') NOT NULL COMMENT '绑定目标类型',
    target_id BIGINT NOT NULL COMMENT '目标ID',
    
    -- 绑定规则配置
    bind_rule JSON COMMENT '绑定规则配置',
    work_time_only BOOLEAN DEFAULT FALSE COMMENT '仅工作时间生效',
    effective_weekdays VARCHAR(10) DEFAULT '1,2,3,4,5' COMMENT '生效星期(1-7)',
    effective_start_time TIME DEFAULT '09:00:00' COMMENT '生效开始时间',
    effective_end_time TIME DEFAULT '18:00:00' COMMENT '生效结束时间',
    
    -- 多租户支持
    customer_id BIGINT DEFAULT 0 COMMENT '租户ID',
    org_id BIGINT COMMENT '组织ID',
    
    -- 状态控制
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_by VARCHAR(32) COMMENT '创建人',
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    UNIQUE KEY uk_fence_target (fence_id, target_type, target_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_customer_org (customer_id, org_id),
    INDEX idx_active (is_active),
    
    -- 外键约束
    FOREIGN KEY (fence_id) REFERENCES t_geofence(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='围栏绑定关系表';

SELECT 'Created t_geofence_bind table' as status;

-- ============================================================================
-- 4. 围栏告警记录表 (全新)
-- ============================================================================

CREATE TABLE IF NOT EXISTS t_geofence_alert (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_id VARCHAR(32) NOT NULL COMMENT '告警ID',
    fence_id BIGINT NOT NULL COMMENT '围栏ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    device_id VARCHAR(64) COMMENT '设备ID',
    
    -- 告警信息
    alert_type ENUM('ENTER','EXIT','STAY_TIMEOUT') NOT NULL COMMENT '告警类型',
    alert_level ENUM('LOW','MEDIUM','HIGH') NOT NULL COMMENT '告警级别',
    
    -- 时间信息
    start_time TIMESTAMP NOT NULL COMMENT '告警开始时间',
    end_time TIMESTAMP COMMENT '告警结束时间',
    duration_minutes INT COMMENT '持续时长(分钟)',
    
    -- 位置信息
    location_lng DECIMAL(10,7) COMMENT '告警位置经度',
    location_lat DECIMAL(10,7) COMMENT '告警位置纬度',
    location_desc VARCHAR(200) COMMENT '位置描述',
    location_geom POINT SRID 4326 COMMENT '告警位置空间对象',
    
    -- 处理信息
    alert_status ENUM('PENDING','PROCESSING','RESOLVED','IGNORED') DEFAULT 'PENDING' COMMENT '处理状态',
    handler_id BIGINT COMMENT '处理人ID',
    handle_time TIMESTAMP COMMENT '处理时间',
    handle_note TEXT COMMENT '处理备注',
    handle_result VARCHAR(500) COMMENT '处理结果',
    
    -- 通知信息
    notify_status JSON COMMENT '通知状态记录',
    notify_retry_count INT DEFAULT 0 COMMENT '通知重试次数',
    notify_success_time TIMESTAMP COMMENT '通知成功时间',
    
    -- 多租户支持
    customer_id BIGINT DEFAULT 0 COMMENT '租户ID',
    org_id BIGINT COMMENT '组织ID',
    
    -- 系统字段
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引优化
    UNIQUE KEY uk_alert_id (alert_id),
    INDEX idx_fence_time (fence_id, start_time),
    INDEX idx_user_time (user_id, start_time),
    INDEX idx_status_level (alert_status, alert_level),
    INDEX idx_customer_time (customer_id, start_time),
    INDEX idx_org_time (org_id, start_time),
    SPATIAL INDEX idx_location_geom (location_geom),
    
    -- 外键约束
    FOREIGN KEY (fence_id) REFERENCES t_geofence(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='围栏告警记录表';

SELECT 'Created t_geofence_alert table' as status;

-- ============================================================================
-- 5. 用户在线状态表 (全新)
-- ============================================================================

CREATE TABLE IF NOT EXISTS t_user_online_status (
    user_id BIGINT PRIMARY KEY COMMENT '用户ID',
    device_id VARCHAR(64) COMMENT '设备ID',
    device_sn VARCHAR(64) COMMENT '设备序列号',
    
    -- 在线状态
    online_status ENUM('ONLINE','OFFLINE','ABNORMAL') NOT NULL DEFAULT 'OFFLINE' COMMENT '在线状态',
    last_seen_time TIMESTAMP COMMENT '最后活跃时间',
    offline_reason VARCHAR(100) COMMENT '离线原因',
    
    -- 位置信息
    last_location_time TIMESTAMP COMMENT '最后定位时间',
    last_lng DECIMAL(10,7) COMMENT '最后经度',
    last_lat DECIMAL(10,7) COMMENT '最后纬度',
    last_altitude DOUBLE COMMENT '最后海拔',
    last_location_desc VARCHAR(200) COMMENT '最后位置描述',
    last_location_geom POINT SRID 4326 COMMENT '最后位置空间对象',
    
    -- 设备状态
    battery_level INT COMMENT '电池电量(%)',
    signal_strength INT COMMENT '信号强度',
    heartbeat_interval INT DEFAULT 30 COMMENT '心跳间隔(秒)',
    upload_method VARCHAR(50) COMMENT '上传方式:wifi/bluetooth/common_event',
    
    -- 统计信息
    daily_distance DOUBLE DEFAULT 0 COMMENT '今日运动距离(km)',
    daily_steps INT DEFAULT 0 COMMENT '今日步数',
    daily_calories DOUBLE DEFAULT 0 COMMENT '今日卡路里',
    last_reset_date DATE COMMENT '最后重置日期',
    
    -- 多租户支持
    customer_id BIGINT DEFAULT 0 COMMENT '租户ID',
    org_id BIGINT COMMENT '组织ID',
    
    -- 系统字段
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引优化
    INDEX idx_online_status (online_status),
    INDEX idx_customer_status (customer_id, online_status),
    INDEX idx_org_status (org_id, online_status),
    INDEX idx_last_seen (last_seen_time),
    INDEX idx_device (device_id, device_sn),
    SPATIAL INDEX idx_last_location (last_location_geom),
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户在线状态表';

SELECT 'Created t_user_online_status table' as status;

-- ============================================================================
-- 6. 轨迹数据月度分表模板 (支持UnifiedHealthDataQueryService的分表策略)
-- ============================================================================

-- 创建分表存储过程
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS CreateMonthlyTrackTable(IN table_suffix VARCHAR(10))
BEGIN
    DECLARE table_name VARCHAR(50);
    SET table_name = CONCAT('t_user_health_data_', table_suffix);
    
    SET @sql = CONCAT('CREATE TABLE IF NOT EXISTS ', table_name, ' (
        LIKE t_user_health_data INCLUDING ALL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT=''健康数据月度表-', table_suffix, '''');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- 添加月度表专用索引
    SET @idx_sql = CONCAT('ALTER TABLE ', table_name, ' 
        ADD INDEX IF NOT EXISTS idx_user_timestamp (user_id, timestamp),
        ADD INDEX IF NOT EXISTS idx_customer_timestamp (customer_id, timestamp),
        ADD SPATIAL INDEX IF NOT EXISTS idx_geom (geom)');
    
    PREPARE idx_stmt FROM @idx_sql;
    EXECUTE idx_stmt;
    DEALLOCATE PREPARE idx_stmt;
    
END$$

DELIMITER ;

-- 创建当前月及未来6个月的分表
CALL CreateMonthlyTrackTable(DATE_FORMAT(NOW(), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 1 MONTH), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 2 MONTH), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 3 MONTH), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 4 MONTH), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 5 MONTH), '%Y%m'));
CALL CreateMonthlyTrackTable(DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 6 MONTH), '%Y%m'));

SELECT 'Created monthly partition tables' as status;

-- ============================================================================
-- 7. 初始化示例数据 (开发测试用)
-- ============================================================================

-- 示例围栏数据
INSERT IGNORE INTO t_geofence (
    id, name, area, fence_type, center_lng, center_lat, radius, 
    alert_on_enter, alert_on_exit, alert_level, customer_id, is_active,
    created_by, create_time
) VALUES 
(1, '办公区域', 'POLYGON((116.397428 39.90923, 116.407428 39.90923, 116.407428 39.91923, 116.397428 39.91923, 116.397428 39.90923))', 
 'POLYGON', 116.402428, 39.914115, NULL, TRUE, TRUE, 'MEDIUM', 0, TRUE, 'system', NOW()),

(2, '安全区域', 'CIRCLE(116.397428 39.90923, 500)', 
 'CIRCLE', 116.397428, 39.90923, 500, TRUE, TRUE, 'HIGH', 0, TRUE, 'system', NOW()),

(3, '禁止区域', 'RECTANGLE(116.390000 39.900000, 116.400000 39.910000)', 
 'RECTANGLE', 116.395000, 39.905000, NULL, TRUE, FALSE, 'HIGH', 0, TRUE, 'system', NOW());

-- 更新围栏空间对象
UPDATE t_geofence SET 
geom = CASE 
    WHEN fence_type = 'CIRCLE' THEN ST_Buffer(ST_GeomFromText(CONCAT('POINT(', center_lng, ' ', center_lat, ')'), 4326), radius/111000)
    WHEN fence_type = 'POLYGON' THEN ST_GeomFromText(area, 4326)
    WHEN fence_type = 'RECTANGLE' THEN ST_GeomFromText(REPLACE(REPLACE(area, 'RECTANGLE(', 'POLYGON(('), ' ', ' '), 4326)
    ELSE NULL
END
WHERE geom IS NULL AND center_lng IS NOT NULL AND center_lat IS NOT NULL;

SELECT 'Initialized sample data' as status;

-- ============================================================================
-- 8. 数据迁移验证
-- ============================================================================

-- 验证表结构
SELECT 'Validating table structures...' as status;

-- 验证 t_user_health_data 新增字段
SELECT COUNT(*) as user_health_data_columns 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 't_user_health_data' 
AND COLUMN_NAME IN ('speed', 'bearing', 'accuracy', 'location_type', 'geom');

-- 验证索引创建
SELECT COUNT(*) as spatial_indexes
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_NAME IN ('t_user_health_data', 't_geofence', 't_geofence_alert', 't_user_online_status')
AND INDEX_TYPE = 'SPATIAL';

-- 验证新表创建
SELECT COUNT(*) as new_tables
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME IN ('t_geofence_bind', 't_geofence_alert', 't_user_online_status');

-- 验证分表创建
SELECT COUNT(*) as monthly_tables
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME LIKE 't_user_health_data_%' 
AND TABLE_NAME REGEXP 't_user_health_data_[0-9]{6}';

-- 统计现有数据量
SELECT 
    (SELECT COUNT(*) FROM t_user_health_data WHERE latitude IS NOT NULL AND longitude IS NOT NULL) as existing_location_records,
    (SELECT COUNT(*) FROM t_geofence) as existing_geofences,
    (SELECT COUNT(*) FROM t_geofence WHERE geom IS NOT NULL) as geofences_with_geom;

SELECT 'Database upgrade completed successfully!' as status;

-- ============================================================================
-- 9. 性能优化建议
-- ============================================================================

-- 创建视图简化常用查询 (配合UnifiedHealthDataQueryService使用)
CREATE OR REPLACE VIEW v_user_current_status AS
SELECT 
    u.id as user_id,
    u.username,
    u.nick_name,
    o.online_status,
    o.last_location_time,
    o.last_lng,
    o.last_lat,
    o.daily_distance,
    o.daily_steps,
    o.battery_level,
    u.org_id,
    u.customer_id
FROM sys_user u
LEFT JOIN t_user_online_status o ON u.id = o.user_id
WHERE u.status = 1 AND u.del_flag = 0;

SELECT 'Created performance optimization views' as status;

-- ============================================================================
-- 脚本执行完成
-- ============================================================================

SELECT CONCAT(
    '🎉 数据库升级脚本执行完成！\n',
    '✅ 扩展了 t_user_health_data 表 (添加轨迹专用字段)\n',
    '✅ 扩展了 t_geofence 表 (添加告警和类型支持)\n', 
    '✅ 创建了 t_geofence_bind 表 (围栏绑定关系)\n',
    '✅ 创建了 t_geofence_alert 表 (告警记录)\n',
    '✅ 创建了 t_user_online_status 表 (在线状态)\n',
    '✅ 创建了月度分表支持 (配合UnifiedHealthDataQueryService)\n',
    '✅ 创建了性能优化索引和视图\n',
    '✅ 初始化了示例数据\n\n',
    '⚠️  重要提醒: 所有健康数据查询必须通过 UnifiedHealthDataQueryService.queryHealthData 方法！'
) as completion_message;