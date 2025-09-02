#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import os
from datetime import datetime, date
import statistics

def test_direct_baseline_insert():
    """直接测试baseline数据插入"""
    try:
        # 数据库连接配置
        connection = pymysql.connect(
            host=os.environ.get('MYSQL_HOST', '127.0.0.1'),
            port=int(os.environ.get('MYSQL_PORT', '3306')),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', '123456'),
            database=os.environ.get('MYSQL_DATABASE', 'lj-06'),
            charset='utf8mb4'
        )
        
        print("=== 直接测试baseline数据插入 ===")
        
        with connection.cursor() as cursor:
            # 1. 查询原始数据
            query = """
            SELECT heart_rate FROM t_user_health_data 
            WHERE device_sn = 'A5GTQ24603000537' 
            AND DATE(create_time) = '2025-06-02' 
            AND is_deleted = 0 
            AND heart_rate IS NOT NULL
            LIMIT 10
            """
            cursor.execute(query)
            heart_rates = [row[0] for row in cursor.fetchall()]
            
            print(f"查询到的心率数据: {heart_rates}")
            
            if len(heart_rates) >= 3:
                # 2. 计算基线统计
                mean_val = statistics.mean(heart_rates)
                std_val = statistics.stdev(heart_rates) if len(heart_rates) > 1 else 0
                min_val = min(heart_rates)
                max_val = max(heart_rates)
                
                print(f"统计结果: 均值={mean_val:.2f}, 标准差={std_val:.2f}, 最小值={min_val}, 最大值={max_val}")
                
                # 3. 插入baseline记录
                insert_query = """
                INSERT INTO t_health_baseline 
                (device_sn, feature_name, mean_value, std_value, min_value, max_value, 
                 is_current, baseline_time, create_time, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                baseline_time = datetime.combine(date(2025, 6, 2), datetime.min.time())
                current_time = datetime.now()
                
                values = (
                    'A5GTQ24603000537',  # device_sn
                    'heart_rate',        # feature_name
                    mean_val,           # mean_value
                    std_val,            # std_value
                    min_val,            # min_value
                    max_val,            # max_value
                    1,                  # is_current
                    baseline_time,      # baseline_time
                    current_time,       # create_time
                    current_time        # update_time
                )
                
                cursor.execute(insert_query, values)
                connection.commit()
                
                print(f"✅ 成功插入baseline记录，插入ID: {cursor.lastrowid}")
                
                # 4. 验证插入
                cursor.execute("SELECT COUNT(*) FROM t_health_baseline")
                new_count = cursor.fetchone()[0]
                print(f"插入后总记录数: {new_count}")
                
            else:
                print(f"❌ 数据不足，只有 {len(heart_rates)} 条记录")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ 直接插入测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_baseline_insert() 