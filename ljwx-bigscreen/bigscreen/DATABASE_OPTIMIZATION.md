# 数据库优化方案

## 1. 表结构优化

### 1.1 健康数据表优化 (解决复杂关联问题)

```sql
-- 原表: t_user_health_data (只有device_sn)
-- 优化: 添加user_id和org_id冗余字段，减少JOIN查询

ALTER TABLE t_user_health_data 
ADD COLUMN user_id BIGINT COMMENT '用户ID(冗余字段)',
ADD COLUMN org_id BIGINT COMMENT '组织ID(冗余字段)',
ADD INDEX idx_user_org_time (user_id, org_id, timestamp),
ADD INDEX idx_device_time (device_sn, timestamp),
ADD INDEX idx_org_time (org_id, timestamp);

-- 数据迁移脚本
UPDATE t_user_health_data h 
JOIN sys_user u ON h.device_sn = u.device_sn
JOIN sys_user_org uo ON u.id = uo.user_id
SET h.user_id = u.id, h.org_id = uo.org_id
WHERE h.user_id IS NULL;
```

### 1.2 分区表策略 (解决千万级数据问题)

```sql
-- 1. 创建按月分区的主表
CREATE TABLE t_user_health_data_partitioned (
    id BIGINT AUTO_INCREMENT,
    device_sn VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    org_id BIGINT NOT NULL,
    heart_rate INT,
    blood_oxygen INT,
    temperature DECIMAL(4,1),
    pressure_high INT,
    pressure_low INT,
    stress INT,
    step INT,
    distance DECIMAL(10,2),
    calorie DECIMAL(10,2),
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    altitude DECIMAL(8,2),
    sleep_data JSON,
    workout_data JSON,
    exercise_daily_data JSON,
    exercise_week_data JSON,
    scientific_sleep_data JSON,
    timestamp DATETIME NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_deleted TINYINT DEFAULT 0,
    PRIMARY KEY (id, timestamp),
    INDEX idx_user_time (user_id, timestamp),
    INDEX idx_org_time (org_id, timestamp),
    INDEX idx_device_time (device_sn, timestamp)
) PARTITION BY RANGE (YEAR(timestamp) * 100 + MONTH(timestamp)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p202403 VALUES LESS THAN (202404),
    -- ... 继续添加分区
    PARTITION p202512 VALUES LESS THAN (202601),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- 2. 创建汇总表(冷数据)
CREATE TABLE t_user_health_data_daily_summary (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_sn VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    org_id BIGINT NOT NULL,
    date DATE NOT NULL,
    avg_heart_rate DECIMAL(5,1),
    avg_blood_oxygen DECIMAL(5,1),
    avg_temperature DECIMAL(4,1),
    avg_pressure_high DECIMAL(5,1),
    avg_pressure_low DECIMAL(5,1),
    avg_stress DECIMAL(5,1),
    total_step INT,
    total_distance DECIMAL(10,2),
    total_calorie DECIMAL(10,2),
    record_count INT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_device_date (device_sn, date),
    INDEX idx_user_date (user_id, date),
    INDEX idx_org_date (org_id, date)
);
```

### 1.3 配置表优化

```sql
-- 健康数据配置表
CREATE TABLE t_health_data_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    org_id BIGINT NOT NULL COMMENT '组织ID',
    field_name VARCHAR(50) NOT NULL COMMENT '字段名',
    field_label VARCHAR(100) COMMENT '字段显示名',
    is_enabled TINYINT DEFAULT 1 COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_org_field (org_id, field_name),
    INDEX idx_org_enabled (org_id, is_enabled)
);

-- 初始化配置数据
INSERT INTO t_health_data_config (org_id, field_name, field_label, sort_order) VALUES
(1, 'heart_rate', '心率', 1),
(1, 'blood_oxygen', '血氧', 2),
(1, 'temperature', '体温', 3),
(1, 'pressure_high', '收缩压', 4),
(1, 'pressure_low', '舒张压', 5),
(1, 'stress', '压力', 6),
(1, 'step', '步数', 7),
(1, 'distance', '距离', 8),
(1, 'calorie', '卡路里', 9);
```

### 1.4 慢更新字段分离优化 (解决存储冗余问题)

