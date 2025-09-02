#!/usr/bin/env python3
"""按月创建分区表并归档数据"""
import os
os.environ['IS_DOCKER'] = 'false'
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from datetime import datetime, timedelta
import calendar

def create_monthly_partitions():
    """创建按月分区表并归档数据"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("🚀 开始创建月度分区表并归档数据...")
            
            # 1. 检查主表数据时间范围
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM t_user_health_data")
            time_range = cursor.fetchone()
            min_date = time_range[0]
            max_date = time_range[1]
            print(f"📊 主表数据时间范围: {min_date} ~ {max_date}")
            
            # 2. 生成需要创建的月份列表
            start_year_month = (min_date.year, min_date.month)
            end_year_month = (max_date.year, max_date.month)
            
            months_to_create = []
            current_year, current_month = start_year_month
            
            while (current_year, current_month) <= end_year_month:
                months_to_create.append((current_year, current_month))
                if current_month == 12:
                    current_year += 1
                    current_month = 1
                else:
                    current_month += 1
            
            print(f"📅 需要创建的月份分区: {len(months_to_create)}个")
            
            # 3. 为每个月创建分区表
            for year, month in months_to_create:
                table_name = f"t_user_health_data_{year}{month:02d}"
                
                # 检查表是否已存在
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if cursor.fetchone():
                    print(f"⚠️  表 {table_name} 已存在，跳过创建")
                    continue
                
                # 创建月度分区表
                create_table_sql = f"""
                CREATE TABLE {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    heart_rate INT,
                    pressure_high INT,
                    pressure_low INT,
                    blood_oxygen INT,
                    stress INT,
                    temperature DOUBLE(5,2),
                    step INT,
                    timestamp DATETIME,
                    latitude DECIMAL(10,6),
                    longitude DECIMAL(10,6),
                    altitude DOUBLE,
                    device_sn VARCHAR(255),
                    distance DOUBLE,
                    calorie DOUBLE,
                    is_deleted TINYINT(1) DEFAULT 0,
                    create_user VARCHAR(255),
                    create_user_id BIGINT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_user VARCHAR(255),
                    update_user_id BIGINT,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    user_id BIGINT,
                    org_id BIGINT,
                    
                    INDEX idx_device_timestamp (device_sn, timestamp),
                    INDEX idx_org_timestamp (org_id, timestamp),
                    INDEX idx_user_timestamp (user_id, timestamp),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康数据月度分区表-{year}年{month}月'
                """
                
                cursor.execute(create_table_sql)
                print(f"✅ 创建分区表: {table_name}")
                
                # 4. 归档数据到分区表
                # 计算该月的开始和结束日期
                start_date = f"{year}-{month:02d}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{month+1:02d}-01"
                
                # 插入数据到分区表
                insert_sql = f"""
                INSERT INTO {table_name} 
                (heart_rate, pressure_high, pressure_low, blood_oxygen, stress, temperature, 
                 step, timestamp, latitude, longitude, altitude, device_sn, distance, calorie,
                 is_deleted, create_user, create_user_id, create_time, update_user, 
                 update_user_id, update_time, user_id, org_id)
                SELECT heart_rate, pressure_high, pressure_low, blood_oxygen, stress, temperature,
                       step, timestamp, latitude, longitude, altitude, device_sn, distance, calorie,
                       is_deleted, create_user, create_user_id, create_time, update_user,
                       update_user_id, update_time, user_id, org_id
                FROM t_user_health_data 
                WHERE timestamp >= '{start_date}' AND timestamp < '{end_date}'
                """
                
                cursor.execute(insert_sql)
                affected_rows = cursor.rowcount
                print(f"📦 归档数据到 {table_name}: {affected_rows}条记录")
                
                # 提交每个表的创建和数据插入
                conn.commit()
            
            # 5. 创建统一的分区视图
            print("\n🔧 创建统一分区视图...")
            
            # 删除旧的分区表（如果存在）
            cursor.execute("DROP TABLE IF EXISTS t_user_health_data_partitioned")
            
            # 创建新的分区视图
            union_tables = []
            for year, month in months_to_create:
                table_name = f"t_user_health_data_{year}{month:02d}"
                union_tables.append(f"SELECT * FROM {table_name}")
            
            if union_tables:
                create_view_sql = f"""
                CREATE VIEW t_user_health_data_partitioned AS
                {' UNION ALL '.join(union_tables)}
                """
                cursor.execute(create_view_sql)
                print("✅ 创建统一分区视图: t_user_health_data_partitioned")
            
            # 6. 验证分区数据
            print("\n📊 验证分区数据...")
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data_partitioned")
            partitioned_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM t_user_health_data")
            original_count = cursor.fetchone()[0]
            
            print(f"原始表数据量: {original_count}")
            print(f"分区表数据量: {partitioned_count}")
            print(f"数据完整性: {'✅ 通过' if partitioned_count == original_count else '❌ 失败'}")
            
            # 7. 显示各分区数据分布
            print("\n📈 各分区数据分布:")
            for year, month in months_to_create:
                table_name = f"t_user_health_data_{year}{month:02d}"
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  {year}年{month:02d}月 ({table_name}): {count}条")
            
            conn.commit()
            print("\n🎉 分区表创建和数据归档完成!")
            
    except Exception as e:
        print(f"❌ 创建分区失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def create_daily_weekly_tables():
    """创建每日和每周数据表"""
    conn = pymysql.connect(
        host=MYSQL_HOST, 
        port=MYSQL_PORT, 
        user=MYSQL_USER, 
        password=MYSQL_PASSWORD, 
        database=MYSQL_DATABASE
    )
    
    try:
        with conn.cursor() as cursor:
            print("\n🔧 创建每日和每周数据表...")
            
            # 创建每日数据表
            create_daily_sql = """
            CREATE TABLE IF NOT EXISTS t_user_health_data_daily (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                device_sn VARCHAR(255) NOT NULL,
                user_id BIGINT,
                org_id BIGINT,
                date DATE NOT NULL,
                sleep_data JSON COMMENT '睡眠数据',
                exercise_daily_data JSON COMMENT '每日运动数据',
                workout_data JSON COMMENT '锻炼数据',
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY uk_device_date (device_sn, date),
                INDEX idx_user_date (user_id, date),
                INDEX idx_org_date (org_id, date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日健康数据表'
            """
            
            cursor.execute(create_daily_sql)
            print("✅ 创建每日数据表: t_user_health_data_daily")
            
            # 创建每周数据表
            create_weekly_sql = """
            CREATE TABLE IF NOT EXISTS t_user_health_data_weekly (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                device_sn VARCHAR(255) NOT NULL,
                user_id BIGINT,
                org_id BIGINT,
                week_start DATE NOT NULL COMMENT '周开始日期(周一)',
                exercise_week_data JSON COMMENT '每周运动数据',
                create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY uk_device_week (device_sn, week_start),
                INDEX idx_user_week (user_id, week_start),
                INDEX idx_org_week (org_id, week_start)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每周健康数据表'
            """
            
            cursor.execute(create_weekly_sql)
            print("✅ 创建每周数据表: t_user_health_data_weekly")
            
            conn.commit()
            print("🎉 每日和每周数据表创建完成!")
            
    except Exception as e:
        print(f"❌ 创建每日/每周表失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 开始数据库分区优化...")
    
    # 1. 创建月度分区表并归档数据
    create_monthly_partitions()
    
    # 2. 创建每日和每周数据表
    create_daily_weekly_tables()
    
    print("\n✅ 所有分区表创建完成!")
    print("📝 建议:")
    print("  1. 验证分区表数据完整性")
    print("  2. 更新应用查询逻辑使用分区表")
    print("  3. 考虑删除或备份原始主表数据") 