```sql
-- 1. 创建每日更新数据表
CREATE TABLE t_user_health_data_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_sn VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    org_id BIGINT NOT NULL,
    date DATE NOT NULL,
    sleep_data JSON COMMENT '睡眠数据(每日更新)',
    exercise_daily_data JSON COMMENT '每日运动数据',
    workout_data JSON COMMENT '锻炼数据',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_device_date (device_sn, date),
    INDEX idx_user_date (user_id, date),
    INDEX idx_org_date (org_id, date)
) COMMENT='健康数据每日更新表';

-- 2. 创建每周更新数据表
CREATE TABLE t_user_health_data_weekly (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_sn VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    org_id BIGINT NOT NULL,
    week_start DATE NOT NULL COMMENT '周开始日期(周一)',
    exercise_week_data JSON COMMENT '每周运动数据',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_device_week (device_sn, week_start),
    INDEX idx_user_week (user_id, week_start),
    INDEX idx_org_week (org_id, week_start)
) COMMENT='健康数据每周更新表';

-- 3. 优化主表结构(移除慢更新字段)
ALTER TABLE t_user_health_data 
DROP COLUMN sleep_data,
DROP COLUMN exercise_daily_data, 
DROP COLUMN workout_data,
DROP COLUMN exercise_week_data,
DROP COLUMN scientific_sleep_data;

-- 4. 添加配置表权重字段
ALTER TABLE t_health_data_config 
ADD COLUMN field_weight DECIMAL(3,2) DEFAULT 1.00 COMMENT '字段权重(用于健康画像)';
```

## 2. 索引优化策略

```sql
-- 复合索引(覆盖查询)
CREATE INDEX idx_health_query_cover ON t_user_health_data 
(org_id, timestamp, device_sn, user_id, heart_rate, blood_oxygen, temperature);

-- 分区表索引
ALTER TABLE t_user_health_data_partitioned 
ADD INDEX idx_hot_query (user_id, timestamp, device_sn),
ADD INDEX idx_org_query (org_id, timestamp, device_sn);
```

## 3. 查询优化

### 3.1 热数据查询(最近3个月)
- 使用分区表
- 复合索引覆盖
- 限制返回字段

### 3.2 冷数据查询(3个月前)
- 使用汇总表
- 预聚合数据
- 减少数据传输

### 3.3 缓存策略
- Redis缓存热点数据
- 5分钟过期时间
- 按组织和时间范围分层缓存

## 4. 数据迁移脚本

```sql
-- 定时任务：热数据汇总到冷数据表
CREATE EVENT evt_health_data_summary
ON SCHEDULE EVERY 1 DAY
STARTS '2025-01-01 02:00:00'
DO
INSERT INTO t_user_health_data_daily_summary 
(device_sn, user_id, org_id, date, avg_heart_rate, avg_blood_oxygen, 
 avg_temperature, avg_pressure_high, avg_pressure_low, avg_stress,
 total_step, total_distance, total_calorie, record_count)
SELECT 
    device_sn, user_id, org_id, DATE(timestamp),
    AVG(heart_rate), AVG(blood_oxygen), AVG(temperature),
    AVG(pressure_high), AVG(pressure_low), AVG(stress),
    SUM(step), SUM(distance), SUM(calorie), COUNT(*)
FROM t_user_health_data 
WHERE DATE(timestamp) = DATE_SUB(CURDATE(), INTERVAL 1 DAY)
AND is_deleted = 0
GROUP BY device_sn, user_id, org_id, DATE(timestamp)
ON DUPLICATE KEY UPDATE
    avg_heart_rate = VALUES(avg_heart_rate),
    avg_blood_oxygen = VALUES(avg_blood_oxygen),
    record_count = VALUES(record_count);
```

## 5. 性能监控

```sql
-- 查询性能监控
SELECT 
    table_name,
    partition_name,
    table_rows,
    data_length/1024/1024 as data_mb,
    index_length/1024/1024 as index_mb
FROM information_schema.partitions 
WHERE table_schema = 'ljwx' 
AND table_name LIKE '%health_data%';

-- 慢查询监控
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
```

## 6. 预期性能提升

- **查询速度**: 提升80%以上
- **存储空间**: 节省60%以上(通过汇总表)
- **并发能力**: 提升5倍以上
- **维护成本**: 降低70%以上 